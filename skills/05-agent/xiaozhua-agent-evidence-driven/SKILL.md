---
name: xiaozhua-agent-evidence-driven
description: "Use for evidence-first xiaozhua Agent delivery."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [xiaozhua, agent, udc, evidence, audit, providers, dry-run, tdd]
    related_skills: [xiaozhua-udc-runtime, xiaozhua-low-code-environment, test-driven-development, writing-plans]
---

# xiaozhua Agent Evidence-Driven Delivery

## Purpose

Use this class-level skill when building or extending a xiaozhua Agent that integrates UDC, Runtime, Integration, SPI, external Providers, audits, diagnostics, or controlled execution. The goal is a reusable, embeddable Agent platform whose conclusions are traceable and whose side effects are gated.

The canonical progression is:

```text
scope and audit
  -> evidence ledger
  -> read-only providers
  -> critical-path matrix
  -> extension boundary
  -> impact graph
  -> dry-run plan
  -> explicit authorization
  -> smallest real change
  -> readback verification
```

## User workflow preference

For this user, keep moving through the agreed sequence without stopping after every small step or asking for routine confirmation. Work in batches, run the next verification immediately, and report only after a meaningful milestone. Ask before a genuinely irreversible external side effect, a security-boundary change, or an ambiguous target that tools cannot resolve.

**Explicit step-by-step override.** When the user says 「一步一步来」/「我自己创建，然后我来检查」/「你做完我检查」, that task switches to one-action-then-report: do exactly the next single action, report the concrete object ids and evidence, and wait. Do not batch three steps to look efficient — in that mode unrequested batching is read as hiding work, and the user's review is the gate.

**「你来做，然后我来检查」= 交付物是平台上的可用结果 + 可核对的证据，不是脚本和报告。** 具体到 UDC 配置类任务，交付判据是「页面上能点到、点完有预期效果、数据落库能回读」，同时给出这三样：具体对象 id、用户能自己复现的操作路径、实测结论。缺任何一样都说清缺哪一项，不要用「已完成 N 个接口」代替。

**报告用用户可见的成果，不用过程指标。** 「进程在线 / 日志在跑 / 提交了多少条 / 测试全绿」都不是用户能验收的东西。用户能验收的是：哪个具体对象正确了、在哪个页面能看到、哪个真实操作跑通了、哪些错误配置还在。写报告时先写可见结果，再写证据；反过来写会被直接打回。

**When the user says 「进度很低 / 我看不到进度」, do not answer with more process metrics.** Re-derive the answer from platform state: read the actual objects back, list what exists, what is wrong, and what is still missing. If the honest answer is 「大部分进展是取证与报告，不是可用能力」，say that in one sentence and then give the shortest path to a working result — do not defend the volume of work.

**Do not re-explain the plan when execution is already authorized.** Repeating the plan after an approval reads as stalling. One sentence of "what I'm doing next", then the action.

**When a fleet has produced no business result, stop it and audit — do not "push harder".** If days of worker time yield reports, re-audits and self-corrections but no page/API/business effect the user can see, the correct move is: stop the workers (keep any explicitly excluded line running), freeze the tree, and audit *why* the loop is unproductive. Adding more dispatch instructions, more parallel agents, or "加快推进" to the same broken loop multiplies the cost instead of the output. Also treat a worker's self-reported progress the way you treat a closure report: liveness, heartbeat and log freshness are not progress.

**Report progress in four separate tiers, never collapse them.** `进程在线` / `日志在跑` / `局部技术产出` / `真实业务链可用` are almost always out of sync; presenting the first three as the fourth is a false progress claim the user will reject on sight. Name which tier each sentence belongs to.

**Assign a failure only to the line that caused it, and only with readable ownership evidence.** When two groups are both hunting the same defect, one is burning budget on duplicate forensics. Before dispatching: confirm ownership from artifact content (a file stating "this is our test fixture", a creation record pointing at it) rather than from module naming or domain association. Once assigned, the other group must receive an explicit "return to your own route" instruction — otherwise it keeps producing duplicate reports. Ownership unknown ⇒ draw the dependency graph read-only first, then split; do not start both sides in parallel hoping one finds it. Likewise a local blockage (login state, permission, missing id) blocks only the one action that needs it — the same group keeps advancing its independent boundaries and states 「唯一缺口 + 最小动作」 instead of writing repeated HOLDs.

- **A swallowed validator exception becomes a silent PASS.** Batch-validating many objects (hundreds of microflows, whole-app scans) through a local constraints model: if the per-item call is wrapped in `except` and the error is appended as a string while the item is still counted as "validated", a validator crash reads exactly like "no problems found". Fix the crash (e.g. a real-data field arrives as a `dict` while the code does `value not in frozenset(...)` → `TypeError: unhashable type`), but also treat 「解析异常」 in bulk output as "the validator did not run" rather than a finding about the data. **同一类还有：校验函数把错误当成字符串 append 进错误列表，逐字迭代那个字符串再输出，看起来像十几条错误其实是一条——先确认错误列表的元素类型再解读批量输出。**
- **判据只排除了一个坏状态就会造出假 PASS。** 排除 `/403` 而没排除 `/login`，会把被踢回登录页的页面判成通过。**任何「页面/会话可用」类判据，必须同时排除所有已知坏状态（未登录、无权限、空白、加载中），并要求有实际渲染内容。** 写完判据后用一个已知坏样本反证它会红。

Respect acceptance order: when the user makes microflow correctness the gate, finish its scoped node/field/expression and execution acceptance before advancing to dataflow, deduction, or other rule domains. Do not substitute breadth, cron dispatch, commits, or documentation volume for closing that gate. Report scoped verified cases and explicit gaps, never an unrestricted guarantee of “100% correct”.

Terminology discipline: when this user says 推送/推进测试 in the xiaozhua Agent project, it means driving the real call-chain verification live — request → backend → readback — never git operations. Git commits are bookkeeping, not the deliverable; do not answer a push-the-test ask with remote/credential hunting (the repo is local-only and that is fine). 「你自己建应用自己测试」 is standing authorization to create throwaway test applications (prefix `zzprobe`) for write-path probing without re-asking; deleting an app stays confirm-gated.

## Non-negotiable evidence rules

1. `FACT` requires direct evidence: source, decompiled class, exact artifact/version/SHA-256, successful readback, or an exact dynamic response.
2. `OBSERVATION` is a seen phenomenon or inventory mention that does not close the implementation or behavior claim.
3. `HYPOTHESIS` is an inference and must remain explicitly labeled.
4. `UNVERIFIED` means the required evidence is absent or incomplete.
5. `BLOCKED` means the check could not execute because of an environmental, permission, or tool boundary.
6. `CONFLICT` means two sources disagree; preserve both records and do not overwrite one with the other.
7. Never promote `HTTP 200`, an outer boolean, `BOOT_0000`, a static class count, or a local snapshot read into `LIVE PASS` or write success. Envelope-level `identity_matches=true` on a double-send is likewise not a PASS while every business object reads back empty — record the precise gap (credential identity cannot see that app's business data, or deployment-state divergence) and keep `UNVERIFIED`.
8. Every claim should retain `source`, target/environment, and where applicable artifact, version, SHA-256, timestamp, trace/task ID, and limitations.

## 统计口径：三层必须同时写死（任何计数型断言的前置）

报任何「有 N 个 X」的数字前，三件事一起声明，缺一个就不算取证：

```text
① 范围  WHERE app_id = ?          —— 哪个应用（本应用 / 全库）
② 位置  nodes[*] vs 任意深度递归   —— dict 在 JSON 树的哪一层
③ 主键  (id, nodeId) vs (name, nodeId) —— 同名不同 id 的多版本如何算
```

- **层①最容易被整层跳过**，因为它不在 JSON 里、在 SQL 的 WHERE 里。做过位置过滤和主键思考，仍然会把全库数字当成本应用事实报出去（实测：全库 4755 行微流程 42 个映射节点，目标应用只有 47 行、9 个节点，虚高 4.7 倍）。**B-5 沉淀的「位置纪律」完全防不住这一层。**
- **层②的错误量级随范围变化**：同一类引用碎片，本应用只多 1 条（9→10），全库多 202 条（42→244）。只在小范围验证过口径就外推，会漏掉大范围的真实噪声。
- **层③在本应用可能完全不触发**（无同名组时 42→42），换应用就爆（全库 848 个名称同名、42→37）。**「错口径在本应用看不出问题」不是口径正确的证据。**
- 本应用与全库的**字段级差异**比计数差异更值钱：同一字段在本应用 6/6 为 `None`、在全库 12/12 为 `DTO`，说明两批数据不同源——以该字段做有效性校验的逻辑会在本应用把全部条目判为无效。发现这种差异要单独成节，不要用全库结论覆盖本应用。

### 一致性闸门必须比数字，不能看退出码

多脚本互证同一数字时，闸门（gate）要**解析并比较各自输出**，而不是检查 `exit code == 0`：两个实现可以都 exit=0 却得出 254 和 255，因为错的那份只是遍历得更深。反向验证闸门是否真有咬合力：喂它一个「正确 + 故意回退成错口径」的组合，必须返回非 0；只跑正向全绿不证明闸门有效，可能只是它从不失败。

### 闸门绑定真伪：三种注入各只证明一件事

审「契约文档 ↔ 字节码」类闸门时，必须分清注入层级，否则会把假闸门判成 PASS：

- 改**文档正文**（负向注入）只证明「某条断言覆盖了该表述」，不证明它绑字节码。
- 改**闸门里的期望字节码值**（对方常自称「反向验证」）只证明「那条 `chk(...)` 行还在」——变异发生在检测循环下游，绕过了上游循环。
- 唯一能证明检测逻辑真在工作的，是把**检测循环整体空转**（`for _m in []`）后重跑：仍 PASS 的反向验证项一律作废。

另两条必查：检测窗口（`body[anchor-400:anchor]`）过窄会让真实分支根本不进视野 ⇒ 假 PASS，但要同时跑「放宽窗口」版排除判据错造成的假 FAIL（三端对照）；数字型断言若「正好等于连续 k 个方法段之和」是方法边界切错，不是事实。完整配方（判据建模、控制字符死断言、存在式断言短路、数字失真识别、按内容验证而非按 commit 复验）：`references/gate-truth-verification.md`。

## Microflow panel and execution acceptance

1. Read the current saved schema and enumerate node IDs recursively, including branches and loops; reconcile expected, captured, skipped, and missing ID sets programmatically. A fixed display-label list is not a coverage denominator, and one standard microflow does not cover listener, scheduled, or custom flow types.
2. After each browser click, verify the selected node ID and expected panel type before attributing any observation to that node. A successful click dispatch or fixed sleep is not proof of panel switching. Compare panel snapshots across different node types: identical text is a stale-capture warning requiring independent identity evidence, not proof that the node configuration is wrong. Mark unconfirmed captures `PANEL_IDENTITY_UNVERIFIED`, exclude them from PASS, and retract prior totals that relied on them.
   - **Validate the click TARGET, not just the node label.** Canvas node titles can be live inputs: a `.node-title-text` wrapper containing `<input class="ant-input edit-input">` means a click at the title's centre lands in the input, puts the node into rename/edit mode, and never switches the panel — every subsequent node then reads the same stale panel and produces identical fingerprints. Before dispatching, resolve the hit with `document.elementFromPoint(x,y)` and reject `input/textarea/[contenteditable]`; retry on the node icon, then an offset point outside the title, and after three failures record `CLICK_TARGET_FAIL` instead of a panel observation. Persist `clickTarget{selector,x,y,hitTag,hitCls,attempts}` per node so a later reviewer can tell a real panel from a mis-click.
   - **Derive the expected panel type from an explicit `nodeType → allowedPanelHints[]` whitelist, never from a regex over the type name.** Substring inference collides across node families (`CHANGE_LIST` matched `/LIST/` and was judged as `CREATE_LIST`, `MAP_OPERATION` as `/MAP/` → `CREATE_MAP`, `CONVERT_DATA` as `/CONVERT/` → `DATA_CONVERT`), so genuine panels get reported as mismatches and real mismatches hide behind the noise. Types absent from the whitelist are recorded `unmapped` and excluded from the verdict rather than guessed at.
   - **Normalise `nodeType` against DOM id suffixes before any comparison.** Raw values arrive as `CREATE_MAP_n6a`, `CONDITION_n18_0`, `CONDITION_n18_1`; strip the `_n<N>` / `_n<M><letter>` tail into a separate `instance` field, or the whitelist lookup fails and branch/condition instances look like distinct unknown types.
   - **Branch/condition nodes are not settings-panel nodes.** Probing them through the settings-panel path returns null; capture their own UI (`branchSpec{branchCount,conditions[]}`) and record `BRANCH_UI_UNCAPTURED` when that fails — never report a null as success.
   - **A drawer left over the canvas silently swallows every later click.** A ~1300px settings drawer with no mask, still mounted, covers the canvas yet leaves no visible overlay hint: subsequent node clicks do nothing, `.active` stays on the previous node, and the collector keeps capturing that same panel — one stale fingerprint propagated across many nodes. Closing with Escape is not enough; assert the drawer is unmounted (or its node gone from the DOM and the canvas clickable) before clicking the next node, and treat any click whose `.active` did not move to the intended node as `PANEL_SWITCH_FAIL` rather than recording a panel.
   - **Fixing one capture defect reveals more of them — expect the failure count to rise.** Each harness fix legitimately uncovers previously-masked failures (a probe that reported PASS on a self-disconnected node count reported 23 failures once the identity assertion became honest). Do not read the larger number as a regression: compare the FAILURE SET, not the count, and retire the earlier PASS verdict explicitly when the harness that produced it is shown unsound.
3. Capture actual input values, selected options, required/validation states, and nested field-mapping/expression dialogs, not just `innerText`. Zero regex matches or zero red messages proves neither filled mandatory fields nor correct mappings. Test the capture/validation harness against a known invalid fixture so a broken matcher cannot silently return an all-clear result.
4. Cross-check each node's candidate identities, service signature and argument bindings, entity/field types, upstream output cardinality, mapping rows, expression tokens and executable representation against exact API/source evidence and saved readback. Keep facts complete for the supported variant; unresolved variants remain explicit unknowns rather than guessed defaults.
5. Separate `CAPTURE_VALID`, `CONFIG_VERIFIED`, platform-check result, page-triggered build result, and `RUNTIME_EFFECT_VERIFIED`. For this user's build acceptance, click Build in the page and retain its request/result evidence; a direct deploy request alone does not satisfy that criterion. For runtime acceptance use bounded authorized test data, exercise required branches and null/error cases, and read back business effects. Never run a flow containing updates, deletes, or event side effects merely to validate the capture harness.
6. Associate asynchronous checks with the exact task/application and wait for an evidenced terminal result. A FAIL followed by an empty result list is not “zero errors”; retain FAIL/UNVERIFIED and investigate its trace/log before proceeding. Likewise, a cron wrapper reporting `ok` proves only job completion until its actual output and referenced artifacts have been inspected.

**Double-send identity is a two-round gate.** `identity_matches=true` requires *both* rounds to pass the envelope gate (HTTP 2xx **and** business `status==0`). Checking only the first response lets a half-failure through: with round 1 at HTTP 200 and round 2 at HTTP 500 carrying the same success body, a resp1-only gate reports PASS for every endpoint. Validate both responses and tag the reason with its round (`R1:`/`R2:`) so a reviewer can tell which send failed. Endpoints that derive a sample from a prior endpoint (e.g. check-exists drawing from select-host) legitimately return `BLOCKED(NO_SAMPLE)` once the upstream is gated — assert only on endpoints that actually issued both requests.

### Generation-side constraints that the platform will not catch

`checkSchema` is a shallow validator: wrong `actionType`, wrong operator, wrong `paramType`
and even `nodes=[]` all return `check:true, errors:0` (recorded in
`core/facts/udc/write-chain/microflow-rest-write-chain.md` §4). So any generator that relies
on the platform to reject a malformed schema ships a request body that fails later — during
code generation or at runtime. Two concrete shapes, both worth a local validator:

- **MESSAGE-triggered flows require a complete root `input`.** In
  `autocode/JAVA/*/templates/microflow/event/BusinessEventListener.java.ftl`, the MESSAGE
  branch evaluates `microFlowBo.input.javaType` (L117) and `microFlowBo.input.name?cap_first`
  (L119). `?then` is lazy, so **both** shapes fail: `input=null` throws at 117, and
  `input` present but missing `javaType` throws at the same placeholder via the other branch.
  Validate `input` is an object carrying `javaType` and `name` whenever
  `trigger.messageInfo.messageSource == "MESSAGE"`; do not scope the rule to EVENT/CONNECTOR
  (they use different template branches).
- **A contract document is not a validator.** `NODE_REQUIRED_FIELDS['CALL_APP_SERVICE'] == ()`
  while `docs/operation-contracts/udc/microflow/cappservice-parameter-semantics.md` §5 already
  tabulates every hard rule (`selectMethod.fullName` required and prefixed by `implClass`,
  `parameter.type ∈ {SingleRequest, PageDtoRequest}`, `returnValue.type ∈ {SingleResponse,
  ListResponse, PageResponse}`, `item.itemType` non-empty, `mappingType == 'attrs'`,
  `attrs[].attrType.id` prefixed by `parameter.item.itemType`). If a §5-style table exists but
  the code only has an empty tuple, the knowledge never reaches the generation path — implement
  the validator and wire it into the public body builder.

Wire local validators into the **public construction entry**, not just the private helper: a
builder that already has an `unknowns` channel should append validation errors there (pure
functions keep returning a body; the caller decides whether to submit). Verify end to end by
calling the public entry with the known-bad shape and asserting `unknowns` is non-empty, plus a
regression case with a valid shape asserting it stays empty.

## Scope and audit first

Before implementing a high-risk feature:

1. Inspect the current repository and existing tests.
2. Run the current suite to establish a real baseline.
3. Audit existing facts for parseability, count consistency, provenance, and version mixing.
4. Separate real executable code from placeholders, snapshots, routing-only branches, and denied operations.
5. Record gaps and decision gates in an audit document.
6. Do not perform an unbounded scan after static facts are sufficient. Prefer targeted dynamic validation of the smallest critical path.

A codebase audit must identify:

```text
real implementation
local-only implementation
placeholder/routing-only surface
blocked capability
documentation drift
missing external adapter
```

## Independent module boundaries and retention

Treat `UDC`, `Standard Product Application`, `SPI`, `Integration`, and `Runtime` as sibling modules/objects. They may be connected by evidence-backed relations, but a relation never changes ownership. Keep module status, evidence, and limitations separate, then report relations in a separate section.

Allowed relation shapes include `UDC --generates--> Customer UDC Application`, `Customer UDC Application --calls--> Standard Product Application`, `Customer Extension --uses--> SPI`, `Customer Extension --integrates-with--> Integration`, and `Runtime --hosts/loads/observes--> each module`. Do not create a default UDC→SPI edge; require exact dependency plus call-site evidence for a customer extension/SPI link.

Customer projects are boundary samples, not durable business knowledge. Store only the minimum locator and classification needed to find the sample again. Customer entity/page/microflow/table inventories, controller lists, ext-file lists, business rules, and endpoint details are `QUERY_ON_DEMAND_NOT_DURABLE` unless a concrete incident requires them temporarily. Do not let customer counts or detailed mappings enter the reusable fact graph or dilute cross-customer platform facts.

When a task spans modules, decompose it into independent workstreams: UDC mechanism, standard-product contract, SPI contract/registration, integration adapter, and runtime evidence. Use cross-module edges only when both endpoint identities, relation type, exact locator, and evidence status are retained. Dependency presence, Pod/Image presence, or a Nacos dataId alone does not prove runtime invocation.


## Evidence repo purification (customer-data eviction, verified)

When the user flags an evidence repo as polluted (customer app content, stray root files, binaries, customer environment data in config/), treat it as a multi-pass eviction with these rules:

1. **Re-grep the customer identifier after EVERY pass.** Stragglers hide where the first sweep didn't look: `modules/decompiled/`, `evidence/`, `tools/db_probe_*` (hardcoded customer schema names), `fixtures/golden/`, `config/projects/`. A pass that only cleared the obvious directories is not done; repeat `git grep -l -i <customer-id>` until the remainder is fully classified, not just smaller.
2. **Before `git rm`/moving a file, grep code + test tree for references to its path.** Files with live code/test references stay in place even when they look like clutter — breaking the reference chain is a FAIL (a contract test that reads the file will red the suite). Fix doc references to point at the new location only for docs, never for loader code paths you are not also updating.
3. **Classify before evicting.** Mechanism fixtures stay (e.g. a Nacos manifest that is only a dataId list with no config values); customer business dumps go (javap of customer controllers, decompiled customer .java, metadata dumps, DB-probe scripts with hardcoded customer schemas, customer-hardcoded rule JSON). A file whose customer-ID occurrences are LIVE-probe parameter records ("this contract was verified with this appId") is a legal retention — it is the fact chain, not business data. State this classification in the delivery report.
4. **Evict with a traceable index**: external evidence repo gets a README (path-mapping table old→new), a `RELOCATED-FROM` note pinning the source repo HEAD, and the source repo gets anti-refill `.gitignore` rules for the evicted prefixes. Copy-verify (count + spot hash) before `git rm`.
5. **Tests that consumed evicted fixtures resolve through an env var** (e.g. `XIAOZHUA_CUSTOMER_EVIDENCE_ROOT`) set in `tests/conftest.py`, with `pytest.mark.skipif` when the external root is absent — keeps the repo clean AND the suite green. Restoring an over-evicted mechanism fixture is a legitimate correction; run the full suite after every pass.
6. **Measure the result**: tracked file count + repo size before/after, and the residual customer-ID file count with its classification. Report these four numbers.

When the user asks "能不能只给域名+地址+登录就自动搭建" — answer from a live capability matrix, layer by layer (credential renewal / live probe / requirement→generate / deploy plan / per-contract live readback / write executor), each marked 全通/部分通/未点火 with the exact test that proved it. Do not answer from command counts or suite greenness; run the real chain (token renewal, one live contract readback) during the answer.

## Provider design

For the read-only phase:

- default to `network=disabled`;
- require explicit opt-in for live GET/POST;
- reject PUT/PATCH/DELETE and Kubernetes `exec/apply/patch/delete`;
- normalize errors as `timeout`, `auth`, `permission`, `not_found`, `parse`, or `unavailable`;
- return structured results rather than leaking low-level exceptions;
- preserve a redacted response summary and source location;
- provide offline fixture tests without real network access.

Whitelist the transport by contract, not by HTTP verb. xiaozhua UDC live readback endpoints are POST by their own HTTP contract (`/udc-runtime/meta-data/*`, `rt-page-log/*`, all `write=False` contracts) — a GET-only gateway client reaches zero live endpoints (verified: every `/udc/*` GET path 404s on test2). Enforce business read-only at the contract layer (`write=False` + policy gate) and keep write verbs rejected at the transport; adding readonly POST touches the transport whitelist, the client `post()` path, the runner, and the tests that pinned the old GET-only wall — grep the test tree for the old rejection assertions before declaring the switch complete.

Never place passwords, tokens, private keys, or kubeconfig contents in reports, fixtures, source control, or command output.

**`ProviderError` is a frozen dataclass, not an exception, and its `kind` is a closed 6-value set** (`timeout`/`auth`/`permission`/`not_found`/`parse`/`unavailable`). The provider *returns* `ProviderResult(error=...)`; it never raises. To abort mid-sequence inside an adapter, carry the error in a private exception class and convert at the boundary — `pytest.raises(ProviderError)` fails outright (`Expected a BaseException type`), and an invented kind such as `CREDENTIAL_RESOLUTION_FAILED` raises `ValueError` at construction (that vocabulary belongs to the gateway/operation layer only).

**Check the registry's mode before claiming a live provider exists.** `providers/registry.py` declares each provider as `fixture` or `live`; a `*FixtureAdapter` plus a write-regex is a read-only *metadata* provider, not a client. Grep for the driver (`pymysql|mysql.connector|sqlalchemy`) — zero hits means the live path does not exist yet regardless of what the adapter class is named.

**A xiaozhua RDS instance hosts many schemas** (test2: 128 — `udc_test2`, `ctp_user_test2`, `organization_test2`, and one `<appName>_test2` per application). Do not bind a single `database` on connect: with it set, cross-schema queries fail with `1046 No database selected`. Connect without a database and address everything as `information_schema` or `<schema>.<table>`; a readback that reports row counts without naming the schema is not evidence. Recipe, security-gate layering and offline test shape: `references/live-provider-and-db-readback.md`.

## Critical-path matrix

Do not use endpoint/class counts as a substitute for closure. Track the smallest meaningful paths:

```text
Application
Entity
Field
Page Schema
MicroFlow
DataFlow
Generate
Publish
Deploy
Runtime Metadata
```

Each path entry should contain `status`, `evidence_refs`, `gaps`, `dependencies`, and `probe_statuses` where relevant. Use explicit labels `STATIC FACT`, `HTTP PASS`, `API PASS`, `LIVE PASS`, `TIMEOUT`, `FAIL`, `BLOCKED`, and `UNVERIFIED`.

The overall matrix is `FACT` only when all required entries are directly verified. Mixed states must become `PARTIALLY_VERIFIED` or `UNVERIFIED`.

## Recovery after interrupted or oversized sessions

When a long xiaozhua Agent session stalls, a provider times out, or delegated work returns without verifiable completion:

1. Treat child summaries and historical test counts as claims, not current facts.
2. Recover from durable sources in this order: current filesystem, current tests/CLI execution, audit documents, then session transcript or exported conversation.
3. Inventory exact files and symbols before deciding work was lost. A tool transport/path error is `BLOCKED`, not proof that a file or repository is absent.
4. Run the current focused/full suite and record the new baseline separately from historical baselines. Never silently reuse an old `N passed` figure.
5. Write a compact recovery checkpoint containing current scope, verified artifacts, current failures, unverified work, safety boundaries, and the next executable step.
6. Resume from the smallest broken acceptance boundary instead of re-running the whole research program or redesigning the architecture.

When a compaction summary says "continue that task" but carries no usable state, replay the source session's own transcript before touching any code: query the Hermes `state.db` sqlite directly (`SELECT id,role,content,tool_calls FROM messages WHERE session_id=? ORDER BY id`) and read the last assistant turns plus their tool results — the decisive intermediate findings (version evidence, failed probes, open branches) live inside TOOL rows, not the summary. If a query returns zero rows, the session id may live in a different `state.db` under the Hermes home: probe each candidate DB for the session-id prefix before concluding the history is gone. When the user hands you a session list and points at one («看看那个是什么会话»), resolve the target by its title in the `sessions` table first (and check `last_activity_at` — most-recently-active is not necessarily the intended one), then read that session's tail turns before assuming what "continue it" means.

For shared-worktree implementation, do not dispatch several agents to edit overlapping core files concurrently. Stabilization phases such as evidence-fixture recovery, schema migration, and test-baseline repair must have one writer. Later independent evidence-source probes may run in parallel, but the parent agent must read the resulting files, run the commands itself, and reconcile conflicts before reporting completion.

## Evidence-first source scan and application boundary classification

When moving from UDC platform evidence to a customer application, first resolve the exact repository and preserve the literal application ID. Do not infer a path from the ID or continue after a failed path lookup without a filesystem check.

Use a bounded static scan to inventory:

- POM coordinates, parent/version placeholders, modules, and direct dependencies;
- Java source count and package distribution;
- controllers and exact mapping annotations;
- generated application/API/AppService/MicroFlow signals;
- external integration call-site candidates;
- SPI candidates from both dependency and exact source usage.

Classify `extend` code as Customer UDC Application / Customer Extension evidence, not UDC Platform Core. Dependency presence is only a static observation; it does not prove runtime coupling, image inclusion, Nacos loading, invocation success, persistence, cache behavior, or deployment. Do not create a default UDC → SPI edge. Require exact dependency plus source call-site evidence, and keep runtime claims `UNVERIFIED` until live readback exists.

Persist the scan as a machine-readable profile plus a short boundary report. Include source path, application ID, status/verification level, limitations, and hashes for delivered artifacts. Keep `network=disabled` for this phase and never emit `LIVE PASS` from static counts or source inventory alone.


## Live 客户微流程逻辑还原

当任务是解释客户微流程的真实业务逻辑时，先绑定 live Pod 中实际加载的客户 `biz/web/facade/ext` 包，再对照前端生成物和实体元数据；不要把本地旧包、方法名或 HTTP 200 当成当前业务事实。流程固定为：定位微流程 ID/caption/输入输出/调用方 → 从 live biz/ext JAR 定位 Service class → `javap -p -c -constants` 保留字节码 → 只提取目标 class 用 CFR 反编译 → 用同应用实体 metadata 的 `attributes[].name/caption` 翻译字段 → 按“DTO → Retrieve → Condition/fallback → setter → ChangeEntity/外部调用 → 子微流程 → 返回值”重建调用图。详细命令和陷阱见 `references/microflow-live-analysis.md`。

只要流程包含 `update/save/submit/ChangeEntity` 或外部写调用，就不要为了证明静态逻辑而直接 POST；没有明确样例 ID、写入范围和授权时，报告 `STATIC LOGIC VERIFIED / LIVE EFFECT UNVERIFIED`。输出必须给出“来源字段(caption) → 目标字段(caption)”映射，并单独标记 `pageSize=1`、无排序、逗号拆分取首项、空值默认值、版本漂移和返回 Boolean 的真实业务含义。

## UDC and Standard Product Code Investigation Boundary

When a task narrows to UDC and Standard Product Application code, pause unrelated SPI work rather than continuing every adjacent module. Keep the two modules independent in both artifact inventories and reports:

```text
UDC Platform artifacts
Standard Product Application artifacts/contracts
SPI: explicitly deferred unless the user reopens it
```

Classify each artifact by direct coordinates and evidence before adding it to a profile. A similarly named package or a cross-module contract does not change ownership; for example, `bpm-facade` is Standard Product Application evidence, not UDC evidence. Use `artifact + version + SHA-256` and retain class/package summaries only as static evidence.

For UDC code that is not available in the local checkout, follow the evidence ladder: remote repository or artifact store first, then local Maven cache/project outputs, then the running server/image. Do not silently substitute a nearby version or promote a local cache artifact to runtime fact.

Frontend evidence must be investigated separately from backend JAR evidence. Read the target server/runtime package and its metadata/configuration to locate frontend build/deploy entry points, mounted resources, object-storage references, or image layers. A server package, frontend URI, or empty frontend version field proves only metadata unless the actual frontend bytes and their artifact/image identity are retrieved. Use bounded, read-only listing/extraction for large packages; do not fully unpack multi-gigabyte archives or start/scale workloads just to close an audit. Record `SERVER_METADATA_FOUND_FRONTEND_BYTES_UNVERIFIED` when metadata is present but the bundle is not yet tied to a digest.

Keep transport status separate from target status: inability to use a local Kubernetes client is a transport/setup observation, not evidence that the workload or frontend is absent. If server-side read-only evidence succeeds while Kubernetes/image verification is unavailable, report the layers independently as `FACT`, `BLOCKED`, or `UNVERIFIED`.

The durable artifacts for this workflow are the compact code-evidence profile and a separate module-link record. Customer entity/page/microflow inventories and SPI details remain excluded unless explicitly reopened by the user.

## UDC/Standard Product code and frontend evidence workflow

When the user explicitly narrows the work to UDC and Standard Product Application code, freeze unrelated SPI investigation and keep the two modules separate in every artifact inventory, profile, and relationship record. Module names, package prefixes, DTO names, or interoperability do not change ownership: `bpm-facade` remains Standard Product Application evidence, while `udc-common`, `udc-facade`, `udc-starter-lowcode`, and `udc-starter-runtime` remain UDC Platform evidence.

Use this evidence ladder:

```text
remote repository / artifact store
  -> local Maven cache or project target
  -> server package and OCI metadata
  -> running image filesystem / Pod
```

For each artifact retain `artifact + version + SHA-256`; keep adjacent versions as separate evidence units. Build a compact targeted index of packages/classes first, then decompile only the relevant UDC AppService/runtime classes and Standard Product DTO/service contracts. A class inventory proves static presence only; it does not prove deployment, loading, invocation, or behavior.

Frontend is a separate evidence stream from backend JARs. Inspect server package metadata for frontend build/deploy URIs, package version, image tag, OCI index/manifest, and layer digests. For large OCI/TAR packages, use bounded read-only reads of `index.json`, `manifest.json`, repositories metadata, and candidate layer listings; do not fully extract multi-gigabyte archives or start/scale workloads. Treat `frontend_project_version` being empty, a frontend URI being present, or a server package existing as metadata only. Upgrade frontend evidence only after the actual bundle/path and its digest are tied to the package or image.

Report each layer independently:

```text
local backend artifact: FACT / STATIC
server package metadata: FACT / SERVER_READ_ONLY
OCI manifest: FACT / SERVER_READ_ONLY
frontend bytes/path: UNVERIFIED until retrieved
Kubernetes current workload: BLOCKED or UNVERIFIED if transport/target evidence is absent
```

A cross-module link must carry exact endpoint identities, FQCNs/methods/DTOs, source locators, and evidence status. `UDC --exposes-contracts-to--> Standard Product Application` may describe contract interoperability, but it must not be upgraded to runtime invocation or ownership without call-site and runtime evidence. Customer entity/page/microflow inventories and SPI details remain out of scope unless explicitly reopened.

The compact supporting detail for this workflow belongs in `references/udc-standard-code-frontend-evidence.md`. Keep it updated when a new reusable extraction or version-binding technique is verified.

For the config-first reusability scheme (environments / infra / version families / per-app configs — multi-version, multi-customer, multi-machine), see `references/udc-config-first-reusability.md`. Standing rule: no hardcoded absolute paths, versions, gateway URLs, appIds, or DB/Redis/storage/Nacos connection values anywhere in the repo; everything resolves through `config/` keys with values injected at runtime.

## Multi-agent live-chain control

When a xiaozhua audit has already established that the offline evidence infrastructure is complete, stop treating the evidence ledger, graph, matrix, closure files, or collaboration bus as the audit target. They are infrastructure evidence, not xiaozhua platform evidence.

Use a bounded live-chain slice:

```text
one real application + one PageTree page or entity
  -> frontend request
  -> backend entrypoint
  -> DTO
  -> Service
  -> Runtime/data source
```

The coordinating agent owns the route and tempo. On every turn it must name the concrete application/page/entity and exactly one next evidence action, then hand off that action. After review, it must do exactly one of: advance to the next boundary, request a narrowly scoped missing proof, or mark the slice `BLOCKED`/`UNVERIFIED` with the next unblock action. It must not reopen a broad discussion merely because the auditor found a gap.

The implementer executes only the current slice and records new platform facts with raw source/output paths. The auditor reviews only that slice's evidence; it must not audit the collaboration tool, demand repeated closure/ledger/graph/matrix artifacts, or invent a wider roadmap. Its output should be short: status, evidence paths, overclaim check, missing proof, and next action. Control returns to the coordinator after review.

A round counts as progress only if it produces a new platform fact: a real request/response, source or bytecode locator, DTO, service call, runtime binding, or data-source binding. File existence, planned probes, static guesses, and agreement among offline reports do not count. Do not write `FINAL`/`COMPLETE` while the live chain remains unverified.

When agent sessions are long or oversized, start a fresh role session rather than resuming a context that cannot compress. Preserve the durable manifest and route file, but do not replay the entire transcript. If the worker cannot resolve the shared path, classify the run as a transport `BLOCKED` and repair the path/context boundary; do not let agents manufacture closure reports to compensate.

See `references/live-chain-multi-agent-control.md` for the compact role protocol and handoff template.


Before any real write, require:

```text
known target
known environment/namespace
sufficient evidence
explicit dependencies
risk classification
confirmation requirement
rollback or cleanup strategy
readback verification
idempotency/terminal-state understanding
```

Dry-run output must state `mode=dry-run`, `requires_confirmation`, `executed=false`, `writes_performed=false`, steps, dependencies, rollback, and verification. If evidence or environment is missing, keep the plan non-confirmable and `UNVERIFIED`. Never silently turn a planner into an executor.

Split create/save, publish, deploy, cache invalidation, restart, and cleanup into separate actions. Each external state-changing action requires readback of the exact target before claiming success.

## TDD and verification rhythm

For every new behavior or bug fix:

1. Write one focused failing test.
2. Run it and verify the failure is caused by the missing behavior.
3. Implement the smallest change.
4. Run the focused test.
5. Run the full offline suite.
6. Run syntax/compile checks and a real CLI subprocess smoke where applicable.

Track evidence separately:

```text
FOCUSED: new behavior
REGRESSION: adjacent/full suite
LIVE: real external path
BLOCKED: attempted but unavailable
UNVERIFIED: not attempted or insufficient
```

A green offline suite proves local behavior only. It does not prove test2, Kubernetes, database, Redis, publishing, deployment, or live provider behavior.

## Repository drift audit and progress reporting (verified 2026-09-14)

When asked "审计一下偏移了吗 / 现在完成的进度是什么 / 接下来怎么做", rebuild the answer from live state — never from session summaries, handoff text, or the closure reports' own claims:

1. `git status/log` first. If the repo has no `.git`, the top corrective action is `git init` + a baseline commit (with user OK) before anything else. A repo holding audit evidence and closure reports without VCS is a bigger risk than any functional gap.
2. Run the offline suite fresh (`uv run --quiet --with pytest python -m pytest tests -q` — the system python has no pytest module; `-m offline` selects the fast subset). The real current count is the only count.
3. Inventory `docs/` by file mtime to find the last active workstream and the dormant ones (the newest code/audit file dates tell you where work actually stopped).
4. Read live evidence JSONs directly (gateway URL, BOOT_0000, verification fields, redaction flags) instead of trusting the closure report that references them.
5. Grep the CLI surface for wiring gaps: a layer that is implemented and tested but never imported by `xiaozhua_cli.py` means human-path integration is UNVERIFIED even when a closure report claims PASS.

Report in three parts: drift verdict (mainline on/off track + concrete process problems), progress table (`workstream | status | evidence`), next steps ranked by priority. This shape was explicitly approved by the user.

**When the user doubts the output volume ("产出是不是很少 / 他们都写到哪里去"), measure committed work, not the working tree.** Each discovery round commits its own deliverable, so `git status --porcelain` being nearly empty alongside a large committed delta is the normal healthy shape — an empty tree is not evidence of little output. Quantify from live state: `git log --oneline -N` (round of work per commit), `git diff --stat <baseline-commit>..HEAD` (files/lines landed since the baseline), per-domain file counts under `docs/operation-contracts/udc/<domain>/`, and the declared-operation count read from `registry.py`'s `specs` list. A domain that produced only a VACUUM negative-evidence report is a valid deliverable, not a missing one — say so in the table instead of listing it as incomplete. Name the not-yet-landed work separately (e.g. the `registry-entries.md` proposals awaiting the single-writer MERGE task) so "committed" and "still pending merge" are never conflated.

## UDC domain-contract discovery over local Maven jars (verified recipe)

The read-only contract-discovery sweep across UDC domains runs entirely offline against the local Maven cache; the recipe below is the verified sequence and the domain map that actually matches the 5.3.517 artifacts. For the verified live route shape (`/service/{appId}/` prefix), WEB-cookie credential-file convention, and live-readback identity rules, see `references/udc-gateway-and-capability-expansion.md`.

1. Enumerate candidate classes with `unzip -l <jar> | grep -io '[a-zA-Z/]*<keyword>[a-zA-Z]*\.class'` before any javap — class-name hits decide which domain has real material, and a zero-hit scan IS a valid VACUUM finding when the command and count are recorded.
2. Controller inventory per jar: `unzip -l | grep -c 'Controller\.class'` then list them. In 5.3.517 the layout is asymmetric — `udc-starter-lowcode` has ZERO Controllers (it is core/service/DTO only; do not hunt design-time REST APIs there), `udc-starter-runtime` has ~30, and `udc-starter-customplan` has 5 (including BpmNodeInfoController, FilterPlanController, UdcRuntimeHistoryMetaDataController). Scan customplan and the runtime `proxy/controller/` package (FormAppInfo/NormalAppInfo/UdcBaseAppInfo/UdcRefer etc.) — they are easy to miss.
3. javap needs a Windows-native jar path: git-bash `/d/repo/...` paths fail with 找不到类; pass `<PATH> javap is not on PATH; the working binary is `/c/Program Files/Java/latest/jdk-21/bin/javap.exe` (resolve it once per session, store in a var). `javap -p` for method signatures; add `-v` when the annotation values (the @GetMapping literal path) are needed.
4. Method-only javap shows the DTO types but NOT the HTTP path — the route literal lives in runtime-visible annotations, so extract it with `javap -v` constant-pool output or record the path as UNVERIFIED rather than inferring it from the method name. Base-class inheritance matters: FormAppInfoController is empty and inherits `getDeployInfo(String)` from UdcBaseAppInfoController — javap the parent before declaring a controller contract-empty.
5. Domain map from the real scan: 菜单域 anchors on UdcFunctionNodeController (function-node tree IS the menu/navigation surface; no separate *Menu*Controller exists in 5.3.517 — a menu-domain task that finds nothing beyond the function-node tree is CORRECT, not a failed scan); 页面规则域 anchors on UdcRtPageInfoController + customplan CustomPlanController (PageProcessEvent) + FilterPlanController; BI 域 keyword scan (bi/report/chart/dashboard) over all modules yields only false-positive substring hits (MethodBizProxy, BillState..., Scalability...) — treat BI as VACUUM unless a live/design-time artifact outside this cache proves otherwise; 基本信息/应用域 anchors on CustomApplicationController + the proxy FormAppInfo family + UdcAppLogController; 流程域 builds on the already-proven bpm-facade 3.12.101 call-site chain (ApproveFeatureService/ApprovalStateChangeListener → BpmUdcApiService) plus BpmNodeInfoController for read-only node-permission queries.
6. GraphqlProxyController (`doGraphql(GraphqlProxyRequestDto) → SingleResponse<String>`) is the generic metadata/query bypass channel — register it once as a runtime-domain contract; it is also the fallback answer when a domain has DTOs but no dedicated REST controller.

Provenance discipline stays as elsewhere: artifact+version+sha256 per class, controller path copied verbatim (no gateway prefix), `local-maven-53517` as source tag, and registry proposals written as constructor-arg-exact entries for a single-writer merge task — never edited into the shared registry by the discovery tasks themselves.

Config-first reusability applies to this recipe too: jar paths, versions, gateway URLs, and appIds must resolve through `config/` keys (see `references/udc-config-first-reusability.md`), not literals — evidence entries keep artifact+version+sha256 as identity, but source paths are assembled from config.

## Capability readiness assessment ("现在到什么程度 / 能不能用它做 X")

When the user asks whether the xiaozhua Agent can already do a named capability (create a MicroFlow, read a page, publish an app), answer from live state, capability by capability. Never answer from CLI command count: the 26 subcommands are offline report/audit generators, and command count is not capability.

1. `git log --oneline -6 && git status --porcelain` — a clean tree means HEAD *is* the current state; do not hunt for uncommitted work or assume your last edits are still present.
2. Run the offline suite via `uv run --with pytest` (see step 2 above). A green suite is local behavior only.
3. Enumerate the *declared* contracts in `components/platform_operations/registry.py` (the `specs` list; `write=True` entries are declared but not executable). Declared ≠ executable.
4. Read the policy gate in `components/platform_operations/layer.py`: `contract.write or contract.method != "GET" or not contract.effective` → `POLICY_DENIED`. Write capability is therefore refused **by design**, not missing code — report it as a policy boundary, never as a bug or a partial pass. `auth_scope` without `"<appId>:readonly"` → `AUTH_SCOPE_DENIED`.
5. Map the requested capability onto its contract directory `docs/operation-contracts/udc/<domain>/`. An EMPTY directory means zero contracts for that domain, so every operation of that domain returns `UNVERIFIED` / `operation contract is not declared` — call it a vacuum, not a partial success.
6. For design-time capability also check `docs/audit/udc-design-artifact-availability-evidence.md` (design-time modules MISSING in the local Maven repo → `BLOCKED / UNVERIFIED`) and `docs/audit/artifacts/<module>/`; an empty artifact directory means that layer has no evidence at all.
7. Before promising the unblock step, verify its prerequisite transport exists in the *current* session (kubectl on PATH, the environment kubeconfig, a credential ref, `--allow-network`). A missing prerequisite is a `BLOCKED` line with the exact input needed — never a plan that assumes it.

Report shape that works for this user: 能用 (with the concrete commands) / 真空区 (capability with zero contracts) / 被策略拦 (by-design denial) / 下一步里程碑 M1…Mn / 需要用户提供的输入 (keep it to ~3 items and state that you handle the rest). Keep `未实现`、`被策略硬拒`、`缺环境输入(BLOCKED)` as three distinct verdicts — collapsing them produces a false "it's done" or a false "it's broken".

## 九大模块状态审计与分域派活

当用户要求「审计九个模块现在各自的状态事实 / 每个模块走一个任务」时，先测量再派活：不要用一句完成度概括九个域，也不要给九个域套同一套「取证→写链→验收」模板——空白域会在模板里空转。

**量化只认两列**：该域在盘证据（`docs/` + `core/facts/` 下相关文件的件数与字节数）与该应用在 MySQL 的实测行数。同一份审计里两者并列，缺一个就会出现「文档很厚但没落库」或「数据很多但零契约」的误判。

**真实表名与直觉名不同，别靠猜**：应用 `udc_application.app_id`；实体 `udc_entity.app_id` + `udc_attribute`（全库大表，按 entity_id 过滤，别拿全库数当本应用成果）；菜单 `udc_function_node`（**没有** `udc_menu` 表，菜单/导航面就是功能节点树）；页面 `udc_page_info` + `udc_page_schema`（**没有** `udc_page`）；微流程 `udc_microflow_info`（**没有** `udc_micro_flow`）；生单 `udc_data_flow` + `udc_data_flow_mapping`；扣减 `udc_deduction_map/_rule/_rule_detail/_algorithm`；DTO `udc_data_transfer_object`；角色 `udc_role` + `udc_role_resource` + `udc_resource`（**没有** `udc_permission`，权限走 resource 关联）；枚举是双域——`udc_enum` 是选项集、`ctp_enum` 是平台枚举，两者不可互换；BI 与栏目**没有任何** `udc_bi`/`udc_report`/`udc_column`/`udc_portal` 表。先用 `SHOW TABLES` + 关键词过滤确认，再逐个 `COUNT(*)`，并区分全库行数与本应用行数。

**角色域最容易被虚报**：`core/role/*.md`（ROLE-CARD / BEHAVIOR / EVIDENCE-DISCIPLINE）是 Agent 的角色卡，不是 UDC 平台角色域证据。把它们算进角色域，会把一个证据近乎为零的域读成「已有 11 个文件」。判别法：文件描述的是「你作为 Agent 该怎么做事」还是「平台角色对象的读写面」。

**派活前先分类，分类决定首个动作**：

```text
CONTINUE       证据在盘且缺口已指名        → 直接补该缺口（写链/字段级/契约）
LOCATE-FIRST   该域证据 ≈ 0，对象都未定位 → 首个动作是「前端页面 → 调用链 → 落表」，不是写链
BOUNDARY-CLOSE 已有完备负证据（VACUUM）    → 确认归属边界后收工，不是「还没做」
FIX-HARNESS-FIRST 当前证据是探针造成的 FAIL → 先修采集/取证工具可信度，再谈平台配置对错
```

VACUUM 与「未做」性质不同：前者是「扫过、结论是零」，属有效交付，报告里不能列成缺口；后者是「没扫过」。同理，探针 FAIL 不等于节点配置错——采集器不可信时，先把「面板/字段能不能被证据化」作为该域自己的第一优先级，但它不阻塞其他域启动。

多个域并行推进时，任务文档按上述分类分别写，不要九个域共用一份模板：空域的任务首行必须是「定位对象」，边界域的首行必须是「确认归属并登记结论」。

## CLI human-path integration — op-execute (verified pattern)

The repo's unified execution boundary is `PlatformOperationLayer`; `xiaozhua_cli.py op-execute` is its verified human path:

```text
op-execute --operation <op> --application-id <id> [--entity-id ...]
  → OperationIntent (readonly enforced; entity-scoped ops require entity_id)
  → PlatformOperationLayer (contract → policy → auth_scope gates)
  → GatewayAdapter → GatewayReadonlyClient (GET + readonly POST, network off by default)
  → redacted OperationResult (--evidence-out persists via OperationEvidenceStore)
```

Boundaries that make it trustworthy:
- Default offline: network disabled; missing credential → `BLOCKED / CREDENTIAL_RESOLUTION_FAILED`, RC 2. Never fabricate a PASS to make the CLI look alive.
- Write contracts are denied at the contract layer (`POLICY_DENIED`) before any gateway call.
- Credentials live in a JSON file outside the repo mapping credential_ref → HTTP headers, resolved per-request and never persisted; only `<REDACTED>` appears in evidence.
- Live GET requires explicit `--allow-network` plus an authorized credential file and stays `UNVERIFIED` until actually run against the authorized target. Do not add a live test requiring real credentials to the offline suite.
- `build_operation_layer(gateway_adapter, registry=None)` in `xiaozhua_cli.py` is the composition root for tests; stub the gateway with a `read()` fake that returns the `{"verified": True, "response": {...}}` shape.
- **Generic contract dispatch in `PlatformOperationLayer._request` (replaces the 4-op hardcode).** Placeholder fill = union of `required_inputs` names and the path's actual `{placeholders}` (they do NOT match: a contract declares `application_id` but the path says `{id}`), sourced from `intent.application_id`/`entity_id` plus `intent.context` keys. `{id}` disambiguation: explicit `entity_id` wins; otherwise falls back to `application_id` — `test_operation_layer.py` pins the entity-scoped case, so do not let appId preempt `{id}`. Unresolvable placeholders raise `missing path parameters [...]` — missing intent data is UNKNOWN, never guessed. The 4 legacy ops' `/udc/*` paths are a registry-data correction item (test2 404s them), not a dispatch bug.

## North-star live-chain acceptance (verified entry points)

Two one-command entries verify the agent's real chain end-to-end. Run them before telling the user the chain "works" — a green offline suite is not the acceptance:

```bash
CRED="<agent-collab-workspace>/shared-credentials/test2-web-credential.json"
# 1) live readonly probe — 4 pinned POST endpoints, dual-send identity
./.venv/Scripts/python.exe run_live_readonly.py --credential-file "$CRED" --allow-network
#    expect every endpoint: verdict=PASS, http1=http2=200, ident=true, auth_fail=false

# 2) north-star multi-round — host-embed + requirement→readback + live stability
./.venv/Scripts/python.exe run_multi_live_test.py --credential-file "$CRED" --allow-network --rounds 3
#    expect overall=PASS: live_stability all rounds PASS + cross_round_md5_stable=true,
#    requirement_readback routed_consistent=true
```

The credential file's canonical location is the collaboration workspace's `shared-credentials/test2-web-credential.json` (the repo's `config/environments.yaml` references it; older per-session `main/` deep paths are archived — a FileNotFoundError means look there, not that credentials are gone). The token expires (~24 h): renew in place by POSTing the endpoint stored in the sibling `shared-credentials/ctp-user-login.json` and writing the new `access-token` plus the decoded-JWT `exp` back into the same file's `expires_epoch`. Without `--allow-network` both entries report the live rounds SKIPPED — that is the discipline, never fake a live PASS offline.

## Pitfall: 批量删除前必须先给出「数量口径 + 归属」两份清单

「其他都删除」这句指令不等于「把整个集合删光」。一个应用里 372 条枚举、47 条微流程、20 个实体里，
只有个位数是实验残留，其余是随业务包导入的真实配置。整集合清空与「筛出 2 条可删」差着两个数量级的代价，
而且**没有还原路径**（平台多数域只有 `is_delete` 逻辑删，无软删/回收站表）。

删除前的交付顺序固定为：

```text
1  先查引用    被引用的一律保留，并在清单里逐条写「谁在引用它」
2  再分类      KEEP（有引用）/ SAFE（无引用+明显测试垃圾）/ MAYBE（无引用+像业务）
3  先给清单    连同数量口径（总数 → 保留 N → 可删 M）一并报给用户
4  备份        目标行 + 明细行导成 JSON 落仓外，再执行
5  执行+回读   分批执行；逻辑删除必须用 is_delete=0 回读，不能用总数比对
```

**数量口径本身要写清范围。** 「删了 363 个」必须同时给出「本应用共 372 个、保留 9 个、其中 9 个有微流程或实体属性引用」，
否则用户无法判断这是清理还是清洗。

**「接口返回成功」与「数据已落库/已删除」要分开判。** 逻辑删除的表里 `COUNT(*)` 不变是正常的，
用总数对比会得出「删除没生效」的错误结论；反过来，同一操作在不同表名下查会得出「返回 SUCCESS 但没落库」的错误结论。
**返回的 id 要在所有候选表里都查一遍再下结论**，查错表名和查错标志位是同一类错误的两面。

**删除端点偶发误报时不重发。** 实测过批量删除中途返回数据库类错误、但该批数据实际已生效；
先回读状态再决定是否重发，否则重发就是重复操作。失败即停的约定在这里的例外是「先回读再判断」，
不是「失败了换个参数再试」。

## Pitfall: 删数据前先画依赖图，删的不是你想删的那一层

用户手工清理废弃对象后构建失败，报的是**代码生成产物的残留 import**，不是你想删的那个东西缺失：

```
<Entity>Service.java:[169] 程序包 com.seeyon.<app>.domain.message.<entity小写> 不存在
```

`domain.message.<entity>` 包只在**该实体仍有微流程引用**时由生成器产出。删掉引用它的微流程后包不再生成，但实体自身生成的 Service 仍 import 它 ⇒ 编译失败。表象是「实体和事件都还在、什么都没删错」，实质是引用链被从中间抽掉了一段。

- **删除前必须画三层依赖图**：实体 ← `udc_event.source/source_id` ← 微流程 `data_schema` 文本 ← 页面/规则。顺序是**先删引用者、再删被引用者**，反过来必留悬空。
- **删前确认有无软删除/回收站表**（`*_history` / `*_del` / `*_bak_<date>`）；没有就只能靠事前依赖图，事后没有还原路径。批量删除后发现的「怎么少了 27 条」是不可修复的。
- **批量删之前必须先把完整清单+归属打给用户确认**，即使指令是「其他都删除」。数量口径（372 → 筛出 2 可删）与「整集合清空」的差别是灾难级的。
- **当一个删除动作的失败原因不明时，先看报错里的 Java 包名反查实体**，不要归因于平台缓存或构建没跑。

## Pitfall: documentation-contract test alignment

`tests/test_documentation_contract.py` hard-asserts that the test counts in `README.md`, `docs/audit/agent-version-audit.md`, and `docs/audit/code-reality-audit.md` equal the live pytest collection count. Adding any test breaks 4 doc-contract tests until counts are aligned. After every test addition: run `pytest tests --collect-only -q`, update the count in all three documents, then rerun the full suite. Also update the subcommand count in `agent-version-audit.md`'s command-evidence block when adding CLI commands. The test matches counts via a fixed set of regex patterns — update ONLY the numbers those patterns capture (verified edit points: README.md test-count line; agent-version-audit.md ×2; code-reality-audit.md ×3), and leave historical log lines and non-asserted numbers (e.g. older `N tests collected in Xs` transcripts, table baselines) untouched: the auditor discipline treats those as historical records, and the doc-contract tests stay green either way. Never edit the test's assertion logic to make counts match.

**Mechanics that keep this a 13-line diff instead of a 900-line one:**

- `Path.write_text()` on Windows rewrites line endings to CRLF. When the file is LF in git, a single-number edit shows the whole file as modified (216/304/388 changed lines instead of 2/12/12) and hides the real change from review. Read bytes, edit bytes, write bytes — or normalise `b'\r\n' → b'\n'` before writing.
- Replace the **exact old count bytes** (`b'1532' → b'1563'`), never a shape regex. A pattern like `re.sub(rb'15[0-9][0-9]', new, ...)` with an empty substitution variable silently deletes every count in the file and breaks sentence structure across three documents at once.
- If a bulk edit goes wrong, `git checkout -- <the three files>` and redo with the exact-number replacement. Do not try to repair a mangled document by more substitution.
- Re-run the full suite afterwards: the four doc-contract tests are the only check that the numbers now agree with collection.

## Recovery after interrupted or oversized sessions

When a long xiaozhua Agent session stalls, a provider times out, or delegated work returns without verifiable completion:

1. Treat child summaries and historical test counts as claims, not current facts.
2. Recover from durable sources in this order: current filesystem, current tests/CLI execution, audit documents, then session transcript or exported conversation.
3. Inventory exact files and symbols before deciding work was lost. A tool transport/path error is `BLOCKED`, not proof that a file or repository is absent.
4. Run the current focused/full suite and record the new baseline separately from historical baselines. Never silently reuse an old `N passed` figure.
5. Write a compact recovery checkpoint containing current scope, verified artifacts, current failures, unverified work, safety boundaries, and the next executable step.
6. Resume from the smallest broken acceptance boundary instead of re-running the whole research program or redesigning the architecture.

For shared-worktree implementation, do not dispatch several agents to edit overlapping core files concurrently. Stabilization phases such as evidence-fixture recovery, schema migration, and test-baseline repair must have one writer. Later independent evidence-source probes may run in parallel, but the parent agent must read the resulting files, run the commands itself, and reconcile conflicts before reporting completion.

## Durable evidence fixtures

Tests and production-facing audit logic must not depend on disposable OS temporary directories or session cache paths. When prior research produced reusable, non-sensitive evidence:

- promote the smallest required subset into a versioned, redacted evidence bundle or repository fixture;
- include a manifest with schema version, source locator, target/application ID, artifact/version/SHA-256 where applicable, limitations, and expected files;
- preserve missing evidence as structured `UNVERIFIED`; do not replace absent files with historical hard-coded counts;
- keep raw sensitive or environment-specific dumps outside source control;
- test both complete and deliberately incomplete bundles;
- ensure documentation counts and audit summaries are derived from or checked against the current test collection rather than copied indefinitely.

A stable fixture proves deterministic offline behavior only. It does not promote the source environment to `LIVE PASS`.

## Recommended phase plan

### Phase 0 — reality audit
Inventory code, evidence files, tests, CLI, real/placeholder surfaces, version boundaries, and documentation drift.

### Phase 1 — evidence platform
Implement Result/Evidence/Status, provider error normalization, schema metadata, evidence ledger, conflict detection, and bounded reports.

### Phase 2 — read-only providers
Implement filesystem and offline fixtures first, then explicit live adapters for HTTP, Kubernetes, Nacos, MySQL metadata, and Redis metadata. Keep live tests opt-in.

### Phase 3 — UDC critical paths
Build the path matrix and close Application -> Entity -> Field -> Page/MicroFlow -> Generate -> Runtime Metadata with evidence references.

### Phase 4 — customer boundaries
Classify UDC Core versus Customer Extension versus SPI/Integration dependency only from source and dependency evidence.

### Phase 5 — consistency and impact
Model metadata, version, generated artifacts, runtime metadata, physical tables, Redis, events, and routes/assets. Mark inferred edges as unverified.

### Phase 6 — dry-run
Generate risk-scored, confirmation-gated, rollback-aware plans. Do not execute them.

### Phase 7 — smallest authorized live closure
Only after the gates pass, use a temporary test2 target and verify every state transition with trace/task/log/database/metadata/cache readback. Publish and deploy remain separate confirmations.

## Live read-only runtime evidence convergence

When offline profiles are stable, close runtime facts in a bounded sequence instead of resuming broad scans:

```text
Nacos dataId
  -> Kubernetes context/namespace
  -> Deployment/Service/Ingress/Endpoint
  -> Pod/Image/digest/log
  -> MySQL schema/table/application metadata
  -> Redis key pattern/type/TTL
  -> exact application route
```

Rules:

- Use an explicit environment-mapped kubeconfig. Read the active context and namespace before querying resources; do not infer environment from a filename, hostname, Pod name, or namespace alone.
- If a command-line client is absent, a verified read-only SDK/client library is an acceptable transport. Report transport success separately from target-layer success.
- A Deployment or image tag is a runtime inventory fact, not proof that the application is running. If desired/ready replicas or Endpoint addresses are zero, mark Pod logs, live JAR identity, and route success `UNAVAILABLE` or `UNVERIFIED`; never scale the workload merely to complete an audit.
- Keep UDC Platform and Customer UDC Application as separate profiles even when Kubernetes and Nacos evidence are collected together.
- For MySQL, distinguish server authentication, schema existence, table/column inventory, estimated table rows, and exact application rows. `information_schema.TABLES.TABLE_ROWS` is commonly an estimate. Use confirmed `app_id/guid` columns before counting application entities/pages/schemas/microflows.
- Preserve numeric state fields (`publish_state`, `state`, `deploy_type`) exactly until enum/source evidence explains them.
- Preserve database `show_version`, UDC app version, image tag, artifact version, digest, and SHA as separate evidence units. If their numbering differs, record a conflict/semantic gap rather than normalizing them.
- Redis timeouts mean cache evidence is `BLOCKED`, not that caching is absent. Use only `PING`, bounded `SCAN`, `TYPE`, and `TTL`; never `KEYS *`, writes, or full sensitive values.
- Persist only redacted summaries. Before delivery, scan reports for passwords, tokens, access/secret keys, private-key blocks, and kubeconfig material.
- **Pod 内探针用脚本文件 + 一次 exec**：把探针写成脚本文件、scp 到中间服务器，再 `kubectl exec -i -n <ns> <pod> -- sh -s < /tmp/<probe>.sh` 一次性送进去，避免几十次单独 exec；脚本内只放只读查询。环境变量只取键名（`printenv | grep '^PREFIX_' | cut -d= -f1`）并逐键标 PRESENT/ABSENT，绝不输出值、绝不全量 `env`/`printenv`。一次 exec 复跑全部只读结论，这本身就是可重复性证据。
- **带 timestamp 的响应体会天然破坏 md5 等价**：Nacos `ns/list` 一类 404 响应体内嵌服务端时间戳，同一查询 PRE/POST 的 md5 必然不同。可重复性判据 = HTTP 状态 + 响应结构 + 稳定字段；把不可比字段排除后仍不一致才算漂移，并在报告里明确写"md5 差异属预期"，否则会被读成环境在漂移。
- **单点负证据必须先升格范围再下结论**：一个 Pod 的 env/文件系统里看不到某坐标，只证明该 Pod。用纯 API 读取扩展范围（`kubectl get deploy -o jsonpath="{...env[*].name}"`、`kubectl get cm`），只有全部 Deployment 与 ConfigMap 都拿不到时，才能写成命名空间级负证据，并立即把只能由云侧或人工提供输入的项标成 NEEDS_HUMAN，而不是继续在 Pod 里换姿势重试。
- 明文凭据可能直接躺在 Deployment env 里（`NACOS_USERNAME` 形态就是云 AK ID）。只报告键名与所在对象、绝不复制值，并作为安全隐患建议改用 Secret/KMS 引用。

A runtime path becomes `LIVE PASS` only when a ready target, exact route response, matching contract, logs/trace, state readback, and digest/SHA-tied artifact identity are all connected. Otherwise report each layer independently.

## 客户问题清单：逐条复现 + 系统方案交付（verified）

当任务是"把某人名下的问题逐条看一遍，给复现和方案"，交付物默认是**一张表 +（可选）逐条长文附录**，不是叙述式长报告。

**交付形态（用户明确要求，且是被打回过的形态）**：用户要的是"列成一个表格"——列顺序固定 `序号 | 记录id | 状态 | 什么问题 | 发生原因 | 复现情况 | 怎么修改 | 代码位置`。md 表出全部行，同时落一份 xlsx（`auto_filter` + 冻结首行 + 状态配色，用户拿去筛选/转派）。逐条长文方案只做附录，**不能代替表格**：先给长文再补表格会被打回一句"不是你，现在就将 N 个问题列成一个表格"。**"代码位置"是必需列**，写真实产物路径/类:行号（反编译类、微流程入口控制器产物、客户扩展类）；确实只有设计器配置可取时写清落点类型（配置层：表单字段/页面规则/列表视图/微流程节点），绝不编造类名或文件名。聊天下发的版本可做前缀短化（`mail/`、`htdangan/`、`web/`、`ext.`）并在表头注明展开规则。表内 `状态`/`复现` 用短代码（`REPRODUCED`/`PARTIAL`/`BLOCKED_OFFLINE`），长解释留在附录。

逐条内容按下面的形状走：

1. **先定口径再取数**：明确"处理人=谁""排除哪些状态"，把被排除条目的记录 id 列在文档头，并写明数据快照时间。状态会迁移，旧导出不能当结论用。
2. **逐条四段齐全**：`编号/记录id ｜ 最新状态 ｜ 模块 ｜ 优先级`，下面接 **问题（业务原话要点）** ＋ **复现** ＋ **系统方案（落点 → 改法 → 验证）**。缺一段就是这条没做完。
3. **复现判定只允许三档，且必须写方式**：`REPRODUCED`（离线真跑出结果或字节码坐实，附可重跑脚本与真实输出片段）、`PARTIAL`（证据到边界，写清还差什么才能定论）、`BLOCKED_OFFLINE`（写最小复现步骤与所需环境）。**不许用"凭经验判断"冒充复现**；坐实不了就老实写 `BLOCKED_OFFLINE` + 复现步骤，这比编结论值钱。业务备注/测试记录里常带复现线索，先读再判定。
4. **复现要打到机制层，不止重现现象**："模板里没有/取值空"要落到模板占位符是否存在、取值表达式取的是哪个字段、上游事件有没有（订阅的是平台事件还是客户自建 MQ）。业务反馈与离线结论对上时（如"待办已加逗号、驳回标题前有，但加签识别不了"对上"平台无加签事件 + 靠文本包含判断节点"），说明复现打穿了 —— 写成结论，不要写成猜测。
5. **共因收敛 + 排序**：把 N 条收敛成少数共因簇（同一写入路径/同一监听缺失/同一取值口径），再按"改一处能连带清掉几条"排动手顺序。逐条平铺的长清单用户不会读。
6. **交付前覆盖校验**：脚本比对文档中的记录 id 集合 vs 源记录集（遗漏/多余/重复），把校验结论写进回复；文档内编号只是引用、以 id 为准。
7. **结尾必列"不猜的待真实验证点"**：每条写清需要什么输入（一次操作日志、一次抓包、某个外部接口、模板实件），并把"不需授权就能先做"与"需要环境/协调"分开。

离线复现客户应用邮件/事件链的取证配方见 `references/offline-mail-and-listener-forensics.md`。

## Generation surface delivery (requirement → skeleton code)

When the goal shifts from "evidence system" to "the agent must DO development" (generate backend/frontend artifacts), keep the evidence discipline while shipping a usable capability:

- **Build the generator on the existing ConstructionEngine plan, not beside it.** The plan's 8 artifact classes already encode the golden-sample contract; the renderer's job is declaration-level skeletons (package/class/extends from javap, fields from the observed type distribution) with `// UNVERIFIED` markers where method bodies would go. Deliver backend (Java skeleton per artifact) and frontend (page-definition JSON from the C2b LIVE 18-field set) as one `generate()` capability.
- **Parse requirements deterministically; never invent identifiers.**
- **Verified requirement-parser input shape** (dense-fail mode): entity line `新建一个实体「Name」标题：Caption` — `标题` must be followed by `：` or the caption regex misfires and the entity line stops matching (UNVERIFIED, no reason given); field lines `- name：type-alias` with NO trailing Chinese description (the `$`-anchored field regex rejects it); types must be in JAVA_TYPES or the alias map (`金额`/`小数`/`BigDecimal`, not `Decimal`). Anything else lands as `PASS_WITH_UNKNOWNS` or `UNVERIFIED` — feed the host LLM this shape instead of patching the parser per input. The requirement parser maps only the golden-observed type vocabulary (String/Long/BigDecimal/Boolean/Date…) and marks unrecognized types `UNVERIFIED` in its result instead of guessing; Chinese attribute names are NOT transliterated to pinyin (the pinyin conversion rule has no evidence) and land as `// UNVERIFIED` comments in the DTO skeleton for the host LLM to confirm. The verified host surface is one bootstrap dict with five capabilities: `dispatch` / `generate` / `generate_from_requirement` / `live_probe` / `agent`.
- **Deliver an interactive artifact, not another test harness.** This user explicitly rejects "an agent that tests forever" — the deliverable is a one-command entry (bootstrap + generate + live probe) the user can run and poke at. Tests guard the capability; they are not the deliverable. When the user says "快速推进，要可测试可交互的产物", prioritize the runnable entry over more test rounds.
- **User-framed capability requests override repo scaffolding defaults.** "记住 xiaozhua agent 不作为单独 agent，要能嵌入 Hermes/CC/Codex，实现基于主流 agent 框架的开发功能，关键是配置文件和初始化脚本" — the answer is a single bootstrap function + per-host wiring docs, checked in, verified end-to-end (offline AND live) before reporting. Not a new test file, not a plan document.
- **Design-time write capability ships as PLAN DATA by default; when the user explicitly opens the write channel, ship it as an authorization object, not by deleting the gate.** Never "just remove" the three deny points (`layer.execute`'s `contract.write` check, `policy.MUTATING_METHODS`, the registry's missing write contracts) — that turns a read-only skeleton into arbitrary write. The verified shape: a `WriteScope` object carrying **(a)** an operation whitelist, **(b)** an application whitelist, **(c)** a `max_writes` budget, defaulting to *empty = deny everything*. `layer.execute(..., write_scope=None)` keeps the old DENY path byte-for-byte when the argument is omitted (so the existing read-only suite stays green), and only consults the scope when one is passed. A separate `WriteExecutor` issues the POST and records evidence (url/body/http/traceId/readback) — keep it out of the read-only `PlatformOperationLayer` so its GET identity-verify path stays simple.
- **Fail-fast is part of the contract, not a convenience**: the user's standing instruction is 「失败即停、报告不动」/ no automatic retry. Implement it in the scope object (`record_failure` → `aborted=True` → every later write refused with a reason that says "不重试"), and make the executor call it on *any* failure — transport exception, non-2xx, or business `status != 0`. A scope that silently resets after a failure has broken the agreement.
- **Success predicate for a write = `HTTP 2xx AND business status == 0`**, never either alone. `BOOT_0000` and `HTTP 200` are envelope noise; a write that returns 200 with `status:3` did not happen. Readback afterwards is a *separate* boolean (`readback_ok`) and must not flip the write verdict either way — a failed readback after a successful write is a readback gap, not a failed write. **Default path (unchanged) — plan data executed by the host:** the working pattern (live-verified end to end on test2: entity → attributes → pages → RELEASE build → physical table) is a plan generator (`deployment.py build_deployment_plan` / `host["deploy_plan"]`) emits ordered steps, each carrying the exact live-proven body, a `verify` readback, the live value domains (stereotype/dataType/deploy enums), and an `unknowns` list for anything inferred; the authorized host executes the steps against the gateway and reads back. Tests pin the plan shape (step order, required-field chain, DENIED regression for the write contract) — the agent stays readonly and the host does the writes. Full detail: xiaozhua-platform-operation-contracts skill, `references/udc-design-time-write-chain.md`.
- **Converge unknown write contracts with the validation-error oracle, not docs.** POST the best-guess body; the platform's `BOOT_1001 <field> must not be null` reply names the next required field; repeat until BOOT_0000. The entity chain converged in ~6 calls (appId-numeric → stereotype → entityNature → full bill shape) and the page chain in 5 (pageType → pageUrl → curTerminalType → actionType enum → success). Every error message is a contract fact — record the chain, because it doubles as the required-field documentation.
- Fix-in-place rule still applies to generated code: a renderer bug that emits `extends class` is fixed at the unpacking site with focused tests pinning each artifact type — the full suite + doc-count sync is the same change, not a follow-up.

### Verified write-path dictionary for test2 UDC (entity→deploy→metadata→create-app)

The read-only chain is proven; the write chain has its own live-verified dictionary. All entries below are test2 LIVE (three-source: live call + udc pod log + javap). Full parameter tables, failure matrix, and the CDP browser-automation recipe live in the environment skill (`xiaozhua-low-code-environment`, `references/test2-write-chain-api.md`) — parameter names are contract-exact from bytecode annotations, never inferred:

- Entity create `POST /service/udc/entity` → LIVE PASS. `appId` must be numeric Long (read it from `GET /service/{app}/app-info/deploy-info`); `name` alphanumeric-only (UDC_ENTITY_0026 rejects underscores/trailing digits); bill vs standard stereotype changes the attribute template (45 vs 9).
- Deploy `POST /service/udc/runtime/deploy-normal` body `{"deployDto":{appId, deployType:"TEST", projectType:"ALL", terminalType:"ALL"}}` → LIVE PASS ×3. Async pipeline ~2–5 min for TEST (verify by readback: `SELECT state,jar_version,msg FROM udc_deploy_record WHERE deploy_id=?` — state 0=in-flight, 1=success, 2=failed; poll ≥60s apart). deployType=3/business_type mismatched shapes fail with 「目标环境为空」— use the TEST/ALL/ALL shape. Physical tables land in the app-own schema (`{appName}_test2`), never `udc_test2`; the sandbox pod is recreated by the build — a fresh pod age ≈ build time confirms the deploy actually shipped.
- Metadata `POST /service/{app}/udc-runtime/meta-data/select-entity` body `{fullName, appName}` → LIVE PASS; entities register into the metadata center only after a successful deploy (UNPUBLISH entities are invisible there). Runtime entity fullName rule (verified from the sandbox pod's biz jar, not guessed): `com.seeyon.{app_name}.domain.entity.{Entity}` — the `.domain.entity` segments live in the **biz** jar (`domain/entity/X.class`), the facade jar carries only `dto/`+`api/`; wrong fullName = BOOT_1000 实体类不存在. Attribute/batch/update/delete faces and the storage mechanism (MySQL authoritative at design time → publish exports to Redis Hash 180h TTL + OSS mirror; `presetData/attribute.json` is ONLY the bill system-attribute template) — see the repo's `core/facts/udc/metadata-storage.md` and `attribute-create.md` for the closed nine-section facts.
- Create page-only app `POST /service/{app}/udc-runtime/custom-app/create` → BLOCKED (platform NPE `create4CustomPage:892`, reproduced on two entity templates). Key contract fact: `masterEntity` is a BARE fullName string, not JSON (bytecode: `setFullName(masterEntity)` passes it straight through); a JSON body fails deserialization to String.
- Entity delete: GraphQL `POST /service/udc/graphql` mutation `udcEntityDeletePost` body `{"id":"<id>"}` → LIVE PASS ×2 with readback. This graphql face carries all `udcXxxPost` mutations; an unknown mutation name returns `UnknownType`, which is a cheap existence probe.
- DataFlow mapping save `udcDataFlowMappingUpdatePost` → LIVE PASS. The two fields that look interchangeable are not: `udc_data_flow.definition` is the **canvas** (`{lines,nodes,transform}`, `nodes[].id = "id_<entityId>"`) as a String, while `udc_data_flow_mapping.rule_info` is the **mapping detail** (`{validate,rules[]}`) also as a String. Sending one where the other belongs produces `MAPPING_QUOTE_OBJECT_NOT_EXIST_ERROR` (UDC_DATAFLOW_0043) that no amount of reference-tweaking fixes. Envelope shape is `{id, appId, caption, name, definition, dataFlowMappingDto:{id, appId(Long), appName, caption, name, dataFlowId, triggerPoint, source*/target* , mappingDetailDto}}` — the OUTER `id` must be the data-flow id (the service does `setDataFlowId(dto.getId())`), `triggerPoint` enum is `MANUALLY`/`EVENT_SUBSCRIBE`, Long fields reject strings, and each `mappingRow`'s source/target must share a data type or the save returns `UDC_DATAFLOW_0004`. Contract converged by reading the decompiled service method, not by error-message guessing: locate the `setDataFlowId(...)`/`setRuleInfo(...)` call sites first.

**status:2 silent-failure rule**: HTTP 200 + `{"status":2,"code":null}` is a business-layer failure with zero response information — never count it as an attempt-result; take the traceId straight to the server log (`kubectl logs <udc-pod> | grep <traceId>`), where `AppService Exception Occur, CODE:BOOT_1000,MESSAGE:<中文原因>` states the real cause and echoes the request body. Error-driven probing (BOOT_1001 `<field> must not be null`) is the contract oracle for required fields, but once a failure goes silent, log-first beats body-guessing.

**Boundary rule (user-enforced, zero tolerance)**: 「新建测试应用」 authorization means creating an INDEPENDENT app on the platform — never creating entities or triggering deploys inside an existing business application (e.g. znxmglpt). Any write inside a business app mutates its version/metadata; the user will stop you mid-run. Clean up test entities with the delete mutation + readback; a triggered TEST deploy cannot be un-published but is functionally inert.

### 设计态搭建链（实体→属性→页面→菜单，全部 LIVE 实测于 zzprobe）

「需求→搭建」不只需要生成方案——整条设计态写链已可全自动执行，配方见 `references/udc-design-state-build-chain.md`。关键规则：

- **建属性是单条对象 body**（appId/entityId/name/caption/dataType），数组包装报 BOOT_3002；字段名撞平台保留字（如 `orderNo`）报 UDC_ENTITY_0002，换名即过，不是参数错误。
- **菜单创建不需要部署**：走平台级 `/service/udc/graphql` 的 `udcPageInfoBaseInfoCreatePost` mutation；设计器登录态用 cookie 注入（SY_ACCESS_TOKEN/TK_EXP/SY_UID → `.客户方.com`）获得，绕过 SSO 动态口令。「必须先部署」是已被实测推翻的推断——需要部署的只有应用沙箱面（{appName}/graphql、运行态 data）。
- **全量推送测试**：修执行层后把全部 GET 契约对目标应用实跑一遍，矩阵状态各自定性（PASS/UNVERIFIED/DENIED/FAIL/缺参），每格都有明确含义；这个方法已两次抓出执行层真 bug（网关前缀双形态、appId Long 形态）。
- **Long 数字形态**：设计态 {appId}/{id} 占位符要求 Long 数字，带前缀 app 名被 NumberFormatException 拒——取名字里的数字段，identity 比对同样归一。
- **网关前缀三形态**（实测修正）：设计态 `/udc/*` → `/service` + path；运行态 `udc-runtime/*` → `/service/{appName}/udc-runtime/*`（按 appName 路由到该应用的沙箱 pod）。裸 `/service/udc-runtime/*` 与 `/service/udc/udc-runtime/*` 均 server_404「服务不存在」——这不是服务挂了，是路由形态错，换 appName 前缀即通。
- **网关适配器返回的 body 必须是 dict**：字符串 body 让 `_normalize` 返回 None，验证链静默降 UNVERIFIED。

### Token 续期与凭据活性

- test2 web token 会提前失效（SSO 弹 BOOT_1006 redirectUrl），不等 24h 窗口走完。续期 = `requests.Session` POST `shared-credentials/ctp-user-login.json` 里存的 endpoint+body，成功后 session cookie 三件套（SY_ACCESS_TOKEN/TK_EXP/SY_UID）全活，无需人工。
- 判断凭据死活用最小 GET（如 `/service/udc/entity/primary/select-by-appid/{appId}`）：HTTP 200 + `BOOT_1006` = SSO 失效需续期；`BOOT_0000` = 活。
- 所有活体请求都走同一个 `requests.Session`（verify=False），cookie 自动续传；不要每发都手拼 Cookie 头。

### 端到端样板链验证配方（设计态→发布→运行态，全链 LIVE 已闭）

「设计态建好但运行态看不到」的验证顺序，每步都有明确判据：

1. 设计态落库：`udc_test2.udc_entity`/`udc_attribute` 按实体 id 回读行数与业务字段名。
2. 点火发布：deploy-normal（TEST/ALL/ALL 形态）→ BOOT_0000 + deployId。
3. 构建收敛：`udc_deploy_record` 轮询 state（0→1 成功/2 失败），物理表 DDL 落应用自身库（`{appName}_test2`），沙箱 pod 新建（pod AGE ≈ 构建时刻）。
4. 运行态读面：`/service/{appName}/udc-runtime/meta-data/select-host-and-only-page-pages` 与 `rt-page-log/search` → BOOT_0000 即元数据面可达；`data/query` 需 `dataId`，空表场景不冒充 PASS。
5. 全名规则：`com.seeyon.{app_name}.domain.entity.{Entity}`（biz jar 实证）。

### 建议与边界修正（本轮实测沉淀）

- 探测新写端点前先在浏览器（CDP 独立 Edge + 页面 cookie）里用 `fetch` 走一遍：页面上下文的请求自动带网关签名，纯 API 直调会被 405/签名拦截（已实测：`POST /service/udc/application/create` 字节码确诊存在但 API 直调 405，请求到 pod 未进 handler）。CDP websocket 连接必须带 `origin`，且 Edge 需 `--remote-allow-origins=*`。
- UDC 运行态页面 URL 形态 = `/main/portal/{appName}/{pageName}`；平台「应用管理」页不在门户菜单里，最务实的建应用路径是让用户在界面手工建空应用后拿 appGuid。

### 子代理（delegation）模型路由

- delegation 的 `provider`+`model` 必须是真实存在的组合（查 config.yaml 的 providers.models 清单）：一个模型名注册在某个 provider 下不代表其它 provider 也能路由它——错配会得到 HTTP 503 「No available channel for model X」，看报错里的模型名就能定位错配。
- 改 delegation 配置用 `hermes config set delegation.provider <p> && hermes config set delegation.model <m>`（write_file 对 config.yaml 被 gate 拒绝，不要硬试）。
- 免费/低额度 provider 跑并发子代理容易 429 限速：三个并发任务挤一个免费 key 时基本全灭。反编译 jar、全仓扫描这类可离线自做的活，优先自己干，不要为了「快」下发给会被限速的通道。

### 反编译工具链（UDC jar 取证的标准路径）

- CFR 位置：`<HERMES_HOME>/skills/seeyon/03-v8-extension/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar`，本机 java 21 可用；用法 `java -jar cfr.jar <class文件>`。
- jar 来源优先级：本地 `<MAVEN_REPO>/com/seeyon/<module>/5.3.517/` → Artifactory `http://10.0.0.1/artifactory/libs-release/com/seeyon/<module>/5.3.517/`。`udc-biz`/`udc-web` 只在 Artifactory。
- 实现类定位：facade jar 只有接口（如 `com.seeyon.udc.api.EntityAppService`）；Impl 在 **udc-biz**（`com.seeyon.udc.appservice.EntityAppServiceImpl`），domain 逻辑在其下 `entity/domain/service/`，DTO/实体在 `entity/domain/entity/`。facade jar 里 `grep Impl` 零命中是预期，不要在错误 jar 里反复换关键词。
- 追落库链的终态锚点：实体/属性类上的 `@Table(name=...)` 注解就是 MySQL 表名（`udc_entity`/`udc_attribute`），Dao 是 `BaseMybatisDao<T>`；到 `@Table` 即闭合，不用再往下挖 MyBatis XML。

## UDC 样板链九段格推进（「继续推进 xiaozhua-agent / UDC 域」的正确动作）

被要求「推进 xiaozhua-agent / 继续 UDC 域」时，不要接着刚做完的诊断任务写沉淀——客户 bug 处置与 xiaozhua-agent 开发是两条独立工作线，即便用户同一条消息里都提到，后者才是任务、前者只是已结背景。推进 = 按 ROADMAP 样板链补下一格九段 Capability 格（`entity.create → attribute.create → page.create → deploy.normal`）：

1. **先重锚定位**：`docs/capability/STATUS.md`（A 八件套 + B 格勾选表）是唯一活跃账本——协作目录 `main/` 的路由/心跳件已冻结过时，不要拿它当现状。配合 `git log --oneline`、`find core/facts/udc -name '*.md'`、全量套件跑一遍取当下基线。
2. **下一格 = 样板链中缺九段格的那步**。格所需证据应全部已在盘（registry 契约行、deployment.py step note、`core/facts/udc/write-chain/evidence/` 的 json/jsonl）——补格本身不需要活体调用、不需要凭据；若发现必须现取新证据才能写格，说明选错了下一格。
3. **九段形状照 B1**（`core/facts/udc/entity/create.md`）：Capability/Version/Input/Required/Execution/Side Effects/Known Constraints/Evidence/Verified + 溯源索引；每段锚 file:line 或证据件+要点；无活体回读的端点/面（如 batch、update/delete）逐项标 UNVERIFIED 不承诺。
4. **落盘后**：STATUS.md 的 B 项登记勾选（附实测记录一行）→ 全量套件回归（纯 md 改动通过数必须不变）→ 本地 commit，不 push。

**边界（用户强制，零容忍）**：客户 bug 的诊断内容不得写入 xiaozhua-agent——包括把客户事故抽象成「平台机制」格。core/facts 只收样板链 capability 格与有在盘证据的平台事实；客户场景明细最多进独立客户证据仓，且当用户说「客户的东西有问题/去掉」时，xiaozhua-agent 里的格与其在客户仓的镜像件一并删除，不降级保留、不反问。

## 补齐核心域内容：厚实审计证据 → 可执行模型 + 全域覆盖审计（verified）

当用户说「这几个核心域你缺少很多用法，全部补齐内容，然后做审计测试每个地方都要测试到」「别问我就行 / 一直推」时，这是**补齐代码能力**而非继续取证的任务类。

1. **先诊断缺口在哪**：读仓库 homebase（哪些 domain 已有可执行 model/contract/validator，哪些只有 doc 审计）。用户抱怨「很多用法你不知道」的根因通常是**证据厚在 doc、没进代码**——此时停止重新 CDP 抓包（低收益、且反复卡在同一交互），转去把已取证值域搬进可执行模型。某条 CDP 交互（如画布打开链）连卡 2-3 轮仍 UNVERIFIED 时判为低收益路径，明确放弃并登记，不耗时间。
2. **逐域建可执行落点**：每个域产出一个 model/validator 或 op-catalog，只填**源码/字节码/活体已证**的值域与结构，未知项进 unknowns/warnings 不臆造。例：微流程节点/动作模型锁 8 控制节点 + 4 组活动值域 + CONVERT_DATA 11 值受控 + 前端 10 项创建类型映射；页面事件校验器锁 actionType 4 值 + buildin 穿透/wIDGET 行删/面板/微流程按钮必绑 id。
3. **加全域覆盖审计测试**：一个 coverage-matrix 测试断言**每个导航域都有可执行落点 + 引用的 registry op-id 都真实登记**（这条能抓出臆造的 op 名）+ 覆盖矩阵可落盘。缺一个域就 FAIL——这是「每个地方都要测试到」的可执行形态。
   **从 bundle 扫描生成的 op 目录必须配一个对账测试**：逐条断言 `fieldType:"<op>"` 与其 paramsType/paramsKey 三元组在源 bundle 文本里逐字存在——凭记忆/旧笔记补的条目会被对账抓出（实测：一个只在写链冒烟 LIVE 用过的删除 op 被误登记为 bundle 扫描产物，对账测试当场标出）。**不同证据源的条目分节登记**：bundle 扫描（STATIC）与 LIVE 冒烟（OBSERVED_LIVE）不混在同一列表里，各自标 source；否则下次全仓重扫会把「bundle 没有的」当目录缺陷删掉，丢掉真实 LIVE 证据。**同一 bundle 里存在多种 service 约定时（saga `load({fieldType, paramsType, paramsKey})` 与 raw Apollo 文档字符串 `(mutation|query) op ($body: …InputBody)` 并存是常态），扫描器必须每约定一个正则，臆造判定每约定一路存在性检查再 OR**——只扫单一约定会静默漏整族 op，漏扫的条目下次补登记后会被单约定对账误判臆造。**约定扩展要三处同步**（扫描器正则/归一 → 对账测试判定 helper → 目录条目）：只改扫描器不改测试，回归当场红（实测：补 18 个新约定 op 后 2 个对账测试仍按单一约定硬校验而失败，修 helper 即绿）。
4. **构建面计划器与只读计划器必须分开**（`UdcPlanner` 类）：`plan()`/`plan_application()` 是既有只读契约（有硬测试钉住 `mode=="dry-run"` + `write_operations==[]`），永不能改产写操作；新增构建面逻辑一律另开 `plan_build(spec)` 方法。构建计划每步带 `channel(graphql|rest)` + `op` + `body_builder` + `evidence` 分级；**引用 op 必须经内部 `op_entry(op)` 解析成功才入步，解析不出 → 落 unknowns，绝不臆造 op 名**；spec 列表里未声明的对象也不臆造生成（只落 unknowns 提示扩展 spec）。破坏性步骤（Deploy ON_ONLINE）标 `destructive` 交宿主先确认；`executed/writes_performed` 恒 False。
   - **`body_builder` 字符串必须指真实可导入的模块全路径**：曾把 `components/construction/metadata_artifacts.py` 的构造器写成裸 `metadata_artifacts.xxx`（宿主会去 `components/udc/` 下找而落空）。跨包引用统一写 `construction.metadata_artifacts.*` / `construction.microflow.*`；同包内写同级模块名。**加一条可解析性测试钉住**：正则抽出计划里每个 `模块.符号`，`importlib.import_module` 后 `hasattr` 断言存在。
   - **spec 模型扩展只用带默认值的可选字段，向后兼容**：给 dataclass 加字段一律带默认（`field(default_factory=list)` / `None` / `""`），既有调用方的构造不破；`to_dict` 只序列化非默认值。验证法 = 一条旧式最小构造 + 一条全语义构造各跑一次，断言旧输出字典逐键不变。
5. **事件 tab 写链坐实为 `udcEventCreateWithDataPost` 而非 `udcEventPost`**：实体「事件」tab 的「新建事件」主链（组件 77200 `createEventWithData`）走带 `eventDataList` 的 createWithData 形态，`udcEventPost` 只是裸事件；按名字猜成后者是错映射。且 `eventDataType` 的字面值要从 bundle 枚举挖（`d.pe.Object` → module 65420 → `"OBJECT"`，不是 `"Object"`）——符号引用的字面值未坐实前不要写字符串常量。
6. **证据级封顶 + 对象边界**（把 CDP 抓取的端点转 op-catalog 时）：独立微服务段（`/service/cdp-data/`、`/service/bpm/`）是 Extension/标品服务，**不是 udc 表**，独立建档不改归属；CDP 活体抓取的端点证据级封顶 `OBSERVED_LIVE`，**不得升 `VERIFIED_STATIC_BYTECODE`**（没 javap）；POST 查询型 op 在 GET-only 执行链上维持 `POLICY_DENIED`（与 udc.metadata.page_tree 同边界），别误标成只读放行。
7. **validator 设计陷阱**：缺「推荐键」（如 caption/output）的软警告只对活动/数据节点约束——控制节点（END 等）本无 output，若对它警告会把合法 schema 误判 UNVERIFIED，测试会红。
8. **诚实登记未尽**：每轮补完写 round 审计记录，逐项标 UNVERIFIED/BLOCKED/未做（写链依赖的 app 构建链是 FAIL → 写操作 BLOCKED；面板 UdcPanel 无字段级证据 → 只锁动作名不锁字段；构建必须走页面点击、未抓包 → 未做）。不谎称完成。

## Common pitfalls

- 报「本应用有 N 个 X」却没加 `WHERE app_id`：把全库聚合数当单应用事实，量级可差数倍。先在 SQL 里过滤应用再谈口径，位置/主键的严谨不能补救范围的缺失。
- 多脚本一致性的判据写成 `exit==0`：错实现同样返回 0。判据必须是「解析出的数字集合完全相等」。
- Continuing broad static scans after high-value facts are sufficient.
- 在压缩 bundle 的正则扫描里避免 `\b` 词边界：bundle 的 JS 字符串转义使 op 名前面常是字面 `n`（`"\nmutation udcXxx…"`），相邻 word 字符时 `\b` 不成立、整族 op 静默漏扫。判定正则修好必须对 bundle 全文计数命中数，不能只在干净样本上单测通过；改用语义锚点（`mutation|query` + `udc` 前缀 + 紧随 `($key:` 变量声明）。
- 长期工作区做 `git add -A` 前 `git status --porcelain` 逐行过暂存集：前序会话遗留的未跟踪文件会静混进本轮 commit。自己的改动单独 add，遗留件另行处置或单独 commit，并在 message 里说明带进了什么。
- 全仓语法体检用 `python -m compileall -q <dirs>` 而非只跑 pytest：能抓出被 git 提交进来、pytest 根本不 import 的截断/坏孤儿文件（无引用且内容不可恢复时直接 `git rm`，历史可找回，不猜内容修复）。
- 在用户点破边界错误（如在业务应用里建测试数据）后，先修边界并清理残留，再继续原任务——不要辩解或降格为"影响可控"；清理必须用正式接口 + 回读验证（如 udcEntityDeletePost 删实体后 GET 确认为空）。
- 把"逐条问题清单"当交付：没有复现判定、没收敛共因、没做覆盖校验的文档，用户只会再问一遍"到底什么问题、怎么修"。每条必须同时有 问题/复现/方案 三段，编号错位也要靠 id 覆盖校验发现。
- 用叙述式长文（或只给附录）当问题清单交付：用户要的是固定列表格 + 可筛选 xlsx，且每行必须有代码位置/落点。"代码位置"列凭空写类名或文件名，比老实写"（配置层：表单/规则/微流程节点）"更糟——下游拿着假路径排期。
- 建属性成功的计数必须按业务字段清单核对，不能拿总属性行数当成果：bill 实体建壳时平台按 `presetData/attribute.json` 模板自动补几十条系统列（流程/作废/挂起/单据编号等），同秒全部落库——「50 个字段建成」的声明必须逐名回读业务字段（DB `WHERE name IN (<业务清单>)`），把系统列算进成果就是虚报，用户会逐条核对并打回。
- 在反编译产物的中文字面量上反复尝试解码还原：javap/反编译后中文常已不可逆损坏（U+FFFD + 残留字节），gbk/latin1 硬解只会得到乱码。改走 ASCII 完整的类名/方法名/节点 ID、带 captions 的摘要产物，或真跑一次取输出。
- Calling a local snapshot or fixture a live integration.
- Treating a 2xx response as proof of persistence.
- Treating a single customer or version as a universal platform contract.
- 用客户 bug 诊断内容「推进 xiaozhua-agent」：从客户事故抽象出的机制文档同样是客户沉淀，写进 core/facts 就是越界。被点破后整份删除（含客户证据仓里的镜像件），然后回 `docs/capability/STATUS.md` 找样板链缺口重定位——不要用辩解或搬仓代替删除。
- Treating class/member compatibility as behavior compatibility.
- Letting a generic fallback count or stale report hide missing evidence.
- Adding a provider without testing its default security boundary.
- Adding CLI commands without subprocess tests and explicit network status.
- Updating code but leaving test counts and audit reports stale.
- Stopping after a plan or stub without executing focused tests, the full suite, and compile checks.
- Trusting a closure report's claims (test counts, "closed" items, live status) instead of re-running pytest, reading evidence JSONs, and grepping the CLI for wiring gaps.
- Moving a directory as "cleanup" without checking whether git tracks it. `scratch/` and similar can be tracked; `shutil.move` on a tracked directory turns into hundreds of ` D path` entries in `git status` and looks like mass deletion. Run `git ls-files <dir> | head` first; if it is tracked, leave it in place and only prune genuinely regenerable artifacts (`__pycache__`, `.pytest_cache`) with untracked-directory checks.
- Reporting "N workers alive / logs are updating" as progress. Process liveness and heartbeat freshness are not business progress; a fleet can be green while every role spends its turns re-polishing a 4096-byte report. Judge by whether a new platform fact or a reproducible business effect landed.
- **Claiming an agent capability from the presence of a skill script.** Measure what the agent's **own** entry points can do: run its declared contracts one by one and classify PASS / UNVERIFIED(needs id) / FAIL. DB readback, page clicks and build triggering are frequently executed by out-of-repo skill scripts, not by the agent — say which layer produced the evidence. **在用户问「你现在到底会什么」时，这条是硬要求：报一张逐契约实测表，并单独说明哪些证据来自仓外脚本。** 用「N 个契约、仓库结构如何」代替逐条实测，是把库存当能力。
- **知道接口却没能力调用 = 能力空洞。** 域目录里记着「分类_创建 -> SomeController.create」，而仓库里没有构造器、没有校验器、registry 里也没有这条契约——这说明接口被识别过但从未被接通。补齐路径固定为：副作用自由的构造器 → 本地校验器（拦下平台会静默放行的形状）→ registry 契约（带 write/read 标志与证据指针）→ 测试。**判断依据是 agent 自己的入口能不能跑到它，不是文档写没写。**
- **事实文件不登记索引 = 没写。** 事实格落在 `core/facts/<module>/<domain>/` 但 `core/facts/INDEX.md` 没有对应行，检索就不到，下一次会话会重新推导出同一份契约。写完事实格必须同时加索引行，并用一个测试断言「事实文件存在 且 被索引登记」——三者（代码、事实、索引）脱节时测试要能报出来。
- **同一事实的两处副本必须一致，且要显式作废旧说法。** 契约被修正后，事实文件里旧的错误说法必须同文件内标为已作废（列表：旧说法 → 现状），否则下一个会话读到自相矛盾的事实文件会重踏同一个坑。静默矛盾比从未写更糟。
- **Measuring capability by declared-contract count instead of by execution.** Running all `effective=True` contracts one by one is the only honest denominator: on this repo 33 executable contracts yielded 6 PASS, 22 UNVERIFIED (missing path ids), 5 FAIL — a fraction that no count of `len(registry)` would ever reveal. When the user asks "现在能用它干什么", answer with that per-contract table, not the registry size.
- **Reporting `0 references` when the scan never covered the right column.** Before publishing a dependency/usage count, print the actual column list of the target table and pick the long-text columns explicitly; getting the column name wrong yields a confident `0` that reads exactly like a real negative. Say `未覆盖` when the scan could not cover a source, never `0`.
- **Serving a browser-rendered document as "extracted" when only the outline came back.** Canvas-/virtualized-rendered docs (Tencent Docs and friends) return the table of contents in `innerText` and nothing else; the body never becomes DOM text. Check `document.querySelectorAll('canvas')` and the app's model objects before claiming the content was read, and tell the user which export format you need instead of attempting OCR of a hundred pages.
- Working in an evidence-heavy repo with no `.git`; baseline commit is the first corrective action, not a nice-to-have.
- Reverting on a "去掉/撤销你刚加的那部分" instruction without checking version control first. This user commits and reverts your edits himself, so run `git status --porcelain` + `git log --oneline -5` + `git log -S <symbol>` before touching a file: if the change is already committed (possibly under the user's own message) or already gone, editing again either destroys a landed fix or re-adds code you were asked to remove.
- Mixing static-evidence artifact versions (local udc 5.3.517) with live-gateway versions in one claim; keep them as separate evidence units.
- Copy-paste CLI growth: new branches using module-level names (`Path`) that were only imported inside another branch → runtime NameError; audit top-of-file imports after branch additions.
- In a long-lived execution kernel (Hermes execute_code), editing a shared component does NOT refresh already-imported modules: tracebacks then cite line numbers and code (`no readonly adapter mapping` at line 63) that no longer exist on disk. When disk and traceback disagree, `del sys.modules[...]` for the package and re-import — or verify via a fresh `pytest` subprocess, which always reads disk. Clearing `__pycache__` alone is insufficient.
- A new third-party import in a SHARED component reds the whole suite at collection time, not one test. `components/platform_operations/` is imported transitively by everything, so a module-level `import yaml` added there while `pyproject.toml` has no `dependencies` section makes pytest abort with `Interrupted: N errors during collection` / `ModuleNotFoundError` — N unrelated modules, one cause. Read the first traceback before assuming N problems, then fix it at the dependency level (`dependencies = ["pyyaml>=6.0"]` in `[project]`; `uv run` syncs the venv on the next invocation — do not vendor a parser or hand-roll a YAML subset to dodge the dependency), and re-run the FULL suite: sibling sessions write to the same tree, so the only trustworthy count is one you just ran yourself.

## References

- `references/session-evidence-baseline.md` — reusable evidence/status baseline and observed xiaozhua/UDC audit boundaries.
- `references/phase-checklists.md` — compact phase gates, commands, and acceptance criteria.
- `references/evidence-bundle-policy-profile-convergence.md` — stable fixture bundles, load-status vs claim-status, executable PolicyGate, four-profile builder, and capability-to-real-inspect closure pattern.
- `references/repo-drift-audit-runbook.md` — 2026-09-14 verified drift-audit commands, workstream status table, git-baseline procedure, op-execute wiring notes, and verification gates for `<XIAOZHUA_AGENT_ROOT>`.
- `references/evidence-ledger-integrity-audit.md` — 冻结集 SHA 复算配方：严格引用匹配、不吻合逐条分类、报告形态。
- `references/gate-truth-verification.md` — 契约闸门真伪验证：注入层级分类（改文档/改期望值/空转检测循环各证什么）、元层验证、窗口掩盖因素三端对照、「无条件」类判据建模、控制字符死断言、方法边界切错导致的假数字。
- `references/offline-mail-and-listener-forensics.md` — 离线复现客户应用邮件/事件链的取证配方：客户包与标品包定位、模板抽取、监听器/MQ 枚举，以及"加签这类事件到底存不存在"的判定方法。
- `references/issue-table-and-code-location-delivery.md` — 问题清单表格化交付与"代码位置"锚定配方：固定列、md/xlsx 生成形状、覆盖校验脚本、反编译/微流程产物定位来源、mojibake 陷阱。
- `references/udc-domain-status-audit.md` — 多域状态审计的输出形状（五值状态表 + 逐域五段）、取数顺序、VACUUM/未做/数据在但能力不在 三种判定的区分，以及按证据成熟度把九域拆成并行任务时的四类分法。
- `references/live-provider-and-db-readback.md` — 把 `mode=fixture` 的 provider 升级成真实只读客户端：ProviderError 不可抛的约定与内部异常载体、多 schema 寻址（不绑定单库）、凭据三级解析、只读 SQL 门的分层、离线假连接测试形状，以及 `op-execute` 的 credential-ref 对齐坑。
