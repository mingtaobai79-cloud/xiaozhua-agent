# 应用域契约层（`docs/operation-contracts/udc/application/`）

> **UTD 契约层的应用域**：7 份 / 121,177 B / 1,395 行。
> 与**事实层** `core/facts/udc/application/`（7 份 md + 17 份证据 JSON）是两件事：
> 事实层记「它实际怎么动」，本层记「它允许怎么被调」。两边会提到同一个 op_id，但**没有一份是另一份的摘要**。
> 上级入口：`docs/operation-contracts/udc/README.md`（14 子域总表）。

**本目录此前零入口**（上级总表里 `application/` 那一行标 ❌）。这是它的域入口。

---

## 〇★、先读这一节：8 处更正，且**最贵那条把「安全实现」记成了「数据质量风险」**

7 份契约里 **1 份**（`udc-app-online-contract.md`，784 行）带 **8 处**更正标记，全部集中在这一份。
其余 6 份零更正 —— 但它们读起来同样顺，所以**不能靠"有没有更正标记"判断可信度**，这份大契约的 8 处就是例子。

### 更正表（按"会不会让人写错代码 / 判错风险"排序）

| # | 原判断（已推翻 / 已撤） | 更正为 | 代价 | 原文 |
|---|---|---|---|---|
| ① | `ImportDelegateColi.saveAs` 的 try/catch **「吞异常、静默降级、数据质量风险」** | **不是**：`log.error` **紧接着** `BootException.throwIt`（`BOOT_3000`），且标 `@Transactional(rollbackFor={Exception.class})`、调用方 `SchemaManager.saveAs` **无 try/catch** ⇒ **异常重抛并触发回滚** | **最贵**：把一个安全实现记成风险，后续会去"修"一个不需要修的地方，而真正的静默失败点反而放过 | `udc-app-online-contract` L615–620 |
| ② | `saveAsNewDesign` **「照样撞 L491 配额门」**（推的是"会被拦"） | **撞门 ≠ 被拦**。计数条件与入口 `sourceType` 无关，但**门体进入条件**是 `if (isNull(dto) \|\| NORMAL == dto.sourceType)` —— FORM 时检查体**整块跳过** | 把「调用」当「生效」，会得出"FORM 应用建不了"的错结论 | L339–350 |
| ③ | 受门面 = **「3 处直接调用」** | **4 入口 + 1 汇聚点**（`copyCreate` L491）；错因是**只做符号 grep**（搜方法名），**漏掉全程不出现方法名的纯间接路径**（`saveAsNewDesign` → schema 另存链 → `copyCreate`） | 与 `column-discovery` 同一个病（方法论 60）：**搜不到 ≠ 不存在**。写配额/门禁这类"能不能绕"的结论时，符号 grep 不足以证否 | L271–281 |
| ④ | 可用源应用 **9 个** | **7 个**。9 = "有 RELEASE 记录"口径；7 = "能过 L1545"口径（额外要求 `udc_app_version.state=SUCCESS`） | 口径差：**两个数都要连口径一起引**，否则同一件事两个数字互相打脸 | L595–608 |
| ⑤ | 「草稿面 `app-draft/create` 是**建应用 LIVE PASS 的主线绕行**」 | **推翻**：`app_data_draft` **0 行**、`dataId` 是 **varchar** 而 `DeployNormalDto.appId` 是 **Long**、控制器**无** publish/online/deploy 方法 ⇒ **结构上不存在**这条链 | 会把一条不存在的路当成待接通的缺口，反复投入 | L629–644 |
| ⑥ | 「转正端点**仍未定位**」 | **过宽表述**：正确说法是「`getPush`/`appOnline` 面**没有** dataId→appId 转换路径」；要解释这句的因果，不能外推成"全平台没有" | 「未定位」暗示"再找找就有"，会让人继续找一段不存在的东西 | L643–644 |
| ⑦ | `checkAssignOrgIdAndCreator` 的入参结论 | **时序敏感**：L417 调用时 `sourceType` 仍是**入参原值**，默认化 (L430) **晚于** L417 ⇒ **两种入参结论不同**。（本侧先写错，已按 main 纠正，留痕） | 读方法不看调用顺序，会得出适用范围相反的结论 | L559–568 |
| ⑧ | 出路 **3 条**（A 释放配额 / B 提 createAppNum / C 承认不可达） | **4 条**：B 因上限未决改为"确认生效上限是 10 还是 11"，新增 **D 直接授权 target 运行态**（不经配额门、不新建应用） | 少一条出路 = 一个本来有解的局面被记成僵局 | L654–658 |

### 三条贯穿性错因

| 错因 | 实例 | 判据 |
|---|---|---|
| **搜不到 ≠ 不存在** | ③ | 符号 grep 只能证"这个名字不在"，不能证"这条路径不通"。**纯间接路径全程不出现方法名** |
| **「调用」当「生效」** | ② | 看到方法被调用就以为约束生效；实际要读**门体内部条件**。同族错误：`state` 当草稿态（`microflow` 目录 §〇 ①） |
| **口径不随数字走** | ④ | 9 和 7 都是真的，**换口径就换数**。文档里出现两个数，必须逐个标口径，否则后人必混 |

### 一条反向教训：**"我判错"要留痕**

③ 的更正记录写着「本契约 2a46143 的『受门仍是 3 处』结论也错」，并且把**错因**（只做符号 grep）写进了正文。
⇒ **不要把这些"我判错"整理成一句"已更正"。** 写"已更正"等于删掉了"下次要用什么手段查"，而这正是下一个人最需要的。

---

## 一、七份一览（按字节降序）

| 文件 | 字节 | 行 | 证据等级 | 一句话 |
|---|---:|---:|---|---|
| `udc-app-online-contract.md` | 64,904 | 784 | STATIC + **NEEDS_HUMAN** | **发布（上线）动作**的完整链路：两形态、入参、门链、pushEnv 判定。**全篇 0 次 LIVE 调用** |
| `udc-app-basic-readonly-contracts.md` | 12,899 | 102 | VERIFIED_STATIC_BYTECODE | 基本信息域只读端点的 `javap` 取证（30 个 controller 类扫出 5 个候选） |
| `udc-app-inner-readonly-2026-10-22.md` | 12,069 | 198 | **LIVE_PASS** | 应用内功能页 + 底部四类日志 tab 的实测结果总表 |
| `udc-app-deploy-info-live-contract.md` | 9,157 | 94 | STATIC + **BLOCKED** | 补 `udc.application.deploy_info` 的路由判定 + LIVE 回读 + `Long` 形态三项缺口 |
| `udc-app-readonly-live-2026-10-22.md` | 9,096 | 120 | **LIVE_PASS** / CALLED_NO_DATA / BLOCKED | 9 条只读探针 → 8 PASS / 1 BLOCKED（服务缺席） |
| `registry-entries.md` | 7,946 | 34 | VERIFIED_STATIC_BYTECODE | 5 条只读契约的 `UdcOperationContract` 字面量。**见 §二，它已经落库了** |
| `app-inner-contracts.md` | 5,106 | 63 | OBSERVED | **索引件**：应用内功能页 / 依赖设置 / 沙箱构建的 registry 键名总表 |

合计 **121,117 B / 1,395 行**（含本 README 时不适用——上表只算 7 份契约）。

---

## 二、`registry-entries.md` 自称"冻结期内，不改 registry.py"——**已经改完了**

那份文件第 2 行写着：

> 本文件供 UDC-MERGE 任务照抄进 `components/platform_operations/registry.py`；
> 本任务不改 registry.py（冻结）。

**这是 2026-10 中旬的事实，现在是假话。** 实测（2026-11-07）：

| | 数 |
|---|---:|
| 该文件列出的 `contracts[...]` 条数 | 5 |
| 其中已在 `registry.py` 里 | **5 / 5** |

`udc.application.deploy_info` / `draft.exist` / `draft.select` / `search.no_page` / `search.page` —— 全部在。

⇒ **别把它当待办去"照抄"。** 方法论同 `docs/operation-contracts/udc/README.md` §二那条：
「供 X 照抄」类措辞会随时间变成谎言，看到必须去消费方实测。

---

## 三、本目录最容易骗人的三处

### ① `udc.deployment.*` 这个命名空间在 `registry.py` 里**不存在**

`udc-app-online-contract.md` 的两个 op 写成 `udc.deployment.app_online` / `udc.deployment.app_online_new`。
全文搜 `registry.py`：**零命中**（`app_online` 三个字都没有）。`registry.py` 里只有
`udc.deploy.normal` / `udc.deploy.deploy_normal` / `udc.deploy.search_status`。

**这不是遗漏，也不是有人忘了落库。** 那份契约自己是这么写的：本 op 在 test2 **当前无可用 appId 来源**——
既有应用走 `/service/{appName}/` 撞 `server_403`（授权门）、新建应用撞 `UDC_APP_0030` 配额门（上限 10-or-11 未决）、
草稿转正**结构上不存在**（`AppDraftDto.dataId` 是 varchar，`DeployNormalDto.appId` 是 Long，喂不进去）。

⇒ 一条**已知进不去**的写面，入 registry 只会让人以为它可调。**docs 有、registry 无，是这里的正确状态。**
但你必须知道这一点，否则会把它当"漂移"去"修"。

### ② `udc.sandbox.flexible.test_status` 在 registry 里**掉了 `udc.` 前缀**

`udc-app-readonly-live-2026-10-22.md` 写 `udc.sandbox.flexible.test_status`；
`registry.py` L735 注册的是 `sandbox.flexible.test_status`（无前缀）。
**同一条端点两个 key**。按名字 grep 会得出"未落库"，按路径 grep 才能对上。

（这也是全仓唯一一处不带 `udc.` 前缀的应用域键——`registry.py` 128 条里 `udc.` 前缀 109 条。）

### ③ 四份 LIVE_PASS 的口径各不相同

`udc-app-readonly-live-2026-10-22.md` 写明判定要三件事同时成立才算 PASS：
**HTTP 200 且 信封 `code=BOOT_0000` 且 `data.content` 有形状**（GraphQL 还要下钻 alias 层）。
不满足的降级成 `CALLED_NO_DATA`；`BOOT_1006` 记 `AUTH_REDIRECT`（**不算通过**）。

**只看 HTTP 200 会把 3 类不同的事混成一类"成功"。** 每个文件的表里"判定"列必须逐条读，
不要跨文件假设同一套标准。

---

## 四、证据单元：两个版本**禁止混写**

这些契约横跨两个互不相通的证据单元，文件头都单独声明了：

| 单元 | 版本 | 来源 | 出现于 |
|---|---|---|---|
| 本地 Maven | **5.3.517** | `config/environments.yaml#environments.local-maven` 组装的 jar | 4 份（static 取证） |
| test2 镜像 | **5.3.496** | LIVE 环境 | 2 份（LIVE 实测） |
| lowcode-test 命名空间 | 5.3.358 | 部署态构件清单 | 1 份（`udc-app-online-contract.md` §10 单独声明**不是 test2**） |

`udc-app-deploy-info-live-contract.md` 原文：

> 环境口径：LIVE 侧 test2 镜像 **5.3.496**（jar 内同族类逐字核对）；与既有契约的 5.3.517 本地 Maven 单元**两单元禁混写**。

⇒ **同一份文件里出现两个版本号时，先确认它有没有声明禁止混写**；没声明的，不能拿 517 的字节码结论去断言 496 的运行行为。

---

## 五、拿不到什么（别指望本目录回答）

- **`app_online` 能不能跑通** —— 不能。NEEDS_HUMAN 未解（配额门 / 授权门 / 上限 10-or-11），4 条出路全需人工拍板。
  文件里明写「agent 不自行选、不自行删应用、不改环境配置」。
- **客户环境的真实 appId** —— 示例应用本身用的是保留段代号（`9000000000000000001`）。
- **写面契约** —— 本目录**只读为主**。唯一的写面（`app_online`）是上面那条进不去的。
  `registry-entries.md` 的 5 条全部 `write=False`。
- **跨域调用链** —— 那是事实层 `core/facts/udc/application/app-inner/app-inner-write-chain.md` 的事。

---

## 六、与事实层怎么分工

| 想知道 | 去 |
|---|---|
| 这个 op_id 允不允许被调、入参长什么样、什么证据等级 | **本层** |
| 它实际怎么被调、前端在哪发、写链经过哪几张表 | `core/facts/udc/application/` |
| 应用域整体在事实层的定位 | `core/facts/udc/application/README.md` |
| 本层在 14 个子域里的位置 | `docs/operation-contracts/udc/README.md` |

**两层会提到同一个 op_id，这是正常的**——不是重复写，是"允许"与"实际"两件事。
`core/facts/udc/application/README.md` 已就此声明过口径，本文件不重抄。
