# xiaozhua Agent Code Reality Audit

Test collection: `3201 tests collected`. Historical counts below are not current execution results; see `docs/plans/xiaozhua-distribution-progress.md` for the latest run.

> **正文是 2026-09-03 那次审计的现场快照，不是当前状态。**
> 其中的 `183 passing tests` / `183 collected` / `total of 59` 都是**当时**的数值（仓库后来从
> 183 涨到 2710）。只有下面这行 `Test collection:` 由
> `tests/test_documentation_contract.py` 守着、必须与 `pytest --collect-only` 同步，
> 其余历史数字一律按"时点值"读，不要当现状引用。
> 标注 `【当前 2026-11-07】` 的条目是按现值改过的，改的依据都写在行内。

- **Audit type:** evidence-first static/runtime audit
- **Target:** `<XIAOZHUA_AGENT_ROOT>`
- **UDC evidence input:** `<USER_HOME>/...
- **Scope constraint:** offline/read-only only; no test2 connection and no external-environment changes
- **Audit date:** 2026-09-03 (local task context)

## Executive conclusion

**The repository is a small, tested, offline read-only skeleton, not a complete xiaozhua Agent runtime.** The core registry, routing, evidence envelope, UDC catalog/analyzer/planner, local snapshot providers, and CLI are real executable code and are covered by 183 passing tests. Runtime and Integration are snapshot-backed report components, not live adapters. SPI is referenced by routing but has no registered implementation. Write/publish/deploy/real test2 operations are denied or not implemented in the current public surface.

## Evidence status

| Area | Status | Evidence boundary |
|---|---|---|
| Filesystem/module inventory | **FACT** | Direct enumeration and source reads in current checkout |
| Core routing/registry/evidence | **FOCUSED VERIFIED** | `pytest tests -q` 【当前 2026-11-07】: 3172 passed, 23 skipped；source inspection |
| UDC catalog/analyzer over local artifacts | **REAL LOCAL SMOKE VERIFIED** | CLI run against Temp `udc_*.json`; no network |
| Runtime/Integration live behavior | **UNVERIFIED** | Only local JSON snapshots/providers exercised |
| CLI process boundary | **REAL LOCAL SMOKE VERIFIED** | Actual `python xiaozhua_cli.py ...` subprocesses |
| Full external/test2 acceptance | **NOT RUN / UNVERIFIED** | Explicitly out of scope |
| Git change baseline | **BLOCKED** | Target directory has no `.git` repository; Git commands returned “not a git repository” |

## FACT — directly observed

### Repository shape

Top-level entries are: `core/`, `components/`, `providers/`, `tests/`, `.pytest_cache/`, `__pycache__/`, `integration.json`, `runtime.json`, `pyproject.toml`, `README.md`, and `xiaozhua_cli.py`.

Python inventory from the checkout:

| Layer | Python files | Approx. source LOC | Reality |
|---|---:|---:|---|
| `core/` | 5 | 190 | Ports, registry, evidence, agent routing, file snapshot provider |
| `components/udc/` | 7 | 255 | Catalog, analyzer, models, planner, component, thin contract/version helpers |
| `components/runtime/` | 1 (+ init) | 18 | Snapshot/provider report component |
| `components/integration/` | 1 (+ init) | 18 | Snapshot/provider report component |
| `providers/` | 6 | ~400 | Read-only HTTP/Kubernetes/Nacos/MySQL/Redis providers and registry |
| `tests/` | current test suite | current runtime collection | 183 collected tests, including four duplicated `_Collected` unittest methods |

### Entrypoints

1. **Python CLI:** `xiaozhua_cli.py`, guarded by `raise SystemExit(main())`.
2. **Library composition root:** `core.agent.XiaozhuaAgent`.
3. **Registry:** `core.registry.ComponentRegistry`.
4. **UDC component:** `components.udc.component.UdcComponent`.
5. **No package console-script entry** is declared in `pyproject.toml`; the project exposes a directly runnable script rather than an installed CLI command.

### Core behavior

- `XiaozhuaAgent.route()` uses keyword heuristics for UDC, Integration, Runtime, and SPI intents.
- `XiaozhuaAgent.dispatch()` applies the injected/default `ReadOnlyPolicy`, dispatches through `ComponentRegistry`, and appends an event to `MemorySession`.
- `ComponentRegistry` registers components by their `name`, rejects duplicate names, lists capabilities, and dispatches either `execute()` or `inspect()`.
- `core.evidence.Status` defines `FACT`, `OBSERVATION`, `HYPOTHESIS`, `UNVERIFIED`, `DENIED`, and `UNAVAILABLE`.
- `Result` produces a JSON-compatible envelope with `component`, `target`, `status`, and `evidence`.
- `FileSnapshotProvider` reads JSON from a local path only.

### UDC behavior over actual local evidence

The Temp directory contained **22** readable `udc_*.json` files, including controller contracts, frontend mappings, dynamic contract gaps, persistence audits, version manifests, deployment artifacts, and runtime side-effect catalogs.

Actual command output from:

```text
python xiaozhua_cli.py udc-report --audit-dir <USER_HOME>/... --target demo
```

reported:

- artifact version: `5.3.517`
- loaded evidence files: all 10 files listed in `UdcEvidenceCatalog.REQUIRED_FILES`
- backend contract count: `672`
- frontend contract count: `36`
- application domain count: `3`
- entity domain count: `16`
- page domain count: `8`
- microflow domain count: `9`
- backend operation count surfaced by analyzer: `145`
- deployment artifact entry count: `1793`
- sampled version count: `6`
- preserved unverified gaps: `dynamic_contract_fields`, `frontend_static_source`

The command returned `RC=0` and a JSON result with `status=FACT`; this means the local catalog files were loaded, not that the UDC platform was contacted or that every domain is complete.

### Other local snapshot behavior

- `runtime.json` is `{"environment":"test2","pod":"udc"}` and is read as a local snapshot by `runtime-report`.
- `integration.json` is `{"http":200,"business_code":"SUCCESS"}` and is read as a local snapshot by `integration-report`.
- Both components also accept an injected provider with a `.read()` method.

### Tests and compilation

Fresh commands executed in the target checkout:

```text
python -m pytest tests --collect-only -q
# 3201 tests collected in 0.74s   【当前 2026-11-07 实测】

python -m pytest tests -q
# 3172 passed, 23 skipped in 72.38s   【当前 2026-11-07 实测】

python -m py_compile <all Python files under the repository>
# RC 0
```

> 收集数 2714 = 通过 2691 + 跳过 23，口径自洽。下方 `Commands and raw-result summary`
> 表里的 `3201 tests collected` 是同一批数据，已补上对应通过数，以本节为准。

## OBSERVATION — behavior seen in current runs

- CLI output is valid JSON for report/capability/action commands, with no banner or traceback on the exercised paths.
- `udc-execute publish demo ...` returned `RC=2`, `status=DENIED`, and policy evidence. This is a genuine safe-denial path, not a publish attempt.
- `udc-execute inspect_entity demo ...` returned `RC=0` but `status=UNVERIFIED`; the current `UdcComponent.execute()` does not analyze entity/page/microflow evidence and returns a generic unverified result for those actions.
- `runtime-report` and `integration-report` expose a FACT result whenever the supplied local snapshot exists; the FACT is about the snapshot file/provider read, not a live runtime or integration check.
- Missing required CLI arguments are rejected by argparse with `RC=2` and usage on stderr.
- The test suite collects four duplicate methods from `_Collected(unittest.TestCase)` in addition to the module-level tests, contributing to the total of 59.【当前 2026-11-07】这句话描述的是 2026-09-03 的旧 tests 目录（当时 `59` 个），那套 `_Collected` 结构已不存在；当前收集 2710。保留原文以维持审计可追溯，不作为现状。

## GAP — missing or incomplete capability

### High priority

1. **No live provider layer.** `providers/` contains only `__init__.py`; there is no Kubernetes, database, Redis, Nacos, HTTP, browser, or test2 adapter.【当前 2026-11-07】此条已失效：`providers/` 现有 **10 个 `.py`**（HTTP/Kubernetes/Nacos/MySQL/Redis 只读 provider 与注册表）。保留原文以维持审计可追溯。
2. **No real SPI component.** The router recognizes SPI keywords and can return `"spi"`, but no SPI component is constructed/registered by the CLI or documented composition path. Such requests resolve to `UNAVAILABLE`.
3. **UDC action coverage is mostly a report shell.** Only `inspect_application` has a catalog-backed path. `inspect_entity`, `inspect_page`, and `inspect_microflow` return generic `UNVERIFIED`; `dry_run` also returns generic `UNVERIFIED` from `execute()` rather than invoking `UdcPlanner`.
4. **Runtime and Integration capabilities are not action-specific.** Their `capabilities()` lists multiple actions, but `inspect(target)` is the only implementation and always returns one whole snapshot/provider read. There are no separate route/pod/log/database comparison implementations.
5. **No real execution lifecycle.** There is no plan execution engine, tool invocation layer, approval/resume lifecycle, cancellation, timeout handling, persistence, or cross-process identity/concurrency contract.

### Medium priority

6. **No installed CLI contract.** `pyproject.toml` has no `[project.scripts]` entry, so `xiaozhua` is not declared as an installable console command.
7. **Error handling is narrow.** Snapshot JSON parsing and provider exceptions are not normalized into the stable `Result`/evidence envelope; malformed or failing provider reads can raise directly.
8. **Registry dispatch dynamically creates a dataclass per `execute()` call.** This works in tests but is an ad-hoc boundary rather than a shared request type/port contract.
9. **Evidence model is not enforced end-to-end.** Components can return plain dictionaries; `Status` validates `Evidence` objects but does not constrain every result payload or source provenance.
10. **No test marker split or live acceptance suite.** The current suite is deterministic/offline, but there is no explicit `slow`/live test separation or real-environment acceptance command.

## DRIFT — mismatch between stated design and current code

1. **README says “统一入口，按组件接入 UDC、SPI、Integration、Runtime”;** source has no SPI implementation or registration, so the stated component set exceeds the live implementation.
2. **README says “当前版本是可测试的只读骨架”;** this is broadly accurate, but it should explicitly call Runtime/Integration snapshot-only and UDC non-application actions unverified.
3. **README reports “当前实测：`2714`”;** 【当前 2026-11-07 修正】fresh execution reports **3172 passed, 23 skipped**（收集 2955）。本条原始结论"README 计数是当前的"已不成立——README 里的 `2710` 是**收集数**不是通过数，两者口径本来不同。
4. **README describes UDC output as version, evidence file count, and FACT/UNVERIFIED status;** current output additionally surfaces domain counts, backend/frontend counts, deployment count, and dynamic/static gaps. Documentation understates the implemented report shape.
5. **The architecture target in the component skill names Core + sibling UDC/SPI/Runtime/Integration/Workflow + Providers + Adapters;** current tree has Core + UDC/Runtime/Integration only, no Workflow, no concrete Providers, and no Adapters directory.【当前 2026-11-07】已部分兑现：`adapters/{hermes,codex,claude-code,mcp}` 已建、`providers/` 已有 10 个只读 provider、`installer/` 已建；**仍无 Workflow 组件、无 SPI 实现**。原文的"无 Adapters 目录/无 concrete Providers"已失效。
6. **The component contract recommends `name`, `capabilities()`, `inspect()`, `plan()`, `execute()` for each component;** UDC has most of these, Runtime/Integration have only `name`, `capabilities()`, and `inspect()`, and neither has `plan()`/`execute()`.
7. **`core.evidence.report` is defined three times in the same module.** The final definition wins; earlier definitions are dead/redundant source and indicate incomplete cleanup.【当前 2026-11-07】已清理：`grep -c "^def report" core/evidence.py` = **1**。原文描述的三重定义不复存在。
8. **Several imports are duplicated/unused** (for example repeated `Evidence`/`Result` imports in components and `UdcComponent`), indicating scaffold-level cleanup debt rather than a polished package.

## Placeholder/realness triage

| Surface | Classification | Evidence |
|---|---|---|
| Core route/registry/evidence | **REAL, tested** | Executable implementations; direct tests pass |
| UDC catalog loading | **REAL, locally exercised** | Reads 22 local artifact files; CLI report verified |
| UDC domain analyzer | **REAL but evidence-bound** | Extracts counts from named JSON fields; missing fields become `UNVERIFIED` |
| UDC planner | **REAL but not wired to CLI execution** | `UdcPlanner.plan()` builds dry-run steps; current component `execute(dry_run)` does not call it |
| Runtime component | **REAL snapshot adapter; not live runtime** | Local JSON/provider read only |
| Integration component | **REAL snapshot adapter; not live integration** | Local JSON/provider read only |
| SPI | **ROUTING PLACEHOLDER / missing implementation** | Route branch exists; no component/provider |
| Providers | **PLACEHOLDER package** | Empty package init; no concrete adapters |
| Writes/publish/deploy | **SAFE DENIAL / unsupported** | Publish action returns DENIED; no write implementation |
| Agent loop/planning/reflection/tools | **MISSING** | No loop/tool runtime modules in inventory |
| Persistence/session continuity | **IN-MEMORY SKELETON** | `MemorySession.events` only; no durable store |

## Commands and raw-result summary

| Command | Result |
|---|---|
| `git status --short --branch` | **BLOCKED**: target is not a Git repository |
| `git log -5 --oneline --decorate` | **BLOCKED**: target is not a Git repository |
| `git diff --check` | **BLOCKED**: target is not a Git repository |
| `pytest --collect-only -q` | **3201 tests collected** |
| `pytest -q` | 【当前 2026-11-07】**3172 passed, 23 skipped**（原表此行留空，已补） |
| `py_compile` all repository Python files | **RC 0** |
| `xiaozhua_cli.py --help` | **RC 0**, dependency-light help |
| `capabilities` | **RC 0**, read-only/network-disabled declaration |
| `udc-report` against Temp artifacts | **RC 0**, JSON `status=FACT` with preserved gaps |
| `udc-analyze` against Temp artifacts | **RC 0**, domain report with `dynamic_contract_fields` and `frontend_static_source` unverified |
| `runtime-report` local snapshot | **RC 0**, snapshot `FACT` |
| `integration-report` local snapshot | **RC 0**, snapshot `FACT` |
| `udc-execute publish` | **RC 2**, structured `DENIED` |
| missing `udc-report --target` | **RC 2**, argparse usage/error |

## Prioritized closure sequence

1. Keep the offline/read-only boundary explicit and correct stale README counts.
2. Wire `UdcPlanner` into a real `dry_run` result and implement evidence-backed entity/page/microflow projections.
3. Add a concrete SPI component or remove the SPI routing claim until it exists.
4. Establish shared component request/result/error contracts and normalize provider failures.
5. Add real provider adapters behind ports, with isolated fixtures and read-back verification; only then consider test2.
6. Add persistence/session/run identity and lifecycle tests before claiming an agent runtime.
7. Add an installable CLI entrypoint and explicit offline-vs-live test markers.

## Audit limitations

- No Git history/diff ownership analysis was possible because the specified directory is not a Git worktree.
- No test2, network, Kubernetes, database, Redis, Nacos, browser, publish, deploy, or other external operation was attempted.
- Static conclusions describe current source; they do not prove behavior in unavailable external systems.
