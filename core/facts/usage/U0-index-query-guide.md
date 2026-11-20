# U0 · 索引怎么查：速度、边界、正确姿势（实测）

## Capability

**回答「这个索引有多快、能查到什么、查不到什么、怎么查才准」。**

给 Agent 用：**查询前必读**。本格是从 20 个真实需求实测出来的，不是估算。

## 一、速度（实测）

| 项 | 实测值 |
|---|---|
| 索引文件 | **139 MB**（`interfaces-full.json`） |
| 冷加载 `json.load` | **0.89–1.01 秒** |
| 单次类名查询 | **0.0–0.1 ms** |
| 单次方法名查询 | **0.0–0.1 ms** |
| 全库正则搜索（2.4 万类） | **15–59 ms** |
| 20 个需求连续查（含加载） | **0.91 秒** |
| **平均单查** | **0.9 ms** |

**结论：速度完全够用。加载一次后常驻内存，后续查询几乎零成本。**

## 二、覆盖（24,618 类 / 249,560 方法）

| 项 | 数 |
|---|---:|
| 构件 | 176 |
| 类 | 24,618 |
| 方法 | 249,560 |
| 方法名索引 | 86,141 |
| 重名类 | **787 组** |

## 三、★★★★★ 两个必须知道的边界

### 3.1 边界一：裸查类名会命中错误域（787 组重名）

实测，同一个短类名有多个全名：

```
JsonUtils      → 3 个
  ★ com.seeyon.boot.util.JsonUtils        ← 正确的
    com.seeyon.boot.license.JsonUtils
    com.seeyon.ai.core.common.JsonUtils    ← 裸查先命中这个（错）

FileUtils      → 3 个
  ★ com.seeyon.boot.util.FileUtils
    com.seeyon.udc.common.utils.FileUtils
    com.seeyon.cdp.schedule.schedule.utils.FileUtils

DateUtils      → 3 个
StringUtils    → 2 个
GenericService → 2 个
```

**⇒ 裸查会命中错的。必须用 `priority.json` 的权威排序，或带包前缀。**

权威度规则（`build_priority.py`）：

```
com.seeyon.boot.core / boot.util      最高（平台内核工具）
com.seeyon.boot.transport             次之（传输协议）
com.seeyon.boot.*                     再次
com.seeyon.{app}.api.*                标品契约
com.seeyon.udc.*                      UDC 自身
com.seeyon.ai.* / *.core.common.*     次级（各应用私有副本）
```

### 3.2 边界二：方法名跨域冲突很严重

实测命中质量：

| 查询 | 总命中 | 第一条是什么 | 要找真入口需翻 |
|---|---:|---|---:|
| `send()` | 49 | `HttpClientUtil#send`（HTTP） | **11 条**才到 bpm |
| `submit()` | 34 | `SeeyonExecutorService#submit`（线程池） | **7 条** |
| `create()` | 832 | `ICoMiPageInfoAppService#create` | — |
| `update()` | 714 | `ICoMiPageInfoService#update` | — |
| `selectById()` | 673 | `AiUserService#selectById` | — |

**⇒ 裸查方法名基本不可用。必须加 `--domain` 限定。**

```bash
# ❌ 裸查：命中 HttpClientUtil#send
python query_platform.py find-method send

# ✅ 限定域：第一条就是 BpmAppService#send
python query_platform.py find-method send --domain bpm
```

### 3.3 ★★★ 边界三：索引只收录 Java 字节码，不含这些

实测 3 个「查不到」的真实原因：

| 我查的 | 结果 | 真相 |
|---|---|---|
| `udcEnumPost` | **0 处** | 这是 **GraphQL operation 名**，不是 Java 方法 |
| `udcDataTransferObjectUpdateDtoPost` | **0 处** | 同上，GraphQL operation |
| `callDataFlow` | **0 处** | 这是**微流程 actionType**，不是方法名 |

**索引里有什么 / 没有什么：**

| 类型 | 有 | 查法 |
|---|---|---|
| Java 类 / 方法 / 字段 | ✅ | 本索引 |
| GraphQL operation 名（`udcEnumPost` 等） | ❌ | 去 `core/facts/udc/` 查 |
| 微流程 actionType（`CALL_DATA_FLOW` 等） | ❌ | 去 `core/facts/udc/microflow/` 查 |
| REST 路由（`/service/udc/...`） | ⚠️ 部分（Controller 方法有） | 按 Controller 类查 |
| 数据库表名 / 物理列 | ❌ | 去 `core/facts/udc/` 或直接查库 |

**⇒ 所以「查不到」不等于「平台没这个能力」。先分清你要查的是哪一层。**

## 四、正确查询姿势（三步）

```
第 1 步：确定你要查什么层
   Java 方法      → 本索引（query_platform.py）
   GraphQL 操作   → core/facts/udc/
   微流程节点     → core/facts/udc/microflow/
   REST 路由      → 按 Controller 类查本索引

第 2 步：查询必须带约束
   查类  → query_platform.py find-class JsonUtils（自动用 priority 排序）
   查方法 → query_platform.py find-method send --domain bpm
   查类的方法 → query_platform.py methods <全限定类名>

第 3 步：验证第一条是你要的
   → 看包路径是否在你预期的域
   → 不在就加 --domain 或换全限定名
```

## 五、工具用法

```bash
cd C:/Users/白明涛/xiaozhua-agent

# 1) 按短类名查（自动权威排序，解决 787 组重名）
python tools/core/platform/query_platform.py find-class JsonUtils

# 2) 按方法名查（★ 必须带 --domain）
python tools/core/platform/query_platform.py find-method send --domain bpm
python tools/core/platform/query_platform.py find-method createAffairByMicroflowReturnIds --domain ctp

# 3) 看一个类的全部方法签名（最有用）
python tools/core/platform/query_platform.py methods com.seeyon.bpm.api.common.BpmAppService

# 4) 正则搜类名（模糊找能力）
python tools/core/platform/query_platform.py search "库存|stock|subtract"

# 5) 看某个应用的类分布
python tools/core/platform/query_platform.py app organization
```

## 六、实测 20 个真实需求的结果

| # | 需求 | 耗时 | 结果 |
|---:|---|---:|---|
| 1 | 查组织的人 | 0.0ms | ✅ `OrgCommonAppService` |
| 2 | 发起流程 | 0.1ms | ✅ `BpmAppService#send` |
| 3 | 提交流程 | 0.0ms | ✅ `BpmAppService#submit` |
| 4 | JSON 转对象 | 0.0ms | ✅ `boot.util.JsonUtils`（priority 生效） |
| 5 | 生成 id | 0.0ms | ✅ `boot.util.id.Ids` |
| 6 | 对象拷贝 | 0.0ms | ✅ `boot.util.bean.BeanCopier` |
| 7 | 生成待办并拿id | 0.0ms | ✅ `AffairMicroflowAppService#...ReturnIds` |
| 8 | 查用户 | 0.0ms | ✅ `CtpUserCoreAppService` |
| 9 | 枚举项查询 | 0.0ms | ✅ `CtpEnumItemService` |
| 10 | 文件服务 | 0.0ms | ✅ `FileInfoService` |
| 11 | 写枚举 | 0.0ms | ❌ 查 `udcEnumPost`（GraphQL 名，不在索引） |
| 12 | 自定义对象字段 | 0.0ms | ❌ 同上 |
| 13 | 微流程触发 | 0.0ms | ✅ `triggerFlowForUdc` → dataflow |
| 14 | 数据流生单 | 0.0ms | ❌ 查 `callDataFlow`（actionType，不在索引） |
| 15 | 库存扣减 | 15.3ms | ✅ 2 个 `SubtractCaller` |
| 16 | 分页查询 | 0.1ms | ✅ `BaseDao#selectPageByConditions` |
| 17 | 更新前事件监听 | 0.0ms | ✅ `BeforeUpdateEvent` |
| 18 | 泛化调用入口 | 0.0ms | ✅ `AppServiceProxy` |
| 19 | 当前用户 | 0.0ms | ✅ `SystemVariableUtils` |
| 20 | AI 域能力 | 3.4ms | ✅ 237 个类 |

**命中 17/20 = 85%。3 个未命中全部是「查错层」（见 §3.3），不是索引缺陷。**

## 七、Known Constraints

| # | 约束 |
|---|---|
| 1 | **裸查类名命中错的（787 组重名）** —— 必须用 priority 或全限定名 |
| 2 | **裸查方法名基本不可用** —— `send` 命中 49 处，第 12 条才是 bpm |
| 3 | **索引只有 Java 字节码** —— GraphQL operation / actionType / 表名都没有 |
| 4 | **加载 1 秒 / 139MB** —— 一次性成本，进程内常驻即可 |
| 5 | **`find-class` 的推荐值来自 priority.json**，它按平台内核优先排序 |
| 6 | **正则搜索要 15–59ms**（扫 2.4 万类），比精确查慢但可接受 |

## 八、Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 139MB / 0.89-1.01s 加载 | `bench_query.py` 实测 | **LIVE** |
| 20 需求 0.91s / 平均 0.9ms | `bench_20.py` 实测 | **LIVE** |
| 787 组重名 | `build_priority.py` 统计 | **LIVE** |
| `send` 49 处、bpm 14 处、第 12 条 | `bench_accuracy.py` 实测 | **LIVE** |
| `JsonUtils` 3 个 / priority 命中 boot.util | 同上 | **LIVE** |
| `udcEnumPost` 0 处（GraphQL 非方法） | 索引查询 + 与 `core/facts/udc/setting/enum/` 对照 | **LIVE** |
| 17/20 命中率 | `bench_20.py` | **LIVE** |

## 九、Verified

- ✅ **LIVE**：以上全部速度与命中数字均为本机真实运行结果
- ✅ **可复算**：`bench_query.py` / `bench_20.py` / `bench_accuracy.py` 三个脚本可直接重跑
- ⚠️ **UNVERIFIED**：`subGenericType` 分隔符（见 U2）
- ⚠️ **UNVERIFIED**：泛化调用真实发起

## 十、给 Agent 的判据

```
问「查一个类要多久」
  → 加载 1s（一次性），之后每次 <1ms

问「JsonUtils 是哪个」
  → 裸查有 3 个，用 find-class 自动挑 com.seeyon.boot.util.JsonUtils
  → 千万别用 com.seeyon.ai.core.common.JsonUtils

问「怎么找流程的 send」
  → find-method send --domain bpm  → BpmAppService#send
  → 裸查 send 会先命中 HttpClientUtil#send（错）

问「我查 udcEnumPost 怎么没有」
  → 那是 GraphQL operation 名，不是 Java 方法
  → 去 core/facts/udc/setting/enum/

问「我查 CALL_DATA_FLOW 怎么没有」
  → 那是微流程 actionType
  → 去 core/facts/udc/microflow/

问「查不到是不是平台没这个能力」
  → 不一定。先确认你查的是哪一层（Java / GraphQL / actionType / REST / DB）

问「怎么快速看一个类有什么方法」
  → query_platform.py methods <全限定类名>
  → query_platform.py pkg <包名>  看一个包下有什么

问「查全量太慢 / 只想知道某一域」
  → 用分片：--scope bpm / --scope ctp__affair / --scope file
  → query_platform.py scopes 列出全部 395 个分片
```

## 十一、分片索引（解决「裸查不准」和「加载慢」）

**四种拆法，全部落盘并自证总数对齐：**

| 目录 | 文件数 | 合计类数 | 切分依据 | 加载实测 |
|---|---:|---:|---|---:|
| `by-domain/` | 16 | 24,618（= 源） | `com.seeyon.{X}` | 0.05–0.2s |
| `by-sub/` | 185 | 19,681（= 9 大域） | `com.seeyon.{X}.{Y}` | 0.02–0.15s |
| `by-starter/` | 79 | 3,678（= boot.starter 全部） | `com.seeyon.boot.starter.{Y}` | 0.01–0.05s |
| `by-app/` | 115 | 24,618（= 源） | 类的 `pkg` 落在应用构件里 | 0.05–0.3s |

**实测分片查询（本机）：**

```
send --scope bpm                 加载 0.11s → 14 处，第一条 BpmAppService#send  ✅
OrgCommonAppService --scope organization  加载 0.05s → 命中 1 个            ✅
JsonUtils --scope boot           加载 0.11s → 2 个，推荐 boot.util.JsonUtils ✅
```

**⇒ 分片把「必须带 --domain」的纪律变成了物理隔离：**
在 `by-sub/ctp__affair.json` 里查 `send`，不可能命中 HTTP 的 send。

**完整清单：`docs/audit/artifacts/index/TREE.md`**（每个文件一行，含类数/方法数/包数/大小）
**全部包：`docs/audit/artifacts/index/PACKAGES.md`**（5,048 行，包 → 类数 → 构件）

### 为什么不是每个域都切二级

`boot` 的二级结构就是 starter（`boot.starter.file` / `boot.starter.enums` / …），
`by-starter/` 已经切过了，再进 `by-sub/` 会产生两份同内容文件。

所以：
- 有二级业务的 9 个大域（cip/bpm/udc/cdp/ctp/app/organization/portal/m5）→ `by-sub/`
- boot（纯组件）→ `by-starter/`
- 其余小域（ai 237 / ocip 222 / devops 245 / m5 473 …）→ 只到 `by-domain/`，够用

### 构建脚本

`tools/core/platform/index_build/`（含 README 和两个真实坑的记录）

```bash
python tools/core/platform/index_build/build_priority.py
python tools/core/platform/index_build/split_all.py
python tools/core/platform/index_build/split_apps.py
python tools/core/platform/index_build/split_sub.py
python tools/core/platform/index_build/rebuild_tree.py
python tools/core/platform/index_build/verify_index.py   # 退出码必须 0
```

## 十二、我在这件事上犯的两个错（记录，防止重犯）

### 错 1：只挑 3 个域就说「按域拆分」

第一次回答时我只列了 `bpm / org / udc`，理由是我刚测的 20 个需求里出现最多的三个。
**这是拿测试样本当总体。** 24,618 个类里有 16 个顶级域、79 个 starter，
事项（481）/ 连接器（439）/ 用户中心（1,069）/ 文件（89）/ 枚举（51）/
元数据（102）/ 数据源（29）/ mybatis（138）全都没进方案。

**应该做的**：先枚举全部包路径 → 按类数排序 → 给出完整切分，再讨论优先级。

### 错 2：两次断言确实抓住了漏项

| 现象 | 原因 | 谁发现的 |
|---|---|---|
| 域合计 24,617 ≠ 24,618 | `com.seeyon.MyMojo` 是三段类名，前缀匹配漏掉 | `assert total_dom == len(cls)` |
| 115 个应用全部 0 类 | `sources` 无 `class_list`，我从它反推 | 目视 TREE 全是 0 |

**教训**：写「按前缀分组」的代码时，一定要单独验证「只有类名、没有子包」的项。
`sys.exit(1)` 的断言必须写，不然这两处都会静默通过。