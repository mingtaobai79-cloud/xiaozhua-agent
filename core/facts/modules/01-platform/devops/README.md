# 运维（devops）

## 一句话

`com.seeyon.devops` 域的**可调用接口面**：6 个构件、245 个类、0 个 facade 接口 / 0 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `devops-starter-pipeline` | 其他 | 60 |
| `devops-starter-repo` | 其他 | 53 |
| `devops-starter-artifact` | 其他 | 51 |
| `devops-starter-common` | common | 51 |
| `devops-starter-migration` | 其他 | 16 |
| `devops-starter-images` | 其他 | 14 |
| **合计** | | **245** |

## 二、分层规律（写代码前必读）

`com.seeyon.devops` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

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

## facade 层：0 个接口 / 0 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| **合计** | **0** | **0** |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 0 个领域服务，下表列**方法数最多的 0 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|

## biz 层：事件与监听

事件 4 个 · 监听器 0 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| DeployApp | `DeployAppEvent` |
| NpmAppSync | `NpmAppSyncEvent` |
| PipelineBuild | `PipelineBuildEvent` |
| PresetApp | `PresetAppEvent` |

## web 层：Controller

共 0 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|

## 这个域没有 facade（为什么）

`com.seeyon.devops` 共 245 个类，包结构是 `devops.starter`，
即**运维/监控的 starter 组件**（健康检查、指标上报、灰度）。没有业务 AppService。

**结论**：运行时框架能力，业务代码不需要调。

它有 4 个事件类，用于运维侧监听，不在业务链路里。


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
| 0 接口 / 0 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 0 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 4 事件 / 0 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 0 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表 | 未取证 | `UNVERIFIED` |
