# 页面规则域契约层（`docs/operation-contracts/udc/page/`）

> **UTD 契约层的页面规则域**：2 份 / 48,032 B / 340 行。
> 上级入口：`docs/operation-contracts/udc/README.md`（14 子域总表）。
> **本目录此前零入口**（上级总表里 `page/` 那一行标 ❌）。这是它的域入口。

---

## 一、8 条建议：5 条同名落库、1 条带占位符落库、2 条**故意不落**

| 状态 | 条数 | 明细 |
|---|---:|---|
| ✅ 同名落库 | **5** | `page_log.search` / `page_log.search_non_metadata` / `page_info.check_exists` / `page_info.select_host_and_only_page` / `page_refer.select_by_id` |
| ⚠️ 带占位符落库 | （含上面第 5 条） | `udc.page_refer.select_by_id` 的 path 里有 `<BASE-UNRESOLVED-in-5.3.517>` |
| ❌ **故意不落** | **2** | `page_refer.select_tree` / `page_refer.search_list_by_conditions` |
| ❌ 待定 | 1 | `page_general.get_cascade_default_value` |

（合计 5 + 2 + 1 = 8。第 5 条既"落库"又"带占位符"，故单列一行说明。）

---

## 二、⚠️ `registry.py` 里有一条 path 是**占位符**，不是可调地址

实测 `registry.py` 原文：

```python
contracts["udc.page_refer.select_by_id"] = UdcOperationContract(
    "udc.page_refer.select_by_id", "GET",
    "<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{referGuid}/{objectId}",
    ...
    ("同一 objectId 回读 identity_matches，SingleResponse.data 为该参照对象",
     "base 段 UNRESOLVED-in-5.3.517（同 C5，需 LIVE 解析 BaseComponentController 基址）",
     "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

**这是全库 117 条契约里唯一一条 path 不是可调地址的。** 其余 116 条的 path 都是
`udc-runtime/...` 或 `graphql?...` 之类真实字面量。

`registry-entries.md` 对这件事的原话：

> **base 段逐字保留**：path = `<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/…/​{objectId}`，
> **未臆造任何前缀**；base 的 LIVE 解析（继承 `BaseComponentController`，**5.3.517 全库无此类**）
> 仍为 UNRESOLVED，`verification_rules` 内该项保留为待 LIVE 项。

⇒ **这是"正确的拒绝"**：宁可把不确定性原样留在契约里，也不猜一个前缀。
⇒ 但后果要清楚：**按 path 直接调这条会失败**（`<` 不是合法 URL 段）。
⇒ **判据：契约"在 registry 里"不等于"可调用"。** 查可用端点时要过滤掉含 `<` 的 path。

---

## 三、那 2 条"故意不落"的理由

| 条目 | path 尾部 |
|---|---|
| `udc.page_refer.select_tree` | `…/{referGuid}/select-tree` |
| `udc.page_refer.search_list_by_conditions` | `…/{referGuid}/search-list-by-conditions` |

它们的 base 段同样 UNRESOLVED，**且与已落库的 `select_by_id` 同族**（同一 controller、同一 base）。
⇒ 同一 base 未解析的情况下，落了一条（带占位符）而不落另外三条，**不一致但可解释**：
`select_by_id` 是 GET 且已有 LIVE readback 判据可写；另三条是 POST 且条件更复杂。
⇒ **但这是需要裁决的不一致**，已记入进度文件待裁决。

### 为什么 registry 里 5 条不是 8 条

`page_info.*` 与 `page_log.*` 那几条的 base 段**是确定值** `udc-runtime/meta-data/…` /
`udc-runtime/rt-page-log/…`，所以能干净落库。
`page_refer.*` 与 `page_general.*` 的 base 来自 `BaseComponentController` —— **5.3.517 里根本没有这个类**，
所以 base 无从解析。

⇒ **同一份建议里两种 base 状态混在一起**，是 5 条而不是 8 条的全部原因。

---

## 四、⚠️ 这一域还有两处别名重复（接第 40 轮实体域的线索）

`registry.py` 里同一 path 被注册两次，本域占两条：

| path | 注册两次的名字 |
|---|---|
| `udc-runtime/meta-data/check-page-exists` | `udc.page_info.check_exists` **+** `udc.metadata.page_exists_check` |
| `udc-runtime/meta-data/select-host-and-only-page-pages` | `udc.page_info.select_host_and_only_page` **+** `udc.metadata.page_tree` |

注意 `udc.metadata.page_tree` 的**名字与路径语义对不上**（`page_tree` 配 `select-host-and-only-page-pages`）。
本域建议的是 `page_info.*` 那一套；`metadata.*` 那一套**不在任何一份 `registry-entries*.md` 里，来路不明**。

⇒ 全库重复注册已实测为 **6 条路径 / 12 条契约**（第 41 轮），本域占 2 条。
⇒ **不属文档整理范围**，已记待裁决⑨。本目录不改 `registry.py`、不删任何一份文件。

---

## 五、两份一览（按字节降序）

| 文件 | 字节 | 行 | 性质 | 一句话 |
|---|---:|---:|---|---|
| `registry-entries.md` | 26,397 | 187 | **8 条建议条目**（主文档） | 字段级构造 + base 段逐字保留声明 |
| `page-readonly-contracts.md` | 21,635 | 153 | 只读契约 7 要素 | 端点面 + 证据 + 排除清单 |

合计 **48,032 B / 340 行**（含本 README 时不适用——上表只算 2 份）。

---

## 六、拿不到什么

- **`BaseComponentController` 的基址** —— 5.3.517 全库无此类，base 段 UNRESOLVED，需 LIVE。
- **`page_general` / `page_refer` 三条的可用 path** —— 同上，只有 `<BASE-UNRESOLVED…>` 占位。
- **LIVE 回读** —— 本域 `VERIFIED_STATIC_BYTECODE`，0 次 LIVE。
- **网关 service 前缀** —— 每条 `verification_rules` 都写「UNVERIFIED，禁止拼前缀」。

---

## 七、与事实层怎么分工

| 想知道 | 去 |
|---|---|
| 8 条的入参/返回/`write`/evidence | **本层**（`registry-entries.md`） |
| 页面规则域有哪些端点面、排除哪些 | **本层**（`page-readonly-contracts.md`） |
| 页面在运行态怎么被读写 | `core/facts/udc/page/`（3 份 / 75,774 B） |
| 那两条别名 `udc.metadata.*` 的来由 | **没人知道**（待裁决⑨） |
| 本层在 14 个子域里的位置 | `docs/operation-contracts/udc/README.md` |

---

## 八、证据在哪

`registry-entries.md` 头注写明风格来源 = `registry.py` 现有条目构造签名，
`class_sha256` / `javap` 路径逐条写在 evidence dict 里。
本目录自己的证据目录：`docs/audit/artifacts/` 下 `u` 开头的 runtime / entity 目录
（页面规则面与 runtime 共用 `udc-starter-runtime-5.3.517.jar`，
`jar_sha256 = 74ae50bd…40a66f`）。
