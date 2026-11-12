# 菜单域契约层（`docs/operation-contracts/udc/menu/`）

> **UTD 契约层的菜单域**：7 份 / 33,444 B / 257 行。
> 上级入口：`docs/operation-contracts/udc/README.md`（14 子域总表）。
> **本目录此前零入口**（上级总表里 `menu/` 那一行标 ❌）。这是它的域入口。

---

## 一、菜单域最根本的事实：**UDC 里没有"菜单"这个类**

`SCAN.md` §2 做过负证据：6 件 5.3.517 UDC jar × 5 个关键词
（`menu|menutree|topbar|sitemenu|resourcemen`）= **全部 0 命中**。

| jar | 命中 |
|---|---|
| udc-common / udc-facade / udc-starter-customplan / udc-starter-dataflow / udc-starter-lowcode / udc-starter-runtime | **0 / 0 / 0 / 0 / 0 / 0** |

⇒ **菜单域不靠 "menu" 关键词定位。** 它是**功能节点 + 页面 + 资源权限的只读视图**，
契约取自 page / resource / role / applog / serial-config / database 六个语义控制器的只读端点。
⇒ 所以"在 UDC 里搜 menu 搜不到"**不是漏了**，是这一域本来就没有自己的类。

---

## 二、于是本目录的 5 条契约**全部是借来的**

| 候选 | op_id | 借自哪个域 | 控制器 |
|---|---|---|---|
| P1 | `udc.role.has_system_admin` | 角色域 | `UdcRoleRtController` |
| P2 | `udc.applog.datalog_get_by_id` | 日志域 | `UdcAppLogController` |
| P3 | `udc.applog.datalog_list_by_data_id` | 日志域 | `UdcAppLogController` |
| P4 | `udc.serial_config.entity_list` | 流水号域 | `UdcSerialConfigController` |
| P5 | `udc.database.query_data` | 运行时数据库 | `UdcRuntimeDatabaseController` |

⇒ **菜单域没有自己的边界。** 判断"这个端点属不属于菜单域"没有任何类级判据，
只能按"它是不是菜单/功能节点/页面/资源权限的读视图"来语义归类。
⇒ 所以本目录**不要**去找"菜单域专属的证据"，它不可能有。

---

## 三、`registry-entries.md` 只列 3 条，但 5 条都落库了

`registry-entries.md`（103 行）只给了 P1 / P3 / P4 三条。P2 和 P5 不在里面。

实测（2026-11-07）**5 条全部在 `registry.py`**：

| op_id | 在 `registry-entries.md` 里 | 在 `registry.py` 里 | registry 里实际叫 |
|---|:---:|:---:|---|
| `udc.role.has_system_admin` | ✅ | ✅ | 同名 |
| `udc.applog.datalog_get_by_id` | ❌ | ✅ | **`udc.applog.select_by_id`** |
| `udc.applog.datalog_list_by_data_id` | ✅ | ✅ | 同名 |
| `udc.serial_config.entity_list` | ✅ | ✅ | 同名 |
| `udc.database.query_data` | ❌ | ✅ | 同名 |

⇒ P2 又是"换了名字"那种情况（同一模式在实体域也出现过，见方法论第 27 条）。
⇒ **`registry-entries.md` 不是本域的完整清单，只是 P1/P3/P4 的构造依据。** 别把它当全集。

---

## 四、`P5` 头部写"不入 registry"，而它**已经进去了**

`P5-udc-database-query-data.md` 标题原文：

> `# P5 — udc.database.query_data（HYPOTHESIS，不入 registry）`

`SCAN.md` §4 也写「标 HYPOTHESIS，**不入 registry**」。

**实测：`udc.database.query_data` 已在 `registry.py` 里注册**，
`status = OperationStatus.VERIFIED_STATIC_BYTECODE`，`write = False`，
且 `verification_rules` 里带着那句保留的疑点：

> 「响应为 SingleResponse 包裹 UdcRuntimeDatabaseQueryRespDto；**GET 带请求体语义需 LIVE 复核**」

⇒ 这是"**HYPOTHESIS 被入库、但把 HYPOTHESIS 的性质写进了 verification_rules**"的处理方式。
**不算误入库，但文件名和标题的"不入 registry"现在是过去时。**
⇒ 别照着"不入 registry"去把它删掉或当未完成项。**它进了，而且把该挂的 UNVERIFIED 挂着。**

---

## 五、⚠️ 本域 3 条是**重复注册**，全库共 6 条（这是 registry.py 的问题，不是文档的）

实测全库：**117 条契约 / 111 条不同路径 / 6 条路径被注册两次（共 12 条契约）**。
本目录占了 **3 条**：

| 路径 | 注册了两次的名字 |
|---|---|
| `udc-runtime/app-log/datalog/list-by-dataid/{dataId}` | `udc.applog.list_app_data_by_dataid` **+** `udc.applog.datalog_list_by_data_id` |
| `udc-runtime/serial-config/select-entity-list` | `udc.serial.select_entity_list` **+** `udc.serial_config.entity_list` |

（第三处同型的在实体域：`meta-data/check-page-exists` 与
`meta-data/select-host-and-only-page-pages`，各注册两次。全库另有两处在
`deploy-info` 与 `udc/graphql?...` 上。）

**特征很明显：两套命名风格** —— `udc.applog.*`（短）vs `udc.applog.list_app_data_by_dataid`（长）、
`udc.serial.*` vs `udc.serial_config.*`、`udc.page_info.*` vs `udc.metadata.*`。
**两个合并会话各按自己的命名落了同一批端点。**

⇒ **同一路径注册两次意味着同一接口在能力清单里出现两个身份。** 调用方按 op_id 记审计会分裂。
⇒ **但这不属文档整理范围。** 本目录不改 `registry.py`、不删任何一份 `P*.md`
（每份都是"这个 op_id 凭什么这样构造"的依据）。**已记入进度文件待裁决⑨。**

---

## 六、七份一览（按字节降序）

| 文件 | 字节 | 行 | 性质 | 一句话 |
|---|---:|---:|---|---|
| `registry-entries.md` | 13,157 | 103 | 落库条目（**只 3 条**） | P1/P3/P4 的 10 字段构造签名，照抄风格对齐 `registry.py` L44–L51 |
| `SCAN.md` | 5,070 | 77 | **域定位 + 负证据** | 本目录唯一解释"为什么没有 menu 类"的文件 |
| `P4-udc-serial-config-entity-list.md` | 4,211 | 16 | 单条 7 要素 | `GET select-entity-list` |
| `P2-udc-applog-datalog-get-by-id.md` | 3,185 | 16 | 单条 7 要素 | `GET datalog/{id}` |
| `P3-udc-applog-datalog-list-by-data-id.md` | 2,899 | 15 | 单条 7 要素 | `GET datalog/list-by-dataid/{dataId}` |
| `P1-udc-role-has-system-admin.md` | 2,883 | 15 | 单条 7 要素 | `GET has-system-admin/{appName}` |
| `P5-udc-database-query-data.md` | 2,039 | 15 | 单条 7 要素（**标题已过期**） | `GET query-data`，见 §四 |

合计 **33,444 B / 449 行**（含本 README 时不适用——上表只算 7 份）。

---

## 七、`SCAN.md` 里两件必须传下去的事

### ① 排除清单比候选清单更值钱

§5 列了 **13 个 GET 端点被排除**，理由全是"GET 但其实是写"：

| 控制器 | 被排除的 GET | 为什么 |
|---|---|---|
| `UdcAppLogController` | `delete-all` / `clear-org-manager` / `clear-runtime-data-source-cache` / `unload-dynamic-app/{appName}` / `enable-log/{enable}` | 清缓存 / 卸载 / 改开关 |
| `UdcAttrSnapshotRtController` | `delete-by-data-id/{dataId}` / `delete-by-master-data-id/{masterDataId}` | delete 语义 |
| `UdcSerialConfigController` | `refresh-historical-data/{appName}` / `cache-evict/{appName}` | refresh / 清缓存 |

⇒ **这不是洁癖：这套系统里大量"写"操作走 GET。** 任何"GET 就是只读"的推断都会把删除/清缓存写成只读契约。
⇒ 反过来：`POST` 里的 `search` / `search-details` **是读但需要 POST 体**，
本轮不圈定**不等于**它们是写。SCAN 如实记了这点。

### ② 「C1 被微流程域占用」这句是跨域边界的唯一记录

> C1 `selectFunctionNodeTreeMetaData` 已被微流程会话占用，**不入菜单域候选**。

功能节点树读视图明明最像"菜单"，但它归微流程域。
**跨域归属靠这句话记下来** —— 删了 SCAN 就再没人知道 C1 为什么不在菜单域。

---

## 八、拿不到什么

- **LIVE 回读** —— 本域 0 次 LIVE。5 条全部 `VERIFIED_STATIC_BYTECODE`。
- **网关 service 前缀** —— 每份 `P*.md` 都写「禁拼网关前缀；网关 service 前缀 UNVERIFIED」。
- **GET 带请求体的语义** —— `udc.database.query_data` 的 `RuntimeDataBaseQueryDataReqDto` 要不要 body，
  离线不可确证，`verification_rules` 里明确挂着待 LIVE 复核。
- **菜单域自己的证据目录** —— 没有。证据都在 `docs/audit/artifacts/u` 开头的其他域目录里。

---

## 九、与事实层怎么分工

| 想知道 | 去 |
|---|---|
| 这 5 条 op_id 的入参/返回/证据等级 | **本层**（`P*.md` 7 要素） |
| 为什么 UDC 没有 menu 类、7 个控制器怎么映射 | **本层**（`SCAN.md`） |
| 哪些 GET 其实是写（**避免误判只读**） | **本层**（`SCAN.md` §5） |
| 功能节点树 / 页面 / 资源权限在事实层怎么描述 | `core/facts/udc/`（`page/`、`entity/`、microflow 域） |
| 本层在 14 个子域里的位置 | `docs/operation-contracts/udc/README.md` |

---

## 十、证据在哪

`SCAN.md` 头注写明：证据等级 `VERIFIED_STATIC_BYTECODE`（`javap -p -v`，本地 Maven 离线），
禁 LIVE / 禁连网关 / 禁连 `.207`。jar 基线
`<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`
（`jar sha256 = 74ae50bd…40a66f`，实测存在）。
类级 sha256 前 8 位：`UdcRoleRtController` ed024802 / `UdcAppLogController` f6a2111d /
`UdcSerialConfigController` fe1e5a72 / `UdcRuntimeDatabaseController` 588bc1cf。
