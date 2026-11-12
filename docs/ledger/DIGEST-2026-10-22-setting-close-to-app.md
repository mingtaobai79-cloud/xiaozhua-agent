# 续接件 · 会话 20261021_234751_d68325 压缩恢复

- 源会话：`20261021_234751_d68325`（Hermes LCM，2421 条消息，唯一用户指令 34 条，长回复 37 条）
- 时间跨度：2026-10-21 23:49 → 2026-10-22 16:19（本文件生成于 2026-10-22 21:0x）
- 压缩依据：`<HERMES_HOME>/lcm.db` 原始消息去重后逐条提取，非转述猜测
- 用途：新会话开局读这一份即可续上，不依赖对话历史

---

## 0. 一句话现状

设置域「第一步收口」已完成并提交（HEAD `73fffdbe`）：扩展实体验收 6/6 全过、字段集默认值链被彻底纠正为「两套列 + 类型匹配」、10 个 tab 四类资产零缺口、全量测试 1716 passed。随后转入**应用域**，读面接口已全部抓到并部分 LIVE，**写面（设计/测试/发布）尚未抓**。最后停在用户的两条硬指令上：**不发布、不发测试；页面点击只准点「数据迁移」这一个应用**。

---

## 1. 仓库与目录（已按用户要求切好）

```
<XIAOZHUA_AGENT_ROOT>          ← 纯本地 git，勿 push
├── core/facts/                    事实（按域：udc/setting/...）
├── components/                    实现（constructors / constraints / api_model）
├── tools/core/<域>/               可复用脚本：setting 24 / decompile 26 / feishu 13 /
│                                  audit 12 / bpm 7 / page 6 / platform 5 / db 4 / microflow 3
├── docs/                          契约 / 能力 / 台账 / 证据（166M）
├── tests/  providers/  config/
├── _attic_pending/                待删但冻结（135M，UDC 完工前不动，逐条抽离复用）
└── _attic_trash/                  可随时整删（251K）
```

- Hermes 侧 skill 已从 4 个平行目录收拢为 `skills/seeyon/`（01-platform / 02-udc / 03-v8-extension / 04-integration / 05-agent / 06-delivery / 07-office-collaboration）
- 仓库只镜像 **3 个无 PII** 的 skill：`xiaozhua-agent-fact-protocol`、`xiaozhua-constraint-extraction`、`sdd-protocol`；同步工具 `tools/core/_meta/sync_skills_from_hermes.py --check`
- 工作区唯一未提交文件：`tools/core/setting/attribute_default_expr_build.py`（重建默认值表达式验收字段集的脚本，17/17 通过）

---

## 2. 用户定的规矩（后续一切动作的边界）

1. **事实 / 证据 / skill 三层抽离**：规则进仓库，测试值只进 tools 和 R-E8，不许把一次性测试数据写死进事实格。
2. **可复用脚本与一次性脚本分目录**，一次性脚本集中在可整体删除的目录。
3. **删除分两桶**：`_attic_pending`（含已取证事实，先抽离再删）/ `_attic_trash`（纯死物，随时整删）。UDC 全部完工前不删 pending。
4. **不发布、不发测试**（应用域明确禁止）；页面点击**只点「数据迁移」应用**，其他一律不点。
5. **证据优先**：动手前先查 `core/facts` 与 `docs/operation-contracts`；`check` 的返回值必须读，**不许兜底**；只验证到落库不算通过。
6. **URL 只按真实证据**：反编译 `@RequestMapping` 或页面抓包，**禁止按 javap 方法名拼路径**。
7. **UDC 全部完工后**：统一清理测试数据 + 跑一轮全量测试。

---

## 3. 本轮实测硬事实（可复核，均已落事实格）

### 3.1 字段集默认值（最大纠错点）

| 事实 | 内容 | 证据 |
|---|---|---|
| 两套列互斥 | 计算值 → `expressionDesignData` / `expressionRuntimeData`（UDC_ATTR_0017）；默认值 → `defaultValueExpressionDesignData` / `defaultValueExpressionRuntimeData`（UDC_ATTR_0018） | `AttributeService.checkExpressionPattern:1593-1607`（反编译） |
| design/runtime 必须成对 | 只写 design、runtime 写 `""` → 前端拿不到 `executableExpr`，**默认值框空白** | 前端组装 `JSON.stringify(e.designData/runtimeData)` |
| 枚举/选项集不走表达式 | 默认值直接写 `default_value` = **枚举项 id**；多选逗号分隔 | 真实样本（未碰过的应用）+ `ctp_enum_item` 回读 |
| caption 回填差异 | 选项集（`udc_enum_item`）路径下 caption 会被服务端重算成 id；真实样本同样如此 → **不是 bug**；平台枚举（CTP）读 name 的 i18n JSON，caption 正常 | DB 回读对比 |
| `resultTypeInfo` 必须 = 字段 dataType | CTPENUM 字段给 `STRING` 是错的 | 真实样本 `resultTypeInfo="CTPENUM"` |
| BOOLEAN | 必须用 `OPERATOR` 的 `true`，不是 `CONSTANT` | 17/17 验收 |
| 枚举常量 token 形态 | `{type:CONSTANT, value:<itemValue>, controlData:{controlType:"ENUM", controlProperties:'{"type":"CTP","data":{appName,enumCode,multi:false}}'}}` | `ControlData.isSingleCtpEnumConstant()`（`ControlData.java:40-49`） |
| 表达式里禁止放组件 | 只能函数 / 系统变量 / 应用参数；用户原话「放个组件本身是不对的」，正确形态 `textToLong(substring(应用参数.附件,0,18))` | 用户判定 + 回读 `controlData: False` |

**最终 17/17 状态**：全部 `check` 通过、`resultType` 与字段类型一致、`design`+`runtime` 均非空、无 `controlData`；`dfEnum` 走 `default_value`，`dfCtpenum` 走「文本+函数+枚举常量」链。

### 3.2 字段集 / 实体属性的类型差异（新发现）

```
字段集      ENTITY   → relationEntity = 数字 id（如 3582244432195832261）
实体属性    ENTITY   → relationEntity = 全类名 com.seeyon....OrgMember
字段集      Serial   → serial_number_guid = ctp_serial_scheme.guid（不是 id）
字段集枚举            → relation_app 必须有值，否则前端渲染 undefined~<枚举id>
```

### 3.3 删除语义（成功码不可信）

- `udcEnumItemDeletePost` 返回 `BOOT_0000 SUCCESS` **但数据仍在**（`app_guid=-1` 的 3 条 notStarted/processing/finished 至今未清）
- 选项集 `udc_enum` **没有 `is_delete` 列**（逐列核过）→ 「批量删=逻辑删」结论已改为 UNVERIFIED
- 扩展实体 delete 的**真实通道是 GraphQL `udcScalabilityDeletePost`**；REST `/udc/scalability-option/delete` 六种 body 形态全报 `BOOT_3000 message:null`

### 3.4 扩展实体

- 18 种 data-type 全部 `validate=true`；**17 种可写**，仅 `CTPENUM` 失败：`BOOT_1000 扩展字段不允许选择级联枚举`（旧结论「只支持 10 种」是架构推理猜的，被推翻）
- 预留组：25 组 / 17 种类型读通；新建 → BOOT_0000 + 回读 1 行；delete → 回读消失（6/6 验收）
- `udc_custom_ext_field` 只有应用存在 `...Ext` 实体并发布时才物化 → 本应用 0 行是正确的，不是缺陷

### 3.5 应用域（进行中）

| 接口 | 状态 |
|---|---|
| `GET /service/udc/application/{id}` | **LIVE PASS**（BOOT_0000 + 完整 ApplicationDto；不存在 → UDC_APP_0001） |
| `POST /service/udc/graphql?udcApplicationSearchNewWithVersionListPost` | **LIVE PASS**，返回 10 个应用；**mutation**，`paramsKey=body`，`queryFields` 必须逐字照抄 |
| `GET /service/udc/application/user-role?appName=udc` | 已抓到，返回未验证 |
| `GET /service/udc/application/role-resource?appName=udc` | 已抓到，返回未验证 |
| 契约里的 `udc-runtime/custom-app/search-*` | **BLOCKED-ENV**：`udc-runtime` 服务本环境不存在（server_404），契约应废弃 |
| `components/udc/application_api_model.py` 106 个 op | ⚠ 多为 javap 方法名而非真实 URL（8 个实测全 405）→ 需路径审计 |

设计器真实入口（已抓，存 `scratch/app-design/designer-endpoints.json`）：

```
REST
  GET  /service/udc/application/user-role
  GET  /service/udc/sandbox/delta-build-info/{appId}
  GET  /service/udc/application/search/front-detection
  GET  /service/udc/deployment/latest-test-info
GraphQL（13 op）
  udcApplicationGet / udcApplicationDetailGet / udcApplicationAppVersionAppGuidPost
  udcApplicationIsLastVersionAppGet / udcApplicationAppFeatureAppGet
  udcApplicationSearchDetectionPost / udcApplicationDependentApplicationSelectByConditionPost
  udcCollaborationAppGet / udcSandboxSelectAppGet / udcSandboxBuildInfoAppGet
  udcDeploymentAppReadyStatePost / udcOperationLogSearch / InitDataAppGet
```

---

## 4. 产出物路径

```
core/facts/udc/setting/attribute-set/create.md              字段集事实格（含 §15.6 函数维度）
core/facts/udc/setting/attribute-set/default-value-chain.md  默认值赋值链（本轮新建，纠正整条错误）
core/facts/udc/setting/scalability/create.md                 扩展实体 + R-E9 验收
docs/operation-contracts/                                    option-set / parameter / excel-template / expression-component 四份补齐
tools/core/setting/attribute_default_expr_build.py           17/17 默认值表达式重建脚本（未提交）
scratch/app-gql/search-new-with-version.payload.json         应用列表可用 payload
scratch/app-gql/designer-payloads.json                       设计器 GraphQL payload（16:42 写入）
scratch/app-design/designer-endpoints.json                   设计器入口清单
```

设置域审计基线：实现 15 / 事实 14 / 契约 11 / 脚本 30 / registry 设置域契约 37 条 / 10 tab 零缺口。

---

## 5. 待办（按优先级，含未完成与遗留）

1. **应用域写面抓包**（设计 / 测试 / 发布入口）——只准点「数据迁移」应用，**不执行发布、不发测试**，只抓请求体。
2. 应用域读面收尾：`user-role`、`role-resource` 实发验证 → 落事实格；修正 `udc-runtime/*` 废弃条目。
3. `application_api_model.py` 路径审计：从反编译 `@RequestMapping` 提取真实路径，替换方法名拼装。
4. 清 `UI轨迹枚举` 下 3 条 `app_guid=-1` 脏数据（`udcEnumItemDeletePost` 假成功，需换真实通道）。
5. 设置域遗留 UNVERIFIED 逐条推进（已全登记在事实格，未隐瞒）。
6. UDC 全部完工后：清理测试数据 + 全量 `pytest`。

---

## 6. 新会话恢复动作

```bash
cd <XIAOZHUA_AGENT_ROOT>
git log --oneline -3        # 期望 HEAD 73fffdbe 或其后
git status --porcelain      # 期望仅 attribute_default_expr_build.py 未跟踪
pytest tests -q             # 基线 1716 passed / 22 skipped
```

然后读：`core/facts/udc/setting/attribute-set/default-value-chain.md` → `scalability/create.md` → `core/facts/INDEX.md`，即可续做应用域。

---

## 7. 本轮教训（反复踩过的同一类坑，必须记住）

1. **只验证到落库 ≠ 验证到渲染**。`fnJoin` 丢 `expressionTranslation` 页面空白；widgetConfig 只对 STRING 成立就当全类型通用——同一个错误两种形态。
2. **兜底逻辑等于跳过验证**。`transform` 返回空就自己拼 tokens，结果落库成功、前端空白。
3. **不读 `check` 返回值就宣布通过**是第三次重犯。
4. **架构推理猜出来的结论会被一条 `BOOT_1000` 直接推翻**（扩展实体「只支持 10 种」）。
5. **成功码不可信**，一律 DB 回读。
6. 把 Hermes 工作手册当交付物镜像进仓库会撞 PII 检查——已改为白名单 3 个。

---

## 8. 应用域只读面收口（2026-10-22 晚，本轮新增）

### 8.1 结论

9 条只读探针 → **8 LIVE_PASS / 1 BLOCKED（服务缺席）**，全部有 traceId；写面**零执行**。

| op | method | path | 判定 |
|---|---|---|---|
| `udc.application.get`（控制组） | GET | `udc/application/{appId}` | LIVE_PASS（`publishState=UNPUBLISH`、`deployType=RELEASE`） |
| `udc.application.user_role` | GET | `udc/application/user-role?appName=` | LIVE_PASS（92 条角色 id） |
| `udc.application.role_resource` | GET | `udc/application/role-resource?appName=` | LIVE_PASS（8 动作键 → disabled/basic） |
| `udc.deployment.latest_test_info` | POST | `udc/deployment/latest-test-info` | LIVE_PASS（leastTestVersion 1.0.30、testSuccess=true） |
| `udc.application.front_detection` | POST | `udc/application/search/front-detection` | LIVE_PASS（计数全 0，appId=null 占位形态） |
| `udc.sandbox.delta_build_info` | GET | `udc/sandbox/delta-build-info/{appId}` | LIVE_PASS（state=NONE） |
| `udc.sandbox.is_deploy_war` | GET | `udc/sandbox/system/config/is-deploy-war` | LIVE_PASS（false） |
| `udc.sandbox.app_search` | POST | `udc/sandbox/app/search` | LIVE_PASS（10 行，含 appState=RUNNING） |
| `sandbox.flexible.test_status` | POST | `sandbox/flexible/test-status`（服务 sandbox） | **BLOCKED**：`server_404`「sandbox 服务不存在…」 |

### 8.2 新硬事实（改变了后续做法）

1. **设计师页内 `window.fetch('/service/udc/...')` 永久不可用**：CDP `Network.loadingFailed` =
   `net::ERR_CONNECTION_CLOSED`；同 URL 导航 / curl 均 200。→ 探针一律改「CDP 取 cookie → Python 直发」。
2. **弹性部署属独立微服务 `sandbox`**，不是 udc 子路径：`/service/udc/sandbox/flexible/*` = 404，
   `/service/sandbox/flexible/*` = 200+`server_404`。该族在 test2 整体不可用（服务未部署）。
3. **设计器 child-frame 不能单独 reload / 顶层导航**（→ `chrome-error://chromewebdata/` 或空白页）；
   重进设计器只能走「应用列表 → 设计」。
4. 前端调用面 19 条字面量已按 verb 落表；「测试」入口 = `POST /udc/deployment/app-delta-deploy`；
   「发布」入口前端字面量 0 命中（发布在主壳），后端已有 `udc.deploy.normal` 登记。

### 8.3 落盘文件

- `core/facts/udc/application/app-frontend-callsurface.md`（前端 19 条调用面 + 服务边界反证）
- `core/facts/udc/application/evidence/live-app-readonly-2026-10-22.json`（9 探针原始记录，含 traceId）
- `core/facts/udc/application/evidence/app-frontend-surface-2026-10-22.json`（按 bundle 分组的路径提取）
- `docs/operation-contracts/udc/application/udc-app-readonly-live-2026-10-22.md`（逐条契约 + 踩坑）
- `tools/core/application/gateway_readonly_probe.py`（只读白名单探针；`--base` 不写死域名）
- `tools/core/application/cdp_net_capture.py`（CDP 被动抓包，只抓不发）
- `tests/udc/test_application_readonly_surface.py`（12 条自证：契约/白名单/证据结构/无 cookie 泄漏）
- registry 新增 8 条应用域只读契约（总 124 条）

### 8.4 基线

`pytest tests -q` → **1728 passed / 22 skipped**（新增 12 条；文档计数已同步 1738→1750 collected）。

### 8.5 下一步（写面仍未动）

1. 发布入口：从主壳 bundle 找 `app-online` / `deploy-normal` 前端字面量（本页 0 命中）。
2. 测试入口（`app-delta-deploy`）**只登记不执行**，等负责人明确授权再发；验收反向证据用
   `latest-test-info` 的 `leastTestVersion` 递增。
3. `application_api_model.py` 路径审计仍未做。
4. `sandbox` 服务就绪后补登弹性部署族（create/delete/restart/select-deployment-page）。

## 9. 应用内功能页收口（2026-10-22 夜，本轮新增）

### 9.1 覆盖了哪些「进到应用里」的功能
左侧菜单 7 项 + 底部日志 4 类，全部按「点击录制 → cookie 重放」取证：

| 功能 | 取数接口 | 判定 |
|---|---|---|
| 页面测试 | `udc/deployment/latest-test-info` + `udc/graphql?udcDeploymentAppReadyStatePost` | LIVE_PASS |
| 沙箱测试 | 同上（`state=RUNNING`,`msg=DEPLOY_SUCCESS`） | LIVE_PASS |
| 发布版本 | 仅 `latest-test-info`；列表取数未见独立请求 | 部分 UNVERIFIED |
| 应用依赖 / 组件依赖 | 点击 0 请求（判为随应用详情下发） | UNVERIFIED |
| 团队设置 | `udc/graphql?udcCollaborationAppGet` | LIVE_PASS |
| 应用主题 | `app-common/graphql?appCommonThemeSelectDefaultBrandPost`（mutation，页面自动发） | DENIED |
| 设计日志 | `udc/graphql?udcOperationLogSearchInitDataAppGet` + `?udcOperationLogSearch` | 前者 LIVE，后者 mutation 未重放 |
| 微流程运行日志 | `{appName}/udc-runtime/app-log/search/microflow` | LIVE_PASS（10 行） |
| 生单/扣减规则运行日志 | 同族 `dataflow` / `deduction` | 200 + 空列表 |

计数：LIVE_PASS 4 / 存活空结果 2 / 404 证伪族 1 / UNVERIFIED 1 / DENIED 1。

### 9.2 三条新学到的硬规则
1. 运行态日志前缀是**应用名**：`/service/{appName}/udc-runtime/app-log/search/{kind}`，
   拼 `/service/udc/...` 或 `/service/sandbox/...` 全 404。kind 只有 `microflow|dataflow|deduction`，
   `design|page|bizrule|build|compile|sandbox|deployment` 七连 404 已证伪。
2. 应用内功能页的数据面基本是 `POST /service/{service}/graphql?<operation>`，
   回包是 `{alias:{code,data:{content}}}`，alias 可能是 `data0` 也可能是 op 名 ——
   套 REST 顶层 `code` 判据会把成功判成失败（首轮 7 条全 FAIL 的根因）。
3. 「打开页面就发 mutation」是真实存在的：应用主题页自动发 `appCommonThemeSelectDefaultBrandPost`。
   → 抓包审计必须区分「我发的」和「页面自动发的」，后者也要登记为写面。

### 9.3 未验证项（明确挂账，不粉饰）
- 沙箱构建日志接口：只有构建中才渲染「展开沙箱日志」，本轮沙箱已结束，入口消失；7 个 REST 候选全 404。
- 依赖清单独立取数接口、发布版本列表取数：点击 0 请求，判为随应用详情一次性下发。
- 「检查通过」的服务端依据：未定位，禁止用 `front-detection`（计数全 0、`appId=null`）顶替。
- `udcOperationLogSearch` 的真实回包：语义是查询但声明成 mutation，需授权才重放。

### 9.4 落地物
- `tools/core/application/cdp_click_capture.py`（点击录制，被动 Network）
- `tools/core/application/replay_read_probe.py`（cookie 重放，mutation 硬跳过）
- `core/facts/udc/application/app-inner-pages.md`（功能页接口地图）
- `docs/operation-contracts/udc/application/udc-app-inner-readonly-2026-10-22.md`（只读契约，已脱敏）
- 证据：`core/facts/udc/application/evidence/app-inner-pages-2026-10-22/*.json`（6 份，无 cookie）
- registry +9 契约（含 1 条 mutation DENIED、1 条 404 证伪族）
- 测试 +12（`tests/udc/test_application_readonly_surface.py` 共 27 条）
- `pytest tests -q` → 1743 passed / 22 skipped（1765 collected）

## 10. 依赖设置全链路打通（用户授权实测，已复原）

上一轮把「依赖设置」记成 UNVERIFIED（点两页 0 请求），本轮被用户点破：点「添加依赖」就有请求。
补做后全链路五步全部拿到，且**依赖清单接口本来就有**，只是切 tab 复用缓存不重发。

| 步骤 | 接口 | 类型 | 证据 |
|---|---|---|---|
| 点「添加依赖」 | `udc/graphql?udcMetaDataSearchAvailableAppMultiVersionPost` | 声明 mutation，语义查询 | `dep-available-apps.json` |
| 勾选 + 确定 | `udc/graphql?udcApplicationDependentApplicationCreateBatchPost` | **写** | `dep-write-create.json` |
| 自动重拉列表 | `udc/graphql?udcApplicationDependentApplicationSelectByConditionPost` | 声明 mutation，语义查询 | `dep-select-replay.json`（LIVE_PASS） |
| 移除 + popconfirm 确定 | `udc/graphql?udcApplicationDependentApplicationDeleteByIdPost` | **写** | `dep-write-remove.json` |
| 自动重跑检测 | `udc/graphql?udcApplicationSearchDetectionPost` | 检测（写缓存） | `dep-write-remove.json` |

复原：加依赖后列表 3 行，移除后回到 2 行（平台 + 集成平台），与操作前一致。

四条新学到的规则：
1. **0 请求 ≠ 没接口**：SPA 切 tab 复用缓存，只有写操作后才会重拉。要抓列表接口，就得先触发一次数据变更。
2. **勾选失效会发空写**：`params0: []` 照样发请求，什么都没加。判勾选是否生效看
   `tr.ant-table-row-selected` + `input.checked`，不看点击返回值。
3. **antd checkbox 的 DOM click 会被吞**：`label.click()`/`input.click()` 对受控组件常无效，
   必须 `scrollIntoView` + `CDP Input.dispatchMouseEvent` 按坐标点 `.ant-checkbox-inner`。
4. **disabled 是后端许可位**：可选列表 `enableDependent=false`（如无版本 `addressBook`）必 disabled；
   依赖行 `enableDelete=false` 表示内置依赖不可删。

顺带解决的两个挂账：
- 「依赖清单取数接口」→ 已解，见上表第 3 行。
- 「检查通过」服务端来源 → 最强候选是 `udcApplicationSearchDetectionPost`
  （返回 `detectionType/moduleType/path/route/interpolatedMessage`，依赖增删后平台自动串发）。
  但它是写面且未主动触发、未取回包，仍记 UNVERIFIED，不许拿 REST `front-detection` 顶替。

registry +5（`udc.dependency.available_apps|list|create_batch|delete_by_id` + `udc.application.detection`），
测试 +10（该文件 37 条），`pytest tests -q` → 1753 passed / 22 skipped（1775 collected）。

## 11. 沙箱构建全链路 + 组件依赖闭环

用户一句「你自己点不就行了」把剩下两块挂账一次清掉。

### 11.1 构建（工具栏「测试」→「立即构建」）

六段链路，全部实录制：

| # | 接口 | 类型 | 实测 |
|---|---|---|---|
| ① | `POST udc/graphql?udcApplicationSearchDetectionPost` | 一致性检测（mutation） | 1 次 |
| ② | `POST udc/graphql?udcRuntimeDeployNormalPost` | **构建+部署（声明成 query，实为写）** | 1 次 |
| ③ | `POST udc/graphql?udcSandboxBuildInfoAppGet` | 构建信息轮询 | **44 次 / 约 6s 一次** |
| ④ | `WS udc_detection_channel` / `udc_deploy_channel` | 实时状态推送 | 多帧 |
| ⑤ | `WS common-message` | 完成通知 | 1 帧 |
| ⑥ | `POST ctp-application/appcenter/search-app-edition` | 刷新版本列表 | 1 次 |

一次真实构建：前端 PC 编译 14s / 前端 MOBILE 8s / 后端编译 33s / 部署 124s，`totalTime=224`，
结束后页面「测试启动完成 应用启动完成 23:14:55」。

**最大收获**：构建日志不用抓流。`udcSandboxBuildInfoAppGet` 一把返回
`{state,progress,totalTime,logs[37]}`，`logs` 就是「[展开沙箱日志]」的内容。
之前把它记成「必须在构建窗口内抓包」的挂账，是我没找对取数口。

细节坑：
- 该接口别名是 **`path:`** 不是 `body:`（`udcSandboxBuildInfoAppGet(path: $params0)`）。
- 响应外层多一层：`{traceId, data:{data0:…}}`，直接取顶层 `data0` 会 KeyError。
- `udc_detection_channel` 字段名是 `seriouCount`（少个 s），照抄别"修"。
- 构建弹窗文案「立即构建」，点它之前工具栏「测试」还会先发一次 `udcDeploymentLatestTestInfoPost`。

### 11.2 组件依赖（`dependentCmp`）

| 动作 | 接口 | 差异 |
|---|---|---|
| 列表 | `udcApplicationDependentApplicationSelectByConditionPost` | 与应用依赖同一口，返回 44 行（SERVICE 11 + FRONTEND 33） |
| 候选组件 | **无请求** | 86 行来自前端内置目录 `@seeyon/biz-*` / `@seeyon/mbiz-*` |
| 添加 | `udcApplicationDependentApplicationCreateBatchPost` | 同写口，`dependentAppType=FRONTEND`，多 10 个字段 |
| 删除 | `POST udc/application/dependent-application/delete-by-ids` | **REST 批量删**，与应用依赖的 GraphQL `DeleteByIdPost` 不是一条路 |

三个坑：
1. 行内没有「移除」，删除入口是表格上方「批量删除依赖」。
2. 确认框文案「删除后不可恢复! 确定删除吗」，按钮是「取消 / **确认**」（不是 确定）。
3. 该 REST 请求用 CDP `requestWillBeSent` 抓不到（事件被 `Runtime.evaluate` 往返吞掉），
   必须在页面里 hook `XMLHttpRequest`/`fetch` 记 `window.__CAP__` —— 这一招以后抓"抓不到的写口"通用。

复原：加 `@seeyon/biz-lock-sign` 5.3.1（电子签章 web 端）→ 45 行 → 批量删除 → 44 行，
`SERVICE` 11 条（含 `cip-manager`）与 `FRONTEND` 33 条全程未被误改。

### 11.3 顺手清掉的三个挂账

| 原挂账 | 结论 |
|---|---|
| 沙箱构建日志接口 | `udcSandboxBuildInfoAppGet.logs[]` |
| 组件依赖列表/增删 | 同列表口 + 同写口 + REST `delete-by-ids` |
| 发布版本页版本列表 | `ctp-application/appcenter/search-app-edition`（`IN_appId` 传 **appName** 不是 appId） |

### 11.4 落地

registry +6（148 条）：`udc.deploy.deploy_normal`、`udc.sandbox.build_info`、`ctp.version.list`、
`udc.ws.business_channels`、`udc.dependency.component_create`、`udc.dependency.delete_by_ids`。
证据目录 `core/facts/udc/application/evidence/app-inner-build-2026-10-22/`（4 个 json）。
测试该文件 49 条；`pytest tests -q` → 1765 passed / 22 skipped（1787 collected）。

## 12 应用域收口：四类资产补齐（capability 由 ○ 转 ✅）

### 12.1 为什么做这一步

按 `docs/KNOWLEDGE-LANDING-RULES.md`，一个域推进完必须四类同时存在且互相引用：
实现 / 事实格 / 契约 / skill，随后落位测试 + `capability_report.py --check` 无缺口 + 脱敏闸门。
此前应用域只有「契约 + 散装事实 md」，`capability_report` 判定为 **○ 有契约无事实格**。

### 12.2 本次新增

| 类别 | 文件 |
|---|---|
| 实现 | `components/udc/application/__init__.py` |
| 实现 | `components/udc/application/app_inner_ops.py`（取数口/请求体构造/路径归属分类，纯函数） |
| 实现 | `components/udc/application/dependency_constraints.py`（依赖行校验：SERVICE 六字段 / FRONTEND 十扩展字段 / 删除吃行 id） |
| 事实格 | `core/facts/udc/application/app-inner/create.md`（Capability 表 17 行 + 响应层级三坑 + 写面边界） |
| 写链 | `core/facts/udc/application/app-inner/app-inner-write-chain.md`（依赖六步 / 构建六段 / 日志命名 / 三条未解） |
| 契约 | `docs/operation-contracts/udc/application/app-inner-contracts.md`（读 14 条 + 写 6 条，键名对齐 registry） |
| skill | `skills/xiaozhua-udc-application-app-inner/SKILL.md` |
| 测试 | `tests/udc/test_application_app_inner_asset_layout.py`（23 条：落位 / 互链 / 实现形状 / 校验器 / 分类 / 证据一致性 / 脱敏） |

### 12.3 复跑结果

```
capability_report.py --check
  应用    67   7   7   4   ✅ 完整          （此前 67 / 5 / 6 / 4 → ○ 有契约无事实格）
tests/udc/test_application_app_inner_asset_layout.py   23 passed
pytest tests -q                                        1788 passed / 22 skipped（1810 collected）
```

仓库 skill 由 5 个增至 6 个（+`xiaozhua-udc-application-app-inner`）。

### 12.4 剩余缺口（下一站，按同一套规矩补）

`capability_report --check` 仍报 6 个域缺事实格：menu（菜单）、rule（规则）、
microflow（流程/微流程）、bi、column（栏目）、role（角色）。这六域目前只有契约文档、
实现散在 `components/udc/` 根上，没有 `core/facts/udc/<域>/<子模块>/create.md`。

### 12.5 顺带记录：一次可视化复演

应用依赖「加 → 移除」再演一遍（用户要求亲眼看）：
加「公告 5.3.98」→ 3 行；点行内「移除」→ 确认 → 回到 2 行。
删除请求 `{"params0":{"id":"<依赖行 id>"}}`，删除后平台自动串发
`udcApplicationSearchDetectionPost`。截图留在本机 `<HERMES_HOME>/images/dep-add-0*.png`（不入仓）。
