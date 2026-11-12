# UDC 九大域能力面盘点 + 跨域公用候选

> 证据：程序化实测（`registry` 全量 + 目录扫描），不是引用旧声明。
> 日期：2026-10-23。生成方式：读 `UdcOperationRegistry.default()._contracts` + `rglob`。
> ⚠ 本表只反映**契约与资产存量**，不等于「能力可用」。可用性看各域事实格的 R-E9。

## 一、九域能力面（契约口径）

| 域 | 契约 | 写面 | 事实件 | 脚本 | 状态分布 |
|---|---|---|---|---|---|
| application | 42 | 7 | 7 | 4 | VERIFIED_STATIC 19 / **OBSERVED 16** / DENIED 7 |
| entity | 28 | 6 | 8 | 0 | VERIFIED_STATIC 19 / UNKNOWN 9 |
| setting | 39 | **22** | 15 | **62** | VERIFIED_STATIC 5 / **OBSERVED 34** |
| flow | 13 | 3 | 0 | 0 | VERIFIED_STATIC 13 |
| menu | 5 | 0 | 0 | 0 | VERIFIED_STATIC 5 |
| bi | 5 | 0 | 0 | 0 | VERIFIED_STATIC 5 |
| role | 1 | 0 | 0 | 0 | VERIFIED_STATIC 1 |
| **rule** | **0** | **0** | 0 | 0 | — |
| **column** | **0** | **0** | 0 | 0 | — |

合计 148 条契约。

### 读法（别把状态当完成率）

```
OBSERVED                   活体上真发过、真拿到回包
VERIFIED_STATIC_BYTECODE   反编译坐实路径与 DTO，**没跑过**
DENIED                     策略层默认拒发（与"跑没跑过"无关）
UNKNOWN                    路径未定
```

**两个反向的错**：把 `DENIED` 读成"没实现"；把 `VERIFIED_STATIC` 读成"已实现"。

### 真实短板

```
规则域  0 契约   ← 最大的空
栏目域  0 契约
菜单域  5 契约、0 写面、0 事实
BI 域   5 契约、0 写面、0 事实
角色域  1 契约、0 写面、0 事实
实体域  UNKNOWN 9 条（路径未定）
```

⇒ 「不要少内容」的真正缺口在**规则域与栏目域**：这两个域连契约都没有。

### 未归类的 operation（8 组，共 14 条）

```
database       udc.database.query_data
attachment     ×3   template_get_by_guid / list_by_guids / list_by_app_id
flexible       ×5   sandbox.flexible.*（测试状态/部署 CRUD）
operation_log  ×2   init_data / search
collaboration  ×1
theme          ×1
version        ×1
ws             ×1
```

这些不属于九域任何一域，是**平台级能力**。放 `components/platform_operations/`。

## 二、重复能力矩阵 —— 为什么"同名动作"不该抽公用

| 动作 | 出现域数 | 是否该抽 |
|---|---|---|
| search | 4（entity/menu/operation_log/setting） | ❌ 不抽 |
| list | 4（application/entity/setting/version） | ❌ 不抽 |
| create | 3（entity/flow/setting） | ❌ 不抽 |
| update | 3（entity/flow/setting） | ❌ 不抽 |
| get | 3（application/entity/setting） | ❌ 不抽 |

**理由**：这些只是**动词同名**，DTO、必填槽位、错误码、落库表**完全不同**。
把它们抽象成 `create()` 只会得到一个什么都做不了的函数。

判据：**抽公用的依据是「同一份实现被多处复制」，不是「名字一样」。**

## 三、真正该抽的公用（已落地 3 项）

| 公用能力 | 位置 | 判据（实测量） |
|---|---|---|
| 表达式引擎 | `components/udc/expression/` | 出现在 **5 个模块**（实体字段/字段集/页面规则/微流程/实体规则），引擎只有 1 套 |
| appGuid 前置 | `components/udc/setting/application_guid.py` | 设置域 **9 个子域**全部依赖，且 appGuid≠appId |
| GraphQL 调用器 | `components/platform_operations/graphql_call.py` | `graphqlLoader` 样板在仓内**手写 25 处** |

### 为什么 GraphQL 调用器必须抽（三个已踩的坑）

```
① 响应是双层的：code 在 data.data0.code，不在顶层
   看顶层 → 字段其实成功了却判失败（一轮把 14 个存在的 op 全判成"未定"）
② str(None) == "None" 恒真
   拿 str(message) 判真假 → 把"什么都没返回"当"有返回"
③ 空 body 回 BOOT_0000 不代表成功
   delete 缺 id 时平台仍回 BOOT_0000 但 content=0
```

⇒ 公用器只做**结构归一化**（`GraphqlResult.ok` = 平台层成功），
**不做业务成功判定**。业务成功一律由调用方回读 DB / 看页面。

### 通道必须分两类（同一轮踩过）

```
GraphQL   enum / option_set / custom_object / parameter / serial /
          entity / flow / application / scalability
REST      attribute-set / qrcode-rule / excel（导入导出模板）
```

用 GraphQL 探 REST 域必然 `FieldUndefined` —— 那是**假阴性**，不代表不存在。

## 四、跨域 import 耦合现状（components 内）

```
gateway               → platform_operations   3
construction          → udc                   2
application           → udc                   1
udc-root              → udc                   1
```

耦合很轻，没有形成环。**保持这个状态**：跨域只允许「域 → platform_operations / udc 公用层」单向依赖，
不允许域与域互相 import。

## 五、下一步的优先级建议

```
P1  规则域建契约     0 → N   （规则是生成应用的必要环节，现在完全没有）
P2  栏目域建契约     0 → N
P3  菜单域写面       0 写面 → 至少 建/改/删
P4  entity UNKNOWN 9 条收口
P5  9 个域的事实件补 INDEX 登记（见 INDEX 里「未逐条登记」那一行）
```

不建议做的事：把 search/list/create/update/get 抽成"通用 CRUD"。
