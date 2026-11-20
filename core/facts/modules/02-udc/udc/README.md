# udc｜应用能力索引

> 构件 22 个 / 类 3708 / 方法 40349
> 版本：3.8.105, 5.3.605

## 一、构件清单

| 层 | 构件 | 类数 | 方法数 |
|---|---|---:|---:|
| facade | `udc-facade` | 66 | 501 |
| biz | `udc-biz` | 1855 | 21992 |
| web | `udc-web` | 54 | 691 |
| module | `udc-affair` | 1 | 2 |
| module | `udc-app-common` | 15 | 69 |
| module | `udc-bpm` | 46 | 235 |
| module | `udc-cdpbi` | 49 | 218 |
| module | `udc-cicd` | 59 | 594 |
| module | `udc-cip` | 10 | 27 |
| module | `udc-common` | 424 | 4457 |
| module | `udc-dataflow` | 224 | 2491 |
| module | `udc-extend` | 82 | 618 |
| module | `udc-m5` | 11 | 144 |
| module | `udc-portal` | 58 | 766 |
| module | `udc-test` | 0 | 0 |
| module | `udc-upgrade` | 44 | 501 |
| module | `udc-user` | 37 | 586 |
| starter | `udc-starter-autocode` | 52 | 223 |
| starter | `udc-starter-customplan` | 78 | 1001 |
| starter | `udc-starter-dataflow` | 116 | 1122 |
| starter | `udc-starter-lowcode` | 121 | 1081 |
| starter | `udc-starter-runtime` | 306 | 2814 |

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
| 构件与类数 | `extension-surface-full/interfaces-full.json`（3708 类） | **VERIFIED_STATIC_BYTECODE** |
| 接口入参语义 | 未填 | **UNVERIFIED** |
