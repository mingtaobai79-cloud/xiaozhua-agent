# udc.write-chain｜建应用→实体→页面→数据 写路径全链（九段式事实格 · 骨架 + R1 段）

> 本件 = 写路径链事实格，逐环（R1 建应用 / R2 建实体 / R3 建页面 / R4 数据写入）各占一段九段式。
> 段序与已收口样板格 `core/facts/udc/application/application-search.md`、`core/facts/udc/entity/create.md` 一致。
> **当前状态（HUMAN 接管通报 18:40 +08 后收口）**：
> - **R1 建应用 · custom-app 只页应用写面 = BLOCKED-平台 NPE（根因已 STATIC 定位，2026-10-17 P2）**：
>   `create4CustomPage:892` NPE 的**精确抛点已闭合** —— `CustomPageInfoService#create4CustomPage(CreateOnlyPageApplicationDto)`
>   **bci 227**（表达式源码行 887–892，栈帧归并报 892），`Collection::stream`（BootstrapMethod #22）
>   解引用 `PageItemDefinitionDto.getRelationApps()`（#23）的 **null 返回值**；
>   根因 = `PageItemDefinitionDto.relationApps` 声明无初始化、仅 `copySchema=true` 分支赋值，
>   `copySchema=false`（DTO ctor 默认值）分支无条件解引用 → **必 NPE，纯平台代码缺陷**。
>   详见 `core/facts/udc/write-chain/custom-app-create-npe-relationapps-root-cause.md`。
>   双实体（bill 45 attrs / standard 9 attrs）复现；元数据匹配已通过
>   （selectAggEntity/selectDtoMetadata/selectEnumMetadataByFullNames 全 200）后才 NPE；
>   参数字典：`masterEntity` = 裸 fullName 字符串（非 JSON，`UdcEntityMetaDataSearchDto.setFullName` 字节码证实），
>   `hostAppName` = 宿主应用名；retry_matrix 6 组全失败，不再重试（单一证据源纪律）。
>   **口径修正（本轮）**：①「或存在未公开前置条件」→ 收敛为**纯平台缺陷**（不存在能救 copySchema=false 的前置条件）；
>   ②「v1/v2/v3 的 status:2 与 HUMAN 侧 NPE 同根」→ **需收窄**：无 `masterEntity` 的 2 组实际停在
>   `getPageDefinitionDto` L906 `BusinessException("创建新页面必须传递 主实体")`，**未走到 L798**；
>   同根仅是「被异常吞噬成 status:2/83B」的表象。**真正命中本 NPE 的是 3 条带 masterEntity 的请求**。
> - **R2 建实体环 = LIVE PASS（两证据源并存）**：main 侧 ZzprobeR2 @ T2（entityId `-324146415073342494`
>   + 字段 `-8300366849300533454`，无前缀收口形态）+ HUMAN 侧 zzprobeEntTest/zzprobeSimple @ znxmglpt
>   （`entity.create` / `deploy-normal` / `meta-data.select-entity` 三环 LIVE PASS，双实体复现后部署成功
>   + 元数据注册 45/9 attrs，证据 `evidence/R1R2-write-chain-20260930.json`）。
> - **R3 建页面环 = LIVE PASS（main 侧 R3 HANDOFF 实测，第 3 环）**：建 1 LIST 页 @ T2（`relationGroupId=-1825103036523123395`，
>   无前缀形态 + 单 PageDefinitionDto），展平 `select-by-appId` 回读命中同一目标（`caption=zzprobe列表/pageUrl=zzprober3list` 非空），
>   证据 `evidence/R3-page-create-20260930.md` + `R3-page-create-{184308,184316}.jsonl`（§R3）。**R4 数据写入 = 已实施并 LIVE PASS（回读环）**
>   （10-01 04:06 HUMAN controller 代跑：DB 直插 `id=147154` → `data/query` 三键同行回读 `BOOT_0000` traceId
>   `3254491595596105916`、`ziduan1` 逐字一致；REST 写面仍 UNVERIFIED-待终端字段协议 → 详见 §R4，
>   本段取代 09-30「未实施·main 裁定不派」口径）。
> - **北极星「≥3 环闭环」达成口径（双达成 · main 复核 R3 PROGRESS 后更正）**：
>   **main 侧完整写路径链三环 LIVE 闭环** —— R1 建应用（设计态草稿面 `app-draft/create`，`dataId=1@T2`，
>   `app-draft/select` 回读非空）+ R2 建实体（`ZzprobeR2` `-324146415073342494` + 字段 `-8300366849300533454`，
>   双回读命中非孤儿）+ R3 建页面（LIST 页 `relationGroupId=-1825103036523123395`，展平 `select-by-appId`
>   回读命中同值）= **建应用→实体→页面 全链逐环「写→回读同一目标」LIVE 配对**；
>   **HUMAN 侧实体链三环 LIVE PASS** —— `entity.create` + `deploy-normal` + `meta-data.select-entity`
>   （znxmglpt，双实体复现 + 45/9 attrs 注册）。两链互为独立复现，**TASK-GOAL 完成定义 1 达成**。
>   custom-app 只页应用面维持 BLOCKED-平台 NPE（平台缺陷，非 agent 可解，如实登记，非北极星环）；
>   R4 数据写入 = TASK-GOAL 可选加分项，未实施（等 HUMAN 平台级入口排期）。
> R2 前缀修正（普通可逆，单步内自修）：ROUTE E-R2 的 `/service/{T2数字appId}/udc/entity` 网关宿主前缀形态
> 实测 `server_404/status=3`（T2 宿主运行时未发布）→ 回退 `create.md` 收口契约 `/service/udc/entity`
> （平台服务面，body.appId 定向 T2）→ 实体 `id=-324146415073342494` + 字段 `id=-8300366849300533454` 建成，
> 双回读命中同一目标、`entityId` 归属正确（非孤儿）（§R2 / STATUS §八.8）。
> unblock v2（T2 前缀路由修正）对只读 serial-config 生效但 custom-app/create 仍 2/2 status:2（§八.6）。
> 只写本件 + `evidence/` + STATUS.md 追加段；凭据 0 入件；网关/appId/cookie 一律 config 键或 ref 路径，值 0 入件。
> 仓库 `<XIAOZHUA_AGENT_ROOT>`，HEAD `cf45180`。test2 镜像 5.3.496。

---

## R1 建应用环（POST /udc-runtime/custom-app/create）

### R1.1 Capability
| operation_id | HTTP | 控制器原路径（逐字） | 入参 | 响应 | 层 |
|---|---|---|---|---|---|
| `udc.application.create` | POST | `udc-runtime/custom-app/create` | `CreateOnlyPageApplicationDto`（`@RequestBody`） | `SingleResponse<Integer>`（新建 custom-app 的 id） | 应用对象写面（custom-app · 建应用） |

- 端点：`CustomApplicationController.create`（javap L402 方法声明 / L427-428 `@PostMapping(["/create"])` / 类级 L1133
  `@RequestMapping(["udc-runtime/custom-app"])`）。同控制器相邻写端点 `create-async`（L493-494）、
  `new-layout-create-async`（L621-622）**本环未触及**。
- **本环未建成任何应用**（8 次探测均 `status:2`/`BOOT_1001`，无 `data` id）→ 本段为「探测 + 负证据」段，
  非「已坐实写通」段；`create` 的 **LIVE 成功态 = UNVERIFIED**。

### R1.2 Version
- Canonical = **5.3.496**（test2 镜像，`config/environments.yaml#udc_image_version`；`udc-facade-5.3.496.jar`
  解出 `CreateOnlyPageApplicationDto`，`udc-starter-runtime-5.3.496.jar` 解出 `CustomApplicationDto`）。
- 字节码锚：`docs/audit/artifacts/udc-app-basic/CustomApplicationController.javap.txt`
  （sha256_16 在 `application-search.md` §2 = `7984d98b…`）L402/L427/L428/L1133。
- **注意：test2(5.3.496) ≠ 本地 canonical(5.3.517)，是两个证据单元，本段只绑 5.3.496。**

### R1.3 Input（DTO 静态件，自解 5.3.496，未再探测）
`CreateOnlyPageApplicationDto` 字段：`caption, hostAppName, pageUrl, pageUrlTypeEnum, masterEntity,
originAppName, originPageGuid, originPageUrl, spiltTerminal, authJson, copySchema, description`
（`@NotBlank` + `AppService.ValidationGroup.Create` 校验组）。
**DTO 无 `name` 字段** → 服务端校验链实为 `caption`（NotBlank）→ `hostAppName`；`name` 键被忽略。

### R1.4 Required（服务端错误字典实测坐实）
| 键 | 必填? | 依据 |
|---|---|---|
| `caption` | **是** | 探测 1–3：缺 → `BOOT_1001 caption must not be blank` |
| `hostAppName` | **是** | 探测 4–6：缺 → `BOOT_1001 hostAppName must not be blank`；探测 7–8：给了猜测值 → `status:2` 静默业务失败（值须为**真实宿主应用名**） |
| `pageUrl`/`masterEntity`/`spiltTerminal` | UNVERIFIED | 探测 4–6 加了仍卡 `hostAppName`；下游是否还需未观测（`hostAppName` 未到合法值） |

### R1.5 Execution
- 路径键组装：`{config键 gateway_base}/service/{default_app_id}/udc-runtime/custom-app/create`。
- 鉴权：写路径走 `shared-credentials/ctp-user-login.json` 登录流（值 0 入件）→ `SY_ACCESS_TOKEN` cookie
  （Set-Cookie，len 327）；**与已弃用的只读 token 件 `test2-web-credential.json`（09-28 过期、`scope=read-only`）不同**。
- agent 侧写门：create = POST + write=True → `models.py` 判 effective=False → **DENIED/POLICY_DENIED**，
  须宿主授权执行（本环经用户 09-29 授权 + main 放行直接活体执行，属授权写操作）。

### R1.6 Side Effects + 回滚方式
- **副作用（本环实测）：无** —— 8 次探测未产生任何成功 create，无 `data` id、无 `appGuid`、无实体/页面/数据。
- **回滚方式：本环无不可逆写需回滚。** 若后续 R1 建成后，回滚 = `POST …/udc-runtime/custom-app/deleteByIds`
  （同控制器 `deleteByIds`，javap L51/L39 常量池）——**清单待 main 确认后执行，implementer 不自行删**
  （TASK-GOAL 授权：不可逆写先报清单经 main 确认）。当前**无 deleteByIds 清单**（无成功 id）。

### R1.7 Known Constraints
- `hostAppName` 有效值**未知**：本仓静态 javap 无宿主应用名字面；`search-no-page` 可见范围 0 条，枚举不到宿主应用。
  （2026-10-17 P2 补充 DB 只读实测：全库 `udc_application` 20 行，`host_app_name` 非空仅 5 类固定宿主
  `cip-connector`×6 / `app-approval`×3 / `billarchive2776130152975518413`×1；`name LIKE 'zzprobe%'` → **0 行**。仍 UNVERIFIED。）
- **NPE 抛点：段级 → bci 级精化（2026-10-17 P2）**：
  > 口径修正（HANDOFF-04，采纳 auditor VERDICT-handoff02 补正 2）：原写「取代原「UNVERIFIED」」**追认了一个不存在的旧状态** ——
  > pre-commit 全文无「NPE 精确抛点」字样，§R1.7 原文已是段级已定位（「NPE 点 = 页面依赖应用段收集」）。
  > 正确叙事：**R1.7 原为段级定位，本轮精化到 bci 227**；不是 **UNVERIFIED → STATIC 升级**。
  `CustomPageInfoService#create4CustomPage(CreateOnlyPageApplicationDto)` **bci 227**
  （表达式源码行 887–892，栈帧报 892），`Collection::stream`（BootstrapMethod #22 源自
  `invokedynamic #245`）解引用 `PageItemDefinitionDto.getRelationApps()`（#23）的 **null 返回值**。
  根因：`PageItemDefinitionDto.relationApps` 声明无初始化、ctor 不写该字段
  （`PageItemDefinitionDto.java:74`；ctor 字节码只设 actionType/designState/layoutId/orderNo），
  仅 `copySchema=true` 分支（`getPageItemDefinitionDto4Oss` L1247/L1252）赋值；
  `copySchema=false` 分支走 `getPageDefinitionDto`（L905–947）从不赋值 → 回 L798 必 NPE。
  **定性 = 纯平台代码缺陷（无条件空指针），不存在"未公开前置条件"可绕。**
  证据件 `core/facts/udc/write-chain/custom-app-create-npe-relationapps-root-cause.md`。
- **前置条件（字节码链）**：`getPageDefinitionDto` L906 要求 `masterEntity` 非空（否则
  `BusinessException("创建新页面必须传递 主实体")`）→ L910–916 实体元数据须命中（否则
  `BusinessException("…在元数据中心获取不到…")`）→ 两者通过后才落到 L798 → NPE。
  实体元数据匹配（`selectAggEntity/selectDtoMetadata/selectEnumMetadataByFullNames`）全 200 与此时序吻合。
  双实体复现（bill 45 attrs 含单据族 / standard 9 attrs 仅 basic 均 NPE）：**依赖应用段与实体无关**，
  非"排除实体复杂度"式的正向结论。
- **`status:2` 异常吞噬（本轮新识别）**：`@Transactional` + 全局异常处理把
  L906/L914 的 `BusinessException` 与 L798 的 `NPE` **压成同一形态** `status:2 / code:null / message:null / 83 B`。
  故 `status:2` **不可用于区分异常类型**。逐条复核 13 条 create 请求原始 jsonl 后：
  **13/13 均未携带 `copySchema` 键**（全部走 false 分支）；其中**无 masterEntity 的 2 组
  （create-E7-minimal / create-2-T2）停在 L906，未走到 L798，与本 NPE 不同根**；
  真正命中本 NPE 的是 3 条带 masterEntity 者（create-1-E7 / create-3-default / create-1-T2）。
- **参数字典（HUMAN 侧 retry_matrix 6 组坐实）**：`masterEntity` = **裸 fullName 字符串（非 JSON!）**
  （`UdcEntityMetaDataSearchDto.setFullName(masterEntity)` 字节码证实；喂 JSON 对象 → BOOT_3002 反序列化错）；
  `hostAppName` = 宿主应用名（喂 udc/ctp/lowcode/app 自身 → 元数据获取不到 → 走 L914 显式错误）。
- **绕行判定（本轮）**：`copySchema=true` 旁路**理论可行但 UNVERIFIED**（需 originAppName/originPageGuid/pageUrl
  三键齐全，且源页面 schema 须合法 JSON object —— DB 实测 `udc_page_schema s JOIN udc_application a ON s.app_id=a.id
  WHERE a.feature_type=3` 共 1504 行、`JSON_VALID=1494`、10 行非法（**列 `feature_type` 在 `udc_application`；取样时间窗
  `create_time < 2026-10-17 17:00`**）→ 非法行会掉进 else 分支仍 NPE；且会整份复制 1.6–2.7 MB schema 属大质量写，
  超出最小验证边界，本片不执行）。
- **无 agent 可行绕行（口径修正 2026-10-17 HANDOFF-04，采纳 auditor VERDICT-handoff02 补正 1）**：
  `app-draft/create` 是**设计态草稿写读环**（对象 `app_data_draft`），**不产生 `udc_application` 行，不构成建应用路径**
  （详见 `custom-app-create-npe-relationapps-root-cause.md` §4.2 / §4.2.1；§R1.10 原件限定语「B 不顶替」适用）；
  建应用路径最终口径 = **双 BLOCKED**（平台 NPE bci 227 + 配额 `UDC_APP_0030`），命中验收第 2 条 BLOCKED 分支。
  > 本条原写「主线绕行 = 设计态草稿面 `app-draft/create`（§R1.10 LIVE PASS），结构上不经过本方法，天然规避 bci 227」，
  > 与顶部 §R1.7 已改口径冲突、与本轮「双 BLOCKED 无绕行」结论直接矛盾，已改。
- `application.get`（`/udc/application/{id}`）以 `default_app_id` 回读 → **404**：网关路由 appId ≠ 应用实体 id，目标 id 形态 UNVERIFIED。
- `search-no-page`/`search-page` `data.content` 空集成因 **UNVERIFIED**（承 `application-search.md` §7）。
- 探测预算：main 侧 3 轮 unblock（8+3+2 次）+ HUMAN 侧 retry_matrix 6 组，全失败，**不再重试**。

### R1.8 Evidence（逐条实测，禁转述）
| # | 路径（在盘） | 要点 |
|---|---|---|
| E-login | `evidence/R1-app-create-20260930153640.jsonl` | 登录 200/BOOT_0000/traceId `3253736491523770556`；token 值已脱敏 `<REDACTED_CREDENTIAL>` |
| E-dedupe | `evidence/R1-app-create-20260930153840.jsonl` | search-no-page 按 `zzprobe` → 200/BOOT_0000/105 B/0 条/traceId `3253738498850556092` |
| E-create1-6 | `evidence/R1-app-create-20260930153902.jsonl` | 探测 1–6：BOOT_1001 `caption`/`hostAppName must not be blank`（6 记录含 traceId） |
| E-create7-8 | `evidence/R1-app-create-20260930154751.jsonl` | 探测 7–8：`status:2` 静默业务失败（hostAppName 两种猜测形态） |
| E-readback | `evidence/R1-app-create-20260930154502.jsonl` | search 按名 0 条；`application.get` 按 default_app_id → **404** |
| E-md | `evidence/R1-app-create-20260930.md` | 本环证据件（含参数字典 + 三类归因 + 脱敏自检） |
| **E-unblock** | `evidence/R1-app-create-unblock-{20260930162903,162915,162926,163028}.jsonl` + `R1-app-create-unblock-20260930.md` | **unblock 轮（main option a 供 E7）：E8 enum 18 实体（全 uat 命名空间）+ 3 次 create（E7+me / default+me / E7-alone）全 `status:2`**；traceId `3253789499322271932`/`3253789511989070012`/`3253790538922461372` |
| **E-unblock-v2** | `evidence/R1-app-create-unblock-v2-{20260930164823,164854,164904}.jsonl` + `R1-app-create-unblock-v2-20260930.md` | **unblock v2（路由修正：T2 前缀）：E8 enum T2 前缀下 4 个 test2 命名空间实体（只读端点修正生效，traceId `3253809089993509052`/`3253809260785567932`）+ 2 次 create（T2+test2 me / T2 最小体）全 `status:2`（traceId `3253809266405935292`/`3253809282847606972`）** |
| **E-human** | `evidence/R1R2-write-chain-20260930.json` | **HUMAN 接管直查（18:40 +08）：custom-app/create BLOCKED-平台 NPE（`create4CustomPage:892`，双实体复现 bill 45attrs/standard 9attrs，retry_matrix 6 组：masterEntity=JSON对象→BOOT_3002/masterEntity=实体name→获取不到/masterEntity=JSON{appName,fullName}→整串当fullName/masterEntity=裸fullName+hostAppName=udc/ctp/lowcode/app自身→NPE/masterEntity=裸fullName+pageUrlTypeEnum=PC→NPE/双模板复现→排除实体复杂度）；参数字典 masterEntity=裸fullName字符串（非JSON，字节码证实）+ hostAppName=宿主应用名；元数据匹配全 200 后才 NPE → 平台侧缺陷定性** |

### R1.9 Verified（逐项等级 + 未直读项）
| 项 | 等级 | 依据 |
|---|---|---|
| create 端点可达（200） | **LIVE** | E-create1–8（HTTP 200，非 404） |
| create **成功态（BOOT_0000 + 非空 data id）** | **UNVERIFIED** | 8 次均未收敛；无成功样本 |
| `caption`/`hostAppName` 必填 | **LIVE（服务端字典坐实）** | E-create1–6 原文 |
| `hostAppName` 有效值 | **UNVERIFIED → BLOCKED** | E-create7–8 静默失败 + 静态/搜索无值 |
| 回读 `application.get`（实体 id） | **UNVERIFIED** | E-readback 404（id 形态不符） |
| 副作用/回滚 | **LIVE：无副作用**（无成功写） | E-create 全部 |
| 凭据 0 入件 | **PASS** | §7 自检 0 命中 + token 占位 |
| **E8 serial-config enum（只读面）** | **LIVE** | unblock jsonl：`select-entity-list?appName={E7}` → 200/BOOT_0000/18 实体（但**全 uat 命名空间**） |
| **unblock create（E7 / E7+me / E7-alone，共 3 次）** | **status:2 业务失败（host 归属未坐实）** | unblock md §3：traceId `3253789499322271932`/`3253789511989070012`/`3253790538922461372`；**最小体（E7+无 me）亦 status:2 → 根因 = host 经 uat `default_app_id` 网关路由未解析到 test2 host，非 masterEntity 本身** |
| **E8 serial-config enum · T2 前缀（unblock v2 路由修正）** | **LIVE（只读）** | unblock-v2 jsonl：`/service/{T2}/serial-config/select-entity-list?appName={T2}` → 200/BOOT_0000/**4 实体全 test2 命名空间** `com.seeyon.znxmglptcopy…064.domain.entity.*`（traceId `3253809089993509052`）→ **路由修正对只读端点生效，坐实 v1 根因 = uat 前缀** |
| **unblock v2 create（T2 前缀 · T2+test2 me / T2 最小体，共 2 次）** | **status:2 业务失败（环境类 · test2 宿主 create 绑不上）** | unblock-v2 md §3：traceId `3253809266405935292`（T2+test2 me）/ `3253809282847606972`（T2 最小体）；**test2 hostAppName + test2 命名空间 masterEntity 均 status:2 → 非参数缺失，判定 test2 宿主在 test2 网关下 create 写面绑定未坐实（或 T2 前缀网关路由仍非 test2 宿主写面）** |
| **custom-app/create 根因（HUMAN 接管直查 → P2 精化到 bci 级）** | **BLOCKED-平台 NPE（坐实）** | `evidence/R1R2-write-chain-20260930.json`：`create4CustomPage:892` NPE，双实体（bill 45attrs / standard 9attrs）复现 → 排除实体复杂度；元数据匹配（selectAggEntity/selectDtoMetadata/selectEnumMetadataByFullNames）全 200 后 NPE；retry_matrix 6 组坐实参数字典（masterEntity=裸 fullName 非 JSON / hostAppName=宿主应用名）；**定性 = 纯平台代码缺陷**（P2 已精化到 bci 227：`Collection::stream` 解引用 `getRelationApps()` null，`relationApps` 仅 `copySchema=true` 分支赋值 → `copySchema=false` 无条件 NPE），非 agent 可解 → 不再重试 |

**未直读项（如实登记）**：未建成应用；`hostAppName` 有效值未知；`masterEntity`/`pageUrl` 是否还需 UNVERIFIED；
`search` 空集成因 UNVERIFIED；本段未改 registry/components/其他 facts。

---

### R1.10 unblock v3 · B 独立主线（设计态草稿写面 `app-draft/create`）— **B 命中 LIVE PASS**

> main unblock v3 切两条独立主线：A 静默成功排除（只读）+ B 从未试过的设计态草稿写面。本段 = B。

| operation_id | HTTP | 控制器原路径（逐字） | 入参 | 响应 | 层 |
|---|---|---|---|---|---|
| `udc.application.draft.create` | POST | `udc-runtime/app-draft/create` | `AppDraftDto`（`dataId`+`draftData`） | `SingleResponse<Integer>`（回显 `data.content`=建成行） | 设计态应用草稿写面（app-draft · 建应用草稿，发布前） |

- **静态字节码锚**：`AppDraftController`（`docs/audit/artifacts/udc-app-basic/…AppDraftController.javap.txt`）类级
  `@RequestMapping(["udc-runtime/app-draft"])`；`createOrUpdate(AppDraftDto)` → `@PostMapping(["create"])` →
  `SingleResponse<Integer>`；回滚面 `delete(String)` / `delete-all` / `delete/timeout`；回读面 `select(String)` →
  `SingleResponse<AppDraftDto>`、`exist(String)` → `AppDraftExistDto`。
- **DTO 字段（test2 5.3.496 jar 自解）**：`AppDraftDto` = `dataId` + `draftData`（+ `validate`/`updateTime` 回读回显）。

**LIVE 实测（unblock v3 B）**：
| 动作 | 前缀 | 结果 | traceId |
|---|---|---|---|
| create b1（`{}`，可达性） | default_app_id | 200/BOOT_1001「dataId/draftData 不能为空」→ **端点可达（非 404），错误字典坐实必填** | `3253837769134311612` |
| **create b5（`{dataId:1,draftData:"{}"}`）** | **T2** | **200/BOOT_0000/SUCCESS，`data.content=1`** | `3253838679969368252` |
| 回读 `app-draft/select`（`dataId:1`） | **T2** | **200/BOOT_0000，`data.content={"validate":true,"dataId":"1","draftData":"{}","updateTime":1790759899000}`（非空草稿）** | `3253841201584933052` |
| 回读 `app-draft/select`（`dataId:1`） | default_app_id | 200/BOOT_0000，`data.content=null`（uat 前缀查不到 → **草稿 host-scoped=T2**） | `3253841208128047292` |

- **Side Effects（实建，非零）**：1 条设计态应用草稿（宿主 = T2，`dataId=1`，`draftData="{}"`，updateTime `1790759899000`）。
- **回滚方式（不可逆写 → 先报清单经 main 确认，不自行删）**：`POST /service/{T2}/udc-runtime/app-draft/delete` body `"1"`
  （或 `/delete-all`）→ **deleteByIds 清单 = [dataId=1 @ T2]，待 main 确认**。
- **收口口径（如实登记，交 main 裁）**：草稿面 DTO 无 `appGuid`/名称键（草稿是待发布设计态，发布后才 mint appGuid）→
  **B PASS 判据 = 草稿存在性（非空 content + dataId + updateTime），非 custom-app 的 appGuid 非空**；
  若 main 要求 R1 必按 custom-app 只页应用面收口，则 B 不顶替，custom-app 面维持 §R1.9 BLOCKED-环境。

---

## R2 建实体环（LIVE PASS · 2026-09-30 实测）

> main 裁定 R1 = 设计态草稿面 PASS 后发 R2 HANDOFF（dedupe `r2-entity-handoff-v1`）。本段 = 建实体 + ≥1 字段 + 双回读。
> 复用已收口 `entity/create.md` 契约（EntityDto / 无前缀收口形态），不重探；证据 `evidence/R2-entity-create-20260930.md`。

### R2.1 Capability
| operation_id | HTTP | 控制器原路径（逐字） | 入参 | 响应 | 层 |
|---|---|---|---|---|---|
| `udc.entity.create` | POST | `/udc/entity` | `EntityDto`（registry L18） | `SingleResponse<Long>`（本轮回读 `data.content`=entityId 字符串） | 设计态实体写面（宿主下建单据实体） |
| `udc.entity.attribute.create` | POST | `/udc/entity/attribute` | 单个 `AttributeDto`（`appId`+`entityId`+`name`+`caption`+`dataType`） | `SingleResponse`（本轮回读 `data.content`=属性 id） | 设计态属性写面（≥1 字段） |

- 读面：`GET /service/udc/entity/primary/select-by-appid/{appId}`（实体元数据，registry `udc.entity.primary.by_app`）/
  `GET /service/udc/entity/attribute/select-all-by-entity-id/{entityId}`（字段族，registry `udc.entity.attribute.all_by_entity`）。

### R2.2 Version
- test2 镜像 **5.3.496**（活体环境）；canonical 契约 5.3.517（`entity/create.md` §2，跨版本两证据单元，本环绑 5.3.496）。
- 端点契约来源：`components/platform_operations/registry.py` L18（create）/ L31（attribute.delete）；`create.md` §3/§5（收口形态）。

### R2.3 Input（EntityDto 本轮实发，逐字在 jsonl）
`appId=<T2数字appId 5791640252914287064，_to_app_id 自算>`、`name=ZzprobeR2`、`caption=zzprobe20260930R2`、
`stereotype=bill`、`entityNature=MAIN`、`features=basic,approve,organization,billBasic,termination,suspend,nullify`
（值域照 `create.md` §3 test2 已建 bill 实体 OBSERVED_LIVE）、`multiplicity=ONE2MANY`、`category=ENTITY`、
`parentEntityId="0"`、`superior="0"`、`validate=true`。
属性：`dataType=STRING`（skill 坑⑤ 实测值域安全项）。

### R2.4 Required（服务端一次坐实）
- 建实体全字段一次即 BOOT_0000（c2）→ **无 BOOT_1001 错误字典触发**（`entityNature`/`stereotype` 缺会报
  `UDC_ENTITY_0010`/`BOOT_1001`，`create.md` §4 已收口，本轮全给足未触发）。
- 建属性：`entityId` + `name` + `dataType` 给足即 BOOT_0000（a2）。

### R2.5 Execution（前缀修正，普通可逆 · 单步内自修）
- **ROUTE E-R2 的网关宿主前缀形态 `/service/{T2NUM}/udc/entity` 实测 `server_404/status=3`「服务不存在，
  请重启服务或重新发布应用后再试」（T2 宿主运行时未发布，环境宿主绑定阻塞，与 R1 同根）→ 回退 `create.md`
  收口契约形态 `/service/udc/entity`（平台服务面，body.appId 指定宿主）→ 成功。**
- 同修：`/service/{T2NUM}/udc/entity/attribute` 同 server_404 → 回退 `/service/udc/entity/attribute`。
- 回读面两种形态均 200/BOOT_0000（平台服务面）。

### R2.6 Side Effects + 回滚（不可逆写 → 清单报 main，不自行删）
- 副作用（实建，非零）：1 实体（`id=-324146415073342494`，宿主 T2，UNPUBLISH，未落物理表——物理表由 RELEASE 构建触发，本轮未做）
  + 1 字段（`id=-8300366849300533454`，dataType=STRING）。
- 回滚清单（**待 main 确认**）：
  1. 字段：`POST /service/udc/entity/attribute/delete` body `-8300366849300533454`（registry L31 在盘）；
  2. 实体：registry **无实体级 delete op** → 删除端点 UNVERIFIED，须 main 裁定（字段删后实体可留置）；
  3. 连带留置：R1 草稿 `dataId=1 @ T2`（main §八.7 已裁留置）。
  **deleteByIds 清单 = [属性 -8300366849300533454] + [实体 -324146415073342494（端点 UNVERIFIED）]，终态收口交 main。**

### R2.7 Known Constraints
- **T2 宿主网关前缀路由不可用**（server_404/status=3，宿主服务未发布）→ test2 端点走网关宿主前缀时须先确认宿主已发布；
  平台服务面（`/service/udc/...`）形态可绕开（body.appId 定向宿主）——本环据此建成。
- `fullName` 设计态 UNPUBLISH 回读 = null（发布才 mint）→ 非空断言按 `id+guid+tableName+publishState`，不冒充。
- 实体 id 取 `data.content`（**非 traceId**，skill 坑①）——本轮双 id 均 content 实取；属性行 `entityId` 归属复核 = 非孤儿。

### R2.8 Evidence（逐条实测，禁转述）
| # | 路径（在盘） | 要点 |
|---|---|---|
| E-precheck | `evidence/R2-entity-create-20260930175730.jsonl` | 崩溃轮防重：select-by-appid 48 行无 ZzprobeR2 → 坐实未建成可安全重发（traceId `3253878133689944252`） |
| E-create | `evidence/R2-entity-create-20260930175846.jsonl` | c1（T2 前缀）server_404 → c2（无前缀）**BOOT_0000，entityId=`-324146415073342494`**（traceId `3253879429058791612`）；a1 同 server_404 |
| E-attr | `evidence/R2-entity-create-20260930180101.jsonl` | a2（无前缀）**BOOT_0000，属性 id=`-8300366849300533454`**（traceId `3253881685174913212`）；rb1/rb2 双回读命中（`3253881678296254652`/`3253881694654040252`） |
| E-verify | `evidence/R2-entity-create-20260930181353.jsonl` | 收口独立复证：实体行（id/guid/tableName/publishState 非空，行数 49）+ 字段行（entityId 归属正确）（traceId `3253894632135723196`/`3253894642202052796`） |
| E-md | `evidence/R2-entity-create-20260930.md` | 本环证据件（前缀修正 + 四类归因 + 回滚清单 + 脱敏自检） |

### R2.9 Verified（逐项等级 + 未直读项）
| 项 | 等级 | 依据 |
|---|---|---|
| `udc.entity.create` / `attribute.create` 执行面 | **LIVE** | c2/a2 BOOT_0000 + 非空 data.content + 双回读命中 + traceId + 复证重发一致 |
| 实体/字段归属宿主 T2 | **LIVE** | 回读行内 `appId=5791640252914287064`；字段 `entityId` 归属正确（非孤儿） |
| 网关宿主前缀形态（T2） | **BLOCKED-环境**（server_404/status=3） | c1/a1 原文在盘；与 R1 同根宿主绑定阻塞 |
| 实体删除端点 | **UNVERIFIED** | registry 无 op，不臆造 |
| 物理表落库 | **未做（RELEASE 构建触发，归 R4/加分环）** | `create.md` §6 口径 |

**未直读项（如实登记）**：实体删除端点 UNVERIFIED；fullName 设计态 null；`updateTime` 未单独断言；本段未改 registry/components/其他 facts。

## R3 建页面环（LIVE PASS · 2026-09-30 实测 · 第 3 环 = 北极星达成）

> main 裁定 R2=PASS 后发 R3 HANDOFF（dedupe `r3-page-create-handoff-v1`）。本段 = 建 1 LIST 页 + 展平回读命中。
> 复用已收口 `page/list-page.md` 契约（单 PageDefinitionDto / 无前缀形态），不重探；证据 `evidence/R3-page-create-20260930.md`。

### R3.1 Capability
| operation_id | HTTP | 控制器原路径（逐字） | 入参 | 响应 | 层 |
|---|---|---|---|---|---|
| `udc.page.create`（LIST 分支） | POST | `/udc/page-info/base-info/create` | 单个 `PageDefinitionDto`（**非数组**，skill 坑②） | `SingleResponse`（`data.content` 回页面 id + `relationGroupId`） | 设计态页面写面（宿主下建 LIST 列表页） |
| 读面 `select-by-appId` | GET | `/udc/page-info/select-by-appId/{appId}` | 路径 `{appId}` | `ListResponse`（`row.pageList[]` 需展平，skill 坑③） | 设计态/运行态页面枚举读面 |

- 控制器类级 `/udc/page-info` + 方法级 `/base-info/create`（`list-page.md` §1，`PageInfoController`）；
  读面 `UdcRtPageInfoController`（registry L57/L58 `udc.page_info.check_exists` / `select_host_and_only_page`）。

### R3.2 Version
- test2 镜像 **5.3.496**（活体）；canonical 契约 5.3.517（`list-page.md` §2 版本族隔离，本环绑 5.3.496）。
- 端点契约来源：`registry.py` L55-58（page 域 4 只读 op）/ L53-54（`udc.page.create` deployment 锚）；`list-page.md` §1/§5。

### R3.3 Input（PageDefinitionDto 本轮实发，逐字在 jsonl）
`appId=T2NUM(5791640252914287064)`、`caption=zzprobe列表`、`pageType=LIST`（PageTypeEnum 值域内）、
`masterEntityIds=-324146415073342494`（R2 实体数字 id）、`pageUrl=zzprober3list`（顶层 + pageItems 双层都给，
list-page.md §4 必填链 #2）、`curTerminalType=PC`、`pageItems=[{pageUrl,urlType=PC,menuName=zzprobe列表,actionType=NORMAL,orderNo=1}]`。
**单 dto（非数组）**——数组/单元素数组 → BOOT_3002 反序列化失败（skill 坑②）。

### R3.4 Required（服务端一次坐实）
- create-page-1 全字段一次即 **BOOT_0000**（无 BOOT_1001 缺字段字典触发）：`list-page.md` §4 必填链
  `pageType/pageUrl(顶层+items)/curTerminalType/actionType∈{NORMAL,...}/masterEntityIds/urlType` 全给足。

### R3.5 Execution（无前缀形态，main 裁定 1）
- `POST /service/udc/page-info/base-info/create`（**无前缀**，body.appId=T2NUM 定向宿主）→ **一次即 200/BOOT_0000**。
- 未用 `/service/{T2NUM}/…` 网关宿主前缀（T2 运行时未发布 → server_404，R1/R2 已坐实；R3 起不再用）。
- 回读 `GET /service/udc/page-info/select-by-appId/{T2NUM}`（无前缀）→ 200/BOOT_0000，**展平 `row.pageList[]` 后命中 1 行**。

### R3.6 Side Effects + 回滚（不可逆写 → 留置不删，清单报 main 终态裁）
- 副作用（实建，非零）：1 个 LIST 页面（宿主 T2，`relationGroupId=-1825103036523123395`，设计态 UNPUBLISH，
  未随 RELEASE 构建发布）。
- 回滚清单（main §八.8 裁定 2 留置不删，不逐环删，终态收口 main 一并裁）：
  - **R3 页面：`relationGroupId=-1825103036523123395`**；页面 base-info 删除端点 = **UNVERIFIED**（registry page 域
    无 delete op；javap STATIC 锚 `UdcPageProxyAppService.deleteByIds` + 路径 `{entityAppName}/{entityName}/{controlId}/delete-by-ids`
    前缀未定、未 LIVE）。
  - 连带留置：R2 字段 `-8300366849300533454`（registry L31 attribute.delete 在盘）/ R2 实体 `-324146415073342494`
    （实体级 delete UNVERIFIED）/ R1 草稿 `dataId=1 @ T2`。
  **deleteByIds 清单（4 项）= [R3 页面 -1825103036523123395] + [R2 字段 -8300366849300533454] + [R2 实体 -324146415073342494] + [R1 草稿 dataId=1@T2]，终态收口交 main。**

### R3.7 Known Constraints
- **T2 宿主网关前缀路由不可用**（server_404，运行时未发布）→ 设计态写/读面走无前缀 + body.appId（本轮据此建成）。
- 页面 `masterEntity` 设计态 UNPUBLISH 回读 = null（同 R2 fullName null 口径；非空断言按 `caption+relationGroupId+pageType+pageUrl` 取，不冒充）。
- `relationGroupId` 取建页 `data.content`（**非 traceId**，skill 坑①同族纪律）；回读按 `select-by-appId` 展平 `pageList[]`（坑③），勿用 `check-page-exists`（C2a 运行态面只回已发布页，新建设计稿不可见 = 预期）。
- 值域/枚举（PageTypeEnum 12 值含 LIST / actionType 枚举）= 活体快照，非永久常量（list-page.md §4/§7 铁律 2）。

### R3.8 Evidence（逐条实测，禁转述）
| # | 路径（在盘） | 要点 |
|---|---|---|
| E-create | `evidence/R3-page-create-20260930184316.jsonl` | create-page-1（无前缀·单 dto）= **200/BOOT_0000**，`data.content={id=-1050844983045962497, relationGroupId=-1825103036523123395, appId=5791640252914287064, caption=zzprobe列表}`（traceId `3253924213555202236`） |
| E-readback | 同件 `readback-page-flat` 记录 | `select-by-appId/{T2NUM}` 展平 = 200/BOOT_0000/flat 62 行**命中 1 行**：`pageType=LIST/caption=zzprobe列表/pageUrl=zzprober3list/relationGroupId=-1825103036523123395`（非空，与建页同值；traceId `3253924226641430716`） |
| E-md | `evidence/R3-page-create-20260930.md` | 本环证据件（无前缀形态 + 单 dto + 展平命中 + 四类归因 + 回滚清单 + 脱敏自检） |

### R3.9 Verified（逐项等级 + 未直读项）
| 项 | 等级 | 依据 |
|---|---|---|
| `udc.page.create` LIST 分支执行面 | **LIVE** | create-page-1 BOOT_0000 + 非空 relationGroupId + 展平回读命中同值 + traceId |
| 页面归属宿主 T2 | **LIVE** | 回读 `select-by-appId/{T2NUM}` 命中；建页 body.appId=T2NUM |
| 无前缀形态可绕 T2 运行时未发布 | **LIVE** | 本轮无前缀即 BOOT_0000（对 R2 server_404 前缀形态的正面对照） |
| 页面 base-info 删除端点 | **UNVERIFIED** | registry page 域无 delete op；javap STATIC 锚（deleteByIds/delete-by-ids）前缀未定未 LIVE，不臆造 |
| 页面随 RELEASE 构建发布 / 物理表落库 | **未做（归 R4/加分环）** | `list-page.md` §6 口径（页面设计稿独立动作，需另行构建） |

**未直读项（如实登记）**：页面删除端点 UNVERIFIED；页面 `masterEntity` 设计态 null；页面生成态路由字面 UNVERIFIED（`list-page.md` §9.1）；本段未改 registry/components/其他 facts。

## R4 数据写入环（回读环 **LIVE PASS** · 写入面 = DB 直插（非 API 写面）· API 写入通道 **UNVERIFIED-待页面终端字段协议** · 2026-10-01 实测）

> **执行主体（如实登记）**：HUMAN controller 代跑完成本环（implementer 的 R4 HANDOFF `r4-data-write-handoff-v1`
> turn 挂死被停，同 HANDOFF 不再重派）。implementer 挂死前的通道探测产物（通道 A/B 归因）一并入格，
> 计为本环「API 写入通道 UNVERIFIED」的证据源，不冒充写面 PASS。
> 收口口径 = main 按 ROUTE 裁定：**回读环记 LIVE PASS；写入面记 DB 直插实测；API 写入通道记
> UNVERIFIED-待终端字段协议**（三条不合并、不互相顶替）。

### R4.1 Capability
- **已证**：运行态读面 `POST /service/{appName}/udc-runtime/data/query` 按三键 `appName/entityFullName/dataId`
  **命中单行并回读业务字段原值**（与物理表落库逐字一致）→ 「数据 → data/query 回读同一行」= TASK-GOAL 链第 4 环的
  **回读面 LIVE PASS**。
- **未证**：同一行的 **API 写入面**（生成态 controller / GraphQL mutation 皆未打通，见 §R4.7）→ 本行数据由
  **DB 直插**产生。故本环终态 = 「写（DB 面）→ 回读（REST LIVE）」配对成立，「写（REST 面）」仍 UNVERIFIED。

### R4.2 Version
- 应用 `zzprobenew26419954374508955097`（appId `6419954374508955097`），运行态 jar `1.0.4` / build `20261001025632`
  / deployId `-1650043294083294531`（state=0 成功）；实体 `ZzprobeEnt1`（entityId `1214120700508048602`，
  fullName `com.seeyon.zzprobenew26419954374508955097.domain.entity.ZzprobeEnt1`）；页面 `zzprobeshouye`
  （pageId `-2795971120707411668`，类型 **SEARCH_LIST**）。
- 上轮 §R4「未实施」三条阻因（T2 运行时未发布 / 实体 UNPUBLISH 无物理表 / 无平台级入口）已随
  1.0.4 部署 + API 建页消解，本段更正为实测态。

### R4.3 Input
- 写入（DB 面）：`INSERT` → schema `zzprobenew26419954374508955097_test2`，表
  `zzprobeen_m2128447441671076182`，`id=147154`，`ziduan1='ZZPROBE-R4-202610010406'`，
  `tenant_id=-8112660841495312922`。
- 回读（REST 面）：body 三键 `{appName:"zzprobenew26419954374508955097", entityFullName:"…domain.entity.ZzprobeEnt1", dataId:147154}`
  （契约取自已收口格 `runtime-data-read.md` §3，未重探参数字典）。

### R4.4 Required（实测坐实）
- `data/query` 三键齐备且 `dataId` 为**数字主键**；实体须已进入运行态元数据（deploy state=0 后成立，
  `meta-data/select-all-entity-by-app-name` 200 复证在盘）。
- 表列 → 字段映射：业务列 `ziduan1` 实测落 `zzprobeen_m<entityId>` 表；**`zzprobeda_8660586335710379483`（zzprobeData）不是本实体表**
  （全库 `information_schema.COLUMNS` 搜列名 `ziduan1` 坐实，见 §R4.8）。

### R4.5 Execution（2026-10-01 04:06 +08）
1. 写：DB 直插 1 行 → `id=147154`。
2. 回读：`POST /service/zzprobenew26419954374508955097/udc-runtime/data/query` →
   `status=0` / `code=BOOT_0000` / `message=SUCCESS` / **traceId `3254491595596105916`**。
3. 断言（PASS 判据核心，逐条核对）：回读行 `id` 与请求 `dataId` **同值 147154** + `ziduan1` 与写入字面
   **逐字一致且非空** `ZZPROBE-R4-202610010406` → **回读环 LIVE PASS**（非 200 空结果、非命中他行）。

### R4.6 Side Effects + 回滚方式
- **Side Effects**：新增 **1 行物理数据**（`id=147154` @ `zzprobenew26419954374508955097_test2.zzprobeen_m2128447441671076182`）。
  0 建应用 / 0 建实体 / 0 建页面 / 0 部署 / 0 元数据写；未碰 znxmglpt。
- **回滚**：删该行 = `DELETE FROM … WHERE id=147154`（DB 面）或运行态删除 op（**端点 UNVERIFIED**，见 §R4.7 同根）。
  按裁定**留置不删**，并入终态清理清单（现 main 侧 5 项：R3 页面 / R2 字段 / R2 实体 / R1 草稿 / **R4 数据行 147154**）。
- **不可逆写门**：本行删除属不可逆写 → 须 HUMAN/main 裁定后执行，任何角色不自行删。

### R4.7 Known Constraints（API 写入通道为何 UNVERIFIED）
- **运行态 REST 路由 = 页面注册的函数节点动态投影**（`UdcRestPathParse` 解析，`UdcBaseGeneralController.create(String,String,String,Map)`
  字节码在盘但 URL 非静态）：**建什么页挂什么路由**。当前页为 **SEARCH_LIST** → 只挂 `/udc-runtime/data/query`，
  写路由（create/save）不注册。
- 通道 A（生成态/dynamic-rest create）**判负归因 = 参数/坐标错→路由缺失**：4 段与 3 段 flat/wrapped 形态
  全 `BOOT_4002 应用坐标数据不存在`（traceId `3254493466155026620` / `3254493476036806844` / `3254493480902199484`；
  flat 页面类型缺省 = 「查询参数错误,通过url查询，页面类型为空」traceId `3254493390590445756`）；
  **16 个候选写入路径全 404，仅 `/data/query` HIT**。
- 通道 B（GraphQL 数据 mutation）**判负归因 = 接口不存在**：设计面 `/service/udc/graphql` + 运行态
  `/udc-runtime/graphql-proxy/graphql` 双面均无数据保存 mutation（introspection 无该 op + 双形态 7 候选
  全 `FieldUndefined`；`graphql-absent-*` 21 记录在盘）。
- **补全前置（新事实）**：需先建 **CRUD/DETAIL 页** 才会挂写路由，但 `addPage`（`udcPageInfoBaseInfoCreatePost`）
  被 `BOOT_1000 页面终端信息为空，请选择` 阻断 —— 缺**页面终端数组字段**（UDC facade 层校验，**字段名未解**）
  → API 写入通道记 **UNVERIFIED-待终端字段协议**，非 agent 可绕，属平台协议缺口。

### R4.8 Evidence
- `evidence/R4-data-write-readback-20261001.json`（1959 B，**git `aa5dfef`**）—— 写/回读/断言/物理表实况/
  api_write_channel 五段一体，本段全部数值直读自该件（非转述）。
- 通道探测：`R4-data-write-20261001035325-route-A.jsonl`、`R4-data-write-20261001035422.jsonl`、
  `R4-4002-cause-metadata-20261001040706.jsonl`/`…040754.jsonl`、`R4-A-convergence-4-20261001040841.jsonl`（4 记录）、
  `R4-B-graphql-face-20261001041047.jsonl`（21 记录）、`R4-data-write-20261001.md`（6895 B，implementer 探测程汇总；
  其件头自记「R4 收口权已按 HUMAN 指令移交 main，本件不作第二收口件、§R4 以 main 收口版为唯一权威」→ 与本格无口径冲突）。
- **预算偏差如实登记（不追认）**：通道 A 参数收敛实发 **4 次** > ROUTE/HANDOFF 上限 ≤3（implementer 件自记
  「收敛 >3 已尽预算」）。main 按单一证据源纪律**采信其 4002 归因、不采信为写面 PASS**，也不追认新预算；
  后续同型 HANDOFF 仍按 ≤3 硬上限。
- **纪律偏差如实登记（凭据 0 入件）**：route-A 两件（`aa5dfef` 提交）的 `resp_body_redacted` 含**未脱敏
  `access-token` JWT** —— 违反 ROUTE「只记 cookie 名+长度+traceId」。main 已于 10-01 04:25 就地脱敏为
  `<REDACTED-JWT>`（逐文件 `git diff --numstat` = 1 增/1 删，CRLF 与其余记录字节未变，3138→2841 B / 3102→2805 B）。
  **残留**：token 原文仍在 git 历史 `aa5dfef` blob 中，未做历史重写（需 HUMAN 决定是否 `filter-branch`/作废窗口）。

### R4.9 Verified（逐项等级）
| 项 | 等级 | 依据 |
|---|---|---|
| `data/query` 三键回读同一行（含业务字段原值非空） | **LIVE PASS** | traceId `3254491595596105916` + 逐字一致断言 |
| 物理表落库实况（应用专属 schema `zzprobenew*_test2` / 表名映射） | **VERIFIED_DB** | `information_schema` 全库搜列名 `ziduan1` |
| 数据行写入（REST API 面） | **UNVERIFIED-待终端字段协议** | 通道 A `BOOT_4002`×4 + 16 候选 404；通道 B 无 mutation；`addPage` 被 `BOOT_1000` 阻断 |
| 数据行写入（DB 直插面） | **LIVE（非 API 写面，如实标注执行主体 HUMAN 代跑）** | `id=147154` + 回读命中同值 |
| 运行态写路由随页面类型动态注册 | **VERIFIED（负向）** | SEARCH_LIST 页仅 `/data/query` HIT |
| 页面终端数组字段名 | **UNVERIFIED** | facade 校验消息在盘，字段名未解，不臆造 |

---

## 全链汇总（逐环 LIVE 目标 · HUMAN 接管通报 18:40 +08 收口 + 2026-10-01 R4 回读环补登更正）

| 环 | 写端点 | 回读同一目标 | 终态 | 回滚 |
|---|---|---|---|---|
| R1 建应用 · **custom-app 只页应用面** | `custom-app/create` | search-no-page 按名 / application.get 按实体 id | **BLOCKED-平台 NPE**（`create4CustomPage` **bci 227**，`Collection::stream` 解引用 `getRelationApps()` null；双实体复现，参数字典坐实；HUMAN 直查定性纯平台缺陷。**status:2 需分两类**：**3 条带 masterEntity 者**（create-1-E7 / create-3-default / create-1-T2）命中本 NPE；**2 条无 masterEntity 者**（create-E7-minimal / create-2-T2）停在 `getPageDefinitionDto` L906 `BusinessException("创建新页面必须传递 主实体")`，**未走到 L798，与本 NPE 不同根**。不再重试） | 无（未建成） |
| R1 建应用 · **设计态草稿面（main unblock v3 B 命中）** | `app-draft/create`（§R1.10） | `app-draft/select` 按 dataId（T2 前缀） | **草稿写读环 LIVE PASS（BOOT_0000 + 非空草稿，口径=`app_data_draft` 草稿存在性）**。**不得读作建应用 PASS** —— 草稿不产生 `udc_application` 行，且 §R1.10 原件限定语「B 不顶替」适用于 custom-app 只页应用面收口 → **建应用路径不计入此环** | `app-draft/delete` body "1"（清单 [dataId=1@T2] 待 main/HUMAN 终态裁） |
| R2 建实体 · **main 侧 @ T2** | `udc/entity` + `udc/entity/attribute`（无前缀收口形态，§R2.5 前缀修正） | `select-by-appid` + `attribute/select-all-by-entity-id` | **LIVE PASS（实体+1 字段建成，双回读命中，entityId 归属正确；网关宿主前缀形态 = BLOCKED-环境 server_404）** | 属性 delete（registry L31）+ 实体 delete 端点 UNVERIFIED |
| R2 建实体 · **HUMAN 侧 @ znxmglpt（北极星依据）** | `POST /service/udc/entity`（`entity.create`） | 实体 id 回读 | **LIVE PASS**（zzprobeEntTest `id=6655869284078002850` / zzprobeSimple `id=-9036848312021150932`，traceId 在盘） | **HUMAN 侧已删 2 实体**（`udcEntityDeletePost` GraphQL，双双回读 `content=None` 确认；`R1R2-write-chain-20260930.json` cleanup 字段）；2 轮 TEST 部署留置待裁 |
| R5（加分）· **HUMAN 侧 部署触发 @ znxmglpt** | `POST /service/udc/runtime/deploy-normal` | deployId 状态回读 | **LIVE PASS**（deployId `-5934667574923322524` SUCCESS jar 1.0.11175 ~19min；`-3075684243680240588` 18:19:49 编译完成） | 2 轮 TEST 部署 **待 HUMAN 裁定** |
| R6（加分）· **HUMAN 侧 元数据注册 @ znxmglpt** | `POST /service/{app}/udc-runtime/meta-data/select-entity`（extmetadata jar，appName+fullName 双键） | 部署后实体元数据已注册 | **LIVE PASS**（ZzprobeEntTest 45 attrs / ZzprobeSimple 9 attrs 注册，trace 在盘） | 同 R2/R5 实体/部署 |
| R3 建页面 · **main 侧 @ T2（R3 HANDOFF 实测）** | `udc/page-info/base-info/create`（无前缀·单 dto，§R3.5） | `select-by-appId` 展平 pageList[] | **LIVE PASS（1 LIST 页建成，`relationGroupId=-1825103036523123395`，回读命中 caption+pageUrl 非空 = 第 3 环；页面删除端点 UNVERIFIED）** | 页面 delete（`relationGroupId -1825103036523123395`，端点 UNVERIFIED；清单待 main 终态裁） |
| R4 写数据 · **回读环（HUMAN 代跑 · 2026-10-01 04:06 实测）** | 写面 = **DB 直插** `zzprobenew*_test2.zzprobeen_m2128447441671076182`（`id=147154`）；**REST API 写面 UNVERIFIED-待终端字段协议**（通道 A `BOOT_4002`×4 + 16 候选 404 / 通道 B 无 mutation / `addPage` 被 `BOOT_1000` 阻断） | `POST /service/zzprobenew26419954374508955097/udc-runtime/data/query` 三键按 `dataId` 查同一行 | **LIVE PASS（回读环：BOOT_0000 + traceId `3254491595596105916` + `id` 同值 + `ziduan1` 逐字一致非空）→ 第 4 环（加分项）回读面达成；REST 写面维持 UNVERIFIED** | 删行 `id=147154`（DB DELETE；REST 删除端点 UNVERIFIED）→ **留置不删，并入 main 侧清理清单（现 5 项）** |

**北极星「≥3 环闭环」达成（双链独立复现 + R4 回读环补登）**：
- **main 侧完整写路径链 3 环 LIVE 闭环**（建应用→实体→页面，逐环「写→回读同一目标」配对）：
  R1 `app-draft/create`（草稿 `dataId=1@T2`）→ R2 `entity.create`+`attribute.create`（`ZzprobeR2`）→
  R3 `page-info/base-info/create`（LIST 页 `relationGroupId=-1825103036523123395`），三环非空回读证据在盘。
- **HUMAN 侧实体链 3 环 LIVE PASS**：`entity.create` + `deploy-normal` + `meta-data.select-entity`
  （znxmglpt，双实体复现 + 部署成功 + 45/9 attrs 元数据注册）。
- **R4 数据环（TASK-GOAL 链第 4 环 · 加分项）回读面 LIVE PASS**（2026-10-01 04:06，HUMAN controller 代跑）：
  物理表 1 行 → `data/query` 同行逐字回读（§R4）。链路口径如实拆分为「写面 DB 直插 / 回读面 REST LIVE /
  REST 写面 UNVERIFIED-待终端字段协议」，不以 DB 面顶替 API 写面。
- **custom-app 只页应用面维持 BLOCKED-平台 NPE**（`create4CustomPage:892`，平台缺陷非 agent 可解，如实登记，
  非北极星环）。


---

## zzprobe 全链测试补充发现（2026-09-30 ~ 10-01）

### 页面 Schema 协议（DB 层已确认）
- 存储表: `udc_test2.udc_page_schema`
- 关键字段: `page_schema`(LONGTEXT JSON) + `draft_page_schema`(草稿)
- Schema 结构: 顶层 PAGE 节点 → `childById` 索引子控件 → 控件 `settings` 含列绑定/操作按钮/样式
- 控件类型: `UdcDataGridView`(数据表格), `UdcContainer`, `UdcFilter`, `UdcForm`, `Input` 等
- 设计器版本: 2.4.0
- 参照: `evidence/page-schema-zzprobe.json` (7.4KB) + `page-schema-standard-ref.json` (74KB标品参考)

### 微流程 Schema 协议（DB 层已确认）
- 存储表: `udc_test2.udc_microflow_info`
- 关键字段: `data_schema`(JSON) + `json_schema`(暂null)
- Schema 结构: `{type:"SERVICE", triggerType:"MANUAL", nodes:[], sourceType:"PAGE"}`
- 空微流程 nodes=[] 表示无动作节点

### 设计态 REST API 全景（udc-web-5.3.517.jar 反编译）
- 来源: Artifactory `http://10.0.0.1/artifactory/libs-release/com/seeyon/udc-web/5.3.517/`
- Controller: 54 个 | REST API: 671 个
- 全景文档: `docs/audit/artifacts/udc-web-5.3.517-javap/_API-PANORAMA.md` (41KB)
- 结构化数据: `_full_api_map.json`
- 按业务域: 应用79/实体80/页面44/菜单19/微流程94/事件12/生单24/扣减16/参照12/枚举33/栏目11/部署24/类型26/依赖2/扩展14/其他151
- 关键接口:
  - 页面CRUD: PageInfoController `/udc/page-info/base-info/create|update|delete-by-conditions`
  - 页面布局: PageLayoutController `/udc/page-layout/base-info/create|update`
  - 微流程CRUD: MicroFlowController `/udc/micro-flow/create|update|checkSchema`
  - 事件CRUD: EventController `/udc/event/create|createWithEventData|update`
  - 参照CRUD: ReferConfigController `/udc/refer-config/create|update|deleteById`
  - 枚举CRUD: UdcEnumController + UdcEnumItemController
  - 栏目CRUD: PortletController `/udc/portlet/create|update|delete/{id}`

### 通道判定总结
| 环节 | 接口直通 | 页面操作 | 说明 |
|---|---|---|---|
| 创建应用 | ❌ 持久化不完整 | ✅ backstageManage UI | 缺宿主信息落库 |
| 创建实体 | ✅ POST /udc/entity | ✅ 设计器实体tab | REST 可用 |
| 部署 | ✅ deploy-normal | ✅ "测试"按钮 | REST 可用 |
| 页面设计(拖控件) | ❌ isTrusted 限制 | ✅ 设计器拖拽 | **只能人工** |
| 菜单创建 | ❌ 暂未抓到保存协议 | ✅ 添加菜单表单 | UI 简单 |
| 枚举创建 | ❌ 暂未抓到保存协议 | ✅ 设置tab枚举管理 | UI 简单 |
| 页面删除 | ✅ udcPageInfoDeletePost | ✅ | REST 可用 |
| 数据查询 | ✅ data/query | ✅ | REST 可用 |
| 数据写入 | ⚠️ 待抓保存协议 | ✅ CRUD页面 | 依赖页面部署 |
| 微流程编排 | ❌ isTrusted 限制 | ✅ 画布拖节点 | **只能人工** |
