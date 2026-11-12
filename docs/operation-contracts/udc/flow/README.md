# 流程域（BPM 集成）契约层（`docs/operation-contracts/udc/flow/`）

> **UTD 契约层的流程域**：4 份 / 51,344 B / 570 行。
> 上级入口：`docs/operation-contracts/udc/README.md`（14 子域总表）。
> **本目录此前零入口**（上级总表里 `flow/` 那一行标 ❌）。这是它的域入口。
> 证据单元：本地 Maven **5.3.517** 六 jar，全离线，**禁相邻版本混写**。

---

## 一、`registry-entries.md` 的 12 条：8 条同名落库、1 条去重归一、3 条是写侧

| 状态 | 条数 | 明细 |
|---|---:|---|
| ✅ 同名落库 | **8** | `bpm_node_info_search` / `form_data_query` / `data_flow_map_get_by_id` / `data_flow_map_search` / `data_flow_mapping_get_by_id` / `data_flow_mapping_search_original` / `data_flow_mapping_init_data` / `data_flow_mapping_detail` |
| ↔ **去重归一** | **1** | `udc.flow.function_node_tree` → 实际为 **`udc.microflow.function_node_tree`**（同 controller + 同 method + 同 `class_sha256`） |
| ❌ 写侧未落库 | **3** | `bpm_fill_error_data` / `data_flow_mapping_update` / `data_flow_mapping_update_state`（均 `write=True`） |

### 那 1 条去重是**正确的**，而且它正好证明重复注册是 bug

`registry-entries.md` 自己写了：

> 第 2 条 `udc.flow.function_node_tree` 与微流程域 `udc.microflow.function_node_tree`
> **跨域重叠 → MERGE 去重归一（删一留一），勿新增重复 operation_id。**

MERGE **照做了**：`registry.py` 里只有 `udc.microflow.function_node_tree`
（GET `udc-runtime/meta-data/select-function-node-tree/{appName}`），**没有** `udc.flow.function_node_tree`。

⇒ **这是全库唯一一处"发现同路径重复、并且真的去重了"的记录。**
⇒ 它说明"同路径两个 op_id"在本仓库被判定为**要修的问题**——
所以第 41 轮查出的另 6 条（12 条契约）重复注册，**是遗漏，不是设计**。
⇒ 反过来说：**别照 `flow` 的做法再造重复**。`flow` 是正例，其余 6 处是反例。

---

## 二、⚠️ 「write=true 策略门控未放开」这句**在消费方不成立**

3 条写侧契约的 `verification_rules` 都写着：

> 「`write=true` 策略门控未放开」「仅登记，不进入只读契约计数」

**实测（2026-11-07）`registry.py` 里已有 25 条 `write=True` 条目**：
`udc.deploy.normal`、`udc.microflow.create` / `check_schema` / `update`、
`udc.enum.*`（4 条）、`udc.custom_object.*`（3 条）、`udc.option_set.*`（4 条）、
`udc.parameter.*`（2 条）、`udc.serial.create` / `delete`、
`setting.excel.template.create` / `qrcode.rule.create` / `attribute_set.*`（2 条）/ `scalability.*`（2 条）。

⇒ **门控早就放开了。** 这 3 条没进 registry **不是因为门控**，是因为没人再去落。
⇒ 这是"措辞会随时间变成谎言"的又一例（方法论第 9 条）。
⇒ **但也别急着补**：补进去会新增 3 条写契约，属策略决定，**已记入待裁决**（第 42 轮）。

---

## 三、`.effective` 门控表——本目录最实用的一张表

`registry-entries.md` §R5 给出的门控条件是
「`status ∈ {PASS, VERIFIED_STATIC_BYTECODE, OBSERVED}` 且 `write=False` 且 `method == "GET"`」：

| 类别 | `.effective` | 条数 | 条目 |
|---|---:|---:|---|
| GET 只读 | **True** | 3 | `function_node_tree` / `data_flow_map_get_by_id` / `data_flow_mapping_get_by_id` |
| **POST 读型（`write=False`）** | **False** | **6** | `bpm_node_info_search` / `form_data_query` / `data_flow_map_search` / `data_flow_mapping_search_original` / `data_flow_mapping_init_data` / `data_flow_mapping_detail` |
| 写型（`write=True`） | False | 3 | `bpm_fill_error_data` / `data_flow_mapping_update` / `data_flow_mapping_update_state` |

**那句话最关键**：

> POST 只读条目 `.effective=False`，MERGE 时须走与普通只读 POST 相同的 `auth_scope` 通道，
> **勿依赖 `.effective` 自动放行**。

⇒ **6 条"读"契约会被 `.effective` 判成 False。** 谁按 `.effective` 筛选只读能力，
**会漏掉这 6 条**，然后以为"流程域只有 3 条只读"。
⇒ 这是本目录最容易踩的坑，也是这张表唯一的价值。

---

## 四、负证据：40 个 controller 的穷尽枚举

`flow-domain-boundary-negative-evidence.md` §1 逐 jar 跑
`jar tf <jar> | grep -E 'controller/.*Controller\.class$' | grep -vE '\$' | sort`：

| jar | controller |
|---|---:|
| udc-common | 0 |
| udc-facade | 0 |
| udc-starter-customplan | 5 |
| udc-starter-dataflow | 5 |
| udc-starter-lowcode | 0 |
| udc-starter-runtime | 30 |
| **合计** | **40** |

40 类 = **6 个 BPM 集成域** + **34 个 non-flow**，§2 对每个 non-flow 类给一行归属理由
（customplan 管理面 / meta-data / deduction 引擎 / page / log / dtype / app / attachment / graphql / proxy …）。

**"0 遗漏"是怎么论证的**（负证据的写法范本）：
- 40 类**全枚举**，原始 `jar tf` 输出全文落 `controller-enumeration.txt`
- 6 域**已契约化核对**（不是"我看了觉得像"）
- `javap` 仅用于 main 复核，**未深挖任何 non-flow 方法体**（禁把推断写成 FACT）
- 证据等级 **OBSERVATION**，明确声明"结论基于全枚举 + 已契约化核对，**非推测**"

⇒ 这个域的负证据比大多数域严谨：**它区分了"枚举级证据"和"字节码级证据"**，
并且不把前者说成后者。抄这套写法，不要抄"我很确定没有"。

---

## 五、R7/R8 裁定：proxy 层为什么不算流程域

`registry-entries.md` 末尾【R7/R8 裁定·移交项 ④】：

> `UdcBaseGeneralController`（runtime/proxy，**无类级 `@RequestMapping` 前缀**）：
> 字节码扫描真命中 proxy 层 flow/microflow 透明路径 =
> `create-bpm` / `update-bpm`（写侧）+ `dataflow/{entityName}/{restMappingName}` /
> `.../dynamic/select` + `microflow/{microFlowName}` / `host/microflow/{microFlowName}`。
> 裁定**不扩流程域边界**，理由三条：microflow 属微流程域、create-bpm/update-bpm 为写侧非只读、
> 本任务非目标「不评价其他域」→ MERGE 时与微流程域合并裁定该 proxy controller，
> **勿入本域 6 controller 专属只读契约**；仅登记，不落地。

⇒ **这是一条"我看见了但决定不管、并说明为什么"的记录。**
⇒ 最危险的做法是把这个 proxy controller 的路径当"流程域漏了"去补 —— 会与微流程域撞车。

---

## 六、四份一览（按字节降序）

| 文件 | 字节 | 行 | 性质 | 一句话 |
|---|---:|---:|---|---|
| `registry-entries.md` | 16,327 | 236 | **落库条目 + 裁定**（主文档） | 12 条 + `.effective` 门控表 + R5 可构造性核验 + R7/R8 裁定 |
| `flow-domain-boundary-negative-evidence.md` | 13,854 | 129 | **负证据** | 40 controller 穷尽枚举 + 逐类域判定 |
| `flow-domain-scan.md` | 12,174 | 107 | P0 扫描定位 | 6 controller 逐方法映射（R2-C1..C9） |
| `flow-contracts.md` | 8,989 | 98 | 只读契约 7 要素 | 9 条只读 + 3 条写侧的字段级定义 |

合计 **51,344 B / 570 行**（含本 README 时不适用——上表只算 4 份）。

---

## 七、R5 可构造性核验（12/12 PASS）

`registry-entries.md` §R5 有一份**可复跑的核验**：
脚本 `docs/audit/artifacts/udc-flow-5.3.517/registry-construct-check.py`
（只 import `models.py` + 读本文件，**绝不写** `registry.py`/`layer.py`/`tests/` 冻结件），
stdout 落 `registry-construct-check.txt`。

> 构造结果：**12/12 块 construct=OK，总判定 PASS**。
> 块数核对：总 `UdcOperationContract(` 提及 **14** 处 = 代码块内 **12**（只读 9 + 写 3，可构造）
> + 正文/示意 **2**（签名示意 1 + 本句自身 1，非代码块，显式区分，不计入构造）；`python` 围栏 **10**。

⇒ 把"14 处提到 vs 12 条可构造"的差额**当场解释掉**，这是好核验的样子。
⇒ 别看到"14"就以为多写了 2 条。

---

## 八、拿不到什么

- **LIVE 回读** —— 本域证据等级最高只到 `VERIFIED_STATIC_BYTECODE`（`javap -p -v`），0 次 LIVE。
- **网关 service 前缀** —— 全部 "未拼网关前缀"。
- **non-flow 34 类的方法体** —— 明确"未深挖"，属其他域。
- **proxy 层流路径的归属** —— R7/R8 裁定"与微流程域合并裁定"，本域不落地。
- **那 3 条写侧的入库决定** —— 需人工授权（见 §二）。

---

## 九、与事实层怎么分工

| 想知道 | 去 |
|---|---|
| 12 条的入参/返回/`write`/evidence | **本层**（`registry-entries.md`） |
| 哪些东西 `.effective` 会是 True（会被自动放行） | **本层**（§R5 门控表，**别自己按 method 猜**） |
| 40 个 controller 里哪个属于流程域 | **本层**（负证据文件 §2） |
| BPM 写链在运行态怎么跑 | `core/facts/bpm/` + `core/facts/udc/write-chain/` |
| 微流程域的 `function_node_tree` | `docs/operation-contracts/udc/microflow/` |
| 本层在 14 个子域里的位置 | `docs/operation-contracts/udc/README.md` |

---

## 十、证据在哪

`docs/audit/artifacts/udc-flow-5.3.517/`：
`controller-enumeration.txt`（40 controller `jar tf` 原始输出 + 6 jar 路径/SHA-256）、
各 `*.javap.txt`（`DataFlowForBpmController` / `DataFlowRtMappingController` / `DataFlowRtMapController` /
`BpmNodeInfoController` / `UdcFunctionNodeController` 等）、
`registry-construct-check.py` + `registry-construct-check.txt`。
