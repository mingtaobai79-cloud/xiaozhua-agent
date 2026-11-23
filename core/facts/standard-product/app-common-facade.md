# app-common-facade：应用公共能力（二维码/标签/印章/分类/图片/关注/积分/样式）

## Capability

**十来个「每个应用都要用，但谁都不想做」的公共能力**，全在 `com.seeyon.app.common.*`：
二维码、标签、印章、分类、图片（含图片库）、关注、积分台账、样式文件、关联配置、智能体。

## Version

`app-common-facade` 5.3.600（jar 在盘，javap 全量抽取）。

## Input

多数接口按 `appId`/`entityFullName` 作用域；租户由上下文决定。

## ★ 一、二维码（客开常用）

```java
@Autowired(required = false) private QrCodeCommonAppService qrCode;

QrCodeCreateDto req = new QrCodeCreateDto();   // 规则 + 内容
SingleResponse<QrCodeResultDto> r = qrCode.create(SingleRequest.from(req));
SingleResponse<QrCodeDto> q = qrCode.selectByJson(SingleRequest.from(jsonStr));  // 解析
```

```java
SingleResponse<QrCodeResultDto> create(SingleRequest<QrCodeCreateDto>);
SingleResponse<QrCodeDto>       selectByJson(SingleRequest<String>);
```

> 二维码**规则**（类型/链接/字段码）的建链在 `udc/setting/qrcode/create.md`（REST `/service/udc/qrcode-rule/*`），
> 本格只讲「拿规则生成/解析码」这一层。

## ★ 二、标签

```java
LabelAppService
  SingleResponse<Boolean>       updateReferenceCount(SingleRequest<LabelDepartmentDto>);
  SingleResponse<Boolean>       batchUpdateReferenceCount(SingleRequest<LabelUpdateCountDto>);
  ListResponse<LabelDto>        batchSelectLabelDtos(SingleRequest<List<Long>>);
```

## ★ 三、印章

```java
SealCommonAppService
  ListResponse<SealDto>   selectUsableList(ListRequest);                 // 可用印章
  ListResponse<SealDto>   selectListByCondition(ListRequest);
  SingleResponse<Boolean> checkSealPassword(SingleRequest<SealPasswordCheckDto>);  // 用印密码
```

## ★ 四、分类（通用树）

```java
CategoryCommonAppService
  SingleResponse<Long>     create(SingleRequest<CategoryDto>);
  SingleResponse<Integer>  update(SingleRequest<CategoryDto>);
  SingleResponse<Integer>  deleteById(SingleRequest<Long>);
  SingleResponse<CategoryDto> selectById(SingleRequest<Long>);
  ListResponse<CategoryDto>   selectListByConditions(ListRequest);
```

## 五、图片 / 图片库

```java
ImageAppService        // 业务图片
  SingleResponse<Boolean> create(SingleRequest<List<ImageDto>>);      // ★ 批量，一次一张列表
  SingleResponse<Integer> update(SingleRequest<List<ImageDto>>);
  PageResponse<ImageDto>  selectImage(PageRequest);
  SingleResponse<Integer> deleteImage(SingleRequest<List<Long>>);

ImageStoreAppService   // 图片库（素材）
  SingleResponse<Long>  save(SingleRequest<ImageStoreDto>);
  ListResponse<ImageStoreDto> selectImageStore();
  SingleResponse<Integer>     deleteStore(SingleRequest<Long>);
  ListResponse<ImageStoreAndCategoryDto> selectStoreAndCategory();
```

## 六、关注

```java
MyAttentionCommonAppService
  SingleResponse<Long>     create(SingleRequest<MyAttentionDto>);
  SingleResponse<Integer>  deleteByObjectIdOrPageUrl(SingleRequest<Map<String,Object>>);
  SingleResponse<Boolean>  isAttention(SingleRequest<Map<String,Object>>);
  SingleResponse<List<MyAttentionQueryDto>> getAttentionByObjectIds(SingleRequest<List<Long>>);
  ListResponse<Long>       getAttentionUserIdsByObjectIds(SingleRequest<List<Long>>);
```

## 七、积分台账

```java
IntegralLedgerOprateAppService
  SingleResponse<IntegralLedgerDto>       create(SingleRequest<IntegralLedgerDto>);
  SingleResponse<List<IntegralLedgerDto>> createBatch(SingleRequest<List<IntegralLedgerDto>>);
  PageResponse<IntegralLedgerDto>         selectPageByConditions(PageDtoRequest<IntegralLedgerDto>);
  SingleResponse<IntegralRankResultDto>   selectRankById(SingleRequest<Long>);
```

## 八、样式与关联

```java
StyleFileAppService.getCurrentTenantPortalFile();          // 当前租户门户样式（无入参）
AssociateCommonAppService
  ListResponse<AssociateEntityReferDto> selectEntityConfigByConditions(ListRequest);
  ListResponse<AssociateCompleteDto>    selectAssociateCompleteByAppName(SingleRequest<String>);
```

## 九、智能体（若应用挂了 agent）

```java
AgentCommonAppService
  ListResponse<AgentInfoDto> selectByAgentUserId(SingleRequest<Map<String,Object>>);
  SingleResponse<Map<String,Object>> hasAgent(SingleRequest<AgentParamDto>);
  ListResponse<AgentInfoDto> selectByUserIdAndTemplate(SingleRequest<AgentParamDto>);
  SingleResponse<AgentInfoDto> selectById(SingleRequest<Long>);
  SingleResponse<Long>         create(SingleRequest<AgentDto>);
```

## Side Effects

- `ImageAppService.create/update` 是**整批覆盖**语义（传 List），只传要改的那张会丢别的。
- `deleteImage(List<Long>)` 是物理删（按业务表），删前先查引用。
- `checkSealPassword` 失败会返回 false 而不是抛异常，别当成功。

## Known Constraints

1. 这些接口**作用域靠 appId/entityFullName**，跨应用调要显式传，不传就是当前应用。
2. 分页入参是 `PageRequest`（`getParams()/getPageInfo()/getSort()`，**无 getData()**）；
   积分那套用 `PageDtoRequest<Dto>`——两种分页包装都存在，别混。
3. `StyleFileAppService` 只有一个方法，取租户门户样式，不提供写入。
4. 智能体接口依赖应用是否启用 agent 能力，`hasAgent` 先判再调。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 10 个域接口 34 个方法签名 | `javap -p` 5.3.600 | VERIFIED_STATIC_BYTECODE |
| `ImageAppService` 批量语义（List 入参） | 同上 | VERIFIED_STATIC_BYTECODE |
| `IntegralLedgerOprateAppService` 用 `PageDtoRequest` | 同上 | VERIFIED_STATIC_BYTECODE |
| `StyleFileAppService` 仅 1 方法 | 同上 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 全部签名逐字可复核
- ⚠️ 未真机调用（缺应用样本）

## 给 Agent 的判据

```
要生成/解析二维码   → QrCodeCommonAppService.create / selectByJson（规则在 udc/setting/qrcode）
要挂标签           → LabelAppService.batchSelectLabelDtos / updateReferenceCount
要用印             → SealCommonAppService.selectUsableList + checkSealPassword
要分类树           → CategoryCommonAppService（通用 CRUD）
要存业务图片        → ImageAppService（List 批量，整批覆盖语义）
要素材库           → ImageStoreAppService
要关注/取消关注      → MyAttentionCommonAppService（按 objectId 或 pageUrl）
要记积分           → IntegralLedgerOprateAppService.createBatch
要智能体信息        → AgentCommonAppService（先 hasAgent）
```