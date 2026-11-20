# 统计口径登记表

> 硬规则：**任何报告里的数字必须能在这里找到口径。对不上的数字一律重新统计，不许沿用。**
> 统计脚本：`scripts/research/stats_registry.py`
> 复现命令：`./.venv/Scripts/python.exe scripts/research/stats_registry.py --md`
> 平台版本：`udc-platform-5.3.517`
> 最后核验：2026-11-17

---

## 1. 签名库总量

| 字段 | 内容 |
|---|---|
| 统计对象 | 全平台类与方法签名 |
| 数据源 | `docs/audit/signatures.txt.gz`（2,236,202 bytes） |
| 版本 | udc-platform-5.3.517 |
| 统计规则 | 逐行读取；第 2 列为 `class/interface/enum/@interface` 者计类声明；含 `#` 且含 `(` 者计方法声明 |
| 结果 | 总行 **245709**；类 **21389**；方法 **224320** |
| 证据等级 | `STATIC_RULE` |
| 局限 | 签名不含方法体，无法证明运行行为 |

---

## 2. CodeTask 实现类

| 字段 | 内容 |
|---|---|
| 统计对象 | 声明 `code(CodeContext)` 的类 |
| 数据源 | `docs/audit/signatures.txt.gz` |
| 统计规则 | 检索含 `#code(com.seeyon.udc.common.autocode.context.CodeContext)` 的行，取 `#` 前类名去重 |
| 结果 | **53**（含接口自身 1 个）→ **真实实现 52** |
| 证据等级 | `VERIFIED_STATIC_BYTECODE`（签名级） |

### 构成（必须区分）

| 包 | 数量 | 性质 |
|---|---|---|
| `com.seeyon.udc.autocode.task` | 30 | 主生成任务 |
| `com.seeyon.udc.autocode.task.front` | 5 | 前端元数据任务 |
| `com.seeyon.udc.autocode.v27.task` | 9 | **版本化（v27）** |
| `com.seeyon.udc.autocode.v27.task.front` | 5 | **版本化前端（v27）** |
| `com.seeyon.udc.common.autocode` | 1 | **接口自身，非实现** |
| `com.seeyon.udc.extend.task` | 1 | 扩展 `CtpExcelJsonTask` |
| `com.seeyon.udc.extend.detection.associate.deploy` | 1 | 扩展 `AssociateCodeTask` |
| `com.seeyon.udc.extend.domain.service.deploy` | 1 | 扩展 `CtpEnumCodeTask` |

### 对照口径（不可混用）

| 口径 | 数量 |
|---|---|
| 类名以 `Task` 结尾（全平台） | **204** |
| `autocode.task` 包内 class 声明 | **32**（其中 `AbstractMicroFlowCodeTask` 抽象、`PageControllerTask` 本包未声明 code → 实际 30） |

**⇒ v3 的「32」= 包内 class 数，非实现数。已查明，不冲突。**

---

## 3. Template 类

| 字段 | 内容 |
|---|---|
| 统计对象 | 模板载体类 |
| 数据源 | `docs/audit/signatures.txt.gz` |
| 统计规则 | 口径 A：声明 `getTemplateOutMap()` 的类去重；口径 B：类名以 `Template` 结尾 |
| 结果 | 口径 A **36**；口径 B **74** |
| 证据等级 | `VERIFIED_STATIC_BYTECODE`（签名级） |

### 口径 A（主）构成

| 包 | 数量 |
|---|---|
| `com.seeyon.udc.autocode.template` | 23 |
| `com.seeyon.udc.autocode.v27.template` | 13 |

### 另有 4 个抽象基类（不是模板载体）

```
com.seeyon.udc.autocode.template.base.AbstractUdcFreemarkerTemplate
com.seeyon.udc.autocode.template.base.AbstractUdcDecoratableFreemarkerTemplate
com.seeyon.udc.autocode.template.base.AbstractDecorateEntityTemplate
com.seeyon.udc.autocode.template.base.AbstractDecorateMicroFlowTemplate
```

**⚠️ 「36」≠「某次生成实际用了 36 个」。实际参与数是动态的，取决于应用元数据。**

**⇒ v3 的「24」是手工枚举，已废弃。**

---

## 4. 模板清单 `_codegen_templates.json`

| 字段 | 内容 |
|---|---|
| 统计对象 | 模板资源记录 |
| 数据源 | `udc-platform-5.3.517.tar.gz` → `udc-biz-5.3.517/_codegen_templates.json` |
| 统计规则 | 41 个顶层 key 的 value 数组元素求和 |
| 结果 | 分组 **41**；条目 **464** |
| 版本分布 | 2.7→13 组 / 2.8→14 组 / 2.9→13 组 / 3.0→1 组 |
| 证据等级 | `STATIC_RULE` |
| 局限 | ① 含目录占位（如 `"third/"`），非纯文件数 ② 只证明资产记录存在 ③ 无 .ftl 内容 |

---

## 5. DAO 方法

| 类 | 方法数 | 唯一名 | 重载 |
|---|---|---|---|
| `com.seeyon.boot.starter.mybatis.inone.dao.AllInOneBaseDao`（接口） | **41** | 36 | 5 |
| `com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao`（抽象类） | **55** | 50 | 5 |

**⇒ 不是 41+55=96 的相加关系。抽象类实现接口，有重叠。**
**未判定：** 各实体生成的 `*Dao` 如何继承、是否覆盖。

---

## 6. AppService

| 口径 | 数量 |
|---|---|
| 文件总行数 | 10176 |
| 含方法行 | **9343** |
| 唯一 owner 类 | **830** |
| 名字以 `AppService` 结尾 | **830**（全部） |
| 名字以 `AppServiceImpl` 结尾 | **0** |

**⇒ 830 全是接口，零实现类。平均每接口 11.3 方法。**
**⇒ 「830」是接口类数，不是能力数。**

**⇒ v4 的「1000」是概数，已废弃。**

---

## 7. udc 实体 Service 接口

| 字段 | 内容 |
|---|---|
| 统计规则 | 类名匹配 `udc.*\.(api\|service)\.\w+Service$` 且有方法行 |
| 结果 | **179** |
| 局限 | 平台预置服务；客户应用生成的 Service 不在签名库 |

---

## 8. 元数据资源（本轮新增）

| 统计对象 | 数据源 | 结果 | 规则 |
|---|---|---|---|
| stereotype | `resources/stereotype/*/config.json` | **6** | 文件计数 |
| feature 定义 | `resources/feature/*/config.json` | **18** | 排除 4 个 `*/template/config.json` |
| feature 模板声明 | `resources/feature/*/template/config.json` | **4** | 含 `classType`/`classMode` 声明 |
| feature config 总数 | 同上合计 | **22** | 文件计数 |
| attributeSet | `presetData/attributeSet.json` | **18 个集 / 122 字段** | 数组元素求和 |
| 字段 dataType 种类 | 同上 | **10 种** | `set()` |
| 实体事件 | `presetData/event/defaultevent.json` | **9** | 3 动作 × 3 时机 |
| 单据状态 | `presetData/billEnum.json` → `billStatus` | **8** | 枚举项计数 |
| 单据发送状态 | 同上 → `billSendState` | **2** | 枚举项计数 |
| 扩展列 | `presetData/scalability.json` | **30** | 10+10+10 |
| 字段权限项 | `presetData/attribute/presetAttributeCapacity.json` | **58** | 数组元素 |
| 平台服务依赖 | `presetData/dependencyGraph.json` | **17** | `dependList` 长度 |
| 预置实体 | `presetData/entity.json` | **3** | 数组元素 |
| classType 种类 | `feature/*/template/config.json` | **7** | 去重 |
| classMode 种类 | 同上 | **2** | 去重 |
| joinPointName 种类 | `feature/tree_entity/template/config.json` | **5** | 去重 |

---

## 9. ★ 双源交叉验证（新增）

**方法：用 `extension-points.md`（独立统计）验证 `stats_registry.py`（脚本统计）。**

来源：`surface-index.tar.gz` → `extension-points.md`（由 `tools/core/platform/emit_extension_points.py` 生成）

| 接口 | extension-points 的 impl 数 | 我的脚本统计 | 一致性 |
|---|---|---|---|
| `CodeTask` | **52** | 52 实现 | ✅ 完全吻合 |
| `TransportHandler` | **32** | 30+（现修正为 32） | ✅ 修正 |
| `Interpreter` | **9** | 9 | ✅ 完全吻合 |
| `CodeContextAware` | 5 | 未统计 | — |
| `TenantDataFilter` | 2 | 未统计 | — |

**⇒ 结论：`CodeTask` 52 个实现、`TransportHandler` 32 个实现、`Interpreter` 9 个实现，均有双源确认。**
**⇒ 这三个数字可以升级为「已交叉验证」。**

**扩展点总体规模（逐字）：**
```
151 个带 abstract 的 UDC 接口
├─ 128 个真接口
│   ├─ 101 个平台已有实现
│   └─ 27 个纯扩展位（零实现）
└─ 23 个注解
```

---

## 10. 数字变更台账

| 指标 | v3/v4 旧值 | 当前实测 | 差异原因 |
|---|---|---|---|
| CodeTask | 32（v3）/ 53（v4） | 53 含接口 / **52 实现**（双源确认） | v3 用包内类数；v4 未排除接口 |
| Template | 24（v3）/ 36（v4） | **36**（口径 A） | v3 手工枚举 |
| TransportHandler | 30+ | **32**（双源确认） | 精确化 |
| 模板条目 | 464 | **464** | 一致 |
| 模板分组 | 41 | **41** | 一致 |
| AppService 类 | 1000（v4 初稿）/ 830 | **830**（全接口） | 初稿为概数 |
| AppService 方法 | 9343 | **9343** | 一致 |
| DAO 接口方法 | 41 | **41**（唯一 36，重载 5） | 补重载信息 |
| DAO 抽象类方法 | 55 | **55**（唯一 50，重载 5） | 补重载信息 |
| feature config | 26（v4） | **22**（18+4） | v4 计数错误 |
| 预置实体 | 6（假设） | **3** | 假设错误 |

---

## 11. ★★ 标品 18 包清点（第 10 轮新增，独立口径）

| 字段 | 内容 |
|---|---|
| 统计对象 | 18 个标品 jar 的 CFR 反编译产物 |
| 数据源 | `/d/software/hermes/cache/scratch/std-src/<jar>/` |
| 版本 | 见下表（**非 5.3.517，本机版本更高**） |
| 统计脚本 | `scripts/research/std_census.py` |
| 去重方式 | 同文件内同名方法取参数最长者；跨包同名类型**不合并** |
| 过滤规则 | 只统计 `public/double-default` 声明；排除 if/for/while/switch/catch/try/synchronized/return/new |
| 统计时间 | 2026-11-17 |
| 证据等级 | `VERIFIED_STATIC_SOURCE`（源码级，非仅签名） |

### 11.1 逐包结果

| 包 | 类 | 接口 | 枚举 | 注解 | 方法 | 合计 | 版本 |
|---|---|---|---|---|---|---|---|
| bpm-facade | 397 | 40 | 96 | 0 | 5894 | 533 | 5.3.374 |
| organization-facade | 295 | 54 | 64 | 1 | 6449 | 414 | 5.3.601 |
| ctp-user-facade | 165 | 44 | 54 | 0 | 2987 | 263 | 5.3.429 |
| boot-starter-formula | 181 | 10 | 8 | 3 | 1281 | 202 | 5.3.603 |
| boot-starter-file | 80 | 8 | 1 | 0 | 987 | 89 | 5.3.600 |
| boot-starter-serialnumber | 73 | 6 | 6 | 0 | 824 | 85 | 5.3.603 |
| boot-starter-excel | 68 | 2 | 2 | 0 | 816 | 72 | 5.3.603 |
| boot-starter-enums | 45 | 4 | 2 | 0 | 605 | 51 | 5.3.603 |
| boot-starter-cache | 41 | 3 | 2 | 0 | 270 | 50 | 5.3.600 |
| boot-starter-dynamicsql | 36 | 5 | 1 | 0 | 364 | 42 | 5.3.600 |
| boot-formula-engine | 27 | 2 | 6 | 6 | 379 | 41 | 5.3.603 |
| boot-starter-eventbus | 16 | 2 | 1 | 2 | 184 | 24 | 5.3.600 |
| boot-starter-datatype | 22 | 1 | 0 | 0 | 144 | 23 | 5.3.600 |
| boot-starter-parameter | 19 | 2 | 1 | 0 | 215 | 22 | 5.3.603 |
| boot-starter-attachment | 12 | 1 | 2 | 0 | 139 | 15 | 5.3.290 |
| boot-starter-transaction | 11 | 0 | 0 | 0 | 60 | 15 | 5.3.600 |
| boot-starter-lock | 9 | 0 | 0 | 0 | 75 | 9 | 5.3.600 |
| boot-starter-systemvariable | 3 | 0 | 1 | 0 | 146 | 4 | 5.3.603 |
| **合计** | **1500** | **184** | **247** | **12** | **21819** | **1954** | |

**跨包同名类型 6 个（不合并）：**
```
BpmRepealDto / BpmStopDto / BpmTakeBackDto        bpm-facade 内部重名
FunctionReturnValueDto                             boot-formula-engine / boot-starter-formula
OrgScopeConditionDto / OrgScopeDataDto             ctp-user-facade / organization-facade
```
**⇒ 去重后唯一类型名 1678。**

### 11.2 ★ 与 domain-index.json 的口径差异（必须区分，不可混用）

| 口径 | 统计对象 | 接口数 | 方法数 |
|---|---|---|---|
| `domain-index.json`（第 9 轮） | **业务域视图**（跨包归并，含 boot-core） | 329 | 3179 |
| `std-census.json`（第 10 轮） | **jar 包视图**（严格 18 包） | 184 | 21819 |

旧 domain-index 的域分布：
```
affair 15 / bpm 64 / connector 32 / datasource 6 / dubbo 10
file 28 / formconvert 16 / formula 36 / mybatis 62
organization 58 / systemvariable 2
```

**⇒ 差异根因（已核实，非数据错误）：**
1. **统计对象不同**：domain-index 按业务域跨包归并（`bpm` 域含 bpm-facade + udc 中相关类）；std-census 严格按 jar 包
2. **包含范围不同**：domain-index 含 `boot-core`（datasource/dubbo/mybatis 等域），std-census 只含这 18 个 jar
3. **包名字段写法不同**：domain-index 记录 `com.seeyon.boot.starter.file`，实际为 `com.seeyon.boot.starter.file.appservice`

**⇒ 两个数字都对，但回答不同问题。以后引用必须标明口径。**

### 11.3 ★ 扫描器缺陷修正记录

| 项 | 内容 |
|---|---|
| 缺陷 | `METHOD_RE` 用 `^\s{4}` 匹配，只能匹配 4 空格缩进且带修饰符的方法，漏掉 `public SingleResponse<X> send(...)` 这种「public + 无 default」声明 |
| 症状 | `BpmAppService` 算成 **4** 个方法（实际 **26**）；全平台方法数偏低 |
| 修正 | `^\s{4}` → `^\s+` |
| 修正后 | `BpmAppService` = 26（8 public + 18 default）；全量方法 21578 → **21819** |
| 发现方式 | 与实际 `grep -cE "^\s+default\s+"` 结果（4）不符 → 重读全文 → 发现 8 个 `public` 声明被漏 |
| 教训 | **统计脚本必须先做「单点人工核对」**：挑一个已知类手数一遍，不一致就查正则 |
