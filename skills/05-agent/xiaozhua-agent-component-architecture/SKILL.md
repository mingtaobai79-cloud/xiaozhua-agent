---
name: xiaozhua-agent-component-architecture
description: Use when building a modular xiaozhua Agent component system or defining its capability/platform architecture.
version: 0.2.0
author: Hermes curator
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [xiaozhua, agent, components, udc, spi, runtime, integration, adapters, capability, roadmap]
    related_skills: [xiaozhua-udc-runtime, xiaozhua-v8-spi, xiaozhua-platform-operation-contracts]
---

# xiaozhua Agent Component Architecture

## Purpose

Build one xiaozhua Agent entry point composed of independent domain components. UDC is a platform component, not the whole conversational agent. SPI, Runtime, Integration, Workflow, Organization and other capabilities remain sibling components under a shared Core.

## Target architecture

```text
xiaozhua Agent
├── Core
│   ├── intent/routing
│   ├── context/session
│   ├── planning/execution
│   ├── evidence/verification
│   └── safety policy
├── Components
│   ├── udc
│   ├── spi
│   ├── runtime
│   ├── integration
│   └── workflow
├── Providers
│   ├── kubernetes
│   ├── mysql
│   ├── redis
│   ├── nacos
│   ├── http
│   └── browser
└── Adapters
    ├── host-agent/python
    ├── mcp
    ├── http
    └── cli
```

## Boundary rules

1. A domain component must not own the host conversation, LLM, global tool registry or user identity.
2. Host integrations inject Context, Session, Tool and Policy ports. Standalone mode may use default in-memory implementations.
3. UDC and SPI are sibling components. Do not create a default UDC-to-SPI call chain. A customer `ext` dependency on an SPI requires code/dependency evidence.
4. Providers expose infrastructure ports; components should not scatter direct `kubectl`, SQL, Redis CLI or curl calls through business logic.
5. Write operations, publish, deploy, restart, cache deletion and runtime metadata changes require an explicit policy decision and read-back verification.

## Component contract

Each component should expose:

```text
name
capabilities()
inspect(request)
plan(request)
execute(request)
```

The first usable implementation should be read-only and dry-run capable. Unsupported writes must return a structured denial rather than silently executing or pretending success.

## UDC component contract

UDC belongs under `components/udc/` and is organized by:

```text
model/
contract/
version/
adapters/
analyzers/
planners/
executors/
evidence/
```

Its first useful slice should load existing UDC evidence catalogs, preserve FACT/OBSERVATION/HYPOTHESIS/UNVERIFIED distinctions, report application/entity/page/microflow/version/deployment domains, and produce a no-write plan.

Known UDC evidence must remain distinct:

```text
frontend remoteEntry/chunks and loader contracts
UDC Web Controller/DTO contracts
Service/DAO/runtime/cache/event evidence
autocode/publish/deploy evidence
customer frontend/web/facade/biz/ext artifacts
artifact + version + sha256 compatibility evidence
```

Do not turn a customer application ID, table name, field name or external URL into Core configuration.

## Turning a platform domain into a first-class capability (five landings)

A domain is not part of the agent because a document mentions it. It is part of the agent only when all five landings exist, and a test keeps them wired:

```text
1  domain fact file      core/facts/<module>/<domain>/<capability>.md   nine-section fact
2  write-chain fact      core/facts/<module>/write-chain/<domain>-write-chain.md
3  operation contract    registry entry  → the domain becomes callable, not just documented
4  index row             core/facts/INDEX.md                             else it is unsearchable
5  wiring test           asserts 1-4 stay connected
```

Landing 3 is the one that is usually skipped. A fact file plus a builder still leaves the domain outside the agent's own execution surface — the agent can *know* the endpoint but cannot *call* it, so every use needs an out-of-repo script. If the agent's own contract sweep cannot reach the domain, it is not a capability.

Landing 4 is the one that is silently skipped. A fact file that no index references is unsearchable, which means the next session re-derives the same contract from scratch and re-runs the same capture. Register it.

**A knowledge file that names an endpoint with no callable path is a capability hole, not a fact.** Domain catalogs routinely record 「分类_创建 -> SomeController.create」 while the repo has no builder, no validator, and no registry entry for it. That shape means the interface was identified but never operationalized. Close the hole rather than treating the catalog entry as coverage: builder (side-effect free) → validator (local rejection of shapes the platform accepts silently) → registry contract (with write/read flag and evidence pointer) → test.

Contract entries carry their evidence pointer so a later reader can recompute them, and the write/read flag is decided by *what the call does*, not by its HTTP verb: a GraphQL query posted over POST is a read face; the same verb on a mutation is a write face that must require the explicit write scope.

**Separate "readable" from "executable" in every capability statement.** A domain can be fully documented, fully validated offline, and still not runnable end to end. Report the three tiers separately — documented / callable / proven to run — and never let the first stand in for the third. When a whole domain's verification lives in out-of-repo scripts, say so: the agent's own entry points cannot reproduce that evidence.

**Supersede wrong claims explicitly, in place.** When a contract is corrected, the fact file must carry a short "已作废" table naming the old claim and its replacement. Leaving the old sentence in the file is how the next session re-derives the same wrong body — a fact file that quietly contradicts itself is worse than one that was never written.

## Context, session and tools

Use ports so a host can embed the component:

```python
class ContextPort(Protocol): ...
class SessionPort(Protocol): ...
class ToolPort(Protocol): ...
class PolicyPort(Protocol): ...
```

The host owns the conversation context. xiaozhua may own a scoped execution record containing `run_id`, component, phase, plan, tool results, evidence and verification status. Keep `conversation_id` and `run_id` separate.

## Verification discipline

For behavior changes, follow RED → GREEN → REFACTOR:

1. Write the smallest behavior test.
2. Run it and observe the expected failure.
3. Add minimal implementation.
4. Run focused tests.
5. Run the full regression suite.
6. Run a real local smoke using the actual collected evidence or fixture boundary.

A first usable package is not complete when classes merely import. It must have a callable entry point, structured results, safe denial for unsupported writes, and real test output. Report offline tests separately from live environment validation.

## Recommended first implementation scope

Implement together, not as disconnected stubs:

```text
Core request/context/session/policy ports
component registry and routing
UDC evidence catalog and domain analyzer
UDC model and dry-run planner
Runtime and Integration read-only component contracts
CLI JSON report and denial surface
focused tests + full regression
```

Defer real test2 writes until the read-only and dry-run contracts are green. A dynamic test2 loop must be isolated to a temporary application, and publish/deploy remain separate confirmation gates.

## Failure and evidence rules

- HTTP 200 is not proof of business success.
- A model or component claiming completion is not evidence.
- Missing source, schema or runtime read-back is `UNVERIFIED`, not a guessed FACT.
- Static artifact indexing and live end-to-end verification are separate acceptance layers.
- If a tool invocation fails, preserve the working alternative and do not encode a transient setup failure as a permanent tool prohibition.

## Live read-only execution (test2)

When the goal is "the agent must be live-testable against test2" the execution layer is the bottleneck, not the evidence layer:

- **xiaozhua UDC read-only endpoints are HTTP POST, not GET** (e.g. `/service/{appId}/udc-runtime/meta-data/select-host-and-only-page-pages`, `check-page-exists`, `/udc-runtime/rt-page-log/search`). The repo's `GatewayReadonlyClient`/`GatewayRequest` method whitelist defaults to GET-only, so the live path returns `BLOCKED`/`404` on every proven endpoint and the agent can never show a live `PASS`. The correct extension is to widen the whitelist to `{GET, POST}` and add a body-carrying `post()`; keep write methods (PUT/PATCH/DELETE) denied — the `write=False` operation contract is what makes a POST read-only, the HTTP verb alone is not. Measure which endpoints 404 vs 200 on test2 BEFORE assuming the live path works (GET `/udc/application/{id}` → 404, POST `/udc-runtime/meta-data/...` → 200 `BOOT_0000` is the observed split), rather than inferring from the contract table.

- **Ship a live capability as three pieces and keep the offline suite green:** (1) an offline deterministic stub test for the new runner, into the default collection — it proves the verdict/identity/auth-fail logic without touching the network; (2) a config-driven one-command entry script that defaults to network-off and takes the credential by path (ironclad 040402 — no machine values in code); (3) the widened gateway client. Never let the live script be the only thing that exercises the new code, and never let widening the method whitelist regress the write-denial tests.

- **The repo pins its test count and a contract test enforces it.** `tests/test_documentation_contract.py` runs `pytest --collect-only` and asserts the count equals the number written in `README.md` + `docs/audit/agent-version-audit.md` + `docs/audit/code-reality-audit.md`. Adding N tests therefore fails 4 documentation-contract tests until all three numbers are bumped to the new collect count. Grep the three files for the old `N passed` / `N tests collected` and update them together before declaring the suite green — an "all passed" run that leaves the doc-contract tests red is not green. The count drifts again every time you add/remove a test, so re-check the collect number and the three docs in the same change.

## Execution layer (PlatformOperationLayer) — dispatch and routing

The execution layer translates a contract from the registry into a gateway request. Keep it contract-generic; the hardcoded-op era produced these pitfalls:

- **Never add per-operation `if intent.operation == ...` branches in `_request`** — the 4-op hardcode made the other 52 registry contracts raise `no readonly adapter mapping`. Build the request from the contract itself (path placeholders filled from `required_inputs` ∪ actual path placeholders ∪ intent context). Missing placeholder values → raise `missing path parameters`; never guess a value (缺参是 UNKNOWN 不是猜).
- **Gateway prefix is dual-form.** `/udc/*` design-time contracts → `/service/udc/...`; `udc-runtime/*` runtime contracts → `/service/udc/udc-runtime/...`. A prefix helper that only prepends `/service` renders the second form as `/serviceudc-runtime/...` and every runtime contract 404s. Catch this class of bug by push-testing, not spot-checking (below).
- **`{appId}`-class placeholders take the Long numeric form.** UDC design-time routes bind `{appId}/{id}` to `java.lang.Long`; passing the prefixed string app name (`letters+digits`) dies with Spring `NumberFormatException` (live-observed BOOT_3000). When the intent value matches the prefixed-name shape, strip to the digit segment (the digit run is the app's numeric id — same value the write-chain evidence used). Same normalization applies to identity comparison: response payloads carry pure-numeric appId while intents often carry the prefixed name — compare digit-segments, or every list contract reads UNVERIFIED forever.
- **`effective()` gating is deliberate: the execution chain only fires GET contracts** (write=False + method=GET). POST read-type contracts stay DENIED here by design; the standalone live-probe runner is the sanctioned bypass for POST readback. Do not "fix" the DENIED.

### Push-test the whole registry, not one contract

After any dispatch/routing change, sweep EVERY GET contract against a live app in one loop and classify results (PASS / UNVERIFIED / DENIED / FAIL / missing-params / exception). Spot-checking one happy-path contract passed while 12 runtime contracts were 404-ing; the sweep exposed it in one run. Interpret the buckets: PASS = true positive; UNVERIFIED = request reached the gateway but verification needs real business data (undeployed runtime, missing guid) — expected on a test app; DENIED = POST gating; FAIL with empty collection = correct business answer for an empty app; missing-params = contract needs real ids you don't have. Fix code for EXCEPTION/404 buckets; do not chase UNVERIFIED buckets that are just missing business data.

### UDC design-time write chain (live, on the test app)

The four-step sample chain (entity→attribute→page→deploy) plus microflow/page-rules are ALL API-automatable on test2 — proven end-to-end on the throwaway app. Facts live in the repo (`core/facts/udc/`); the workflow:

1. **Token first.** POST the login credential file (shared-credentials `ctp-user-login.json`) to `/service/ctp-user/auth/token`; the session cookie jar (SY_ACCESS_TOKEN/TK_EXP/SY_UID) comes back alive. Verify with one cheap GET before any write loop.
2. **Create attributes one call each** — `POST /service/udc/entity/attribute` with a SINGLE object `{appId:Long, entityId:Long, name, caption, dataType}`. An array body deserializes to BOOT_3002; loop N times instead. Reserved field names (orderNo, billCode...) die with UDC_ENTITY_0002 — rename, don't fight. Verify by counting `name LIKE 'field%'` rows in `udc_test2.udc_attribute`, NOT by the write response: system columns the platform auto-adds (bill-family template from `presetData/attribute.json` in the biz jar) will otherwise be miscounted as business fields and inflated into a false completion report.
3. **Deploy = `POST /service/udc/runtime/deploy-normal` with `deployDto{appId:Long, deployType:TEST, projectType:ALL, terminalType:ALL}`.** Wrong deployType/businessType shapes fail with misleading '目标环境为空'. Takes ~2-4 min; poll `udc_test2.udc_deploy_record.state` (1=success). Physical tables land in the app's OWN schema (`{app}_test2`), never `udc_test2`.
4. **Runtime routing: bare `/service/udc-runtime/*` is `server_404` — the runtime face routes through the app-name prefix: `/service/{appName}/udc-runtime/*`.** Discovery: the sandbox pod built by deploy carries the generated jars; entity full names follow `com.seeyon.{appName}.domain.entity.{Entity}` (biz jar, `domain/entity/` package) — read them with `unzip -l` in the pod instead of guessing packages.
5. **Microflow save is API-open: `udcMicroflowUpdatePost` via `/service/udc/graphql`.** Body needs the existing row's `id`+`guid` (omitting them → BOOT_4002 'no permission') and numeric DB enums for `type`/`triggerType` (read them from `udc_microflow_info`, don't send strings). `dataSchema` is a JSON STRING: `{sourceType, trigger(MFStartNode/MANUAL), endNode(END_NODE), nodes[]}`. Find mutation shapes by grepping the frontend chunk for `fieldType:"udc...Post"` rather than guessing GraphQL syntax.
6. **Page rules/events bind inside the page schema**: `childById[controlId].events[] = {eventType, actionType:'microflow', microFlow:<id>, ...}` plus an `eventDefine[]` registry entry, saved through the same `submitPage`. A re-submit of an existing pageSchema also formalizes a draft page (schema_state 0→2) — the fix for menus pointing at draft pages.
7. **Page/menu/flow verification = direct MySQL readback** (`udc_page_schema.schema_state`, `udc_function_node.schema_state`, `udc_microflow_info.data_schema`), not the write response. A session with interrupted writes leaves draft rows and stale menu records — check for them before reporting completion, and never report system-template columns as created fields.

The metadata storage model behind all of this: design-time MySQL (`udc_entity`/`udc_attribute`/...) is authoritative; publish exports metadata into a Redis Hash (180h TTL) + OSS JSON mirror; `presetData/attribute.json` is ONLY the system-attribute template. So a design-time write is invisible to runtime metadata faces until deploy — expected, not a bug.

## Test-target discipline

Run live probes and push-tests against the dedicated throwaway test app (`zzprobe测试应用`, appId `6419954374508955097`), NEVER against the customer application — the user called this out explicitly. The customer app is for evidence collection only when a task demands it. Keep the app switch recorded in the credential file (app_id/gateway_prefix/scope fields) so every session inherits the target. Note the throwaway app's runtime is undeployed between experiments: `deploy-info` returns server_500 and runtime endpoints 404/empty by design; design-state endpoints (`/udc/application/{id}`, entity listings) stay live.

## Customer-evidence separation (repo hygiene)

The platform evidence repo must not carry customer application data. Customer javap dumps, frontend chunks, metadata dumps, decompiled customer microflow sources, customer DB-probe scripts, golden fixtures keyed by customer app id, and customer config values all migrate OUT to a sibling customer-evidence directory with a README migration index (original path → new path, source HEAD recorded). Grep the whole tracked tree for the customer app id to find leaks; classify each hit before moving:

- **Migrate**: customer data dumps (entity attribute contracts, metadata trees, listener/email class lists), scripts whose inputs are customer jars/DBs, customer profiles.
- **Keep**: LIVE probe parameter records (`app=znxmglpt...` inside an evidence file is the fact chain that proves the endpoint worked), negative-evidence scans ("BI does not exist in customer web" is platform knowledge), placeholder-template rules (`<ApplicationId>` tokens, not hardcoded ids).
- **Watch for false-positive migrations**: mechanism fixtures that tests depend on (a Nacos manifest listing dataIds), placeholder-based rules. A migration that turns tests red must be reverted or the fixture re-classified — run the full suite after each migration batch.
- Add `.gitignore` guards (customer dirs, `*.jar`, `*.class`) in the same commit so purged data cannot silently return.

## Accepting "embeddable + live-testable" (the north-star check)

When the goal is "embed the agent into a host (Claude/Hermes/Codex), understand the requirement, do the work, and I can test it tomorrow," prove it with a re-runnable multi-round driver, not a one-shot call:

- **Host embeddability = the host can read back what the agent did.** The agent takes host-injected `context`/`session`/`policy` ports; after a dispatch, assert the host session's event log actually grew (the agent recorded its action into a host-owned structure). A host that cannot read the agent's execution record back is not embedded — the ports existing in the file is not proof of embeddability.
- **Multi-round, not single-shot.** Run requirement→route→dispatch N rounds and the live readback N rounds; assert per-round PASS **and cross-round stability** (the same endpoint's strip(traceId) md5 identical across rounds). One PASS can be luck; identical readback across N rounds is the stability evidence the user's "can I test it" actually needs.
- **The driver is a committed, re-runnable script in the repo** (one command), so "test it tomorrow" is a command, not a narrative. Default it offline: live rounds report `SKIPPED`, never a fabricated live PASS; gate the live rounds behind an explicit flag + credential-by-path.

## Generation surface (requirement → skeleton code)

The repo's `ConstructionEngine` plans 8 artifact classes (dto/api/entity/domain_service/app_service_impl/dao/abstract_controller/controller) but stops at the plan. Wiring the generation capability is governed by evidence rules, not by writing plausible Java:

- **Render declaration-level skeletons only.** Package/class/extends come from the golden javap dumps (`docs/audit/artifacts/customer-*`); field types come from the observed javap type distribution; method bodies are NEVER invented — emit an `// UNVERIFIED` comment instead (contract caveat: "Observed output contract only; generator causality UNKNOWN"). A skeleton that invents method bodies is a fabrication, not a generation.
- **Frontend page-definition field sets come from the C2b LIVE page sample** (the 18 observed `UdcMainPageMetadataDto` fields). Fill only fields with evidence (appName/masterEntity/name/sourceType/urlType, caption when the model carries one); list the rest under `unverified_fields` — runtime values like `pageUrl` cannot be derived offline, so guessing them defeats the evidence contract.
- **Grep the whole repo INCLUDING `_deferred/` before writing a new generator** — a working v1 DTO generator with passing tests sat in `_deferred/source-generator-v1/` while the capability was treated as missing. Unwired code is still code.
- **Expose the capability set to hosts through ONE bootstrap function** (`xiaozhua_host_bootstrap.bootstrap()`) returning a dict of callables (dispatch/generate/generate_from_requirement/live_probe/deploy_plan/agent); each host (Hermes skill, CC, Codex) wires a doc/skill file to that single entry rather than re-assembling components. Verify the bootstrap end-to-end in BOTH offline and `allow_network=True` modes before committing.
- **Bootstrap-surface changes must keep capabilities-object assertions green.** The doc-contract test asserts the capabilities payload shape (`payload["readonly_only"] is True` etc.), and other tests read the returned dict's keys — adding a new callable (e.g. `deploy_plan`) is safe, but changing/removing existing keys or the capabilities dict fields breaks tests that pinned them. Run the focused capability tests plus the full suite after any bootstrap signature change.
- **When the user redefines the product's architecture, freeze it as a committed ROADMAP before spawning execution.** The v2 reframe ("not a new Agent — xiaozhua capabilities/facts/runtime as verifiable Capabilities, packaged as an installable agent role + capability set into Hermes/Codex/CC, with dual compatibility: xiaozhua version adapters AND agent-host adapters") landed as `docs/capability/ROADMAP-v2.md` + a phase-1 task doc (8 architecture docs + one UDC sample chain), and a fresh three-role session launched against it. Archive completed/stale sessions wholesale (one timestamped archive dir, monitor SESSIONS dict emptied then repopulated with the new session id) so watchdogs and dedupe state start clean; promote shared credentials to a workspace-level `shared-credentials/` dir and update the config reference — tasks then reference one stable path instead of per-session deep paths.

### Semantic layer (requirement text → entity model)

The entry point is `generate_from_requirement(text, application_id)` → `RequirementParser` → model → plan → skeletons. Its rules:

- **The parser is deterministic only; the LLM's semantic understanding lives in the HOST.** The parser extracts entity name, caption, and `field：type` lines with a fixed alias table (字符串→String, 金额→BigDecimal, 是否→Boolean, 日期→Date, 整数→Long — the alias table must mirror the golden javap type distribution). No entity found → `UNVERIFIED` with a reason; never fabricate a model to keep the pipeline moving.
- **Do NOT transliterate Chinese attribute names into field names.** Golden generated artifacts use romanized field names (`fahuodanweiyouxiang`), but no evidence supports a pinyin-conversion rule — inventing one is a fabrication. Flag `attribute-name-not-java-identifier`, return the model as `PASS_WITH_UNKNOWNS`, and let the host (LLM/user) confirm the field name before a second render.
- **Don't stuff verification flags into frozen model dataclasses** — `NormalizedAttribute.__post_init__` rejects unknown kwargs. Carry per-field verification in the parse-result dict (`type_verified` map) instead of inventing model fields; the frozen schema is part of the evidence contract.
- **A skipped attribute must leave a trace in the skeleton** — silent `continue` makes the gap invisible and the DTO renders empty with no explanation. Emit `// UNVERIFIED: 字段 X(类型) ...待确认` at the skip site so the host sees exactly what is missing and why.

Dev-loop pitfalls for this surface:
- **The repo-root `AGENTS.md` is a protected agent-instruction file — writing it hits an approval gate that times out with no user present.** Put host-integration docs in `docs/HOST-INTEGRATION.md` (or a skill file) instead; never retry the AGENTS.md write via terminal.
- **A credential JSON created to drive a live probe must not live inside the repo** — even untracked, it is one `git add .` away from leaking. Write it outside the repo (session workspace), add `*_credential.json` to `.gitignore`, and re-scan for `eyJ` strings before committing.
- **The persistent `execute_code` kernel caches imports: after patching a repo module, the kernel still runs the old bytecode**, so a fix looks like it failed (or an old bug looks alive). Verify with a fresh `subprocess python -c` run against the repo venv before concluding anything about the patched code.
- Tuple-shaped constants (e.g. `(kind, baseclass)` pairs in a renderer) get unpacked wrong under rename refactors — when a renderer emits a literal like `extends class`, fix the unpacking site, and let the focused tests name which artifact types must render.
- Answer "is the token still valid" from a live request, not from decoding `exp`: refresh the credential file from the user's cookie string, then fire ONE real POST at a cheap endpoint (`check-page-exists`) — an expired window returns nginx 403, and the live verdict is the answer the user needs (decode is only the estimate).
- **Token renewal is fully self-service**: the shared credentials dir carries a login credential file (endpoint + body with username/password) whose POST returns a fresh `access-token` (JWT, ~24h window). Fire it, decode `exp` from the JWT payload only to record the expiry timestamp in the credential file, and carry on — no user round-trip needed. Renew proactively whenever a push-test or probe is about to run and the recorded expiry is near.
- **Line-ending noise breaks diffs**: several repo files are CRLF in the index with `core.autocrlf=false`; a patch tool that rewrites the file flips every line in `git diff`. After editing, check `git diff --stat` — if a one-line intent shows as a whole-file rewrite, normalize the file back to its index line-ending style (CRLF→index-CRLF, LF→index-LF) before committing, or the commit drowns the real change.

## Committing in a shared working tree

The agent repo is also where a live evidence-engine session drops its half-finished artifacts (audit scans, decompiled modules, tool scripts) while you work:

- Stage ONLY your files by explicit path — never `git add .` — so a concurrent session's in-progress artifacts do not get committed into your capability commit. Leave the other session's untracked files alone; it manages them.
- Before committing, re-scan every staged + untracked file for a live token (long `eyJ...` strings). A credential file you created to drive a live probe WILL otherwise leak into the repo; keep credentials path-referenced and add them to `.gitignore` in the same change.

## References

- `references/first-usable-slice.md` — coherent skeleton-to-tested-package delivery recipe.
- `references/udc-entity-construction-evidence-closure.md` — UDC entity construction evidence closure notes.
- `references/udc-contract-discovery-playbook.md` — the per-domain contract-discovery workflow (three-role session roles, three-layer scan, diff rules, verdict criteria) and the registry-merge + test-target conventions that go with it.
