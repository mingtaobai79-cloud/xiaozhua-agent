# 余量 62 op 定域 —— 全版本全构件穷尽扫描（第五轮）

> 证据等级：**VERIFIED_STATIC_BYTECODE（大规模）+ BUNDLE_LITERAL**
> 目的：把「余 62 条 `udc*` 未归位 op」从「候选取样扫过」升级为「**已穷尽扫描仍不承接**」。

## 1. 扫描域（本轮建立，远超历轮）

| 项 | 历轮 | 本轮 |
|---|---|---|
| 构件数 | 12（候选）/ 22（归位轮） | **201** 个含 `@RestApi` Controller 的构件 |
| jar 数 | 34（worktree 现成） | **437**（230.3 MB） |
| class 数 | 未记 | **619** 个 distinct `@RestApi` Controller |
| 版本覆盖 | 单一 5.3.517 | **全 `5.3.x`**（12 个 `udc-web` 版本 5.3.314→5.3.517） |

事实源：Artifactory `libs-release-local/com/seeyon`
（`http://10.0.0.1/artifactory`，匿名，与既有约定一致）。
落盘：`<HERMES_HOME>/cache/scratch/bulk/{jars,v496,allvers}/`（jar 不入 git）。
抽取器：`tools/core/extract_component_contracts.py`（**已移入 `_attic_pending/one-off/unsorted/extract_component_contracts.py`**，仓库内已无此路径）（621 controller / 5813 api，5.3.517 面）。

## 2. ★ 穷尽扫描结论：62 条中 0 条归位

三道独立判据，全部为 **0 命中**：

1. **path→op 规则匹配**（含 `BaseComponentController` → `addPathPrefix /udc` 前缀机制）
   - 对 619 个 Controller 全部路径算 op → 余 62 条 **0** 命中。
   - *方法自证*：同一管线对**已验 31 条跨构件归位**跑 **31/31 命中** ⇒ 管线不是空转。
2. **字面量片段扫描**（kebab 化 op 名 / 族名，437 jar 逐 class）
   - 仅 27 条有片段命中，且**逐条查证均为同形不同源**（见第 3 节）。
3. **Controller 类名族扫描**（437 jar，`@RestApi`+`@RestApiOperation` 双注解门）
   - 零 Controller 的族（**8 个族 / 28 条 op**）：
     `CustomDataType`(6) / `PageComponent`(6) / `FormUpgradeDeploy`(7) /
     `MessageCategory`(4) / `MessageLink`(4) / `Pinyin`(1) / `PageAdmin`(1) / `RuntimeUpgrade`(2)
     ⇒ 这些族在**本地 Artifactory 全 5.3.x 里不存在任何 Controller**，
     故不是「换了构件」，而是**构件本身不在本仓库**（在 test2 pod `BOOT-INF/lib` 或加密 `assemble.jar` 内）。

## 3. 27 条「同形不同源」逐条证伪（重点：不得据此归位）

| 余量 op | 片段命中处 | 判定 |
|---|---|---|
| `udcMessageCategory*`(4) / `udcMessageLink*`(4) | `ctp-message-web`（`ctp-message/ctp-message-classification` 等 9 个类级 mapping） | 类级恒为 `ctp-message`，**无** `BaseComponentController`，不叠 `/udc`；`ctp` 前缀规则不成立 ⇒ **非源**（与三轮前结论一致，本轮扩到全版本复证） |
| `udcAffairListPost` / `udcAffairUpdatePost` | `ctp-affair-web`（`ctp-affair/affair-list` 等）、`app-common-web`（`app-common/affair-center`） | 类级 `ctp-affair` / `app-common`，非 `udc` ⇒ **非源** |
| `udcSandbox*`(10) | `boot-starter-sandbox-5.3.289`（`registerName` 未加引号，字典键） | 现有 endpoint 已由 31 条归位表覆盖 22 条；余 10 条在该类**无对应 mapping** ⇒ **非源** |
| `udcRuntimeDeployPost` / `udcRuntimeUpgradeAppListPost` / `udcRuntimeUpgradeHostAppNameListPost` | `udc-starter-runtime` `udc-runtime/*` | 类级 `udc-runtime` = 运行态族，**与设计态 `udc/web`=rpc 调用语义**（`/udc/runtime`）**不可混用** ⇒ **非源** |
| `udcApplicationCopyGet` / `udcApplicationSaveAsPost` | `udc-web::ApplicationController` | 该类**属 udc-web 本体**，但余量口径是「不由 674 端点契约产出」⇒ 是 udc-web **契约漏项**，非跨构件（下一代提取器重活） |
| `udcMicroflowCopy` | `udc-web::MicroFlowController` | 同上一行 |

## 4. ★ 前端侧新证据：loader 契约（补 25 → 32）

`docs/audit/udc-semantics/frontend-op-loader-contract.json`（**机械复算产物**）：
62 条中 **32 条**在 bundle 里找到 loader 证据（历轮 `store_registry` 覆盖 25，本轮 +7）。

**关键结构事实**：前端**从不携带 path** —— 一律
`udcMutationLoader|udcQueryLoader.load({ fieldType: <op>, paramsType, paramsKey, params, queryFields })`。
⇒ ① path 无法从 bundle 得到，只能由 path→op 规则反推（这也是既有归位法的前提）；
   ② 但 `paramsType/paramsKey` **可以直接读**，请求体形状无需臆造。

命名规约 32 条中 **28 条标准**（`<op>InputBody|InputPath|InputQuery`），
**4 条偏离**（与历轮「13 条偏离」同源现象，本口径下 4 条）：

| op | paramsType | paramsKey | 说明 |
|---|---|---|---|
| `udcCtpManagerTransferSelectGet` | `udcBackendComponentSearchAppPostInputBody` | — | 跨 op 复用他人 DTO |
| `udcEnvCurrentEnvGet` | `udcApplicationSearchNewWithVersionListPostInputBody` | — | 同上 |
| `udcSandboxResourcesGet` | `udcSandboxBatchCleanStopPostInputBody` | `body` | 同上（无参 op 却带 body 类型） |
| `udcSandboxClearDataPost` | `String`（标量） | `body` | 标量入参 |

⇒ **构建请求体必须读 `paramsType` 原值，禁止按 op 名臆造 DTO**（已入护栏）。

## 5. 诚实边界

- 62 条仍 **UNVERIFIED**：本轮是**强负面证据**（穷尽扫描不承接），**不是**正面归位。
  「不存在任何 Controller」与「Controller 藏在未入 Artifactory 的构件（加密 `assemble.jar` / pod `BOOT-INF/lib`）」
  两种解释本轮**无法区分** ⇒ 不写成「证明不存在」。
- 抽取值（619 controller / 201 构件 / 437 jar）为扫描时点事实，Artifactory 内容可变。
- LIVE 通道仍断：直连网关 403、共享 token 2026-10-13 过期、`10.0.0.1:22` timeout。
