# UDC 运行态（udc-starter-runtime）+ 元数据域（boot-starter-metadata）约束

**版本**：udc-starter-runtime 5.3.517 / boot-starter-metadata 5.3.358
**证据**：CFR 反编译 `<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar` 与 `boot-starter-metadata/5.3.358/boot-starter-metadata-5.3.358.jar` 中的 Controller / api / dto / enums。

## 1. 运行态端点目录（19 Controller / 78 端点）

落在 `components/udc/runtime_constraints.py` `RUNTIME_ENDPOINTS`。核心只读面：

| 端点 | 方法 | 说明 | DTO 必填 |
| --- | --- | --- | --- |
| `udc-runtime/data/query` | POST | 表单数据查询 | EntityDataRequestDto: appName / entityFullName / dataId（@NotNull） |
| `udc-runtime/database/query-data` | GET | 数据库直查 | RuntimeDataBaseQueryDataReqDto（无必填） |
| `udc-runtime/datatype/getAll` | GET | 全部数据类型 | - |
| `udc-runtime/graphql-proxy/graphql` | POST | **GraphQL 代理**（6 个未归位 op 的后端通道） | GraphqlProxyRequestDto |
| `udc-runtime/serial-config/list` | POST | 流水号方案不分页查询 | Map |
| `udc-runtime/serial-config/update` | POST | 流水号配置更新 | UdcSerialConfigDto: sourceFullName / entityFullName（@NotNull） |
| `udc-runtime/evn-check/*` | GET | 环境自检 5 项（build-info/app-version/data-permission/response-length/request-content） | - |
| `udc-runtime/app-log/search*` / `datalog/*` | POST/GET | 应用日志查询（microflow/dataflow/deduction/datalog） | Map/Long |
| `udc-runtime/meta-data/*` | GET/POST | 功能节点树 / 页面存在性 / 宿主页面列表 | - |

写端点（`delete*`/`create*`/`update*`/`clear*`/`unload`/`init-tenant`/`enable-log`/`import`/`upgrade`/`copy`）一律标 readonly=False，**LIVE 探针禁调**。例外：`dynamic/jar/import/status/{requestId}` 名字含 import 但功能是查询导入状态，标只读。

路径匹配：`find_endpoint` / `is_readonly_endpoint` 支持 `{var}` 模式与含具体值的真实路径（逐段比较，`{x}` 匹配任意非空段）。

## 2. GraphqlProxy 是 6 个未归位 op 的后端通道

前端 `udcQueryLoader` / `udcMutationLoader`（GraphQL 动态字段，无 REST 路径）→
`udc-runtime/graphql-proxy/graphql`（GraphqlProxyController.doGraphql）→
`boot.starter.udcrt.appservice.GraphqlProxyAppServiceImpl`。
这解释了为什么 `udcMicroflowFindNodesGet` 等在 udc-web 的 54 个 Controller 里找不到：
**它们是 GraphQL schema 动态注册的字段，不是 REST 端点**。证据链：
前端 module-70857（`getMicroFlowNodeDefinition(nodeGroupEnum)` 的 loader 定义，fieldType=udcMicroflowFindNodesGet，queryFields=content{caption description type actionType tag icon order bgColor paramDefinitionSchema}）→ autocode 模板 `GraphQLControllerUtil.java.ftl` → udcrt.appservice。

## 3. 元数据域（boot-starter-metadata）

落在 `components/udc/metadata_constraints.py`。

- **MetadataController**（`@RequestMapping("metadata")`）端点：**105 mapping / 99 op 面**（2026-10-15 字节码直读更正；旧稿「12 端点」是**假阴性**——源于一份不带 `-v` 的残缺 javap 文本；该文本只落 309/865 个 Utf8 常量且注解类型名 0 命中，见 `tests/udc/test_metadata_controller_registry.py`）。子路径举例：`starter-all`/`starter`/`starters`/`starter-multi-version`/`check-service-version`/`service-all`/`service`/`services`/`service-multi-version`/`service-by-hostAppName`/`service-normal`/`service-development`
- **MetadataTypeEnum 14 种**：Service(0) Entity(1) Agg(2) Enum(3) RestApi(4) OpenApi(5) Mq(6) Dto(7) AppService(8) CtpEnum(9) Page(10) Starter(11) AggEntity(12) CtpEnumItem(13)
- **ServiceStatusEnum**：PUBLISHED / UNPUBLISHED
- **ServiceMetadataDto 语义键**：`udcApp`（是否 UDC 应用）、`hostAppName`（宿主应用）、`enableGraphql`（默认 true）、`status`、`appVersion`、`udcDesignVersion`、`dynamicService`、`md5`、`depends`
- 语义谓词：`is_udc_app` / `is_service_published` / `is_graphql_enabled`

## 4. 设计态 vs 运行态 vs 元数据——三面分离

| 面 | 前缀 | 构件 | 用途 |
| --- | --- | --- | --- |
| 设计态 REST | `/udc/*` | udc-web（54 Controller） | 设计器页面操作（实体/页面/微流程/菜单的增删改查） |
| GraphQL 动态字段 | `udcQueryLoader`/`udcMutationLoader` | GraphqlProxy → udcrt.appservice | 设计器部分动态查询（6 个 op） |
| 运行态 | `/udc-runtime/*` | udc-starter-runtime（19 Controller） | 应用运行时（表单查询/流水号/日志/环境自检） |
| 元数据 | `/metadata/*` | boot-starter-metadata | 应用本身是否合法/已发布/是 UDC 应用 |

**写操作纪律**：LIVE 探针只调只读端点；所有写端点（含 `custom-app/*`、`serial-config/update`、`app-log/delete-all` 等）禁止在探针里调用。

## 5. 三个**并行** metadata 面（候选 (v) 收口，2026-10-15）

> 本节回答 §4 表格留下的一处过度简化：`/udc/*` 面下**不止一个** metadata 前缀。
> 证据：仓内 udc-web 契约 + ctp `.class` 直读 + LIVE 调用计数。
> 复算器 `tools/core/decompile/enumerate_metadata_planes.py`；证据件 `METADATA-PLANES.json`。

| # | 外部前缀 | 提供构件 | Controller | 端点 |
| --- | --- | --- | --- | --- |
| 1 | `/udc/meta-data/` | `udc-web-5.3.517` | `MetaDataController` | 32 |
| 2 | `/udc/design-metadata/` | `udc-web-5.3.517` | `UdcDesignMetadataController` | 47 |
| 3 | `/udc/metadata/` | `metadata-5.3.358` | ctp `MetadataController` | 105（99 op 面） |

**口径更正（重要）**：`674 端点`是 **udc-web 单构件视图**，不是平台操作面全量。
按**全构件并集**理解时至少要加上 ctp 面 105 条 ⇒ 本窗口已知 **779**；
779 **也不是运行期全量**（其它非 udc-web 提供者未纳入，`pods/exec` 仍被 RBAC 挡）。
两个数字口径**不可混用**。

**重叠与陷阱**：面 2 ∩ 面 3 = **43 个同名字面量**；
`/udc/meta-data/refer-and-app`（面 1）与 `/udc/metadata/refer-and-app`（面 3）
**只差一个连字符**，且 `refer-and-app` 是**三面共有**的唯一个字面量。
因此「按语义猜路径」在 `design-metadata` 上几乎总能拼出一个**语法成立**的路径。

**哪个面是活的（两条独立轴）**：

1. 设计器耐久 chunk（`udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js`）：
   `udcMetaData*` **68** 次 / `udcDesignMetadata*` **0** 次。
2. LIVE 调用计数：`/udc/metadata/` **20** 次 / `/udc/design-metadata/` **0** 次。

⇒ **面 2（design-metadata）在本窗口是死面**：契约登记在案、leaf 词表与活面大面积同名，
但前端不发、运行期不调。op 名同样三分（`path_to_op` 由全路径派生）：
`udcMetaDataReferAndAppPost` / `udcDesignMetadataAppServiceByNamePost` /
`udcMetadataAppServiceByNamePost`。

**限制**：设计器 chunk 为 5.3.496 而部署 `udc` 为 5.3.517（版本差未消除）；
LIVE 计数是**单窗口**事实，只证该窗口分布，不证面 2 永不使用；
面 3 的静态证据是 5.3.358 样本 + LIVE 同线程日志。
