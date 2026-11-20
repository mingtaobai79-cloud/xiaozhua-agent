# 平台开发知识体系：重做方案与目录设计

> 起因：用户问「其他的应用就那么少吗，我不是列了 202 多个 jar，基础工具类我怎么看不出来，
> 泛化等我怎么都看不到」。核查后确认 —— **不是平台内容少，是我的产物偏了**。
> 本文是重做方案，先给用户审目录，审过再动手。

---

## 一、核查结果：三个问题的真实答案

### 问题 1：202 多个 jar，为什么产物里看不到

| 项 | 实测数字 |
|---|---|
| 在盘 jar（cplib） | **221 个** |
| 去重后模块数 | **216 个** |
| 索引 `interfaces.json` 实际扫的 | **91 个** |
| **未索引** | **125 个模块** |

**差在哪里：**

```
已索引的 91 个 = facade 接口层 + boot-starter 组件
未索引的 125 个 = 几乎所有 -biz / -web 实现层
```

未索引清单（真实）：

```
ai-biz ai-core ai-web
app-approval-biz app-approval-web app-common-biz app-common-web app-doc-biz app-doc-web
bpm-biz bpm-web bpm-org bpm-org-facade bpm-ext-models
cdp-common cdp-data-biz cdp-data-web cdp-schedule-biz cdp-schedule-web
cip-capability-biz cip-capability-web cip-connector-biz cip-connector-web
cip-convert-biz cip-convert-web cip-manager-biz cip-manager-web
cip-openapi-gateway-biz cip-openapi-gateway-web
ctp-affair-biz ctp-affair-web ctp-media-biz ctp-media-facade ctp-media-web
ctp-message-biz ctp-message-web ctp-user-api ctp-user-biz ctp-user-web
ctp-webapi-gateway-biz ctp-webapi-gateway-web
m5-biz m5-web
organization-biz organization-web
portal-biz portal-web
udc-affair udc-app-common udc-bpm udc-cdpbi udc-cip udc-dataflow udc-m5 udc-portal
udc-starter-autocode udc-test udc-upgrade udc-user
boot-starter-basicdata / captcha / communication / documentnumber / dynamiccode
boot-starter-k8s / k8s-adapter / queue / sandbox / test / upgrade
```

**根因：`pkgs_clean.txt` 只有 91 行，是我上一轮为了「跑通索引脚本」而裁剪的清单，
不是完整 classpath。然后我把这份裁剪品当成了「平台全貌」。**

**影响：**
- `com.seeyon.ai.*` → 索引里 **0 个类**
- `com.seeyon.portal.*` → **49 个**（实际 portal-facade 远不止）
- `com.seeyon.m5.*` → **55 个**
- 125 个模块的实现层、DTO 具体字段、业务编排 → **全部没有**

---

### 问题 2：基础工具类为什么看不出来

**这是最严重的一处。**

| 项 | 数字 |
|---|---|
| `com.seeyon.boot.util` 下真实类数 | **176 个** |
| `boot-core-utils-and-annotations.md` 大小 | 8,994 B |
| 该格里实际列举的条目 | **4 行表格** |

**我把 176 个工具类，写成了 4 行「举例」。**

而 `capability-map` §4.1 明明写着「★★ `com.seeyon.boot.util` 的 177 个工具类（用户点名的「工具类」层）」——
**研究底稿里点出来了，落地产物里丢了。**

**这正是你说的「我怎么看不出来」。**

---

### 问题 3：泛化调用为什么看不到

| 项 | 现状 |
|---|---|
| `dubbo-cross-service.md` | 8,182 B |
| 这份文件讲的是什么 | Dubbo 跨服务调用的**概念** |
| 缺什么 | **泛化调用（GenericService）的完整参数怎么填** |
| 关键事实 | 泛化调用有 5 个必填位：`interfaceName` / `methodName` / `paramType` / `genericType` / `paramJson` |
| 现状 | 只在 `api-usage-cards.md` 里出现过一句「五个值怎么填」，**没有单独可用的格** |

**→ 用 Ai 写代码时，只知道「要用泛化」，不知道五个参数具体怎么拼。等于没有。**

---

## 二、为什么产物会偏（我的反思）

三处偏差有同一个根因：

```
研究底稿（core/research/ 60 篇）   ← 内容都在
        ↓ 我凭印象挑着写
落地产物（core/facts/ 215 格）     ← 只沉淀了"我记得重要的"
```

**具体表现为三种丢失：**

| 类型 | 例子 |
|---|---|
| **数量丢失** | 176 个工具类 → 4 行；216 个模块 → 91 个 |
| **层级丢失** | 只写了接口层（facade），没写实现层（biz/web） |
| **机制丢失** | 写了「有泛化调用」，没写「五个参数怎么填」 |

**我上一轮还在跟你说「充分覆盖 3/33 = 9%」——那个 33 本身也是我裁剪过的口径，
真实模块数是 216。用我的口径算覆盖率，等于自欺。**

---

## 三、新目录设计（请审这一节）

### 3.1 设计原则

```
① 一个 jar 一个格（216 格），不合并、不省略
   → 任何模块都能"从名字找到格"，不用先猜归到哪个大类

② 三层分离（每层都独立成格，不互相吞并）
   A. 契约层：facade 接口的方法签名 + DTO 字段
   B. 实现层：biz/web 的业务编排与真实落库
   C. 使用层：怎么调（注入 / 泛化 / 工具类），一页可抄

③ 数量必须与源一致
   → 176 个工具类就是 176 行，216 个模块就是 216 行
   → 每格标"源里有 N 个，本格收录 N 个"，差一个就是错
```

### 3.2 目录树

```
core/facts/
│
├── INDEX.md                          ← 总入口（216 模块清单，一行一个）
│
├── platform-dev-system/              ← 【保留】自定义微流程开发六格（已完成，不动）
│   ├── 01-custom-microflow-implement.md
│   ├── 02-udc-generated-reference.md
│   ├── 03-io-params-and-custom-object.md
│   ├── 04-generated-service-methods.md
│   ├── 05-calling-platform-capabilities.md
│   ├── 06-beforeupdate-listener-code.md
│   └── README.md
│
├── modules/                          ← 【新建】216 个 jar，一格一模块
│   ├── README.md                     ← 216 行清单表（模块 / jar数 / 类数 / 版本 / 格路径 / 状态）
│   │
│   ├── 01-core/                      ← 平台内核（必须先做，工具类在这）
│   │   ├── README.md                 ← 索引
│   │   ├── boot-core.md              ← 512 类，含 com.seeyon.boot.util 176 个工具类 ★★★
│   │   ├── boot-spi.md
│   │   └── boot-formula-engine.md
│   │
│   ├── 02-starter/                   ← 69 个 boot-starter 组件
│   │   ├── README.md                 ← 69 行清单 + 状态矩阵
│   │   ├── appservice.md
│   │   ├── artifact.md
│   │   ├── attachment.md
│   │   ├── basicdata.md
│   │   ├── cache.md                  ← ★ 高频
│   │   ├── captcha.md
│   │   ├── communication.md
│   │   ├── condition.md
│   │   ├── datainit.md
│   │   ├── datamigration.md
│   │   ├── datasource.md
│   │   ├── datatype.md
│   │   ├── documentnumber.md
│   │   ├── dubbo.md                  ← ★ 泛化调用在这层
│   │   ├── dynamiccode.md
│   │   ├── dynamicloader.md
│   │   ├── dynamicsql.md
│   │   ├── elasticsearch.md
│   │   ├── enums.md
│   │   ├── environment.md
│   │   ├── eventbus.md               ← 06 格依赖它
│   │   ├── excel.md
│   │   ├── extmetadata.md
│   │   ├── file.md                   ← ★ 高频
│   │   ├── filterchain.md
│   │   ├── formconvert.md
│   │   ├── formula.md                ← 用户说优先级低
│   │   ├── frontend-log.md
│   │   ├── ganttchart.md
│   │   ├── graphql.md
│   │   ├── i18n.md
│   │   ├── index.md
│   │   ├── k8s.md
│   │   ├── k8s-adapter.md
│   │   ├── labelprint.md
│   │   ├── license.md
│   │   ├── lock.md
│   │   ├── metadata.md
│   │   ├── mgn-export.md
│   │   ├── module.md
│   │   ├── monitor.md
│   │   ├── mq.md
│   │   ├── mybatis.md
│   │   ├── nacos.md
│   │   ├── opinion.md
│   │   ├── parameter.md
│   │   ├── prometheus.md
│   │   ├── proxy.md
│   │   ├── qrcode.md
│   │   ├── queue.md
│   │   ├── sandbox.md
│   │   ├── scanner.md
│   │   ├── schedule.md
│   │   ├── security.md               ← ★ 高频
│   │   ├── sensitive.md
│   │   ├── serialnumber.md
│   │   ├── sharding.md
│   │   └── ...（其余 boot-starter-* 逐个补齐，不合并）
│   │
│   ├── 03-business-app/              ← 标品业务应用（facade + biz + web 三层）
│   │   ├── README.md                 ← 应用 × 三层 的矩阵表
│   │   ├── organization/             ← ★ 用户点名
│   │   │   ├── README.md
│   │   │   ├── facade.md             ← 414 类，45 个 AppService
│   │   │   ├── biz.md                ← 实现层（当前完全空白）
│   │   │   └── web.md
│   │   ├── bpm/                      ← ★ 用户点名
│   │   │   ├── README.md
│   │   │   ├── facade.md             ← 533 类
│   │   │   ├── biz.md                ← 流程引擎实现
│   │   │   ├── org.md                ← bpm-org 选人匹配
│   │   │   └── web.md
│   │   ├── affair/
│   │   ├── message/
│   │   ├── user/
│   │   ├── media/
│   │   ├── portal/                   ← 当前 49 类，实际更多
│   │   ├── m5/
│   │   ├── app-common/               ← app-* 系列
│   │   ├── app-approval/
│   │   ├── app-doc/
│   │   ├── ai/                       ← ★ 当前 0 类，完全缺失
│   │   ├── cdp/                      ← 数据分析域
│   │   ├── cip/                      ← 连接器（1267 类已索引，但 biz/web 没有）
│   │   └── webapi-gateway/
│   │
│   ├── 04-udc/                       ← UDC 自身
│   │   ├── README.md
│   │   ├── udc-biz.md
│   │   ├── udc-common.md
│   │   ├── udc-facade.md
│   │   ├── udc-plugin-api.md
│   │   ├── udc-affair.md
│   │   ├── udc-app-common.md
│   │   ├── udc-bpm.md
│   │   ├── udc-cdpbi.md
│   │   ├── udc-cip.md
│   │   ├── udc-dataflow.md
│   │   ├── udc-m5.md
│   │   ├── udc-portal.md
│   │   ├── udc-user.md
│   │   ├── udc-extend.md
│   │   ├── udc-web.md
│   │   ├── udc-starter-*.md（6 个）
│   │   └── udc-{test,upgrade,cicd}.md
│   │
│   └── 05-tooling/                   ← 构建/插件
│       ├── boot-maven-plugins.md
│       ├── seeyon-maven-plugin.md
│       ├── seeyon-archetype-ext.md
│       └── ...
│
├── usage/                            ← 【新建】怎么调，一页可抄（与 modules 分离）
│   ├── README.md
│   ├── U1-injection.md               ← @Autowired / @DubboReference 选择判据
│   ├── U2-generic-call.md            ← ★★★ 泛化调用五参数完整填法（当前缺）
│   ├── U3-tools-index.md             ← ★★★ 176 个工具类全表（按功能分组，一行一个）
│   ├── U4-appservice-invoke.md       ← SingleRequest/Response 包装
│   └── U5-extension-points.md        ← SPI 扩展点注册与回调
│
├── standard-product/                 ← 【保留但瘦身】现有专题格（不删，作为深挖区）
├── udc/                              ← 【保留不动】155 格，已充分
├── bpm/                              ← 【保留不动】7 格
├── spi/                              ← 【保留不动】6 格
└── （connector / deploy / gateway / runtime / item-mgmt 保留）
```

### 3.3 关键设计决定（需要你拍板）

| # | 决定 | 我的建议 | 理由 |
|---|---|---|---|
| **1** | 216 个模块，是**一格一 jar** 还是**一格一应用**？ | **一格一 jar** | 你说「202 多个 jar」，一个不漏才能查。合并就会重演这次「176 写 4 行」 |
| **2** | `-biz` / `-web` 实现层要不要写？ | **要，但分级**：facade 全量方法签名；biz 只写「业务编排入口 + 落库表」；web 只写「REST 路由 + 请求体」 | 实现层类多（ai-biz 等），全量方法签名会爆炸。但完全不写就是现在这个空白状态 |
| **3** | 176 个工具类，全表列吗？ | **全表列，一行一个**：类名 / 用途 / 关键方法 / 用它的场景 | 这是你点名的，且只有 176 行，成本低收益高 |
| **4** | 泛化调用单独一格？ | **单独一格 `U2-generic-call.md`**：五参数 + 3 个真实可跑示例 | 现在散在各格，Agent 拼不出来 |
| **5** | 现有 `standard-product/` 32 格怎么办？ | **不删，降级为「深挖区」**：新 `modules/` 是检索入口，`standard-product/` 是细节补充 | 那 32 格里有些 LIVE 证据很贵（枚举写链、设置域），删了就丢 |
| **6** | 重建索引要多久？ | **重扫 216 个 jar 约 15-25 分钟**（上次 91 个约 8 分钟） | 一次性成本，之后所有核对都准 |

---

## 四、执行计划（三阶段，每阶段可验收）

### 阶段 1：重建正确的地基（必须先做）

| 步 | 动作 | 产物 | 验收标准 |
|---|---|---|---|
| 1.1 | 重扫 **216 个模块**全量建索引 | `interfaces-full.json` | 类数 > 25,000（当前 10,453）；`com.seeyon.ai.*` 非 0 |
| 1.2 | 生成 `modules/README.md` 216 行清单 | 模块 / jar 数 / 类数 / 版本 / 格路径 / 状态 | 216 行，每行可点 |
| 1.3 | 生成 `05-tooling/` + 核对 `boot-core.md` 的 176 类 | 176 行全表 | **176 行，与源类数逐个对齐** |
| 1.4 | 写 `U2-generic-call.md` | 泛化五参数 + 3 示例 | 能直接抄进代码 |

**阶段 1 完成标志：** 你说的三个盲区（模块数 / 工具类 / 泛化）全部消失。

### 阶段 2：按优先级补模块格

| 批 | 范围 | 格数 | 依据 |
|---|---|---:|---|
| 2.1 | `01-core/` + `02-starter/` 高频 8 个（cache/file/security/enums/metadata/excel/serialnumber/eventbus） | 12 | 几乎所有业务都要用 |
| 2.2 | `03-business-app/` 用户点名 3 个（organization / bpm / affair），三层各一格 | 12 | 你明确点过 |
| 2.3 | `03-business-app/` 剩余应用 facade 层 | ~30 | 先契约后用 |
| 2.4 | `02-starter/` 剩余 61 个 | 61 | 补齐 |
| 2.5 | `03-business-app/` 剩余 biz/web 层 | ~50 | 最后做 |

**每格固定九段式**（沿用现有规范）：Capability / Version / Input / Required / Execution / Output / Side Effects / Known Constraints / Evidence / Verified。

**每格必带数量声明：**
```
源里 N 个类 / M 个方法 → 本格收录 N 个类 / M 个方法
差一个就是错，必须在 §Verified 说明为什么差
```

### 阶段 3：补正确性声明

| 步 | 动作 |
|---|---|
| 3.1 | 跑脚本扫现有 215 格里的所有类名/方法名，逐个核对 `interfaces-full.json` |
| 3.2 | 不存在的一律标红，写入 README「已修正」表 |
| 3.3 | 无 `## Evidence` 段的 145 格，补上验证等级 |

---

## 五、这一轮我已经确认的错（不是推测）

| # | 我写的 | 真相 | 严重度 |
|---|---|---|---|
| 1 | 平台共 91 个构件 | **216 个模块**（221 jar） | ★★★ 地基错 |
| 2 | 33 个域里有 15 个缺失 | 真实缺口是 125 个**模块**，不是 15 个域 | ★★★ 口径错 |
| 3 | 工具类格 | 176 个类写成 **4 行** | ★★★ 数量丢失 |
| 4 | 泛化调用有格 | 只有概念，**五参数没落地** | ★★ 机制丢失 |
| 5 | `com.seeyon.ai.*` | 索引 0 类（**整个 AI 域不存在**） | ★★★ 整域缺失 |
| 6 | 覆盖率 9% | 用我裁剪的口径算的，**真实更低** | ★★ 自欺 |

---

## 六、需要你回答的三个问题

1. **216 个模块，一格一 jar 还是允许按应用合并？**（我建议不合并）
2. **`-biz` / `-web` 实现层，写到什么粒度？**（我建议：facade 全量签名，biz 只写业务编排入口+落库表，web 只写路由+请求体）
3. **阶段顺序认不认？** 我建议先做阶段 1（重建索引 + 216 清单 + 176 工具类 + 泛化格），
   因为**这三样不修，后面写的每一格都建在错地基上**。

---

## 七、我现在就能开始的（等你一句话）

```
1. 重扫 216 个 jar 建全量索引      （15-25 分钟，脚本已有，只改清单）
2. 生成 modules/README.md 216 行   （索引建完就能生成）
3. 写 U3-tools-index.md 176 行     （索引建完就能生成）
4. 写 U2-generic-call.md 泛化格    （读字节码 + 组示例）
```

**这四个不用你拍板就能做，且都是纯增量的。要不要我先跑？**