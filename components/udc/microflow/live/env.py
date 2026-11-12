"""mf.env —— 运行时环境发现。零硬编码：不写死 appId / 实体名 / 流程 id / 字段名。

一切从活着的浏览器和平台接口现查：
  应用   ← 当前编辑器 URL 的 appId 参数（或 store）
  实体   ← udcMicroflowSearchTreeEntityPost 反查，按 label 或 fullName 匹配
  字段   ← udcMicroflowFindDtoByEntityPost 返回的 content.attributes
  流程   ← 当前编辑器 URL 的路径末段（mid）
  凭证   ← CDP Network.getAllCookies（浏览器里的真 cookie，不用外部文件）

用法：
    from components.udc.microflow.live import env
    ctx = env.Context.load()          # 自动发现
    ctx.app_id, ctx.app_name          # 8704...
    ctx.entity("实体标题或 fullName")   # Entity 对象，带 fields
    ctx.fields                        # {name: Field}
"""
import json
import os
import re
import urllib.request


# ---------------------------------------------------------------- 基础配置

def base_url():
    """平台根地址。默认 localhost:3000，可用 UDC_BASE 覆盖。"""
    return os.environ.get("UDC_BASE", "http://localhost:3000").rstrip("/")


def cdp_url():
    return os.environ.get("UDC_CDP", "http://127.0.0.1:9222")


# ---------------------------------------------------------------- 凭证

def cookies_from_cdp(host=None):
    """从浏览器 CDP 直接取 cookie —— 永远是最新的，不需要外部文件。

    注意：Network.getAllCookies 返回**整个浏览器**所有域名的 cookie（上百个）。
    必须按平台 host 过滤，否则请求头膨胀到服务端直接 400。
    """
    if host is None:
        host = re.sub(r"^https?://", "", base_url()).split(":")[0].split("/")[0]
    raw = json.loads(urllib.request.urlopen(
        cdp_url() + "/json/list", timeout=5).read().decode())
    ws = next((t["webSocketDebuggerUrl"] for t in raw
               if t.get("type") == "page" and t.get("url", "").startswith(base_url())), None)
    if not ws:
        raise RuntimeError("没有打开发着平台页面的 tab，先在浏览器里打开 UDC 应用")
    import websockets.sync.client as wsc
    with wsc.connect(ws, max_size=64 * 1024 * 1024) as c:
        c.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
        while True:
            m = json.loads(c.recv())
            if m.get("id") == 1:
                out = {}
                for ck in m["result"]["cookies"]:
                    dom = (ck.get("domain") or "").lstrip(".")
                    if dom == host or dom.endswith("." + host) or host.endswith(dom):
                        out[ck["name"]] = ck["value"]
                return out


def cookie_header(ctx=None):
    """Cookie 头。优先 CDP 现取（含续期后的新 token），失败退回凭据文件。"""
    if ctx is not None and getattr(ctx, "_cookie", None):
        return ctx._cookie
    try:
        ck = cookies_from_cdp()
    except Exception:
        p = os.environ.get("UDC_COOKIE_FILE")
        if not p or not os.path.exists(p):
            raise RuntimeError("取不到 cookie：CDP 不可用且未配置 UDC_COOKIE_FILE")
        ck = json.load(open(p, encoding="utf-8"))
    return "; ".join("%s=%s" % (k, v) for k, v in ck.items())


# ---------------------------------------------------------------- 接口

def gql(op, variables, query, ctx=None):
    body = json.dumps({"query": query, "variables": {"p": variables}}).encode()
    req = urllib.request.Request(
        base_url() + "/service/udc/graphql?" + op, data=body,
        headers={"Content-Type": "application/json", "Cookie": cookie_header(ctx)})
    return json.loads(urllib.request.urlopen(req, timeout=90).read().decode())


def rest(path, body=None, ctx=None, method=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        base_url() + path, data=data, method=method,
        headers={"Content-Type": "application/json", "Cookie": cookie_header(ctx)})
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode() or "{}")


def content(r):
    """剥 GraphQL 信封，取 data.data0.data.content（平台统一形状）。"""
    d0 = (r.get("data") or {}).get("data0")
    if not isinstance(d0, dict):
        return None
    d = d0.get("data")
    return d.get("content") if isinstance(d, dict) else d


def gql_page(d, op, variables, query):
    """在页面内 fetch GraphQL，自动带浏览器会话（避免本机 cookie 不全导致 403）。

    返回 {status, body, json}；GraphQL 业务错误也原样保留，不把 HTTP 200 当成功。
    """
    expr = """(async () => {
      const r = await fetch('/service/udc/graphql?%s', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: %s, variables: {p: %s}})
      });
      const body = await r.text();
      let parsed = null;
      try { parsed = JSON.parse(body); } catch (e) {}
      return JSON.stringify({status: r.status, body, json: parsed});
    })()""" % (op, json.dumps(query), json.dumps(variables))
    raw = d.eval(expr, await_promise=True)
    if not isinstance(raw, str):
        return {"status": None, "body": str(raw), "json": None}
    out = json.loads(raw)
    return out


def read_schema_page(d, mid):
    """页面内回读流程 dataSchema，返回 (meta, schema)。调用方仍需递归遍历嵌套节点。"""
    q = ("query graphqlLoader ($p: udcMicroflowFindByIdGetInputPath) "
         "{ data0: udcMicroflowFindByIdGet(path: $p) { code data { content { id dataSchema } } } }")
    r = gql_page(d, "udcMicroflowFindByIdGet", {"id": str(mid)}, q)
    if r.get("status") != 200 or not r.get("json"):
        return None, None
    c = content(r["json"]) or {}
    ds = c.get("dataSchema")
    if isinstance(ds, str):
        ds = json.loads(ds)
    return c, ds


# ---------------------------------------------------------------- 数据类

class Field:
    """实体属性。全部字段从接口现拿，不预设。"""
    __slots__ = ("name", "caption", "data_type", "java_type", "attr_id",
                 "source_type", "raw", "dto")

    def __init__(self, dto, raw):
        self.dto = dto
        self.raw = raw
        self.name = raw.get("name")
        self.caption = raw.get("caption") or raw.get("name")
        self.data_type = raw.get("dataType")
        self.java_type = raw.get("javaType")
        self.source_type = raw.get("sourceType")
        self.attr_id = str((raw.get("customs") or {}).get("id") or raw.get("id") or "")

    def left_param(self):
        """RETRIEVE 等节点过滤条件的 leftParam（前端编辑后保存的形态）。"""
        return {"id": "%s.%s" % (self.dto, self.name), "type": "OBJECT",
                "javaType": self.java_type, "dto": "_" + self.name, "field": self.name,
                "desc": self.caption, "dataType": self.data_type, "multiSelect": False}

    def attr_type(self):
        """sortParams.attrType（创建变量 OTHER / 排序规则用）。"""
        raw = dict(self.raw)
        raw.setdefault("validate", True)
        raw.setdefault("id", "%s.%s" % (self.dto, self.name))
        raw.setdefault("fullName", "%s.%s" % (self.dto, self.name))
        raw.setdefault("type", "OBJECT")
        raw.setdefault("multiSelect", False)
        return raw

    def __repr__(self):
        return "<Field %s %s>" % (self.name, self.data_type)


class Entity:
    __slots__ = ("ctx", "entity_id", "label", "dto", "full_name", "domain", "_fields")

    def __init__(self, ctx, raw):
        self.ctx = ctx
        self._fields = None
        # 真实响应键名（udcMicroflowSearchTreeEntityPost 实测）：
        #   caption=中文名  fullName=domain 全名  dtoFullName=DTO 全名  relationEntity=实体数字 id
        self.label = raw.get("caption") or raw.get("label") or raw.get("title")
        self.domain = raw.get("fullName") or raw.get("key") or raw.get("entity") or ""
        self.dto = raw.get("dtoFullName") or (
            raw.get("id") if _looks_like_dto(raw.get("id")) else "") or raw.get("javaType") or ""
        self.full_name = self.domain
        self.entity_id = str(raw.get("relationEntity") or raw.get("entityId")
                             or (raw.get("customs") or {}).get("id") or raw.get("id") or "")

    @property
    def fields(self):
        if self._fields is None:
            self._fields = self.ctx.load_fields(self)
        return self._fields

    def field(self, name_or_caption):
        """按字段名或中文标题取字段 —— 两种都支持，避免脚本里写死英文名。"""
        f = self.fields.get(name_or_caption)
        if f:
            return f
        for x in self.fields.values():
            if x.caption == name_or_caption:
                return x
        raise KeyError("%s 没有字段 %r，现有：%s"
                       % (self.label, name_or_caption, list(self.fields)))

    @property
    def structure(self):
        """节点结构里的 structure 段（创建变量 / RETRIEVE 共用）。"""
        return {"key": self.domain, "id": self.dto, "label": self.label,
                "dataType": "DTO", "entity": self.domain, "dtoType": "MASTER_ENTITY",
                "udcApp": True, "fullName": self.dto, "relationEntity": self.entity_id,
                "methodLegal": {"available": True, "complexCondition": True,
                                "seniorMethod": True, "serviceType": "NONE",
                                "interfaceClassFullName": None}}

    def __repr__(self):
        return "<Entity %s %s>" % (self.label, self.entity_id)


def _looks_like_dto(v):
    return isinstance(v, str) and "." in v


# ---------------------------------------------------------------- 上下文

class Context:
    """一次探测的根上下文：app + 当前流程 + 缓存。"""

    # GraphQL 调用契约（来自前端 bundle `udcMutationLoader` 的 load 定义，不是猜的）：
    #   paramsType 以 InputBody 结尾 → mutation + body: $p
    #   paramsType 以 InputPath 结尾 → query    + path: $p
    # 变量类型名 = 接口名 + InputBody / InputPath。
    ENT_QUERY = ("mutation graphqlLoader ($p: udcMicroflowSearchTreeEntityPostInputBody) "
                 "{ data0: udcMicroflowSearchTreeEntityPost(body: $p) { code data { content } } }")
    DTO_QUERY = ("mutation graphqlLoader ($p: udcMicroflowFindDtoByEntityPostInputBody) "
                 "{ data0: udcMicroflowFindDtoByEntityPost(body: $p) { code data { content } } }")
    GET_QUERY = ("query graphqlLoader ($p: udcMicroflowFindByIdGetInputPath) "
                 "{ data0: udcMicroflowFindByIdGet(path: $p) { code data { content { id dataSchema } } } }")

    def __init__(self):
        self.app_id = None
        self.app_name = None
        self.app_caption = None
        self.mid = None
        self.editor_url = None
        self._cookie = None
        self._entities = {}
        self._schema_cache = {}

    # -- 发现 ------------------------------------------------------------

    @classmethod
    def load(cls, app_id=None, mid=None):
        c = cls()
        c._cookie = cookie_header()
        url = c.current_editor_url()
        c.editor_url = url
        if url:
            m = re.search(r"[?&]appId=(\d+)", url)
            if m:
                c.app_id = m.group(1)
            m2 = re.search(r"/microflow/editor/(-?\d+)", url)
            if m2:
                c.mid = m2.group(1)
        c.app_id = app_id or c.app_id
        c.mid = mid or c.mid
        if c.app_id:
            c.resolve_app()
        return c

    def current_editor_url(self):
        raw = json.loads(urllib.request.urlopen(
            cdp_url() + "/json/list", timeout=5).read().decode())
        for t in raw:
            u = t.get("url", "")
            if "/microflow/editor/" in u:
                return u
        return None

    def resolve_app(self):
        """解析 appName（= 包前缀，DTO 全名靠它拼）。

        平台所有 UDC 类的全名都是 `com.seeyon.<appName>.<...>`，
        所以 appName 可以从流程 schema 里出现的任意 DTO/实体全名反推，
        不需要额外的 application 查询接口（没有稳定的 operation 名）。
        顺序：节点 app 引用 → 流程 schema 正则 → 实体树正则。
        """
        # 1) 页面 store 里的 app 引用（节点 app 字段带 appName + caption）
        try:
            from .cdp import Driver
            d = Driver()
            d.attach()
            got = d.eval(r"""(() => {
              const st = appReduxStore.getState().appDesign.microflowEditorReducer;
              const seen = new Set();
              const walk = (ns) => (ns || []).forEach(n => {
                const a = n && n.app;
                if (a && a.appName) seen.add(a.appName + '|' + (a.caption || ''));
                walk(n && n.nodes);
                (n && n.conditions || []).forEach(c => walk(c.nodes));
              });
              walk(st.flowNodes);
              return JSON.stringify([...seen]);
            })()""")
            d.close()
            arr = json.loads(got) if isinstance(got, str) else []
            if arr:
                name, _, cap = arr[0].partition("|")
                self.app_name, self.app_caption = name, (cap or None)
        except Exception:
            pass

        # 2) 流程 schema 里的 com.seeyon.<pkg>. 正则
        if not self.app_name and self.mid:
            try:
                raw = json.dumps(self.read_schema(), ensure_ascii=False)
                m = re.search(r"com\.seeyon\.([A-Za-z0-9_]+)\.", raw)
                if m:
                    self.app_name = m.group(1)
            except Exception:
                pass

        # 3) 实体树正则（appName 未知时接口会报 UDC_MICROFLOW_0024，故放最后）
        if not self.app_name:
            try:
                raw = json.dumps(self._raw_entities(""), ensure_ascii=False)
                m = re.search(r"com\.seeyon\.([A-Za-z0-9_]+)\.", raw)
                if m:
                    self.app_name = m.group(1)
            except Exception:
                pass
        return self

    # -- 实体 ------------------------------------------------------------

    def _raw_entities(self, app_name=None):
        body = {"appId": self.app_id,
                "appName": self.app_name if app_name is None else app_name,
                "needChildren": True, "needThirdEntity": False,
                "serviceType": "SELECT_LIST_BY_COMPLEX_CONDITIONS"}
        r = gql("udcMicroflowSearchTreeEntityPost", body, self.ENT_QUERY, self)
        return list(_walk_entities(content(r)))

    def entities(self, only_current_app=True):
        """当前应用可选的实体全集。"""
        if not self._entities:
            for item in self._raw_entities():
                e = Entity(self, item)
                if e.label:
                    self._entities[e.label] = e
                    if e.dto:
                        self._entities[e.dto] = e
        return self._entities

    def entity(self, key):
        self.entities()
        if key in self._entities:
            return self._entities[key]
        # 允许只给类名尾段
        for k, v in self._entities.items():
            if isinstance(k, str) and (k.endswith(key) or key in k):
                return v
        raise KeyError("找不到实体 %r，可选：%s"
                       % (key, sorted({v.label for v in self._entities.values()})))

    def load_fields(self, ent):
        """拉实体全部属性（含数字 attr id、md5）。"""
        body = {"appId": self.app_id, "appName": self.app_name,
                "entityFullName": ent.domain or ent.dto}
        r = gql("udcMicroflowFindDtoByEntityPost", body, self.DTO_QUERY, self)
        c = content(r) or {}
        attrs = c.get("attributes") or {}
        if isinstance(attrs, list):
            attrs = {a.get("name"): a for a in attrs}
        return {k: Field(ent.dto, v) for k, v in attrs.items() if isinstance(v, dict)}

    # -- 流程 ------------------------------------------------------------

    def read_schema(self, mid=None):
        """回读流程 dataSchema —— 一切「是否真落库」的唯一判据。"""
        mid = mid or self.mid
        r = gql("udcMicroflowFindByIdGet", {"id": mid}, self.GET_QUERY, self)
        c = content(r) or {}
        ds = c.get("dataSchema")
        if isinstance(ds, str):
            ds = json.loads(ds)
        self._schema_cache[mid] = (c, ds)
        return ds

    def flow_meta(self, mid=None):
        mid = mid or self.mid
        if mid not in self._schema_cache:
            self.read_schema(mid)
        return self._schema_cache[mid][0]

    def nodes(self, mid=None):
        return ((self.read_schema(mid) or {}).get("nodes") or [])

    def find_nodes(self, action_type, mid=None):
        """按 actionType 找节点，支持递归进分支/循环子链。"""
        out = []

        def walk(ns):
            for n in ns or []:
                if n.get("actionType") == action_type or n.get("type") == action_type:
                    out.append(n)
                walk(n.get("nodes"))
                for c in n.get("conditions") or []:
                    walk(c.get("nodes"))
        walk(self.nodes(mid))
        return out

    def __repr__(self):
        return "<Context app=%s(%s) mid=%s>" % (self.app_caption, self.app_id, self.mid)


def _walk_entities(node):
    """实体树是嵌套的（应用 → 实体 / 分组 → 实体），拍平。

    实测每个实体项的特征键：caption + dtoFullName + relationEntity。
    """
    if isinstance(node, list):
        for x in node:
            yield from _walk_entities(x)
        return
    if not isinstance(node, dict):
        return
    if node.get("dtoFullName") and node.get("caption"):
        yield node
        return
    for k in ("children", "entities", "data"):
        if k in node:
            yield from _walk_entities(node[k])
