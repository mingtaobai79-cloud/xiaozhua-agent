# UDC → BPM 单据发起链路（实证）

> 来源：`udc-starter-lowcode-5.3.491.jar` CFR 反编译 + `bpm-facade-5.3.374.jar` 源码
> 等级：`VERIFIED_STATIC_SOURCE`（方法体逐行读取，非签名推断）
> ⚠️ **VERSION_CAVEAT**：本机 5.3.491、5.3.374，用户环境 5.3.517。

---

## 1. 一句话结论

```
业务代码
  └─ BaseEntityCurdService.create4Bpm(dto)          [udc-starter-lowcode]
       ├─ Ids.gidLong() 预生成主键
       ├─ 落库 create(dto)
       ├─ approvalCallBack.afterApprovalCreate(context)
       │    └─【实现类】ApproveFeatureService        [udc-starter-runtime]
       │         ├─ getBpmPrefixParams              ← 查模板参数
       │         │    └─ bpmUdcApiService.prefixForUdc
       │         ├─ startProcess0  ← 状态机判定
       │         │    ├─ sendProcess → bpmUdcApiService.sendForUdc   ← 发起流程
       │         │    └─ saveDraft   → bpmUdcApiService.saveDraft    ← 存草稿
       │         └─ updateBpmProcessAttribute → 回写 caseId/templateId
       └─ context.getParamter("bpm") 取结果
```

**★★ 三层桥接全部定位到具体类和方法：**

| 层 | 接口/类 | 位置 |
|---|---|---|
| L1 扩展点 | `ApprovalCallBack`（6 空 default） | `udc-starter-lowcode` |
| L2 实现类 | **`ApproveFeatureService`** | **`udc-starter-runtime`** |
| L3 RPC | `BpmUdcApiService`（`@DubboReference`） | `bpm-facade` |

**⇒ 实现类不在接口所在 jar，在 runtime 包 —— 这是本次排查最大的坑（详见 §7）。**

---

## 2. `ApprovalCallBack` 接口全貌

**包：** `com.seeyon.boot.starter.lowcode.callback.ApprovalCallBack`

```java
public interface ApprovalCallBack {
    default public void beforeApprovalCreate(ApprovalContext context) {}
    default public void afterApprovalCreate(ApprovalContext context) {}
    default public void beforeApprovalUpdate(ApprovalContext context) {}
    default public void afterApprovalUpdate(ApprovalContext context) {}
    default public void beforeApprovalCreateValidate(ApprovalContext context) {}
    default public void beforeApprovalUpdateValidate(ApprovalContext context) {}
}
```

**★★ 6 个扩展点，按「时机 × 动作」二维排列：**

| 时机 | 创建 | 更新 |
|---|---|---|
| 校验前 | `beforeApprovalCreateValidate` | `beforeApprovalUpdateValidate` |
| 落库前 | `beforeApprovalCreate` | `beforeApprovalUpdate` |
| 落库后 | `afterApprovalCreate` | `afterApprovalUpdate` |

**`ApprovalCallBackExt` 是第二个接口，方法签名完全相同。**
**⇒ 平台保留了两套扩展位（`CallBack` / `CallBackExt`），可能是版本演进，需读实现类才知道谁在用。**

---

## 3. `ApprovalContext` —— 扩展点的数据载体

**从 `BaseEntityCurdService` 的用法反推可用 API：**

| 方法 | 作用 |
|---|---|
| `putProcessData(dto)` | 放入当前业务 DTO |
| `putTargetStatusType(String)` | 放入目标单据状态 |
| `getParamter("bpm")` | **取出流程结果**（拼写是 `Paramter`，平台笔误） |
| `getParamter("bpmProcessType")` | 取流程类型（用于判断是否主流程） |
| `hasException()` | **是否有异常** |
| `getErrorMsg()` | 异常消息 |

**⇒ `context.getParamter("bpm")` 就是流程发起结果 —— 它会被回写进 `ResultDto.resultMap`。**

---

## 4. 完整链路（逐行实证）

### 4.1 入口：`create4Bpm`

```java
public ResultDto create4Bpm(@Nonnull D frontDto) {
    if (null == frontDto.getId()) {
        frontDto.setId(Ids.gidLong());        // ① 预生成主键
    }
    BaseEntityCurdService<D> baseEntityCurdService = this.getBaseEntityCurdService();
    ApprovalContext<D> context = new ApprovalContext<D>();
    context.putProcessData(frontDto);
    baseEntityCurdService.create4BpmInternal(frontDto, context);   // ② 转内部方法
    ResultDto resultDto = new ResultDto();
    HashMap<String, Object> map = new HashMap<String, Object>(2);
    map.put("bpm", context.getParamter("bpm"));    // ③ 取出流程结果
    resultDto.setResultMap(map);
    resultDto.setId(frontDto.getId());
    return resultDto;
}
```

**★ 关键：主键**在调 BPM 之前**就已经生成了（`Ids.gidLong()`）。**
**⇒ 业务数据先有 ID，流程才引用这个 ID，不是流程先建再回填。**

### 4.2 核心：`create4BpmInternal`

```java
public D create4BpmInternal(D frontDto, ApprovalContext context) {
    BaseEntityCurdService<D> baseEntityCurdService = this.getBaseEntityCurdService();

    // ① 目标状态必须非空
    Enum targetStatusType = (Enum) ReflectFieldUtil.getFieldValue(frontDto, "statusType");
    if (Objects.isNull(targetStatusType)) {
        throw BusinessException.message("目标状态错误：目标状态为空");
    }

    // ② 老表单兼容：PENDING_REVIEW → TO_BE_SUBMITTED
    if ("PENDING_REVIEW".equals(targetStatusType.name())) {
        log.warn("老表单逻辑：发起走udc，单据状态设置为：TO_BE_SUBMITTED");
        Map enumMap = EnumUtils.getEnumMap(targetStatusType.getClass());
        ReflectUtil.setFieldValue(frontDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));
    }

    context.putTargetStatusType(targetStatusType.name());

    // ③ 落库前扩展点
    this.approvalCallBack.beforeApprovalCreate(context);

    // ④ 主表+子表落库
    baseEntityCurdService.create(frontDto);

    // ⑤ 备份落库后的 DTO（用于后续 diff）
    BaseEntityActionDto oldDto = BeanCopier.copy(frontDto, this.dtoClass);

    try {
        // ⑥ 落库后扩展点 —— 真正发流程在这里
        this.approvalCallBack.afterApprovalCreate(context);

        // ⑦ 扩展点报告了异常 → 降级为待提交
        if (context.hasException()) {
            log.info("数据id{},bpm流程有异常：{},状态置为待提交",
                     frontDto.getId(), context.getErrorMsg());
            Map enumMap = EnumUtils.getEnumMap(targetStatusType.getClass());
            ReflectUtil.setFieldValue(frontDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));
        }
    } catch (Exception e) {
        // ⑧ 抛异常 → 降级为待提交 + 立即写库 + 重新抛出
        log.warn("startProcess fail:{}", frontDto.getId(), e);
        Map enumMap = EnumUtils.getEnumMap(targetStatusType.getClass());
        ReflectUtil.setFieldValue(frontDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));
        this.updateStatusType(frontDto);
        ExceptionUtils.rethrow(e);
    }

    // ⑨ 主流程才回写根实体
    if (this.isMainProcess(context)) {
        this.updateRootEntity(oldDto, frontDto);
    }
    return frontDto;
}
```

### 4.3 三条降级路径（★ 最容易踩坑）

| 场景 | 业务数据 | 单据状态 | 异常 |
|---|---|---|---|
| **正常** | 已落库 | 目标状态 | 无 |
| **`context.hasException()`** | 已落库 | **`TO_BE_SUBMITTED`** | **不抛，静默继续** |
| **抛 Exception** | 已落库 | **`TO_BE_SUBMITTED`** + 立即 `updateStatusType` | **rethrow** |

**★★ 最危险的一条：`hasException()` 分支不抛异常。**
**⇒ 调用方拿到的是「成功」的 ResultDto，但流程其实没发起，单据停在「待提交」。**
**⇒ 必须检查 `resultDto.getResultMap().get("bpm")` 才知道真实结果。**

### 4.4 `isMainProcess` —— 主/子流程判定

```java
private boolean isMainProcess(ApprovalContext context) {
    Object processType = context.getParamter("bpmProcessType");
    return processType == null || Boolean.parseBoolean(processType.toString());
}
```

**⇒ `bpmProcessType` 为 null 或 `"true"` ⇒ 主流程 → 回写根实体。**
**⇒ 为 `"false"` ⇒ 子流程 → **不**回写根实体（主子表场景下子表行不发流程）。**

---

## 5. `update4Bpm` —— 更新时走不走流程

**这个方法的判定逻辑比 create 复杂，是关键陷阱区。**

```java
public ResultDto update4Bpm(@Nonnull D frontDto) {
    Enum targetStatusType = ReflectFieldUtil.getFieldValue(frontDto, "statusType");
    if (Objects.isNull(targetStatusType)) {
        throw BusinessException.message("目标状态错误：目标状态为空");
    }

    // ★ 开关：checkStatusType（从 extendMap 取，默认 false）
    boolean checkStatusType = MapUtils.getBoolean(frontDto.getExtendMap(),
                                                  "checkStatusType", false);
    Long id = frontDto.getId();
    Asserts.notNull(id, "id");
    boolean callBpm = true;

    if (checkStatusType && Objects.nonNull(oldStatus = this.selectBillStatusById(id))) {
        if (!("NONE".equals(oldStatus.name())
           || "DRAFT".equals(oldStatus.name())
           || "TO_BE_SUBMITTED".equals(oldStatus.name()))) {
            // ★ 库里状态不是这三种 → 清空 statusType + 不走 BPM
            ReflectUtil.setFieldValue(frontDto, "statusType", null);
            callBpm = false;
            log.warn("表单状态：数据库状态为-{},目标状态为-,不进行任何bpm操作!",
                     oldStatus, targetStatusType);
        } else {
            log.warn("表单状态：数据库状态为-{},目标状态为-,执行bpm逻辑。",
                     oldStatus, targetStatusType);
        }
    }
    ...
}
```

### ★★ 更新走流程的判定表

| `checkStatusType` | 库里状态 | 结果 |
|---|---|---|
| `false`（默认） | 任意 | **总是走 BPM** |
| `true` | `NONE` / `DRAFT` / `TO_BE_SUBMITTED` | 走 BPM |
| `true` | 其他（审批中/已结束等） | **不走 BPM，且 `statusType` 被置 null** |

**⇒ 陷阱：`statusType` 被置为 `null` 后，如果后续代码还读它，会拿到 null。**
**⇒ `checkStatusType` 默认 `false`，即默认「随便改都尝试发流程」—— 这在审批中的单据上会出问题。**

### 更新链路

```java
if (callBpm) {
    if ("PENDING_REVIEW".equals(targetStatusType.name())) {
        // 老表单兼容（同 create）
        ReflectUtil.setFieldValue(frontDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));
    }
    this.approvalCallBack.beforeApprovalUpdate(context);      // 落库前
}

D dbDto = this.getBaseEntityCurdService().updateWithResult(frontDto);   // 落库

BaseEntityActionDto frontCopyDto = BeanCopier.copy(frontDto, this.dtoClass);

if (callBpm) {
    try {
        context.putProcessData(frontCopyDto);                  // ★ 用拷贝
        this.approvalCallBack.afterApprovalUpdate(context);    // 落库后发流程
    } catch (Exception e) {
        log.warn("startProcess fail:{}", frontCopyDto.getId(), e);
        // ★ 只改状态，不写库，不 rethrow
        ReflectUtil.setFieldValue(frontCopyDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));
    }
    if (this.isMainProcess(context)) {
        this.updateRootEntity(dbDto, frontCopyDto);
    }
}
```

**★★ update 与 create 的异常处理**不一致**：**

| 行为 | `create4BpmInternal` | `update4Bpm` |
|---|---|---|
| 抛异常时写库 | ✅ `updateStatusType` | ❌ **不写** |
| 抛异常时 rethrow | ✅ `ExceptionUtils.rethrow` | ❌ **吞掉** |

**⇒ update 失败是**完全静默**的：状态只改在内存对象上，库里还是旧值，调用方也不知道失败。**

---

## 6. 单据状态机（实证）

**出现过的状态名（从 if 判断里提取）：**
```
NONE              无状态（新建）
DRAFT             草稿
TO_BE_SUBMITTED   待提交（降级态 / 老表单转换目标）
PENDING_REVIEW    待审（★ 老表单专用，会被强制转成 TO_BE_SUBMITTED）
（其他）          审批中 / 已结束等
```

**关键规则：**
```
PENDING_REVIEW  →  强制转 TO_BE_SUBMITTED（不论 create 还是 update）
                   log.warn("老表单逻辑：发起走udc，单据状态设置为：TO_BE_SUBMITTED")
```

**⇒ `PENDING_REVIEW` 是**死状态**，任何传入都会被改写成 `TO_BE_SUBMITTED`。**

---

## 7. ★★★ 实现类已找到：`ApproveFeatureService`

**追查过程（这是本轮最关键的突破）：**

```
① 全盘 grep "implements ApprovalCallBack"
   udc-lowcode-src/  → 0
   udc/              → 0
   std-src/          → 0
   ⇒ 不在 lowcode 包

② 换策略：二进制搜 class 里引用 ApprovalCallBack 的类
   grep -rl "ApprovalCallBack" udc/
   → udc-starter-runtime/.../ApproveFeatureService.class   ★ 命中

③ 反编译 udc-starter-runtime-5.3.605.jar
   → grep "implements.*ApprovalCallBack"
   → ./ApproveFeatureService.java                          ★ 确认
```

**★ 教训：接口实现类不在接口所在 jar 里，要搜**引用方**而不是搜**实现方**（子串搜 class 文件）。**

### 7.1 实现类定位

```
类：    com.seeyon.boot.starter.udcrt.domain.service.ApproveFeatureService
模块：  udc-starter-runtime-5.3.605.jar     ← 注意：runtime 包，不是 lowcode
注解：  @Service + implements ApprovalCallBack
源码：  udc-runtime-src/com/seeyon/boot/starter/udcrt/domain/service/ApproveFeatureService.java
```

### 7.2 依赖

```java
@Autowired      private UdcSerialConfigService serialConfigService;
@DubboReference private BpmUdcApiService       bpmUdcApiService;   // ★ Dubbo 远程调用
@Autowired      private BpmRetryService        bpmRetryService;    // ★ 重试队列
```

**⇒ `BpmUdcApiService` 是 `@DubboReference` —— BPM 是独立 Dubbo 服务，不是本地 Bean。**

### 7.3 6 个扩展点的真实实现

| 扩展点 | 实现 | 关键动作 |
|---|---|---|
| `beforeApprovalCreate` | ✅ | `getBpmPrefixParams` → `context["bpmPrefix"]` |
| **`afterApprovalCreate`** | ✅ **核心** | `startProcess0` → `context["bpm"]` / `context["bpmProcessType"]` / `addErrorMsg` |
| `beforeApprovalUpdate` | ✅ | 同 create 的 before |
| **`afterApprovalUpdate`** | ✅ **核心** | 同 create，多传 `oldStatus` |
| `beforeApprovalCreateValidate` | ❌ **空方法** | 什么都不做 |
| `beforeApprovalUpdateValidate` | ❌ **空方法** | 什么都不做 |

### 7.4 `afterApprovalCreate` 全文

```java
public void afterApprovalCreate(ApprovalContext context) {
    String targetStatusType = context.getTargetStatusType();
    BpmProcessLaunchResultDto r = this.startProcess0(
        context.getProcessData(),
        targetStatusType,
        null,                                   // create 时 oldStatus = null
        (BpmPrefixForUdcResponseDto) context.getParamter("bpmPrefix")
    );
    context.addParamter("bpm", r);
    Optional.ofNullable(r).ifPresent(dto -> context.addErrorMsg(dto.getErrorMsg()));   // ★
    context.addParamter("bpmProcessType", this.isMainProcess(r));
}
```

**★★ `addErrorMsg(dto.getErrorMsg())` 是「静默失败」的源头：**
```
BPM 返回的 errorMsg 被塞进 context
  → BaseEntityCurdService 检测 context.hasException()
  → true ⇒ 状态置 TO_BE_SUBMITTED，但不抛异常
```

### 7.5 `afterApprovalUpdate` 的差异

```java
String oldStatus = ((Enum) context.getProcessData()
                    .getExtendMap().get("oldStatusType")).name();   // ★ 从 extendMap 取
```

**⇒ update 的 `oldStatus` 是**外部塞进 `extendMap` 的**，不是查库得到的。**
**⇒ 调用方没塞 `oldStatusType` 会 `NullPointerException`。**

---

## 7B. ★★★ 状态机（`startProcess0` 完整 switch，实证）

**这是最核心的业务规则表：**

```java
switch (oldStatus) {
    case "PENDING_REVIEW":
        case targetStatus "PENDING_REVIEW"  → sendProcess()      // 发起
        break;
    case "DRAFT":
        case targetStatus "PENDING_REVIEW"                  → sendProcess()
        case targetStatus "DRAFT"/"TO_BE_SUBMITTED"         → saveDraft()
        break;
    case "TO_BE_SUBMITTED":
    case "NONE":
    case "":
        case targetStatus "PENDING_REVIEW"  → sendProcess()
        case targetStatus "DRAFT"           → saveDraft()
        break;
}
```

### 状态转移矩阵

| oldStatus \ target | `PENDING_REVIEW` | `DRAFT` | `TO_BE_SUBMITTED` | 其他 |
|---|---|---|---|---|
| **`PENDING_REVIEW`** | **sendProcess** | — | — | — |
| **`DRAFT`** | **sendProcess** | **saveDraft** | **saveDraft** | — |
| **`TO_BE_SUBMITTED`** | **sendProcess** | **saveDraft** | — | — |
| **`NONE`** | **sendProcess** | **saveDraft** | — | — |
| **`""`（null）** | **sendProcess** | **saveDraft** | — | — |

**空格 = 不做任何 BPM 操作（`bpmProcessLaunchResultDto` 保持 null）。**

### ★★ 三条硬规则

**① 只有 `PENDING_REVIEW` 才真正发起流程**

**⚠️ 但 `create4BpmInternal` 会把 DTO 的 `PENDING_REVIEW` 改写成 `TO_BE_SUBMITTED` —— 为什么还能发起？**

因为改写发生在 `putTargetStatusType` **之前**，且 `targetStatusType` 是**局部变量**：
```java
if ("PENDING_REVIEW".equals(targetStatusType.name())) {
    ReflectUtil.setFieldValue(frontDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));  // ① 改 DTO 字段
}
context.putTargetStatusType(targetStatusType.name());   // ② 局部变量没变，仍是 PENDING_REVIEW
```
**⇒ `ReflectUtil` 只改字段，不改局部变量。所以 context 里仍是 `PENDING_REVIEW` → 能发起。**

**② `DRAFT → TO_BE_SUBMITTED` 走 saveDraft（不是发起）**
**⇒ 降级单据重试时不会重新发起，这是潜在坑。**

**③ `TO_BE_SUBMITTED → TO_BE_SUBMITTED` 什么都不做**
**⇒ 降级态再保存不会重试，必须显式改成 `PENDING_REVIEW`。**

---

## 7C. ★★★ 模板查找：`getBpmPrefixParams` → `prefixForUdc`

```java
public BpmPrefixForUdcResponseDto getBpmPrefixParams(Object data) {
    String entityFullName = this.getEntityFullName(data);     // ① 根实体全名
    BpmPrefixForUdcDto param = new BpmPrefixForUdcDto();
    param.setRootEntityName(entityFullName);

    param.setTemplateId(UdcReflectUtil.getFieldValue(data, "templateId"));   // ② 单据的 templateId

    if (data instanceof BaseRootDto && MapUtils.isNotEmpty(extraParamMap)) {
        param.setPageGuid(extraParamMap.get("pageGuid"));
        param.setTemplateGuid(extraParamMap.get("templateGuid"));
        param.setPageUrl(extraParamMap.get("pageUrl"));
        param.setPageParameter(extraParamMap.get("pageParameter"));
        param.setCaseId(UdcReflectUtil.getFieldValue(data, "caseId"));

        // ③ pageType 合法性校验（非法值静默丢弃）
        String pageType = extraParamMap.get("pageType");
        boolean illegal = true;
        for (PageTypeEnum e : PageTypeEnum.values()) {
            if (e.name().equals(pageType)) illegal = false;
        }
        if (illegal) pageType = null;
        param.setPageType(pageType == null ? null : PageTypeEnum.valueOf(pageType));
    }

    SingleResponse resp = bpmUdcApiService.prefixForUdc(SingleRequest.from(param));   // ④ RPC
    if (!resp.success()) { ... throw new BusinessException("BPM_PROCESS_0004", ...); }
    if (resp.getData() == null || resp.getData().getContent() == null) {
        log.warn("未获取到流程参数配置...");
        return null;                                          // ⑤ 返回 null
    }
    return (BpmPrefixForUdcResponseDto) resp.getData().getContent();
}
```

### ★★ 「单据怎么找到自己的流程模板」

**不是靠 `templateCode`，靠这些入参组合：**

| 参数 | 来源 | 作用 |
|---|---|---|
| **`rootEntityName`** | `getEntityFullName(data)` | **主键** |
| `templateId` | 单据 DTO 的 `templateId` | 多模板选择 |
| `templateGuid` | `extraParamMap["templateGuid"]` | 版本 |
| `pageGuid` / `pageUrl` / `pageParameter` | `extraParamMap` | 页面上下文 |
| `caseId` | 单据 DTO 的 `caseId` | 已有实例 |
| `pageType` | `extraParamMap["pageType"]` | 必须匹配 `PageTypeEnum`，否则静默置 null |

### ★★ 最常见的「发起没反应」原因

```java
// startProcess0 开头
if (bpmPrefixForUdcResponseDto == null) {
    log.warn("未配置流程模板或根据参数未查询到流程模板，无法发送流程...");
    return null;    // ★ 静默返回 null
}
```

**完整静默链：**
```
没配流程模板
  → prefixForUdc 返回 null
  → startProcess0 直接 return null
  → context["bpm"] = null，getErrorMsg() = null
  → hasException() = false
  → 调用方看到"成功"，但流程根本没发起
```

**⇒ 诊断关键字：`未配置流程模板或根据参数未查询到流程模板，无法发送流程`**

---

## 7D. ★★★ `sendProcess` —— 真正调 BPM

### DTO 装配

```java
Long dataId = Long.parseLong(dataMap.get("id").toString());
BpmSendUdcDto dto = new BpmSendUdcDto();

// templateId 优先级：单据 > 模板参数
Long templateId = Nullable.ofNullable(dataMap.get("templateId")).ofLong().orElse(0L);
templateId = (templateId == 0L) ? bpmResult.getTemplateId() : templateId;
dto.setTemplateId(templateId);

dto.setCaseId(caseId);
dto.setRootEntityName(this.getEntityFullName(data));
dto.setUserId(RequestContext.get().getUserId());          // ★ 从上下文取
dto.setFormRecordId(dataId);                              // ★ Long
dto.setCommentDto(this.getBpmComment(dataMap));
dto.setCommentRequired(this.getCommentRequired(dataMap));
dto.setChangeNodeRequestDtos(this.getChangeNodeRequest(dataMap));
dto.setPreMatchRequestDto(this.getPreMatchRequestDto(dataMap));
dto.setApplicationName(Apps.getAppName());                // ★ 从上下文取
dto.setCommandId(String.valueOf(dataId));
dto.setAffairId(this.getAffairId(data));

// ★ formData 按模板声明裁剪，不是全量
List paramPathNames = bpmResult.getParamPathNames();
Map<String,Object> processParamMap = BpmDataUtil.filterMapData(dataMap, paramPathNames);
dto.setFormData(processParamMap);
```

**★★ 三个关键点：**

**① `formData` 是**按模板声明裁剪**的**
`prefixForUdc` 返回 `paramPathNames`，只传这些字段。**⇒ 模板没声明的字段不会传给 BPM。**

**② `userId` / `applicationName` 从**上下文**取**
```java
dto.setUserId(RequestContext.get().getUserId());
dto.setApplicationName(Apps.getAppName());
```
**⇒ 必须在**有请求上下文的线程**里执行，不能放异步线程池或定时任务裸调。**

**③ `templateId` 优先级：DTO 非 0 → 用 DTO；DTO 为 0 → 用模板参数**

### 三级异常处理（★ 重试队列）

```java
try {
    response = bpmUdcApiService.sendForUdc(SingleRequest.from(dto));
    UdcReflectUtil.setEnumFiled(data, "sendState", "SEND_SUCCESS");      // ① 成功
    if (this.errorResponse(response)) { ... throw new BusinessException("BPM_PROCESS_0004"); }
} catch (BusinessException e) {
    throw e;                                                             // ② 业务异常直抛
} catch (Exception e) {
    UdcReflectUtil.setEnumFiled(data, "sendState", "SENDING");           // ③ RPC 失败
    bpmRetryService.enqueue(data, dataMap.get("extraParamMap"));          //    ★ 进重试队列
    throw e;
}
```

| 异常类型 | `sendState` | 重试队列 | 抛出 |
|---|---|---|---|
| 正常 | **`SEND_SUCCESS`** | ❌ | ❌ |
| `BusinessException` | — | ❌ | ✅ |
| 其他 `Exception`（RPC） | **`SENDING`** | ✅ **enqueue** | ✅ |

**⇒ `sendState` 三态：`SEND_SUCCESS` / `SENDING` / 初始。**

### 返回值处理（★ 第四个降级点）

```java
BpmApiSendApiResponseDto content = response.getData().getContent();

if (content.getPreMatchResponseDto() != null && content.getPreMatchResponseDto().isPop()) {
    UdcReflectUtil.setEnumFiled(data, "statusType", "TO_BE_SUBMITTED");
    log.info("需要选人，更新单据状态为：TO_BE_SUBMITTED");
}
```

**★★ 流程有分支需要人工选人 → 单据退回 `TO_BE_SUBMITTED`，等用户选完再发。**

### 回写的 13 个流程属性

```java
resultDto.setCaseId(content.getCaseId());
resultDto.setPreMatchResponseDto(content.getPreMatchResponseDto());
resultDto.setCaseSender(content.getSenderId());
resultDto.setCaseSenderDepartment(content.getSenderDepartmentId());
resultDto.setCaseSenderInstitution(content.getSenderInstitutionId());
resultDto.setCaseSenderPost(content.getSenderPostId());
resultDto.setCaseTitle(content.getSubject());
resultDto.setCaseState(content.getCaseState());
resultDto.setApprovalState(content.getApprovalState());
resultDto.setCaseStartTime(content.getCaseStartTime());
resultDto.setErrorMsg(content.getErrorMsg());
resultDto.setProcessType(content.getProcessType());
resultDto.setTemplateId(templateId);
```

---

## 7E. ★ 五条降级路径汇总（全部实证）

| # | 触发条件 | 单据状态 | 抛异常 | 日志关键字 |
|---|---|---|---|---|
| **1** | `prefixForUdc` 返回 null（**没配模板**） | 不变 | ❌ | `未配置流程模板或根据参数未查询到流程模板` |
| **2** | `content.errorMsg` 非空 | **`TO_BE_SUBMITTED`** | ❌ | 依赖 BPM 返回 |
| **3** | **RPC 异常** | `sendState=SENDING` + 进重试队列 | ✅ | `发送bpm流程rpc调用失败即将进入重试队列` |
| **4** | **`preMatch.isPop()==true`** | **`TO_BE_SUBMITTED`** | ❌ | `需要选人，更新单据状态为：TO_BE_SUBMITTED` |
| **5** | `BusinessException` | 不变 | ✅ | `发起流程业务异常` |

**⇒ #1 / #2 / #4 **都不抛异常** —— 调用方只能查库或查日志发现。**

---

## 7F. 错误码清单

| 错误码 | 含义 |
|---|---|
| `BPM_PROCESS_0001` | 单据数据不能为空 |
| `BPM_PROCESS_0002` | 获取旧单据状态枚举值失败（oldData） |
| `BPM_PROCESS_0003` | 获取新单据状态枚举值失败（newData） |
| `BPM_PROCESS_0004` | BPM 调用失败（带 message） |
| `BPM_PROCESS_0007` | 获取预发送请求参数失败 |
| `BOOT_1004` | 特殊透传码（原样抛出） |

---

## 7G. 对开发的实际指导

### 让单据走审批的唯一方式

```java
dto.setStatusType(BillStatusEnum.PENDING_REVIEW);   // 必须
ResultDto r = curdService.create4Bpm(dto);

// ★ 必须验证流程真的发起了
Map bpm = (Map) r.getResultMap().get("bpm");
Long caseId = (bpm != null) ? (Long) bpm.get("caseId") : null;
if (caseId == null) { /* 流程未发起 */ }
```

### 「发起没反应」诊断顺序

```
1. 日志 "未配置流程模板或根据参数未查询到流程模板"
   → 没配模板，检查 rootEntityName 是否匹配

2. 日志 "需要选人，更新单据状态为：TO_BE_SUBMITTED"
   → 流程有分支要选人，前端要弹选人框

3. 日志 "发送bpm流程rpc调用失败即将进入重试队列"
   → BPM 服务不可用，查 sendState=SENDING

4. 查库 sendState：SENDING = 进了重试队列，SEND_SUCCESS = 发起成功

5. 查库 statusType：TO_BE_SUBMITTED = 降级了
```

### 不要依赖返回值判断成功

```java
// ❌ 没抛异常 ≠ 流程发起成功
create4Bpm(dto);

// ✅ 自己校验 caseId + sendState
```

### 重试降级单据

```
TO_BE_SUBMITTED → TO_BE_SUBMITTED 什么都不做（状态机）
必须显式改成 PENDING_REVIEW 再调 update4Bpm
```

### 上下文依赖

**⇒ `create4Bpm` **不能在异步线程池或定时任务里裸调**，必须先建 `RequestContext` 和 `Apps` 上下文。**

---

## 7H. 证据索引

| 结论 | 证据 | 等级 |
|---|---|---|
| `ApproveFeatureService` 实现 `ApprovalCallBack` | `ApproveFeatureService.java:97-98` | `VERIFIED_STATIC_SOURCE` |
| `BpmUdcApiService` 是 `@DubboReference` | 同文件 `:103-104` | `VERIFIED_STATIC_SOURCE` |
| 状态机 5×3 转移矩阵 | `startProcess0` switch 全文 | `VERIFIED_STATIC_SOURCE` |
| 模板靠 `rootEntityName` + 6 参数查找 | `getBpmPrefixParams` | `VERIFIED_STATIC_SOURCE` |
| `formData` 按模板声明裁剪 | `sendProcess` 中 `filterMapData` | `VERIFIED_STATIC_SOURCE` |
| RPC 失败进重试队列 | `catch (Exception)` → `bpmRetryService.enqueue` | `VERIFIED_STATIC_SOURCE` |
| `preMatch.isPop()` 降级 | `sendProcess` 中 `if (...isPop())` | `VERIFIED_STATIC_SOURCE` |
| `sendState` 三态 | `SEND_SUCCESS` / `SENDING` 字面量 | `VERIFIED_STATIC_SOURCE` |
| 6 个错误码 | `BusinessException("BPM_PROCESS_000x")` | `VERIFIED_STATIC_SOURCE` |
| `saveDraft` / `repealProcess` 内部实现 | — | **UNVERIFIED**（未逐行读） |
| 是否真走 Dubbo 网络 | 只有 `@DubboReference` 注解 | **UNVERIFIED**（需运行时） |

