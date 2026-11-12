# AppService 入参 DTO 字段表

## 1. Capability

补上「怎么传参」的最后一块。

之前给到的粒度只到这里：

```java
SingleResponse<BpmSendResultDto> send(SingleRequest<BpmSendDto> request);
```

知道要传 `BpmSendDto`，但**不知道它里面有什么字段**——等于还是不会用。

本格把 322 个 AppService 接口里 761 个入参 DTO 的字段全部摊开，
字段名 / 类型 / 是否常量逐字来自 javap。

## 2. Version

基线见 `docs/audit/artifacts/extension-surface-20261029/BASELINE.md`。

## 3. Input

```
interfaces.json  →  *.AppService 接口的每个方法
                    取 SingleRequest<X> / ListRequest<X> 里的 X
                    → 去 classes[X].fields 取字段
```

## 4. Required

传参三件套：

| 要素 | 从哪拿 |
|---|---|
| DTO 类型 | 方法签名 `SingleRequest<X>` 里的 X |
| DTO 字段 | 本格对应的域文件（`dto-fields/<域>.md`） |
| 包装方式 | `SingleRequest` / `ListRequest` 见 `transport-usage.md` |

## 5. Execution

```
① 打开包的 md（packages/<构件>.md），找到目标 AppService 接口
② 看方法签名 → 记下 SingleRequest<XxxDto>
③ 到 dto-fields/<域>.md 查 XxxDto 的字段表
④ 按字段名 set 值 → 按 transport-usage.md 包成 SingleRequest → 调方法
```

## 6. Side Effects

无（纯读文档）。但 DTO 字段与真实 REST 键名一致——字段名写错，请求体里就是 null 或被忽略，
平台通常不报错（**静默丢参**），这是最容易踩的坑。

## 7. Known Constraints

### 7.1 全量在哪

`docs/audit/artifacts/extension-surface-20261029/dto-fields/`

| 域 | 文件 | DTO 数 | 被引用处数 |
|---|---|---|---|
| 连接器 | `cip.md` | 308 | 431 |
| BPM 流程 | `bpm.md` | 96 | 112 |
| 协同（事项/人员/消息） | `ctp.md` | 95 | 125 |
| UDC 低代码 | `udc.md` | 81 | 201 |
| 组织架构 | `organization.md` | 72 | 101 |
| 平台基础 | `boot.md` | 32 | 96 |
| 应用通用 | `app.md` | 26 | 37 |
| 数据平台 | `cdp.md` | 23 | 28 |
| 移动端 | `m5.md` | 14 | 14 |
| 门户 | `portal.md` | 14 | 20 |

合计 **761 个 DTO**，缺字段 11 个（都是 `Long`/`String` 这类基础类型当泛型参数，正常）。

### 7.2 高频 DTO 速查

**BPM 发起流程** `BpmAppService.send()` → `BpmSendDto`（10 字段）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `templateCode` | `String` | 模板编码 |
| `templateId` | `Long` | 模板 ID（与 templateCode 二选一） |
| `currentUserId` | `Long` | 发起人 |
| `orgId` | `Long` | 发起人所属组织 |
| `bpmCommentDto` | `BpmCommentDto` | 处理意见（嵌套 DTO，同样在 `bpm.md` 里） |
| `formRecordId` | `String` | 表单数据 ID |
| `parameterData` | `Map<String,Object>` | 表单字段值，**键 = 实体属性名** |
| `caseId` | `Long` | 流程实例 ID（追发/回退时用） |
| `sendPolicy` | `String` | 发送策略 |

**提交** `submit()` → `BpmSubmitDto`（10 字段）、**保存草稿** `saveDraft()` → `BpmSaveDraftDto`。

组织侧 `OrgCommonAppService` 的入参多为 `OrgUnitDto` / `SelectPeopleDataDto`；
事项侧 `AffairUdcAppService` 用 `AffairSimpleDto`（61 字段）。

### 7.3 三个坑

**① `serialVersionUID` 不是参数**
每个 DTO 的字段表第一行通常是 `serialVersionUID | static long`——那是序列化常量，别当入参传。
凡是 `static` 前缀的字段都不是实例字段。

**② `parameterData` 是 Map，键 = 实体属性名**
`Map<String,Object>` 这类字段要填「属性名 → 值」，属性名来自设计的实体元数据，不是中文标题。
填中文标题也不会报错，就是**存不进**。

**③ 嵌套 DTO 要再查一层**
`bpmCommentDto` 的类型是 `BpmCommentDto`，它自己的字段在同一个域文件的另一节。
链式深两层以上（如 `BpmCommentDto.attachments[]`）要逐层展开查。

### 7.4 字段名 = REST 键名

平台把 DTO 直接序列化成请求体，**字段名就是 JSON 键名**。
这与 `custom-service-api.md` 里「REST 键名 = 字段名」是同一套规则。
所以：DTO 字段表 = 请求体格式说明书。

### 7.5 缺字段的 11 个

泛型直接用了 JDK 类型（`SingleRequest<String>` 之类），或者 DTO 定义在未抽取的外部 jar 里。
遇到时按需反编译那个 jar，不要猜字段。

## 8. Evidence

```
docs/audit/artifacts/extension-surface-20261029/dto-fields/
  README.md（索引：域 → 文件 → DTO 数）
  cip.md / bpm.md / ctp.md / udc.md / organization.md / boot.md / app.md / cdp.md / m5.md / portal.md
  每个 DTO：全名 + 被哪些方法当入参 + 字段表（name / type / static 标记）

生成器 tools/core/platform/emit_dto_fields.py
  正则 REQ = (?:SingleRequest|ListRequest)<([\w.$]+)>
  闸门：DTO 总数 < 500 视为抽取失败，exit 5
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 761 个入参 DTO 的字段名与类型 | `VERIFIED_STATIC_BYTECODE`（javap 原文） |
| 「字段名 = REST 键名」 | `VERIFIED_STATIC_BYTECODE`（DTO 字段 + transport 包装约定） |
| 每个字段的业务语义（该填什么值） | **UNVERIFIED**（索引只给名字与类型，语义要查设计态元数据或实测） |
| 哪些字段必填 | **UNVERIFIED**（javap 不带校验注解，必填规则在 `@NotNull` 之类的运行时注解里，需反编译带 `-v`） |
