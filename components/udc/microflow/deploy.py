"""微流程发布：create → checkSchema/update(RELEASE) → 回读校验。

契约（实测，2026-10 于 lowcode-test2）：
  1. create  : GraphQL `udcMicroflowCreatePost`，state=DRAFT
  2. 取 guid : GraphQL `udcMicroflowFindByIdGet`（create 的返回不含 guid）
  3. 发布    : REST `POST /service/udc/microflow/checkSchema/update`，
               **必须带 appId**（少它直接 BOOT_1001「appId must not be null」），
               共 15 字段，state=RELEASE
  4. 回读    : 再 FindByIdGet 确认 state=RELEASE

★ 为什么发布不能走 GraphQL `udcMicroflowUpdatePost`：
  提交 state=RELEASE 后回读仍是 DRAFT。只有 REST checkSchema/update 真发布。
"""
from __future__ import annotations

import json
import urllib.request

CREATE_Q = ("mutation g($p: udcMicroflowCreatePostInputBody) { data0: udcMicroflowCreatePost"
            "(body: $p) { code data { content } message } }")
# ★ 必须查 triggerType + dataSchema：发布时 body 要带 triggerType，
#   回读校验要核 endNode/trigger/nodes。只查 5 个轻量字段会让 publish() 拿到
#   triggerType=None 再发出去，并且无法回读复核（实测踩过）。
GET_Q = ("query g($p: udcMicroflowFindByIdGetInputPath){ data0: udcMicroflowFindByIdGet(path:$p)"
         "{ code message data { content { id state guid name caption type triggerType "
         "serviceInterface groupType microFlowGroupId dataSchema } } } }")
DELETE_Q = ("mutation g($p: udcMicroflowDeletePostInputBody) { data0: udcMicroflowDeletePost"
            "(body: $p) { code message } }")

PUBLISH_FIELDS = ("appId", "id", "name", "caption", "type", "triggerType", "state",
                  "dataSchema", "serviceInterface", "sourceType", "creationMethod",
                  "groupType", "versionCode", "openApi", "restApi", "microFlowGroupId")


class PublishError(RuntimeError):
    pass


def _req(host, path, body, cookie, timeout=180, transport=None):
    """JSON POST。★ 默认走 curl：本环境网关对 Python urllib 的 TLS 指纹
    间歇性回 `SSL: UNEXPECTED_EOF_WHILE_READING`（HTTP/1.1），curl(HTTP/2) 稳定。
    实测 2026-11-01：同一请求 urllib 全 EOF、curl 正常；表达式接口同样现象。
    保留 urllib 作为 curl 不可用时的回退（少数环境没有 curl）。

    ``transport`` 若给出（如 components.transport.page_fetch.PageFetch），
    则请求由浏览器页面发出，cookie 不离开浏览器 —— 这是首选路径，
    因为 session token 就是用户身份，导出到本地重放等于复制身份。
    """
    import subprocess

    if transport is not None:
        r = transport.post(path, body)
        j = r.get("json")
        if j is None:
            raise RuntimeError("页面 fetch 失败: status=%s %s"
                               % (r.get("status"), str(r.get("error") or r.get("body"))[:300]))
        return j

    url = host.rstrip("/") + path
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        p = subprocess.run(
            ["curl", "-sS", "--max-time", str(timeout), "-X", "POST", url,
             "-H", "Content-Type: application/json", "-H", "Cookie: " + cookie,
             "--data-binary", "@-"],
            input=payload, capture_output=True, timeout=timeout + 30)
        if p.returncode == 0 and p.stdout:
            return json.loads(p.stdout.decode("utf-8", "replace"))
        err = (p.stderr or b"").decode("utf-8", "replace")[:300]
        raise RuntimeError("curl rc=%s %s" % (p.returncode, err))
    except FileNotFoundError:
        pass          # 没有 curl → 走 urllib 回退
    except (RuntimeError, ValueError):
        raise

    r = urllib.request.Request(url, data=payload,
                               headers={"Content-Type": "application/json",
                                        "Cookie": cookie})
    return json.loads(urllib.request.urlopen(r, timeout=timeout).read().decode("utf-8"))


def _gql(host, op, body, query, cookie, timeout=180, transport=None):
    return _req(host, "/service/udc/graphql?" + op,
                {"query": query, "variables": {"p": body}}, cookie, timeout,
                transport=transport)


def _content(r):
    """取 data0.data.content。

    ★ create 的 content 是**裸 id 字符串**（"8849229208645378355"），
      FindByIdGet 的 content 才是对象 {id,state,guid,...}。
      旧实现 `return d.get("content") if isinstance(d,dict) else d` 对字符串
      会返回整个 data dict 而不是 id，导致 create 被判「未返回 id」。
    """
    d0 = (r.get("data") or {}).get("data0")
    if not isinstance(d0, dict):
        return None
    d = d0.get("data")
    if isinstance(d, dict):
        return d.get("content")
    return d


def _schema_trigger_type(schema) -> str:
    """从 schema 的 trigger.type 推出 triggerType。"""
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except Exception:
            return ""
    t = ((schema or {}).get("trigger") or {}).get("type")
    return t if t in ("MANUAL", "SCHEDULE", "BUSINESS_EVENT") else ""


def create(host, cookie, *, app_id, app_name, name, caption, schema,
           trigger_type="", group_id="", open_api="STOP",
           rest_api="DISABLED") -> str:
    """建流程（DRAFT），返回 id。

    ★ trigger_type 留空时从 schema.trigger.type 推导 —— 传空串会让 create 失败，
      而失败又被 _content 折成 None，报成误导性的「create 未返回 id」（实测踩过）。
    """
    trigger_type = trigger_type or _schema_trigger_type(schema) or "MANUAL"
    ds = schema if isinstance(schema, str) else json.dumps(schema, ensure_ascii=False)
    body = {"appId": str(app_id), "name": name, "caption": caption, "type": "SERVICE",
            "triggerType": trigger_type, "state": "DRAFT", "dataSchema": ds,
            "serviceInterface": None, "sourceType": "PAGE",
            "creationMethod": "MANUAL", "groupType": "DEFAULT",
            "openApi": open_api, "restApi": rest_api}
    if group_id:
        body["microFlowGroupId"] = group_id
    r = _gql(host, "udcMicroflowCreatePost", body, CREATE_Q, cookie, transport=transport)
    mid = _content(r)
    if not mid:
        d0 = (r.get("data") or {}).get("data0") or {}
        raise PublishError("create 失败 code=%s message=%s（triggerType=%r）"
                           % (d0.get("code"), d0.get("message"), trigger_type))
    return str(mid)


def get(host, cookie, mid, transport=None) -> dict:
    return _content(_gql(host, "udcMicroflowFindByIdGet", {"id": str(mid)},
                         GET_Q, cookie)) or {}


def publish(host, cookie, mid, *, app_id, schema, name="", caption="",
            trigger_type="", group_id="", open_api="STOP",
            rest_api="DISABLED", transport=None):
    """走 REST checkSchema/update 真发布。返回 (ok, 详情 dict)。"""
    cur = get(host, cookie, mid, transport=transport)
    guid = cur.get("guid")
    # ★ triggerType 从回读取，不默认 MANUAL —— 定时/事件流程用 MANUAL 发会被拒或触发方式丢失
    trigger_type = trigger_type or cur.get("triggerType") or "MANUAL"
    ds = schema if isinstance(schema, str) else json.dumps(schema, ensure_ascii=False)
    extra = {"description": "", "publishState": "UNPUBLISH",
             "lastVersionMetadataState": "DISABLED", "restPath": None}
    body = {**extra, "appId": str(app_id), "id": str(mid),
            "name": name or cur.get("name"), "caption": caption or cur.get("caption"),
            "type": "SERVICE", "triggerType": trigger_type, "state": "RELEASE",
            "dataSchema": ds, "serviceInterface": None, "sourceType": "PAGE",
            "creationMethod": "MANUAL", "groupType": "DEFAULT", "versionCode": 100,
            "openApi": open_api, "restApi": rest_api}
    if guid:
        body["guid"] = guid
    # ★ 定时/事件流程必须带这两个字段，否则部署阶段「一致性检测未通过」
    #   （真实抓包 body 里恒有，服务定义流程填 "-" 即可）见
    #   core/facts/udc/microflow/schedule-structure.md / event-listener-structure.md
    body.setdefault("scheduleCaption", "-")
    body.setdefault("businessEventCaption", "-")
    if group_id:
        body["microFlowGroupId"] = group_id
    missing = [f for f in ("appId", "id", "dataSchema", "state") if body.get(f) is None]
    if missing:
        raise PublishError("发布体缺必填字段 %s（少 appId 会 BOOT_1001）" % missing)
    r = _req(host, "/service/udc/microflow/checkSchema/update", body, cookie,
             transport=transport)
    code = r.get("code")
    cc = (r.get("data") or {}).get("content") or {}
    if code != "BOOT_0000":
        raise PublishError("发布被拒 code=%s message=%s" % (code, r.get("message")))
    if cc.get("check") is not True:
        errs = cc.get("errorMessage") or []
        raise PublishError("check=false，errors=%s" % [
            (e.get("nodeCaption"), e.get("path"), e.get("errorCode")) for e in errs[:10]])
    back = get(host, cookie, mid, transport=transport)
    if back.get("state") != "RELEASE":
        raise PublishError("发布后回读 state=%s（应为 RELEASE）" % back.get("state"))
    return True, {"id": str(mid), "state": back.get("state"),
                  "errors": cc.get("errors"), "guid": guid}


def delete(host, cookie, mid, transport=None) -> bool:
    r = _gql(host, "udcMicroflowDeletePost", {"id": str(mid)}, DELETE_Q, cookie,
             transport=transport)
    return ((r.get("data") or {}).get("data0") or {}).get("code") == "BOOT_0000"


def deploy(host, cookie, *, app_id, app_name, name, caption, schema, group_id="",
           trigger_type="") -> dict:
    """一步到位：create → publish → 回读。失败即抛（不留半成品：失败自动删）。"""
    mid = create(host, cookie, app_id=app_id, app_name=app_name, name=name,
                 caption=caption, schema=schema, trigger_type=trigger_type,
                 group_id=group_id)
    try:
        ok, info = publish(host, cookie, mid, app_id=app_id, schema=schema,
                           name=name, caption=caption, trigger_type=trigger_type,
                           group_id=group_id)
        return info
    except Exception:
        try:
            delete(host, cookie, mid)
        except Exception:
            pass
        raise
