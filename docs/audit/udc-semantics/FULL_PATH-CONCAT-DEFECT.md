# FULL_PATH 拼接缺陷 —— 定位、修复与影响面（2026-10-14）

> 证据：**VERIFIED_STATIC_BYTECODE** + **LIVE**（404 实证）
> 影响面：`docs/audit/artifacts/udc-web-5.3.517-contracts/_api_full.json`（657 方法 / 54 Controller）

## 1. 缺陷

`tools/core/decompile/merge_udc_web_api.py` 原规则：

```python
if pv.startswith("/"):
    full_path = "/udc" + pv          # 把方法级 value 当绝对路径
elif not pv:
    full_path = "/" + base if base else "/"
else:
    full_path = ("/" + base + "/" + pv).replace("//", "/")
```

## 2. 为什么错（Spring 语义 + 字节码）

Spring `@RequestMapping` 的**类级**与**方法级** value 是 **恒拼接**关系；
方法级 value 以 `/` 开头只是书写习惯，Spring 从不把它解析成绝对路径。

字节码实证（`udc-web-5.3.517.jar`，`javap -v`，`PageInfoController.javap.txt`）：

```
#212 = Utf8   udc/page-info                    <- 类级 @RequestMapping
#74  = Utf8   /base-info/create                <- 方法级 @PostMapping
RuntimeVisibleAnnotations:
  org.springframework.web.bind.annotation.PostMapping(value=["/base-info/create"])
```

-> 真路径 = `/udc/page-info/base-info/create`。
缺陷产物给的是 `/udc/base-info/create`，**凭空丢掉了类级段**。

LIVE 佐证（独立于本次修复、先已记录）：

- `docs/audit/udc-semantics/S7-WRITE-CHAIN-LIVE.md` section 1：页面 REST 真路径
  `/udc/page-info/base-info/create`（**带 page-info 前缀**，LIVE PASS），
  而 `_api_full.json` 的 `/udc/base-info/create` **已证 404**。
- `components/udc/live_write_templates.py:87`（在线创建成功）：`POST /service/udc/page-info/base-info/create`
- `PAGE-DOMAIN-CONSTRAINTS.md:42`、`page-menu-source-audit.md:56-67`：同。

即：仓库内**已有 LIVE 反例把该缺陷钉死**，但缺陷长期未修（文档与产物互相矛盾）。

## 3. 修复

```python
frag = (pv or "").lstrip("/")     # 只去前导斜杠（尾斜杠是字节码字面，保真）
if not frag:
    full_path = "/" + base if base else "/"
elif base:
    full_path = "/" + base + "/" + frag
else:
    full_path = "/" + frag        # 类级注解无 value（ParameterController）
```

- 量：657 方法中 **159 个（24.2%）** `full_path` 被纠正。
- 逐条字节码核对过的类级 mapping（javap 中 value=["udc/..."]）：
  `udc/page-info` `udc/page-layout` `udc/portlet` `udc/portlet-group` 
  `udc/page-template` `udc/page-template-class` `udc/sandbox` `udc/runtime` 
  `udc/deployment` `udc/collaboration` `udc/microflow` `udc/application`
- 唯一非方法级以 / 开头的变化：`ApplicationController.transferFormAppPackage`
  字节码字面为 `transfer/batch/`（含**尾部**斜杠）。首版实现用 `.strip("/")` 会误删尾部斜杠，
  已改为 `.lstrip("/")`（保真，差异收敛到恰好 159 条）。

## 4. 影响面

### 4.1 REST 契约面
- 159 条 `full_path` 纠正；被仓库模型消费的断言 21 处（见第 5 节）。
- 缺陷造出的**线上不存在**路径（现全部消失）：
  `/udc/base-info/create`、`/udc/handover`、`/udc/publish`、`/udc/create-portlet`、
  `/udc/app-online`、`/udc/import/new`、`/udc/build-info/{appId}`、`/udc/role-resource`

### 4.2 GraphQL op 面
规则 `op = pathToCamel(path + "/" + httpMethod)`（见 `GRAPHQL-OP-NAMING-RULE.md`）。
由**全量 159 条**（含未被前端目录采集的端点）计算：

| 指标 | 修复前 | 修复后 |
|---|---|---|
| 规则可推导 op | 618 | **655** |
| 其中**线上不存在**的幻影 op | **122** | **0** |

幻影示例（现不应由规则产出）：`udcAppOnlinePost` `udcAppDeltaDeployPost` `udcHandoverPost`
`udcPublishPost` `udcCreatePortletPost` `udcBuildInfoAppIdGet` `udcRoleResourceGet`
`udcAppFeatureAppGet` `udcImportNewPost` `udcBaseInfoCreatePost`
-> 修复后真名形如 `udcDeploymentAppOnlinePost` / `udcApplicationImportNewPost`。

### 4.3 前端 op 归位（**重要口径区分**）
- 对 **`frontend-extraction.json` 的 346 op**：修复前后**都是 224 已归位 / 122 未归位**
  （未归位里 udc 前缀 99）-> 该口径**不变**，`GRAPHQL-OP-NAMING-RULE.md` 的 224/99 仍成立。
- 对 **`frontend-op-catalog.json` 的 456 op**（更宽，全 chunk 扫描）：未归位 **225 -> 133**（多归位 92）。
  且 `derive_ops` 双候选兜底把旧绝对路径幻影并入 op 宇宙，
  令**前端根本不存在**的 op 也出现在映射表里。修复后 op 宇宙干净。

### 4.4 掩蔽机制（已拆）
`components/udc/graphql_op_naming.py:derive_ops` 原并列试算两种拼法：
`full_path` **以及** `class_mapping + 方法 path`。后者在缺陷期间充当兜底，
**掩盖了本缺陷**。修复后实测两种拼法产出 **完全相同的 op 集（655 vs 655，差异 0）**，
兜底已成为死代码 -> 已删除，只保留 `full_path` 单一权威来源；
并加护栏 `test_workaround_is_now_noop_on_real_artifact` 防其复活。
## 5. 修正的既有断言（原为缺陷固化产物，逐条按字节码重判）

| 文件 | 原断言 | 修正为 |
|---|---|---|
| `test_application_api_model.py` | `/udc/import/new` | `/udc/application/import/new` |
| `同上` | `/udc/app-online` | `/udc/deployment/app-online` |
| `同上` | `/udc/build-info/{appId}` | `/udc/sandbox/build-info/{appId}` |
| `同上` | `/udc/app-delta-deploy` | `/udc/deployment/app-delta-deploy` |
| `同上` | `/udc/role-resource` | `/udc/application/role-resource` |
| `同上` | `/udc/appFeature/{appId}` | `/udc/application/appFeature/{appId}` |
| `同上` | `/udc/handover` | `/udc/collaboration/handover` |
| `test_column_api_model.py` | `/udc/base-info/create` | `/udc/page-info/base-info/create` |
| `同上` | `/udc/batch-create` | `/udc/page-info/batch-create` |
| `同上` | `/udc/detail/{id}` | `/udc/page-info/detail/{id}` |
| `同上` | `/udc/select-by-appId/{appId}` | `/udc/page-info/select-by-appId/{appId}` |
| `同上` | `/udc/search-no-page-available` | `/udc/page-layout/search-no-page-available` |
| `同上` | `/udc/base-info/update/caption` | `/udc/page-layout/base-info/update/caption` |
| `同上` | `/udc/create-portlet` | `/udc/portlet/create-portlet` |
| `同上` | `/udc/select-by-appId/{appId} (分组)` | `/udc/portlet-group/select-by-appId/{appId}` |
| `同上` | `/udc/publish` | `/udc/page-template/publish` |
| `同上` | `/udc/check-name` | `/udc/page-template/check-name` |
| `同上` | `/udc/select-tree` | `/udc/page-template-class/select-tree` |
| `test_microflow_api_model.py` | `/udc/search/treeEntity` | `/udc/microflow/search/treeEntity` |
| `同上` | `/udc/find/dto-by-entity` | `/udc/microflow/find/dto-by-entity` |
| `同上` | `/udc/find/data-system` | `/udc/microflow/find/data-system` |

## 6. 回归护栏（新增 6 项）

`tests/udc/test_udc_web_full_api.py`（5 -> 8 项，+3）：
- `test_class_level_mapping_is_always_concatenated` —— PageInfoController 类级拼接（含 LIVE 引注）
- `test_no_full_path_drops_its_class_mapping` —— **全量 657 方法**前缀恒等护栏
- `test_absolute_path_regression_is_gone` —— 负面护栏，幻影路径不得复活

`tests/udc/test_graphql_op_naming.py`（12 -> 15 项，+3）：
- `test_derive_ops_takes_op_from_full_path_only`
- `test_full_path_fix_removed_absolute_path_phantoms`
- `test_workaround_is_now_noop_on_real_artifact`

## 7. 遗留 / 未验证

- `ParameterController` 的类级 @RequestMapping **无 value**（`_contracts.json` 记 `class_mapping: null`
  且 `class_mapping_annotation: true`）-> 其路径形如 `/create` `/update`。是**类级无 value 的真实回退**，
  不是本缺陷（本缺陷只影响方法级以 / 开头的分支）。其网关前缀是否 `/service/udc/...` **UNVERIFIED**。
- `_api_full.json` 的 `full_path` 只含**类级+方法级**，不含网关前缀 `/service/{appId}`；
  实际调用路径 = `/service/udc` + `full_path`（见 `live_write_templates.py`）。
- 前端 op 未归位的 99（extraction 口径）/ 133（catalog 口径）仍属 test2 镜像 5.3.496 API 面，
  **保持 UNVERIFIED**；本轮未改变该结论。
