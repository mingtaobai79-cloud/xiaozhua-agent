"""xiaozhua Agent 宿主初始化 —— 供 Hermes / Claude Code / Codex 等 agent 框架嵌入的唯一入口。

用法（宿主 agent 的初始化脚本/工具里一行调用）:
    from xiaozhua_host_bootstrap import bootstrap
    agent = bootstrap(credential_file="<PATH>")   # 活体
    agent = bootstrap()                                                      # 离线（只读证据面）

返回的 dict 即宿主可用的能力注册表：
  - agent:      装配好的 XiaozhuaAgent（宿主可注入 context/session/policy）
  - dispatch:   需求 → 路由 → 组件执行 → 证据化结果
  - live_probe: test2 只读 POST 活体探测（默认关，allow_network=True 才联网）
  - generate:   需求(实体+属性) → 后端 8 类 Java 骨架 + 前端页面定义
  - op_execute: 契约化只读平台操作（PlatformOperationLayer）
安全边界：默认离线只读；写操作一律 DENIED；凭据仅路径引用、值 0 落盘。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent


def _find_rules_dir() -> Path:
    """定位 construction-rules 目录。

    两种布局都要支持：
      - 源码树 / git clone：`<root>/docs/construction-rules`
      - pip 装成 wheel：`<site-packages>/xiaozhua_agent_data/construction-rules`
        （docs/ 不是 Python 包，装不进去，所以打包时复制了一份进 xiaozhua_agent_data）

    都找不到就抛带路径的错 —— 不要静默用空规则生成错误骨架。
    """
    candidates = [
        _REPO_ROOT / "docs" / "construction-rules",
        _REPO_ROOT / "xiaozhua_agent_data" / "construction-rules",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    raise FileNotFoundError(
        "找不到 construction-rules，试过：%s\n"
        "源码树请确认仓库完整；pip 安装请确认 xiaozhua_agent_data 已随包安装。"
        % " , ".join(str(c) for c in candidates)
    )


def _entity_rule_publish_flow(_post, dto: dict):
    """规则发布的两步流程，与传输方式无关（curl / 页面 fetch 共用）。

    ★ 顺序固定：checkSchema 先 → 判据过了才 create。
    ★ 判据是 content.check==true 且 errors==0，不看 code：
      BOOT_0000 也可能 check=False。
    ★ 校验不过就不 create —— 平台本身不拦，会留一条空条件规则。
    """
    body = dict(dto)
    chk = _post("/service/udc/microflow/checkSchema", body)
    # ★ content 在 data.content，不在顶层 —— 取顶层永远拿到 None，
    #   于是 check=None 被判成"校验不通过"，create 一次都没执行过。
    content = (chk.get("data") or {}).get("content")
    if content is None:
        content = chk.get("content") or {}
    try:
        n_err = int(content.get("errors") or 0)
    except (TypeError, ValueError):
        n_err = 1
    if not (bool(content.get("check")) and n_err == 0):
        return {"ok": False, "stage": "checkSchema",
                "code": chk.get("code"), "check": content.get("check"),
                "errors": content.get("errors"),
                "errorMessage": content.get("errorMessage"),
                "note": "校验未通过，未执行 create（避免库里留空条件规则）"}
    cr = _post("/service/udc/microflow/create", body)
    if cr.get("code") != "BOOT_0000":
        return {"ok": False, "stage": "create",
                "code": cr.get("code"), "message": cr.get("message")}
    rid = (cr.get("data") or {}).get("content", cr.get("content"))
    return {"ok": True, "stage": "done", "ruleId": str(rid),
            "check": True, "errors": 0}


def _expression_filter_flow(be, F, dto_full, list_desc, entity_model,
                            *, field="", op="GT", const=None, spec=None, title=""):
    """FILTER 表达式构造的纯流程，与传输后端无关。"""
    if spec is not None:
        ast = F.parse_filter_spec(spec, dto_full=dto_full,
                                  list_desc=list_desc, entity_model=entity_model)
        return F.build_ast_expression(dto_full=dto_full, list_desc=list_desc,
                                      entity_model=entity_model, ast=ast,
                                      backend=be, title=title or None)
    if not field:
        raise ValueError("必须给 field（简单形态）或 spec（AST 形态）")
    return F.build_filter_expression(dto_full=dto_full, list_desc=list_desc,
                                     entity_model=entity_model, field=field,
                                     op=op, const=const, backend=be)


def _expression_backend(host: str, cookie: str, cdp_port: int):
    """表达式接口的传输后端。

    cdp_port > 0 → PageBackend：请求由页面发，cookie 不离开浏览器（首选）
    否则         → CurlBackend：直接带 Cookie 头
    """
    from components.udc.microflow.expression_transport import CurlBackend, PageBackend
    if not cdp_port:
        return CurlBackend(host, cookie)

    from providers.cdp import CdpClient
    from components.transport.page_fetch import PageFetch

    pf = PageFetch(int(cdp_port))

    class _Driver:
        """PageBackend 要 driver.eval(expr, await_promise=)，这里适配到 PageFetch。"""
        def __init__(self, fetch):
            self._f = fetch

        def eval(self, expr: str, await_promise: bool = False):
            return self._f._eval(expr)

    class _Backend(PageBackend):
        """既有 PageBackend 的 _post/check/transform，也直接当 driver 用。

        expression_api 里有两套调用方式：一部分走 backend.check/transform，
        一部分把 backend 当 driver 直接调 .eval()。两者都要满足。
        """
        def __init__(self, fetch):
            self._f = fetch
            super().__init__(_Driver(fetch))

        def eval(self, expr: str, await_promise: bool = False):
            return self._f._eval(expr)

        def close(self):
            self._f.close()

    _Backend._f = pf
    return _Backend(pf)


def bootstrap(*, credential_file: str | None = None, allow_network: bool = False,
              audit_dir: str | None = None) -> dict[str, Any]:
    # --- 组件装配（宿主可覆盖 policy/context/session，见 core/agent.py 三个 Port） ---
    from core.agent import XiaozhuaAgent, AgentRequest, MemoryContext, MemorySession, ReadOnlyPolicy
    from core.registry import ComponentRegistry
    from components.udc.component import UdcComponent
    from components.runtime.component import RuntimeComponent
    from components.integration.component import IntegrationComponent
    from components.construction import (
        ConstructionEvaluator, ConstructionRuleRegistry, ConstructionEngine, ConstructionTask,
        NormalizedEntityModel, JavaSkeletonRenderer, PageDefinitionRenderer,
    )

    comps = ComponentRegistry([UdcComponent(audit_dir=audit_dir), RuntimeComponent(), IntegrationComponent()])
    agent = XiaozhuaAgent(comps)

    # --- 生成面 ---
    _rules = ConstructionRuleRegistry(_find_rules_dir()).load()
    _engine = ConstructionEngine(ConstructionEvaluator(_rules))
    _renderer = JavaSkeletonRenderer()

    def generate(application_id: str, entity_name: str, attributes: list[dict] | None = None,
                 caption: str | None = None) -> dict[str, Any]:
        """需求 → 后端 8 类 Java 骨架 + 前端页面定义（声明级，方法体 UNVERIFIED）。"""
        model = NormalizedEntityModel(application_id, None, entity_name,
                                      attributes or [], caption=caption)
        plan = _engine.evaluate(ConstructionTask(model=model)).plan
        sources = _renderer.render(plan, model)
        page = PageDefinitionRenderer(application_id).render(model)
        return {
            "status": "PASS" if sources and not plan.blocked else "UNVERIFIED",
            "backend": {
                "schema": plan.schema,
                "artifacts": [s.to_dict() if hasattr(s, "to_dict") else {
                    "artifact_type": s.artifact_type, "relative_path": s.relative_path} for s in sources],
                "sources": {s.relative_path: s.source for s in sources},
            },
            "frontend": page.to_dict(),
            "plan_warnings": plan.warnings,
            "plan_blocked": plan.blocked,
        }

    # --- 需求解析 → 生成（语义层入口：宿主 LLM 圈实体/字段后走这里结构化） ---
    from components.construction.requirement_parser import RequirementParser
    _parser = RequirementParser()

    def generate_from_requirement(text: str, application_id: str) -> dict[str, Any]:
        """自然语言需求 → 实体模型（确定性解析）→ 后端骨架 + 前端页面定义。"""
        parsed = _parser.parse(text, application_id)
        if parsed["status"] == "UNVERIFIED":
            return {"status": "UNVERIFIED", "reason": parsed.get("reason", ""),
                    "unknowns": parsed.get("unknowns", []), "schema": parsed.get("schema", "")}
        model = parsed["model"]
        plan = _engine.evaluate(ConstructionTask(model=model)).plan
        sources = _renderer.render(plan, model)
        page = PageDefinitionRenderer(application_id).render(model)
        return {
            "status": "PASS" if sources and not plan.blocked else "UNVERIFIED",
            "parsed": {"entity_name": model.entity_name, "caption": model.caption,
                       "attributes": [a if isinstance(a, dict) else getattr(a, "to_dict", lambda: {})() for a in model.attributes],
                       "unknowns": parsed["unknowns"]},
            "backend": {
                "schema": plan.schema,
                "sources": {s.relative_path: s.source for s in sources},
            },
            "frontend": page.to_dict(),
            "plan_blocked": plan.blocked,
        }

    # --- 活体只读探测（test2 4 端点）---
    def live_probe(cred_file: str | None = None) -> dict[str, Any]:
        cf = cred_file or credential_file
        if not cf:
            return {"status": "SKIPPED", "reason": "no credential file provided"}
        if not allow_network:
            return {"status": "BLOCKED", "reason": "allow_network=False (default offline)"}
        from components.gateway import GatewayReadonlyClient
        from components.platform_operations import LiveReadonlyRunner, make_cookie_headers_resolver
        credential = json.loads(Path(cf).read_text(encoding="utf-8-sig"))
        base_url = credential.get("base", "")
        app_id = credential.get("app_id", "")
        prefix = credential.get("gateway_prefix") or f"/service/{app_id}"
        client = GatewayReadonlyClient(base_url=base_url, allow_network=True, timeout=30.0)

        class _P:
            def __init__(self, c): self._c = c
            @property
            def base_url(self): return self._c.base_url
            def post(self, path, *, body=None, headers=None):
                return self._c.post(prefix.rstrip("/") + "/" + path, body=body, headers=headers)

        return LiveReadonlyRunner(_P(client), make_cookie_headers_resolver(credential), app_id).run()

    # --- 设计态部署方案（建实体→建属性→RELEASE 构建→物理表；只出方案 data，宿主执行）---
    def deploy_plan(application_id: str, entity_name: str, attributes: list[dict],
                    caption: str | None = None, stereotype: str = "bill",
                    deploy_type: str = "RELEASE") -> dict[str, Any]:
        """生成可执行的部署方案 data（readonly_plan=True）。

        agent 不出写（写门 DENIED）；宿主按 steps 顺序调真实端点执行并 verify。
        证据见 components/platform_operations/deployment.py 与各 step 的 evidence。
        """
        from components.platform_operations.deployment import build_deployment_plan
        return build_deployment_plan(
            application_id, entity_name, caption or entity_name,
            attributes, stereotype=stereotype, deploy_type=deploy_type)

    # --- 需求入口 ---
    def dispatch(intent: str, target: str | None = None) -> dict[str, Any]:
        return agent.dispatch(AgentRequest(intent, {"target": target or "request"}))

    # --- 生成面（声明级 body data，宿主执行；不新增网络/写能力）---
    def _entity_meta(meta: dict, entity_name: str, app_id: str) -> dict:
        """补齐 entity 六件套缺省占位。

        审计纪律：可从输入推导的（name/caption/appName/appId）就填推导值；
        推不出的（fullName 深包结构）必须出明显占位符，绝不臆造 plausible 假值——
        证据：真实 fullName 是 `com.seeyon.<pkg>.domain.entity.<Pascal>` 深包名，
        离线无从推起；appId 按 skill「app name 末尾数字段即 appId」提取数字。
        """
        import re
        m = re.search(r"(\d+)$", str(app_id))
        return {
            "id": meta.get("id", "<entity_id>"),
            "name": meta.get("name", entity_name),
            "fullName": meta.get("fullName", "<entity_full_name>"),
            "caption": meta.get("caption", entity_name),
            "appName": meta.get("appName", app_id),
            "appId": meta.get("appId", m.group(1) if m else "<numeric_app_id>"),
        }

    def list_page_schema(application_id: str, entity_name: str, caption: str,
                        attributes: list[dict], entity_meta: dict | None = None) -> dict[str, Any]:
        """列表页 pageSchema 骨架（三控件 + 工具栏按钮 + 行操作事件；宿主填真实 id 后 submitPage）。"""
        from components.construction.page_schema import PageSchemaRenderer
        from components.construction.models import NormalizedEntityModel, NormalizedAttribute
        attrs = [NormalizedAttribute(a["name"], a.get("type"), a.get("caption", a["name"]))
                 for a in attributes]
        model = NormalizedEntityModel(application_id, None, entity_name, attrs, caption=caption)
        return PageSchemaRenderer(application_id).render(model, _entity_meta(entity_meta or {}, entity_name, application_id)).to_dict()

    def detail_page_schema(application_id: str, entity_name: str, caption: str,
                          attributes: list[dict], entity_meta: dict | None = None) -> dict[str, Any]:
        """详情页 pageSchema 骨架（UdcForm SINGLE + 子页；面板/弹窗无证据不生成）。"""
        from components.construction.page_schema import PageSchemaRenderer
        from components.construction.models import NormalizedEntityModel, NormalizedAttribute
        attrs = [NormalizedAttribute(a["name"], a.get("type"), a.get("caption", a["name"]))
                 for a in attributes]
        model = NormalizedEntityModel(application_id, None, entity_name, attrs, caption=caption)
        return PageSchemaRenderer(application_id).render_detail_page(model, _entity_meta(entity_meta or {}, entity_name, application_id)).to_dict()

    def microflow_create_body(name: str, caption: str, application_id: str,
                              data_schema: Any, trigger_type: str = "MANUAL") -> dict[str, Any]:
        """微流程 create/checkSchema body（dataSchema 字符串化；节点富结构宿主填真值）。"""
        from components.construction.microflow import build_microflow_create_body
        from components.platform_operations.deployment import _to_app_id
        return build_microflow_create_body(
            name=name, caption=caption, app_id=_to_app_id(application_id),
            data_schema=data_schema, trigger_type=trigger_type)

    def index_body(caption: str, entity_id: int, field_ids: list) -> dict[str, Any]:
        from components.construction.metadata_artifacts import build_index_body
        return build_index_body(caption, entity_id, field_ids)

    def enum_body(app_id: int, caption: str, name: str, order_no: int = 100) -> dict[str, Any]:
        from components.construction.metadata_artifacts import build_enum_body
        return build_enum_body(app_id, caption, name, order_no)

    def enum_item_body(app_id: int, enum_id: int, caption: str, item_value: str,
                       enum_code: str, order_no: int, enable: int = 1,
                       parent_id: str = "0") -> dict[str, Any]:
        """枚举项 body。平台槽位：itemValue=枚举项值、parentId=上级项ID（顶层 "0"）。"""
        from components.construction.metadata_artifacts import build_enum_item_body
        return build_enum_item_body(app_id, enum_id, caption, item_value, enum_code,
                                    order_no, enable, parent_id)

    def dto_body(app_id: int, caption: str, name: str,
                 attributes: list[dict]) -> list[dict[str, Any]]:
        from components.construction.metadata_artifacts import build_dto_with_attrs_body
        return build_dto_with_attrs_body(app_id, caption, name, attributes)

    def event_body(app_id: int, caption: str, event_name: str, dto_id: int) -> dict[str, Any]:
        from components.construction.metadata_artifacts import build_event_body
        return build_event_body(app_id, caption, event_name, dto_id)

    def filter_plan_body(app_name: str, app_id: int, page_id: int, grid_suffix: str,
                         driven_entity: str, caption: str,
                         conditions: list[dict]) -> dict[str, Any]:
        from components.construction.metadata_artifacts import build_filter_plan_body
        return build_filter_plan_body(app_name, app_id, page_id, grid_suffix,
                                      driven_entity, caption, conditions)

    # ================= 2026-11-09 补齐：UDC 成熟能力 → MCP =================
    # 口径：只暴露 components/ 里**已有实现**的能力，不新建、不猜形态。
    # 每个函数都注明实现文件与对应事实格，宿主可自行核对。

    # --- 设置域：此前已实现但未接 MCP 的三个 body ---
    def enum_category_body(app_id: int, name: str, *, order_no: int = 100,
                           parent_id: int | None = None,
                           description: str = "") -> dict[str, Any]:
        """枚举分组 body（ctp_enum_category）。

        实现：components/construction/metadata_artifacts.py::build_enum_category_body
        事实：core/facts/udc/setting/enum/create.md（三段写链第一段）
        """
        from components.construction.metadata_artifacts import build_enum_category_body
        return build_enum_category_body(app_id, name, order_no=order_no,
                                        parent_id=parent_id, description=description)

    def event_data_body(app_id: int, caption: str, event_name: str,
                        entity_id: int, attrs: list[dict[str, Any]],
                        description: str = "", message_type: int = 0) -> dict[str, Any]:
        """带数据的事件 body（事件绑的是 DTO，不是实体；attrs 是事件数据字段）。

        实现：build_event_with_data_body
        事实：core/facts/udc/entity/event-dto-binding.md
        """
        from components.construction.metadata_artifacts import build_event_with_data_body
        return build_event_with_data_body(app_id, caption, event_name, entity_id, attrs,
                                          description=description,
                                          message_type=message_type)

    def refer_config_body(app_id: int, entity_id: int, caption: str,
                          refer_type: str, terminals: dict[str, Any],
                          group_id: Any = None) -> dict[str, Any]:
        """实体「参照」tab 配置 body。★groupId 不传会静默落 0 → 参照列表看不到。

        实现：build_refer_config_body
        事实：core/facts/udc/entity/refer-event-index-tabs.md
        """
        from components.construction.metadata_artifacts import build_refer_config_body
        return build_refer_config_body(app_id, entity_id, caption, refer_type,
                                       terminals, group_id=group_id)

    # --- 微流程节点构造：nodes.py 的 18 个构造器统一入口 ---
    def microflow_node(action: str, *, app: dict | None = None,
                       structure: dict | None = None, entity: dict | None = None,
                       title: str = "", caption: str = "",
                       condition_: dict | None = None, value: Any = None,
                       fetch_type: str = "CONDITION", mapping_type: str = "attrs",
                       mapping: list | None = None, delete_type: str = "CONDITION",
                       select_param: dict | None = None, select_method: dict | None = None,
                       mf_service: dict | None = None, data_type: str = "STRING",
                       param_type: str = "BASIC", level: str = "ERROR",
                       for_end: int = 1, nodes: list | None = None,
                       output_desc: str = "", variable_title: str = "",
                       null_handling: str = "CONTINUE") -> dict[str, Any]:
        """构造单个微流程节点（结构级，返回可直接塞进 dataSchema.nodes 的 dict）。

        action ∈ retrieve / retrieve_array / create_entity / change_entity /
                 delete_entity / call_app_service / sub_microflow /
                 create_variable / change_variable / for_each / custom_error

        实现：components/udc/microflow/nodes.py（18 个构造器 + 条件原语）
        ★ app / structure 必须来自实体选择器接口的真实返回
          （udcMicroflowSearchTreeEntityPost），不能手拼 —— nodes.retrieve 会校验。
        事实：core/facts/udc/microflow/node-actiontypes.md、ref-and-condition-contract.md
        """
        from components.udc.microflow import nodes as N
        a = action.strip().lower()
        kw: dict[str, Any] = {"caption": caption} if caption else {}
        if a == "retrieve":
            return N.retrieve(app or {}, structure or {}, title=title or "查询",
                              condition_=condition_, value=value,
                              fetch_type=fetch_type, null_handling=null_handling, **kw)
        if a == "retrieve_array":
            return N.retrieve_array(app or {}, structure or {},
                                    variable_title=variable_title or title or "列表",
                                    condition_=condition_, value=value,
                                    fetch_type=fetch_type, **kw)
        if a == "create_entity":
            return N.create_entity(entity or {}, mapping_type=mapping_type,
                                   mapping=mapping or [], app=app, structure=structure, **kw)
        if a == "change_entity":
            return N.change_entity(select_param or {}, title=title or "更新数据",
                                   condition_=condition_, **kw)
        if a == "delete_entity":
            return N.delete_entity(entity or {}, delete_type=delete_type,
                                   condition_=condition_, app=app, structure=structure, **kw)
        if a == "call_app_service":
            return N.call_app_service(app or {}, select_method or {},
                                      mapping_type=mapping_type, value=value,
                                      select_param=select_param, **kw)
        if a == "sub_microflow":
            return N.sub_microflow(mf_service or {}, mapping_type=mapping_type,
                                   value=value, output_desc=output_desc, **kw)
        if a == "create_variable":
            return N.create_variable(title or "变量", data_type, param_type=param_type,
                                     value=value, **kw)
        if a == "change_variable":
            return N.change_variable(select_param or {}, value=value, **kw)
        if a == "for_each":
            return N.for_each(for_end, nodes or [], **kw)
        if a == "custom_error":
            return N.custom_error(title or "错误", level=level, **kw)

        # ── 以下是 22 种里原先没接进本入口的 12 种 ──────────────────
        # 为什么另起一段：完整 22 种构造器在 components/construction/
        # microflow_nodes_*.py（走 MicroflowComposer 的 _st_<kind> 分派），
        # 而 components/udc/microflow/nodes.py 只有 11 个。两套并存，
        # 本入口原先只绑了少的那套 → MCP 侧只能造 11 种节点。
        # 事实：core/facts/udc/microflow/node-catalog.md（前端面板只有 5 个分组）
        #       core/facts/udc/microflow/all-nodes-coverage.md（真实落库 22 种）
        from components.construction.microflow_composer import MicroflowComposer
        from components.construction.node_builder import NodeBuilder

        def _compose(kind: str, **cw):
            """借 MicroflowComposer._st_<kind> 造单个节点。

            LiveRefs 传 None：这些 action 的实体/列表/服务引用都由调用方
            以已构造好的节点 dict 传入（select_param / list_node），
            不需要组装器去活取。

            ★ 关键：composer 的引用参数收的是**别名**（str），不是节点 dict。
              外部调用方手上是上一步返回的节点 dict，所以这里把 dict 里的
              nodeId/输出名注册成临时别名，再把别名传给 composer。
              不这样做会 `TypeError: cannot use 'dict' as a dict key`。
            """
            cb = NodeBuilder(app_id=cw.pop("app_id", 0) or 0,
                             app_name=cw.pop("app_name", "") or "")
            mc = MicroflowComposer(cb, None, app_id=0, app_name="")

            def _alias_of(obj, default="prev"):
                """节点 dict → 可被 composer 解析的别名，并登记进 by_alias。"""
                if not isinstance(obj, dict):
                    return obj
                name = (obj.get("nodeId") or obj.get("outputName")
                        or obj.get("id") or default)
                mc.by_alias[str(name)] = obj
                return str(name)

            for key in ("list_node", "from_node", "map_node", "select_param"):
                if key in cw and isinstance(cw[key], dict):
                    cw[key] = _alias_of(cw[key], default=key)

            # entity 也收别名：composer.entity(label) 先查 _entities 再回落 LiveRefs。
            # 调用方给的是实体选择器返回的 dict（含 attributes），直接登记进去即可，
            # 不查 LiveRefs（这里没有活引用通道）。
            ent = cw.get("entity")
            if isinstance(ent, dict):
                ek = (ent.get("fullName") or ent.get("name")
                      or ent.get("dtoShortName") or ent.get("id") or "entity")
                ek = str(ek)
                if not ent.get("attributes"):
                    ent = dict(ent)
                    ent.setdefault("attributes", {})
                mc._entities[ek] = ent
                cw["entity"] = ek
            return mc.step(kind, cw.pop("alias", title or kind), **cw)

        _mt = mapping_type if mapping_type != "attrs" else None

        if a == "create_list":
            return _compose("CREATE_LIST", title=title or "vList",
                            data_type=data_type, default_value=value)
        if a == "create_map":
            return _compose("CREATE_MAP", title=title or "vMap",
                            key_type="STRING",
                            value_type=data_type if _mt is None else _mt)
        if a == "list_operation":
            # select_param 传前序 CREATE_LIST / RETRIEVE_ARRAY 的节点 dict
            return _compose("LIST_OPERATION", list_node=select_param or {},
                            op_type=_mt or "SIZE",
                            title=title or "列表处理后结果")
        if a == "map_operation":
            return _compose("MAP_OPERATION", map_node=select_param or {},
                            op_type=_mt or "PUT",
                            result_title=title or "映射取值", data_type=data_type)
        if a == "change_list":
            return _compose("CHANGE_LIST", list_node=select_param or {},
                            action=_mt or "ADD")
        if a == "convert_data":
            return _compose("CONVERT_DATA", from_node=select_param or {},
                            convert_type=_mt or "BasicData2String",
                            title=title or "数据转换")
        if a == "data_mapping":
            return _compose("DATA_MAPPING", entity=entity or {},
                            from_node=select_param or {},
                            src_field=_mt or "name")
        if a == "create_batch_entity":
            return _compose("CREATE_BATCH_ENTITY", entity=entity or {},
                            list_node=select_param or {})
        if a == "change_batch_entity":
            return _compose("CHANGE_BATCH_ENTITY", entity=entity or {},
                            list_node=select_param or {})
        if a == "publish_business_event":
            return _compose("PUBLISH_BUSINESS_EVENT", event=value or {},
                            attrs=mapping or None)
        if a == "break":
            return _compose("BREAK")
        if a == "call_data_flow":
            return _compose("CALL_DATA_FLOW", entity=entity or {},
                            rule=value or {}, condition=condition_)

        raise ValueError(
            "未知 action %r；可用 23 个（含 FOR 结构节点），"
            "逐个清单见 microflow_node_actions()" % action)

    def microflow_node_actions() -> dict[str, Any]:
        """列出 microflow_node 支持的 action → actionType 映射（能力发现）。

        为什么需要：之前 docstring 写 11 个、实现也是 11 个，
        而事实层认定微流程域有 22 种 actionType，外部只能靠猜。
        现在把「支持哪些」变成可查询事实，不用翻代码。
        """
        table = {
            "retrieve": "RETRIEVE", "retrieve_array": "RETRIEVE_ARRAY",
            "create_entity": "CREATE_ENTITY", "change_entity": "CHANGE_ENTITY",
            "delete_entity": "DELETE_ENTITY",
            "create_batch_entity": "CREATE_BATCH_ENTITY",
            "change_batch_entity": "CHANGE_BATCH_ENTITY",
            "data_mapping": "DATA_MAPPING",
            "create_variable": "CREATE_VARIABLE", "change_variable": "CHANGE_VARIABLE",
            "create_list": "CREATE_LIST", "change_list": "CHANGE_LIST",
            "list_operation": "LIST_OPERATION",
            "create_map": "CREATE_MAP", "map_operation": "MAP_OPERATION",
            "convert_data": "CONVERT_DATA",
            "call_app_service": "CALL_APP_SERVICE",
            "sub_microflow": "SUB_MICROFLOW",
            "call_data_flow": "CALL_DATA_FLOW",
            "publish_business_event": "PUBLISH_BUSINESS_EVENT",
            "for_each": "FOR", "custom_error": "CUSTOM_ERROR", "break": "BREAK",
        }
        return {"ok": True, "count": len(table), "actions": table,
                "note": "22 种微流程 actionType 全覆盖；FOR 是结构节点（循环容器），"
                        "BREAK 恒在 BRANCH 分支内。"}

    def microflow_gates(schema: dict, app_name: str | None = None) -> dict[str, Any]:
        """对完整 dataSchema 跑 G1–G41 静态闸门（0 浏览器，生成期最后一道）。

        实现：components/udc/microflow/gates.py::run_gates / run_end_gate /
              run_leak_gate / run_order_gate
        判据：problems 为空才算过；非空时逐条是 `G<n> [节点] 说明`。
        事实：core/facts/udc/microflow/generation-gates.md
        """
        from components.udc.microflow import gates as G
        problems = list(G.run_gates(schema, app_name=app_name))
        problems += list(G.run_end_gate(schema))
        problems += list(G.run_leak_gate(schema))
        return {"ok": not problems, "count": len(problems), "problems": problems}

    def microflow_capability(action: str = "") -> dict[str, Any]:
        """微流程节点能力矩阵：每个 actionType 的验证等级与证据文件。

        实现：components/udc/microflow/capability_registry.py::load/summary
        事实：core/facts/udc/microflow/capability-matrix.md（等级唯一事实源）
        """
        from components.udc.microflow import capability_registry as CR
        caps = CR.load()
        if action:
            c = caps.get(action)
            if c is None:
                return {"action": action, "found": False,
                        "available": sorted(caps)}
            return {"action": action, "found": True,
                    "capability": c.__dict__ if hasattr(c, "__dict__") else str(c)}
        return {"summary": CR.summary(caps)}

    # --- 表达式域 ---
    def expression_catalog(kind: str = "function", group: str = "") -> dict[str, Any]:
        """表达式目录：88 个函数 / 131 个系统变量。

        kind ∈ function / variable
        实现：components/udc/microflow/function_catalog.json（生成物）
        事实：core/facts/udc/expression/functions.md、system-variables.md
        """
        import json as _json
        p = _REPO_ROOT / "components" / "udc" / "microflow" / "function_catalog.json"
        if kind == "function":
            raw = _json.loads(p.read_text(encoding="utf-8"))
            funcs = raw.get("functions") or {}
            if group:
                funcs = {k: v for k, v in funcs.items()
                         if group in str(k) or group in str(v)}
            return {"kind": "function", "count": len(funcs),
                    "source": raw.get("_source", ""), "items": funcs}
        facts = _REPO_ROOT / "core" / "facts" / "udc" / "expression" / "system-variables.md"
        if not facts.exists():
            return {"kind": "variable", "status": "UNVERIFIED",
                    "reason": "system-variables.md 不在盘"}
        text = facts.read_text(encoding="utf-8")
        return {"kind": "variable", "source": str(facts), "chars": len(text),
                "content": text[:20000]}

    # --- 自定义页面 ---
    def custom_page_scaffold(page_url: str, app_id: str, title: str = "",
                             with_fetch: bool = True) -> dict[str, Any]:
        """生成 customPage.tsx 骨架（可直接写入 pc/src/pages/<pageUrl>/）。

        契约（实测，见 core/facts/udc/page/custom-page-dev-server-glob.md）：
          路径  pc/src/pages/<pageUrl>/customPage.tsx
          产物  custom-page-<pageUrl>.js
          路由  /main/portal/<appName>/<pageUrl>
        ★ 新建目录后必须重启 dev server（启动时一次性 glob 扫描）。
        """
        t = title or page_url
        fetch_block = (
            "  const [rows, setRows] = useState<Row[]>([]);\n"
            "  const [state, setState] = useState('loading');\n"
            "  useEffect(() => {\n"
            "    let alive = true;\n"
            "    fetch(`/service/udc/page-info/select-by-appId/%s`, { credentials: 'include' })\n"
            "      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status))))\n"
            "      .then((j) => { if (alive) { setRows(flatten(j)); setState('ok'); } })\n"
            "      .catch(() => { if (alive) setState('error'); });\n"
            "    return () => { alive = false; };\n"
            "  }, []);\n" % app_id
        ) if with_fetch else ""
        src = (
            "import React%s from 'react';\n\n"
            "const APP_ID = '%s';\n\n"
            "type Row = { id: string; name: string; code: string; type: string };\n\n"
            "function flatten(payload: any): Row[] {\n"
            "  const out: Row[] = [];\n"
            "  const walk = (ns: any[]) => (ns || []).forEach((n) => {\n"
            "    if (n && n.pageIds && n.pageIds.length) {\n"
            "      out.push({ id: String(n.pageIds[0]), name: n.name || '',\n"
            "                 code: n.pageUrl || '', type: n.pageType || '' });\n"
            "    }\n"
            "    walk(n && n.children);\n"
            "  });\n"
            "  const content = payload && payload.data ? payload.data.content : payload;\n"
            "  walk(Array.isArray(content) ? content : [content]);\n"
            "  return out;\n"
            "}\n\n"
            "export default function CustomPage() {\n"
            "%s"
            "  return (\n"
            "    <div style={{ padding: 24, fontFamily: 'inherit' }}>\n"
            "      <h2 style={{ margin: '0 0 16px' }}>%s</h2>\n"
            "      {state === 'loading' && <div>加载中…</div>}\n"
            "      {state === 'error' && <div style={{ color: '#c00' }}>接口调用失败</div>}\n"
            "      {state === 'ok' && (\n"
            "        <table style={{ borderCollapse: 'collapse', width: '100%%' }}>\n"
            "          <thead><tr>{['名称', '标识', '类型'].map((h) => (\n"
            "            <th key={h} style={{ textAlign: 'left', padding: '8px 12px',\n"
            "                 borderBottom: '2px solid #e5e7eb' }}>{h}</th>))}</tr></thead>\n"
            "          <tbody>{rows.map((r) => (\n"
            "            <tr key={r.id}>\n"
            "              <td style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0' }}>{r.name}</td>\n"
            "              <td style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0' }}>{r.code}</td>\n"
            "              <td style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0' }}>{r.type}</td>\n"
            "            </tr>))}</tbody>\n"
            "        </table>\n"
            "      )}\n"
            "      {state === 'ok' && rows.length === 0 && <div>暂无数据</div>}\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        ) % (", { useEffect, useState }" if with_fetch else "", app_id, fetch_block, t)
        return {"pageUrl": page_url, "appId": app_id,
                "target_path": "pc/src/pages/%s/customPage.tsx" % page_url,
                "artifact": "custom-page-%s.js" % page_url,
                "route": "/main/portal/<appName>/%s" % page_url,
                "restart_required": True,
                "source": src}

    # --- SPI 域 ---
    def spi_catalog() -> dict[str, Any]:
        """SPI 扩展点事实目录（4 格结论 + evidence 13 份）。

        事实层：core/facts/spi/（spi-ext-registration / loading / live / runtime /
                contract-surface），入口 core/facts/spi/README.md
        ★ 分级纪律：配置启用 ≠ 插件已加载 ≠ 实现被调用。
        """
        d = _REPO_ROOT / "core" / "facts" / "spi"
        if not d.exists():
            return {"status": "UNVERIFIED", "reason": "core/facts/spi 不在盘"}
        docs = []
        for p in sorted(d.glob("*.md")):
            docs.append({"file": p.name, "bytes": p.stat().st_size})
        ev = d / "evidence"
        evid = [{"file": p.name, "bytes": p.stat().st_size}
                for p in sorted(ev.glob("*.md"))] if ev.exists() else []
        return {"status": "OK", "conclusion_docs": docs, "evidence_docs": evid,
                "entry": "core/facts/spi/README.md"}

    # ================= 设置域 7 子域（按八大模块：setting/）=================
    # 契约：docs/operation-contracts/udc/setting/*-contracts.md
    # 事实：core/facts/udc/setting/<子域>/
    # ★ 公共前置：appGuid ≠ appId，取法 udcApplicationDetailGet(path:{id:appId}).guid

    # --- 选项集（udc_enum*，与枚举 ctp_enum* 是两套表，id 不互通）---
    def option_set_category_body(app_id: Any, app_guid: str, name: str, caption: str,
                                 *, order_no: int = 1, parent_id: str = "0",
                                 description: str = "") -> dict[str, Any]:
        """选项集分组 body → udcUdcEnumCategoryPost。★name 必须首字母大写（UDC_ENUM_0001）。"""
        from components.construction.setting_artifacts import build_option_set_category_body
        return build_option_set_category_body(app_id, app_guid, name, caption,
                                              order_no=order_no, parent_id=parent_id,
                                              description=description)

    def option_set_body(app_id: Any, app_guid: str, name: str, caption: str,
                        category_id: Any, *, order_no: int = 10) -> dict[str, Any]:
        """选项集 body → udcUdcEnumPost → udc_enum。category_id 来自分组。"""
        from components.construction.setting_artifacts import build_option_set_body
        return build_option_set_body(app_id, app_guid, name, caption, category_id,
                                     order_no=order_no)

    def option_set_item_body(app_id: Any, app_guid: str, enum_id: Any, name: str,
                             caption: str, code: int, *, order_no: int = 1,
                             enable: bool = True) -> dict[str, Any]:
        """选项集项 body → udcUdcEnumItemPost。★三槽位 name/caption/code 缺一不可。"""
        from components.construction.setting_artifacts import build_option_set_item_body
        return build_option_set_item_body(app_id, app_guid, enum_id, name, caption, code,
                                          order_no=order_no, enable=enable)

    # --- 字段集（父 REST 驼峰 + 子 GraphQL，两套协议）---
    def attribute_set_body(app_id: Any, name: str, caption: str, *,
                           description: str = "", source_type: str = "APP",
                           order_no: int = 1) -> dict[str, Any]:
        """字段集 body → REST POST /service/udc/attributeSet（驼峰）。attributes 恒空。"""
        from components.construction.setting_artifacts import build_attribute_set_body
        return build_attribute_set_body(app_id, name, caption, description=description,
                                        source_type=source_type, order_no=order_no)

    def attribute_set_field_body(app_id: Any, set_id: Any, name: str, caption: str,
                                 *, data_type: str = "STRING", not_null: bool = False,
                                 min_length: int = 0, max_length: int = 50,
                                 decimal_digits: int = 0, multi_select: bool = False,
                                 searchable: bool = False, uniqueness: bool = False,
                                 attribute_group_id: int = 0, order_no: int = 1,
                                 column_name: str = "", widget_config: str = "",
                                 encryption: str = "NOT_ENCRYPTION",
                                 desensitization: str = "None") -> dict[str, Any]:
        """字段集字段 body → GraphQL udcEntityAttributePost。

        ★ entityId=sourceId=字段集 id；sourceType 恒 ATTRIBUTESET；widgetConfig 是 JSON 字符串
        ★ 父 REST update 带 attributes 会被静默忽略 —— 字段只能走这个子接口
        """
        from components.construction.setting_artifacts import build_attribute_set_field_body
        return build_attribute_set_field_body(
            app_id, set_id, name, caption, data_type=data_type, not_null=not_null,
            min_length=min_length, max_length=max_length, decimal_digits=decimal_digits,
            multi_select=multi_select, searchable=searchable, uniqueness=uniqueness,
            attribute_group_id=attribute_group_id, order_no=order_no,
            column_name=column_name, widget_config=widget_config,
            encryption=encryption, desensitization=desensitization)

    # --- 扩展实体 ---
    def scalability_option_body(app_id: Any, name: str, caption: str) -> dict[str, Any]:
        """扩展实体方案 body → REST POST /service/udc/scalability-option（连字符）。"""
        from components.construction.setting_artifacts import build_scalability_option_body
        return build_scalability_option_body(app_id, name, caption)

    def scalability_field_body(app_id: Any, option_id: Any, prefix: str, caption: str,
                               *, count: int = 5, data_type: str = "STRING",
                               data_type_properties: Any = "") -> dict[str, Any]:
        """扩展实体字段 body → GraphQL udcScalabilityPost。

        ★ prefix ≤20，count ≤50(DTO)/≤20(UI)
        ★ 17 种 data_type 可写，CTPENUM 被拒（BOOT_1000 扩展字段不允许选择级联枚举）
        ★ 删除只能走 udcScalabilityDeletePost，REST delete 六种形态全 BOOT_3000
        """
        from components.construction.setting_artifacts import build_scalability_field_body
        return build_scalability_field_body(app_id, option_id, prefix, caption,
                                            count=count, data_type=data_type,
                                            data_type_properties=data_type_properties)

    # --- 二维码 / 条码 / 链接码 ---
    def qrcode_body(app_id: Any, app_guid: str, name: str,
                    *, qr_type: str = "FIELDQRCODE", link_type: str = "APP",
                    entity_full_name: str = "", value_field_code: str = "",
                    pc_page_path: str = "", mobile_page_path: str = "") -> dict[str, Any]:
        """二维码 body → REST POST /service/udc/qrcode-rule/（非 GraphQL）。

        ★ 链接码 pc_page_path 必须来自 udc_page_info.page_url，禁止自编
        """
        from components.construction.setting_artifacts import build_qrcode_body
        return build_qrcode_body(app_id, app_guid, name, qr_type=qr_type,
                                 link_type=link_type, entity_full_name=entity_full_name,
                                 value_field_code=value_field_code,
                                 pc_page_path=pc_page_path,
                                 mobile_page_path=mobile_page_path)

    # --- 流水号 ---
    def serial_scheme_body(app_id: Any, app_guid: str, code: str, name: str,
                           sections: list, *, contain_flow: bool = True,
                           active: bool = True, reset_rule: str = "NONE",
                           edit_entity: bool = True, serial_type: str = "APP",
                           sort_num: int = 1, org_id: str = "-1",
                           entity_full_name: str = "",
                           source_app_name: str = "udc") -> dict[str, Any]:
        """流水号方案 body → GraphQL udcSerialSchemeCreatePost。

        ★ 段列表字段名 serialSectionDtoList（不是 sections）；段数 1~12；totalSize 自动算
        ★ 段 DTO 用 size/dateType/show/flow/increase（不是 sectionSize/isXxx）
        sections 由 xiaozhua_serial_section 生成后传入。
        """
        from components.construction.setting_artifacts import build_serial_scheme_body
        return build_serial_scheme_body(
            app_id, app_guid, code, name, sections, contain_flow=contain_flow,
            active=active, reset_rule=reset_rule, edit_entity=edit_entity,
            serial_type=serial_type, sort_num=sort_num, org_id=org_id,
            entity_full_name=entity_full_name, source_app_name=source_app_name)

    def serial_section(size: int, section_type: str = "CONSTANT", value: str = "",
                       caption: str = "", fill_type: str = "NONE",
                       cut_type: str = "NONE", fill_char: str = "0",
                       date_type: bool = False, date_pattern: str = "yyyyMMdd",
                       show: bool = True, flow: bool = False, increase: bool = True,
                       section_rank: int = 1, serial_current: int = 1,
                       start_value: int = 1, end_value: int = -1,
                       source_app_name: str = "udc") -> dict[str, Any]:
        """流水号的一个段。section_type ∈ CONSTANT / CONTEXT / ENTITY / SERIAL。"""
        from components.construction.setting_artifacts import build_serial_section
        return build_serial_section(size=size, section_type=section_type, value=value,
                                    caption=caption, fill_type=fill_type,
                                    cut_type=cut_type, fill_char=fill_char,
                                    date_type=date_type, date_pattern=date_pattern,
                                    show=show, flow=flow, increase=increase,
                                    section_rank=section_rank,
                                    serial_current=serial_current,
                                    start_value=start_value, end_value=end_value,
                                    source_app_name=source_app_name)

    # --- 参数 ---
    def parameter_body(app_id: Any, app_guid: str, name: str, caption: str,
                       *, data_type: str = "STRING",
                       data_type_properties: dict | None = None,
                       description: str = "", param_group: str = "",
                       value: str = "", order_no: int = 10,
                       param_type: int = 0) -> dict[str, Any]:
        """应用参数 body → GraphQL udcCtpParameterDefinitonPost（★ 平台拼写少一个 i）。

        ★ dataTypeProperties 必须是对象，传 JSON 字符串报 BOOT_3002
        """
        from components.construction.setting_artifacts import build_parameter_body
        return build_parameter_body(
            app_id, app_guid, name, caption, data_type=data_type,
            data_type_properties=data_type_properties, description=description,
            param_group=param_group, value=value, order_no=order_no,
            param_type=param_type)

    # --- 导入导出模板 ---
    def excel_template_body(app_id: Any, app_guid: str, name: str, caption: str,
                            main_full_name: str, columns: list,
                            *, is_import: bool = True,
                            is_custom: bool = False) -> dict[str, Any]:
        """导入导出模板 body → REST POST /service/udc/excel/。

        ★ is_custom 必须 false，否则 search 列表看不到
        ★ 列锚点 attributeFullName = <实体全类名>.<字段名>，displayName 才是表头
        columns 用 xiaozhua_excel_template_column 生成。
        """
        from components.construction.setting_artifacts import build_excel_template_body
        return build_excel_template_body(app_id, app_guid, name, caption,
                                         main_full_name, columns,
                                         is_import=is_import, is_custom=is_custom)

    def excel_template_column(attribute_full_name: str, display_name: str,
                              data_type: str = "STRING") -> dict[str, Any]:
        """导入导出模板的一列。attribute_full_name = <实体全类名>.<字段名>。"""
        from components.construction.setting_artifacts import build_excel_template_column
        return build_excel_template_column(attribute_full_name, display_name, data_type)

    # --- 九大域能力总索引（平台侧边栏口径）+ 自定义 ---
    def capability_index(domain: str = "") -> dict[str, Any]:
        """按 UDC 九大域返回能力总索引（工具名 + 事实位置 + 契约位置 + 状态）。

        domain 留空返回全量；传 application / entity / setting / flow / menu /
        bi / role / rule / column / custom_page / custom_microflow 只返回该域。

        ★ 九域口径来源：core/facts/udc/DOMAIN-SURVEY.md（程序化实测 registry 全量）
          application 42 / entity 28 / setting 39 / flow 13 / menu 5 / bi 5 /
          role 1 / rule 0 / column 0（契约条数）
        ★ 自定义页面 / 自定义微流程不在九域内，单列。
        """
        MF_TOOLS = ["xiaozhua_microflow_create_body", "xiaozhua_microflow_node",
                    "xiaozhua_microflow_gates", "xiaozhua_microflow_capability",
                    "xiaozhua_microflow_trigger", "xiaozhua_microflow_data_schema",
                    "xiaozhua_microflow_publish"]
        domains = {
            "application": {
                "contracts_count": 42, "write_surface": 7,
                "facts": "core/facts/udc/application/（8 份）",
                "contracts": "docs/operation-contracts/udc/application/",
                "tools": ["xiaozhua_app_dependency_body", "xiaozhua_app_dependency_remove_body",
                          "xiaozhua_app_deploy_body", "xiaozhua_app_version_list",
                          "xiaozhua_app_build_info"],
                "status": "PARTIAL",
                "note": "依赖加删/构建/版本/构建信息已接（内页写链 LIVE 实测）；"
                        "建应用本身不提供（用户裁决不需要构造器）",
            },
            "entity": {
                "contracts_count": 28, "write_surface": 6,
                "facts": "core/facts/udc/entity/（12 份）",
                "contracts": "docs/operation-contracts/udc/entity/",
                "tools": ["xiaozhua_deploy_plan", "xiaozhua_index_body",
                          "xiaozhua_dto_body", "xiaozhua_refer_config_body"],
                "status": "PARTIAL",
                "note": "deploy_plan 已给 entity/attribute/page/deploy 四步 body；"
                        "参照/事件/索引三 tab 已有写面事实",
            },
            "setting": {
                "contracts_count": 39, "write_surface": 22,
                "facts": "core/facts/udc/setting/（16 份）",
                "contracts": "docs/operation-contracts/udc/setting/（11 份）",
                "tools": ["xiaozhua_enum_body", "xiaozhua_enum_item_body",
                          "xiaozhua_enum_category_body", "xiaozhua_event_body",
                          "xiaozhua_event_data_body",
                          "xiaozhua_option_set_category_body", "xiaozhua_option_set_body",
                          "xiaozhua_option_set_item_body",
                          "xiaozhua_attribute_set_body", "xiaozhua_attribute_set_field_body",
                          "xiaozhua_scalability_option_body", "xiaozhua_scalability_field_body",
                          "xiaozhua_qrcode_body",
                          "xiaozhua_serial_scheme_body", "xiaozhua_serial_section",
                          "xiaozhua_parameter_body",
                          "xiaozhua_excel_template_body", "xiaozhua_excel_template_column"],
                "status": "WIRED",
                "note": "10 个 tab 中 7 个已有 body 构造器；★appGuid ≠ appId；"
                        "枚举(ctp_enum) 与 选项集(udc_enum) 是两套表",
            },
            "flow": {
                "contracts_count": 13, "write_surface": 3,
                "facts": "core/facts/udc/microflow/（64 份）",
                "contracts": "docs/operation-contracts/udc/microflow/（25 份）",
                "tools": MF_TOOLS,
                "status": "WIRED",
                "note": "节点构造器 18 个 + G1–G41 闸门 + 触发器 + 发布；"
                        "★app/structure 必须来自实体选择器，不能手拼",
            },
            "menu": {
                "contracts_count": 5, "write_surface": 0,
                "facts": "（无独立目录；散在 docs/audit/udc-semantics/）",
                "contracts": "docs/audit/udc-semantics/MENU-FUNCTIONNODE-CONSTRAINTS.md",
                "tools": [],
                "status": "HALF_BUILT",
                "note": "★只推进了「建菜单节点」；页面上那些控件组件不会用，"
                        "搭不了完整页面。涉及核心模块多，暂不推进，不提供工具",
            },
            "bi": {
                "contracts_count": 5, "write_surface": 0,
                "facts": "（无）", "contracts": "（无）",
                "tools": [], "status": "NOT_STARTED",
                "note": "5 条契约，0 写面，0 事实 —— 未做",
            },
            "role": {
                "contracts_count": 1, "write_surface": 0,
                "facts": "（readonly-faces-batch2.md 内含角色只读面）",
                "contracts": "（无）", "tools": [], "status": "NOT_STARTED",
                "note": "1 条契约，只读面；未做",
            },
            "rule": {
                "contracts_count": 0, "write_surface": 6,
                "facts": "core/facts/udc/entity/rule-domain.md（写入链全 LIVE）",
                "contracts": "（无独立目录；契约写在 rule-domain.md §1）",
                "tools": ["xiaozhua_entity_rule_body", "xiaozhua_entity_rule_publish"],
                "status": "WIRED",
                "note": "★DOMAIN-SURVEY 写 0 契约是 2026-10-23 快照，"
                        "rule-domain.md 已证 create/checkSchema/update/findById/list/delete 全 LIVE。"
                        "body 与微流程同构（MicroFlowDto），sourceId 指向实体、type=ENTITY。"
                        "★checkSchema 返回 BOOT_0000 也可能 check=False，"
                        "且校验失败不阻塞 create（库里会多一条空条件规则）",
            },
            "column": {
                "contracts_count": 0, "write_surface": 0,
                "facts": "（无）", "contracts": "（无）",
                "tools": [], "status": "NOT_STARTED",
                "note": "0 契约 —— 最大的空档之一，未做",
            },
        }
        custom = {
            "custom_page": {
                "facts": "core/facts/udc/page/（4 份）",
                "contracts": "docs/operation-contracts/udc/page/",
                "tools": ["xiaozhua_custom_page_scaffold"],
                "status": "WIRED",
                "note": "customPage.tsx 骨架；★新建目录后必须重启 dev server"
                        "（启动时一次性 glob 扫描）",
            },
            "custom_microflow": {
                "facts": "同 flow 域",
                "contracts": "同 flow 域",
                "tools": MF_TOOLS,
                "status": "WIRED",
                "note": "自定义微流程 = flow 域的 SERVICE 型；工具与 flow 共用",
            },
        }
        if domain:
            key = domain.strip().lower().replace("-", "_")
            if key in domains:
                return {"domain": key, "found": True, "kind": "domain", **domains[key]}
            if key in custom:
                return {"domain": key, "found": True, "kind": "custom", **custom[key]}
            return {"domain": domain, "found": False,
                    "available_domains": sorted(domains),
                    "available_custom": sorted(custom)}

        by_status = {}
        for name, v in domains.items():
            by_status.setdefault(v["status"], []).append(name)
        return {
            "domains": domains,
            "custom": custom,
            "domain_count": len(domains),
            "summary": {
                "契约合计": sum(v["contracts_count"] for v in domains.values()),
                "有工具": sorted(n for n, v in domains.items() if v["tools"]),
                "未做": sorted(n for n, v in domains.items()
                               if v["status"] == "NOT_STARTED"),
            },
            "by_status": by_status,
            "entry": "core/facts/udc/DOMAIN-SURVEY.md",
        }

    # --- 客开代码落点（先知道往哪写，再拉代码，然后自己写）---
    def repo_sync(repo_dir: str, action: str, confirm: bool,
                  message: str = "", paths: list | None = None) -> dict[str, Any]:
        """客开仓库写操作：pull / commit / push。**必须 confirm=True**。

        实现：components/construction/repo_ops.py（repo_pull / repo_commit / repo_push）
        事实：core/facts/standard-product/code-repo-and-targets.md

        ★ confirm 是布尔授权位，不传就一律拒绝 —— 写能力不得默认可用。
        ★ commit 的 paths 必填，且拒绝 "." / "-A" / "*" 全量通配。
          一个 add -A 就能把别的会话的未提交改动一起带进去，事后很难拆。
        ★ pull 只走 --ff-only。客开仓里自动 merge 出的冲突提交极难收拾。
        ★ 无上游分支时 pull/push 都直接拒绝，不猜远端。

        先读状态用 repo_state（只读、不需要 confirm）。
        """
        from components.construction.repo_ops import (
            repo_commit, repo_pull, repo_push,
        )
        a = (action or "").strip().lower()
        if a == "pull":
            return repo_pull(repo_dir)
        if a == "commit":
            return repo_commit(repo_dir, message, list(paths or []), confirm)
        if a == "push":
            return repo_push(repo_dir, confirm)
        return {"ok": False, "reason": "action 只能是 pull / commit / push",
                "got": action,
                "readOnly": "要想只看状态，用 repo_state（不需要 confirm）"}

    def repo_state(repo_dir: str, recent: int = 5) -> dict[str, Any]:
        """客开仓库只读状态：分支 / remote / ahead / behind / 改动 / 最近提交 / 工程形态。

        实现：components/construction/repo_ops.py::repo_state
        事实：core/facts/standard-product/code-repo-and-targets.md

        ★ 只读。commit / push / pull 不在这里 —— 写操作要显式确认，另走单独入口。
        ★ 拿不到就回 ok=False + reason，不返回空壳。
        ★ 后端仓会顺带给 projectShape（五模块/单模块）与 basePackage。
        """
        from components.construction.repo_ops import repo_state as _rs
        return _rs(repo_dir, recent=recent)

    def code_targets(target: str, app_name: str, *,
                     backend_dir: str = "", frontend_dir: str = "",
                     page_url: str = "", extension_point: str = "") -> dict[str, Any]:
        """返回客开代码该写在哪 + 约束。**不出死模板源码** —— 代码由宿主自己写。

        target ∈ custom_service / custom_page / spi / entity_ext

        事实：core/facts/standard-product/code-repo-and-targets.md
              core/facts/standard-product/extension-project-skeleton.md

        ★ 不返回 git 地址。域名与仓库组是环境配置，用 repo_url 显式传 base。
        ★ 会先探工程形态（五模块 / 单模块）再给路径 —— 两种形态并存，别默认五模块。
        """
        from components.construction.code_targets import targets_for
        return targets_for(target, app_name, backend_dir=backend_dir,
                           frontend_dir=frontend_dir, page_url=page_url,
                           extension_point=extension_point)

    def project_shape(backend_dir: str) -> dict[str, Any]:
        """探后端工程形态：五模块（平台生成）/ 单模块 / UNKNOWN。

        ★ 五模块只有 <appName>-ext/extend/ 能写，其余重建即整包覆盖。
        ★ 单模块（实测两个样本都是）写到 src/main/java/com/seeyon/<appName>/extend/。
        """
        from components.construction.code_targets import detect_project_shape
        return detect_project_shape(backend_dir)

    def repo_url(app_name: str, git_base: str, side: str = "backend",
                 local_repo_dir: str = "") -> dict[str, Any]:
        """拼客开仓库地址。★ git_base 必填 —— 域名随客户变、仓库组随环境变，不猜。

        规则：<git_base>/backend/<appName>.git 或 <git_base>/frontend/<appName>.git

        拿不到 git_base 时：传 local_repo_dir（已有 clone 的目录），从 remote 反推。
        """
        from components.construction.code_targets import (
            git_base_from_local, repo_url as _ru, repo_url_from_local,
        )
        derived = ""
        if not git_base and local_repo_dir:
            derived = git_base_from_local(local_repo_dir) or ""
            git_base = derived
        if not git_base:
            return {"ok": False,
                    "reason": "缺 git_base。它是环境配置（<host>/<repo-group>），"
                              "本仓没有平台返回 git 地址的证据，不臆造。"
                              "传 git_base，或传 local_repo_dir 从已有 clone 反推。",
                    "tried": ("local_repo_dir 反推失败" if local_repo_dir else "未提供")}
        return {"ok": True, "url": _ru(git_base, app_name, side),
                "gitBase": git_base, "side": side,
                "derivedFromLocal": bool(derived),
                "localOrigin": (repo_url_from_local(local_repo_dir)
                                if local_repo_dir else None)}

    # --- 应用内功能页（依赖设置 / 构建部署 / 版本 / 日志面）---
    def app_dependency_body(app_id: str, dep_app_name: str, dep_app_caption: str,
                            dep_app_version: str,
                            dependent_app_type: str = "SERVICE",
                            dep_app_base_package: str = "com.seeyon",
                            extra: dict | None = None) -> dict[str, Any]:
        """构造「添加依赖」的 GraphQL body（SERVICE 应用依赖 / FRONTEND 组件依赖共用）。

        实现：components/udc/application/app_inner_ops.py::build_dependency_create
        校验：components/udc/application/dependency_constraints.py::validate_create_row
        事实：core/facts/udc/application/app-inner-write-chain.md §一
        契约：docs/operation-contracts/udc/application/app-inner-contracts.md §2

        ★ params0 是**数组**，不是对象。
        ★ FRONTEND 在 6 个基础字段外必须多带 10 个字段（description /
          dynamicModuleGroup / dynamicService / enableDelete / needGenerate /
          sort / supportUpgrade / terminalType / sourceType / packageType），
          实测形态 packageType=CONTROL / terminalType=PC / dynamicService=True。
          用 extra 透传；不传这 10 个字段也能发出请求，但组件依赖不生效。
        ★ 加完平台会自动串发 udcApplicationSearchDetectionPost（一致性检测）。
        """
        from components.udc.application.app_inner_ops import build_dependency_create
        from components.udc.application.dependency_constraints import (
            FRONTEND_EXTRA_FIELDS, validate_create_row,
        )
        body = build_dependency_create(
            app_id, dep_app_name=dep_app_name, dep_app_caption=dep_app_caption,
            dep_app_version=dep_app_version,
            dep_app_base_package=dep_app_base_package,
            dependent_app_type=dependent_app_type, extra=extra)

        row = body["variables"]["params0"][0]
        problems = validate_create_row(row)
        if problems:
            hint = ""
            if dependent_app_type == "FRONTEND":
                from components.udc.application.dependency_constraints import (
                    FRONTEND_SAMPLE_SHAPE,
                )
                hint = ("\n\nFRONTEND 用 extra 补齐这 10 个字段。实测形态：\n  %s"
                        "\n其余取值参考 dependency_constraints.FRONTEND_SAMPLE_SHAPE。"
                        % json.dumps(FRONTEND_SAMPLE_SHAPE, ensure_ascii=False))
            raise ValueError("依赖行不合法：\n  - %s%s" % ("\n  - ".join(problems), hint))

        missing = []
        if dependent_app_type == "FRONTEND":
            missing = [f for f in FRONTEND_EXTRA_FIELDS if f not in row]
        return {
            "op": "udcApplicationDependentApplicationCreateBatchPost",
            "body": body,
            "dependentAppType": dependent_app_type,
            "missingFrontendFields": missing,
            "note": ("★FRONTEND 必须补齐这 10 个字段，否则组件依赖不生效"
                     if missing else ""),
            "autoFollowUp": "平台在写入后自动串发一致性检测（udcApplicationSearchDetectionPost）",
        }

    def app_dependency_remove(row_id: str = "", ids: list | None = None) -> dict[str, Any]:
        """构造「移除依赖」body。两条路，别混。

        实现：build_dependency_delete / build_component_delete
        校验：validate_delete_arg / validate_component_delete

        ★ row_id 是**依赖行 id**（列表里该行的 id），不是 appId、也不是 depAppName。
          传后两者平台不报错，只是删不掉 —— 这是踩过的坑。
        ★ 应用依赖（SERVICE）走 GraphQL DeleteByIdPost；组件依赖（FRONTEND）走
          **REST** udc/application/dependent-application/delete-by-ids，body {"ids":[...]}。
          两条不是一条路。

        ⚠⚠ 两个删接口都会**真的删数据**，返回 content=1 就是删掉了。
          只能删你自己刚造出来的依赖行，绝不能拿列表里的现有行去试 ——
          即使 enableDelete=true（平台允许删），别人的配置也不该拿来当试验品。
          （2026-11-12 拿 cip-manager 行试接口，content=1 真删了，靠 create 补回；
           版本未变，只有行 id 变了 —— docs/audit/INCIDENT-20261112-deleted-builtin-dependency.md）

        ★ enableDelete 判断可删性是**准确的**：
            true  → 界面「移除」绿色可点，平台允许删（app-common / cip-capability / cip-manager）
            false → 界面灰色禁删（其余 8 条 SERVICE 依赖）
          它回答「平台允许不允许」，不回答「你该不该拿它试」。
        """
        from components.udc.application.app_inner_ops import (
            build_component_delete, build_dependency_delete,
        )
        from components.udc.application.dependency_constraints import (
            validate_component_delete, validate_delete_arg,
        )
        if ids is not None:
            problems = validate_component_delete(ids)
            if problems:
                raise ValueError("\n  - ".join(problems))
            r = build_component_delete(ids)
            return {"mode": "component_rest_batch",
                    "url": r["url"], "body": r["body"],
                    "note": "组件依赖批量删；入口在表格上方「批量删除依赖」"}
        if not row_id:
            raise ValueError("必须给 row_id（单删应用依赖）或 ids（批删组件依赖）")
        problems = validate_delete_arg(row_id)
        if problems:
            raise ValueError("\n  - ".join(problems))
        b = build_dependency_delete(row_id)
        return {"mode": "app_graphql_single",
                "op": "udcApplicationDependentApplicationDeleteByIdPost",
                "endpoint": "POST /service/udc/graphql?udcApplicationDependentApplicationDeleteByIdPost",
                "body": b}

    def app_deploy_body(app_id: str, project_type: str = "ALL",
                        terminal_type: str = "ALL",
                        deploy_type: str = "RELEASE") -> dict[str, Any]:
        """构造沙箱「立即构建」body（构建 + 部署）。

        实现：build_deploy_normal
        事实：app-inner-write-chain.md §二

        ⚠ 平台把它声明成 query，**实际是写操作**，会覆盖沙箱态，不属于可重放的读面。
        ★ 实测一次全量构建：前端 PC 14s / 前端 MOBILE 8s / 后端编译 33s /
          部署 124s，平台自报 totalTime=224。
        ★ 构建日志不用抓流：udcSandboxBuildInfoAppGet 一把返回 {state, progress,
          totalTime, buildVersion, logs[]}，构建结束后仍可取（state=SUCCESS）。
        ★ 进度是 WebSocket 推的，HTTP 侧只有约 6s 一次的轮询。
        """
        from components.udc.application.app_inner_ops import build_deploy_normal
        b = build_deploy_normal(app_id, project_type=project_type,
                                terminal_type=terminal_type, deploy_type=deploy_type)
        return {"op": "udcRuntimeDeployNormalPost", "body": b,
                "isWrite": True,
                "note": "声明成 query 实为写；会覆盖沙箱态，不要当读面重放",
                "buildInfoOp": "udcSandboxBuildInfoAppGet（别名用 path: 不是 body:）"}

    def app_version_list(app_name: str, page_size: int = 20) -> dict[str, Any]:
        """构造发布版本列表 body（REST，顶层裸数组）。

        ★ IN_appId 传 **appName 字符串**，不是 appId。
        ★ 响应不套 code 信封，别找 BOOT_0000。
        """
        from components.udc.application.app_inner_ops import build_version_list
        return build_version_list(app_name, page_size=page_size)

    def app_build_info(app_id: str) -> dict[str, Any]:
        """构造构建信息查询（含 logs[] 全文）。

        ★ 别名是 path: 不是 body: —— udcSandboxBuildInfoAppGet(path: $params0)
        """
        from components.udc.application.app_inner_ops import build_build_info_query
        return build_build_info_query(app_id)

    # --- 规则域（实体规则，写入链已 LIVE，body 与微流程同构）---
    def entity_rule_body(app_id: Any, entity_id: Any, name: str, caption: str = "",
                         *, group_type: int = 1, nodes: list | None = None,
                         trigger: dict | None = None,
                         description: str = "",
                         state: int = 20) -> dict[str, Any]:
        """构造实体规则 body（MicroFlowDto 规则形态），含离线作用域校验。

        group_type：1=VALIDATE（校验，可多条） 2=ASSIGN_VALUE（赋值，未验证）
                    3=DEFAULT_VALUE（默认值，★同一实体只能一条）

        实现参考：tools/core/entity/write_entity_rule.py
                  components/udc/rule_domain_scope.py
        事实：core/facts/udc/entity/rule-domain.md

        ★ state 默认 20（RELEASE）。写 10 的规则在 udcMicroflowSearchEntityRulePost
          里查不到 —— 建完等于隐形，页面规则列表看不见。
        ★ 建之前跑作用域校验（fail-closed）：三个域允许的节点集合互不相交，
          塞错域的节点前端不报错但节点行为不对。
        ★ 新建时 dataSchema 必须完整（nodes / input / sourceType / endNode）
        """
        from components.udc.rule_domain_scope import (
            iter_action_nodes, validate_rule_scope, validate_sub_microflow_service,
        )
        from components.construction.microflow_triggers import make_data_schema
        trg = trigger if trigger is not None else microflow_trigger("MANUAL")
        schema = make_data_schema(name=name, caption=caption or name,
                                  mf_type="ENTITY", trigger_type="MANUAL",
                                  trigger=trg, nodes=nodes or [])
        schema.setdefault("input", None)

        errs = validate_rule_scope(schema, group_type)
        for at, node in iter_action_nodes(schema):
            if at == "SUB_MICROFLOW":
                errs.extend(validate_sub_microflow_service(node.get("mfService")))
        if errs:
            raise ValueError("规则越域，拒绝构造（groupType=%s）：\n  - %s"
                             % (group_type, "\n  - ".join(errs)))
        if group_type == 3:
            scope_note = "★DEFAULT_VALUE 同一实体只能一条，再建报 UDC_MICROFLOW_0027"
        else:
            scope_note = ""
        return {"appId": str(app_id), "sourceId": str(entity_id),
                "name": name, "caption": caption or name,
                "description": description,
                # ★ MicroFlowTypeEnum: SERVICE(0) FRONTEND(1) ENTITY_RULE(2) CUSTOM(3) FUNCTION(4)
                # 写成 "ENTITY" 平台直接 BOOT_3002「No enum constant ...ENTITY」
                "type": "ENTITY_RULE", "groupType": str(group_type),
                "state": state, "creationMethod": "MANUAL",
                "triggerType": "MANUAL",
                "dataSchema": json.dumps(schema, ensure_ascii=False),
                "scopeNote": scope_note,
                "verifyNote": "★checkSchema 返回 BOOT_0000 也可能 check=False，"
                              "判据是 content.check==true 且 errors==0；"
                              "校验失败不阻塞 create（库里会多一条空条件规则）"}

    def entity_rule_publish(dto: dict, host: str = "", cookie: str = "",
                            cdp_port: int = 0) -> dict[str, Any]:
        """实体规则 create + checkSchema。

        **两种传输二选一：**
          cdp_port > 0   页面自己 fetch(credentials:'include')，cookie 不离开浏览器 ← 首选
          host + cookie  直接带 Cookie 头（仅当宿主明确持有会话）

        ★ 首选 cdp_port：session token 就是这个用户的身份，导出重放等于复制身份。

        顺序固定：先 checkSchema 拿明细 → 再 create。
        ★ 只认 content.check==true 且 errors==0，不看 code（BOOT_0000 也可能 check=False）
        ★ 校验失败不阻塞 create —— 所以校验不过时本工具**不执行 create**，
          避免库里留一条空条件规则
        """
        import subprocess as _sp

        if not cdp_port and not (host and cookie):
            return {"ok": False,
                    "reason": "需要 cdp_port（推荐）或 host+cookie 之一",
                    "hint": "cdp_port 走页面 fetch，cookie 不离开浏览器"}

        if cdp_port:
            from components.transport.page_fetch import PageFetch
            pf = PageFetch(int(cdp_port))
            try:
                def _post(path: str, body: dict) -> dict[str, Any]:
                    r = pf.post(path, body)
                    return r.get("json") or {"code": "TRANSPORT_ERROR",
                                             "message": str(r)[:300]}
                return _entity_rule_publish_flow(_post, dto)
            finally:
                pf.close()

        def _post(path: str, body: dict) -> dict[str, Any]:
            cmd = ["curl", "-sS", "--max-time", "120", "-X", "POST",
                   host.rstrip("/") + path,
                   "-H", "Content-Type: application/json",
                   "-H", "Cookie: " + cookie,
                   "--data-binary", "@-"]
            p = _sp.run(cmd, input=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                        capture_output=True, timeout=150)
            out = (p.stdout or b"").decode("utf-8", "replace")
            try:
                return json.loads(out)
            except ValueError:
                return {"code": "TRANSPORT_ERROR",
                        "message": (p.stderr or b"").decode("utf-8", "replace")[:300]}

        return _entity_rule_publish_flow(_post, dto)

    # --- 微流程触发器（纯函数，零联网）---
    def microflow_trigger(kind: str = "MANUAL", *, node_id: str = "",
                          job_caption: str = "", cycle_type: str = "DAY",
                          rotation_type: str = "DAY", value: str = "1",
                          day_of_week: int = 1, param_type: str = "NONE",
                          output: dict | None = None, caption: str = "开始",
                          basic: str | None = None, event: dict | None = None,
                          out_param_name: str = "事件数据") -> dict[str, Any]:
        """构造微流程触发器（dataSchema.trigger）。

        kind ∈ MANUAL / SCHEDULE / EVENT / MF_EVENT
          MANUAL     服务定义，可带出入参（SERVICE+MANUAL 才有）
          SCHEDULE   定时任务，★无出入参（output=null 是 24 条真实样本的一致形态）
          EVENT      实体事件监听，需 event（来自 udcMicroflowFilterEventPost）
          MF_EVENT   微流程事件，需 event（sourceTypes=[MICRO_FLOW_EVENT]）

        实现：components/construction/microflow_triggers.py
        事实：core/facts/udc/microflow/trigger-and-type-mapping.md、
              schedule-structure.md、event-listener-structure.md
        ★ SCHEDULE 的 value ≥5（MINUTE 最小 5）；显式传 1 会让调度任务根本不注册
        """
        from components.construction import microflow_triggers as T
        k = kind.strip().upper()
        nid = node_id or "MFStartNode"
        if k == "MANUAL":
            return T.manual_trigger(node_id=nid, param_type=param_type, output=output,
                                    caption=caption, basic=basic,
                                    desc=(output or {}).get("desc")
                                         or (output or {}).get("description") or "")
        if k == "SCHEDULE":
            if not job_caption:
                raise ValueError("SCHEDULE 必须给 job_caption")
            return T.schedule_trigger(node_id=node_id or ("SERVICE_" + T._rid(6)),
                                      job_caption=job_caption, cycle_type=cycle_type,
                                      rotation_type=rotation_type, value=value,
                                      day_of_week=day_of_week)
        if k == "EVENT":
            if not event:
                raise ValueError("EVENT 必须给 event（来自 udcMicroflowFilterEventPost）")
            return T.event_trigger(node_id=nid, event=event,
                                   out_param_name=out_param_name)
        if k == "MF_EVENT":
            if not event:
                raise ValueError("MF_EVENT 必须给 event")
            return T.mf_event_trigger(node_id=nid, event=event,
                                      out_param_name=out_param_name)
        raise ValueError("未知 kind %r；可用：MANUAL / SCHEDULE / EVENT / MF_EVENT" % kind)

    def microflow_data_schema(name: str, caption: str, trigger: dict,
                              nodes: list, *, mf_type: str = "SERVICE",
                              trigger_type: str = "MANUAL",
                              end_output: dict | None = None,
                              input_param: dict | None = None,
                              description: str = "") -> dict[str, Any]:
        """组装完整 dataSchema（trigger + nodes + endNode）。

        实现：components/construction/microflow_triggers.py::make_data_schema
        ★ 本函数产出的 endNode 是 9 键形态（真实 SCHEDULE/EVENT 样本 24/24 都是 9 键）。
          MANUAL 要渲染「参数」面板还需补 paramType / basic 等键 —— 用
          xiaozhua_microflow_gates 校验，G11 会指出缺哪个。
        ★ 判据不是「写入成功」，而是 gates 全绿 + publish check=True 且 errors=[]
        """
        from components.construction.microflow_triggers import make_data_schema
        return make_data_schema(name=name, caption=caption, mf_type=mf_type,
                                trigger_type=trigger_type, trigger=trigger,
                                nodes=nodes, end_output=end_output,
                                input_param=input_param, description=description)

    # --- FILTER 过滤条件表达式（需显式 host+cookie）---
    def expression_filter(dto_full: str, list_desc: str, entity_model: dict,
                          host: str = "", cookie: str = "", cdp_port: int = 0, *,
                          field: str = "", op: str = "GT",
                          const: Any = None, spec: dict | None = None,
                          title: str = "") -> dict[str, Any]:
        """构造 LIST_OPERATION FILTER 的过滤条件表达式（返回 {title, schema}）。

        两种用法（二选一）：
          ① field + op + const  简单形态，如 field='processedRows' op='GT' const=2
          ② spec               任意布尔 AST（算术/函数/逻辑组合）

        实现：components/construction/microflow_filter.py
              build_filter_expression（简单）/ build_ast_expression（AST）
        事实：core/facts/udc/microflow/node-list-operation.md §9、
              expression/functions.md
        ★ 含字段引用的表达式**完全离线可编译**，不需要进设计器
        ★ OPERATOR token 必须平铺在 tokens 数组里，不能塞进 subOps（否则 FORMULA_6070）
        ★ containsText 参数顺序是 (被查文本, 子串)，反序恒 0 条
        ★ 布尔函数不要包 `== true`，裸函数条件才对
        """
        from components.construction import microflow_filter as F
        if not cdp_port and not (host and cookie):
            return {"ok": False,
                    "reason": "需要 cdp_port（推荐）或 host+cookie 之一"}
        be = _expression_backend(host, cookie, cdp_port)
        try:
            return _expression_filter_flow(be, F, dto_full, list_desc, entity_model,
                                           field=field, op=op, const=const,
                                           spec=spec, title=title)
        finally:
            if cdp_port:
                be.close()


    # --- 微流程发布（写，需显式 host+cookie）---
    def microflow_publish(mid: str, app_id: str, data_schema: Any,
                          host: str = "", cookie: str = "", cdp_port: int = 0,
                          name: str = "", caption: str = "",
                          trigger_type: str = "", group_id: str = "") -> dict[str, Any]:
        """把微流程发布到 RELEASE（create 之后的第二步；已存在则用本工具刷新）。

        实现：components/udc/microflow/deploy.py::publish（唯一实现，自拼 body
              少一个键就是 BOOT_1001 且不给明细）
        ★ 发布体必须完整 DTO：versionCode=100、openApi=STOP、restApi=DISABLED
        ★ 判据：返回 check=True 且 errors=[]；只看到 BOOT_0000 不算发布成功
        事实：core/facts/udc/microflow/state-lifecycle.md、
              generation-gates.md、save_pipeline.py（完整保存链）
        """
        import json as _json
        from components.udc.microflow import deploy as DP
        if not cdp_port and not (host and cookie):
            return {"ok": False,
                    "reason": "需要 cdp_port（推荐）或 host+cookie 之一"}
        schema = data_schema
        if isinstance(schema, str):
            schema = _json.loads(schema)
        transport = None
        if cdp_port:
            from components.transport.page_fetch import PageFetch
            transport = PageFetch(int(cdp_port))
        try:
            ok, info = DP.publish(host, cookie, str(mid), app_id=str(app_id),
                                  schema=schema, name=name, caption=caption,
                                  trigger_type=trigger_type, group_id=group_id,
                                  transport=transport)
        finally:
            if transport is not None:
                transport.close()
        errs = (info or {}).get("errors") or []
        return {"ok": bool(ok), "check": bool(ok), "errors": errs,
                "published": bool(ok) and not errs,
                "note": "只看到 BOOT_0000 不代表发布成功；判据是 check=True 且 errors 为空"}

    # --- 表达式编译校验（需显式 host+cookie）---
    def expression_verify(tokens: list, context: list,
                          host: str = "", cookie: str = "", cdp_port: int = 0,
                          result_type: str = "BOOLEAN",
                          is_multi_select: bool = False) -> dict[str, Any]:
        """校验 + 编译表达式，返回 executableExpr（可直接塞进节点配置）。

        实现：components/udc/microflow/expression_api.py::verify_expression
              + expression_build.py::build_dto / make_expression
        事实：core/facts/udc/expression/engine.md、functions.md
        ★ 变量必须绑 schemas（只给 paramId 报 FORMULA_6058），且放字段节点不放实体根
        ★ executableExpr = 44 字符固定 Base64 前缀 + URL 编码表达式，由服务端返回，
          不要自己生成
        """
        from components.udc.microflow import expression_api as EA
        expr = {"tokens": tokens, "context": context,
                "resultType": result_type, "isMultiSelect": is_multi_select}
        if not cdp_port and not (host and cookie):
            return {"ok": False,
                    "reason": "需要 cdp_port（推荐）或 host+cookie 之一"}
        be = _expression_backend(host, cookie, cdp_port)
        try:
            return EA.verify_expression(be, expr)
        finally:
            if cdp_port:
                be.close()


    return {
        "agent": agent,
        "dispatch": dispatch,
        "generate": generate,
        "generate_from_requirement": generate_from_requirement,
        "live_probe": live_probe,
        "deploy_plan": deploy_plan,
        "list_page_schema": list_page_schema,
        "detail_page_schema": detail_page_schema,
        "microflow_create_body": microflow_create_body,
        "index_body": index_body,
        "enum_body": enum_body,
        "enum_item_body": enum_item_body,
        "dto_body": dto_body,
        "event_body": event_body,
        "filter_plan_body": filter_plan_body,
        # ---- 2026-11-09 补齐：设置/实体/微流程/表达式/自定义页/SPI ----
        "enum_category_body": enum_category_body,
        "event_data_body": event_data_body,
        "refer_config_body": refer_config_body,
        "microflow_node": microflow_node,
        "microflow_node_actions": microflow_node_actions,
        "microflow_gates": microflow_gates,
        "microflow_capability": microflow_capability,
        "expression_catalog": expression_catalog,
        "custom_page_scaffold": custom_page_scaffold,
        "spi_catalog": spi_catalog,
        # ---- 设置域 7 子域（按八大模块：setting/）----
        "option_set_category_body": option_set_category_body,
        "option_set_body": option_set_body,
        "option_set_item_body": option_set_item_body,
        "attribute_set_body": attribute_set_body,
        "attribute_set_field_body": attribute_set_field_body,
        "scalability_option_body": scalability_option_body,
        "scalability_field_body": scalability_field_body,
        "qrcode_body": qrcode_body,
        "serial_scheme_body": serial_scheme_body,
        "serial_section": serial_section,
        "parameter_body": parameter_body,
        "excel_template_body": excel_template_body,
        "excel_template_column": excel_template_column,
        "capability_index": capability_index,
        "repo_state": repo_state,
        "repo_sync": repo_sync,
        "code_targets": code_targets,
        "project_shape": project_shape,
        "repo_url": repo_url,
        "app_dependency_body": app_dependency_body,
        "app_dependency_remove": app_dependency_remove,
        "app_deploy_body": app_deploy_body,
        "app_version_list": app_version_list,
        "app_build_info": app_build_info,
        "entity_rule_body": entity_rule_body,
        "microflow_trigger": microflow_trigger,
        "microflow_data_schema": microflow_data_schema,
        # ---- 需显式 host+cookie 的写/编译能力 ----
        "microflow_publish": microflow_publish,
        "entity_rule_publish": entity_rule_publish,
        "expression_filter": expression_filter,
        "expression_verify": expression_verify,
        "allow_network": allow_network,
        "capabilities": {
            "components": sorted(agent.registry.names()),
            "readonly_only": True,
            "credential_mode": "path-ref-only",
            "deployment_plan": "readonly data; host executes the write steps",
            "generators": [
                "list_page_schema", "detail_page_schema", "microflow_create_body",
                "index_body", "enum_body", "enum_item_body", "dto_body",
                "event_body", "filter_plan_body",
                "enum_category_body", "event_data_body", "refer_config_body",
                "microflow_node", "microflow_gates", "microflow_capability",
                "expression_catalog", "custom_page_scaffold", "spi_catalog",
            ],
            "schema": "xiaozhua-host-bootstrap.v1",
        },
    }


__all__ = ["bootstrap"]
