# Entity Construction 黄金样本（当前静态链）

- 范围：UDC 5.3.517 本地已保存反编译证据；离线、只读。
- 当前等级：STATIC_RULE（不是 VERIFIED_RULE/LIVE_RULE）。
- 原因：已闭合接口契约、微流程实体动作解析和运行时消费者的静态关系；尚未取得设计器创建 Entity 的真实 Network payload，也没有保存动作后的 DB/Nacos/metadata 回读。

## 已确认的静态链

```text
Entity construction contract
  ├─ ApplicationManagerAppService.createEntity(SingleRequest<EntityDto>)
  ├─ EntityAppService.create(SingleRequest<EntityDto>) -> SingleResponse<Long>
  ├─ EntityAppService.update/delete/select... (entity lifecycle facade)
  ├─ MicroFlow CreateEntityActivity
  │    ├─ parses node JSON into activity
  │    ├─ resolves Entity service via MicroFlowComponentUtils
  │    ├─ binds Structure / attrs / value / output
  │    ├─ validates UDC Entity OpenAPI
  │    └─ extracts DTO full name for generated code
  └─ EntityRuntimeService
       ├─ buildInitialValue(EntityMeta,...)
       ├─ requiredValidate(EntityMeta,...)
       ├─ setEntityValue(BaseDto, entityClass)
       └─ EntityMetaUtil.forEachMeta(...)
```

## 证据文件

| 角色 | 文件 | SHA-256 |
|---|---|---|
| Entity facade | `docs/audit/modules/decompiled/udc-facade-5.3.517-EntityAppService.java` | `fe11c35f36c122033662b1bcc650a5d11455c4b9c1e6cc8832b1c3e768182822` |
| Application facade | `docs/audit/modules/decompiled/udc-facade-5.3.517-ApplicationManagerAppService.java` | `2abee3dd241c6308ab23268e410815de2993227122f90dd61339ed6916e9dad6` |
| Runtime consumer | `docs/audit/modules/decompiled/udc-starter-runtime-5.3.517-EntityRuntimeService.java` | `4cb0e688038b4e954d05c084cbbea2c371e7592f18298ae0575a64aebecf6025` |
| Front metadata handler | 本地 Temp decompiled source：`_cfr_com_seeyon_udc_autocode_metadata_config_EntityMetaDataPostProcessor` | 需进一步固化 manifest/hash |

## 关键边界

1. `ApplicationManagerAppService.createEntity` 当前反编译结果是 default 方法并返回 `SingleResponse.ok()`；它不能被解释为已证实的实体落库实现。
2. `EntityAppService.create` 只是 facade contract；实现类、Controller 路由和 DB 写入尚未在本证据集闭合。
3. `CreateEntityActivity` 是微流程运行/生成阶段的实体操作节点，不等价于设计器“创建 Entity”保存动作。
4. `EntityRuntimeService` 是运行态实体值初始化、必填校验、序列号/元数据处理消费者，不等价于元数据构造器。
5. `UdcRuntimeDatabaseQueryService` 可以按实体类的 `@Table(name=...)` 查表元数据和数据，但这是运行态查询证据，不证明设计态保存链。

## 缺口与下一步

- P0：通过已授权浏览器/Network 获取设计器创建 Entity 的真实请求 URL、method、payload、response。
- P0：从对应 facade 实现/Controller 或真实请求反查保存实现。
- P0：定位 EntityMetaData/metadata processor 对 EntityDto、AttributeDto 的落库或版本化处理。
- P1：在只读条件下根据真实 application/entity 标识查询 DB/Nacos/运行态 metadata，建立前后回读证据。
- P1：定位 Code Generator 的 Entity/DTO/AppService 输出入口及生成文件。
- P1：把生成物与 Runtime Consumer 的 EntityMeta/EntityBeanContainer 绑定起来。
- 禁止：没有用户明确确认前执行创建应用、创建实体、发布、部署、数据库写入或 Redis 写入。

## 规则记录（暂定）

```yaml
rule_id: udc.entity-construction.v0
object: Entity
verification_level: STATIC_RULE
inputs: [ApplicationId, EntityDto]
facade_contract: EntityAppService.create
lifecycle_contract: EntityAppService.update/delete/select
runtime_consumer: EntityRuntimeService
microflow_consumer: CreateEntityActivity
unverified: [designer_create_payload, controller_mapping, persistence_write, metadata_version, generated_source]
```

## 新增前端静态证据（GET-only）

已从 `https://lowcode-test2.example.com/udc/` 读取并保存真实编译物：

- `docs/audit/frontend/udc-remoteEntry.js`：47,554 bytes；webpack runtime 映射出 `entity-modeling`、`application`、`rule/microflow` 等 chunk。
- `docs/audit/frontend/udc-manifest.json`（**客户场景证据，已迁出至 `seeyon-customer-evidence/frontend/`**，仓库内已无此路径）：`appId=udc`，hash=`10aaca62404d89a89a9d36be5ba93403`。
- 实体字段编辑 chunk：`src_pages_app-design_entity-modeling_entity-fieldset_index_tsx.fdeccdc6.js`，49,615 bytes。

字段编辑器的静态行为已经观察到：

```text
Form onFinish
  → assemble field payload
      { ...formValues, ...dataTypeDefaults,
        entityId, sourceId, sourceType, appId,
        attributeGroup, relation info, widgetConfig,
        calculate: "NORMAL",
        expressionDesignData: "",
        expressionRuntimeData: "" }
  → K.YM.postEntityAttribute(payload, "/update" | "")
  → fetchEntityFieldList({ entityId, sourceType, sourceId })
```

这条证据只把 `Field Construction` 提升到 `STATIC_RULE_CANDIDATE`：已能解释前端如何组装字段保存对象，以及成功后如何重新读取字段列表；`K.YM` 的底层 GraphQL fieldType、Controller 路由、持久化表和回读仍未闭合。

注意：这是字段构造，不是 Entity 本体创建。不能把 `postEntityAttribute` 误写成 `EntityAppService.create`。

证据清单：`docs/audit/frontend/chunk-evidence-manifest.json`（**客户场景证据，已迁出至 `seeyon-customer-evidence/frontend/`**，仓库内已无此路径）。

## Field → API module → GraphQL contract（已闭合到 STATIC_RULE）

由真实前端 bundle 的 webpack module `48659` 提取：

```text
UI: K.YM.postEntityAttribute(payload, suffix)
    ↓
module 48659 export: postEntityAttribute
    ↓
suffix == "/update"
    → udcMutationLoader.load({
         fieldType: "udcEntityAttributeUpdatePost",
         paramsType: "udcEntityAttributeUpdatePostInputBody",
         paramsKey: "body",
         params: payload,
         queryFields: "content"
       })

suffix != "/update"
    → udcMutationLoader.load({
         fieldType: "udcEntityAttributePost",
         paramsType: "udcEntityAttributePostInputBody",
         paramsKey: "body",
         params: payload,
         queryFields: "content"
       })
    ↓
return response.data.content
```

字段列表回读也已从同一模块确认：

```text
fetchEntityFieldListService
  → udcQueryLoader.load
      fieldType: "udcAttributeGroupEntityGet"
      paramsType: "udcAttributeGroupEntityGetInputPath"
      paramsKey: "path"
      params: { entityId, sourceId, sourceType, ... }
      queryFields: content { attributeDtoList { ... } }

fetchEntityFieldDetailService
  → udcQueryLoader.load
      fieldType: "udcEntityAttributeGet"
      paramsType: "udcEntityAttributeGetInputPath"
      paramsKey: "path"
      params: { id }
      queryFields: content { field metadata ... }
```

当前可确认：

- `K.YM` 是字段 API 模块导出对象，调用点位于字段集编辑器 chunk。
- 创建和更新使用两个不同的 GraphQL fieldType。
- 两者均通过 `udcMutationLoader`，参数统一放在 `body`。
- mutation 只请求 `content`。
- 保存成功后，前端重新调用字段列表查询。
- 字段查询返回的元数据范围包含 `entityId`、`appId`、`name`、`caption`、`dataType`、`notNull`、`uniqueness`、`relation*`、`defaultValue*`、`expression*`、`widgetConfig`、`publishState`、`columnName` 等。

因此 `udc.field-construction.v1` 现在可以标记为 `STATIC_RULE`，但不能标记 `VERIFIED_RULE`：GraphQL loader 的真实 HTTP endpoint、服务端 resolver/controller、DTO 实现、持久化和回读仍未验证。

直接证据：

- `docs/audit/frontend/chunks/src_pages_app-design_entity-modeling_entity-fieldset_index_tsx.fdeccdc6.js`
- `docs/audit/frontend/chunks/src_redux_store_ts.14dc061e.js`
- `docs/audit/frontend/entity-field-api-module-evidence.md`（**客户场景证据，已迁出至 `seeyon-customer-evidence/frontend/`**，仓库内已无此路径）
