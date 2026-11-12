"""S7-固化: LIVE 写链实验 → 仓内可执行构建模板（live_write_templates.py）。

每条模板 = 已在 datamigration 应用 LIVE 验证的 写操作契约：
  channel (rest|graphql) + path/op + body 模板（javap 权威字段）+ 证据级别。
证据边界：LIVE（真调 + 回读验证）。planner plan_build 可直接引用。
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_ID = "udc.live.write-template.v1"
EVIDENCE = "LIVE (datamigration 9000000000000000002, 2026-10-14)"

# 8 条已验证写链
WRITE_TEMPLATES: dict[str, dict] = {
    # ---- REST 面 ----
    "entity_create": {
        "channel": "rest", "method": "POST", "path": "/service/udc/entity",
        "body": {"appId": "<appId>", "name": "<name小写开头>", "caption": "<caption>",
                 "description": "<desc>", "stereotype": "standard", "type": "MAIN"},
        "verified": "id=474806313816300867 (7→8 回读一致)",
        "note": "自动生成 9 预置字段（creator/tenantId/draft/version…）",
    },
    "attribute_create_text": {
        "channel": "rest", "method": "POST", "path": "/service/udc/entity/attribute",
        "body": {"appId": "<appId>", "entityId": "<entityId>", "name": "<fieldName>",
                 "caption": "<caption>", "dataType": "STRING",
                 "dataTypeCategory": "PRIMITIVE", "type": "INPUT", "notNull": False},
        "verified": "id=8016904624316689195",
    },
    "attribute_create_members": {
        "channel": "rest", "method": "POST", "path": "/service/udc/entity/attribute",
        "body": {"appId": "<appId>", "entityId": "<entityId>", "name": "<fieldName>",
                 "caption": "<caption>", "dataType": "ENTITY",
                 "dataTypeCategory": "PRIMITIVE",
                 "relationEntity": "com.seeyon.organization.domain.core.entity.OrgMemberMetadata",
                 "relationApp": "organization",
                 "type": "LIST", "multiSelect": True, "notNull": False},
        "verified": "id=-5827776113672387650（人员多选=人员多选四要件的 API 形态）",
    },
    "attribute_update": {
        "channel": "rest", "method": "POST", "path": "/service/udc/entity/attribute/update",
        "body": "<findById 式回读的字段全量 DTO（select-all-by-entity-id 取单项）+ appId + 改动字段>",
        "verified": "expText caption 改名 BOOT_0000",
        "constraints": ["全量回传（回读单项 → 改 → update）"],
    },
    "entity_update": {
        "channel": "rest", "method": "POST", "path": "/service/udc/entity/update",
        "body": "<findById 回读的实体全量 DTO + appId + 改动字段（如 caption）>",
        "verified": "caption+V2 BOOT_0000 content=1",
        "constraints": ["全量回传"],
    },
    "attribute_create_ctpenum": {
        "channel": "rest", "method": "POST", "path": "/service/udc/entity/attribute",
        "body": {"appId": "<appId>", "entityId": "<entityId>", "name": "<fieldName>",
                 "caption": "<caption>", "dataType": "CTPENUM",
                 "dataTypeCategory": "PRIMITIVE", "relationEntity": "<enumId>",
                 "type": "SELECT", "notNull": False},
        "verified": "id=2166766729287798468 (引用 XzhEnum)",
    },
    "enum_create": {
        "channel": "rest", "method": "POST", "path": "/service/udc/udc-enum",
        "body": {"appId": "<appId数字Long>", "name": "<Name大写开头>", "caption": "<caption>",
                 "enable": True, "edit": True, "orderNo": 999, "udcEnumType": "DEFAULT"},
        "verified": "id=3934748939202274853",
        "constraints": ["appId 数字 Long", "name 大写字母开头",
                        "udcEnumType ∈ DEFAULT|CONNECTOR|DYNAMIC_DEPENDENCY",
                        "枚举项不能一体创建（enumId 必填→分两步）"],
    },
    "enum_item_create": {
        "channel": "rest", "method": "POST", "path": "/service/udc/udc-enum-item",
        "body": {"appId": "<appId数字Long>", "enumId": "<enumId>", "name": "ONE",
                 "code": 1, "caption": "<caption>", "orderNo": 1, "enable": True},
        "verified": "2 项回读一致（ONE/TWO code 1/2）",
        "constraints": ["item.code 必填 Integer"],
    },
    "index_create": {
        "channel": "rest", "method": "POST", "path": "/service/udc/index",
        "body": {"appId": "<appId>", "entityId": "<entityId>", "name": "<idxName>",
                 "caption": "<caption>", "fieldIds": "<attrId逗号分隔>",
                 "fieldNames": "<names>", "fieldCaptions": "<captions>", "type": "NORMAL"},
        "verified": "id=8907545166533903531",
        "note": "回读接口 /udc/index/entity/list body 形态待调（SingleRequest）",
    },
    "page_create": {
        "channel": "rest", "method": "POST", "path": "/service/udc/page-info/base-info/create",
        "body": {"appId": "<appId>", "caption": "<caption>", "pageType": "SEARCH_LIST",
                 "pageUrl": "<pageUrl小写>", "masterEntityIds": "<entityId>",
                 "groupId": 0, "curTerminalType": "PC",
                 "pageItems": [{"urlType": "PC", "pageUrl": "<pageUrl>",
                                "actionType": "INSERT", "menuId": "<先建菜单>",
                                "menuName": "<menuCaption>", "orderNo": 1}]},
        "verified": "id=1520098474917276520 (21→22, relationGroupId 自动生成)",
        "constraints": ["PageDefinitionDto（javap 权威）：curTerminalType+pageItems[].urlType",
                        "页面必须挂菜单（pageItems[].menuId）→ 先 menu_create",
                        "真实路径带 page-info 前缀（_api_full 拼接缺前缀已证 404）"],
    },
    "page_schema_draft": {
        "channel": "rest", "method": "POST", "path": "/service/udc/page-info/update-draf",
        "body": {"appId": "<appId>", "id": "<pageId>", "relationGroupId": "<rgId>",
                 "draftPageSchema": "<真绑实体 schema JSON 字符串（见 PAGE-SCHEMA-REAL-BIND.md 三要素）>",
                 "pageUrl": "<pageUrl>", "urlType": "PC"},
        "verified": "content=1；回读 schemaState EMPTY→DRAFT",
        "constraints": ["draftPageSchema 是 JSON 字符串（children=id引用，实体在 childById）",
                        "真绑定三要素缺一不可：①dataSource(ENTITY+fullName) ②settings.columns[](逐字段) ③uiModel",
                        "fullName 硬格式：com.seeyon.<appName>.domain.entity.<Name大写开头>",
                        "成熟列表页组件树 = UdcContainer(含UdcFilter) + UdcDataGridView"],
    },
    "page_schema_formal": {
        "channel": "rest", "method": "POST", "path": "/service/udc/page-info/update",
        "body": {"appId": "<appId>", "id": "<pageId>", "relationGroupId": "<rgId>",
                 "pageSchema": "<同 draft 的 schema 字符串>", "pageUrl": "<pageUrl>",
                 "urlType": "PC", "pageType": "SEARCH_LIST",
                 "caption": "<caption>", "masterEntityIds": "<entityId>"},
        "verified": ("两次 LIVE：①13 列全绑实验实体字段 FORMAL；"
                     "②业务列2(剔9系统字段)+行按钮3(查看/编辑/删除)+事件3(openPage view/edit+ENTITY_DELETE) FORMAL"),
        "constraints": ["草稿（update-draf）与正式（update）body 同构，字段名不同（draftPageSchema/pageSchema）",
                        "表格列只放业务字段——9 系统字段(creator/updater/createTime/updateTime/"
                        "tenantId/draft/version/creatorDepartment/creatorPost/creatorInstitution/id)"
                        "设计器默认剔除（成熟页 13 列零系统字段实证）",
                        "行按钮 = uiModel.controlledProps[]（parentCode=actionColumnOperates）"
                        "+ flowAuthKeys（topOperates/actionColumnOperates 各含 正常/禁用/隐藏）",
                        "行按钮事件 = 组件 events[]：actionType ∈ buildin(openPage+pageInfoType=DETAIL"
                        "+openMode=view|edit) | widget(ENTITY_DELETE) | microflow(须真实微流程id)"],
    },
    # ---- GraphQL 面 ----
    "menu_create": {
        "channel": "graphql", "op": "udcFunctionPost",
        "gql": ("mutation udcFunctionPost($body: udcFunctionPostInputBody)"
                "{ udcFunctionPost(body: $body) { code data { content } message status } }"),
        "body": {"appId": "<appId>", "name": "<menuName>", "caption": "<caption>",
                 "type": "MENU", "terminalType": "PC", "parentId": "0", "orderNo": 999},
        "verified": "id=7853445889453184321",
    },
    "microflow_create": {
        "channel": "graphql", "op": "udcMicroflowCreatePost",
        "gql": ("mutation udcMicroflowCreatePost($body: udcMicroflowCreatePostInputBody)"
                "{ udcMicroflowCreatePost(body: $body) { code data { content } message status } }"),
        "body": {"appId": "<appId>", "name": "<mfName>", "caption": "<caption>",
                 "type": "CUSTOM", "triggerType": "MANUAL", "groupType": "DEFAULT",
                 "nodes": [], "input": None, "output": None, "trigger": {}},
        "verified": "id=5810815099733137875（DRAFT）；⚠️ 空基座 dataSchema=null → 设计器打开报"
                    "「微流程数据加载失败」，必须紧跟 microflow_update_dataSchema 补全",
        "constraints": ["创建后必须补 dataSchema（对照真实微流程结构）:",
                        "dataSchema={endNode(END_NODE/output STRING), output, input, "
                        "sourceType:PAGE, trigger(type:MANUAL), nodes:[]} 的 JSON 字符串",
                        "★★★手写简写 schema 会让设计器出参区渲染空白 + 检查红点。必须【复制】同应用"
                        "一个真实微流程的 dataSchema 当骨架：endNode/trigger 各有 17/11 个键，"
                        "缺 nodeId(MFEndNode/MFStartNode)、paramType、caption 就找不到节点。只清 nodes。",
                        "★★★output 不能是 null：出参面板用 output.desc 覆盖 endNode.desc，"
                        "null 会让 desc 变 undefined。最小合法值 {\"desc\":\"\",\"hasPagination\":false}。",
                        "★★CDP 传含中文 body 禁用裸 atob()（按 latin1 解，中文全乱成 éªè¯...）："
                        "必须 Uint8Array.from(atob(x),c=>c.charCodeAt(0)) + new TextDecoder('utf-8')。",
                        "微流程列表查询 op=udcMicroflowSearch，body 三段结构：",
                        "{pageInfo:{needTotal,pageNumber,pageSize,pages,total}, params:{appId,"
                        "IN_type:[SERVICE,CUSTOM]}, sort:{orders:[{direction,property}]}}",
                        "search 响应字段路径 = data.content[]（op 类型直接包 data，非标准 code 包装）"],
    },
    "microflow_update_dataSchema": {
        "channel": "graphql", "op": "udcMicroflowUpdatePost",
        "gql": ("mutation udcMicroflowUpdatePost($body: udcMicroflowUpdatePostInputBody)"
                "{ udcMicroflowUpdatePost(body: $body) { code data { content } message status } }"),
        "body": "<findById 回读的全量 DTO + dataSchema=合法 JSON 字符串 + appId>",
        "verified": ("两次 LIVE：①结构补全 1152B；②入参定义修正 1403B"
                     "（input.desc=同步任务ID/output.desc=执行结果，回读一致）"),
        "constraints": ["update 是全量回传（findById → 改 → update）",
                        "dataSchema 结构对照真实微流程（SyncNowData）逐字段对齐",
                        "★★入参定义面板读 dataSchema.trigger（非 input！）；出参读 endNode，且 aT 用 output.desc 覆盖 endNode.desc。",
                        "  证据：module-37302 Uu(): flowNodes[trigger.nodeId]=clone(trigger)，nodes.push(endNode)；",
                        "        module-64734: 入参Card formData=flowNodes['MFStartNode'] 去 {id,nodeId,type,actionType,canRollback,runAfter}",
                        "        module-18640 aT: B.endNode={...B.endNode, desc:B.output?.desc, hasPagination:B.output?.hasPagination}",
                        "  ☆LIVE 踩坑：只改 input.desc → 面板入参名称仍为空（因为面板读 trigger.desc）；必须同时写 trigger.desc+basic+paramType",
                        "  参数名称字段 key='desc'（required，placeholder「请输入显示名称」，module-83128 FLOW_INPUT.items）",
                        "  paramType: NONE|BASIC|ENTITY_OBJECT|DEFAULT_OBJECT；BASIC 子字段 basic 值域:",
                        "    STRING|INTEGER|LONG|BIGINTEGER|DECIMAL|BOOLEAN|DATE|DATETIME|OBJECT|DTO|ARRAY（module-65420 pe）",
                        "  保存链: 面板保存修改 → G.d(节点,表单值,FLOW_INPUT/FLOW_OUTPUT) → OK(nodeId,objectInfo) → RF 组 dataSchema",
                        "          → updateMicroflowSchema(有id)=udcMicroflowUpdatePost | saveMicroflowSchema(无id)=udcMicroflowCreatePost",
                        "          | checkAndUpdateMicroflowSchema(非DRAFT,先节点校验)=udcMicroflowCheckSchemaUpdatePost",
                        "  列表: udcMicroflowSearch，body={pageInfo,params:{appId,IN_type:[SERVICE,CUSTOM]},sort:{orders:[{direction,property}]}}",
                        "  trigger 三大类: MANUAL(标准/自定义) | SCHEDULE(定时) | 事件(业务事件)"],
        "doc": "docs/audit/udc-semantics/MICROFLOW-PARAMS-TAB-DATACHAIN.md",
    },
    "microflow_business_event_trigger": {
        "channel": "graphql",
        "ops": ["udcMicroflowFilterEventPost", "udcMicroflowSearchAppsPost",
                "udcMicroflowFilterMqPost"],
        "body": {
            "应用内(实体事件)": {"appId": "<appId>", "id": "<微流程id>",
                                 "sourceTypes": ["ENTITY"], "eventTypes": ["ENTITY_EVENT"]},
            "应用列表": {"appId": "<appId>", "needBootStarter": True, "needConnectorApp": True},
            "应用间(MQ消息)": {"appId": "<appId>", "appName": "<app.name>", "microFlowId": "<微流程id>"},
        },
        "verified": ("LIVE PASS：①应用内 45 条实体事件（5实体×9事件）；②应用间 bpm 29 条/"
                     "organization 18/ctp-message 2/cip-capability 7；③写入 BPM「流程发起消息」"
                     "BpmStartEvent 后回读一致"),
        "constraints": [
            "★★事件选择器两个 tab：应用内(INTERNAL) 走 filterEvent，应用间(EXTERNAL) 走 filterMq。",
            "  应用内: EventSourceEnum 只接受 ENTITY（BPM/MQ/MESSAGE 报 No enum constant）；",
            "          EventTypeEnum 只接受 ENTITY_EVENT；每实体 9 事件 = {Before,After,TransactionSuccess}×{Create,Update,Delete}",
            "          eventClassName=com.seeyon.udc.common.event.X；eventMfCustomDtoName={实体短名}.{eventClassName}",
            "          messageInfo: {caption,messageSource:'EVENT'|'MICRO_FLOW_EVENT',eventFullName:eventClassName,",
            "            eventDataFullName,eventMfCustomDtoName,eventName:name,currentId,currentType,",
            "            output:{id:eventDataFullName,dataType:'DTO',type:'OBJECT',javaType:eventMfCustomDtoName,appName}}",
            "  应用间: 先 searchApps 选应用 → filterMq 取消息；javaType=contentDto.item.itemType||contentDto.type；",
            "          arrayOrObject = contentDto.type=='java.util.List' ? 'ARRAY' : 'OBJECT'",
            "          messageInfo: {caption,messageSource:'MESSAGE',eventDataFullName:javaType,topic,",
            "            currentId:fullName,currentType:appName,output:{id:javaType,dataType,type:arrayOrObject,javaType,appName}}",
            "          cip-connector/INTEGRATION 应用额外 connectorMessageInfo:customs, messageSource:'CONNECTOR'",
            "  ★BPM 事件在【应用间】tab（appName=bpm, topic=BPM），不在应用内——不要死盯 sourceTypes 枚举",
            "  trigger 终态(BUSINESS_EVENT): {nodeId,name,caption:'事件监听',description:'',type:'BUSINESS_EVENT',",
            "    input:null,output:<事件数据DTO>,messageInfo:<见上>,expression:null,title:'事件数据'}",
            "  面板三字段: 事件选择(eventSelector,required) / 触发条件(filterExpression,需先选事件) / 节点出参名称(title)",
        ],
        "doc": "docs/audit/udc-semantics/MICROFLOW-BUSINESS-EVENT-TRIGGERS.md",
    },
    "microflow_schedule_trigger": {
        "channel": "graphql", "op": "udcMicroflowCreatePost",
        "body": {"appId": "<appId>", "type": "CUSTOM|SERVICE", "triggerType": "SCHEDULE",
                 "trigger": {"nodeId": "CUSTOM_<nanoid6>|MFStartNode", "caption": "定时任务", "type": "SCHEDULE",
                             "scheduleCronRule": {"jobCode": "<19位数字>", "jobCaption": "<任务名>",
                                                  "cronRules": [{"cycleType": "DAY", "rotationType": "MINUTE",
                                                                 "type": "ANY", "value": "5",
                                                                 "startTime": None, "endTime": None}]},
                             "isCompleted": True}},
        "verified": ("LIVE PASS：①自定义 id=-7551185604892573345；②标品 id=-8675485534859429311"
                     "（SERVICE，trigger.nodeId=SERVICE_<nanoid>）"),
        "constraints": ["cycleType: YEAR|MONTH|WEEK|DAY|HOUR|SIMPLE；type: FIRST|LAST(仅MONTH)|ANY；",
                        "hasPagination/入参出参：SCHEDULE 无入参出参（前端不给），dataSchema 顶层只有 endNode/sourceType/trigger/nodes",
                        "列表字段 scheduleCaption（如「每天 00:05」）"],
        "doc": "docs/audit/udc-semantics/MICROFLOW-BUSINESS-EVENT-TRIGGERS.md",
    },
    "microflow_service_create": {
        "channel": "graphql", "op": "udcMicroflowCreatePost",
        "body": {"appId": "<appId>", "type": "SERVICE", "triggerType": "MANUAL|BUSINESS_EVENT|SCHEDULE",
                 "serviceInterface": "CustomMicroFlowAppService", "microFlowGroupId": "<分组id>",
                 "trigger": {"nodeId": "SERVICE_<nanoid6>|MFStartNode", "caption": ["开始","事件监听","定时任务"],
                             "type": "<triggerType>", "output": "<MANUAL 时 basic 入参>"},
                 "nodes": ["<活动节点，见 microflow_activity_node>"]},
        "verified": ("LIVE PASS：①SERVICE/MANUAL id=862673936068342178（含 SUB_MICROFLOW 活动节点）；"
                     "②SERVICE/BUSINESS_EVENT id=1524985498115296151（messageInfo 实体事件）；"
                     "③SERVICE/SCHEDULE id=-8675485534859429311"),
        "constraints": [
            "★标品 type=SERVICE（对应新建表单「标准微流程」）；自定义 type=CUSTOM",
            "★★trigger.nodeId 决定入参面板能否读到入参（aT 解析：flowNodes[trigger.nodeId]=clone(trigger)）：",
            "  MANUAL 触发（服务定义）必须 trigger.nodeId='MFStartNode'（与真实 getMigrationsource 一致）；",
            "  预置 'SERVICE_xxx'/'CUSTOM_xxx' 会导致入参面板空白（aT 只在 trigger 无 nodeId 时才补 MFStartNode）",
            "  SCHEDULE/BUSINESS_EVENT 触发可用 ${type}_${nanoid6}（真实样本 MigrationScheduler 即 SERVICE_Et34XS）",
            "☆踩坑实证：标品服务定义初建用 SERVICE_<nanoid>，入参面板空 → 改 nodeId='MFStartNode' 后画布显示「订单ID [长整数]」",
            "标品才用活动节点编排（type:'ACTIVITY'）；节点目录 90 个见 module-83128",
            "MANUAL 触发可带入参：trigger={nodeId:'MFStartNode', type:'MANUAL', paramType:'BASIC'|'ENTITY_OBJECT'|'DEFAULT_OBJECT', basic, output}，且 dataSchema.input 同步",
        ],
        "doc": "docs/audit/udc-semantics/MICROFLOW-SERVICE-AND-ACTIVITY-NODES.md",
    },
    "microflow_activity_node": {
        "channel": "graphql", "op": "udcMicroflowUpdatePost",
        "body": "<findById 回读全量 → dataSchema.nodes 追加活动节点 → update>",
        "verified": ("LIVE PASS：往标品服务定义追加 RETRIEVE/RETRIEVE_ARRAY/DATA_MAPPING 三节点，回读一致"),
        "constraints": [
            "活动节点 .type='ACTIVITY'（分支为 'BRANCH'）；公共字段 nodeId,name,type,caption,description,",
            "  runAfter,input,output,isCompleted,actionType",
            "★画布是否显示「设置节点数据」(未完成) 由 nodeDesc(node) 是否为空决定：",
            "  RETRIEVE: needs title+output.dataType+output.type；RETRIEVE_ARRAY: needs ★variableTitle(不是title!)+同上；",
            "  DATA_MAPPING: needs structure.id（结构见 doc）",
            "★填充完整 RETRIEVE 需：fetchType('IDS'|'CONDITION')/app/structure/value(SelectParam)/title/nullHandling/selectType/scope/output",
            "★填充完整 RETRIEVE_ARRAY 需：fetchType/app/structure/variableTitle/pageSearch/size/output(type=ARRAY)",
            "★填充完整 DATA_MAPPING 需：selectParam(源ARRAY变量)/targetType/structure/title/mappingRule/output(type=ARRAY)",
            "  实体 DTO 全名 = com.seeyon.<appName>.dto.<EntityName>Dto；实体清单 GET /service/udc/entity/select-all-by-appid/{appId}",
            "常用 actionType：RETRIEVE 查询单记录 / RETRIEVE_ARRAY 查询多记录 / CREATE_VARIABLE 创建变量 /",
            "  CREATE_ENTITY 插入 / CHANGE_ENTITY 更新 / DELETE_ENTITY 删除 / FOR_EACH 循环 / SUB_MICROFLOW 子微流程 /",
            "  DATA_MAPPING 数据转换 / SEND_MQ_MESSAGE 消息推送 / PUBLISH_BUSINESS_EVENT 事件投递 / CREATE_AFFAIR 待办",
            "★节点目录权威源=前端 module-83128（90 个 export const X={group:'base',name,type,settings}）；",
            "  后端 udcMicroflowFindNodesGet 的 GraphQL 类型名需按实际 schema（内省已关）",
            "☆LIVE 实证：三个标品微流程已挂 RETRIEVE+RETRIEVE_ARRAY+DATA_MAPPING 全链，画布渲染完整不带红字",
        ],
        "doc": "docs/audit/udc-semantics/MICROFLOW-SERVICE-AND-ACTIVITY-NODES.md",
    },
    "microflow_update": {
        "channel": "graphql", "op": "udcMicroflowUpdatePost",
        "gql": ("mutation udcMicroflowUpdatePost($body: udcMicroflowUpdatePostInputBody)"
                "{ udcMicroflowUpdatePost(body: $body) { code data { content } message status } }"),
        "body": "<回读的全量 DTO + 修改字段 + appId>",
        "verified": "content=1（caption 修改）",
    },
}

# 读接口回读模板（LIVE PASS）
READ_TEMPLATES: dict[str, str] = {
    "application_detail": "GET /service/udc/application/detail/{id}",
    "entity_list": "GET /service/udc/entity/select-all-by-appid/{appId}",
    "entity_primary": "GET /service/udc/entity/primary/select-by-appid/{appId}",
    "attribute_all": "GET /service/udc/entity/attribute/select-all-by-entity-id/{entityId}",
    "page_all": "GET /service/udc/page-info/detail-app-id/{appId}",
    "event_list": "POST /service/udc/event/list {appId}",
    "enum_list": "POST /service/udc/udc-enum/list {appId}",
    "refer_group_list": "POST /service/udc/refer-config/group/list {appId}",
    "function_tree": "POST /service/udc/function/find/tree-and-group {appId}",
}

# 已知校验规则（错误消息 = 字段说明书）
VALIDATION_RULES: list[dict] = [
    {"rule": "枚举 name 大写字母开头，含字母数字", "source": "UDC_ENUM_0001"},
    {"rule": "udcEnumType ∈ DEFAULT|CONNECTOR|DYNAMIC_DEPENDENCY", "source": "No enum constant"},
    {"rule": "枚举/项分两步（item.enumId 必填）", "source": "enumId must not be null"},
    {"rule": "item.code 必填 Integer", "source": "code must not be null"},
    {"rule": "页面必须先建菜单（pageItems[].menuId）", "source": "页面必需绑定归属资源"},
    {"rule": "页面 pageUrl 必填", "source": "pageUrl must not be null"},
    {"rule": "实体/字段 name 小写开头（推测自枚举反向约束+1077 枚举全大写开头观察）",
     "evidence": "UNVERIFIED"},
]


def template(name: str) -> dict | None:
    return WRITE_TEMPLATES.get(name)


def build_order() -> list[str]:
    """推荐构建顺序（依赖驱动）。"""
    return ["enum_create", "enum_item_create",
            "entity_create", "attribute_create_text", "attribute_create_ctpenum",
            "index_create",
            "menu_create", "page_create",
            "microflow_create", "microflow_update"]



# 字段类型×控件 LIVE 矩阵（全部 BOOT_0000，datamigration 实验）
ATTR_TYPE_MATRIX: dict[str, str] = {
    "STRING/INPUT": "文本", "DATETIME/DATE": "日期", "INTEGER/INPUTNUMBER": "整数",
    "BOOLEAN/SWITCH": "布尔", "CTPENUM/SELECT": "枚举（relationEntity=enumId）",
    "ENTITY/LIST+multiSelect": "人员多选（relationEntity=OrgMemberMetadata, relationApp=organization）",
}

__all__ = ["SCHEMA_ID", "EVIDENCE", "WRITE_TEMPLATES", "READ_TEMPLATES", "ATTR_TYPE_MATRIX",
           "VALIDATION_RULES", "template", "build_order"]
