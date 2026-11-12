# 接口使用卡：拿到就能调

## 1. Capability

前面 22 格把平台拆成了「签名 / 字段 / 流转 / 调用通路」四份证据，但写一段扩展代码时要在
四份文件之间跳。本格把它们合成**一页一接口**：

```
## `BpmAppService`
`com.seeyon.bpm.api.common.BpmAppService`
实现 `BpmApiAppServiceImpl` · 26 个方法

### `send` → `BpmSendResultDto`
入参 `BpmSendDto`（com.seeyon.bpm.dto.operation.openapi.BpmSendDto）
  templateCode    String    ← 模板code
  templateId      Long      ← 模板ID · 模板code/模板ID两者传其一，如果都传，以模板code为准
  currentUserId   Long      ← userCode · 例:1 · 关联 OrgMemberDto
  ...
返回 `BpmSendResultDto` 字段
  caseId / subject ...
流转（反编译方法体）：
  Service `BpmUserTemplateService` → selectCanSendTemplateByCode
  Service `BpmOperationService` → send
  ...
泛化调用（interfaceName / methodName / paramType / genericType / paramJson 五个值怎么填）
```

## 2. Version

同 `BASELINE.md`。

## 3. Input

```
interfaces.json        接口全名 + 方法签名 + 入参/返回 DTO + 字段
dto-meta.json          字段中文名/示例/说明/关联 DTO（来自 @DtoAttribute）
dto-validations.json   校验注解（本版为空，平台不用 javax.validation）
impl-map.json          接口 → 实现类（269 个）
service-flow-20261103/ 实现类方法体调用链
```

## 4. Required

无（查表）。

## 5. Execution

```
① 找接口 → api-usage/<域>.md（10 个域文件，开头有「怎么调」两种模板）
② 看方法 → 卡片内「### 方法名 → 返回 DTO」
③ 填字段 → 字段行的「←」后面是平台自己写的中文名/示例/业务规则
④ 要精确 → 完整签名去 packages/，流转全文去 service-flow-，动作分类去 action-index.md
```

## 6. Side Effects

无（文档）。

## 7. Known Constraints

### 7.1 字段说明的真正来源：`@DtoAttribute`

平台不用 `javax.validation`，用的是自己的注解：

```java
private java.lang.Long templateId;
  @DtoAttribute(
    value="模板ID",
    example="",
    description="模板code/模板ID两者传其一，如果都传，以模板code为准"
  )
private java.lang.Long currentUserId;
  @DtoAttribute(value="userCode", example="1",
                relationDto="com.seeyon.organization.dto.core.response.OrgMemberDto")
```

注解元素（`com.seeyon.boot.annotation.DtoAttribute`）：
`value / description / example / hidden / xssProcess / dataI18n / relationApp /
relationHostAppName / relationAppName / relationDto / subRelation / sort / customs`

类级 `@DtoInfo`：`value / entity / sort / isPublic / customs`。

**覆盖：1331 个 DTO 里 1305 个有元信息（98%）**。

### 7.2 扫注解的两个坑

- **javap 必须带 `-p`**：`javap -v` 单独用**不输出 private 字段**，字段注解全丢
- **输出是 GBK**：中文 Windows 上按 utf-8 解会得到 `ģ��code` 这种乱码，要按 gbk 解

### 7.3 `value` 不总是中文名

有的字段 `value` 是编码名而不是中文名：

| 字段 | value | 实际含义 |
|---|---|---|
| `currentUserId` | `userCode` | 当前用户 ID |
| `orgId` | `orgCode` | 组织 ID |
| `parameterData` | `bpmSentWeakTypeEscapeService` | 表单参数（内部服务名，注解写错了） |

这时靠 `example` 和 `relationDto` 补：`currentUserId` 的 `relationDto` 指向
`OrgMemberDto`，说明传的是成员 ID 不是编码。

### 7.4 没有必填标记

平台不用 `@NotNull`，`@DtoAttribute` 也没有 required 元素。
**必填与否只能从 `description` 里的「必须」「两者传其一」这类措辞判断**，
或者实测（缺字段看报错）。

`dto-validations.json` 扫了 1331 个 DTO，`with_constraints = 0` —— 确认平台不用 javax.validation。

### 7.5 字段语义只有平台写的那些

`@DtoAttribute` 没写的字段（2% 的 DTO 完全没有元信息）只有字段名和类型，
**不要猜业务含义**。宁可标注「未说明」也不要编。

### 7.6 契约探针：编译验证

文档说「这么写」，但没人保证真能编译。`tools/core/platform/probe_contracts/` 里有两个探针，
用**真实 jar 编译**（不运行）：

| 探针 | 验证什么 |
|---|---|
| `ProbeBpmSend.java` | `BpmAppService.send(SingleRequest<BpmSendDto>)` → `SingleResponse<BpmSendResultDto>` |
| `ProbeUdc.java` | `EntityAppService.create` → `Long`；`ApplicationManagerAppService.deployNormal` → `DeployParamDto` |

跑法：

```
python tools/core/platform/probe_contracts.py \
  --src tools/core/platform/probe_contracts --repo <MAVEN_REPO> \
  --interfaces docs/audit/artifacts/extension-surface-20261029/interfaces.json
```

classpath **从 `interfaces.json` 的 `pkg` 字段自动推导**（import 的类 → 哪个构件 → 哪个 jar），
不用手写一长串 `-cp`。这一步顺带证明了索引的一个实际用途：
`EntityDto` 在 `udc-common` 而不是 `udc-facade`，编译报错前就能查到。

已跑通：2 探针 PASS / 2 个 .class。

**探针暴露的一个真问题**：`DeployNormalDto` 只有 3 个字段
（`lockCompatibility` / `generateLog` / `entityFullNameCondition`），**没有 `appId`**。
`appId` / `deployType` / `projectType` / `terminalType` 在**返回的** `DeployParamDto` 里。
所以「部署要传 appId」这个印象来自 REST 请求体，不是 AppService 入参——appId 走请求上下文。

## 8. Evidence

```
docs/audit/artifacts/api-usage/          10 个域文件 / 327 接口 / 3.30 MB
  udc.md            55 接口  483 方法  717 KB
  organization.md   48 接口  396 方法  698 KB
  cip.md            72 接口  552 方法  653 KB
  bpm.md            30 接口  227 方法  523 KB
  ctp.md            60 接口  350 方法  458 KB
  app / boot / cdp / m5 / portal（5 份，其余 335 KB）
  （生成器 DOMAIN_OF 认识 14 个域名、落盘 10 个；ai / file / formula 无接口，org 是 organization 别名）

docs/audit/artifacts/extension-surface-20261029/
  dto-meta.json            1331 扫 / 1305 有元信息
  dto-validations.json     1331 扫 / 0 有 javax 校验
  impl-map.json            269 接口 → 实现类

生成器
  tools/core/platform/emit_api_usage.py     出卡片（--dto-meta 带中文名/示例）
  tools/core/platform/scan_dto_meta.py      扫 @DtoAttribute/@DtoInfo
  tools/core/platform/scan_dto_validations.py 扫 javax 校验（本版 0 命中，留作对照）
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 1331 个 DTO 的 `@DtoAttribute` 元信息 | `VERIFIED_STATIC_BYTECODE`（javap -p -v） |
| 字段中文名/示例/说明逐字 | `VERIFIED_STATIC_BYTECODE` |
| 平台不用 javax.validation | `VERIFIED_STATIC_BYTECODE`（1331 扫 0 命中） |
| 卡片里的流转 | `VERIFIED_STATIC_BYTECODE`（反编译方法体，只到第一步） |
| **按卡片写的调用代码能编译** | **`VERIFIED_COMPILE`**（javac 21 真实 jar，2 探针 PASS） |
| `EntityDto` 在 udc-common 而非 udc-facade | `VERIFIED_COMPILE`（编译报错实证） |
| `DeployNormalDto` 无 appId | `VERIFIED_COMPILE` + `VERIFIED_STATIC_BYTECODE` |
| 字段是否必填 | **UNVERIFIED**（无注解可依，需实测） |
| `paramJson` 反序列化的边界行为 | **UNVERIFIED** |
| 调用是否真跑通（运行时） | **UNVERIFIED**（无运行环境） |
