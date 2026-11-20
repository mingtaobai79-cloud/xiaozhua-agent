# m5｜应用能力索引

> 构件 3 个 / 类 473 / 方法 4056
> 版本：5.3.265

## 一、构件清单

| 层 | 构件 | 类数 | 方法数 |
|---|---|---:|---:|
| facade | `m5-facade` | 55 | 504 |
| biz | `m5-biz` | 401 | 3373 |
| web | `m5-web` | 17 | 179 |

## 二、分层职责

| 层 | 你能用它做什么 | 调用方式 |
|---|---|---|
| **facade** | 对外契约：AppService 接口 + DTO | `@DubboReference`（有 `@DubboService` 才能远程） |
| **biz** | 实现层：业务编排 + 落库 | **不可直接调**，看它的入参理解行为 |
| **web** | REST 路由 | **不可直接调**，看路由 + 请求体 |

## 三、接口入参速查（biz/web 只看这个）

> 口径：biz/web 只记录「接口入参 + 这个接口干什么」，不逐方法展开。

（待补：按 facade 方法逐个填「入参 DTO / 用途」）

## 四、Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 构件与类数 | `extension-surface-full/interfaces-full.json`（473 类） | **VERIFIED_STATIC_BYTECODE** |
| 接口入参语义 | 未填 | **UNVERIFIED** |
