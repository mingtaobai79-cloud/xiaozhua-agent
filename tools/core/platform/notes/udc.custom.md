## 概念对照（udc 的名词）

| 平台术语 | 中文 | 关键 id |
|---|---|---|
| **application**（应用） | 一个低代码应用（含实体、页面、微流程） | `appId` |
| **guid** | 应用的稳定标识（跨版本不变，复制/迁移用） | `guid` |
| **entity**（实体） | 数据模型（对应一张物理表） | `entityId` |
| **attribute**（字段） | 实体字段 | `attributeId` |
| **dataTransferObject**（DTO） | 自定义对象（微流程出入参用，非实体） | `dtoId` |
| **enum / enumCategory / enumItem** | 枚举 / 枚举分类 / 枚举项 | `enumId` |
| **page** | 页面（表单/列表/流程页） | `pageId` |
| **layout** | 布局（页面外壳） | `layoutId` |
| **microflow** | 微流程（节点编排） | `microFlowId` |
| **dataflow** | 生单规则（数据流画布） | `dataFlowId` |
| **deploy** | 部署（设计态 → 运行态） | `deployRecordId` |

## 设计态与运行态是两套数据

```
设计态（MySQL）：udc_entity / udc_attribute / udc_application ...
                  ↑ ApplicationAppService / EntityAppService / AttributeAppService 写这里
                       ↓ deployNormal / deployForm 部署
运行态（Redis 180h → OSS）：metadata 快照
                  ↑ UdcMetaDataAppService 读这里（selectXxxMetaData*）
```

**⇒ 判据：**

- 要**改模型** → 调 `EntityAppService` / `AttributeAppService`（设计态）
- 要**读运行时结构**（页面渲染、微流程校验、流程取字段） → 调 `UdcMetaDataAppService`（运行态）

混用会拿到过期或空数据 —— 部署前的元数据在运行态里根本不存在。

## 建一个应用的完整链路（真实方法名）

```java
@Autowired private ApplicationManagerAppService appMgr;

// ① 建应用，返回 appId
SingleResponse<Long> appId = appMgr.create(SingleRequest.from(applicationDto));

// ② 建设计态应用（带成员/分类），或只用应用壳
appMgr.updateWithMember(SingleRequest.from(appWithMemberDto));

@Autowired private EntityAppService entitySvc;

// ③ 建实体（= 一张表），返回 entityId
SingleResponse<Long> entityId = entitySvc.create(SingleRequest.from(entityDto));

@Autowired private AttributeAppService attrSvc;

// ④ 建字段（可批量）
SingleResponse<Integer> n = attrSvc.createBatch(SingleRequest.from(List.of(attr1, attr2)));
// 系统内置字段用 createBatch4System（跳过用户字段校验）

// ⑤ 查实体下所有字段（建页面/生成代码前必做）
ListResponse<AttributeDto> attrs = attrSvc.selectAllAttributeByEntityId(SingleRequest.from(entityId));
```

## 部署（最容易出错的一步）

```java
@Autowired private ApplicationManagerAppService appMgr;

// 常规部署：入参 DeployNormalDto，返回 DeployParamDto
SingleResponse<DeployParamDto> r = appMgr.deployNormal(SingleRequest.from(deployNormalDto));

// 表单类应用部署
SingleResponse<DeployResultDto> r2 = appMgr.deployForm(SingleRequest.from(deployFormDto));
```

**REST 路径（此前实测可用，**`LIVE`** 级证据来自历史联调，不是本次会话重放）**：

```
POST /service/udc/runtime/deploy-normal
{
  "deployDto": {
    "appId": 8704025620829192834,
    "deployType": "TEST",
    "projectType": "ALL",
    "terminalType": "ALL"
  }
}
```

**两个部署钩子**（框架在部署前后回调，可用来做扩展）：

| 接口 | 方法 | 时机 |
|---|---|---|
| `DeployBeforeService` | `handle(AppContext)` → `boolean` | 部署前；返回 false 可中断 |
| `DeployFinishService` | `callback(DeployCallbackDto)` → `boolean` | 部署后 |

**⚠️ 部署后页面/微流程的改动要重新部署才生效** —— 只改设计态数据不部署，运行态看不到。

## 自定义对象（DTO）—— 微流程出入参就用它

```java
@Autowired private DataTransferObjectAppService dtoSvc;

// 建 DTO 并同时建它的字段，返回 id+字段
SingleResponse<Map<String,Object>> dto = dtoSvc.createDtoWithAttrs(SingleRequest.from(dtoDto));

// 带引用关系（DTO 套 DTO / 引实体）
SingleResponse<Long> withRef = dtoSvc.createDtoWithAttrsAndRefDtos(SingleRequest.from(List.of(dtoDto)));

// 读全量（含字段 + 引用）
ListResponse<DataTransferObjectDto> full = dtoSvc.selectDtoWithAttrsAndRefDtos(SingleRequest.from(dtoId));

// 微流程里可选的 DTO 列表（搭节点时选对象用）
ListResponse<DataTransferObjectDto> selectable = dtoSvc.searchSelectableDtoList(SingleRequest.from(queryDto));
ListResponse<DataTransferObjectDto> byFlow = dtoSvc.selectAllByMicroFlowId(SingleRequest.from(microFlowId));
```

**`*4EntityEvent` 后缀的方法**（`createDtoWithAttrs4EntityEvent`）是**实体事件触发时**的专用入口，
不要用它做常规建数据 —— 它带事件上下文参数。

## 读运行态元数据（生成代码/校验前必做）

```java
@Autowired private UdcMetaDataAppService meta;

// 应用全量元数据（生成页面代码用这个）
SingleResponse<UdcApplicationMetaData4PageCode> all = meta.selectAppMetaData4PageCode(SingleRequest.from(appId));

// 实体元数据（字段、类型、引用）
SingleResponse<UdcEntityMetaDataDto> e = meta.selectEntityMetaData(SingleRequest.from(searchDto));

// 聚合实体（含关联）
ListResponse<UdcEntityMetaDataDto> agg = meta.selectAggEntityIncludeAssociation(SingleRequest.from(searchDto));

// 页面元数据（取页面 schema，流程/微流程要字段时用）
SingleResponse<UdcPageMetadataV2Dto> page = meta.selectPageMetaData(SingleRequest.from(pageSearchDto));
ListResponse<UdcPageMetadataV2Dto> pagesForBpm = meta.selectPageSchema4Bpm(SingleRequest.from(list));

// 枚举元数据
ListResponse<CtpEnumDto> enums = meta.selectEnumMetaDataByAppId(SingleRequest.from(appId));
```

## UDC 与 bpm 的接缝

```java
// udc 侧：取流程默认布局应用名（发起页渲染用）
@Autowired private UdcBpmAppService udcBpm;
SingleResponse<String> layoutAppName = udcBpm.selectDefaultLayoutAppName();

// bpm 侧：从 UDC 发起流程 —— 用 BpmUdcApiService（见 bpm 模块）
//   sendForUdc / triggerFlowForUdc
```

**边界**：`udc` 管「应用/实体/页面/微流程」，`bpm` 管「流程实例」。
UDC 触发流程只调 `BpmUdcApiService`，不要调 `BpmAppService.send`。

## Agent 生成代码时的引用顺序（这是最常错的地方）

```
1. 先 assert 设计态存在        → EntityAppService.selectById / AttributeAppService.selectAllAttributeByEntityId
2. 再读运行态元数据            → UdcMetaDataAppService.selectAppMetaData4PageCode
3. 改完模型必须部署            → ApplicationManagerAppService.deployNormal
4. 部署后重新读运行态元数据     ← 不重读会用旧 schema 生成代码
```

**踩过两次的坑**：第 3 步没做就写第 4 步，拿到的还是旧字段列表；
第 1 步没做直接读运行态，实体刚建还没部署时返回空。

## 应用级操作速查

| 要做 | 方法 |
|---|---|
| 新建应用 | `ApplicationManagerAppService.create` |
| 复制应用 | `copyApp` / `copyAppAsync`（大批量用 async） |
| 移交应用（换负责人） | `handoverApp` |
| 导出应用 | `downloadApp` / `downloadAppAsync` |
| 导入应用 | `importApp` / `importAppWithDto` |
| 查依赖（被谁引用） | `getDependsByAppId` / `getShelfDepend` |
| 上架 | `ApplicationShelfService` |
| 查部署状态 | `selectAppDeployState` |
| 查部署记录 | `selectDeployRecordById` |
| 按 guid 取最新设计版本 | `selectLatestDesignAppByGuid` |