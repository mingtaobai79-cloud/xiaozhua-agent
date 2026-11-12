# AppService 高频动作 cookbook

六个常用动作的完整写法。前三个已用真实 jar **编译通过**（`VERIFIED_COMPILE`），
后三个是 `VERIFIED_STATIC_BYTECODE`（签名逐字，未编译）。

字段后面 `←` 的内容来自平台自己的 `@DtoAttribute`（不是我们编的）。

---

## 1. 发起流程

```java
// com.seeyon.bpm.api.common.BpmAppService  实现 BpmApiAppServiceImpl
// ⚠️ 命名不规则：不是 BpmAppServiceImpl
@Autowired private BpmAppService bpmAppService;

BpmSendDto dto = new BpmSendDto();
dto.setTemplateCode("PROBE_TEMPLATE_001");   // ← 模板code
dto.setCurrentUserId(1L);                    // ← userCode · 关联 OrgMemberDto
dto.setOrgId(1L);                            // ← orgCode · 关联 OrgUnitDto
dto.setFormRecordId("FORM_RECORD_001");      // ← 表单数据id
dto.setSendPolicy("node");                   // ← node=添加节点 / exception=抛异常

SingleResponse<BpmSendResultDto> r = bpmAppService.send(SingleRequest.from(dto));
BpmSendResultDto result = r.getData().getContent();   // { caseId, subject }
```

**字段规则**（`@DtoAttribute.description` 原文）：
> 模板code/模板ID两者传其一，如果都传，以模板code为准

⇒ `templateCode` 和 `templateId` 只传一个。

**流转**（反编译 `bpm-biz-appservice.md`）：
```
BpmUserTemplateService.selectCanSendTemplateByCode  查可用模板
BpmTemplateService.selectEntityById                 查模板实体
UserAppServiceProxy.getBpmMemberPost                跨服务取人员岗位
BpmOperationService.send                            真正发送
MessageRepository.getMessage                        消息
```

**坑**：UDC 发起流程走 `BpmUdcApiService.sendForUdc`，不是这里（这里是通用入口）。

---

## 2. 建实体

```java
// com.seeyon.udc.api.EntityAppService
@Autowired private EntityAppService entityAppService;

EntityDto dto = new EntityDto();
dto.setCapFirstName("ProbeOrder");                              // ← 首字母大写实体名称
dto.setUnCapFirstName("probeOrder");                            // ← 首字母小写实体名称
dto.setFullName("com.seeyon.probe.entity.ProbeOrder");          // ← 实体fullName
dto.setDtoFullName("com.seeyon.probe.dto.ProbeOrderDto");       // ← 实体对应的dto的fullName

List<AttributeDto> attrs = new ArrayList<>();
AttributeDto attr = new AttributeDto();
attr.setName("probeName");
attrs.add(attr);
dto.setAttributes(attrs);                                       // ← 实体属性列表

SingleResponse<Long> r = entityAppService.create(SingleRequest.from(dto));
Long newEntityId = r.getData().getContent();
```

**EntityDto 19 字段**：`capFirstName` / `unCapFirstName` / `fullName` / `dtoFullName` /
`attributes` / `parent` / `children` / `events` / `hasChild` / `hasValidateRule` /
`hasAssignValueRule` / `hasDefaultValueRule` / `generateAggregateValidateClass` …

**坑**：`EntityDto` 在 **udc-common**，不在 udc-facade（编译报错前先查 `interfaces.json` 的 `pkg`）。

---

## 3. 发布应用

```java
// com.seeyon.udc.api.ApplicationManagerAppService
@Autowired private ApplicationManagerAppService appManagerAppService;

DeployNormalDto dto = new DeployNormalDto();
dto.setLockCompatibility(false);   // ← 兼容性锁定
dto.setGenerateLog(true);          // ← 是否生成日志

SingleResponse<DeployParamDto> r = appManagerAppService.deployNormal(SingleRequest.from(dto));
DeployParamDto param = r.getData().getContent();
```

⚠️ **重要纠正**：`DeployNormalDto` **只有 3 个字段**，**没有 appId**：

```
lockCompatibility / generateLog / entityFullNameCondition
```

`appId` / `deployType` / `projectType` / `terminalType` 在**返回的** `DeployParamDto` 里（7 字段）：

```
deployId ← 发布id      appId ← 应用Id
deployType ← 发布类型（test,release）
projectType ← 工程类型  terminalType ← 目标环境
pushEnv / extraParamMap
```

所以「部署要传 appId」这个印象来自 **REST 请求体** `POST /service/udc/runtime/deploy-normal`
（body `{deployDto:{appId,deployType,projectType,terminalType}}`），不是 AppService 入参。
AppService 里 appId 走请求上下文。

**流转**：`→ ApplicationService.deploy`

---

## 4. 文件上传 / 下载

```java
// com.seeyon.boot.starter.file.storage.StorageService
@Autowired private StorageService storageService;

StorageUploadRequestDto req = new StorageUploadRequestDto();
req.setInputStream(inputStream);   // 文件流
req.setFileName("demo.xlsx");      // 文件名
req.setBizType("attachment");      // 业务类型
req.setStorageKey("...");          // 存储键（不传则由平台生成）
req.setRuntime(true);              // 是否运行时

UploadResultDto result = storageService.upload(req);   // default 方法
// result: storageKey / mimeType / fileSize / isPublic / md5 / metadata

InputStream in = storageService.download("storageKey");
boolean exists = storageService.exist("storageKey");
```

**三桶**：`private` / `public` / `ferryboat`（按 `StorageProperties` 配置）。

**坑**：
- `upload` / `download` / `exist` / `delete` 都是 **default 方法**（接口里有默认实现），
  不要自己去实现 `StorageService`。
- 接自建对象存储要**实现 `StorageSpi`**（含三个桶名），不是改 `StorageService`。
- 返回值不是 transport 包装（`UploadResultDto` 裸返回），这是这个接口的风格。

---

## 5. 分页查询

```java
// com.seeyon.udc.api.ApplicationAppService
PageRequest req = new PageRequest();
// PageRequest 承载 pageNo/pageSize/conditions，具体字段见 api-usage/udc.md

PageResponse<ApplicationDto> r = applicationAppService.selectPageByConditions(req);
List<ApplicationDto> rows = r.getData().getContent();     // 注意：PageResponse 也是 getData().getContent()
```

**坑**：
- `PageResponse` 的取值链和 `SingleResponse` 一样：`getData().getContent()`。
- Dao 层返回的是 `PageData<T>`，**不要在这一层套 `PageResponse`**（那是 AppService 的事）。
- 条件构造三套：`ByCondition(s)` → `ByComplexConditions(LinkedHashMap)`（保序）→
  `ByDynamicConditions(SeeyonCondition)`（最灵活）。

---

## 6. 泛化调用（不知道类型 / 动态模块）

```java
AppServiceInvokeDto d = new AppServiceInvokeDto();
d.setInterfaceName("com.seeyon.bpm.api.common.BpmAppService");
d.setMethodName("send");
d.setParamType("com.seeyon.boot.transport.SingleRequest");            // 包装类型
d.setGenericType("com.seeyon.bpm.dto.operation.openapi.BpmSendDto");  // DTO 在这里
d.setParamJson("{\"templateCode\":\"T1\",\"currentUserId\":1}");
d.setReturnJson(Boolean.TRUE);

SingleResponse<Object> r = appServiceProxy.invokeAppService(SingleRequest.from(d));
```

**Bean 查找 6 层**（`CtpCustomerProxyAppServiceImpl.processServiceInvoke`）：
```
① getBean(接口名末段首字母小写)  BpmAppService → bpmAppService
② getBean(接口全名)
③ ModuleAppBeanCache.getBean(接口名)
④ getBean(动态 Bean 名)
⑤ getBean(dto.getBeanName())
⑥ getBeansOfType(loadClass(接口名))  跳过含 mock 的
全找不到 → BusinessException("BOOT_4014")
```

**前提**：目标实现必须带 `@AppService`（= `@Service` + `@Primary`）。
`domain/service/XxxService` 不是 AppService Bean，泛化调不到。

---

## 通用注意事项

| 项 | 规矩 |
|---|---|
| 构造 | `SingleRequest.from(dto)`，不是 `new SingleRequest()` |
| 取值 | `resp.getData().getContent()` 两层，少一层编译不过 |
| Sort | 用 `com.seeyon.boot.transport.Sort`，不是 Spring 的 |
| 多参数 | 多个 `SingleRequest` 平铺 + 裸 `Sort`，不要打包 |
| 写操作返回 | `Integer`（行数）或 `Long`（新 id）；0 = 没命中行，不是异常 |
| 批量 | `createBatch`/`updateBatch`/`deleteByIds`，不要循环单条 |
| 异常 | 抛语义异常，不要 try/catch 拼响应（框架 AOP 统一翻译） |
| 上下文 | `AppServiceContext` 取，不要自建 ThreadLocal |
| 编译验证 | 写完跑 `probe_contracts.py`，别靠肉眼 |

**必填**：平台不用 `javax.validation`（1331 个 DTO 扫 0 命中），
必填只能看 `@DtoAttribute.description` 的措辞（「两者传其一」「必须」）或实测。
