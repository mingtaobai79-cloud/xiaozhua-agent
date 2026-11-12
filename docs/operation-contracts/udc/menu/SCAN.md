# SCAN — 菜单域（UDC）只读契约候选扫描 5.3.517

日期：2026-09-17；证据等级：VERIFIED_STATIC_BYTECODE（javap -p -v，本地 Maven 离线）；禁止 LIVE / 禁连网关 / 禁连 .207。

## 1. 域定位说明（菜单 = 功能节点 + 页面 + 资源权限的只读视图）

UDC 域内没有独立的 "menu" 类。菜单域契约取 page / resource / role 语义控制器的只读端点：
功能节点树读视图（C1，微流程域占用）、页面元数据读、资源/角色权限读、流水配置实体读、
应用日志/数据日志读、运行时数据库查询。SCAN 把此映射逻辑写清，避免把"菜单"当成类名关键词去搜。

## 2. 负证据（menu 关键词 0 命中，宽→窄）

命令：`jar tf <jar> | grep -icE "menu|menutree|topbar|sitemenu|resourcemen"`
（本机 jar 在 PATH 缺失，用 <LOCAL_ROOT>/java/bin/jar.exe；jar tf 计数为 OBSERVATION 级，逐条升级需 javap）

| jar | 命中计数 |
|---|---|
| udc-common-5.3.517.jar | 0 |
| udc-facade-5.3.517.jar | 0 |
| udc-starter-customplan-5.3.517.jar | 0 |
| udc-starter-dataflow-5.3.517.jar | 0 |
| udc-starter-lowcode-5.3.517.jar | 0 |
| udc-starter-runtime-5.3.517.jar | 0 |

结论：6 件 5.3.517 UDC jar 对 menu/menutree/topbar/sitemenu/resourcemen 全部 0 命中（负证据）。
菜单域不靠 "menu" 关键词定位，靠功能节点/页面/资源/角色/日志/数据库语义类定位（下述 7 控制器）。

## 3. 候选 7 控制器（均在 udc-starter-runtime-5.3.517.jar，jar sha256=74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f）

逐类映射表（原路径 = 类级 @RequestMapping value + 方法级 value，逐字抄 javap.txt，禁拼网关前缀）：

| 类（classfile sha256 前 8） | 方法 | 类前缀 | 方法 value | 全原路径 | verb | 返回 |
|---|---|---|---|---|---|---|
| UdcRoleRtController (ed024802) | search | udc-runtime/udc-role | has-system-admin/{appName} | udc-runtime/udc-role/has-system-admin/{appName} | GET | SingleResponse<Boolean> |
| UdcAppLogController (f6a2111d) | selectAppDataById | udc-runtime/app-log | datalog/{id} | udc-runtime/app-log/datalog/{id} | GET | SingleResponse<UdcEntityMonitorLogDto> |
| UdcAppLogController (f6a2111d) | selectAppDataByDataId | udc-runtime/app-log | datalog/list-by-dataid/{dataId} | udc-runtime/app-log/datalog/list-by-dataid/{dataId} | GET | ListResponse<UdcEntityMonitorLogDto> |
| UdcSerialConfigController (fe1e5a72) | selectEntityList | udc-runtime/serial-config | select-entity-list | udc-runtime/serial-config/select-entity-list | GET | SingleResponse<EntityGroupAndItemDto> |
| UdcRuntimeDatabaseController (588bc1cf) | queryData | udc-runtime/database | query-data | udc-runtime/database/query-data | GET | SingleResponse<UdcRuntimeDatabaseQueryRespDto> |

## 4. GET 只读候选圈定（≥3 条）

已圈定 4 条纯读候选（P1–P4）+ 1 条 HYPOTHESIS（P5）：

- P1 udc-role GET has-system-admin/{appName} — 权限判定读
- P2 app-log GET datalog/{id} — 按 id 读单条日志
- P3 app-log GET datalog/list-by-dataid/{dataId} — 按 dataId 读日志列表
- P4 serial-config GET select-entity-list — 按 appName 读流水配置实体列表
- P5 database GET query-data — 运行时数据库查询；入参无显式绑定注解 → 标 HYPOTHESIS，不入 registry

均排除 delete/clear/unload/set/update 语义；C1 selectFunctionNodeTreeMetaData 已被微流程会话占用，不入菜单域候选。

## 5. 排除项清单（写语义，GET 亦排除）

- UdcAppLogController：deleteAll (GET delete-all)、clearOrgManager (GET clear-org-manager)、
  clearRuntimeDataSource (GET clear-runtime-data-source-cache)、unloadDynamicApp (GET unload-dynamic-app/{appName})、
  setRestEnableLog (GET enable-log/{enable}) — 全为 GET 写/清缓存/卸载语义，排除。
- UdcAttrSnapshotRtController：deleteByDataId (GET delete-by-data-id/{dataId})、
  deleteByMasterDataId (GET delete-by-master-data-id/{masterDataId}) — delete 语义，排除。
- UdcSerialConfigController：update (POST update)、refreshHistoricalData (GET refresh-historical-data/{appName})、
  cacheEvict (GET cache-evict/{appName}) — update/refresh/清缓存写语义，排除。
- 其余 POST（create-batch / search / update / init-tenant-data / update-data-init-version / save-front-log /
  check-page-exists / select-* 等 POST）为写或需 POST 体，不属本轮"GET 只读"圈定目标。

## 6. 逐类映射计数（方法带映射注解数）

| 类 | 带 Mapping 方法数 | GET | POST |
|---|---|---|---|
| UdcRoleRtController | 1 | 1 | 0 |
| UdcAppLogController | 18 | 7 | 11 |
| UdcAttrSnapshotRtController | 2 | 2 | 0 |
| UdcSerialConfigController | 7 | 3 | 4 |
| UdcRuntimeDatabaseController | 1 | 1 | 0 |
| UdcRtPageInfoController | 2 | 0 | 2 |
| FrontFunctionSupportController | 1 | 0 | 1 |

（POST/GET 计数为映射注解统计，语义判定以 §5 排除项为准；POST 中的 search/search-details 为读但需 POST 体，
不属本轮 GET 只读圈定目标，如实记录。）
