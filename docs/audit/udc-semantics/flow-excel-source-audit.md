# 生单、扣减与 Excel 模板：设计态到执行链审计

## 范围与证据身份

本报告属于 xiaozhua-agent 主线的离线平台机制审计，不是客户应用搭建结果。未访问平台、未连接数据库、未上传文件、未发送业务通知。

源码根与 artifact 位置由 `config/udc-semantics-evidence.local.json` 配置。本机配置被 git 忽略；本文仅引用相对于 source_snapshot.root 的源码路径。旧源码 checkout 的运行版本绑定为 UNVERIFIED，不将其自动视为本地 reference jar 或 test2 已部署版本。

机器清单：`flow-excel-contracts.json`。清单记录源文件 SHA-256、逐行引用、范围 SHA-256、断言 token、DTO 字段、Controller 字面路径和表名。全部 `can_execute=false`、`live_verified=false`；未经核对的副作用为 null，不根据 GET/POST 或方法名推断只读。

辅助脚本：`tools/core/audit_udc_flow_excel.py`（**已移入 `_attic_pending/one-off/unsorted/audit_udc_flow_excel.py`**，仓库内已无此路径）。这是离线证据抽取/回放工具，不是 xiaozhua-agent 的平台执行器、页面 validator 或完整业务 planner。

## 1. 必须纠正的两条结论

1. `CALL_DATA_FLOW` 是生单规则调用节点。其生成模板调用 `<SourceEntity>DataFlowRuntimeService`，把 `DataFlowResultDto` 包装为 `CallDataFlowResultDto`。没有直接调用 Deduction 的证据。此前把它描述成“调用生单/扣减的统一节点”过宽。
2. Excel 模板由 Excel starter 的 `ExcelExportTemplate` 持久化到 `ctp_excel_export_template`。不是 `udc_page_schema` 的子字段，也不是只存在于实体 preset JSON。表名已静态确认，目标环境的实际 schema/database 未读取。

进一步发现：`excel/check-excel` 和旧版 `check-excel-data` 会解析上传文件的模板，必要时创建跨环境模板，并可能发布异步检查事件。它们不能因为叫 check 就自动进入只读执行白名单。

## 2. DataFlow：图与映射是独立对象

### 入口、输入与输出

`udc/udc-web/src/main/java/com/seeyon/udc/controller/DataFlowDesignController.java:62-92,151-171`：

| 动作 | Controller 路径 | 绑定 | 结果 |
|---|---|---|---|
| 新建生单图 | POST `/udc/data-flow` | 平铺 DataFlowDto | Long 图 ID |
| 读图 | GET `/udc/data-flow/{id}` | path id | DataFlowDto |
| 新建映射 | POST `/udc/data-flow/mapping` | 平铺 DataFlowMappingSaveDto | DataFlowMappingResultDto |
| 更新映射 | POST `/udc/data-flow/mapping/update` | 平铺 DataFlowMappingSaveDto | DataFlowMappingResultDto |
| 读映射 | GET `/udc/data-flow/mapping/{id}` | path id | DataFlowMappingDto |

这里只是 Controller 字面路径，不拼接/猜测 Gateway 与宿主应用前缀。

`DataFlowMappingSaveDto extends DataFlowDto`，并增加 definition、dataFlowMappingDto。引用：

- `udc/udc-dataflow/src/main/java/com/seeyon/udc/dataflow/dto/DataFlowMappingSaveDto.java:22-30`。
- `udc-common/src/main/java/com/seeyon/udc/common/dto/DataFlowMappingDto.java:27-125`。
- `udc-common/src/main/java/com/seeyon/udc/common/dto/DataFlowMappingDetailDto.java:27-50`。

映射拥有自己的 app/sourceApp、sourceEntity/targetEntity、triggerPoint、bindEvent 和 mappingDetailDto；mappingDetailDto 包含手工前置条件、事件过滤/来源查找条件和 rules。设计态字段与生成时 @JsonIgnore 的 preCondition/eventFilterCondition 分开。

### 保存与校验

直接调用链：

```text
DataFlowDesignController.createMapping
 → DataFlowMappingDesignAppService.create (@Transactional)
 → DataFlowMappingDesignService.create
 → handleGraphDefinition（更新连线规则计数）
 → DataFlowDesignService.update（写图）
 → create(mappingDto, currentAppId)
 → dataCheck / dataProcess
 → ruleInfo = JSON(mappingDetailDto)
 → DataFlowMapping DAO
 → 一致性检测记录与设计态日志
```

证据：

- `udc/udc-dataflow/src/main/java/com/seeyon/udc/dataflow/appservice/DataFlowMappingDesignAppService.java:100-113`。
- `udc/udc-dataflow/src/main/java/com/seeyon/udc/dataflow/domain/service/DataFlowMappingDesignService.java:172-186,222-229,262-280`。
- 同文件 `378-470`：应用依赖、来源/目标实体、编码、触发方式、循环映射、mappingArea、字段映射、连续主子孙实体、CREATE_OR_UPDATE 关键字段、回写校验。

`triggerPoint=MANUALLY` 与 `EVENT_SUBSCRIBE` 为受控值，见 `udc-common/src/main/java/com/seeyon/udc/common/enums/TriggerPointEnum.java:14-22`。操作类型是 CREATE、UPDATE、CREATE_OR_UPDATE，见同目录 `DataFlowOperationTypeEnum.java:12-24`。

持久化表：

- `DataFlow.java:30` → `udc_data_flow`。
- `DataFlowMapping.java:33` → `udc_data_flow_mapping`。

两个类均位于 `udc/udc-dataflow/src/main/java/com/seeyon/udc/dataflow/domain/entity/`。

新建 DataFlow 图还可能预制 DATA_FLOW 菜单/页面（非 dynamic/form 对应条件以源代码分支为准），见 `DataFlowDesignService.java:246-267`。不能把它当成无副作用的单表插入。

### 微流程节点与运行链

`udc/udc-biz/src/main/java/com/seeyon/udc/microflow/domain/bo/flow/activity/CallDataFlowActivity.java:86-123`：

- dataFlowMappingId、structure.entityId 为输入引用。
- dataSourceType=SELECT_PARAM 时必须有 selectParam；否则走 condition。
- output 必填。
- 全局检测检查映射 id 是否存在。

生成模板（旧源码静态）：

`udc/udc-biz/src/main/resources/autocode/JAVA/2.9/templates/microflow/plugin/calldataflow/CallDataFlowActivity.java.ftl:1-17`。

输入 DataFlowExecuteParamDto，调用实体生单服务，输出 CallDataFlowResultDto。后者只复制 targetIds、updateIds：

`udc-starters/udc-starter-runtime/src/main/java/com/seeyon/boot/starter/udcrt/dto/CallDataFlowResultDto.java:19-31`。

运行生单服务的源模板支持：选择 ID、条件查询、微流程 DTO 输入、事件 DTO 数据。引用：

`udc/udc-dataflow/src/main/resources/autocode/JAVA/2.9/templates/dataflow/DataFlowRuntimeService.java.ftl:227-314`。

`DataFlowResultDto` 还有 dataFlowType、errorMsg、relationshipIds、targetDtoInfo 等字段；不能误以为都由 CallDataFlowResultDto 暴露。见 `udc-common/src/main/java/com/seeyon/udc/common/dto/DataFlowResultDto.java:25-43`。

## 3. Deduction：扣减图、规则、算法与状态明细

### 保存对象及接口

`udc/udc-web/src/main/java/com/seeyon/udc/controller/DeductionRuleController.java:49,69-89,107-139`：

```text
POST /udc/deduction/map           DeductionMapDto → Long
GET  /udc/deduction/map/{id}      → DeductionMapDto
POST /udc/deduction/rule          DeductionRuleDto → DeductionResultDto
POST /udc/deduction/validRule     DeductionRuleDto → DeductionResultDto
GET  /udc/deduction/rule/{id}     → DeductionRuleDto
```

图 definition 有 nodes、lines、transform，node id 形如 `id_<entityId>`。图校验禁止实体连到自身，并拒绝 bill 作为目标实体：

`udc/udc-dataflow/src/main/java/com/seeyon/udc/deduction/domain/service/DeductionMapService.java:579-634`。

规则输入包括 source/target 根实体与末级实体、searchConditionDtoList、deductionAlgorithmDtoList、deductionRuleDetailDtoList、extendInfoDto。见 `udc-common/src/main/java/com/seeyon/udc/common/dto/DeductionRuleDto.java:25-106`。

`DeductionRuleService.create`：先 validRule，再保存规则，更新图上的规则数量，生成关联的 algorithm/detail，并可能预制 DEDUCT 菜单/页面；不是普通 CHANGE_ENTITY 的别名。

证据：

- `udc/udc-dataflow/src/main/java/com/seeyon/udc/deduction/domain/service/DeductionRuleService.java:190-217,320-325,1168-1181`。
- AppService 事务边界：同模块 `deduction/appservice/DeductionRuleAppService.java:41-54`。

持久化表来自同模块 `deduction/domain/entity/`：

```text
DeductionMap.java:26          udc_deduction_map
DeductionRule.java:27         udc_deduction_rule
DeductionAlgorithm.java:26    udc_deduction_algorithm
DeductionRuleDetail.java:26   udc_deduction_rule_detail
```

表无数据只能说明查询范围内无配置记录，不能证明功能未启用。

### 代码生成、加载与生命周期执行

`DeductionCodeTask` 只有取得非空规则元数据才生成代码，并按 sourceEntity 输出专用模板。见 `udc/udc-dataflow/src/main/java/com/seeyon/udc/deduction/autocode/task/DeductionCodeTask.java:32-74`。

生成模板在 `udc/udc-dataflow/src/main/resources/autocode/JAVA/2.9/templates/deduction/`：

| 生命周期 | 直接证据 | 行为 |
|---|---|---|
| BeforeCreate | `DeductionRuntimeCreateListener.ftl:18-25,119-133` | SYNC；DO 扣减，写 source deductionInfo |
| BeforeUpdate | `DeductionRuntimeBeforeUpdateListener-update.ftl:13-21,100-134` | SYNC；根据新旧数据与算法求 UNDO/DO，再调用目标更新服务 |
| BeforeDelete | `DeductionRuntimeDeleteListener.ftl:19-22,85-101` | SYNC；根据保存的规则/算法信息 UNDO |

目标更新服务为 `DeductionUpdateTargetEntityService.ftl:123-147,286-315,393-438`：接收 DeductionUpdateParamDto，使用计算后的查询/更新语句与来源/目标映射执行 `dao.update4Deduction`，并生成扣减日志。本文没有验证任何目标应用的事务回滚、并发锁或真实余额结果。

运行初始化读取版本元数据或 classpath 的 init/tenant JSON，FORM 应用直接跳过：

`udc-starters/udc-starter-dataflow/src/main/java/com/seeyon/boot/starter/deduction/listener/DeductionDataInitListener.java:58-89`。

同文件 `92-133,144-154` 还会停用不属于当前发布规则集合的旧 map/rule，并清理有效规则缓存。这是运行加载副作用；Agent 不应通过手工改表模拟。

运行 `DeductionController` 是规则版本管理/查询面，见同 starter `deduction/controller/DeductionController.java:39-90`。它与生成的生命周期监听器执行面不同，不把 saveRuleNewVersion/enableRule 当成执行扣减接口。

## 4. Excel：模板存储、列映射、异步导入导出

### 模板结构与持久化

`boot-extend/boot-starter-excel/src/main/java/com/seeyon/boot/starter/excel/domain/entity/ExcelExportTemplate.java:22-88`：

```text
ctp_excel_export_template
 app_id (String), app_guid (Long), app_name, main_full_name
 signature_code, metadata_content, excel_head_info
 custom_flag, import_flag, default_flag, belong_group_id, auth_info
```

注意 appId 在此 DTO/表为 String，不将其他 UDC Long appId 协议套到它上面。

默认实体模板链：

```text
EntityController.preset/create-default-excel-template
 → EntityPresetAppServiceImpl
 → EntityPresetService.createDefaultExcelTemplate
 → ExcelExportAppService.createExcelDataGridTemplate
 → ExcelExportTemplateService.create
 → ctp_excel_export_template
```

证据：

- `udc/udc-biz/src/main/java/com/seeyon/udc/entity/domain/service/EntityPresetService.java:305-339`。
- `boot-extend/boot-starter-excel/src/main/java/com/seeyon/boot/starter/excel/appservice/ExcelExportAppService.java:246-320`。
- 同 starter `domain/service/ExcelExportTemplateService.java:134-195`。

默认模板会按 appId、mainFullName、isImport/isCustom/isDefault 查找并复用。未指定表头时，从实体聚合元数据提取普通字段；Many2One 参照字段使用唯一标识字段，CTPENUM 单独处理。层级 metadataContent 与拉平的 excelHeadInfo 是两份结构，不能仅给中文表头就认为列映射完整。

### Excel check 有副作用

Component Controller 类级路径是 `excel`（继承 BaseComponentController），宿主/Gateway 前缀未解析，不自行拼成 `/service/udc/excel`。

`ExcelController.java:135-150` → `ExcelImportAppService.java:74-91,123-132`。

- checkExcelDataV2 调用 checkExcelAndGetInfoData，可能创建模板，然后发 ASYNC 校验事件、写 Redis DOING。
- importExcelData 先读取文件的 meta_info，识别 signatureCode、实体和模板，再发 ASYNC 导入事件。
- 主体入口使用 ExcelUploadRequestDto：fileStorageKey、mainFullName、appName、map 等，其他继承字段另行核对。

跨环境模板签名未命中时会 `templateService.create`，直接证据：同 starter `appservice/ExcelImportAppService.java:154-195`；模板 JSON 解析见 `290-318`。

### 从异步句柄到真实数据

```text
ExcelImportAppService.importExcelData → redisKey + DOING
 → ExcelEventListener.onExcelImport (ASYNC)
 → ExcelConvertService.onExcelImportForEvent
 → ExcelImportListener 分批读取/构造主子孙数据
 → ExcelConvertService.saveTreeList
 → ExcelTemplateUtil.invokeSaveBatch(createBatch/updateBatch)
 → EntityAppService；不存在时可回退 EntityDAO
 → 逐行结果 / SUCCESS 或错误文件 / 通知 / 清临时缓存
```

证据根均为 `boot-extend/boot-starter-excel/src/main/java/com/seeyon/boot/starter/excel/`：

- `event/listener/ExcelEventListener.java:138-147`。
- `event/listener/ExcelImportListener.java:84-130`。
- `domain/service/ExcelConvertService.java:1234-1307,3054-3104`。
- `utils/ExcelTemplateUtil.java:943-1013`。

重要异常候选：旧源码 `saveTreeList` 的更新异常 catch (`1304-1306`) 只记录日志，没有像插入分支那样将 successFlag=false。此为 STATIC_SOURCE 异常传播缺口候选，未对当前部署版本验证，不在本轮修复。也因此异步 SUCCESS 仍不能替代业务数据回读。

导出同样异步：`appservice/ExcelExportAppService.java:188-197` 发 ExcelExportEvent、返回 redisKey；`ExcelEventListener.java:77-90` 才开始生成工作。验收必须拿到文件、打开核验列映射与行数据，不能止于返回的 redisKey。

## 5. 版本对照的实际结果

当前 reference `udc-biz` jar 的 SHA-256 是 `8a1cda618cdc23d18d02e39f4f93d6fad4ff732c987fd47bbb28118dbf66ef25`，位置由配置解析。

jar 内 `autocode/JAVA/2.9/templates/microflow/plugin/calldataflow/CallDataFlowActivity.java.ftl` 的 SHA-256 是 `7ad8102e86a2ec3a4e1fdfc99c01c2937c33f662d2ccbf1bf7c0e9ef3989e9b5`，可独立支持生单节点调用契约。

同一个 jar 没有 `templates/deduction/` 与 `templates/dataflow/` 目录条目。此结论仅限该 jar，不能推断平台没有这些模板；旧源码把它们放在独立 udc-dataflow 模块，当前模块 artifact 尚未绑定。

已有 Controller javap 的 DataFlowDesignController/DeductionRuleController 与旧源码路径字面量一致；只支持静态路由旁证，不证明 Excel starter 版本一致，也不证明 live Gateway 可达。

## 6. 主线实现和验收门槛

本轮只交付证据工具、清单和报告，不接入 runtime operation registry，不发写请求。

后续主线实现应独立建模：

1. DataFlowGraph / Mapping / MappingDetail / Trigger / SourceData / Result。
2. DeductionMap / Rule / Algorithm / Detail / RuntimeRuleVersion / DO-UNDOContext。
3. ExcelTemplate / ColumnMetadata / FlatHeader / Signature / AsyncTask / RowResult。
4. can_execute 与证据等级、版本绑定、readback 分开；check 端点副作用必须显式分类。

静态审计通过不等于业务验收。目标应用仍需要：

- 设计态 identity 与关联对象读回。
- codegen/deploy 状态、生成 listener/service、初始化文件与版本。
- 生单目标 ID/数据回读。
- 扣减 create/update/delete 三种生命周期的 DO/UNDO 与目标值回读。
- Excel 模板/签名/列映射、异步终态、错误文件和业务行回读。
- 设计器构建按钮的真实请求。

## 离线复核命令

在仓库根目录执行（Python 路径由环境选择）：

```text
python tools/core/audit_udc_flow_excel.py verify --config config/udc-semantics-evidence.local.json --manifest docs/audit/udc-semantics/flow-excel-contracts.json
```

没有本机源码/参考 jar 时应报告证据不可用，不生成替代数据。该命令默认且始终不发网络请求、不操作平台；PASS 仅表示离线证据与源码/artifact 一致。
