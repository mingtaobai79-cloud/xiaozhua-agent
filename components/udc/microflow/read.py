"""微流程的**接口读取**（不走数据库）。

为什么单独开这个模块：

  1. DB 只是取证工具，不是常规验证通道。客户环境里通常没有 DB 访问权，
     只有接口是通用路径。
  2. 「接口写成功」必须由「接口读回来」闭环 —— 用 DB 回读等于换了一套信源，
     验证的是存储层而不是平台契约。
  3. 接口要能读，才能把「读」也建模成可复用能力。

★ 实测（LIVE）：
    `udcMicroflowServiceListPost`
      body: {pageInfo, params:{appId}, sort}
      → content **是数组**（每个元素是一组 {appId, caption, groupId,
        microFlowServiceInfoDtos[], pageInfo}）
      → dto.state 是**字符串枚举名** `DRAFT` / `RELEASE`，不是数字 10/20
      → 列表**不过滤草稿**：DRAFT 也会返回
      → dto.path / hostPath 在未生成 REST 暴露时为 null

★ GraphQL 必须带 `data { }` 层，漏了会报 FieldUndefined（踩过多次）。
"""
from __future__ import annotations

LIST_OP = "udcMicroflowServiceListPost"

_LIST_QF = """
code
data {
  content {
    appId
    caption
    groupId
    microFlowServiceInfoDtos {
      id appId name caption description type triggerType state
      path method hostPath hasInput hasOutput
    }
  }
  pageInfo { needTotal pageNumber pageSize pages total }
}
message
status
"""

_LIST_JS = r"""
(async () => {
  const q = `mutation g($p: %(op)sInputBody) {
    data0: %(op)s(body: $p) { %(qf)s }
  }`;
  const body = {
    pageInfo: {needTotal: true, pageNumber: 1, pageSize: %(size)d, pages: 0, total: 0},
    params: {appId: %(app)s},
    sort: {orders: [{direction: "DESC", property: "createTime"}]}
  };
  const r = await fetch("/service/udc/graphql?%(op)s", {
    method: "POST",
    headers: {"Content-Type": "application/json", "Accept": "application/json"},
    body: JSON.stringify({query: q, variables: {p: body}}),
    credentials: "include"
  });
  return await r.text();
})()
"""


def _flatten_content(content) -> list[dict]:
    """content 是数组，每组里挂 microFlowServiceInfoDtos。"""
    groups = content if isinstance(content, list) else [content or {}]
    out = []
    for g in groups:
        if isinstance(g, dict):
            out.extend(g.get("microFlowServiceInfoDtos") or [])
    return out


def _parse(raw: str) -> tuple[list[dict], dict]:
    import json
    d = json.loads(raw)
    if d.get("errors"):
        raise RuntimeError("GraphQL 报错：%s" % json.dumps(d["errors"], ensure_ascii=False)[:300])
    d0 = (d.get("data") or {}).get("data0") or {}
    code = d0.get("code")
    if code not in (None, "BOOT_0000"):
        raise RuntimeError("读列表失败 code=%s message=%s" % (code, d0.get("message")))
    return _flatten_content((d0.get("data") or {}).get("content")), d0


def list_services(client, app_id: str, *, page_size: int = 200) -> list[dict]:
    """读某应用下的微流程列表（含草稿）。

    ★ 读不到就是读不到：解析失败直接抛，不返回空列表假装成功。
    """
    import json
    js = _LIST_JS % {"op": LIST_OP, "qf": _LIST_QF,
                     "size": page_size, "app": json.dumps(str(app_id))}
    items, _ = _parse(client.evaluate(js, await_promise=True))
    return items


def find_service(client, app_id: str, service_id) -> dict | None:
    """按 id 在列表里定位一条。找不到返回 None（调用方必须当作失败处理）。"""
    sid = str(service_id)
    for it in list_services(client, app_id):
        if str(it.get("id")) == sid:
            return it
    return None


def is_release(svc: dict) -> bool:
    """★ 接口返回的是字符串枚举名 `RELEASE`，不是数字 20。"""
    return str((svc or {}).get("state") or "").upper() == "RELEASE"


def state_of(svc: dict) -> str:
    return str((svc or {}).get("state") or "")


# ───────────────────────── op 名 / 类型名（可执行规则） ─────────────────────────
#
# 反编译来源：boot-starter-graphql 5.3.358
#   GraphQLProvider.pathToCamel          → op 名
#   GraphQLTypeNameUtil.touchName        → GraphQL 类型名
# 详见 core/facts/udc/microflow/graphql-op-naming.md

def _to_camel_case(s: str, capitalize_first: bool = False,
                   delimiters: str = "-/_") -> str:
    """对齐 Apache commons-text CaseUtils 的行为（含开头分隔符特例）。

    ★ 关键：分隔符出现在**开头**（outOffset==0）时不触发下一个字母大写，
      所以 "/udc/microflow/serviceList" → "udcMicroflowServiceList"（首字母小写）。
    """
    if not s:
        return s
    out: list[str] = []
    cap_next = capitalize_first
    for ch in s:
        if ch in delimiters:
            cap_next = True
            if not out:            # outOffset == 0
                cap_next = False
            continue
        if cap_next or (not out and capitalize_first):
            out.append(ch.upper())
            cap_next = False
        else:
            out.append(ch)
    return "".join(out)


def path_to_op_name(path: str, http_method: str = "POST") -> str:
    """元数据 path + httpMethod → GraphQL op 名。

    例：("/udc/microflow/serviceList", "POST") → "udcMicroflowServiceListPost"
    """
    import re

    p = (str(path) + "/" + str(http_method).lower())
    p = p.replace("{", "").replace("}", "")
    p = _to_camel_case(p, False, "-/_")
    p = re.sub(r"[^A-Za-z0-9]", "", p)
    p = re.sub(r"Id$", "", p)              # ★ 先 Id$
    p = re.sub(r"IdGet$", "Get", p)        # ★ 再 IdGet$
    p = re.sub(r"SearchPost$", "Search", p)
    return p


def type_name(dto_full_name: str, app_name: str, is_input: bool = False) -> str:
    """→ GraphQL 类型名（去掉所有非字母数字）。

    例：("com.seeyon.udc.microflow.dto.definition.MicroFlowSubMfDto", "udc")
        → "UdccomseeyonudcmicroflowdtodefinitionMicroFlowSubMfDto"
    """
    import re

    s = _to_camel_case(str(app_name), True, "-") + str(dto_full_name)
    if is_input:
        s += "InputBody"
    return re.sub(r"[^A-Za-z0-9]", "", s)


__all__ = ["list_services", "find_service", "is_release", "state_of",
           "path_to_op_name", "type_name", "LIST_OP",
           "search_services", "find_by_id", "FIND_OP", "SEARCH_OP"]


# ───────────────── 正确的读回 op（LIVE 实测 2026-10-29） ─────────────────
# ★ ServiceListPost 查不到刚 create 的草稿（total=0、只有旧数据）；
#   真正能全量读回（含 DRAFT）的是 udcMicroflowSearch，按 id 查详情用
#   udcMicroflowFindByIdGet。create → 验证必须走这两个。
SEARCH_OP = "udcMicroflowSearch"
FIND_OP = "udcMicroflowFindByIdGet"

_SEARCH_QF = """
code
data {
  content { id name caption description type triggerType state path method hostPath }
}
message
status
"""

_FIND_QF = """
code
data {
  content { id name caption type triggerType state dataSchema }
}
message
status
"""


def search_services(client, app_id: str, *, page_size: int = 999,
                    types: list[str] | None = None) -> list[dict]:
    """用 udcMicroflowSearch 全量读回微流程（含草稿）。★ 创建验证必须走这条。

    params 里 IN_type 限定类型，默认 ["SERVICE", "CUSTOM"]。
    """
    from components.platform_operations.graphql_call import call
    types = types or ["SERVICE", "CUSTOM"]
    r = call(client, SEARCH_OP,
             {"pageInfo": {"needTotal": True, "pageNumber": 1, "pageSize": page_size,
                           "pages": 0, "total": 0},
              "params": {"appId": str(app_id), "IN_type": types}},
             selection=_SEARCH_QF)
    r.require_ok()
    content = r.content
    return content if isinstance(content, list) else []


def find_by_id(client, service_id) -> dict | None:
    """用 udcMicroflowFindByIdGet 按 id 查详情（含 dataSchema）。找不到返回 None。"""
    from components.platform_operations.graphql_call import call_query
    r = call_query(client, FIND_OP, {"id": str(service_id)}, selection=_FIND_QF)
    r.require_ok()
    return r.content if isinstance(r.content, dict) else None
