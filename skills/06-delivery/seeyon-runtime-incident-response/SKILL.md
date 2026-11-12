---
name: seeyon-runtime-incident-response
description: "Use when 2小爪 UDC runtime, frontend or deploy failures."
version: 0.1.0
author: 小爪
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [2小爪, udc, kubernetes, incident-response, oom, gateway, nacos, dubbo]
    related_skills: [seeyon-udc-runtime, seeyon-low-code-environment]
---

# 2小爪 Runtime Incident Response

## When to Use

Use for 2小爪/UDC incidents such as front-end pages failing, `/udc/graphql` returning 5xx, data APIs returning no data, `BOOT_3000 Field [X] is not exist in [ClassY]` from list/filter-plan data queries, UDC Pod restarts, readiness/liveness failures, suspected Nacos/Dubbo registration problems, or app publish failures (`发布失败`, `应用元数据处理类[X]执行异常: null`).

Not this skill: 「数据迁移 / 融合同步」方案运行失败（`迁移任务异常` / `数据校验失败，进行数据回滚` / 是否落库）走 `seeyon-runtime-configuration-and-sync` 的《平台数据迁移（迁移方案）运行核验》——那里有方案配置读法、源目标对账与 VALIDATE 阶段抽样校验取证的完整命令。本技能只管它的基础设施面（pod 重启/探针/发布/日志轮转）。

## Operating Principles

1. Evidence first: capture live state, timestamps, Pod status, events, logs, and the exact failing request before restarting or changing configuration.
2. Separate layers: frontend token/session, gateway, UDC runtime, generated application Pod, Nacos/Dubbo discovery, database, and external services are different failure domains.
3. `Running` is not equivalent to usable. Check `Ready`, probe events, registration time, and a real health/data request.
4. Do not infer the root cause from one `server_500`, one HTTP 200, or a stale page. Correlate the same timestamp/trace ID across layers.
5. Cleanup/restart is a state-changing action. Scope it narrowly, verify afterward, and never delete a Deployment/Service when only stale Failed Pods are being cleaned.

## Standard Diagnostic Sequence

### 0. Access preflight before interpreting the incident

Before attributing a restart to the application, verify the observation path itself:

1. Resolve the exact environment (`test2` or `uat`), namespace, Pod name/selector, and observation time. Never infer the environment from a Pod name such as `sandbox`.
2. Check whether the local `kubectl` binary and the environment-specific kubeconfig are actually available. If the cluster is administered through a bastion/worker host, run the read-only Kubernetes queries there using the explicitly approved SSH material; do not silently substitute another host or kubeconfig.
3. Treat network tests as layered evidence: ICMP reachability does not prove TCP/22 or Kubernetes API reachability. Record the failed layer and stop at that boundary rather than inferring an application root cause.
4. Once access works, capture one bounded evidence bundle before any restart or cleanup: Pod JSON, `describe`, previous-container logs, current logs, and namespace events.

A blocked observation path is `BLOCKED`, not evidence of OOM, probe failure, rollout, or manual restart. Do not repeatedly retry malformed paths or credentials; correct the access prerequisite or ask for the missing environment/access context.### 1. Identify the exact environment

Use the environment-specific kubeconfig explicitly. For test2:

```bash
kubectl --kubeconfig=configtest2 ...
```

Do not infer environment from namespace, node name, or Pod name. Record namespace, target application, current Pod name, image/version, and current time.

### 2. Inspect runtime state

```bash
kubectl --kubeconfig=configtest2 get pods -o wide
kubectl --kubeconfig=configtest2 get pod <pod> -o json
kubectl --kubeconfig=configtest2 describe pod <pod>
kubectl --kubeconfig=configtest2 top pod <pod>
kubectl --kubeconfig=configtest2 get events --sort-by=.lastTimestamp
```

Record phase/ready/restartCount, running/terminated timestamps, termination reason and exit code, resources, JVM flags, injected agents, probe configuration, and node/eviction signals.

### 3. Classify restart causes

- `OOMKilled`, exit 137: container exceeded memory limit; primary root cause is memory pressure.
- Liveness probe failure: usually a consequence or an independent health-check problem; correlate with memory, CPU, blocked threads, and application logs.
- Readiness failure: Pod may be alive but not eligible for traffic; check startup completion and service discovery.
- `Error`/nonzero exit without OOM: inspect previous container logs and termination message.
- Pod replacement with `SuccessfulDelete`, `ScalingReplicaSet`, image pull, or changed ReplicaSet: likely rollout/manual restart, not a process crash.
- `Evicted`/`NodeNotReady`: node/resource event; do not attribute it to application code without evidence.

### 4. Check the correct network layer

UDC may not have a Kubernetes Service named `udc`. Generated applications and frontend traffic can use gateway routing plus Nacos/Dubbo registration. Check all of these explicitly:

```bash
kubectl --kubeconfig=configtest2 get svc
kubectl --kubeconfig=configtest2 get endpointslice -A
kubectl --kubeconfig=configtest2 get pods -l app=ctp-webapi-gateway -o wide
kubectl --kubeconfig=configtest2 get pods -l app=<application-id> -o wide
```

A missing `svc/udc` is not sufficient evidence of outage. Confirm the actual gateway Service and the UDC Nacos/Dubbo registration.

### 5. Read logs narrowly and correlate timestamps

Start with bounded windows and focused patterns:

```bash
kubectl --kubeconfig=configtest2 logs <udc-pod> -c udc --since=15m --timestamps
kubectl --kubeconfig=configtest2 logs <udc-pod> -c udc --previous --timestamps
kubectl --kubeconfig=configtest2 logs -l app=ctp-webapi-gateway --since=15m --timestamps
kubectl --kubeconfig=configtest2 logs -l app=<application-id> --since=15m --timestamps
```

Search for OOM/exit 137, health probes, gateway 5xx/upstream timeouts, request URLs/trace IDs, Nacos/Dubbo registration, Redis/MySQL/SQL errors. Do not treat generic startup warnings as the root cause unless the failing request occurs after startup and directly references that warning.

### 6. Check session/token independently

If the gateway says token expired, decode JWT claims locally and compare `exp` with current time. An expired browser token explains WebSocket rejection, but it does not explain an OOMKilled UDC process. Report both as separate findings when both exist.

Never paste or persist full tokens, cookies, passwords, Nacos credentials, or private keys in reports or reference files.

### 7. Validate recovery with a real request

After a restart or recovery, verify Pod `Ready=true`, no new probe failures, completed startup and Nacos/Dubbo registration, no new gateway 5xx for the target operation, and a real authenticated frontend/GraphQL/data request. A health endpoint alone is insufficient for a data-access incident.

## Gateway-first diagnosis for API failures

When diagnosing a live API request, classify the failure layer before inspecting application business logs. Capture the exact request path, execution time, HTTP status, response envelope, gateway/application trace ID, and whether the response is generated by Gateway or the target service.

A gateway authentication/signature response is not a BPM/UDC business failure. For example, `OPEN_GATEWAY_5000` with `message=无效签名` establishes a Gateway rejection path; it does not establish that the BPM controller, template validation, form record lookup, user lookup, command handling, or database write ran. Stop downstream root-cause claims at that boundary and mark them `UNVERIFIED` until correlated logs prove otherwise.

For mutating requests, do not retry blindly after a timeout or ambiguous response. First determine whether the request passed Gateway, whether the target service logged it, and whether a business readback is needed. A successful HTTP status or a non-null response is not sufficient proof of business effect.

## Decompiling the deployed class behind a stack line

When a stack frame points to `Class.java:NNNN` but the local source tree is a different version (or absent), decompile the exact class from the running Pod before theorizing. This is also how you prove an internal contract mismatch between two services.

1. Capture the full stack with its `traceId` (`grep -a -A 40 "<traceId>"`); note every `Class:line` frame — those are compile-time line numbers of the deployed jar.
2. Locate the class inside the Pod:
   - `ls /app`: the deployed shell is usually `*-assemble.jar`; business code lives in nested `BOOT-INF/lib/<module>-<version>.jar` (list with `jar tf /app/<assemble>.jar | grep <module>`).
   - In-container `unzip` may report `bad archive`; the JDK `jar` tool works. Prefix `JAVA_TOOL_OPTIONS=` to suppress the agent banner.
   - Extract one class, then pipe out: `cd /tmp && jar xf <jar> path/Class.class && gzip -c path/Class.class | base64`; decode locally with `base64 -d | gunzip`. For a whole module jar (~3 MB): `kubectl cp <pod>:/tmp/x.jar /tmp/x.jar -c <container>` then `scp` it home. Beware: `jar xf` exits 0 silently when the entry does not exist — always `ls` the extracted result.
3. Decompile locally with CFR: `curl -sLO https://repo1.maven.org/maven2/org/benf/cfr/0.152/cfr-0.152.jar`; `java -jar cfr-0.152.jar --comments false Class.class > Class.java`.
4. **CFR line numbers are NOT the original line numbers.** Map the stack line with `javap -p -l Class.class > lines.txt`: `line NNNN: 0` marks a synthetic lambda body starting at that source line; `LocalVariableTable` confirms parameter names. Cross-check against the CFR text.
5. Confirm the trigger data with a read-only DB query. On Windows hosts without a mysql client, `uv run --no-project --with pymysql python probe.py` works; load connection material from the environment skill's `.env`.
6. When two internal services disagree, state both sides: a caller reading `map.get("memberId")` while the callee builds maps with keys `"memberIds"`/`"m"`/`"o"` is a hard contract bug (NPE every time that branch runs) — fix belongs in the vendor jar, not in configuration.

Shell-quoting pitfalls for these commands over SSH + `kubectl exec`:

- Avoid quotes inside the `sh -c "..."` script; use plain-word fixed-string `grep` patterns. Nested quoting often lands literal quote characters in the pattern and silently matches nothing.
- Strip transport noise before saving output locally: `2>/dev/null | sed '/^\*\*/d;/^Picked up/d'`.
- When nested quoting collapses (`unterminated quoted string`), stop fighting the layers: base64-embed the probe script and materialize it on the bastion (`echo <b64> | base64 -d > /tmp/probe.sh && bash /tmp/probe.sh` over one ssh call); the script itself calls `kubectl exec` and must be quote-free. One exec carries the whole probe set.
- The bastion runs BusyBox: `base64 -w0` is rejected (`unrecognized option -- w`). Pipe blobs out as `gzip -c file | base64 | tr -d '\n'` and decode locally with `base64 -d | gunzip`.
- To find which nested jar holds a class, try name-matched jars (`udc-*.jar`, the module named by the stack's package) before scanning `BOOT-INF/lib/*.jar`: 500+ `jar tf` invocations take minutes and get auto-backgrounded. Class homes are unintuitive — a `*MetaDataPostProcessor` lives in `udc-biz` while its `AppMetaDataContextPostProcessDelegate` lives in `udc-plugin-api`.
- **For extension (`ext`) code, the built source sits on a shared mount, not in the jar — and there are several build directories side by side.** Before quoting any line number as "the failing code", locate the file by NAME across the build dirs rather than trusting the newest timestamp, then `diff` candidate builds: identical files ⇒ quoting either is safe, different files ⇒ you must establish which build the *running* pod was compiled from (compare build-dir timestamp against the pod's container start time / image) before attributing behavior. Quoting a line from a build newer than the running one silently inverts the conclusion ("already fixed" vs "still broken").

  ```bash
  # 定位文件（不要在 /app 的 jar 里找 ext 源码）
  kubectl exec <pod> -- sh -c 'ls /A8C/base/autocode/<appId>/; find /A8C/base/autocode/<appId> -name <Class>.java'
  # 逐个 build 目录比对：无差异则可引用任一；有差异先定运行版本
  kubectl exec <pod> -- sh -c 'diff <buildA>/…/<Class>.java <buildB>/…/<Class>.java | wc -l'
  ```

## `BOOT_3000 Field [X] is not exist in [ClassY]` — runtime metadata vs generated DTO mismatch

This error from dynamic-join surfaces (筛选方案, list-page data query, `dynamicJoinSelect` chain) is a generated-artifact/metadata mismatch, not bad data. The framework does NOT read `X` from the DTO — `X` is DERIVED from runtime entity metadata: for `One2OneAggregation` it is `lowerFirst(last segment of child entity fullName) + "Dto"` (`EntityRelationHandler.convertDtoList`), and `DbMap2DtoUtil.recursiveBuildData` reflection-writes child DTOs at each recursion level. The durable mechanism fact grid was planned at `core/facts/udc/entity/relation-dtolistname-mechanism.md` but **that file was never committed** (git history empty; `core/facts/udc/entity/` has no `relation-*` file as of 2026-11-07). The mechanism itself is quoted above; treat this paragraph as the authoritative record until the fact is written.

1. Decode `X`: strip the `Dto` suffix, upperFirst → expected child entity fullName tail; the reported `ClassY` is the current recursion level's parentDto. First-layer success with a second-layer failure means the parent DTO HAS the child field and the child's own metadata declares one more relation whose derived name lands back on `ClassY` — self-aggregation/主数据多版本 is the typical trigger.
2. Prove the generation gap by javap-ing the CURRENT Running pod's `*-facade-*.jar`: the field present in the parent DTO and absent (check both `private` fields and `get/set<Name>` accessors) in the child DTO is the decisive fact.
3. After any pod restart, container `/tmp` extraction state is gone and the loaded jar version may have advanced — re-list `/app/libs/BOOT-INF/lib/` on the Running pod and re-extract before citing a version fact.
4. Build a version matrix before choosing a fix: javap the same DTO on every reachable published version (including failed/old pods). Every consecutive published version missing the field ⇒ stable generator defect; do NOT propose cache-cleaning or "wait for self-heal redeploy" — publish won't fix it. Only the version at error time lacks it ⇒ stale metadata, re-publish is the fix.
5. When the live HTTP readback path is blocked by expired SSO (`BOOT_1006` with `redirectUrl` in the envelope), do not chase credential renewal just to re-confirm DTO structure — the deployed jar in the running Pod is an equally authoritative artifact source and requires no auth.

Inspect the complete process budget: Java heap (`-Xms/-Xmx`), Metaspace, thread stacks (`-Xss × thread count`), direct/native memory, Netty/Dubbo buffers, ARMS/javaagent overhead, class metadata, and mapped files.

A container with a 16Gi limit and `-Xms10G -Xmx10G` has limited headroom. Large UDC metadata queries, GraphQL concurrency, page detection, Kafka/Dubbo pools, and an APM agent can push total RSS beyond the limit. Do not claim that increasing the limit alone fixes a leak; capture memory trend and workload correlation first.

## Bill write / submit failures (primary-key violation, BOOT_4004, duplicate row after submit)

For 「提交报主键约束」 / `BOOT_4004 违反主键约束` / 「提交后同一条数据两份」 / 「详情页查询结果为多条记录」, check the **page's submit semantics** before touching the database. Default hypothesis: the bill was already persisted (copy / change / migration wrote it) while the submit request is sent as a *create*.

- The platform regenerates ids in exactly two narrow cases: `id` empty/`NULL_ID`, or a child row carrying a `parentId` that differs from the parent id. **A sub-table row with `actionType=INSERT` does not get a new id** — id present and no `parentId` in the payload means a literal INSERT of an id that already exists.
- `create-bpm` / `create4Bpm` = create + start workflow; `update-bpm` / `update4Bpm` = update existing bill + start workflow. Payload without a main id ⇒ the platform must treat it as new, so an already-persisted bill submitted that way is a double write; fix the semantics, not the id generation.
- Which copy path ran is proven by the `MFSERVICE*` route in the logs, never inferred from a Chinese microflow name: "copy into DB" and "runtime copy (regenerate ids, do not persist)" have completely different consequences.
- Triage trio: `traceId` → Pod log → request URL (`create-bpm`/`update-bpm`) + payload; confirm whether the main DTO has an id and what ids/`actionType` the child rows carry; count `parentId|parent_id` occurrences in the payload (zero ⇒ the "fill parentId, keep the id" branch fired).
- Fix priority: change the page open/submit semantics (update instead of create) > make the copy non-persisting (runtime copy) > strip child ids as an emergency (creates an extra row — clean it up). Platform-side upsert/`resetId` alignment goes in as a product ticket. Give the user the recommended fix and its concrete change points; do not answer with a menu of options.
- DB forensics: back up business tables with `CREATE TABLE bak LIKE t; INSERT INTO bak SELECT * FROM t;` — on PolarDB with GTID enabled `CREATE TABLE ... SELECT` fails outright. Emit a duplicate-row list (business key + child ids) for user confirmation before deleting business data.

See `references/udc-bill-write-and-submit-semantics.md` for the platform method/`DtoFieldHelper` semantics table, the reproducible triage steps, and the four-option fix matrix.

## Silent write-path failures: traceId → pod log forensics

UDC write probes (`entity/create`, `custom-app/create`, page/app creation) commonly return HTTP 200 with `{"status":2,"code":null,"message":null}` — the gateway swallows the business error. The real reason is only in the udc pod log:

1. Take the `traceId` from the response body and grep the udc pod: `kubectl logs <udc-pod> --since=10m | grep <traceId>`.
2. The `ExceptionHandleFilter ... MESSAGE:` line IS the real cause (e.g. 「创建新页面必须传递 主实体」, 「创建页面使用的实体在元数据中心获取不到」). Never treat status:2 as "no evidence" or as an exhausted parameter dictionary — the reason is only in the server log.
3. To find which pod holds the trace, loop all pods with a hit count: `for p in $(kubectl get pods -o name | sed 's|pod/||'); do L=$(kubectl logs $p --since=20m | grep -c <traceId>; [ "$L" -gt 0 ] && echo "$p: $L"); done`.

### Verified UDC write-chain contract facts (2026-09-30 test2 live)

- `custom-app/create` `masterEntity` is a **String** (serialized entity-metadata JSON); passing a nested object fails deserialization (BOOT_3002).
- The metadata center only knows **published** entities: a just-created entity (UNPUBLISH) is invisible to `meta-data/select-entity` until `POST /service/udc/runtime/deploy-normal` (body wrapped in `deployDto`) publishes it. `select-entity` returning 200 with `content:null` means "not in metadata center", not "wrong endpoint". Probe `select-entity` with `{fullName, appName}`.
- Numeric appId: `entity/create` requires a Long `appId`. Get it from `GET /service/{app}/app-info/deploy-info` → `data.content` JSON → `appId` field (strip the business prefix from the string app id).
- `entity/create` name validation (UDC_ENTITY_0026) is stricter than its message: use plain camelCase alphanumeric names; underscore forms that satisfy the stated rule are still rejected — do not probe the boundary, just use camelCase.

## Deploy/publish FAIL forensics (`发布失败` / `应用元数据处理类[X]执行异常: null`)

**先定性再查栈**：`udc_deploy_record.state`（`1` 成功 / `2` 失败）与 `image_url` / `schema_storage_key` 是否为空是唯一权威判据；HTTP 200、`BOOT_0000`、`udc_resource` 被刷新、`udc_app_version.show_version` 推进都不是成功证据（失败发布会照样刷新资源表与版本号）。要判定「新版本到底生效没有」，比对 `remoteEntry.js` 与 `remoteEntry.<build_version>_*.js` 的 sha256。完整判定矩阵见 `seeyon-low-code-environment` 的 `references/udc-publish-success-verification.md`。

1. **Grep the udc pod first, never the failing app's pod.** The FAIL text seen in the app pod is a Kafka notice (`TEST2_CMD_MSG`, invoker `DeployChangeEventListener#onDeployChangeEvent`): every subscriber prints it, so cluster-wide hits only prove delivery. Only the udc pod runs `PipeLineManager`/`NormalDeployService`, i.e. only it can throw. Pod selector: `for p in $(kubectl get pods -o name | sed 's|pod/||'); do n=$(kubectl logs $p --since=90m 2>/dev/null | grep -c NormalDeployService); [ $n -gt 0 ] && echo "$p $n"; done`.
2. **`执行异常: null` means `ex.getMessage()==null`** — an NPE-shaped exception. The delegate's catch builds `exMsg` and rethrows a `BusinessException`, so the surfaced message carries no stack; the real stack is the `log.error(appId + exMsg, ex)` line on the udc console.
3. **Check the log window before grepping.** udc console lines are huge (single metadata dumps of hundreds of KB), so kubelet rotation retains only a few minutes: `--since=60m` can return 5. Read `head -1` of the fetched output first; if it starts AFTER the failure time, no grep will find the stack. Rotated files live on the node and node SSH is normally unreachable from the bastion → report `BLOCKED`, and never present a candidate NPE line as the cause.
4. **Recover with a live capture** (background, bounded): `timeout 900 kubectl logs -f <udc-pod> --since=5s | grep --line-buffered -B2 -A45 -E "执行异常|NullPointerException" > capture.log`, then ask the user to reproduce the publish.
5. **Attribute stacks by header, not by proximity.** Concurrent pipelines interleave; the `log.error` header carries appId and traceId — a nearby stack can belong to another app's processor entirely.
6. **WARN stacks are candidates only.** Swallowed parse errors in the same window (e.g. `JsonUtils MismatchedInputException` inside `MicroFlowParser`) show a plausible mechanism but are not the failing stack; label them `UNVERIFIED` until an ERROR header for the failing appId shows that frame.
7. **Narrow candidates while waiting:** decompile the named processor and list null-dereferences whose exception message would be null (`.stream()/.size()/.getId()` on a service/DAO result, or on a BO returned by a parser that can fail), keeping them ranked rather than declared as root cause.

## Common Misdiagnoses

- `Running` but `Ready=false`: traffic may still fail.
- Gateway `server_500`: inspect gateway stack and upstream readiness; do not immediately blame the database.
- Expired token: explains authentication/WebSocket failures, not container OOM.
- Generic `JsonPathHelper` warnings: may be noisy metadata parsing warnings; identify whether they coincide with the target request.
- Missing Kubernetes Service named `udc`: UDC may be exposed through gateway/Nacos rather than that Service name.
- HTTP client timeout: the server may still be processing; check Pod logs and database writes before retrying a mutating operation.
- Short-key maps (`m`/`o`/`memberIds`) returned where the caller reads long keys (`memberId`): an internal contract mismatch shipped inside the vendor jar — decompile both sides before blaming data or configuration.
- **The outermost `log.error` catch is an amplifier, not the root cause.** A generic line like `[数据迁移] 迁移任务异常: table=…, taskId=…, error=<异常自带 message>` only re-states an exception already logged a few lines earlier at the point of throw. Walk *backwards* in the window to the first `WARN`/`ERROR` that carries the *specific* values (sample keys, differing fields, SQL text). Reporting the outer line's text as the cause yields a tautology (`error=数据校验失败，进行数据回滚`).
- **Temporal proximity in a namespace is not causality.** A pod `exitCode 137`, a rollout (`ScalingReplicaSet`/`Scaling down`), and a readiness-probe failure landing in the same minutes as an application error are separate facts; the rollout explains the *pod log being short*, not the application error. Report them as parallel findings unless a traceId ties them together.
- **Short `--since` windows on a freshly rolled deployment return nothing.** When the target pod has just been replaced, the failure window belongs to the PREVIOUS ReplicaSet's pod: read `--previous` and sweep sibling pods (including old `Failed` ones, whose logs may be GC'd) before concluding "no evidence".

## Reporting Format

```text
结论：PASS / FAIL / BLOCKED / UNVERIFIED
环境：test2|uat，namespace，应用/组件
时间线：故障、重启、注册、探针和请求时间
运行态：Pod phase/Ready/restarts/image/resources
调用链：前台 → gateway → UDC/generated app → Nacos/Dubbo → DB/external service
证据：FACT（命令输出/日志原文）
根因：已验证根因；并列问题；未验证假设
恢复验证：真实请求结果和观察窗口
处理建议：只列有证据支持的动作，区分只读和变更
```

## Supporting Evidence

See `references/udc-runtime-incident-evidence.md` for a compact, redacted evidence pattern from a UDC OOM/gateway outage and the verification checklist.
