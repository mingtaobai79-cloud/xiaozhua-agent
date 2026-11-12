# core/facts/udc/setting/ 索引（设置域事实格）

## 这个目录是什么

**设置域的事实层**：17 份，10 个 tab 子目录（每个一个 `create.md` 为主）+ 2 份目录级公共件。
合计 **170,855 B**（2026-11-07 实测）。

⚠️ **先分清本目录和 `docs/operation-contracts/udc/setting/` 的分工**——两者同名，极易走错：

| | `core/facts/udc/setting/`（本目录） | `docs/operation-contracts/udc/setting/` |
|---|---|---|
| 层级 | **事实层** | **契约层** |
| 回答 | 「这个 tab **实际长什么样**」——真实 body、真实报错、实测坑 | 「这个 tab 的**端点叫什么、必填什么、协议是什么**」 |
| 单位 | 一个 tab 一份 `create.md` | 一份 tab 契约 + 一份 runbook |
| 入口 | 本文件 | 该目录 `README.md` |

**查用法看本目录，查端点/必填/报错码看契约目录。** 两边都记录了同一个坑时，以本目录的实测记录为准
（契约层是从这里提炼的）。

## 一、17 份一览（2026-11-07 实测）

| 文件 | 字节 | 行 | 外部引用 | 一句话 |
|---|---:|---:|---:|---|
| `attribute-set/create.md` | 35,192 | 817 | 7 | **字段集（Attribute Set）**——本域最大一份，含 `calculate=COMPUTE` 三段链 |
| `attribute-set/default-value-chain.md` | 10,363 | 234 | 6 | 默认值赋值链（2026-10-22 实测） |
| `scalability/create.md` | 16,555 | 391 | 6 | 扩展实体（Scalability Option）——影子实体 `<name>Ext` |
| `enum/enum-write-chain.md` | 14,224 | 347 | 4 | 枚举域写链（UdcEnum / UdcEnumCategory / UdcEnumItem） |
| `custom-object/fields.md` | 12,443 | 264 | 4 | 自定义对象字段组装（12 类数据类型 × 3 类类别） |
| `excel-template/create.md` | 11,195 | 274 | 5 | 导入导出模板（Excel Template） |
| `custom-object/create.md` | 9,741 | 178 | 7 | 自定义对象（DataTransferObject）域事实格 |
| `enum/create.md` | 9,386 | 169 | 6 | 枚举域写链事实格（分组/枚举/枚举项/删除/查询） |
| `qrcode/create.md` | 9,300 | 228 | 6 | 二维码规则（QR Code Rule） |
| `expression-component/component.md` | 8,952 | 230 | 4 | 表达式组件（「默认值 +」→「高级模式」）链路 |
| `serial/create.md` | 8,521 | 237 | 6 | 流水号（Serial Scheme） |
| `serial/serial-number-enums.md` | 5,814 | 148 | 0 | **流水号枚举取值域**（javap 直读）+ `checkDto4Create` 逐分支还原 —— 1008 的真相是「SERIAL 段计数 != 1」 |
| `operation-matrix.md` | 6,011 | 109 | 5 | **操作存在性矩阵**（update / delete / search）——目录级公共件 |
| `option-set/create.md` | 5,542 | 123 | 6 | 选项集（Option Set） |
| `body-vs-dto-fields.md` | 8,634 | 212 | 0 | **工具 body ↔ 平台 DTO 字段对照**（javap 直读）—— 揪出 refer_config 的 unknowns 垃圾键 |
| `precondition-appguid.md` | 4,154 | 103 | 4 | **取 appGuid**——目录级公共前置，所有 tab 都要先过这关 |
| `parameter/create.md` | 3,462 | 88 | 6 | 参数（Parameter） |

合计 **17 份 / 179,489 B**。**每一份都有外部引用**（4–7 处），不存在可以随手删的孤立件。

## 二、两份目录级公共件（先读这两份）

| 文件 | 为什么先读 |
|---|---|
| `precondition-appguid.md` | **所有设置域写操作的第一个坎**：拿不到 `appGuid` 什么都做不了。这里写的是「取法」（`udcApplicationDetailGet`），不是"取自 `udc_application.guid`"这种表名列名。真实事故（2026-10-23）：功能都做完了，换个地方用，**第一步 appGuid 就卡住**，搜 INDEX 搜不到 |
| `operation-matrix.md` | **先查存在性再动手**：update / delete / search 哪些 tab 有、哪些没有。没有 delete 的 tab 去试删除只会得到误导性报错 |

## 三、协议分布（本域最贵的错误来源）

设置域的 10 个 tab **不是同一种协议**，混起来查必错。详见契约层
`docs/operation-contracts/udc/setting/README.md` 的分组表，这里只给判据：

| 协议 | tab | 判据 |
|---|---|---|
| **GraphQL** | enum / option-set / custom-object / serial / parameter | op 名形如 `udcEnumCreatePost`，body 是对象 |
| **REST** | excel-template / expression-component / qrcode | 走 `POST /udc/<x>` |
| **父子两协议** | attribute-set / scalability | **父级 REST、子级 GraphQL**（详见下） |

### ★★ `attribute-set` 与 `scalability` 两份都写着同一句「零、最大发现：父子两级用**两种协议**」

这不是巧合——它俩是同一类结构（父容器 + 子列表），失败方式也一模一样：

```text
attribute-set    父（字段集）REST /service/udc/attributeSet      子（字段）GraphQL udcEntityAttributePost
scalability      父（方案）  REST /service/udc/scalability-option 子（预留组）GraphQL udcScalabilityPost
```

`attribute-set/create.md` 原文记录了失败过程：**最初以为字段也走 REST，4 种变体全部静默失败**——
回 `BOOT_0000` 但 `udc_attribute` 零写入。真相只能从页面真实抓包得到。

**教训（原文）**：**DTO 里有某个字段 ≠ 该类通过它写入。父子两级很可能分属两种协议。**

**假阴性判据**：拿 GraphQL 探 REST 端点必然 `FieldUndefined`——**那是假阴性，不代表端点不存在**。
先确认协议再下"不存在"的结论。

## 四、三处已知的坑（本目录最贵的知识）

1. **`parameter` 的平台拼写错**：`udcCtpParameterDefinitonPost` —— `Definition` 少一个 `i`。**照抄错的才对。**
2. **`option-set` 与 `enum` 是两套独立表**，id 不互通。混用会让页面显示 `_<appName>_<id>` 异常串。
3. **`attribute-set` 的 `expressionRuntimeData` 由服务端代码生成写入**，客户端只能传空
   （见 `attribute-set/create.md` §十五，`calculate=COMPUTE` 三段链）。

## 五、不要做的事

- **不要**把本目录和 `docs/operation-contracts/udc/setting/` 合并：事实层记"实际长什么样"，
  契约层记"端点/必填/报错"，合并会失去「实测 vs 提炼」的对照。
- **不要**因为某份看起来"只讲一个 tab"就拆得更细：10 个 tab 就是平台的 10 个页签，一 tab 一份是自然粒度。
- **不要**在本目录再建 `README.md`（本文件就是）；新 tab 出现时加子目录 + 本表一行。
- **不要**手改 `attribute-set/create.md`（817 行、7 处引用）前不跑 `pytest tests/udc -q`。

---

维护：新增 tab → 建 `<tab>/create.md` → §一 加一行 → 更新合计字节 → 若引入新的
「静默成功 / 假阴性」坑，必须登记进 §三或 §四（散落在正文里等于没有）。
