# UDC BI 域只读契约 — 域真空（VACUUM）负证据契约

- 域模块: udc-bi（BI / 报表 / 可视化）
- 版本单元: 5.3.517（本地 Maven `<MAVEN_REPO>\com\xiaozhua`，只读离线证据）
- 证据等级: VERIFIED_STATIC_BYTECODE（类名层扫描计数 + 端点路径字面量层 219 行逐条判定 + 38 类 `javap -p -v`）+ OBSERVATION（常量池邻近词汇层 / 构件层 / customer-web 反编译腿，均为旁证，不升级）
- 生成: implementer · 依据 main/ROUTE.md
- 会话引用基点（R3 补，供本契约内 `main/ROUTE.md`、`main/NEEDS-HUMAN-ganttchart-scope.md` 这类会话内引用可解析）: 协作会话根目录 = `<COLLAB_ROOT>\agent-collaboration\session-20261008-121739-4f41b8ca\`（上述两件相对该目录解析；仓库内件相对 `<XIAOZHUA_AGENT_ROOT>\` 解析；同域证据件相对 `docs\audit\artifacts\udc-bi-5.3.517\` 解析）
- 修订记录: R2/R3/R4（前序会话）加入 customer-web 腿与构件层腿 → **R2 收口（前一轮，依 main/ROUTE.md R2 §3）**把负证据升级为三层并改写扫描方法口径，输入即 R1 产出件 `docs/audit/artifacts/udc-bi-5.3.517/bi-endpoint-literal-scan.md` → **R3 收口修补（本轮，依 main/ROUTE.md R3 §3）= 0 新增扫描、0 取证、0 结论变更，只修证据引用闭包**: D-1 L-A 腿脚本/原始计数断链（三件自归档会话落入本域证据目录并记 sha256+来源）、D-2 脚本枚举 5→6（补 `r1_bi_judge.py`）、D-3 `components/platform_operations/models.py` 行号统一口径、D-4 追加第二条抽查锚 `UdcBaseGeneralController`（数字逐字取 main 实测）

## 结论（唯一判定）
**UDC 5.3.517 域内 0 条真 BI 只读契约（operation count = 0）—— 完备负证据，非"未找到"。**
判定性质 = **VACUUM（域真空）**：在 6 个 UDC 5.3.517 jar（1217 个 class，.class 条目口径含 `$` 内部类；仅顶层类去 `$` = 1111）上按 13 个 BI 关键词做宽口径扫描、逐条排除伪命中后，不存在任何一条可证据化的「真 BI 域只读 controller/服务」。本契约以负证据形式固化该结论，供后续 UDC-MERGE 任务照抄（本域不新增任何 UdcOperationContract 条目）。

### 结论的证据层级（R2 收口：由单层升级为三层，结论行不变）
| 层 | 口径 | 覆盖量 | BI 判定结果 | 证据等级 |
|---|---|---|---|---|
| L-A 类名层 | 1217 class FQCN × 13 BI 关键词宽口径子串 → 逐条排除伪命中 | 1217 class | 真 BI controller/服务 = **0**（唯一 `bi` 子串 29 条全为 biginteger/bill/biz/scalability/combination/compatibility 及 `BiLinkedList`） | VERIFIED_STATIC_BYTECODE |
| L-B 端点路径字面量层 | **219 行逐条判定**（类级基路径声明 35 条 + 方法级 184 条），路径取注解 `path`/`value` element_value 原值 | 6 jar / 1217 class 全量 → mapping-bearing 类 **38** 个（customplan 6 + dataflow 5 + runtime 27；common/facade/lowcode = 0） | **CANDIDATE(真 BI) = 0**；PSEUDO-EXCLUDED = 4（全部为 `stat` 词干被 state/status 包含）；EXCLUDED-NO-BI-STEM = 215 | VERIFIED_STATIC_BYTECODE（38 类 `javap -p -v` 落盘 + class_sha256） |
| L-C 常量池全量层 | 1217 类的**全部**常量池 Utf8（含中文）逐条 BI 词干扫描 + 伪命中族过滤 | 1217 class | BI 邻近词干命中 **84 条**，其中**属于 mapping-bearing 类的 = 0 条**（即 84 条全部落在非 controller、非端点声明位） | VERIFIED_STATIC_BYTECODE（扫描计数）；其**语义判读**为 OBSERVATION，见「域边界」段 |
| 双口径一致性 | L-B 的自实现常量池/注解解析器结果 vs `javap -p -v` 已解码文本独立再提取的 (annotation, path, method) 集合等值比对 | 38/38 类 | **mismatch = 0** | VERIFIED_STATIC_BYTECODE |

- 三层各自独立可复算，且 **L-B 的 219 行覆盖了全部 mapping-bearing 类，无缺口**（L4 完备性查 A: `@RestController` 类 35 个全在 bearing 集内，缺口 0；bearing 38 − RestController 35 = 3 个无 stereotype 的基类 = `UdcBaseGeneralController` / `UdcReferController` / `UdcBaseAppInfoController`，已计入端点表；L4 查 C: bearing 类中 `@interface` = 0 → 不存在自定义 meta-annotation 声明映射的盲区）。
- 数字对账（main 已独立复算通过，ROUTE R2 §1）: 1217 class / 38 mapping-bearing（6+5+27，其余 0）/ `@RestController` 35 全落在 bearing 内且差值 3 = 上述三个无 stereotype 基类 / 219 行 = 35 类级 + 184 方法级（路径串计数 220 的差值 = `UdcBaseGeneralController` 两行各含 2 条路径、`FilterPlanController` 一行含 0 条路径）。
- **结论行仍为「真 BI 端点命中 = 0 → VACUUM」，三层只是把负证据的完备性从类名层升级到端点层与常量池层；本轮未新增任何扫描动作。**
- 证据件: `docs/audit/artifacts/udc-bi-5.3.517/bi-endpoint-literal-scan.md`（L-B/L-C 全量表与逐类 provenance）+ 6 个可复跑脚本 `r1_scan_mapping_bearing.py` / `r1_extract_endpoints.py` / `r1_javap_dump.py` / `r1_completeness_checks.py` / `r1_build_report.py` / `r1_bi_judge.py`（均在 `docs/audit/artifacts/udc-bi-5.3.517/`） + 原始计数 `r1_step1_raw.json` / `r1_step2_endpoints.json` / `r1_step3_dump_report.json` / `r1_step4_bi.json` / `r1_step5_completeness.json` + 38 个 `r1-<Class>.javap.txt`。


## 7 要素（负证据形式）
| 要素 | 取值 | 说明 |
|---|---|---|
| 1. operation_id | **(none — 真空)** | UDC 5.3.517 域内无可登记的 BI 只读 operation；0 条 |
| 2. HTTP method | (n/a) | 无对应 controller，无 HTTP method 可提取 |
| 3. 控制器原路径 | (n/a) | 无 BI controller；故无「原值路径」，亦不涉及网关前缀拼接。注: 本域 5.3.517 全部 219 条端点路径**原值**（35 类级基路径 + 184 方法级）已逐字落盘于 `bi-endpoint-literal-scan.md` §3，其中真 BI 路径为 0 条，未拼任何网关前缀 |
| 4. 参数形态 | (n/a) | 同上，无方法签名可提取 |
| 5. 返回 DTO | (n/a) | 同上，无返回 DTO 可提取 |
| 6. evidence | 见下「证据锚点」 | 6 jar + 版本 + 各 class_sha256 + **三层负证据（类名层 / 端点路径字面量层 / 常量池全量层）+ 双口径一致性** + 扫描方法与计数 + 伪命中排除 |
| 7. LIVE 回读条件 | 见下「LIVE 回读条件」 | 需 BI 模块 jar / 部署态 / 非 5.3.517 版本单元；**本轮不做** |

### 证据锚点（element 6，完整）
- 证据单元（scope）: 6 个 UDC 5.3.517 jar，本地 Maven `<MAVEN_REPO>\com\xiaozhua`，版本 5.3.517（禁混写相邻 5.3.496 test2 单元）。
  - jar 引用解析规则（R3 补，全文唯一）: 本契约与 `registry-entries.md` 中的 jar **只给文件名**（如 `udc-starter-runtime-5.3.517.jar`），解析方式 = 由下表 6 jar 表 + 版本单元目录 `<MAVEN_REPO>\com\xiaozhua\<artifactId>\5.3.517\<jar 文件名>` 拼接为绝对路径；R3 逐个 `os.path.exists` 实测 = 6/6 命中（例: `<MAVEN_REPO>\com\xiaozhua\udc-starter-runtime\5.3.517\udc-starter-runtime-5.3.517.jar`）。
  | jar | 字节 | class_sha256（整 jar 实测，python哈希==sha256sum==Maven.sha1 三向一致） |
  |---|---|---|
  | udc-common-5.3.517.jar | 718566 | 30085724949703b1c2f96a37e72813a6ed9e7b752ebc206c7a47d26afceb30d7 |
  | udc-facade-5.3.517.jar | 66490 | 7e531005de3b94aaaa0ac847328551eaf6e014d743cedf5b79d4bab4769c6501 |
  | udc-starter-customplan-5.3.517.jar | 248550 | 3cba01b314bfae2d8949f21a5dbc6b3e7e4698928bbcb43e43b29439b61659f7 |
  | udc-starter-dataflow-5.3.517.jar | 286897 | ddf664e833ad84c38ad703183ca1d39d2afc1c55f7756e26abef7ef0124148a8 |
  | udc-starter-lowcode-5.3.517.jar | 292500 | 51d1a5e048623f5c26e41d8b5cd605c0adb3321ca4d0919b4ff598c12983cf16 |
  | udc-starter-runtime-5.3.517.jar | 861880 | 74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f |
- 扫描方法（可复现）—— **R2 按 main/ROUTE.md §2-①②④ 采纳后的口径改写**:
  - **口径 ①（路径取值）**: 端点路径 = 注解 `path` / `value` **element_value 原值**（多条以 ` | ` 分隔，未做拼接），并以「常量池中以 `/` 开头的 Utf8 字面量」**兜底**补漏。**不得**只用「常量池里所有以 `/` 开头的字面量」作唯一口径 —— 实测本单元**类级基路径全部无前导 `/`**（如 `udc-runtime/personal-plan`、`node-info`），方法级则前导 `/` 混用，只按 `/` 开头筛会漏掉全部类级基路径。
  - **口径 ②（筛类）**: mapping-bearing 类**按映射注解的描述符筛**，即 class 原始字节常量池内含 `Lorg/springframework/web/bind/annotation/{RequestMapping,GetMapping,PostMapping,PutMapping,DeleteMapping,PatchMapping};` 之一 → **38 类**。**明确记录: 按 `@RestController` stereotype 筛类只有 35 类，会漏 53 行端点**（`UdcBaseGeneralController` 38 行 + `UdcReferController` 14 行 + `UdcBaseAppInfoController` 1 行，三者为 `proxy.controller` 包下的具体父类、无类级 `@RequestMapping`、无 stereotype，其方法级映射由子类继承生效）。后续会话若按 stereotype 口径重扫得出「覆盖不全」的结论即为口径错误。
  - **口径 ③（判定）**: 宽口径先收再逐条排除；收词（对路径原值 / 类级基路径 / 类名三处同时、不区分大小写子串匹配）= `report board analys dashboar chart visuali kpi olap cube stat metric pivot dataset aggregat dimension measure summary baobiao kanban fenxi tongji zhibiao weidu huitu` + 中文 `报表 看板 图表 统计 分析 指标 维度 度量 透视 大屏`；排除族 = `bill biz biginteger integer scalability combination compatibility status state static station statement bootstrap habitat administrator`。
  - **口径 ④（工具链要求）**: `javap` **必须**带 `-J-Dstdout.encoding=UTF-8`，否则中文注解值在本机输出为乱码、路径/枚举原值不可读。工具链实测: `javap = C:\Program Files\Java\latest\jdk-21\bin\javap.exe`（21.0.10，不在 PATH，用绝对路径）；python 入口 = `py`（3.11.9，`python`/`python3` 均不存在）。
  - 类名层（L-A）: 对 6 jar 全量列出 1217 个 class 全限定名（.class 条目口径含 `$` 内部类；仅顶层类去 `$` = 1111；python `zipfile` 读目录 = unzip -l 只读等价；本机 unzip 为 busybox 版恒 RC=1/0B 故用 python），按 13 关键词不区分大小写子串扫描（先宽后窄），逐条排除伪命中。脚本=`docs/audit/artifacts/udc-bi-5.3.517/bi-scan.py`（3949 B，sha256 `54049b7075cebb103babc9085890344993bb2349b1954194b664556124754111`）、`docs/audit/artifacts/udc-bi-5.3.517/bi-dump.py`（624 B，sha256 `e2674ba8c4a852e1359b7d1d65017a178f685a895c18ded79fc120c41b08b18e`），原始计数=`docs/audit/artifacts/udc-bi-5.3.517/bi-scan-raw.json`（7097 B，sha256 `88f1491362a50d1a6729f158cc5e69c5a4965c5a3ca0424cc85c1614bdb56584`），判定报告=`docs/audit/artifacts/udc-bi-5.3.517/bi-domain-scan.md`。**副本来源 = 归档的前序会话目录 `<COLLAB_ROOT>\agent-collaboration\archive-20260925\session-20260917-215537-c54e89d7\`（L-A 腿的原始执行处）；本会话根目录从未有这三件，R3 依 main 裁定把副本落入本域证据目录，本轮未重新生成、未重跑 L-A 扫描 = OBSERVATION。副本内容核对（仅结构、未改任何计数）: `bi-scan-raw.json` 顶层键 = 6 个 artifactId（udc-common / udc-facade / udc-starter-customplan / udc-starter-dataflow / udc-starter-lowcode / udc-starter-runtime），与上「6 jar 表」一一对应；`bi-scan.py` 自述 = 只读 5.3.517 BI 域扫描（sha256 + class 清单关键词宽窄口径），`bi-dump.py` 自述 = 从 `bi-scan-raw.json` 导出逐关键词命中清单。**
  - 端点路径字面量层（L-B）+ 常量池全量层（L-C）+ 双口径核对: 分四层可复算（L1 按描述符筛类 / L2 自实现 JVMS 常量池 + `RuntimeVisibleAnnotations` 解析取 `path`·`value`·`method` 原值 + `/` 开头串兜底 / L3 逐类 `javap -J-Dstdout.encoding=UTF-8 -p -v` 独立再提取并做集合等值比对 / L4 完备性三查 = stereotype 覆盖 · 1217 类全常量池 BI 词干 · bearing 类内 `@interface` 盲区）。脚本（**6 个**，均在 `docs/audit/artifacts/udc-bi-5.3.517/`）= `r1_scan_mapping_bearing.py`、`r1_extract_endpoints.py`、`r1_javap_dump.py`、`r1_completeness_checks.py`、`r1_build_report.py`、`r1_bi_judge.py`（自述 =「R1 步骤4: 生成端点全量表 + BI 语义判定」，是 `r1_step4_bi.json` 的生成者，即口径 ③ 伪命中判定规则的源头）；原始计数 = 同目录 `r1_step1_raw.json` / `r1_step2_endpoints.json` / `r1_step3_dump_report.json` / `r1_step4_bi.json` / `r1_step5_completeness.json`；判定报告 = `docs/audit/artifacts/udc-bi-5.3.517/bi-endpoint-literal-scan.md`；38 个类的 `javap -p -v` 原始输出 = 同目录 `r1-<Class>.javap.txt`（每件头部 provenance 含 `source_jar` / `source_jar_path` / `jar_sha256` / `class_fqcn` / `class_entry` / `class_sha256` / `class_bytes` / `command` / `exit_code` / `run_at_utc` / `evidence_level`）。
  - 单条抽查锚（main 已独立复现，逐字一致）: `com.seeyon.boot.starter.customplan.controller.PersonalPlanContoller`，class_sha256 = `fcc303109b58300eb790efd4f18fdb581a4d25e9417bf03f03dadb312b0adf41`（5135 B），类级基路径原值 `udc-runtime/personal-plan`，5 条方法级路径原值 `detail` / `detail-list` / `/create-batch` / `search` / `delete-by-ids`。复现命令:
    ```
    "C:\Program Files\Java\latest\jdk-21\bin\javap.exe" -J-Dstdout.encoding=UTF-8 -p -v \
      -cp <MAVEN_REPO>/com/seeyon/udc-starter-customplan/5.3.517/udc-starter-customplan-5.3.517.jar \
      com.seeyon.boot.starter.customplan.controller.PersonalPlanContoller | grep -A3 Mapping
    ```
  - 单条抽查锚 ②（R3 追加，数字 = main 于 `main/ROUTE.md` §1 独立实测给定值，逐字照抄，本会话未重新扫描）: `com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseGeneralController`（`udc-starter-runtime-5.3.517.jar`，jar_sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`），class_sha256 = `19c40f0353d2346bd0e5c374e8e7a79b9268b739f18cc1049435c12b37e664c8`（33434 B）；main 自跑 `javap -J-Dstdout.encoding=UTF-8 -p -v` → **类级没有 `RuntimeVisibleAnnotations`**（attributes 计数 = 1，类声明仅 `extends BaseComponentController`，无 `@RestController`/`@Controller` stereotype、无类级 `@RequestMapping`）；映射注解声明计数 = **38 = 35 `PostMapping` + 3 `GetMapping`**；路径原值形态 `dataflow/{entityName}/{restMappingName}`（**无前导 `/`，且用 `value=` 而非 `path=`**）。
    → 该锚把口径 ①（类级基路径无前导 `/`、取 `value` 原值）与口径 ②（按 stereotype 筛类会漏掉此类）**从文字声明升级为盘上可查的字节码实例**，即对口径 ①② 的独立复证。证据件 = `docs/audit/artifacts/udc-bi-5.3.517/r1-UdcBaseGeneralController.javap.txt`（其 provenance 头的 `class_sha256` / `class_bytes` 与上述一致）。复现命令:
    ```
    "C:\Program Files\Java\latest\jdk-21\bin\javap.exe" -J-Dstdout.encoding=UTF-8 -p -v \
      -cp <MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar \
      com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseGeneralController
    ```

- 命中计数: 12 个 BI 强特征词（report/chart/dashboard/analysis/indicator/kpi/olap/cube/cubegroup/visualiz/statistic/metric）× 6 jar = **0 命中**；唯一有关键词命中的 `bi` 共 29 条（.class 条目含内部类；若另计 `.json` 资源条目则 30），逐条排除=0 真命中：
  - biginteger / integer（数值类型转换类）、bill（单据状态/字段）、biz（MethodBizProxy）、scalability（可扩展字段）、combination、compatibility（货架兼容锁）—— 子串伪命中。
  - **BiLinkedList / BiLinkedList$1**: 经 `javap -p -v` 确认 = `public class BiLinkedList<T> implements Iterable<T>`，Node<T> 双端链表（add/removeFirst/removeLast/getFirst/getLast/iterator），**通用数据结构，非 BI controller/服务**；class_sha256=`b4264d3e4f95cd4477ed4143b72331b8b07055785222ba0fdac30ad5304cc914`，来源 jar `udc-starter-customplan-5.3.517.jar`（sha256=`3cba01b3…`），证据=`docs/audit/artifacts/udc-bi-5.3.517/BiLinkedList.javap.txt`。
- 结论行: 1217 个 class（.class 条目口径含内部类；顶层类去 `$` = 1111）× 13 关键词 → 真 BI 域只读 controller/服务命中 = **0** → VACUUM。
- 命中计数（L-B 端点路径字面量层，R1 全量取证）: mapping-bearing **38 类** / 端点行 **219 条**（35 类级 + 184 方法级）逐条判定 → **CANDIDATE(真 BI) = 0**；PSEUDO-EXCLUDED = **4**；EXCLUDED-NO-BI-STEM = 215。4 条伪命中全部是 `stat` 词干被 **state/status（状态）** 包含，逐条为: `DataFlowRtMappingController.updateMappingState` → `state`、`CustomApplicationController.updateDeployState` → `/update-deploy-state`、`CustomApplicationController.updateUsageState` → `/update-usage-state`、`DynamicJarController.getRequestStatus` → `import/status/{requestId}`（基路径分别 `udc-runtime/data-flow-mapping` / `udc-runtime/custom-app` / `udc-runtime/custom-app` / `udc-runtime/dynamic/jar`）。另 main 以自写更宽词干集独立复核全部 220 条路径串 → 原始命中亦仅 4 条、同属 state/status 族 → 排除后 0。
- 命中计数（L-C 常量池全量层，R1）: 1217 类全部常量池 Utf8（含中文）逐条 BI 词干扫描、排除伪命中族后剩 **84 条**，其中**属于 mapping-bearing 类的 = 0 条**；不带伪命中过滤复核 bearing 类的 `/` 开头常量池字面量得 2 条（`/update-usage-state`、`/update-deploy-state`）与 L-B 端点表完全重复 → 常量池层不存在端点表之外的新路径。84 条的语义判读见下「域边界/邻近词汇」段（OBSERVATION 级）。
- 双口径一致性: L-B 自实现常量池/注解解析器 vs `javap -p -v` 已解码文本独立再提取的 (annotation, path, method) 集合等值比对 = **38/38 类 mismatch = 0**。
- 全部 219 行的语义族落在: 自定义/筛选/个人方案、可扩展字段、BPM 节点信息、数据流与生单规则、推演、低代码运行态实体 CRUD 与表单数据查询、动态 REST 代理（`{entityAppName}/{entityName}/{controlId}` 形态）、序列号配置、动态 jar 部署、应用/页面日志、附件模板、GraphQL 代理、运行环境检查 —— 均为 **UDC 低代码平台自身的建模/运行/运维 API**；不存在报表、看板、图表、可视化、OLAP、指标、维度类端点。

### 域边界 / BI 邻近词汇（OBSERVATION 级，依 ROUTE §2-③ 措辞，不作 FACT）
- **L-C 常量池层观察到的 BI 邻近词汇，其载体是枚举常量、页面导航类型码、schema key 与字段命名常量，无一条以 HTTP 路径字面量形式声明**。可举: `MicroFlowActivityTypeEnum.OPEN_REPORT` / `打开报表`、`PageNavTypeEnum.UDC_CDP_DATA_REPORT`、`ModuleTypeEnum.UDC_CDP_DATA_REPORT` / `UDC_CDP_DATA_DATASET`、`UdcNodeTypeEnum.REPORT`、`PageSchemaUtils.ELEMENT_SETTINGS_DATA_REPORT_ID` / `reportId`、`Names.CUBE` / `ST_DIMENSION` / `ANALYSE` / `AGGREGATE`、`Cache4BpmUtil.SummaryPermission` 族、`UdcRamUsageEstimator.measureObjectSize`、`ComponentConstant.APPNAME_GANTTCHART` / `boot-starter-ganttchart` / `Names.gantt_chart_schema`。完整 84 条清单见 `bi-endpoint-literal-scan.md` §5 与 `r1_step5_completeness.json` 的 `checkB_pool_bi_hits`。
- **据此可说明（仍为 OBSERVATION，不是 FACT，未做 LIVE）**: 报表 / 数据集在 5.3.517 字节码里是**被引用、被导航的对象类型**（枚举值、导航类型码、schema 字段名），**本 6 jar 内不存在针对它们的端点声明**。这与既有 VACUUM「本域无 BI 模块」判定同向，不构成反例。
- **禁止升级**: 不得把本段写成「BI 承载模块位于外部/其他构件」—— 那是 HYPOTHESIS，本任务无证据支撑（未取证外部构件、未做 LIVE、未确证运行时装配）。
- **边界条目 · ganttchart（OBSERVATION，依 ROUTE §1.1 给定事实，本轮未取证端点）**: 本地 Maven 存在 `com/seeyon/boot-starter-ganttchart`，**仅 `5.3.260` 一个版本目录**（jar_sha256 `a98863787e97733ea38c2bd57904b4a86dd2db6ada07c968445ac191b2acdbde`，50 个 class，其中 2 个 mapping-bearing 类 = `GanttChartRunningController` / `GanttChartSchemaController`；类级基路径形态 `gantt-chart` / `gantt-chart-schema`；**端点未取证**）。
  - 该构件**不是 5.3.517 证据单元的一部分**，其内容一律不计入本契约的 5.3.517 判定与 219 行端点表。
  - 把 ganttchart 排除出 BI 域，目前**只是名称层（artifactId / 类名）的语义归因**（甘特图 = 项目排程时间轴 widget，非报表/OLAP/可视化分析平台），**不是字节码层或域定义层的取证结论**。
  - 是否把「图表类构件」计入 BI 域定义、以及是否对 `boot-starter-ganttchart-5.3.260` 单独建版本单元取证，**待 HUMAN 裁定**（见会话 `main/NEEDS-HUMAN-ganttchart-scope.md`）。在裁定前本条目永久停留为 OBSERVATION 边界，禁写成 FACT、禁升级为契约。

### LIVE 回读条件（element 7，写清，本轮不做）
若未来需把 BI 契约转正（从负证据转正契约），需满足其一（本离线任务均不可得）:
- 部署态 / 网关可达（`.207` 或对应 service）下对 BI 模块 controller 做 LIVE 回读（identity_matches / 响应非空）——本轮全离线，**禁连网关、禁连 .207、禁 LIVE**。
- 提供 **BI 模块 jar**（本域在 UDC 6 jar 中无 BI 模块；需另指 maven 坐标或本地路径）。
- 提供 **非 5.3.517 版本单元**（如 test2 镜像 5.3.496 的 BI 模块）——属不同证据单元，禁与 5.3.517 混写。
- 交叉证据腿 customer-web-1.0.11029：**反编译证据目录已扫（前序会话 R3），真 BI 域 controller/服务 = 0**（证据 `docs/audit/artifacts/udc-bi-5.3.517/bi-domain-scan-customerweb.md`；100 类中 12 个 BI 强特征词 0 命中，`bi` 子串 18 条全为拼音「表」族/mobile ASCII 伪命中；来源=反编译 .javap.txt，版本单元 1.0.11029，与 5.3.517 严格分开、禁混写）。本地 Maven `<MAVEN_REPO>` 无 `customer-web` jar（OBSERVATION，缺构件不变）→ 本腿用**反编译证据**补齐，maven 构件腿仍待 MERGE 任务另指坐标。
- **BI 邻近载体（图表类构件，如 `boot-starter-ganttchart`）的取证需先由 HUMAN 裁定「图表类构件是否计入 BI 域定义」，并为其单独建立一个版本单元（该构件本地仅 5.3.260，与 5.3.517 禁混写）后再行取证**；在裁定前不属本契约回读路径，也不构成对本判定的反例。

## 范围声明（OBSERVATION，非验收变更）
- 本契约 scope = 6 个 UDC 5.3.517 jar（本地 Maven 证据单元）。
- customer-web-1.0.11029 的 maven jar 不在 <MAVEN_REPO>（磁盘仅存先前会话反编译证据 `docs/audit/artifacts/customer-web-1.0.11029/`，非 5.3.517 maven 单元）→ 不在本任务证据边界内，不作交叉腿强求，仅记入本范围声明。
- 构件（artifactId）层扫描已覆盖（前序会话 R4，**OBSERVATION 级，非字节码证据**）: 本地 Maven `<MAVEN_REPO>\com\xiaozhua` 命名空间 537 个 jar 条目 / **101 个唯一 artifactId**，按 **14 个 BI 特征词**做 substring 扫描 → **得到 6 条子串命中（3×`-biz` + 2×`capability` + 1×`ganttchart`）→ 逐条排除 → 真 BI 构件 = 0**，整体记为 **OBSERVATION 级**。证据 = `docs/audit/artifacts/udc-bi-5.3.517/bi-domain-scan-artifact-layer.md`（含 6 条逐条归因理由）。本腿不改变 5.3.517 主判定（VACUUM / 0 条契约）。
  - **口径纠正（依 ROUTE §1.1，本契约采此表述）**: 此前出现的「全仓 xiaozhua BI 构件 0 命中」说法**过窄** —— 它基于一个不含 `chart` 的关键词集。**构件层的正确表述固定为**「14 特征词 → 6 条子串命中 → 逐条排除 → 真 BI 构件 0（OBSERVATION 级）」，构件层禁用「0 命中」措辞（宽口径确有 6 条子串命中）。
  - 说明（避免与既有锚点混淆）: 上文「命中计数」段里的「12 个强特征词 × 6 jar = 0」指的是 **5.3.517 字节码类名层**的另一项扫描（口径与词集均不同于构件层），属保留的既有锚点，不受本纠正条影响。
  - 同腿另记: `com/seeyon` 113 个 artifactId 宽口径名扫中 BI 形态线索 = ganttchart（已单列为上表 OBSERVATION 边界条目）、graphql（已在 5.3.517 内取证为 `GraphqlProxyController`，见端点层）、3 个 `*-biz`（项目命名噪声）、2 个 `cip-capability-*`（capa·bi·lity 子串）；无 report/board/dataset 形态的 xiaozhua 自研构件。
- 未改任何冻结文件；只读扫描 + javap；路径取注解原值（本域无 BI controller，无路径可提取，故无网关前缀拼接风险；L-B 全量表路径亦逐字未改）。

## 交付三件套索引（TASK-GOAL 三件齐）
1. 本契约（负证据）: `docs/operation-contracts/udc/bi/bi-vacuum-contract.md`
2. javap 证据落盘: `docs/audit/artifacts/udc-bi-5.3.517/` —— `BiLinkedList.javap.txt`（类名层伪命中排除）+ **38 个 `r1-<Class>.javap.txt`（`javap -J-Dstdout.encoding=UTF-8 -p -v` 原始输出，每件含 provenance 头与 class_sha256）** + 判定报告 `bi-endpoint-literal-scan.md`（L-B 219 行端点表 / L-C 84 条常量池层）+ `bi-domain-scan.md` / `bi-domain-scan-customerweb.md` / `bi-domain-scan-artifact-layer.md` + 6 个可复跑脚本（`r1_scan_mapping_bearing.py` / `r1_extract_endpoints.py` / `r1_javap_dump.py` / `r1_completeness_checks.py` / `r1_build_report.py` / `r1_bi_judge.py`）与原始计数 `r1_step1_raw.json` / `r1_step2_endpoints.json` / `r1_step3_dump_report.json` / `r1_step4_bi.json` / `r1_step5_completeness.json`（5 件） + L-A 腿脚本与原始计数 `bi-scan.py` / `bi-dump.py` / `bi-scan-raw.json`（R3 自归档会话 `session-20260917-215537-c54e89d7` 落入本目录，见「扫描方法」段 L-A 行的 sha256 与来源注记）
3. registry 建议: `docs/operation-contracts/udc/bi/registry-entries.md`（0 条 + 真空说明 + 未来补齐证据入口）

## 红线自查（R2 收口）
- 本轮 **0 新增扫描**（无新 jar / 无 ganttchart 取证 / 无新版本单元）；输入即 R1 产出件。
- 领地仅 `docs/operation-contracts/udc/bi/`（本契约 + `registry-entries.md`）+ `docs/audit/artifacts/udc-bi-5.3.517/`；冻结件（`components/platform_operations/registry.py` / `components/platform_operations/layer.py` / `xiaozhua_cli.py` / `tests/**` / `README.md` / `docs/audit/agent-version-audit.md` / `docs/audit/code-reality-audit.md` / 其他域契约目录）零改动；共享件（`core/facts/INDEX.md`、`STATUS.md`、`connector/spi/*`）现盘由其他并发会话改动，本任务未触碰、未回滚、未计入。
- 无 LIVE / 无网关 / 无 `.207`；路径全部取注解原值、未拼任何网关前缀；5.3.517 与 5.3.496 test2、5.3.260（ganttchart）严格分单元，未混写证据。
- 证据等级未越级: L-C 常量池层与构件层、ganttchart 条目均标 OBSERVATION；「BI 承载模块在外部构件」未写成 FACT。
- 契约条目仍为 **0 条**；结论行不变（VACUUM）。


- **边界条目 · ganttchart 指针事实节（R7 追加，2026-10-08；仅指针，不撤销上文）**: 上文原「待 HUMAN 裁定」悬置语句保持原样。HUMAN 已于 2026-10-08 13:56 授权（会话 inbox `evt-1791439622729-37732`）将 ganttchart 作为**独立版本单元 5.3.260** 补扫；取证结论落在 `docs/operation-contracts/udc/bi/ganttchart-5.3.260.md` 与 `docs/audit/artifacts/udc-bi-5.3.260/`（5.3.260 单元 = **非真空**，只读候选 5 条）。**本追加不改变本文件 5.3.517 的 VACUUM 判定，亦禁在两单元间作任何互推。**

