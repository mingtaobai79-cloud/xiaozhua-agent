"""adapters/mcp/server.py — seeyon_host_bootstrap 五能力 → MCP 工具（stdio jsonrpc 2.0 最小实现）。

设计源：adapters/mcp/DESIGN.md（S1 PASS，dedupe mcp-s1-verdict）。
边界（ROUTE）：只写 adapters/mcp/** + tests/test_mcp_server.py；禁改 bootstrap 本体；
凭据 0 入件（路径载体 SEEYON_CRED_FILE）；默认离线（SEEYON_ALLOW_NETWORK 未设 = False）。

协议面（DESIGN §1.1）：每行一个 JSON-RPC 2.0 帧（\n 分隔，UTF-8）；
method 白名单 = initialize / tools/list / tools/call（notifications/initialized 静默 ack）；
protocolVersion 回 "2024-11-05"；未知 method → -32601；参数缺/型错 → -32602。
"""
from __future__ import annotations

import inspect
import json
import os
import sys
from typing import Any, Callable

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "seeyon-mcp", "version": "0.1.0"}

# bootstrap 能力键（seeyon_host_bootstrap.py 实测返回 dict 的键，DESIGN §2 表）。
# 2026-11-08 补：bootstrap 实际返回 15 个能力，此前只接了 5 个 —— 9 个 metadata 构造器
# （pageSchema / microflow / index / enum / dto / event / filter）全部悬空，宿主看不到。
# schema 由 inspect 签名自动生成（`_schema_from_callable`），加一个 key 即可，不用手抄。
TOOL_KEYS = (
    "dispatch", "generate", "generate_from_requirement", "live_probe", "deploy_plan",
    # ---- 以下 9 个此前未接入 MCP ----
    "list_page_schema", "detail_page_schema", "microflow_create_body",
    "index_body", "enum_body", "enum_item_body", "dto_body",
    "event_body", "filter_plan_body",
    # ---- 2026-11-09 补齐：设置/实体/微流程/表达式/自定义页/SPI ----
    "enum_category_body", "event_data_body", "refer_config_body",
    "microflow_node", "microflow_gates", "microflow_capability",
    "expression_catalog", "custom_page_scaffold", "spi_catalog",
    # ---- 设置域 7 子域（八大模块 setting/）----
    "option_set_category_body",
    "option_set_body",
    "option_set_item_body",
    "attribute_set_body",
    "attribute_set_field_body",
    "scalability_option_body",
    "scalability_field_body",
    "qrcode_body",
    "serial_scheme_body",
    "serial_section",
    "parameter_body",
    "excel_template_body",
    "excel_template_column",
    "capability_index",
    # ---- 微流程触发器 / dataSchema（纯函数）----
    "microflow_trigger", "microflow_data_schema",
    "entity_rule_body",
    "repo_state", "repo_sync", "code_targets", "project_shape", "repo_url",
    "app_dependency_body", "app_dependency_remove",
    "app_deploy_body", "app_version_list", "app_build_info",
    # ---- 需显式 host+cookie（不传不联网）----
    "microflow_publish", "expression_verify", "expression_filter",
    "entity_rule_publish",
)

MCP_TOOL_NAMES = {
    "dispatch": "seeyon_dispatch",
    "generate": "seeyon_generate",
    "generate_from_requirement": "seeyon_generate_from_requirement",
    "live_probe": "seeyon_live_probe",
    "deploy_plan": "seeyon_deploy_plan",
    "list_page_schema": "seeyon_list_page_schema",
    "detail_page_schema": "seeyon_detail_page_schema",
    "microflow_create_body": "seeyon_microflow_create_body",
    "index_body": "seeyon_index_body",
    "enum_body": "seeyon_enum_body",
    "enum_item_body": "seeyon_enum_item_body",
    "dto_body": "seeyon_dto_body",
    "event_body": "seeyon_event_body",
    "filter_plan_body": "seeyon_filter_plan_body",
    # ---- 2026-11-09 补齐 ----
    "enum_category_body": "seeyon_enum_category_body",
    "event_data_body": "seeyon_event_data_body",
    "refer_config_body": "seeyon_refer_config_body",
    "microflow_node": "seeyon_microflow_node",
    "microflow_gates": "seeyon_microflow_gates",
    "microflow_capability": "seeyon_microflow_capability",
    "expression_catalog": "seeyon_expression_catalog",
    "custom_page_scaffold": "seeyon_custom_page_scaffold",
    "spi_catalog": "seeyon_spi_catalog",
    # ---- 设置域 7 子域 ----
    "option_set_category_body": "seeyon_option_set_category_body",
    "option_set_body": "seeyon_option_set_body",
    "option_set_item_body": "seeyon_option_set_item_body",
    "attribute_set_body": "seeyon_attribute_set_body",
    "attribute_set_field_body": "seeyon_attribute_set_field_body",
    "scalability_option_body": "seeyon_scalability_option_body",
    "scalability_field_body": "seeyon_scalability_field_body",
    "qrcode_body": "seeyon_qrcode_body",
    "serial_scheme_body": "seeyon_serial_scheme_body",
    "serial_section": "seeyon_serial_section",
    "parameter_body": "seeyon_parameter_body",
    "excel_template_body": "seeyon_excel_template_body",
    "excel_template_column": "seeyon_excel_template_column",
    "capability_index": "seeyon_capability_index",
    # ---- 微流程触发器 / dataSchema ----
    "microflow_trigger": "seeyon_microflow_trigger",
    "microflow_data_schema": "seeyon_microflow_data_schema",
    "entity_rule_body": "seeyon_entity_rule_body",
    "repo_state": "seeyon_repo_state",
    "repo_sync": "seeyon_repo_sync",
    "code_targets": "seeyon_code_targets",
    "project_shape": "seeyon_project_shape",
    "repo_url": "seeyon_repo_url",
    "app_dependency_body": "seeyon_app_dependency_body",
    "app_dependency_remove": "seeyon_app_dependency_remove_body",
    "app_deploy_body": "seeyon_app_deploy_body",
    "app_version_list": "seeyon_app_version_list",
    "app_build_info": "seeyon_app_build_info",
    # ---- 需显式 host+cookie ----
    "microflow_publish": "seeyon_microflow_publish",
    "expression_verify": "seeyon_expression_verify",
    "expression_filter": "seeyon_expression_filter",
    "entity_rule_publish": "seeyon_entity_rule_publish",
}

# ---- JSON-RPC 错误码（DESIGN §1.1）----
ERR_METHOD_NOT_FOUND = -32601
ERR_INVALID_PARAMS = -32602


class JsonRpcError(Exception):
    """携带 code 的协议级错误（→ error 信封，而非裸异常）。"""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------- schema 生成

def _pytype_to_json_type(py_type: Any) -> str:
    """Python 注解 → JSON Schema type（仅覆盖本仓五签名用到的标量/容器）。"""
    name = getattr(py_type, "__name__", None) or str(py_type)
    if py_type is str or name == "str":
        return "string"
    if py_type is int or name == "int":
        return "integer"
    if py_type is bool or name == "bool":
        return "boolean"
    if py_type is list or name in ("list", "List", "_GenericAlias") or "list" in name.lower():
        return "array"
    if py_type is dict or "dict" in name.lower():
        return "object"
    return "string"  # 保守兜底


def _schema_from_callable(fn: Callable) -> dict:
    """inspect.signature() → JSON Schema（required/默认值取实签名，非手抄）。"""
    sig = inspect.signature(fn)
    props: dict[str, Any] = {}
    required: list[str] = []
    for pname, param in sig.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        jtype = _pytype_to_json_type(param.annotation) if param.annotation is not inspect.Parameter.empty else "string"
        prop: dict[str, Any] = {"type": jtype}
        if param.default is inspect.Parameter.empty:
            required.append(pname)
        else:
            prop["default"] = param.default
        props[pname] = prop
    return {"type": "object", "properties": props, "required": required}


def build_tool_schemas(caps: dict[str, Callable]) -> list[dict]:
    """五工具 MCP Tool 列表（纯函数，无副作用；pytest 直接 import 断言）。

    schema 两条源（DESIGN §2.1）：inspect 签名 + deployment.py 常量（枚举非手抄）。
    """
    # 延迟 import：deployment 常量为枚举源（实测值，DESIGN §2.1）
    from components.platform_operations.deployment import (
        DATATYPES, DEPLOY_TYPES, STEREO_TYPES,
    )

    descriptions = {
        "dispatch": "按 intent 路由到 seeyon-agent 组件（只读）。返回 dict 路由决策+证据（含 status）。",
        "generate": "生成 UDC 实体后端骨架+前端页面产物（声明级，方法体 UNVERIFIED；只读出数据不落库）。",
        "generate_from_requirement": "自然语言需求 → 解析(parsed)+后端骨架+前端产物（同上，只读）。",
        "live_probe": "活体只读探测 4 端点。默认离线返回 status=BLOCKED（allow_network=False）；"
                      "活体需显式 SEEYON_ALLOW_NETWORK=1。任何离线输出不得解读为 LIVE PASS。",
        "deploy_plan": "生成 4 步部署方案 data（readonly_plan=True，只读出方案；写由宿主执行）。"
                       "steps op 链：entity.create→entity.attribute.create→page.create→deploy.normal"
                       "（page.create 为 registry-gap：链级 OBSERVED_LIVE，registry 未登记）。"
                       "子契约语义源 core/tools/udc/*.md。",
        # ---- 2026-11-08 新增 9 个 metadata 构造器（此前 bootstrap 有、MCP 没接）----
        "list_page_schema": "UDC 列表页 pageSchema 骨架（三控件 + 工具栏按钮 + 行操作事件）。"
                            "宿主填真实 id 后 submitPage；只出 data，不落库。",
        "detail_page_schema": "UDC 详情页 pageSchema 骨架（UdcForm SINGLE + 子页）。"
                              "面板/弹窗无证据不生成；只出 data，不落库。",
        "microflow_create_body": "微流程 create/checkSchema body（dataSchema 字符串化）。"
                                 "节点富结构由宿主填真值；只出 body，不提交。",
        "index_body": "索引（index）创建 body：caption + entity_id + field_ids。",
        "enum_body": "枚举（enum）创建 body：app_id + caption + name + order_no。",
        "enum_item_body": "枚举项创建 body。平台槽位：itemValue=枚举项值、parentId=上级项ID（顶层 \"0\"）。",
        "dto_body": "DTO + 属性 的创建 body 列表（一次返回多个 body，按顺序提交）。",
        "event_body": "事件（event）创建 body：app_id + caption + event_name + dto_id。",
        # ---- 2026-11-09 补齐：设置/实体/微流程/表达式/自定义页/SPI ----
        "enum_category_body": "枚举分组创建 body（ctp_enum_category，枚举三段写链第一段）。",
        "event_data_body": "带数据的事件 body。★事件绑的是 DTO 不是实体；实体无 DTO 时创建会静默成功但页面 0 条。",
        "refer_config_body": "实体「参照」tab 配置 body。★groupId 不传会静默落 0，参照列表看不到。",
        "microflow_node": "构造单个微流程节点（结构级 dict，可直接放进 dataSchema.nodes）。"
                          "action ∈ retrieve/retrieve_array/create_entity/change_entity/delete_entity/"
                          "call_app_service/sub_microflow/create_variable/change_variable/for_each/custom_error。"
                          "★app/structure 必须来自 udcMicroflowSearchTreeEntityPost 的真实返回，不能手拼。",
        "microflow_gates": "对完整 dataSchema 跑 G1–G41 静态闸门（0 浏览器）。"
                           "判据：problems 为空才算过；非空时逐条形如 `G<n> [节点] 说明`。",
        "microflow_capability": "微流程节点能力矩阵：每个 actionType 的验证等级（CONSTRUCTED/"
                                "SCHEMA_VERIFIED/UI_VERIFIED/BUILD_VERIFIED/RUNTIME_VERIFIED）与证据文件。"
                                "传空 action 返回全局分布。",
        "expression_catalog": "表达式目录：kind=function 返回 88 个函数（可按 group 过滤）；"
                              "kind=variable 返回 131 个系统变量事实。",
        "custom_page_scaffold": "生成 customPage.tsx 骨架（含可选接口调用）。返回 target_path/artifact/"
                                "route/source。★新建目录后必须重启 dev server（启动时一次性 glob 扫描）。",
        "spi_catalog": "SPI 扩展点事实目录（5 格结论 + evidence 清单）。"
                       "★分级纪律：配置启用 ≠ 插件已加载 ≠ 实现被调用。",
        # ---- 设置域 7 子域（八大模块 setting/）----
        "option_set_category_body": "选项集分组 body → udcUdcEnumCategoryPost。★name 必须首字母大写（UDC_ENUM_0001）。",
        "option_set_body": "选项集 body → udcUdcEnumPost（落 udc_enum）。★与枚举 ctp_enum 是两套表，id 不互通。",
        "option_set_item_body": "选项集项 body → udcUdcEnumItemPost。★三槽位 name/caption/code 缺一不可。",
        "attribute_set_body": "字段集 body → REST /service/udc/attributeSet（驼峰）。attributes 恒空，字段走子接口。",
        "attribute_set_field_body": "字段集字段 body → GraphQL udcEntityAttributePost。★父 REST update 带 attributes 会被静默忽略。",
        "scalability_option_body": "扩展实体方案 body → REST /service/udc/scalability-option（连字符）。",
        "scalability_field_body": "扩展实体字段 body → GraphQL udcScalabilityPost。★CTPENUM 被拒；删除只能走 GraphQL。",
        "qrcode_body": "二维码/条码/链接码 body → REST /service/udc/qrcode-rule/（非 GraphQL）。★链接码 pcPagePath 必须来自 page_url。",
        "serial_scheme_body": "流水号方案 body → udcSerialSchemeCreatePost。★段列表字段名 serialSectionDtoList，段数 1~12，totalSize 自动算。",
        "serial_section": "流水号的一个段。type ∈ CONSTANT/CONTEXT/ENTITY/SERIAL。配合 serial_scheme_body 使用。",
        "parameter_body": "应用参数 body → udcCtpParameterDefinitonPost（★平台拼写少一个 i）。★dataTypeProperties 必须是对象。",
        "excel_template_body": "导入导出模板 body → REST /service/udc/excel/。★isCustom 必须 false，否则列表看不到。",
        "excel_template_column": "导入导出模板的一列。attributeFullName = <实体全类名>.<字段名>。",
        "capability_index": "按八大模块（microflow/setting/entity/application/expression/page/serial/write-chain）返回能力总索引：工具名 + 事实位置 + 契约位置。传空返回全量。",
        "microflow_trigger": "构造微流程触发器。kind ∈ MANUAL/SCHEDULE/EVENT/MF_EVENT。★SCHEDULE 无出入参；value ≥5（MINUTE 最小 5），传 1 会让调度任务根本不注册。",
        "microflow_data_schema": "组装完整 dataSchema（trigger + nodes + endNode）。★产出 endNode 是 9 键形态；MANUAL 要渲染参数面板需补 paramType，用 microflow_gates 查 G11。",
        "expression_filter": "构造 LIST_OPERATION FILTER 过滤条件表达式（返回 {title,schema}）。需显式 host+cookie。两种形态：field+op+const 或 spec(AST)。★containsText 参数顺序 (被查文本, 子串)。",
        "repo_sync": "客开仓库写操作 pull/commit/push。★必须 confirm=True；★commit 的 paths 必填且拒 -A 全量；★pull 只 --ff-only；★无上游分支直接拒。",
        "repo_state": "客开仓库只读状态：分支/remote/ahead/behind/改动/最近提交/工程形态。★只读，commit/push 不在这里；★拿不到回 ok=False 不返回空壳。",
        "code_targets": "客开代码该写在哪（custom_service/custom_page/spi/entity_ext）+ 约束。★不出死模板源码，代码由宿主写；★会先探五模块/单模块形态。",
        "project_shape": "探后端工程形态：五模块（只有 -ext/extend 可写）/ 单模块 / UNKNOWN。★两种形态并存，别默认五模块。",
        "repo_url": "拼客开仓库地址。★git_base 必填——域名随客户变、仓库组随环境变，不猜。可从已有 clone 的 local_repo_dir 反推。",
        "app_dependency_body": "构造添加依赖 body（SERVICE 应用依赖 / FRONTEND 组件依赖共用同一写口）。★params0 是数组；★FRONTEND 额外必须 10 个字段，缺了不生效；★写后平台自动串发一致性检测。",
        "app_dependency_remove": "构造移除依赖 body。★row_id 是依赖行 id，不是 appId/depAppName。应用依赖走 GraphQL 单删，组件依赖走 REST 批量删（两条路）。",
        "app_deploy_body": "构造沙箱「立即构建」body（构建+部署）。★声明成 query 实为写，会覆盖沙箱态。构建日志用 app_build_info 一把取，不用抓流。",
        "app_version_list": "发布版本列表 body（REST 裸数组）。★IN_appId 传 appName 字符串；响应不套 code 信封。",
        "app_build_info": "构建信息查询（含 logs[] 全文可回看）。★别名是 path: 不是 body:。",
        "entity_rule_body": "构造实体规则 body（MicroFlowDto 规则形态）+ 离线作用域校验。group_type 1=VALIDATE 2=ASSIGN_VALUE 3=DEFAULT_VALUE(★同实体只能一条)。★state 默认 20(RELEASE)，写 10 会查不到等于隐形。",
        "entity_rule_publish": "实体规则 checkSchema + create。需显式 host+cookie。★判据 content.check==true 且 errors==0（BOOT_0000 也可能 check=False）；校验不过时不执行 create，避免库里留空条件规则。",
        # ---- 需显式 host+cookie（不传不联网）----
        "microflow_publish": "把微流程发布到 RELEASE（create 之后的第二步）。需显式 host+cookie。"
                             "★判据：check=True 且 errors=[]；只看到 BOOT_0000 不算发布成功。",
        "expression_verify": "校验并编译表达式，返回 executableExpr。需显式 host+cookie。"
                             "★变量必须绑 schemas（只给 paramId 报 FORMULA_6058）；"
                             "executableExpr 由服务端返回，不要自己生成。",
        "expression_filter": "构造 LIST_OPERATION FILTER 过滤条件表达式（返回 {title,schema}）。需显式 host+cookie。两种形态：field+op+const 或 spec(AST)。★containsText 参数顺序 (被查文本, 子串)。",
        "filter_plan_body": "过滤方案创建 body：app_name + app_id + page_id + grid_suffix + "
                            "driven_entity + caption + conditions。",
    }

    enum_overrides: dict[str, dict[str, Any]] = {
        "deploy_plan": {
            "stereotype": {"enum": list(STEREO_TYPES)},
            "deploy_type": {"enum": list(DEPLOY_TYPES)},
        },
        "generate": {
            # generate consumes NormalizedAttribute, not deployment's dataType DTO.
            "attributes": {
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "caption": {"type": "string"},
                        "type": {"type": "string", "description": "NormalizedAttribute 类型；缺省为 UNKNOWN"},
                    },
                    "required": ["name"],
                },
            },
        },
        # `data_schema: Any` 会被 `_pytype_to_json_type` 兜底成 "string"，
        # 但它实际接受 dict（dataSchema 在函数内部才字符串化）—— 不覆盖会误拒合法入参。
        "microflow_create_body": {
            "data_schema": {"type": "object", "description": "dataSchema 结构（宿主填真值；内部字符串化）"},
            "trigger_type": {"type": "string", "enum": ["MANUAL", "AUTO", "SCHEDULE"]},
        },
        "index_body": {
            "field_ids": {"type": "array", "items": {"type": "integer"}},
        },
    }

    tools: list[dict] = []
    for key in TOOL_KEYS:
        fn = caps[key]
        schema = _schema_from_callable(fn)
        for prop_name, override in enum_overrides.get(key, {}).items():
            if prop_name in schema["properties"]:
                schema["properties"][prop_name].update(override)
        tools.append({
            "name": MCP_TOOL_NAMES[key],
            "description": descriptions[key],
            "inputSchema": schema,
        })
    return tools


# ---------------------------------------------------------------- 调用面

def _validate_params(schema: dict, params: dict) -> None:
    """缺必填/型错 → JsonRpcError(-32602)，message 指出字段名（DESIGN §4.3）。"""
    if not isinstance(params, dict):
        raise JsonRpcError(ERR_INVALID_PARAMS, "params must be an object")
    missing = [r for r in schema.get("required", []) if r not in params]
    if missing:
        raise JsonRpcError(ERR_INVALID_PARAMS, "missing required param(s): " + ", ".join(missing))
    for name, spec in schema.get("properties", {}).items():
        if name not in params:
            continue
        want = spec.get("type")
        got = params[name]
        checks = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "boolean": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict),
        }
        if want in checks and not checks[want](got):
            raise JsonRpcError(ERR_INVALID_PARAMS, f"param '{name}' must be {want}")
        if "enum" in spec and got not in spec["enum"]:
            raise JsonRpcError(ERR_INVALID_PARAMS, f"param '{name}' must be one of {spec['enum']}")


class McpServer:
    """stdio JSON-RPC 2.0 状态机（可注入 caps/allow_network，pytest 离线驱动）。"""

    def __init__(self, caps: dict[str, Callable] | None = None,
                 allow_network: bool | None = None, credential_file: str | None = None,
                 audit_dir: str | None = None):
        self._caps = caps  # None = 惰性 bootstrap（首次 tools/call 才装配）
        self._allow_network = (os.environ.get("SEEYON_ALLOW_NETWORK", "") in ("1", "true", "True")
                               if allow_network is None else allow_network)
        self._credential_file = credential_file or os.environ.get("SEEYON_CRED_FILE") or None
        self._audit_dir = audit_dir
        self._initialized = False

    # -- bootstrap 惰性装配（tools/list 不触发；首次 tools/call 才要真能力）--
    def _ensure_caps(self) -> dict[str, Callable]:
        if self._caps is None:
            from seeyon_host_bootstrap import bootstrap
            caps = bootstrap(credential_file=self._credential_file,
                             allow_network=self._allow_network,
                             audit_dir=self._audit_dir)
            self._caps = {k: caps[k] for k in TOOL_KEYS}
        return self._caps

    # -- 三个白名单 method --
    def _on_initialize(self, params: dict) -> dict:
        self._initialized = True
        return {"protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO}

    def _on_tools_list(self, params: dict) -> dict:
        # tools/list 不触发 bootstrap：schema 生成只需签名+常量（DESIGN §2.2）
        from seeyon_host_bootstrap import bootstrap
        dummy = bootstrap(credential_file=None, allow_network=False, audit_dir=None)
        return {"tools": build_tool_schemas({k: dummy[k] for k in TOOL_KEYS})}

    def _on_tools_call(self, params: dict) -> dict:
        name = params.get("name")
        args = params.get("arguments") or {}
        caps = self._ensure_caps()
        by_mcp = {v: k for k, v in MCP_TOOL_NAMES.items()}
        if name not in by_mcp:
            raise JsonRpcError(ERR_INVALID_PARAMS, f"unknown tool: {name}")
        key = by_mcp[name]
        schema = {t["name"]: t["inputSchema"] for t in build_tool_schemas(caps)}[name]
        _validate_params(schema, args)
        try:
            data = caps[key](**args)
        except JsonRpcError:
            raise
        except Exception as exc:  # 业务失败 → isError 结果信封（DESIGN §3 错误路径）
            return self._tool_error(f"{type(exc).__name__}: {exc}")
        return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, default=str)}],
                "isError": False}

    @staticmethod
    def _tool_error(message: str) -> dict:
        return {"content": [{"type": "text", "text": message}], "isError": True}

    # -- 帧循环 --
    def handle_frame(self, frame: dict) -> dict | None:
        """处理一帧请求；通知返回 None（无响应）。"""
        if not isinstance(frame, dict):
            return {"jsonrpc": "2.0", "id": None,
                    "error": {"code": -32600, "message": "invalid request"}}
        method = frame.get("method")
        msg_id = frame.get("id")
        is_notification = msg_id is None

        def _result(result: dict) -> dict | None:
            return None if is_notification else {"jsonrpc": "2.0", "id": msg_id, "result": result}

        def _error(err: JsonRpcError) -> dict | None:
            if is_notification:
                return None
            return {"jsonrpc": "2.0", "id": msg_id,
                    "error": {"code": err.code, "message": err.message}}

        if method == "notifications/initialized":
            return None
        try:
            if method == "initialize":
                return _result(self._on_initialize(frame.get("params") or {}))
            if method == "tools/list":
                return _result(self._on_tools_list(frame.get("params") or {}))
            if method == "tools/call":
                return _result(self._on_tools_call(frame.get("params") or {}))
            return _error(JsonRpcError(ERR_METHOD_NOT_FOUND, f"method not found: {method}"))
        except JsonRpcError as err:
            return _error(err)
        except Exception as exc:
            return _error(JsonRpcError(-32603, f"internal error: {type(exc).__name__}: {exc}"))

    def serve(self, stdin=None, stdout=None) -> int:
        """逐行读帧/写响应；EOF 退出。返回 0。"""
        fin = stdin or sys.stdin
        fout = stdout or sys.stdout
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                frame = json.loads(line)
            except json.JSONDecodeError as exc:
                resp = {"jsonrpc": "2.0", "id": None,
                        "error": {"code": -32700, "message": f"parse error: {exc}"}}
            else:
                resp = self.handle_frame(frame)
            if resp is not None:
                fout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                fout.flush()
        return 0


def main() -> int:
    # stdio 直跑场景：仓库根不在 sys.path（pytest 场景已由 conftest/测试侧注入）
    _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    return McpServer().serve()


if __name__ == "__main__":
    sys.exit(main())
