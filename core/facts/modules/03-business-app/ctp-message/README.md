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

## 落表

⚠️ **UNVERIFIED** —— 字节码索引不含 SQL/表名，本文件不写推测的表名。

取证路径（三条，任选其一，务必留证据）：

1. **jar 内 mapper**：`organization-biz` 里 `*.xml` / `*Mapper.java`
2. **库结构**：连 test2 的 MySQL 查 `information_schema.columns` 里 `tb_org_%`
3. **运行态**：开 SQL 日志跑一次写操作，看真实表名

在拿到上述证据前，本文件对「落哪张表」保持空。

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 11 接口 / 41 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 16 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 5 事件 / 4 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 9 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表 | 未取证 | `UNVERIFIED` |
