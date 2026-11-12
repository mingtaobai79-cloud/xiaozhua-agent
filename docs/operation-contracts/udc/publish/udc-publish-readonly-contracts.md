# UDC publish（发布/部署）域只读契约 — 5.3.517 单 jar 取证（CANDIDATE 1 条 + 写形态 1 条排除）

- 域模块: udc-publish（发布 / 部署 / 应用发布状态）
- 版本单元: 5.3.517（本地 Maven `<MAVEN_REPO>\com\seeyon`，只读离线证据）
- 证据单元（scope）: **单 jar** `udc-starter-runtime-5.3.517.jar`
  （`<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`，
  sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`，861880 B）
- 证据等级: **VERIFIED_STATIC_BYTECODE**（三层扫描计数 + 131 端点行逐条判定 + 51 类 `javap -p -v` 落盘）
  + **OBSERVATION**（域归属语义判读 / 构件边界说明 / Live 面旁证，均不升级）
- 生成: implementer · 依据本会话 `main/ROUTE.md` §1 R1 与 `main/HANDOFF-R1.md`；方法论照抄
  `docs/operation-contracts/udc/bi/bi-vacuum-contract.md`（三层扫描法 + 双口径一致性 + 伪命中族排除）
- 会话引用基点: 协作会话根目录 = `<COLLAB_ROOT>\agent-collaboration\session-20261008-213135-b84a9517\`
  （`main/ROUTE.md`、`main/HANDOFF-R1.md`、`inbox/*.json` 相对该目录解析）；仓库内件相对 `<SEEYON_AGENT_ROOT>\` 解析；
  证据件相对 `docs\audit\artifacts\udc-publish-5.3.517\` 解析

## 结论（唯一判定）
**UDC 5.3.517（本 jar）publish 域 = 非真空，但只读候选全部落在「已登记构建件」上：**
1. **只读候选 CANDIDATE = 1 条** —— `UdcBaseAppInfoController.getDeployInfo`（`GET`，方法级路径原值 `deploy-info`，
   返回 `SingleResponse<String>`，读资源 `app-deploy-info.json`）。本契约以 7 要素形式固化，见下 **C1**。
2. **写形态 WRITE-EXCLUDED = 1 条**（**不入契约，仅标注**） —— `CustomApplicationController.updateDeployState`
   （`POST /update-deploy-state`，入参 `(Long, DeployStateEnum, String)`，写应用发布状态）。
3. **本 jar 内 publish 域再无其他端点形态承载**：类名层 0 个 controller、端点层 131 行中除上述 2 行外
   **0** 行含 publish/deploy 词干、常量池层 38646 条 Utf8 中 publish/deploy 强词干命中**无一为端点路径声明**。
4. **registry 建议 = 0 条新增**：C1 与 registry.py 既有 `udc.application.deploy_info`（L90）/
   `udc.appinfo.get_deploy_info`（L110）**同 class（class_sha256 `deebcc39…`）同 method 同 path 语义**，
   属已登记条目的 publish 域侧等价映射 → 见 `registry-entries.md`（显式「0 条建议 + 去重映射表」）。

## 三层证据（逐层计数 + 判定）
| 层 | 口径 | 覆盖量 | publish 判定结果 | 证据等级 |
|---|---|---|---|---|
| L-A 类名层 | 346 class FQCN × 19 关键词（强 publish/deploy，弱 pub/release/dispatch/topic/channel/emit/notice/announce/broadcast + 中文 8 词）宽口径子串 → 逐条排除伪命中 | 346 class | **controller 类名承载 publish 域 = 0**；唯一命中族 = `event.publisher.*`（7 类，**事件发布器**，非 HTTP 端点承载者）+ `api.DeployNoticeService` / `mq.DeployChangeEventListener` / `dto.CustomApplicationUpdateDeployStateDto`（3 类，服务/监听/DTO 层，**均非 mapping-bearing**）+ `pub`/`publish` 同集（子串关系） | VERIFIED_STATIC_BYTECODE |
| L-B 端点路径字面量层 | **131 行逐条判定**（24 类级基路径 + 107 方法级），路径取注解 `path`/`value` element_value 原值（未拼接） | 346 class 全量 → mapping-bearing 类 **27** | **CANDIDATE(publish 域只读) = 1**（`deploy-info`，GET）；**WRITE-EXCLUDED = 1**（`/update-deploy-state`，POST）；EXCLUDED-NO-STEM = 129；PSEUDO-EXCLUDED = 0 | VERIFIED_STATIC_BYTECODE（27 类 `javap -p -v` 落盘 + class_sha256） |
| L-C 常量池全量层 | 346 类的**全部**常量池 Utf8（含中文，38646 条）逐条 publish/deploy 词干扫描 + 伪命中族过滤 | 346 class / 38646 Utf8 | 强词干命中行 352 条（去重后按词干分组见扫描报告 §L-C）：分布于**方法名**（`publish` / `publishEntityEvent` / `publishBusinessEvent` / `updateDeployState` / `handleDeployNotice`）、**字段/属性名**（`deployState` / `deployType` / `deploy_time` / `deploy_state` / `publishScope` / `publishAfterTransaction`）、**枚举常量**（`PUBLISHING` / `UNPUBLISHED` / `PUBLISH_SCOPE` / `PUBLISH_BUSINESS_EVENT`）、**类型描述符**（`Lcom/seeyon/udc/common/enums/DeployStateEnum;` 等）、**中文提示文案**（"应用发布状态" / "接收到应用发布消息:{}" / "页面数据源信息不存在，请重新发布应用！" 等）；**落在路径字面量形态者仅 2 条**（`deploy-info` 与 `/update-deploy-state`，与 L-B 表完全重合） | VERIFIED_STATIC_BYTECODE（扫描计数）；**语义判读为 OBSERVATION** |
| 双口径一致性 | L-B 自实现 JVMS 常量池 + `RuntimeVisibleAnnotations` 解析器结果 vs `javap -p -v` 已解码文本独立再提取的 (annotation, path 原值) 集合等值比对 | 27/27 类 | **mismatch = 0** | VERIFIED_STATIC_BYTECODE |

- 完备性三查（`r1_step5_completeness.json`）：
  - **查 A**: `@RestController`/`@Controller` stereotype 类 **24** 个 → **全部落在 mapping-bearing 集内，缺口 0**
    （按 stereotype 筛类即可得 24 类；mapping-bearing 口径为 **27** 类，差值 3 = `UdcBaseGeneralController` /
    `UdcReferController` / `UdcBaseAppInfoController` 三个**无 stereotype、无类级 `@RequestMapping` 的具体父类**，
    其方法级映射由子类继承生效 —— 与 BI 先例口径②一致，后续会话若按 stereotype 口径重扫得出"覆盖不全"即为口径错误）。
  - **查 A'**: mapping-bearing 类中 `@interface`（自定义元注解声明映射的盲区）= **0**。
  - **查 B**: 全类常量池「以 `/` 开头」字面量共 **40** 条，其中含 publish/deploy 词干者 **1** 条
    （`/update-deploy-state`，已在端点表内）→ 兜底口径下**不存在端点表之外的新路径**。
  - **查 C**: 见上"双口径一致性"行（mismatch = 0）。
- 证据件: `docs/audit/artifacts/udc-publish-5.3.517/publish-endpoint-literal-scan.md`（L-A/L-B/L-C 全量表 +
  27 类 provenance + 完备性表）+ 51 个 `r1-<Class>.javap.txt`（`javap -J-Dstdout.encoding=UTF-8 -p -v` 原始输出，
  每件含 provenance 头：source_jar / jar_sha256 / class_fqcn / class_entry / class_sha256 / class_bytes / command /
  exit_code / run_at_utc / evidence_level）+ 5 个可复跑脚本 + 3 件原始 JSON 计数（见文末三件套索引）。

## C1 — udc.publish.deploy_info（本契约内识别名；registry 侧见 `registry-entries.md` 去重映射）

| 要素 | 值 |
|---|---|
| 1. operation_id | `udc.publish.deploy_info` —— **本契约内的域定位名**；registry.py 已有等价条目 `udc.application.deploy_info`（L90）与 `udc.appinfo.get_deploy_info`（L110），**本任务不新增 key**（见 `registry-entries.md`） |
| 2. HTTP method | `GET`（javap 原值 `@GetMapping`，annotation 描述符 `Lorg/springframework/web/bind/annotation/GetMapping;`） |
| 3. 控制器原路径 | 方法级路径原值 `deploy-info`（`@GetMapping(value=["deploy-info"])`，**无前导 `/`**）；承载类 `UdcBaseAppInfoController` **无类级 `@RequestMapping`、无 stereotype**；其两个具体子类类级基路径原值 = `{hostAppName}/dynamic-rest/com-seeyon/{currentAppName}/app-info`（`FormAppInfoController`）/ `{currentAppName}/app-info`（`NormalAppInfoController`）。**禁拼网关前缀**；完整路由（子类基路径 + 方法级）的 Spring 继承装配为 **OBSERVATION**，离线不确证（LIVE 需实测） |
| 4. 参数形态 | `java.lang.String currentAppName`；参数注解逐字：`@PathVariable(value="currentAppName")` + `com.seeyon.boot.annotation.ParameterInfo(value="currentAppName")`（javap `RuntimeVisibleParameterAnnotations` parameter 0） |
| 5. 返回 DTO | `com.seeyon.boot.transport.SingleResponse<java.lang.String>`（descriptor `(Ljava/lang/String;)Lcom/seeyon/boot/transport/SingleResponse;`；Signature `(Ljava/lang/String;)Lcom/seeyon/boot/transport/SingleResponse<Ljava/lang/String;>;`）；实参 = `UdcLoadResourceService.getRootJsonData(currentAppName, "app-deploy-info.json")` 的 JSON 文本 |
| 6. evidence | artifact=`udc-starter-runtime-5.3.517.jar`（jar_sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`，<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/）· class=`com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController` · class_sha256=`deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95` · class_bytes=1653 · method=`getDeployInfo` · javap=`docs/audit/artifacts/udc-publish-5.3.517/r1-UdcBaseAppInfoController.javap.txt` · evidence_level=VERIFIED_STATIC_BYTECODE |
| 7. LIVE 回读条件 | **本轮不做 LIVE**。触发条件（三者齐方开火）：① 部署态网关可达且获得授权 token；② 明确 `{currentAppName}` 取值来源（类级基路径含 `{hostAppName}`/`{currentAppName}` 两个路径变量，**离线无法确证**子类继承装配与占位符解析）；③ 回读判据 = HTTP 200 + envelope `BOOT_0000/SUCCESS` + `identity_matches`（同一 currentAppName 双读）+ `data.content != null`（`app-deploy-info.json` 存在）。**禁连网关/禁 .207（本轮全离线）** |

- 复现命令:
  ```
  "C:/Program Files/Java/latest/jdk-21/bin/javap.exe" -J-Dstdout.encoding=UTF-8 -p -v \
    -cp <MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar \
    com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController
  ```

## 写形态（WRITE-EXCLUDED，**不入契约**，仅标注）
| # | 端点 | 判据 | 处置 |
|---|---|---|---|
| W1 | `com.seeyon.boot.starter.udcrt.controller.CustomApplicationController.updateDeployState`；`@PostMapping("/update-deploy-state")`；类级基路径 `udc-runtime/custom-app`；入参 `(java.lang.Long, com.seeyon.udc.common.enums.DeployStateEnum, java.lang.String)`；返回 `SingleResponse<java.lang.Integer>`；class_sha256=`d3e82d8bbc65dc92d5f9d30532159f1d10169f2aef1eae6ab67c70d7ad75ae55`（13271 B，`r1-CustomApplicationController.javap.txt`） | javap 原值；语义 = **修改应用发布状态**（写）；同族 DTO `dto.CustomApplicationUpdateDeployStateDto` | **标注不入契约**（HANDOFF 硬纪律：`publish` 动作本身及 create/update/delete 写形态 → 只标注） |

- 写形态相关的常量池旁证（OBSERVATION，非端点）：`domain/service.CustomApplicationService.publish` /
  `PUBLISHING` / `UNPUBLISHED` / `updateDeployState` / `handleDeployNotice`；
  `appservice.CustomApplicationAppService.updateDeployState`；`entity.CustomApplication.deploy_state`；
  `entity.BaseFormEntity.deploy_time / deploy_type`（DDL 注释 "发布类型(TEST|RELEASE)" / "发布时间"）；
  `mq.DeployChangeEventListener.onDeployChangeEvent` + `api.DeployNoticeService.deployNotice`（部署变更 MQ 通知链）；
  `event.publisher.EventPublisherHelper.publishEntityEvent / publishBusinessEvent`（**框架事件发布器**，与"应用发布"域无关）；
  `enums.MicroFlowActivityTypeEnum.PUBLISH_BUSINESS_EVENT`（微流程活动类型枚举值，非端点）。
  以上均为**方法名 / 字段名 / 枚举常量 / 描述符 / 文案**，无一为端点路径声明。

## 域边界与不扩扫声明（OBSERVATION，非验收变更）
- **本契约证据单元 = 单 jar `udc-starter-runtime-5.3.517.jar`**（任务声明构件）。BI 先例的「6 个 UDC jar」口径在本任务
  按 HANDOFF 放宽为单 jar：**本轮未扫同版本其他 `udc-*` 5.3.517 jar，也未扫 `customer-*` 构件**。
- 本判定**不构成"其他构件无 publish 域端点"的结论**：既有 `registry.py` 已含**跨构件**条目
  `udc.deploy.normal`（L125，artifact=`udc-web-5.3.517.jar`，`POST udc/runtime/deploy-normal`，evidence_level=OBSERVED_LIVE）
  与 `udc.deploy.search_status`（L128，同构件，OBSERVED），**属另一证据单元与另一证据等级**，本任务不引用、不合并、不推断。
- 跨版本禁写：证据仅 5.3.517；本地若存在相邻版本单元（如 5.3.496 test2）**不得**与本单元混写。
- 本 jar 内 publish 域**无 mapping-bearing 类名承载**（类名层 0 controller）而端点层有 1 条只读候选这一组合，
  已在三层表中如实并列；**不扩扫**因任务边界=本构件（HANDOFF 明示），如需扩扫应由 main 重开 HANDOFF。

## 交付三件套索引（TASK-GOAL 三件齐）
1. 本契约（含 C1 只读候选 + W1 写形态排除 + 三层证据）: `docs/operation-contracts/udc/publish/udc-publish-readonly-contracts.md`
2. registry 建议: `docs/operation-contracts/udc/publish/registry-entries.md`（**0 条新增建议** + L90/L110 去重映射表 + 10 字段参照构造）
3. javap 证据落盘: `docs/audit/artifacts/udc-publish-5.3.517/` —— `publish-endpoint-literal-scan.md`（L-A/L-B/L-C 全量表）+
   **51 个 `r1-<Class>.javap.txt`**（含 provenance 头与 class_sha256）+ 5 个可复跑脚本
   （`r1_scan_mapping_bearing.py` / `r1_javap_dump.py` / `r1_completeness_checks.py` / `r1_publish_judge.py` / `r1_build_report.py`）
   + 原始计数 `r1_step1_raw.json` / `r1_step3_dump_report.json` / `r1_step5_completeness.json`（3 件）+ 过程输出 `r1_step1_stdout.txt` / `r1_step2_hits.txt` / `r1_step5_stdout.txt`

## 红线自查
- 写面仅 `docs/operation-contracts/udc/publish/**` + `docs/audit/artifacts/udc-publish-5.3.517/**`；
  其他域目录 / `components/platform_operations/registry.py` / `tests/**` / `seeyon_cli.py` **零改动**（registry 仅只读 grep/import 复核）。
- 无 LIVE / 无网关 / 无 `.207`；路径全部取注解原值、**未拼任何网关前缀**；`publish`/update 等写形态**未混入契约**（W1 段单列标注）。
- 证据等级未越级：域归属语义、Spring 继承装配、构件边界、L-C 语义判读均标 **OBSERVATION**；跨构件/跨版本内容仅作边界声明、未写成 FACT。
- 版本归属 5.3.517 单一；`git` 写操作全禁（主控代提交）。
