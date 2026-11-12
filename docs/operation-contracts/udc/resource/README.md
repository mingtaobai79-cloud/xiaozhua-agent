# resource 域契约层（`docs/operation-contracts/udc/resource/`）

> **UTD 契约层的 resource 域**：2 份 / 29,145 B / 219 行。
> 上级入口：`docs/operation-contracts/udc/README.md`（14 子域总表）。
> **本目录此前零入口**（上级总表里 `resource/` 那一行标 ❌）。这是它的域入口。

---

## 一、5 条建议，**5/5 全部落库**，且证据一致

| op_id | method | path | evidence class |
|---|---|---|---|
| `udc.attachment.template_get_by_guid` | GET | `udc-runtime/attachment-template/{guid}` | `AttachmentTemplateController` |
| `udc.attachment.template_list_by_guids` | POST | `udc-runtime/attachment-template/select-by-guids` | 同上 |
| `udc.attachment.template_list_by_app_id` | GET | `udc-runtime/attachment-template/app/{appId}` | 同上 |
| `udc.jar.download` | GET | `udc-runtime/dynamic/jar/download` | `DynamicJarController` |
| `udc.jar.export_app` | GET | `udc-runtime/dynamic/jar/download/{appName}` | 同上 |

实测（2026-11-07）：5 条的 **op_id、method、path、evidence `class`** 与文档**全部一致**
（`AttachmentTemplateController` 3 条、`DynamicJarController` 2 条，`class_sha256` 各自吻合）。

⇒ 这是 14 个子域里**落库最干净的一个**：没有换名字、没有占位符、没有别名重复。
⇒ 对照 `runtime/`（13 条全待落）、`publish/`（0 条新增但 3 重注册）、`page/`（有占位符）——
**本域可以直接当"落库成功长什么样"的样板。**

---

## 二、写着「写形态 5 条**不得**入 registry」

`registry-entries.md` 原文：

> **写形态 5 条（`create` / `create-batch` / `delete` / `delete-by-guids` / `upload`）不得入 registry**
>（只读契约口径）。

⇒ 这是一个**明确的排除决定**，不是遗漏。5 条写形态在 `udc-resource-readonly-contracts.md` 里有记录，
但**不构造契约、不落库**。
⇒ 别看到"resource 域有 10 个端点却只有 5 条契约"就去补那 5 条 —— **那 5 条是被明确排除的。**

---

## 三⚠️、C2 / C5 的「GET-only 口径」取舍：文档自己说**不自行裁定**

`registry-entries.md` 里有一段口径边界声明（原文照录要点）：

> **C2**（`POST` 查询）与 **C5**（`POST` 导出）为**非 GET 形态**，
> 按 R2 HANDOFF「只读候选（GET 查询/下载/列表类）」口径属**边界项**，
> 本文件仍给出构造（对照 registry L86 `udc.application.search.no_page` 同形态 POST 查询 `write=False` 先例）；
> **若 main 采严格 GET-only 口径，仅取 C1/C3/C4 三条，C2/C5 降为契约内标注。**
> 该取舍属主控范围，**本文件不自行裁定**。

**实测结果：C2 和 C5 都落库了**（`template_list_by_guids` 是 POST 查询；
`jar_export_app` 虽然对象在库里，但 C5 指的是 `dynamic/jar/download/{appName}` 这条导出）。
⇒ 也就是说，**最终采用了"非 GET-only"口径**（POST 只读也收）。
⇒ 这与 `flow/` / `runtime/` 的 `.effective` 门控是同一件事：
**`write=False` 的 POST 是合法只读契约，只是 `.effective=false`，需走 auth_scope 通道。**

⇒ 判据：**看到"是否收 POST 只读"这类取舍，不要去问文档，去 registry 里看它最后收没收。**

---

## 四、`@ParameterInfo` 文案与实际形参不符（已照录未改）

`udc.attachment.template_list_by_app_id` 的 `verification_rules` 里写着：

> 源码 `@ParameterInfo` 文案为「附件模板 guid」与形参名 `appId` **不符**（逐字照录，语义待 LIVE 确认）

⇒ 路径是 `attachment-template/app/{appId}`，形参是 `appId`，但源码里的参数说明文案写的是"guid"。
⇒ **这是产品源码的文案错误，不是契约错误。** 契约选择了"逐字照录 + 标注待 LIVE"，没去改写成"看起来对"的样子。
⇒ 好做法：**照录 + 标注，不要顺毛修。**

---

## 五、两份一览（按字节降序）

| 文件 | 字节 | 行 | 性质 | 一句话 |
|---|---:|---:|---|---|
| `udc-resource-readonly-contracts.md` | 18,627 | 145 | **只读取证**（5 只读 + 5 写排除） | 三层扫描 + 131 端点行逐条词干判定 + 35 类 `javap` 落盘 |
| `registry-entries.md` | 10,518 | 74 | **5 条建议条目**（全部已落库） | 去重实测 + 口径边界声明 |

合计 **29,145 B / 219 行**（含本 README 时不适用——上表只算 2 份）。

---

## 六、它抄的是 publish → BI 的方法论链

`udc-resource-readonly-contracts.md` 头注原文：

> 方法论照抄 `docs/operation-contracts/udc/bi/bi-vacuum-contract.md`
>（三层扫描法 + 双口径一致性 + 伪命中族排除）**+ R1（publish 域）先例**

⇒ 方法论传播链是：**BI 域（源头）→ publish 域（第一次套用）→ resource 域（第二次套用）**。
⇒ 想学怎么扫一个域：读 `bi/bi-vacuum-contract.md`，再看这两个域怎么套。

证据等级同样分开：
- **VERIFIED_STATIC_BYTECODE** = 三层扫描计数 + 131 端点行逐条词干判定 + 35 类 `javap -p -v` 落盘
- **OBSERVATION** = 域归属语义判读 / Servlet 流式下载面 / 构件边界 / `ParameterInfo` 文案不符举例，**均不升级**

---

## 七、证据单元

`udc-starter-runtime-5.3.517.jar`
（`sha256 = 74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`，**861,880 B**）
—— 与 `menu/` / `runtime/` / `publish/` 同一个 jar。
证据件相对 `docs/audit/artifacts/udc-resource-5.3.517/` 解析。

---

## 八、拿不到什么

- **写形态 5 条的契约** —— 明确排除（只读口径），**不是遗漏**。
- **`template_list_by_app_id` 的 `appId` 真实语义** —— 源码文案写"guid"，待 LIVE 确认。
- **jar 下载的流式语义** —— 属 `OBSERVATION` 级旁证，未升级。
- **LIVE** —— 本域 `VERIFIED_STATIC_BYTECODE`，0 次 LIVE。

---

## 九、与事实层怎么分工

| 想知道 | 去 |
|---|---|
| resource 域有哪些端点、怎么扫出来的 | **本层**（`udc-resource-readonly-contracts.md`） |
| 5 条契约的字段级定义 | **本层**（`registry-entries.md`） |
| 为什么写形态被排除 | **本层** §二 |
| 附件/jar 在运行态怎么被读 | `core/facts/udc/` |
| 本层在 14 个子域里的位置 | `docs/operation-contracts/udc/README.md` |
