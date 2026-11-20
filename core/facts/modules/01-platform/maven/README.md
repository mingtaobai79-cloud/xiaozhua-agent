# 构建插件（maven）

## 一句话

`com.seeyon.maven` 域的**可调用接口面**：1 个构件、26 个类、0 个 facade 接口 / 0 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `seeyon-maven-plugin` | 其他 | 26 |
| **合计** | | **26** |

## 二、分层规律（写代码前必读）

`com.seeyon.maven` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

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

事件 0 个 · 监听器 0 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|

## web 层：Controller

共 0 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|

## 这个域没有 facade（为什么）

`com.seeyon.maven` 共 26 个类，是**Maven 构建插件**（代码生成、打包、依赖检查）。
只在构建期运行，不进运行时容器。

**结论**：Agent 不需要调它。它出现在索引里是为了说明「这 26 个类不是运行时能力」。

⚠️ 看到 `com.seeyon.maven.*` 的类不要当成平台 API 去引用。


## 落表

⚠️ **UNVERIFIED** —— 本模块构件 的 class 常量池里没有表名字面量。

原因：该模块的 SQL/表名不在 biz 层常量池（走 Dubbo 远端 / 走配置 / 纯计算或 SDK）。
不写推测表名。

## REST 路由

⚠️ **UNVERIFIED** —— 本模块的 web 构件里没有 `@RequestMapping` 动作。

原因：该模块只做远程调用（Dubbo/SPI）或本身无 HTTP 面，接口是给别的服务用的。
不写推测路径。

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 0 接口 / 0 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 0 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 0 事件 / 0 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 0 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 本模块无 HTTP 面 | `N/A` |
| 落表 | 本模块代码无表名常量，不适用 | `N/A` |
