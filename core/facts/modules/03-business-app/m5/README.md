# 移动端（m5）

## 一句话

`com.seeyon.m5` 域的**可调用接口面**：3 个构件、473 个类、6 个 facade 接口 / 30 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `m5-biz` | biz | 401 |
| `m5-facade` | facade | 55 |
| `m5-web` | web | 17 |
| **合计** | | **473** |

## 二、分层规律（写代码前必读）

`com.seeyon.m5` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

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

## facade 层：6 个接口 / 30 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.m5.api` | 4 | 21 |
| `com.seeyon.m5.api.app` | 1 | 3 |
| `com.seeyon.m5.api.enterprise` | 1 | 6 |
| **合计** | **6** | **30** |

### `com.seeyon.m5.api`

#### TeamworkCoreAppService

`com.seeyon.m5.api.TeamworkCoreAppService` · 构件 `m5-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `launch` | `SingleRequest<TeamworkGroupCreateDto> arg0` | `SingleResponse<Long>` | 发起团队协作（创建团队） |
| `dismiss` | `SingleRequest<TeamworkGroupDismissDto> arg0` | `SingleResponse<Integer>` | 解散团队 |
| `join` | `SingleRequest<TeamworkGroupJoinDto> arg0` | `SingleResponse<Integer>` | 加入团队 |
| `quit` | `SingleRequest<TeamworkGroupQuitDto> arg0` | `SingleResponse<Integer>` | 退出团队 |
| `rename` | `SingleRequest<TeamworkGroupRenameDto> arg0` | `SingleResponse<Integer>` | 重命名分组 |
| `unbind` | `SingleRequest<TeamworkGroupUnbindDto> arg0` | `SingleResponse<Integer>` | 解绑分组 |
| `obtain` | `SingleRequest<Long> arg0` | `SingleResponse<TeamworkGroupInfoDto>` | 取团队信息 |
| `batchObtain` | `SingleRequest<List<Long>> arg0` | `ListResponse<TeamworkGroupInfoDto>` | 批量取团队信息 |
| `batchObtainExt` | `SingleRequest<List<Long>> arg0` | `ListResponse<TeamworkGroupInfoNumExtDto>` | 批量取团队信息（含扩展字段） |
| `obtainMemberPageListByCondition` | `PageRequest arg0` | `PageResponse<TeamworkMemberInfoDto>` | 按条件分页取团队成员 |
| `obtainAllMemberList` | `SingleRequest<Long> arg0` | `ListResponse<TeamworkMemberInfoDto>` | 取团队全部成员 |
| `obtainMemberListRequiredFields` | `SingleRequest<TeamworkMemberRequiredFieldDto> arg0` | `ListResponse<TeamworkMemberInfoDto>` | 列出字段Required |
| `obtainGroupIdListByUserId` | `SingleRequest<Long> arg0` | `ListResponse<Long>` | 按用户查其所在团队 groupId 列表 |

#### TeamworkMessageAppService

`com.seeyon.m5.api.TeamworkMessageAppService` · 构件 `m5-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `sendCard` | `SingleRequest<TeamworkCardMessageDto> arg0` | `SingleResponse<Void>` | 发送Card |
| `createNotification` | `SingleRequest<TeamworkNotificationMessageDto> arg0` | `SingleResponse<Long>` | 新建Notification |

#### TeamworkTabAppService

`com.seeyon.m5.api.TeamworkTabAppService` · 构件 `m5-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createTab` | `SingleRequest<TeamworkGroupTabCreateDto> arg0` | `SingleResponse<Long>` | 新建Tab |
| `createTabs` | `SingleRequest<List<TeamworkGroupTabCreateDto>> arg0` | `ListResponse<Long>` | 新建Tabs |
| `updateTab` | `SingleRequest<TeamworkGroupTabUpdateDto> arg0` | `SingleResponse<Integer>` | 修改Tab |
| `updateTabs` | `SingleRequest<List<TeamworkGroupTabUpdateDto>> arg0` | `SingleResponse<Integer>` | 修改Tabs |
| `deleteTab` | `SingleRequest<TeamworkGroupTabDeleteDto> arg0` | `SingleResponse<Integer>` | 删除Tab |

#### TeamworkTabGeneralizeAppService

`com.seeyon.m5.api.TeamworkTabGeneralizeAppService` · 构件 `m5-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `deleteTabs` | `SingleRequest<TeamworkGroupTabListDto> arg0` | `SingleResponse<Integer>` | 删除Tabs |

### `com.seeyon.m5.api.app`

#### AppManageCoreAppService

`com.seeyon.m5.api.app.AppManageCoreAppService` · 构件 `m5-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `check` | `SingleRequest<AppCheckRequestDto> arg0` | `SingleResponse<AppCheckDto>` | 检查应用 |
| `getLatestDownloadUrl` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 获取LatestDownloadUrl |
| `getLatestApp` | `SingleRequest<String> arg0` | `SingleResponse<AppDto>` | 获取应用Latest |

### `com.seeyon.m5.api.enterprise`

#### EnterpriseCoreAppSerivce

`com.seeyon.m5.api.enterprise.EnterpriseCoreAppSerivce` · 构件 `m5-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createEnterprise` | `SingleRequest<EnterpriseCreateDto> arg0` | `SingleResponse<Long>` | 新建Enterprise |
| `updateEnterprise` | `SingleRequest<EnterpriseUpdateDto> arg0` | `SingleResponse<Integer>` | 修改Enterprise |
| `deleteEnterprise` | `SingleRequest<EnterpriseDeleteDto> arg0` | `SingleResponse<Integer>` | 删除Enterprise |
| `selectEnterprise` | `PageRequest arg0` | `PageResponse<EnterpriseDto>` | 查询Enterprise |
| `selectsEnterprise` | `PageRequest arg0` | `PageResponse<EnterpriseDto>` | 批量查企业（多租户企业信息） |
| `selectByEnterpriseName` | `SingleRequest<String> arg0` | `SingleResponse<EnterpriseDto>` | 查询Enterprise按名称 |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 14 个领域服务，下表列**方法数最多的 14 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `GroupService` | 126 | 分组 · 查询×21 / 新建×18 / 处理×10 |
| `UserService` | 61 | 用户 · 查询×20 / 修改×6 / 新建×5 |
| `AppsService` | 59 | Apps · 上传×10 / 获取×10 / 查询×9 |
| `RobotService` | 55 | Robot · 处理×19 / 新建×4 / 查询×3 |
| `AbstractGroupService` | 26 | 分组 · 判断有×7 / 重置×2 / 转移×2 |
| `AbstractTokenService` | 14 | 令牌 · 新建×6 / 取消×2 / 获取×2 |
| `ApplicationService` | 10 | 应用 · 新建×2 / 修改×2 / 删除×2 |
| `ConferenceService` | 9 | Conference · 查询×2 / 处理×1 / 修改×1 |
| `EnterpriseService` | 6 | Enterprise · 查询×2 / 新建×1 / 修改×1 |
| `EntranceService` | 4 | Entrance · 获取×3 / 查询×1 |
| `ParameterService` | 4 | 参数 · 查询×2 / 修改×2 |
| `MessageHistoryService` | 4 | 消息 · 处理×1 / 搜索×1 |
| `ApplicationAuthService` | 2 | 应用认证 · 获取×2 |
| `M5DbService` | 1 | M5Db · 查询×1 |

## biz 层：事件与监听

事件 15 个 · 监听器 3 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| Application | `ApplicationEvent` |
| Group | `GroupCreateMessageEvent` |
| GroupDismissMessage | `GroupDismissMessageEvent` |
| GroupJoinAddMessage | `GroupJoinAddMessageEvent` |
| GroupJoinInviteMessage | `GroupJoinInviteMessageEvent` |
| GroupJoinMessage | `GroupJoinMessageEvent` |
| GroupJoinQRInviteMessage | `GroupJoinQRInviteMessageEvent` |
| GroupKickOutMessage | `GroupKickOutMessageEvent` |
| GroupQuitMessage | `GroupQuitMessageEvent` |
| GroupRenameMessage | `GroupRenameMessageEvent` |
| GroupRobotConnector | `GroupRobotConnectorEvent` |
| GroupRobotJoinMessage | `GroupRobotJoinMessageEvent` |
| GroupRobotQuitMessage | `GroupRobotQuitMessageEvent` |
| GroupSetAdminMessage | `GroupSetAdminMessageEvent` |
| GroupTransferMessage | `GroupTransferMessageEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `GroupEventListener` | 18 |
| `GroupRelationEventListener` | 5 |
| `PrivateEventListener` | 1 |

## web 层：Controller

共 17 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `GroupController` | 55 |
| 核心实体 CRUD | `AppManageController` | 22 |
| 核心实体 CRUD | `OpenApiController` | 16 |
| 核心实体 CRUD | `RcloudController` | 14 |
| 核心实体 CRUD | `UserController` | 14 |
| 核心实体 CRUD | `MemberController` | 12 |
| 核心实体 CRUD | `ApplicationController` | 10 |
| 核心实体 CRUD | `ConferenceController` | 7 |
| 核心实体 CRUD | `AuthenticationController` | 6 |
| 核心实体 CRUD | `EnterpriseController` | 5 |
| 核心实体 CRUD | `InfoController` | 3 |
| 核心实体 CRUD | `ChatSettingController` | 3 |
| 核心实体 CRUD | `FileTabController` | 3 |
| 核心实体 CRUD | `ServerInfoController` | 2 |
| 核心实体 CRUD | `ConfigurationController` | 2 |
| 核心实体 CRUD | `ShareController` | 2 |
| 核心实体 CRUD | `ApplicationAuthController` | 1 |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **20** 张（来源构件：`m5-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `m5_app_info` | — | 1 |
| `m5_app_version` | — | 1 |
| `m5_application_event` | — | 1 |
| `m5_application_operation` | — | 1 |
| `m5_chat_setting` | — | 1 |
| `m5_emoji` | — | 1 |
| `m5_enterprise` | — | 1 |
| `m5_file_tab` | — | 1 |
| `m5_group` | — | 1 |
| `m5_group_message_top` | — | 1 |
| `m5_group_message_top_r` | — | 1 |
| `m5_group_notice` | — | 1 |
| `m5_group_param` | — | 1 |
| `m5_group_robot` | — | 1 |
| `m5_group_robot_connector_e` | — | 1 |
| `m5_group_tab` | — | 1 |
| `m5_member` | — | 1 |
| `m5_notification` | — | 1 |
| `m5_setting` | — | 1 |
| `m5_token_user` | — | 1 |

## REST 路由

> 证据：`javap -v` 读 Controller 字节码里的 `@RequestMapping`/`@PostMapping` 注解值。
> 等级 `VERIFIED_STATIC_BYTECODE`（注解值是常量，非推断）。

**拼法**（端口/前缀按环境配置，以下为通用形）：

```
POST /service/{类级路径}/{方法级路径}
      ↑ 类级路径的第一段就是应用 code（organization / bpm / udc …），不要再加一层
  例：POST /service/udc/runtime/deploy-normal
      = DeployController 类级 `udc/runtime` + 方法级 `deploy-normal`（线上实测过）
```

控制器 **17** 个、路由 **160** 条（来源：`m5-web`）。

> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。
> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-m5.md`

| Controller | 类级路径 | 路由 |
|---|---|---:|
| `GroupController` | `m5/group` | 51 |
| `AppManageController` | `m5/application` | 22 |
| `OpenApiController` | `—` | 16 |
| `RcloudController` | `m5/rcloud` | 14 |
| `UserController` | `m5/user` | 13 |
| `MemberController` | `m5/member` | 12 |
| `ApplicationController` | `m5/application` | 10 |
| `ConferenceController` | `m5/conference` | 7 |
| `EnterpriseController` | `m5/enterprise` | 4 |
| `AuthenticationController` | `m5/auth` | 3 |
| `FileTabController` | `m5/file-tab` | 2 |
| `ShareController` | `m5/message` | 2 |
| `ChatSettingController` | `m5/chat-setting` | 2 |
| `ConfigurationController` | `m5/config` | 1 |
| `ApplicationAuthController` | `m5/appAuth` | 1 |
| `ServerInfoController` | `m5/server-info` | 0 |
| `InfoController` | `m5/info` | 0 |

前 15 条（其余见明细）：

| 方法 | 全路径 |
|---|---|
| `PostMapping` | `/service/m5/application/create` |
| `GetMapping` | `/service/m5/application/{id}` |
| `PostMapping` | `/service/m5/application/search` |
| `PostMapping` | `/service/m5/application/update-icon` |
| `PostMapping` | `/service/m5/application/update` |
| `PostMapping` | `/service/m5/application/upload-oss` |
| `PostMapping` | `/service/m5/application/upload` |
| `PostMapping` | `/service/m5/application/re-upload-oss` |
| `PostMapping` | `/service/m5/application/re-upload` |
| `PostMapping` | `/service/m5/application/dis-enabled` |
| `PostMapping` | `/service/m5/application/enabled` |
| `PostMapping` | `/service/m5/application/version/search` |
| `GetMapping` | `/service/m5/application/version/{id}` |
| `GetMapping` | `/service/m5/application/version/latest/{appId}` |
| `GetMapping` | `/service/m5/application/version/current/{appVersionId}` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 6 接口 / 30 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 14 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 15 事件 / 3 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 17 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（160 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| 落表（21 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |
