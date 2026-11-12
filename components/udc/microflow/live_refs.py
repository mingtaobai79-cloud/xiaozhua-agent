"""活引用解析层：所有外部引用运行时从环境拉取，禁止写死。

解析器（每个都走前端同款候选集接口）：
- entity(app_id, dto_full)          → udcMicroflowSearchTreeEntityPost（实体+methodLegal）
- sub_mf_candidates(app_id)         → udcMicroflowServiceListSubMfPost（可引用子微流程）
- app_service_methods(app_name)     → searchApps / searchMethodByName（自定义服务）
- data_flow_rules(app_id)           → 数据流程/生单规则列表

缓存：进程内 dict（同一次生成里不重复拉）。
失败即抛：查不到就不许生成（G7 语义）。
"""
from __future__ import annotations

import json


class LiveRefs:
    def __init__(self, host: str, cookie: str):
        self.host = host.rstrip("/")
        self.cookie = cookie
        self._cache: dict[str, object] = {}

    # ---- 底层 ----
    def _gql(self, op: str, body: dict, query: str, timeout: int = 90):
        """★ 走 deploy._req（curl 传输）：本环境网关对 urllib 的 TLS 指纹
        间歇性 EOF，curl 稳定。见 facts/udc/microflow/expression-engine.md §一。"""
        from .deploy import _req
        return _req(self.host, "/service/udc/graphql?" + op,
                    {"query": query, "variables": {"p": body}}, self.cookie, timeout)

    def _content(self, r):
        d0 = (r.get("data") or {}).get("data0")
        if not isinstance(d0, dict):
            return None
        d = d0.get("data")
        return d.get("content") if isinstance(d, dict) else d

    # ---- 实体（含 methodLegal / md5 属性表）----
    def entity(self, app_id: str, app_name: str) -> list[dict]:
        """返回应用下全部可选实体（children 递归拍平）。"""
        key = "entities:" + app_id
        if key in self._cache:
            return self._cache[key]  # type: ignore[return-value]
        q = ("mutation g($p: udcMicroflowSearchTreeEntityPostInputBody) { data0: "
             "udcMicroflowSearchTreeEntityPost(body: $p) { code data { content } message } }")
        body = {"appId": app_id, "appName": app_name, "needChildren": True,
                "needThirdEntity": False,
                "serviceType": "SELECT_LIST_BY_COMPLEX_CONDITIONS"}
        r = self._gql("udcMicroflowSearchTreeEntityPost", body, q)
        cc = self._content(r) or []

        flat: list[dict] = []

        def walk(nodes):
            for n in nodes or []:
                if isinstance(n, dict):
                    flat.append(n)
                    walk(n.get("children"))

        walk(cc)
        self._cache[key] = flat
        return flat

    def find_entity(self, app_id: str, app_name: str, *, label: str = "",
                    dto_full: str = "") -> dict:
        """按 label 或 dtoFullName 定位一个实体，找不到抛错（G7）。"""
        for e in self.entity(app_id, app_name):
            if dto_full and (e.get("dtoFullName") == dto_full
                             or e.get("fullName") == dto_full):
                return e
            if label and e.get("caption") == label:
                return e
        raise LookupError("实体不存在: label=%r dto=%r（G7 引用存活闸门）" % (label, dto_full))

    # ---- 可引用子微流程 ----
    def sub_mf_candidates(self, app_id: str) -> list[dict]:
        """SERVICE/CUSTOM 型全部微流程（SUB_MICROFLOW 可引用的候选集）。"""
        key = "submfs:" + app_id
        if key in self._cache:
            return self._cache[key]  # type: ignore[return-value]
        q = ("mutation g($p: udcMicroflowSearchInputBody) { data0: udcMicroflowSearch"
             "(body: $p) { code data { content { id name caption state type } } message } }")
        body = {"pageInfo": {"needTotal": True, "pageNumber": 1, "pageSize": 999,
                             "pages": 0, "total": 0},
                "params": {"appId": app_id, "IN_type": ["SERVICE", "CUSTOM"]}}
        items = self._content(self._gql("udcMicroflowSearch", body, q)) or []
        # 只收 RELEASE（DRAFT 不可被正式流程引用）
        alive = [it for it in items if it.get("state") == "RELEASE"]
        self._cache[key] = alive
        return alive

    def find_sub_mf(self, app_id: str, name: str = "", mf_id: str = "") -> dict:
        for it in self.sub_mf_candidates(app_id):
            if mf_id and str(it.get("id")) == str(mf_id):
                return it
            if name and it.get("name") == name:
                return it
        raise LookupError("可引用子微流程不存在(须 RELEASE): name=%r id=%r（G7）" % (name, mf_id))

    def microflow_detail(self, mf_id: str) -> dict:
        """读子流程完整定义，取出**当前真实的**入参/出参契约。

        ★ 为什么必须读：`sub_mf_candidates` 只回 id/name/caption/state/type，
          不含 input/output。而 SUB_MICROFLOW 节点的 `mfService` 必须与子流程
          当前契约逐字一致，否则发布时 `checkMfService` 报 `MICRO_FLOW_CHANGE`
          （比对 mfService.input/output 与子流程 schema 里的 input/output）。
        """
        key = "mfd:" + str(mf_id)
        if key in self._cache:
            return self._cache[key]  # type: ignore[return-value]
        from .deploy import get as _get
        from .deploy import _req  # noqa: F401  (确保走 curl 传输)
        rec = _get(self.host, self.cookie, mf_id)
        raw_schema = rec.get("dataSchema")
        if not raw_schema:
            raise ValueError("microflow dataSchema missing; contract UNVERIFIED")
        ds = json.loads(raw_schema)
        if not isinstance(ds, dict) or "input" not in ds or "output" not in ds:
            raise ValueError("microflow dataSchema input/output missing; contract UNVERIFIED")
        out = {"id": str(rec.get("id") or mf_id), "name": rec.get("name"),
               "caption": rec.get("caption"), "state": rec.get("state"),
               "triggerType": rec.get("triggerType") or ds.get("trigger", {}).get("type"),
               "input": ds.get("input"), "output": ds.get("output")}
        self._cache[key] = out
        return out

    # ---- 实体模型适配：LiveRefs 输出 → 构造器可消费的 entity dict ----
    def entity_model(self, app_id: str, app_name: str, *, label: str = "",
                     dto_full: str = "") -> dict:
        """把活引用实体 + 属性表，适配成 components/construction 构造器要的形态。

        ★ 为什么必须适配：LiveRefs.find_entity 返回的是**实体树节点**（9 键），
          而构造器（microflow_fields.entity_structure / field_attr）要的是
          **实体模型**（6 键 + attributes 字典）。两者键名还不完全一致：

            LiveRefs 的 fullName      = domain 全名（...domain.entity.YsFull6956）
            构造器的 entity["fullName"] = **DTO 全名**（entity_structure 里当 dto 用）
            构造器的 entity["entity"]   = domain 全名

          直接把 LiveRefs 的 dict 喂给构造器，会造出 dto=domain 的错引用。
          这个转换只做一次，放在活引用层，构造器不再关心来源。

        attributes 需要额外调 udcMicroflowFindCustomDtoPost 拉（树节点不含属性表）。
        """
        ent = self.find_entity(app_id, app_name, label=label, dto_full=dto_full)
        dto = ent.get("dtoFullName") or ent.get("fullName")
        domain = ent.get("fullName")
        return {
            "fullName": dto,                                   # 构造器当 DTO 全名用
            "entity": domain,                                  # domain 全名
            "caption": ent.get("caption"),
            "relationEntityId": str(ent.get("relationEntity") or ""),
            "refApp": app_name,
            "dtoType": ent.get("dtoType") or "MASTER_ENTITY",
            "udcApp": ent.get("udcApp", True),
            "methodLegal": ent.get("methodLegal"),
            "attributes": self.dto_attributes(app_id, app_name, dto),
        }

    def dto_attributes(self, app_id: str, app_name: str, dto_full: str) -> dict:
        """拉 DTO 的字段表，键为字段名（构造器按 entity["attributes"][name] 取）。"""
        key = "attrs:" + dto_full
        if key in self._cache:
            return self._cache[key]  # type: ignore[return-value]
        q = ("mutation g($p: udcMicroflowFindCustomDtoPostInputBody) { data0: "
             "udcMicroflowFindCustomDtoPost(body: $p) { code data { content } message } }")
        r = self._gql("udcMicroflowFindCustomDtoPost",
                      {"appId": app_id, "appName": app_name,
                       "dtoFullName": dto_full, "needChildren": False}, q)
        cc = self._content(r) or {}
        raw = cc.get("attributes") or {}
        # 属性表可能是 dict{name: attr} 或 list[attr]
        if isinstance(raw, list):
            raw = {a.get("name"): a for a in raw if isinstance(a, dict)}
        self._cache[key] = raw
        return raw

    # ---- 自定义服务 ----
    def app_service_method(self, app_id: str, app_name: str, method_full: str) -> dict:
        """按方法全名取真实签名（selectMethod，含 md5/parameter/returnValue）。

        契约：udcMicroflowSearchMethodByNamePost
        body: {appId, appName, dtoFullName=<方法全名>, methodFullName=<方法全名>}
        出处：core/facts/udc/microflow/custom-service-api.md §3 / api-catalog.md
        """
        key = "svc:" + method_full
        if key in self._cache:
            return self._cache[key]  # type: ignore[return-value]
        q = ("mutation g($p: udcMicroflowSearchMethodByNamePostInputBody) { data0: "
             "udcMicroflowSearchMethodByNamePost(body: $p) "
             "{ code data { content } message } }")
        body = {"appId": app_id, "appName": app_name,
                "dtoFullName": method_full, "methodFullName": method_full}
        try:
            cc = self._content(self._gql("udcMicroflowSearchMethodByNamePost", body, q))
        except Exception as exc:
            raise LookupError("服务方法查询失败: %s（G7）— %s" % (method_full, exc))
        item = cc if isinstance(cc, dict) else None
        if not item or not item.get("fullName"):
            raise LookupError("服务方法不存在: %s（G7）" % method_full)
        self._cache[key] = item
        return item

    def data_flow_candidates(self, app_id: str, source_entity_id: str) -> list[dict]:
        """按来源实体查可用生单规则（udcDataFlowListManuallyMappingPost）。
        返回行含 appId/appUrl/caption/id/name/sourceEntityId。"""
        op = "udcDataFlowListManuallyMappingPost"
        q = ("query g($p: %sInputBody) { data0: %s(body: $p) "
             "{ code data { content } message } }" % (op, op))
        r = self._gql(op, {"appId": app_id, "sourceEntityId": source_entity_id}, q)
        return self._content(r) or []
