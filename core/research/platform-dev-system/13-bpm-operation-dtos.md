# BPM 操作 DTO 契约（发起 / 提交 / 退回 / 撤销 / 终止 / 取回 / 移交 / 督办）

> 来源：`bpm-facade-5.3.374.jar` CFR 反编译
> 路径：`com/seeyon/bpm/dto/operation/openapi/*.java`、`com/seeyon/bpm/dto/approval/*.java`
> ⚠️ **版本核对（2026-11-18）**：官方清单 **5.3.600**，本机 5.3.374（旧）。DTO **字段可能已新增**，用前请核对目标环境。
> 等级：`VERIFIED_STATIC_SOURCE`（源码逐字段读取，非签名推断）

---

## 0. 通用基底

所有操作 DTO **都继承 `CommandDto`**（`BpmRepealDto` 例外，继承 `BaseDto`）。

**调用形态统一：**
```java
SingleRequest<XxxDto> req = new SingleRequest<>();
req.setData(dto);
SingleResponse<XxxResultDto> resp = bpmAppService.xxx(req);
```

**所有 DTO 共有字段：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `currentUserId` | `Long` | **是**（`@NotNull`） | 当前用户，对应 organization 的 `OrgMemberDto`，别名 `userCode` |
| `bpmCommentDto` | `BpmCommentDto` | 否 | 意见信息 |

**⚠️ 对外部开放接口调用时，`currentUserId` 会被转成 `userCode`，`orgId` 转成 `orgCode`**（`@Custom(name="openApiCustom", escapeAttributeNameAlias)`）。这是平台对外的字段别名机制。

---

## 1. `BpmSendDto` —— 发起流程

**`@DtoInfo("工作流发送dto")`，继承 `CommandDto`**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| **`templateCode`** | `String` | 二选一 | 模板 code |
| **`templateId`** | `Long` | 二选一 | 模板 ID。**两者都传以 code 为准** |
| **`currentUserId`** | `Long` | **是** | 发起人 |
| `orgId` | `Long` | 否 | 当前机构 |
| `bpmCommentDto` | `BpmCommentDto` | 否 | 意见 |
| **`formRecordId`** | `String` | 否 | 表单数据 ID |
| **`parameterData`** | `Map<String,Object>` | 否 | **流程参数**（`weakTypeEscapeBean=bpmSentWeakTypeEscapeService`） |
| `caseId` | `Long` | 否 | 流程实例 ID |
| **`sendPolicy`** | `String` | 否 | **默认 `"node"`**。可选：`node`（加节点）/ `exception`（抛异常） |

**★★ 两个关键点：**

**① `sendPolicy` 决定「发起失败怎么办」**
```
node       → 失败时降级为「加节点」继续（默认，宽松）
exception  → 失败直接抛异常（严格，业务方要自己 catch）
```
**⇒ 业务单据发起流程，通常用 `node`；需要强一致时用 `exception`。**

**② `parameterData` 是弱类型 Map**
不是强类型对象，平台用 `bpmSentWeakTypeEscapeService` 做类型转义。
**⇒ 传参不能依赖编译期检查，字段名错了运行期才报。**

**返回：`BpmSendResultDto`**
```java
private Long   caseId;    // 流程实例ID
private String subject;   // 标题
```
**⇒ 发起成功后必须回写 `caseId` 到业务单据，否则找不到流程实例。**

---

## 2. `BpmSubmitDto` —— 提交

**`@DtoInfo("工作流提交dto")`**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| **`affairId`** | `Long` | **是** | 事项 ID |
| **`currentUserId`** | `Long` | **是** | 当前用户 |
| `orgId` | `Long` | 否 | 当前机构 |
| `bpmCommentDto` | `BpmCommentDto` | 否 | 意见 |
| `formData` | `Map<String,Object>` | 否 | 表单数据（选择提交时填） |
| `changeNodeRequestDtos` | `List<ChangeNodeRequestDto>` | 否 | **加签参数，不加签传 null** |
| `preMatchRequestDto` | `PreMatchRequestDto` | 否 | 预提交分支匹配结果 |
| `onlyCheck` | `Boolean` | 否 | **仅校验，不真提交** |
| `operationType` | `OperationEnum` | 否 | **默认提交**。可选 `SUBMIT` / `AGREE`（已阅/同意） |

**★★ 三个关键点：**

**① 提交的入口键是 `affairId`，不是 `caseId`**
```
发起（send）     → 拿 caseId
提交（submit）   → 要 affairId
```
**⇒ 一个流程实例（case）可以有多个事项（affair）。提交是「办某一件事」，所以用 affairId。**

**② `onlyCheck=true` 可以干跑**
**⇒ 前端「提交前校验」就是调这个方法，不落库。**

**③ `operationType` 决定语义**
```
SUBMIT   提交
AGREE    同意（已阅）
不传      默认提交
```
**⇒ 「同意」和「提交」在平台是同一入口的两个枚举值，不是两个方法。**

**返回：`BpmSubmitResultDto`**
```java
private PreMatchResponseDto preMatchResponseDto;
private PreMatchResponseDto mainPreMatchResponseDto;
```
**⇒ 返回的是「分支匹配结果」，说明提交可能触发分支，需要二次确认。**

---

## 3. `BpmStepBackDto` —— 退回（最复杂，16 字段外的 9 个语义字段）

**`@DtoInfo("工作流退回dto")`**

### 3.1 定位字段（三选一组合）

| 字段 | 类型 | 说明 |
|---|---|---|
| `affairId` | `Long` | 事项 ID。**`caseId` 不传时必填** |
| `caseId` | `Long` | 流程实例 ID。**`affairId` 不传时必填** |
| `pendingNodeId` | `String` | 当前节点 ID。**`affairId` 不传时必填** |

**⇒ 两种定位模式：**
```
模式A：只传 affairId              → 平台自己推到当前节点
模式B：传 caseId + pendingNodeId  → 显式指定在哪里退
```

### 3.2 退回目标（`selectTargetNodeId` 三态）

**`@DtoAttribute` 原文说明（关键）：**

> 支持三种方式：
> 一、值为空字符串表示上节点；
> 二、值为具体的节点 ID 表示指定退回，`submitStyleAfterStepBack` 必填；
> 三、值为 `start`，退回到发起节点，且 `submitStyleAfterStepBack` 的值只能为 `NODE_GO_BACK`

```
""          → 退回上一节点
"<nodeId>"  → 退回到指定节点（必须配 submitStyleAfterStepBack）
"start"     → 退回到发起节点（submitStyleAfterStepBack 只能是 NODE_GO_BACK）
```

### 3.3 退回后如何再提交

**`submitStyleAfterStepBack`（`AppointStepBackStyleEnum`）**
```java
NONE(-1)         不使用
NODE_GO_BACK(0)  退回到节点后，走节点原路（默认）
NODE_TO_ME(1)    退回到「我」（提交给我）
```

**`nodeToMeItem`（`StepBackNodeToMeSubmitModeEnum`）—— 仅 `NODE_TO_ME` 时有效**
```java
SUBMIT_TO_ME(0)   仅提交给我（默认）
SUBMIT_TO_ALL(1)  提交给退回节点全部处理人
```

**⇒ 这两层组合决定「退回后谁来处理」：**
```
NODE_GO_BACK                     → 退回节点按原规则重新处理
NODE_TO_ME + SUBMIT_TO_ME        → 只有我处理
NODE_TO_ME + SUBMIT_TO_ALL       → 该节点所有人处理
```

### 3.4 人员重新匹配

**`targetNodePeopleNeedReMatch`（默认 `false`）**

原文说明：
> 退回到的目标节点是否需要重新匹配人员，指定退回只有流程重走才生效，提交给我不生效，`false`：取上次匹配的人员，`true`：重新匹配

**⇒ 三条约束：**
1. 只有「指定退回」生效
2. 「提交给我」不生效
3. `false` 复用上次匹配人员，`true` 重新走选人规则

### 3.5 其他

| 字段 | 类型 | 说明 |
|---|---|---|
| `currentUserId` | `Long` | **必填** |
| `bpmCommentDto` | `BpmCommentDto` | 意见 |
| `formData` | `Map<String,Object>` | 表单数据 |

---

## 4. `BpmSaveDraftDto` —— 存草稿

**`@DtoInfo("工作流保存待发dto")`**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `templateCode` | `String` | 二选一 | 模板 code |
| `templateId` | `Long` | 二选一 | 模板 ID（以 code 为准） |
| **`currentUserId`** | `Long` | **是** | 当前用户 |
| `bpmCommentDto` | `BpmCommentDto` | 否 | 意见 |
| **`formRecordId`** | `String` | 否 | **表单数据 ID**（有值表示外部已保存，工作流只更新） |
| `formData` | `Map<String,Object>` | 否 | 单据数据 |
| `caseId` | `Long` | 否 | 流程实例 ID |

**★ `formRecordId` 的语义（原文）：**
> 传表单数据id，表示外部已经保存了表单数据，工作流调用更新即可，如果没有传表单数据id，需要工作流调用接口保存表单数据

**⇒ 草稿有两种模式：**
```
传 formRecordId    → 工作流只更新已有表单
不传 formRecordId  → 工作流负责保存表单数据
```

**返回：`BpmSaveDraftResultDto`**（在 `dto/operation/openapi/`）

---

## 5. `BpmRepealDto` —— 撤销（发起人撤回）

**`@DtoInfo("工作流撤销请求dto")`，⚠️ 继承 `BaseDto`（不是 CommandDto）**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `affairId` | `Long` | 否 | 事项 ID |
| `caseId` | `Long` | 否 | 流程实例 ID。**`affairId` 存在则取其 ID** |
| **`currentUserId`** | `Long` | **是** | 当前用户 |
| `bpmCommentDto` | `BpmCommentDto` | 否 | 意见 |
| `formData` | `Map<String,Object>` | 否 | 表单数据（选择提交时填） |
| **`needCheckAuth`** | `Boolean` | 否 | **默认 `TRUE`**（hidden） |
| **`needCheckPermission`** | `Boolean` | 否 | **默认 `TRUE`**（hidden） |

**⇒ `needCheckAuth` / `needCheckPermission` 默认都是 TRUE，是「越权保护开关」。**
**⇒ 内部系统调用时可关闭，但开放接口绝不建议关。**

---

## 6. `BpmStopDto` —— 终止

**`@DtoInfo("终止操作dto")`**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `affairId` | `Long` | 否 | 事项 ID |
| `caseId` | `Long` | 否 | 流程实例 ID。**某些场景下没有 affairId** |
| **`currentUserId`** | `Long` | **是** | 当前用户 |
| `bpmCommentDto` | `BpmCommentDto` | 否 | 意见 |
| `formData` | `Map<String,Object>` | 否 | 表单数据 |
| `needCheckAuth` | `Boolean` | 否 | 默认 TRUE（hidden） |
| `needCheckPermission` | `Boolean` | 否 | 默认 TRUE（hidden） |

**⇒ 与撤销的区别：终止是流程走完（不可恢复），撤销是回到草稿（可再发）。**

---

## 7. `BpmTakeBackDto` —— 取回（3 个字段，最简）

**`@DtoInfo("工作流取回dto")`**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| **`affairId`** | `Long` | **是** | 事项 ID |
| **`currentUserId`** | `Long` | **是** | 当前用户 |
| `bpmCommentDto` | `BpmCommentDto` | 否 | 意见 |

**⇒ 取回没有 `caseId`，只有 `affairId` —— 是「把自己办过的那件事拿回来」。**

---

## 8. `BpmReplaceDto` —— 移交（换人）

**`@DtoInfo("工作流移交dto")`**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| **`affairId`** | `Long` | **是** | 事项 ID |
| **`currentUserId`** | `Long` | **是** | 当前用户 |
| `bpmCommentDto` | `BpmCommentDto` | 否 | 意见 |
| **`selectPeopleDatas`** | **`String`** | **是** | **需要移交的选人信息（JSON 字符串）** |

**⇒★ `selectPeopleDatas` 是 `String` 不是 DTO 列表 —— 与组织域的 `*Json` 变体同构，前端直接传选人 JSON。**

---

## 9. `BpmPauseDto` —— 督办挂起（暂停）

**`@DtoInfo("工作流督办挂起请求dto")`**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| **`caseIds`** | `List<Long>` | 否 | **流程实例 ID 集合（批量）** |
| **`currentUserId`** | `Long` | **是** | 当前用户 |
| `orgId` | `Long` | 否 | 当前机构 |
| **`comment`** | **`String`** | 否 | 意见（**注意是 String，不是 BpmCommentDto**） |
| `sendMessage` | `Boolean` | 否 | **默认 `true`**，是否发消息 |

**⇒★ 两个差异点：**
1. **`caseIds` 是批量**，暂停天然支持多实例
2. **`comment` 是裸 String**，不是 `BpmCommentDto` —— 与其他操作不一致

**⇒ `cancelPause` 用的是同一个 `BpmPauseDto`（恢复也传同样的入参）。**

---

## 10. `BpmCommentDto` —— 意见信息

**继承 `BaseDto`**

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `Long` | 意见 ID |
| `opinion` | `String` | **意见（常用）** |
| `content` | `String` | 内容 |
| `richContent` | `String` | 富文本内容 |
| `attachmentStorageIds` | `List<BpmAttachmentStorageDto>` | **附件 storageKey 列表** |
| `operationCaption` | `String` | 操作标题 |
| `hidden` | `Boolean` | 是否隐藏 |
| `showPerson` | `String` | 显示人 |
| `extra` | `Map<String,Object>` | 扩展 |
| `attitudeCaption` | `String` | 态度标题（同意/不同意等） |
| `actionTime` | `Date` | 操作时间 |
| `opinionUserId` | `Long` | 意见人 |
| `opinionAccountId` | `Long` | 意见人账号 |

**⇒ 附件通过 `attachmentStorageIds` 传 storageKey（与文件域 `StorageKeyService` 同源）。**

---

## 11. `OperationEnum` —— 操作类型全枚举

```java
DRAFT("DRAFT", "暂存草稿", "DRAFT", false)
SEND("SEND", "发送", "SEND", true)
RE_SEND("RE_SEND", "发起人再次发起", null, true)
SUBMIT("SUBMIT", "提交", "SUBMIT", true)
TEMPORARY("TEMPORARY", "暂存待办", "TEMPORARY", true)
STOP("STOP", "终止", "TERMINATION", true)
SUPERVISE_STOP("SUPERVISE_STOP", "督办终止", "SUPERVISE_STOP", true)
REPEAL("REPEAL", "撤销流程", "UNDO", true)
SUPERVISE_REPEAL("SUPERVISE_REPEAL", "督办撤销", "UNDO", true)
TAKE_BACK("TAKE_BACK", "取回", "RETRIEVE", false)
BACK("BACK", "回退", "BACK", true)
SUPERVISE_BACK("SUPERVISE_BACK", "督办回退", "BACK", true)
START_BACK("START_BACK", "发起者回退", "BACK", true)
TRANSFER("TRANSFER", "移交", "TRANSFER", true)
SUPERVISE_TRANSFER("SUPERVISE_TRANSFER", "督办移交", "SUPERVISE_TRANSFER", true)
AGREE("AGREE", "同意", "AGREE", true)
...
```

**★ `SUPERVISE_*` 系列是「督办」专用 —— 督办人能终止/撤销/回退/移交别人的流程。**
**⇒ 这是一条**特权路径**，普通业务不应用。**

---

## 12. UDC 专用 DTO（与 openapi 版不同！）

### 12.1 `BpmSendUdcDto`（`dto/approval/`）

| 字段 | 类型 | 必填 |
|---|---|---|
| `templateId` | `Long` | — |
| **`rootEntityId`** | `Long` | — |
| **`rootEntityName`** | `String` | — |
| `caseId` | `Long` | — |
| **`userId`** | `Long` | **是**（`userId不能空`） |
| `commentDto` | `BpmCommentDto` | — |
| `preMatchRequestDto` | `PreMatchRequestDto` | — |
| `formData` | `Map<String,Object>` | — |
| **`formRecordId`** | **`Long`** | **是**（`表单记录id不能为空`） |
| `applicationName` | `String` | — |
| `startFormUrl` | `String` | — |
| `changeNodeRequestDtos` | `List<ChangeNodeRequestDto>` | — |
| `informAddSelectPeoples` | `String` | — |

**★★ 与 openapi 版的三处关键差异：**

| 项 | `BpmSendDto`（openapi） | `BpmSendUdcDto`（UDC） |
|---|---|---|
| 用户字段 | `currentUserId` | **`userId`** |
| 表单 ID | `formRecordId` **String** | **`formRecordId` Long** |
| 模板定位 | `templateCode` / `templateId` | **`rootEntityId` / `rootEntityName`** |
| 意见字段 | `bpmCommentDto` | **`commentDto`** |

**⇒ 这就是「UDC 单据怎么找到自己的流程」的答案：**
```
用 rootEntityId / rootEntityName（根实体）定位模板
而不是用 templateCode
```

### 12.2 `BpmSaveDraftUdcDto`

| 字段 | 类型 | 必填 |
|---|---|---|
| `templateId` | `Long` | — |
| `rootEntityId` | `Long` | — |
| `rootEntityName` | `String` | — |
| **`userId`** | `Long` | **是** |
| `commentDto` | `BpmCommentDto` | — |
| `formData` | `Map<String,Object>` | — |
| **`formRecordId`** | **`Long`** | **是** |
| `templateGuid` | `Long` | — |
| **`pageUrl`** | `String` | — |
| **`pageType`** | `PageTypeEnum` | — |
| **`pageGuid`** | `Long` | — |
| `bpmOperationNodeDto` | `BpmOperationNodeDto` | — |

**★ UDC 草稿多了页面上下文（`pageUrl` / `pageType` / `pageGuid`）—— 因为它需要知道从哪个页面存草稿。**

---

## 13. 调用速查表（可直接照抄）

### 13.1 发起单据（UDC 模式，推荐）

**✅ 方法名已确认：`BpmUdcApiService.sendForUdc`（不是 `BpmAppService.send`）**

```java
BpmSendUdcDto dto = new BpmSendUdcDto();
dto.setRootEntityId(rootEntityId);        // 单据类型（根实体）
dto.setRootEntityName(rootEntityName);
dto.setUserId(currentUserId);              // 注意是 userId
dto.setFormRecordId(billId);               // 注意是 Long
dto.setFormData(formDataMap);
dto.setApplicationName(appName);
dto.setCommentDto(commentDto);

SingleRequest<BpmSendUdcDto> req = new SingleRequest<>();
req.setData(dto);
SingleResponse<BpmApiSendApiResponseDto> resp =
    bpmUdcApiService.sendForUdc(req);      // ← 已实测确认
```

### 13.2 发起单据（openapi 模式）

```java
BpmSendDto dto = new BpmSendDto();
dto.setTemplateCode("TPL_XXX");            // 或用 setTemplateId
dto.setCurrentUserId(userId);
dto.setFormRecordId(String.valueOf(billId));  // 注意是 String
dto.setParameterData(paramMap);
dto.setSendPolicy("node");                 // 默认值
```

### 13.3 提交

```java
BpmSubmitDto dto = new BpmSubmitDto();
dto.setAffairId(affairId);                 // 必须 affairId
dto.setCurrentUserId(userId);
dto.setOperationType(OperationEnum.SUBMIT);  // 或 AGREE
dto.setOnlyCheck(false);                   // true = 只校验
dto.setFormData(formDataMap);              // 可选
```

### 13.4 退回上一节点

```java
BpmStepBackDto dto = new BpmStepBackDto();
dto.setAffairId(affairId);
dto.setCurrentUserId(userId);
dto.setSelectTargetNodeId("");              // "" = 上一节点
```

### 13.5 退回到发起节点

```java
dto.setSelectTargetNodeId("start");
dto.setSubmitStyleAfterStepBack(AppointStepBackStyleEnum.NODE_GO_BACK);
```

### 13.6 退回到指定节点

```java
dto.setSelectTargetNodeId(targetNodeId);
dto.setSubmitStyleAfterStepBack(AppointStepBackStyleEnum.NODE_TO_ME);
dto.setNodeToMeItem(StepBackNodeToMeSubmitModeEnum.SUBMIT_TO_ME);
dto.setTargetNodePeopleNeedReMatch(true);   // 重新匹配人员
```

### 13.7 撤销 / 终止 / 取回 / 移交

```java
// 撤销
BpmRepealDto r = new BpmRepealDto();
r.setAffairId(affairId);
r.setCurrentUserId(userId);
r.setNeedCheckAuth(true);          // 默认
r.setNeedCheckPermission(true);

// 终止
BpmStopDto s = new BpmStopDto();
s.setCaseId(caseId);               // 或 affairId
s.setCurrentUserId(userId);

// 取回（只有 2 个必填）
BpmTakeBackDto t = new BpmTakeBackDto();
t.setAffairId(affairId);
t.setCurrentUserId(userId);

// 移交
BpmReplaceDto p = new BpmReplaceDto();
p.setAffairId(affairId);
p.setCurrentUserId(userId);
p.setSelectPeopleDatas(selectPeopleJson);   // JSON 字符串
```

---

## 14. 陷阱清单（实测教训）

| # | 陷阱 | 后果 |
|---|---|---|
| 1 | 用 `caseId` 调 `submit` | 提交要 `affairId`，传 caseId 无效 |
| 2 | `formRecordId` 类型搞混 | openapi 是 `String`，UDC 是 `Long` |
| 3 | 用 `currentUserId` 调 UDC 接口 | UDC 用 `userId` |
| 4 | 发起后不回写 `caseId` | 后续找不到流程实例 |
| 5 | `targetNodePeopleNeedReMatch` 配「提交给我」 | 不生效（原文明确） |
| 6 | `selectTargetNodeId="start"` 配 `NODE_TO_ME` | 非法（只能是 `NODE_GO_BACK`） |
| 7 | `selectTargetNodeId=节点ID` 不配 `submitStyleAfterStepBack` | 必填校验失败 |
| 8 | `BpmPauseDto` 传 `BpmCommentDto` | 它的 `comment` 是 String |
| 9 | `sendPolicy` 不设 | 默认 `node`（宽松降级），要严格必须设 `exception` |
| 10 | `parameterData` / `formData` 字段名拼错 | 弱类型 Map，编译期不报，运行期静默失效 |

---

## 15. 未解决（下一轮）

| 项 | 状态 |
|---|---|
| ~~`BpmAppService` 里 UDC 方法的确切名字~~ | ✅ **已解决**：`BpmUdcApiService.sendForUdc`，`BpmAppService` 无 UDC 方法 |
| ~~`BpmUdcApiService` 10 个方法签名~~ | ✅ **已解决**：全部 10 个已实测（见 11-bpm-domain.md §4） |
| `ApprovalCallBack` 实现类（UDC→BPM 实际桥） | 未读 |
| `ChangeNodeRequestDto`（加签参数结构） | 未读 |
| `PreMatchRequestDto` / `PreMatchResponseDto`（分支匹配） | 未读 |
| `PageTypeEnum` 取值 | 未读 |
| `deleteCaseByIdForUdc` 两个 Long 的含义 | **UNVERIFIED** |
| `BpmApiSendApiResponseDto` 字段 | 未读 |