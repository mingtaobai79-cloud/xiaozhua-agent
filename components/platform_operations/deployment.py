"""Deployment plan generator — readonly plan data, host executes.

把「建实体 → 建属性 → 触发 RELEASE 构建 → 验证物理表落库」组织成一份可执行的
方案 data。agent 本身不出写（写门 DENIED，见 layer.py 的 write/effective 判定），
宿主（Hermes / Claude Code / Codex）拿这份方案去调真实端点执行。

证据基线（2026-09-24 test2 实测 + 活体 pod 反编译 + RDS 直连，非臆测）：
  - 设计态写面：POST /service/udc/entity（EntityController.create, 网关+设计器 cookie）
  - 属性写面：POST /service/udc/entity/attribute（createAttribute）
  - 构建触发面：POST /service/udc/runtime/deploy-normal（DeployController.deployNormal →
      ApplicationAppService.deployNormal；类级 @RequestMapping("udc/runtime")，
      body 须包成 {"deployDto":{...}}（@MultiRequestBody）；执行体是 boot-starter-sandbox 的
      UdcAppDeployService + PipelineProperties 流水线 + SandboxK8sService）
  - 部署记录：udc_test2.udc_deploy_record（deploy_type=2 即 RELEASE / 0 即 TEST；state=1 成功 / 2 失败）
  - 构建硬门：一致性检测（CdpDataDetectionTask，约 2 分钟），未过则整单失败
  - 物理表：建在应用自身库（如 <app_id>_test2），非 udc_test2

铁律 040402：app_id / 网关 / 凭据 / 枚举值域 一律来自 config 与活体证据引用，
代码不写死机器值。枚举值域是「平台侧受控词表」的实测快照，标注来源，随活体复核。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

SCHEMA_ID = "seeyon-deployment-plan.v1"

# ---- 平台受控词表（活体实测快照，非发明；随活体复核刷新） ----
# stereotype 值域：从 test2 目标应用 169 个真实实体回读统计（GET /udc/entity/primary/select-by-appid）
STEREO_TYPES = ("archive", "standard", "bill", "archiveTree")

# dataType 值域：从 bill 单据实体 51 个属性回读统计（GET /udc/entity/attribute/select-all-by-entity-id）
DATATYPES = ("ENTITY", "DATETIME", "ENUM", "STRING", "MULTILINESTRING",
             "BOOLEAN", "BIGINTEGER", "INTEGER", "DECIMAL", "DATE", "Serial")

# 构建维度枚举：活体 pod 反编译 DeployParamDto / 三个枚举类（bytecode）
DEPLOY_TYPES = ("TEST", "RELEASE", "ON_ONLINE", "DELTA")          # DeployTypeEnum
PROJECT_TYPES = ("FRONTEND", "BACKEND", "ALL")                    # ProjectTypeEnum
TERMINAL_TYPES = ("ALL", "PC", "MOBILE")                          # TerminalTypeEnum


@dataclass
class DeploymentStep:
    op: str
    method: str
    path: str
    body: Any = None
    verify: str = ""
    note: str = ""
    def to_dict(self): return asdict(self)


@dataclass
class DeploymentPlan:
    schema: str = SCHEMA_ID
    readonly_plan: bool = True
    application_id: str = ""
    entity_name: str = ""
    stereotype: str = "bill"
    steps: list[DeploymentStep] = field(default_factory=list)
    enums: dict[str, list[str]] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)

    def to_dict(self):
        return {"schema": self.schema, "readonly_plan": self.readonly_plan,
                "application_id": self.application_id, "entity_name": self.entity_name,
                "stereotype": self.stereotype,
                "steps": [s.to_dict() for s in self.steps],
                "enums": self.enums, "evidence": self.evidence, "unknowns": self.unknowns}


# 字段名 → 平台 dataType 的保守默认映射（未命中即 UNVERIFIED，不臆造）
_NAME_HINT: tuple[tuple[str, str], ...] = (
    ("date", "DATE"), ("datetime", "DATETIME"), ("time", "DATETIME"),
    ("amount", "DECIMAL"), ("price", "DECIMAL"), ("decimal", "DECIMAL"),
    ("money", "DECIMAL"), ("int", "INTEGER"), ("count", "INTEGER"),
    ("no", "STRING"), ("name", "STRING"), ("status", "ENUM"),
    ("flag", "BOOLEAN"), ("bool", "BOOLEAN"), ("text", "MULTILINESTRING"),
)


def infer_datatype(field_name: str, explicit: str | None = None) -> tuple[str, bool]:
    """返回 (dataType, verified)。explicit 命中平台词表则 verified=True；
    否则按字段名 hint 猜（verified=False，进 unknowns 待宿主确认）。"""
    if explicit:
        up = explicit.upper()
        if up in DATATYPES:
            return up, True
        # explicit 是 java 类型（如 java.math.BigDecimal）→ 保守映射
        # 顺序关键：LocalDateTime 必须先于 LocalDate/Date 判断（都含 "Date" 子串）
        if "LocalDateTime" in explicit:
            return "DATETIME", False
        if "BigDecimal" in explicit:
            return "DECIMAL", True
        if "Date" in explicit:
            return "DATE", False
        return "STRING", False
    low = field_name.lower()
    for hint, dt in _NAME_HINT:
        if hint in low:
            return dt, False
    return "STRING", False


# 字段语义键：只有“平台 AttributeDto 实际接受、且有 LIVE/静态证据”的键才透传；
# 输入提供且命中此白名单才进 body（未命中的一律不进，避免塞平台不认的键 → BOOT_3002/被忽略）。
# 白名单证据（seeyon-udc-design-time-build skill，metadata-artifact-apis + 设计态建属性节）：
#   - 建属性 create 最小形态 = appId + entityId + name + caption + dataType（缺 dataType → BOOT_1001）
#   - 多选人员族（LIVE 建后回读 multi_select=1）= dataType:ENTITY + multiSelect:true
#     + relationType:1 + relationEntity:com.seeyon.organization...OrgMember + relationApp:organization
#   - uniqueness 是 Boolean（传字符串报 BOOT_3002）
# 注意：indexSource 属于**索引对象**（udc_index.index_source），不是属性键，已剔除；
#       required/length/defaultValue 无建属性 create 接口的受键证据，不进白名单（宿主要带须先取证）。
_ATTR_SEMANTIC_KEYS: tuple[str, ...] = (
    "multiSelect", "relationType", "relationApp", "relationEntity", "uniqueness",
)


def _attr_body(name: str, caption: str, dt: str, a: dict, app_id: int, entity_id: str) -> dict:
    """attribute body：appId + entityId + name/caption/dataType + 输入实际提供的白名单语义键。

    appId/entityId 必填（缺 → BOOT_1001）；entityId 建实体后才有值，plan 阶段用占位符
    <entity_id>（宿主建实体返回后替换，与 page step 同一约定）。
    未提供的白名单语义键不进 body（不臆造，留给宿主补或进 unknowns）。
    """
    body = {"appId": app_id, "entityId": entity_id, "name": name, "caption": caption, "dataType": dt}
    for key in _ATTR_SEMANTIC_KEYS:
        if key in a and a[key] is not None:
            body[key] = a[key]
    return body


def _to_app_id(application_id: str) -> int:
    """app name(如 app9000000000000000001) → 数字 appId(3289082814923688017)。

    LIVE 实测 EntityDto.appId 是数字 Long；设计器/网关用完整 app name。
    取 name 末尾连续数字（app name 以数字 guid 结尾，平台 169 实体回读印证）。
    已是纯数字则原样转 int。
    """
    import re
    m = re.search(r"(\d+)$", str(application_id))
    if not m:
        raise ValueError(
            f"无法从 application_id={application_id!r} 提取数字 appId"
            f"（需以数字串结尾，如 app9000000000000000001；"
            f"纯数字亦可）。请传入含尾数段的 app name 或数字 appId。"
        )
    return int(m.group(1))


def build_deployment_plan(application_id: str, entity_name: str, caption: str,
                          attributes: list[dict], stereotype: str = "bill",
                          deploy_type: str = "RELEASE",
                          project_type: str = "ALL", terminal_type: str = "ALL",
                          hand_written: bool = False) -> dict[str, Any]:
    """生成「建实体+建属性+触发构建+验证」的可执行方案 data（不执行）。

    attributes: [{name, caption, dataType?}]；dataType 缺省时按名推断并进 unknowns。
    hand_written: True = 建「自定义页面」（`handWritten:true` + `pageType:OTHER`），
                  此时不建 LIST/DETAIL；False = 建标品列表页+详情页对。
    所有 path 走网关 service 前缀（铁律：调用方/宿主拼 {gateway_base}{prefix}{path}）。

    ⚠ 2026-11-09 LIVE 实测修正两条（此前契约写错）：
      ① `pageItems[].menuId` **必填** —— 缺了平台不报错但页面检查出 N 个阻断
         （N = 页面数），设计器里表现为「菜单组件」红字。建页前必须先建菜单节点
         （GraphQL `udcFunctionPost`，type=MENU，parentId='0' 为分组），
         用返回的 content 作 menuId。
      ② `page-info/base-info/create` 收**单对象**，数组包装报
         `BOOT_3002 属性的值反序列化为PageDefinitionDto类型时失败`。
         宿主必须逐条 POST（LIST、DETAIL、自定义页各一次），不是一次发数组。
    """
    unknowns: list[str] = []
    if stereotype not in STEREO_TYPES:
        unknowns.append(f"stereotype={stereotype!r} 不在实测值域 {STEREO_TYPES}")

    app_id_num = _to_app_id(application_id)
    # entityId 建实体后才有值，plan 阶段用 <entity_id> 占位（宿主建实体返回后替换，
    # 与 page step 的 <entity_id> 同一约定）
    entity_id_placeholder = "<entity_id>"
    attr_bodies = []
    for a in attributes:
        name = a.get("name")
        if not name:
            unknowns.append("attribute missing name")
            continue
        dt, ok = infer_datatype(name, a.get("dataType"))
        attr_bodies.append(_attr_body(name, a.get("caption", name), dt, a, app_id_num, entity_id_placeholder))
        if not ok:
            unknowns.append(f"attribute {name} dataType={dt} 由名推断（未证实，宿主确认后再建）")

    # ---- 页面 body（2026-11-09 实测修正：单对象逐条 POST + menuId 必填）----
    # 自定义页面（hand_written=True）：只出一个 OTHER 页，handWritten=true；
    # 标品页（False）：LIST + DETAIL 一对。两种都要 pageItems[].menuId。
    _purl = entity_name.lower()
    if hand_written:
        page_bodies = [{
            "appId": app_id_num, "name": _purl + "page", "caption": caption,
            "pageType": "OTHER", "pageUrl": _purl + "page", "curTerminalType": "PC",
            "urlType": "PC", "actionType": "NORMAL",
            "handWritten": True, "masterEntityIds": entity_id_placeholder,
            "pageItems": [{"pageUrl": _purl + "page", "urlType": "PC", "menuName": caption,
                           "menuId": "<menu_id>", "terminalType": "PC",
                           "actionType": "NORMAL", "orderNo": 1}],
        }]
    else:
        page_bodies = [{
            "appId": app_id_num, "caption": f"{caption}列表", "pageType": "LIST",
            "masterEntityIds": entity_id_placeholder, "pageUrl": _purl + "list",
            "curTerminalType": "PC", "urlType": "PC", "actionType": "NORMAL",
            "pageItems": [{"pageUrl": _purl + "list", "urlType": "PC", "menuName": f"{caption}列表",
                           "menuId": "<menu_id>", "terminalType": "PC",
                           "actionType": "NORMAL", "orderNo": 1}],
        }, {
            "appId": app_id_num, "caption": f"{caption}详情", "pageType": "DETAIL",
            "masterEntityIds": entity_id_placeholder, "pageUrl": _purl + "detail",
            "curTerminalType": "PC", "urlType": "PC", "actionType": "NORMAL",
            "pageItems": [{"pageUrl": _purl + "detail", "urlType": "PC", "menuName": f"{caption}详情",
                           "menuId": "<menu_id>", "terminalType": "PC",
                           "actionType": "NORMAL", "orderNo": 1}],
        }]

    plan = DeploymentPlan(
        application_id=application_id, entity_name=entity_name, stereotype=stereotype,
        steps=[
            DeploymentStep(
                op="udc.entity.create", method="POST", path="/service/udc/entity",
                body={"appId": app_id_num, "name": entity_name, "caption": caption,
                      "stereotype": stereotype, "entityNature": "MAIN",
                      "features": "basic,approve,organization,billBasic,termination,suspend,nullify",
                      "multiplicity": "ONE2MANY", "category": "ENTITY",
                      "parentEntityId": "0", "superior": "0", "validate": True},
                verify="GET /service/udc/entity/{id} → publishState/tableName",
                note="bill 单据族完整形态（features 照已建 bill 实体）；entityNature/stereotype 缺会报 UDC_ENTITY_0010/BOOT_1001"),
            DeploymentStep(
                op="udc.entity.attribute.create", method="POST", path="/service/udc/entity/attribute",
                body=attr_bodies,
                verify="GET /service/udc/entity/attribute/select-all-by-entity-id/{entityId}",
                note="body 是逐条列表（宿主循环，逐个 POST 单对象）——数组包装一次性 POST 报 BOOT_3002 "
                     "「Failed to deserialize ... to type AttributeDto」；"
                     "每条带 appId(数字 Long)+entityId(建实体返回后替换 <entity_id> 占位符)+name+caption+dataType；"
                     "dataType 缺报 BOOT_1001；platform auto 补单据族系统属性。"
                     "语义键（multiSelect/relationType/relationApp/relationEntity/uniqueness）仅输入提供时携带"),
            DeploymentStep(
                op="udc.page.create", method="POST", path="/service/udc/page-info/base-info/create",
                body=page_bodies,
                verify="GET /service/udc/page-info/select-by-appId/{appId} 回读新页 caption+relationGroupId",
                note="body 是**逐条模板列表**——每个元素单独 POST 一次；数组整体包装报 BOOT_3002 "
                     "「属性的值反序列化为PageDefinitionDto类型时失败」（2026-11-09 实测）。"
                     "必填链 appId/pageType/masterEntityIds/pageUrl/curTerminalType/urlType "
                     "+ pageItems[].{pageUrl,urlType,menuName,menuId,terminalType,actionType=NORMAL}；"
                     "<menu_id> 必须先建菜单节点（GraphQL udcFunctionPost type=MENU）再替换——"
                     "缺 menuId 平台不报错，但页面检查出 N 个阻断（设计器「菜单组件」红字）。"
                     "hand_written=True 时只出一个 pageType=OTHER + handWritten=true 的自定义页。"),
            DeploymentStep(
                op="udc.deploy.normal", method="POST", path="/service/udc/runtime/deploy-normal",
                body={"deployDto": {"appId": app_id_num, "deployType": deploy_type,
                                    "projectType": project_type, "terminalType": terminal_type}},
                verify="RDS udc_test2.udc_deploy_record 最新行（deploy_type=2 state=1）+ 应用库 SHOW TABLES",
                note="触发 sandbox 流水线（UdcAppDeployService）；构建即部署，非实体级 publish(要密码那条)。放在建页之后：页面设计稿随构建发布。"
                     "路径 09-27 LIVE 确诊：类级 @RequestMapping(\"udc/runtime\") + 方法级 deploy-normal，裸 /service/udc/deploy-normal 经 GET 探针=404（无映射）；"
                     "形参注 @MultiRequestBody（非 @RequestBody），body 必须按形参名包成 deployDto，平铺 → EL1007E。"
                     "硬门：一致性检测（CdpDataDetectionTask ~2 分钟），未过则整单 state=2（无部分成功），明细只在 Redis。"
                     "★ 2026-11-09 实测警告：本条 REST + deployType=TEST **返回 BOOT_0000 但不出包**——"
                     "GET /service/udc/sandbox/delta-build-info/{appId} 一直 state=NONE、buildVersion 空，"
                     "新代码永远不生效。要真出包必须走 GraphQL："
                     "POST /service/udc/graphql?udcRuntimeDeployNormalPost，"
                     "variables.params0.deployDto = {projectType:ALL,terminalType:ALL,deployType:RELEASE,"
                     "appId,generateLog:true}（RELEASE 在此语义为「测试发布」，正式上架是 ON_ONLINE）。"
                     "判据只认 pod 内 BOOT-INF/lib/<app>-ext-x.y.z.jar 版本号递增，不看接口 message。"),
        ],
        enums={"stereoTypes": list(STEREO_TYPES), "datatypes": list(DATATYPES),
               "deployTypes": list(DEPLOY_TYPES), "projectTypes": list(PROJECT_TYPES),
               "terminalTypes": list(TERMINAL_TYPES)},
        unknowns=unknowns,
        evidence=[
            {"fact": "stereotype 值域", "level": "OBSERVED_LIVE", "src": "GET /udc/entity/primary/select-by-appid (169 实体)"},
            {"fact": "dataType 值域", "level": "OBSERVED_LIVE", "src": "GET /udc/entity/attribute/select-all-by-entity-id (51 属性)"},
            {"fact": "deploy 枚举/deployNormal 路径", "level": "VERIFIED_STATIC_BYTECODE", "src": "pod javap DeployController/DeployParamDto/DeployTypeEnum"},
            {"fact": "物理表落应用库非 udc_test2", "level": "OBSERVED_LIVE", "src": "RDS SHOW TABLES <app_table> @ <app_id>_test2"},
            {"fact": "RELEASE=deploy_type 2, 构建成功 state 1", "level": "OBSERVED_LIVE", "src": "udc_deploy_record 2026-09-24 15:52 行"},
        ],
    )
    return plan.to_dict()


__all__ = ["DeploymentPlan", "DeploymentStep", "build_deployment_plan", "infer_datatype",
           "STEREO_TYPES", "DATATYPES", "DEPLOY_TYPES", "PROJECT_TYPES", "TERMINAL_TYPES", "SCHEMA_ID"]
