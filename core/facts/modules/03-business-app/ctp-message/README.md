# 消息通知（message）

## 一句话

`com.seeyon.ctp` 域的**可调用接口面**：3 个构件、205 个类、11 个 facade 接口 / 41 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `ctp-message-biz` | biz | 151 |
| `ctp-message-facade` | facade | 45 |
| `ctp-message-web` | web | 9 |
| **合计** | | **205** |

## 二、分层规律（写代码前必读）

`com.seeyon.ctp` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

| 接口族 | 包 | 能力 | 什么时候用 |
|---|---|---|---|
| `*BaseAppService` | `api.core.*` | **含写**：create / update / 全字段查询 / dynamic | 要改数据，或要完整 DTO |
| `*CoreAppService` | `api.core.*` | **只读**：select*，Core DTO 字段精简 | 只查不改，性能敏感 |
| `OrgCommonAppService` | `api.common` | **业务聚合**：按选人数据解析、权限、组织域、扩展属性反查 | 需要「按规则找人」而不是按 id 查 |

调用顺序建议：

```
知道 id       →  XxxCoreAppService.selectXxxById        （最轻）
知道业务规则   →  OrgCommonAppService.selectXxxBySelectPeopleData
要写          →  XxxBaseAppService.create / update
```

## facade 层：11 个接口 / 41 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.ctp.message.api` | 9 | 39 |
| `com.seeyon.ctp.message.listener.websocket.api` | 2 | 2 |
| **合计** | **11** | **41** |

### `com.seeyon.ctp.message.api`

#### CtpMessageAppService

`com.seeyon.ctp.message.api.CtpMessageAppService` · 构件 `ctp-message-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<CtpMessageQueryDto>` | 分页查询消息按条件 |
| `readMessageByCode` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 读取消息按编码 |
| `deleteMessageByCode` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 删除消息按编码 |
| `getPushMessage` | `SingleRequest<Long> arg0` | `ListResponse<PushMessageDto>` | 获取推送消息 |
| `sendMessage` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 发送消息 |

#### CtpMessageClientAppService

`com.seeyon.ctp.message.api.CtpMessageClientAppService` · 构件 `ctp-message-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectSourceAndClassificationList` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpMessageSourceAndClassificationClientDto>` | 列表查询SourceAndClassification |
| `selectOtherList` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<CtpMessageOtherDto>` | 列表查询Other |
| `selectMessageListByCode` | `PageRequest arg0` | `PageResponse<CtpMessageBaseDto>` | 列表查询消息按编码 |
| `deleteMessageByCode` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 删除消息按编码 |
| `deleteMessageByMessageId` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 删除消息按消息 |
| `updateCtpMessageClientType` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 修改消息客户端类型Ctp |
| `moveOther` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 移动Other |
| `cleanCorner` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 清理角标 |
| `getReadStatus` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Map<String, Boolean>>` | 获取ReadStatus |
| `registerMobileInfo` | `SingleRequest<CtpMessageMobileDto> arg0` | `SingleResponse<Boolean>` | 注册Mobile |
| `unregisterMobileInfo` | `SingleRequest<CtpMessageMobileDto> arg0` | `SingleResponse<Boolean>` | 注销Mobile |
| `readMessageByCode` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Integer>` | 读取消息按编码 |

#### CtpMessageManageAppService

`com.seeyon.ctp.message.api.CtpMessageManageAppService` · 构件 `ctp-message-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `onlineInfo` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, Boolean>>` | 消息管理：查某用户在线状态（各端） |
| `kickOffline` | `SingleRequest<KickOfflineDto> arg0` | `SingleResponse<Integer>` | 踢出离线 |
| `selectBySetType` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<CtpMessageManageDto>` | 查询消息管理按类型 |
| `selectListByUserId` | `SingleRequest<Long> arg0` | `SingleResponse<Map<ManageSetTypeEnum, String>>` | 列表查询按用户（SingleRequest） |
| `set` | `SingleRequest<CtpMessageManageDto> arg0` | `SingleResponse<Integer>` | 设置消息管理 |
| `onlineNumber` | `—` | `SingleResponse<Long>` | 消息管理：统计在线人数 |
| `deleteMessageRegister` | `SingleRequest<String> arg0` | `SingleResponse<Boolean>` | 删除消息Register |
| `getMessageNumber` | `SingleRequest<MessageStatusDto> arg0` | `SingleResponse<Integer>` | 获取消息编号 |

#### CtpMessageOpenApiService

`com.seeyon.ctp.message.api.CtpMessageOpenApiService` · 构件 `ctp-message-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `sendMessageSimple` | `SingleRequest<MessageSendSimpleDto> arg0` | `SingleResponse<Boolean>` | 发送消息简单 |
| `sendMessage` | `SingleRequest<MessageSendDto> arg0` | `SingleResponse<Boolean>` | 发送消息 |
| `saveMessageTemplate` | `SingleRequest<CtpMessageTemplateDto> arg0` | `SingleResponse<Boolean>` | 保存消息模板 |

#### CtpMessageOperateAppService

`com.seeyon.ctp.message.api.CtpMessageOperateAppService` · 构件 `ctp-message-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `deleteMessageByIdentification` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 删除消息按Identification |

#### CtpMessageSourceTypeAppService

`com.seeyon.ctp.message.api.CtpMessageSourceTypeAppService` · 构件 `ctp-message-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createSource` | `SingleRequest<CtpMessageSourceBaseDto> arg0` | `SingleResponse<Long>` | 新建Source |
| `createType` | `SingleRequest<CtpMessageTypeDto> arg0` | `SingleResponse<Long>` | 新建类型 |

#### CtpMessageTypeAppService

`com.seeyon.ctp.message.api.CtpMessageTypeAppService` · 构件 `ctp-message-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<CtpMessageTypeDto> arg0` | `SingleResponse<Long>` | 新建消息类型 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<CtpMessageTypeDto>` | 查询消息类型按 id |
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<CtpMessageTypeDto>` | 分页查询消息类型按条件 |

#### CtpMessageUserSubscribeAppService

`com.seeyon.ctp.message.api.CtpMessageUserSubscribeAppService` · 构件 `ctp-message-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `resetSubscribe` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<Boolean>` | 重置订阅 |
| `selectListByUserId` | `SingleRequest<Map<String, Object>> arg0` | `SingleResponse<CtpMessageUserSubscribeQueryDto>` | 列表查询消息用户订阅按用户 |
| `subscribe` | `SingleRequest<ListSubscribeDto> arg0` | `SingleResponse<Integer>` | 订阅订阅 |

#### CtpUdcMessageSendAppService

`com.seeyon.ctp.message.api.CtpUdcMessageSendAppService` · 构件 `ctp-message-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `sendMessageByUser` | `SingleRequest<UdcMessageSendUserDto> arg0` | `SingleResponse<String>` | 发送消息按用户 |
| `sendMessageByChooseJson` | `SingleRequest<UdcMessageSendChooseDto> arg0` | `SingleResponse<String>` | 发送消息按ChooseJson |

### `com.seeyon.ctp.message.listener.websocket.api`

#### CtpMessageReceiveProcessService

`com.seeyon.ctp.message.listener.websocket.api.CtpMessageReceiveProcessService` · 构件 `ctp-message-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `receiveClientMessage` | `ChannelHandlerContext arg0` | `void` | 接收客户端消息 |

#### SubscribeProcessService

`com.seeyon.ctp.message.listener.websocket.api.SubscribeProcessService` · 构件 `ctp-message-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `subscribeMessage` | `TextMessageBase arg0` | `void` | 订阅消息 |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 16 个领域服务，下表列**方法数最多的 16 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `CtpMessageCounterService` | 30 | 消息 · 获取×5 / 读取×4 / 删除×3 |
| `CtpMessageService` | 25 | 消息 · 查询×6 / 删除×5 / 获取×5 |
| `CtpMessageClientTypeService` | 13 | 消息客户端类型 · 查询×6 / 修改×3 / 新建×2 |
| `CtpMessageUserSubscribeService` | 11 | 消息用户订阅 · 获取×4 / 订阅×2 / 重置×2 |
| `CtpMessageClientService` | 10 | 消息客户端 · 查询×3 / 修改×1 / 移动×1 |
| `CtpMessageManageService` | 10 | 消息管理 · 查询×2 / 踢出×1 / 判断×1 |
| `CtpMessageTemplateService` | 7 | 消息模板 · 获取×2 / 重置×2 / 查询×1 |
| `CtpTaskService` | 7 | 任务 · 查询×2 / 修改×2 / 新建×1 |
| `CtpMessageTypeService` | 6 | 消息类型 · 查询×5 / 新建×1 |
| `CtpMessageUserService` | 6 | 消息用户 · 推送×2 / 删除×1 / 修改×1 |
| `CtpMessageMobileService` | 4 | 消息 · 新建×1 / 修改×1 / 删除×1 |
| `CtpMessageSourceService` | 4 | 消息 · 查询×3 / 新建×1 |
| `CtpMessageBaseService` | 3 | 消息 · 查询×1 / 获取×1 |
| `CtpMessageClassificationService` | 2 | 消息 · 查询×2 |
| `SyncTaskService` | 2 | 任务 · 同步×2 |
| `CtpMessageOnlineService` | 1 | 消息在线 · 判断×1 |

## biz 层：事件与监听

事件 5 个 · 监听器 4 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| Mobile | `MobileEvent` |
| ProcessMaster | `ProcessMasterEvent` |
| ProcessMessage | `ProcessMessageEvent` |
| ProcessSlave | `ProcessSlaveEvent` |
| Sync | `SyncEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `SyncEventListener` | 3 |
| `ProcessMessageEventListener` | 2 |
| `MobileEventListener` | 2 |
| `PushMessageEventListener` | 1 |

## web 层：Controller

共 9 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `CtpMessageClientController` | 13 |
| 核心实体 CRUD | `CtpMessageManageController` | 10 |
| 核心实体 CRUD | `CtpMessageSourceController` | 8 |
| 核心实体 CRUD | `CtpMessageUserSubscribeController` | 8 |
| 核心实体 CRUD | `CtpMessageController` | 7 |
| 核心实体 CRUD | `CtpMessageClassificationController` | 6 |
| 核心实体 CRUD | `CtpMessageTemplateController` | 6 |
| 核心实体 CRUD | `CtpMessageTypeController` | 3 |
| 核心实体 CRUD | `IndexController` | 3 |

## 入参 DTO（字段级）

> 字段来自字节码 `fields`（含继承链，最多 3 层）；**字段名即 JSON 键名**（平台用 Jackson 默认命名，`shortName` 对应库列 `short_name`）。
> 包装类已揭开：`SingleRequest<T>` / `ListResponse<T>` 里看的是 `T` 的字段。
> 等级 `VERIFIED_STATIC_BYTECODE`。全量字段表：`docs/audit/artifacts/dto/DTO-ctp-message.md`

本模块 **21** 个入参/返回 DTO，**20** 个能取到字段。Top 12（按出现次数）：

| DTO | 出现 | 字段数 | 关键字段 |
|---|---:|---:|---|
| `CtpMessageTypeDto` | 4 | 7 | `id`, `name`, `code`, `messageSourceCode`, `parentCode`, `hidden`, `validate` |
| `CtpMessageMobileDto` | 2 | 10 | `id`, `userId`, `registerPlatform`, `pushTokens`, `deviceId`, `deviceType`, `deviceFirm`, `locale` |
| `CtpMessageManageDto` | 2 | 4 | `userId`, `setType`, `setValue`, `validate` |
| `CtpMessageQueryDto` | 1 | 27 | `userId`, `classificationList`, `onlineInfo`, `status`, `mobileOpenUrl`, `mobileOpenType`, `pcOpenUrl`, `pcOpenType` |
| `PushMessageDto` | 1 | 25 | `templateKey`, `messageTypeName`, `messageSourceCode`, `messageSourceName`, `mobileOpenUrl`, `mobileOpenType`, `pcOpenUrl`, `pcOpenType` |
| `CtpMessageSourceAndClassificationClientDto` | 1 | 17 | `unReadCount`, `cornerMarker`, `lastMessageContent`, `id`, `userId`, `icon`, `messageTime`, `topTime` |
| `CtpMessageOtherDto` | 1 | 7 | `unReadCount`, `cornerMarker`, `lastMessageContent`, `name`, `code`, `type`, `validate` |
| `CtpMessageBaseDto` | 1 | 26 | `status`, `classificationList`, `mobileOpenUrl`, `mobileOpenType`, `pcOpenUrl`, `pcOpenType`, `dialogModule`, `extendMap` |
| `KickOfflineDto` | 1 | 8 | `userId`, `tenantId`, `terminal`, `msg`, `i18nCode`, `bId`, `tId`, `validate` |
| `MessageStatusDto` | 1 | 2 | `statusEnum`, `validate` |
| `MessageSendSimpleDto` | 1 | 18 | `identification`, `paramMode`, `title`, `senderId`, `messageTypeCode`, `messageSourceCode`, `messageTime`, `chooseJson` |
| `MessageSendDto` | 1 | 34 | `messageChannelList`, `messageTag`, `uniqueId`, `chooseJson`, `templateDataMap`, `templateKey`, `templateSourceCode`, `operateJson` |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **11** 张（来源构件：`ctp-message-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `ctp_message` | 消息表 | 1 |
| `ctp_message_client_type` | 消息客户定义类型表 | 1 |
| `ctp_message_manage` | 消息设置表 | 1 |
| `ctp_message_mobile` | 移动端信息表 | 1 |
| `ctp_message_source` | 消息来源表 | 1 |
| `ctp_message_template` | 消息模版表 | 1 |
| `ctp_message_type` | 消息分类表 | 1 |
| `ctp_message_url` | 消息url注册表 | 1 |
| `ctp_message_user` | 用户消息关联表 | 1 |
| `ctp_message_user_subscribe` | 用户消息订阅表 | 1 |
| `ctp_task` | 延迟消息任务表 | 1 |

### 接口 → 表（4 条）

> `implements` = 字节码声明实现了该接口；`implements+field` = 再经它持有的
> Manager/Dao 字段一跳；两者都是静态事实。`stem` 只是类名同源（弱证据，需实测）。
> 表名本身都 `VERIFIED`；**哪个方法写哪张表仍未取证**。

| facade 接口 | 承载类 | 表 | 依据 |
|---|---|---|---|
| `CtpMessageAppService` | `CtpMessage` | `ctp_message` | `stem` |
| `CtpMessageManageAppService` | `CtpMessageManage` | `ctp_message_manage` | `stem` |
| `CtpMessageTypeAppService` | `CtpMessageType` | `ctp_message_type` | `stem` |
| `CtpMessageUserSubscribeAppService` | `CtpMessageUserSubscribe` | `ctp_message_user_subscribe` | `stem` |

## REST 路由

> 证据：`javap -v` 读 Controller 字节码里的 `@RequestMapping`/`@PostMapping` 注解值。
> 等级 `VERIFIED_STATIC_BYTECODE`（注解值是常量，非推断）。

**拼法**（以 `organization` 为例，`:8080` 之类按环境）：

```
POST /service/{类级路径}/{方法级路径}
      ↑ 类级路径的第一段就是应用 code（organization / bpm / udc …），不要再加一层
  例：POST /service/udc/runtime/deploy-normal
      = DeployController 类级 `udc/runtime` + 方法级 `deploy-normal`（线上实测过）
```

控制器 **9** 个、路由 **60** 条（来源：`ctp-message-web`）。

> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。
> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-ctp-message.md`

| Controller | 类级路径 | 路由 |
|---|---|---:|
| `CtpMessageClientController` | `ctp-message/ctp-message-client` | 13 |
| `CtpMessageManageController` | `ctp-message/ctp-message-manage` | 10 |
| `CtpMessageUserSubscribeController` | `ctp-message/ctp-message-user-subscribe` | 8 |
| `CtpMessageController` | `ctp-message/ctp-message` | 7 |
| `CtpMessageClassificationController` | `ctp-message/ctp-message-classification` | 6 |
| `CtpMessageTemplateController` | `ctp-message/ctp-message-template` | 6 |
| `CtpMessageSourceController` | `ctp-message/ctp-message-source` | 4 |
| `IndexController` | `ctp-message` | 3 |
| `CtpMessageTypeController` | `ctp-message/ctp-message-type` | 3 |

前 15 条（其余见明细）：

| 方法 | 全路径 |
|---|---|
| `PostMapping` | `/service/ctp-message/ctp-message-classification/create` |
| `PostMapping` | `/service/ctp-message/ctp-message-classification/update` |
| `PostMapping` | `/service/ctp-message/ctp-message-classification/delete` |
| `PostMapping` | `/service/ctp-message/ctp-message-classification/idx` |
| `PostMapping` | `/service/ctp-message/ctp-message-classification/search` |
| `PostMapping` | `/service/ctp-message/ctp-message-classification/search-for-web-list` |
| `PostMapping` | `/service/ctp-message/ctp-message-client/selectSourceList` |
| `PostMapping` | `/service/ctp-message/ctp-message-client/selectOtherList` |
| `PostMapping` | `/service/ctp-message/ctp-message-client/selectMessageListByCode` |
| `PostMapping` | `/service/ctp-message/ctp-message-client/move-other` |
| `PostMapping` | `/service/ctp-message/ctp-message-client/top` |
| `PostMapping` | `/service/ctp-message/ctp-message-client/notDisturb` |
| `PostMapping` | `/service/ctp-message/ctp-message-client/deleteMessageById` |
| `PostMapping` | `/service/ctp-message/ctp-message-client/deleteMessageByCode` |
| `PostMapping` | `/service/ctp-message/ctp-message-client/cleanCorner` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 11 接口 / 41 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 16 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 5 事件 / 4 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 9 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（60 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| REST 真机验证 | 23/23 条安全路由命中（100%） | `LIVE` |
| 落表（12 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |
