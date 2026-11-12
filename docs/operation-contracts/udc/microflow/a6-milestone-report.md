# 微流程只读里程碑 A6 收口报告（能读什么 / 精确怎么读 / 仍 UNVERIFIED·BLOCKED）

状态：A1/A2/A3/A4/A5 PASS，A6=本报告 → **A1–A6 全达成**（A2 由 UNVERIFIED 升级 LIVE PASS，test2 活体 C1 族 function_node_tree 同一 target 双发 identity_matches=TRUE + 非空 23 节点；证据 live-evidence/a2_live_pass_R21_20260920T113816Z.md + 原生 f1/f2 各 187981B）
仓库：xiaozhua-agent 仓库（活体 HEAD 6598e13f；历史锚点：A3 聚合 commit b6ec36d + 6742ab1 保留注记，不删）。
版本边界纪律：本地 5.3.517（离线反编译）与 test2 部署态 5.3.517（R21 P1 胖包 javap 印证同版本族）分列，不混写；客户 test2 1.0.11133 ↔ 本地 customer-web 1.0.11029 版本差分列（未取 1.0.11133）。证据等级 STATIC_CONTRACT < VERIFIED_STATIC_BYTECODE < LIVE：离线契约族停 VERIFIED_STATIC_BYTECODE，**A2 C1 族 function_node_tree 活体双发已升级 LIVE（LIVE PASS）**。

## 一、能读什么（A1：≥3 条微流程只读契约已入 registry）

registry（components/platform_operations/registry.py default()）本轮新增 3 条 microflow 只读契约
（均为 method=GET、write=False、status=VERIFIED_STATIC_BYTECODE，放行条件 = 契约生效 + GET + 非写 + auth_scope 含 <appId>:readonly）：

| # | operation_id | class（全限定） | method | 路径原文（控制器原值，未拼网关前缀） | 参数 | 响应类型 | 证据来源 |
|---|---|---|---|---|---|---|---|
| C1 | udc.microflow.function_node_tree | com.seeyon.boot.starter.udcrt.controller.UdcFunctionNodeController | selectFunctionNodeTreeMetaData | udc-runtime/meta-data/select-function-node-tree/{appName} | appName (String) | ListResponse<UdcFunctionNodeMetadataDto> | 离线反编译 udc-starter-runtime-5.3.517.jar（docs/audit/artifacts/udc-runtime-5.3.517/） |
| C2 | udc.datatype.get_all | com.seeyon.boot.starter.udcrt.controller.UdcDataTypeController | getDataTypes | udc-runtime/datatype/getAll | 无 | ListResponse<DataTypeDto> | 本地 Maven 仓库 udc-starter-runtime-5.3.517.jar（local-maven-53517，绝对路径不写死） |
| C3 | udc.applog.select_by_id | com.seeyon.boot.starter.udcrt.controller.UdcAppLogController | selectAppDataById | udc-runtime/app-log/datalog/{id} | id (Long) | SingleResponse<UdcEntityMonitorLogDto> | 本地 Maven 同上 |

每条 8 要素 locator 齐备（artifact + version + class + method + 路径原文 + 参数 + 响应类型 + 证据等级），
class_sha256 为 javap 实测 64hex（C1 efd8f914…d7d08a7748 / C2 03b3977b…4854bc38 / C3 f6a2111d…aee775），禁止业务名拼路径。
读取语义：C1 = 微流程功能节点树元数据（按 appName）；C2 = 数据类型列表（无参）；C3 = 实体监控日志按 id（Long 型）。

A5 排除证据：UdcAppLogController 内 5 个 @GetMapping 但语义 destructive 的方法
（deleteAll / clearOrgManager / clearRuntimeDataSource / unloadDynamicApp / setRestEnableLog）已单测断言不入 registry，
写路径维持 POLICY_DENIED（本轮未新增任何写能力）。

## 二、精确怎么读（路径 + 参数 + 返回，含 test2 活体路由事实）

1. 本地 5.3.517 静态契约（registry 登记值，VERIFIED_STATIC_BYTECODE）：上表路径原文。
2. test2 活体网关路由（无凭据 + 凭据双态实测；R21 活体重探 2026-09-20 19:38 CST）：
   - 网关 service 名 = `udc`（活体确证）；`/service/udc-runtime/*` 裸前缀报「udc-runtime 服务不存在」。
   - 【R21 活体 LIVE PASS + 404 根因纠正】微流程 C1（udc.microflow.function_node_tree）活体双发命中：
     完整活体路由 = `/service/udc` + `/udc-runtime/meta-data/select-function-node-tree/{appName}`
     （class-level 前缀 `udc-runtime/meta-data` + method 段 `select-function-node-tree/{appName}`，R21 P1 部署态胖包 javap 实证，见
     docs/audit/artifacts/udc-assemble-5.3.517-deployed/MicroFlowReadPlane.javap.txt，udc-starter-runtime-5.3.517.jar sha8=74ae50bd）。
     **早前批次（R20/R20b）探 `/service/udc/meta-data/select-function-node-tree/{APP}` 404 = 漏写 class-level `udc-runtime/` 段（路径段写错，非未部署）**；
     带 `udc-runtime/` 段重探即 200 命中。
   - C1 双发回读（target=`/service/udc/udc-runtime/meta-data/select-function-node-tree/{宿主 appName，字面脱敏}`）：
     HTTP 200 + 业务 `code=BOOT_0000/SUCCESS`（非裸 HTTP 200）；`data.content` = 函数节点树 **23 顶层节点（非空业务对象）**，
     首节点 identity f1.id=f2.id=23088985804278345；去 traceId + sort_keys 归一化后 `normalized_sha(f1)=normalized_sha(f2)=26ceca1edc115505`
     → **identity_matches=TRUE**。原生 raw：live-evidence/udc_microflow_c1_function_node_tree_f{1,2}_20260920T113816Z.json（各 187981B，audit 可独立重算）。
     摘要件：live-evidence/a2_live_pass_R21_20260920T113816Z.md。
   - C2/C3（udc-runtime/datatype/getAll、udc-runtime/app-log/datalog/{id}）：本轮 P1 javap 实证同 `udc-runtime/` class-level 前缀（非 404 根因段），
     活体双发未在本轮执行（非 A2 必需 ≥1 条判据），C1 LIVE PASS 已满足「≥1 条 test2 LIVE PASS」。
   - 既有 23 条 EntityController 契约的 `/service/udc/entity/...` 路径段在 test2 **可达**：
     `/service/udc/entity/1` → HTTP 200 业务 envelope（BOOT_0000 SUCCESS）；
     `/service/udc/entity/primary/select-root/1` → 200 UDC_ENTITY_0007「Entity does not exist」；
     `search/term` GET → 405（部署态该端点为 POST）；
     `select-by-appid/tree`、`application/{id}` → BOOT_3000（path 变量需 **Long 型** id，
     字符串 applicationId `<appId 字面·脱敏>` 不匹配）。
   - 双发回读 identity 判读：envelope 内 traceId 逐次不同 → 须 traceId 归一后比对 sha；404 页面含 created 时间戳 → 不可用于 identity 判定。
   - 凭据：SSO OAuth 墙（uatsso）由 test2 只读 token 穿透（Bearer + Cookie 双注）；R21 轮新 token（18:16 北京刷新，TK_EXP 见 main/SEEYON-TEST2-ACCESS.md，**已达成 LIVE PASS**，值不复述）。
raw 证据：docs/operation-contracts/udc/microflow/live-evidence/（a2_live_readback_*、a2-entity-pilot.md、a2_entity_pilot_*，sha256 清单见下）。

## 三、哪些仍 UNVERIFIED / BLOCKED 及精确缺口

| 项 | 状态 | 精确缺口（缺一不可） | 解阻路径 |
|---|---|---|---|
| A2 ≥1 条 test2 LIVE PASS | **LIVE PASS**（test2 活体 C1 族 function_node_tree 双发 identity_matches=TRUE + 非空 23 节点；R21 活体重探 2026-09-20 19:38 CST） | 已闭合：①C1 路径段 404 根因 = 早前批次漏写 class-level `udc-runtime/` 段（R21 P1 部署态 javap 实证 `udc-runtime/meta-data/select-function-node-tree/{appName}`），带段重探即 200 命中；②C1 参数实为 **appName（String 型，宿主应用标识）**，非 Long appId（早前「需 Long 型 target」缺口系 entity 域口径，C1 微流程读端点按 appName 查）；③token = R21 轮 18:16 北京刷新新 token 已达成 LIVE PASS（值引用 main/SEEYON-TEST2-ACCESS.md，不复述） | **已解阻**：P1 部署态取证（R21）+ 活体双发（R21）完成；A2 由 BLOCKED/UNVERIFIED → **LIVE PASS**。证据：live-evidence/a2_live_pass_R21_20260920T113816Z.md + udc_microflow_c1_function_node_tree_f{1,2}_20260920T113816Z.json + docs/audit/artifacts/udc-assemble-5.3.517-deployed/ 三件 |
| Nacos 只读旁路（历史缺口②候选解阻路径） | 历史封死事实保留（v1 404 + v2 通道可达但目标配置不存在 + 无枚举端点），**注记：A2 已不依赖 Nacos 解阻** | 目标 Nacos 实例为 **2.x**（实例名/端点脱敏）：v1 Open API 全 404；`/nacos/v2/cs/config` 通道可达（v2 协议响应），但 dataId=<appId 字面·脱敏> × group∈{xiaozhua,DEFAULT_GROUP} × tenant∈{空,xiaozhua-test2,test2,xiaozhua} 全 `code=20004 config data not exist`；v2 console/ns、openapi/configs、v3、actuator 全 404。**A2 现经 P1 部署态 jar + 活体双发解阻，不再走 Nacos 旁路**（历史 Nacos 封死事实保留，不作业务路径） | Nacos 不再承载 A2；历史事实归档。详见 live-evidence/nacos-v2-probe.md |
| P1 部署态取证 | **已完成（R21，P1 独立主线）** | test2 UDC Pod udc-assemble.jar（镜像 5.3.517，与本地静态 5.3.517 同版本族）→ JDK8 ZipFile.getEntry 逐 entry 提 udc-starter-runtime/udc-web 嵌套 jar → javap 微流程读面 Controller；三件落 docs/audit/artifacts/udc-assemble-5.3.517-deployed/（MicroFlowReadPlane.javap.txt 272344B / DEPLOYED-VERSION-NOTE.md / 回执） | 已完成（R21）；证据等级 LIVE-DEPLOYED，印证本地 5.3.517 静态契约 |
| 网关 service 前缀（静态契约路径段 vs test2 实际 service 名） | **LIVE 印证**（service=`udc` + `udc-runtime` class-level 段 + 活体 200 命中） | service 名段 `udc` 活体确证；controller class-level 前缀 `udc-runtime/meta-data` 经 R21 P1 部署态 javap 实证；C1 活体 `/service/udc/udc-runtime/meta-data/select-function-node-tree/{appName}` 200 命中（非 404）。**由 UNVERIFIED 升级 LIVE 印证**（早前「C1/C2/C3 路径段 404」系漏 `udc-runtime/` 段，非未部署） | 已闭合（R21 P1 + 活体） |
| udc design-time 模块（udc-biz/web/assemble/extend 5.3.517） | BLOCKED / UNVERIFIED（既有事实） | 本地 Maven MISSING（docs/audit/udc-design-artifact-availability-evidence.md） | P1 或向业务方索取 artifact |
| A3 聚合（ledger/bundle 输入 + 单测） | **PASS（main 亲自收口，commit b6ec36d + 6742ab1）** | microflow-ledger-inputs/ 7 输入 JSON + evidence-ledger（PARTIALLY_VERIFIED）/ audit-bundle（UNVERIFIED, live_pass=0）CLI 实测 + 聚合单测 | 已完成，无需重建消费 |

## 四、离线收口状态

- A4：全量 pytest **345 passed 0 failed**（main 独立实测；含 C/F/A/entity 四族 34 条只读契约单测 + destructive 排除断言 + A3 聚合单测）；文档计数已同步至 345（README L30 / agent-version-audit L44-45 现值）。
- 单测（8 族全绿）：tests/test_microflow_readonly_contract.py（C1）+ test_datatype_applog_readonly.py（C2/C3 + 排除 5 断言）+ test_flow_readonly_contract.py（F 族 8 条）+ test_application_readonly_contract.py（A 族 5 条）+ test_entity_readonly_contract.py（entity 族 13 条 + 排除 3）+ test_microflow_evidence_aggregation.py（A3 聚合）+ test_metadata_anchor_contract / test_metadata_page_exists_contract（运行态元数据锚点）+ test_udc_contract.py（基础边界），含 3 条 microflow 契约单测 + destructive 排除断言 + A3 聚合单测。
- 写路径：registry 中 6 条写契约维持 POLICY_DENIED，本轮零新增写能力。

## 五、离线只读族收口（R6–R17）

本轮 A6 交付件刷新至 post-R17 活体基线：只读契约族自 R6 三契约时代扩展为 **34 条**离线 VERIFIED_STATIC_BYTECODE 只读契约
（C 微流程 8 + F flow 8 + A application 5 + entity 13），全部 method=GET/POST 读面、write=False、证据等级 VERIFIED_STATIC_BYTECODE（不升级 LIVE）。
活体 registry = 62 operation_ids，其中 readonly(write=False)=56、effective(GET+可验)=25；8 族 family 单测全绿，A4 全量 345 passed 0 failed。
13 条候选未并入归因（避免后续误读）：写侧 3 条 flow write=True → A5 POLICY_DENIED 不纳；跨域端点重复 5 条（menu 域 datalog_list_by_data_id/entity_list ≡ R17 applog.list_app_data_by_dataid/serial.select_entity_list、
page.check_exists ≡ C5 udc.metadata.page_exists_check、page.select_host_only_pages ≡ C4 udc.metadata.page_tree、flow.function_node_tree ≡ udc.microflow.function_node_tree C1）按 R15 C1 删一留一排除；
门控 5 条（page_general.get_cascade_default_value UNKNOWN 降级 + page_refer 3 条 base UNRESOLVED 需 LIVE 反查）维持 human 门控待授权。

口径如实区分（两口径并列）：A1 增量口径 = 34（C8+F8+A5+entity13）；implementer local-maven 全量只读口径 = 37（多 4 条 legacy page_info/page_log 未计入 21 基数）。
权威判据 = 全量 345 passed 全绿 + 34 条 has()==True（main _r18_cross.py 实测）。

## 六、证据清单（docs/operation-contracts/udc/microflow/，sha256 前 16 位）

| 文件 | 字节 | sha256(16) |
|---|---|---|
| candidate-contracts-evidence.md | 6681 | 432a1067d16344a9 |
| local-53517-offline-candidates.md | 3034 | d438457742e65713 |
| gateway-live-facts.md | 3170 | 4deec5bb188be227 |
| live-evidence/a2_readback_20260917T151317Z.md | 1639 | a9992f50155d4139 |
| live-evidence/a2_live_readback_20260917T160331Z.md | 2063 | b8228018215c65d4 |
| live-evidence/a2-entity-pilot.md | 2558 | 72f2c6102ae3ad60 |
| live-evidence/a2_entity_pilot_20260917T172153Z.md | 2852 | d7fb5abc74bee03f |
| live-evidence/*.json（15 份双发 raw） | 107–514 | 见各文件头 |
| live-evidence/a2_live_pass_R21_20260920T113816Z.md | 2970 | 18ba8f9424ab6694 |
| live-evidence/udc_microflow_c1_function_node_tree_f1_20260920T113816Z.json | 187981 | 2a40e10f6c2305e5 |
| live-evidence/udc_microflow_c1_function_node_tree_f2_20260920T113816Z.json | 187981 | 86d40a1735f72bff |
| docs/audit/artifacts/udc-assemble-5.3.517-deployed/MicroFlowReadPlane.javap.txt | 272344 | （P1 javap -v 原文，跨目录证据，audit 独立重算） |
| docs/audit/artifacts/udc-assemble-5.3.517-deployed/DEPLOYED-VERSION-NOTE.md | 6172 | （P1 版本分列 + 胖包提取纪律 + 嵌套 jar SHA） |

跨域去重计数说明（A2 LIVE PASS 不影响既有去重口径）：活体 registry = 62 operation_ids；跨域端点重复 5 条中
`udc.flow.function_node_tree ≡ udc.microflow.function_node_tree C1` 仍按 R15 C1「删一留一」排除（同一读面分域登记，
C1 LIVE PASS 证据复用 udc.microflow.function_node_tree 契约 locator，不新增重复 registry 条目、不重复计数）。
本轮 A2 升级 LIVE PASS **不改变 registry 62 ids / 8 族单测 / a6 345 冻结件**，仅新增活体证据 + P1 部署态证据。

凭据引用脱敏：test2 只读 token 一律引用 main/SEEYON-TEST2-ACCESS.md 路径，凭据值（SY_ACCESS_TOKEN 等）明文不落任何报告/对话/产物。
旧凭据 exp=1789660805 与 09-19 新凭据 exp=1789796648 均已过期（仅记录过期事实不复用值）；R21 轮 18:16 北京刷新新 token
已达成 A2 LIVE PASS（TK_EXP 见 main/SEEYON-TEST2-ACCESS.md，值不复述，脱敏前8 eyJ0eXAi…）。
