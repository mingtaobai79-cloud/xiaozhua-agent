# publish 域契约层（`docs/operation-contracts/udc/publish/`）

> **UTD 契约层的 publish 域**：2 份 / 23,427 B / 180 行。
> 上级入口：`docs/operation-contracts/udc/README.md`（14 子域总表）。
> **本目录此前零入口**（上级总表里 `publish/` 那一行标 ❌）。这是它的域入口。

---

## 一、这是**唯一一个「0 条新增建议」的域**

`registry-entries.md` 第一行结论就是：

> 结论：**0 条新增建议**（非真空域，但候选已被既有条目覆盖）

理由：publish 域在这个 jar 里只有 **1 条只读候选**
（`UdcBaseAppInfoController.getDeployInfo`，见 `udc-publish-readonly-contracts.md` C1），
而 C1 **已经被登记过了**。

⇒ 所以本目录**不含任何待落库条目**。这和 `runtime/`（13 条全待落）正好相反。
⇒ 全库 14 个子域里只有本域是"零新增"。

---

## 二、⚠️ 但「登记两次」这句话已经过期了 —— 实测是**三次**

`registry-entries.md` 原文：

> 该候选在 `registry.py` 中**已被登记两次**：
> - `udc.application.deploy_info`（**L90**，application 域侧登记）
> - `udc.appinfo.get_deploy_info`（**L110**，entity/appinfo 域侧登记）

**实测（2026-11-07）是三条**：

| op_id | path | 行号 |
|---|---|---|
| `udc.application.deploy_info` | `{currentAppName}/app-info/deploy-info` | L90 |
| `udc.appinfo.get_deploy_info` | `deploy-info` | L110 |
| **`udc.publish.deploy_info`** | `deploy-info` | **L162** ← 文档没提到 |

⇒ **三个 op_id 指向同一个端点。** 而且三条的 `path` **两种拼法**：
一条带 `{currentAppName}/app-info/` 前缀，两条只写 `deploy-info`。
⇒ 看路径"哪个是真的"要回契约取证，**本目录没有 p 段（项目根路径）的结论**。

---

## 三、三条的 `class` 其实**一致**，同一个 controller 登记了三次

上一节说"已登记两次"，实际是**三次**，而且这三条的 evidence 都指向**同一个类**：

| op_id | path | evidence `class` | `class_sha256` |
|---|---|---|---|
| `udc.application.deploy_info` | `{currentAppName}/app-info/deploy-info` | `UdcBaseAppInfoController` | `deebcc39…` |
| `udc.appinfo.get_deploy_info` | `deploy-info` | `UdcBaseAppInfoController` | `deebcc39…` |
| `udc.publish.deploy_info` | `deploy-info` | `UdcBaseAppInfoController` | `deebcc39…` |

**与本域文档给出的 C1 真实出处完全一致**（`UdcBaseAppInfoController.getDeployInfo`，
`class_sha256 = deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95`）。

⇒ 所以证据是**对的**。问题只剩一件事：**同一个端点、同一个 class、同一个 sha，被登记成了 3 个 op_id。**
⇒ 全库重复注册里这一处最严重（3 份而不是 2 份），而且**路径还写了两种拼法**
（一条带 `{currentAppName}/app-info/` 前缀，两条只写 `deploy-info`）。
⇒ **哪种拼法是对的，本目录没有结论**，需回契约取证或 LIVE。

### 一个容易踩的核查陷阱（本轮踩了）

我第一次抽 `class_sha256` 时用「从 `contracts["x"]` 往后 1400 字符取第一个 `class_sha256`」，
结果取到的是**前一条契约**的 evidence（因为 `xxx_evidence = {...}` 定义写在
`contracts["x"] = ...` **之前**，而前一条契约的行里还留着上一个 evidence 的尾巴）。
得出了"三条 sha 互不相同、都填错了"的**错误结论**，已收回。

⇒ **正确做法：先建 `变量名 → class` 表，再从契约行里取 `[xxx_EVIDENCE]` 那个变量名去查。**
⇒ 修正后实测：**54 个 evidence 变量 / 55 条可判契约 / class↔sha 严格一一对应（0 冲突）**。
⇒ 判据：**「从某个位置往后找第一个匹配」在文档结构里几乎总是错的** ——
   定义常常写在使用之前。

## 四、两份一览（按字节降序）

| 文件 | 字节 | 行 | 性质 | 一句话 |
|---|---:|---:|---|---|
| `udc-publish-readonly-contracts.md` | 14,217 | 106 | **只读取证**（C1 + 写形态排除） | 三层扫描 + 131 端点行逐条判定 + 51 类 `javap` 落盘 |
| `registry-entries.md` | 9,210 | 74 | 落库核对（**0 条新增**） | 去重实测 + 与既有条目比对 |

合计 **23,427 B / 180 行**（含本 README 时不适用——上表只算 2 份）。

---

## 五、它抄的是 BI 域的方法论

`udc-publish-readonly-contracts.md` 头注原文：

> 方法论照抄 `docs/operation-contracts/udc/bi/bi-vacuum-contract.md`
> （三层扫描法 + 双口径一致性 + 伪命中族排除）

⇒ **这是本系列第一个明确写"方法论照抄某处"的域。** 之后 `resource/` 又照抄了它。
⇒ 说明 BI 域那份真空契约是**方法论源头**，不是"又一个域"。
⇒ 想学怎么扫一个域，读 `bi/bi-vacuum-contract.md` → 再看本域怎么用。

证据等级同样分开标：
- **VERIFIED_STATIC_BYTECODE** = 三层扫描计数 + 131 端点行逐条判定 + 51 类 `javap -p -v` 落盘
- **OBSERVATION** = 域归属语义判读 / 构件边界说明 / Live 面旁证，**均不升级**

---

## 六、证据单元与 jar

`udc-starter-runtime-5.3.517.jar`
（`sha256 = 74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`，**861,880 B**）
—— 与 `menu/`、`runtime/`、`resource/` 同一个 jar。

证据件相对 `docs/audit/artifacts/udc-publish-5.3.517/` 解析（本目录文件头写明）。

---

## 七、拿不到什么

- **`deploy-info` 的真实出处** —— 文档说 `UdcBaseAppInfoController`，但 registry 三条都挂了别的 class。**以文档为准还是以 registry 为准，未裁决。**
- **那条路径的完整拼法** —— 两条写 `deploy-info`，一条写 `{currentAppName}/app-info/deploy-info`。
- **写形态 1 条的契约** —— 明确排除（只读口径），未构造。
- **LIVE** —— 本域 `VERIFIED_STATIC_BYTECODE`，0 次 LIVE。

---

## 八、与事实层怎么分工

| 想知道 | 去 |
|---|---|
| publish 域有哪些端点、怎么扫出来的 | **本层**（`udc-publish-readonly-contracts.md`） |
| 为什么 0 条新增 | **本层**（`registry-entries.md`） |
| 三层扫描法怎么做 | `docs/operation-contracts/udc/bi/bi-vacuum-contract.md`（**源头**） |
| 发布/部署在运行态怎么跑 | `core/facts/udc/` + `docs/operation-contracts/udc/application/` |
| 本层在 14 个子域里的位置 | `docs/operation-contracts/udc/README.md` |
