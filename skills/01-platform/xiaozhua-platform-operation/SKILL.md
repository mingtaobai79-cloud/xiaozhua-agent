---
name: xiaozhua-platform-operation
description: "Use when operating xiaozhua APIs safely."
version: 1.0.0
author: 小爪 🐾
license: MIT
platforms: [windows, macos, linux]
tags: [xiaozhua, platform-operation, evidence-first, udc, spi, api-contract]
metadata:
  hermes:
    tags: [xiaozhua, platform-operation, evidence-first, udc, spi, api-contract]
---

# xiaozhua Platform Operation

## Purpose

Use this skill when building xiaozhua Agent capabilities that operate xiaozhua platform modules as a user or operator. The goal is not to reproduce UDC/BPM/Connector/Integration source code. The goal is to understand real platform contracts, construct safe operations, execute them only when authorized, and verify the resulting platform state.

The governing distinction is:

```text
xiaozhua Agent = the overall agent system
Components   = UDC, BPM, SPI, Connector, Integration, Runtime, ...
Providers    = HTTP, Browser, Kubernetes, Nacos, DB, Redis, ...
Workflows    = cross-component orchestration
```

UDC is one component under xiaozhua Agent, not the total architecture. SPI is a parallel component and must not be silently folded into UDC.

## Core operating model

For UDC, BPM, Connector, and Integration, use the platform's own capabilities:

```text
User requirement
  → intent/task normalization
  → module-specific operation contract
  → verified API or frontend operation
  → request/payload construction
  → explicit execution gate
  → readback of the same target
  → evidence-backed result
```

Do not convert generated Java structure into a parallel source generator. Generated DTO/entity/controller files are evidence of platform behavior and may be regression oracles, but they are not automatically templates to clone.

For SPI, use a different model:

```text
SPI contract
  → extension point
  → plugin implementation
  → registration/loading
  → invocation
  → verification
```

Do not model SPI as ordinary low-code user CRUD unless concrete evidence proves a particular UDC extension calls a particular SPI.

## Evidence-first workflow

1. **Fix the component boundary.** State whether the current task belongs to UDC, BPM, SPI, Connector, Integration, Runtime, or a cross-component workflow. Keep component ownership stable.
2. **Identify the real target environment.** For test2, use the verified route `SSH → 10.0.0.1 → kubectl --kubeconfig=configtest2`; obtain the namespace from that kubeconfig/context. Do not substitute a local kubeconfig or infer namespace from memory.
3. **Inventory the deployed artifact.** Prefer the target container, deployed application image, frontend bundle, controller jar, service jar, logs, and configuration actually used by the running system. Record artifact, version, and when practical SHA-256.
4. **Extract contracts from executable evidence.** Use method signatures, bytecode, annotations, frontend request literals, observed Network traffic, logs, or schema/introspection. A class name, interface declaration, or similar method name alone is not a call edge.
5. **Separate evidence levels.** Mark each fact as `FACT`, `OBSERVATION`, `INFERRED`, `UNVERIFIED`, or `BLOCKED`. Keep static route facts separate from live accessibility, authentication, request payload, response envelope, and successful business effect.
6. **Build a read-only contract first.** Define operation ID, HTTP method, path, request type, response type, write flag, evidence references, and readback operation. Request construction must not imply execution.
7. **Resolve identifiers explicitly.** If the user-facing application identifier is a string but the DTO requires a numeric ID, find and verify the mapping through a read operation. Never coerce or guess it.
8. **Use dry-run before writes.** Validate route, payload shape, target scope, authorization context, and expected readback. Destructive or state-changing operations require explicit user authorization.
9. **Verify after every external write.** Read the exact entity/application/plugin/version/record changed. Do not treat HTTP 200, a Boolean, or a returned ID as proof that the complete platform operation succeeded.
10. **Report non-claims.** Explicitly list what was not verified, especially authentication headers, gateway mapping, response JSON, publish/build side effects, cache invalidation, and cross-module causality.

## Signed BPM/OpenAPI live probes

When an authorized user provides a complete signed mutating request and asks for a live probe, treat the request itself as the execution authorization; do not silently alter identifiers, body fields, headers, or timestamp. Preserve the literal request and record the exact UTC/local execution time.

Classify the result by layer before investigating BPM business logic:

```text
HTTP transport → Gateway authentication/signature → BPM controller → BPM business validation → persistence/effect
```

If the response is a gateway envelope such as `OPEN_GATEWAY_5000` with `message=无效签名`, stop BPM-level diagnosis: the request has not yet established that the BPM controller or business service was reached. Capture and report the gateway `traceId`, HTTP status, response body, and a redacted request fingerprint. Do not infer template, form record, user, command, or database failures from a gateway signature rejection.

For signature failures, inspect in this order:

1. Signature freshness: compare the supplied timestamp with the actual request time and the gateway acceptance window.
2. Canonicalization: verify the exact bytes/string used for signing, including JSON field order, Unicode encoding, empty fields, numeric representation, and newline/whitespace handling.
3. Credential binding: verify `app-key` and signing secret/application configuration belong together; never print or persist secrets.
4. Header/path contract: verify exact header names, path, HTTP method, and whether additional gateway headers are required.
5. Only after the gateway accepts the request, correlate the returned trace ID with BPM logs and verify the intended business effect/readback.

A successful HTTP status is not business success. Conversely, a gateway authentication error is useful evidence that the request reached the gateway, but is not evidence that BPM executed it. Use the compact reproduction and redacted evidence format in `references/signed-bpm-live-probe.md`.


```text
Design-time configuration
  → metadata/version
  → publish/generate
  → generated application artifacts
  → runtime registration
  → controller/appservice/entity
  → DB/Redis/cache
```

Never collapse design-time metadata, generated source, runtime metadata, physical tables, and cache entries into one state.

When browser interaction is unfamiliar or unreliable, do not turn that into a permanent prohibition. Use the strongest available evidence source: deployed container inspection, frontend static analysis, actual Network/CDP capture, controller annotations, bytecode, gateway schema, logs, or a controlled read-only HTTP probe.

A typical UDC contract record should contain:

```text
operation_id
component
artifact/version/sha256
controller_fqcn
method
http_method
class_path
method_path
request_type
response_type
write
required_role
evidence_level
readback_operation
unknowns
```

For a controller with class-level mapping, compose the final path only after reading both class and method annotations. Preserve literal route segments and parameter names exactly. Do not map a frontend token to a Java method by naming similarity.

## 受控写通道：显式 scope + 失败即停

把 agent 从「只读骨架」扩到「受控可写」时，**不要删那三道只读门**（`layer` 的 `if contract.write or method != "GET"`、`policy` 的 `MUTATING_METHODS`、`registry` 未登记写契约）。正确做法是加一个**可选参数**：不传时行为与改动前完全一致（一并 DENY），传了才按白名单放行——这样既有只读测试全部保持绿，改动面只有一个入口。

```python
@dataclass
class WriteScope:
    application_ids: set[str]   # 应用白名单
    operations: set[str]        # operation_id 白名单
    max_writes: int             # 次数上限
    aborted: bool = False
```

三重约束缺一不可。用户授权写时必须问清且只写这三个量：哪个 app、哪些操作、多少次。

**失败即停不等同于自动重试。** 任何一次写失败（HTTP 非 2xx、业务 `status!=0`、传输异常）立即 `scope.record_failure()` 置 `aborted`，后续写全部拒绝并报「已中止（失败即停，不重试）」。不要写重试逻辑，不要在失败后自动换个 body 再试。

注意区分两类「失败」：参数拼错导致的 4xx（路径拼错、必填缺失）是**获取契约前的试探**，分析后修正再发不算重试；平台返回业务错误后自己换个猜测值再发才是重试。前者要在报告里明确标注区别。

**成功判据 = HTTP 2xx AND 业务 `status == 0`。** `BOOT_0000` 或 HTTP 200 单独不作为成功。实现时注意一个易错点：`WriteEvidence.ok` 默认 `False`，若两个失败分支都只 `ok = False`，成功路径忘了显式 `ok = True`，则该字段永远为 False——用测试锁定好路径。

## 写后的验证层次（不能只看接口返回）

写完至少两层验证，缺一层就不算完成：

```text
接口层   HTTP 2xx + 业务 status==0 + traceId
存储层   DB 直接 SELECT 回读该对象（不走接口）
```

存储层用真实库客户端读 `udc_test2` 等库表，不依赖任何 fixture 快照。fixture 只能证明代码路径，不能证明平台状态。实测两者会不一致：接口返回成功但列表查不到（索引延迟/落库异库），或实体建成功但字段未入 `udc_attribute`。

接真实库客户端时两个必坑：

- **一个实例承载上百个 schema，不要绑定单个 database。** 元数据库、用户库、组织库、每个应用的业务库（`<appName>_test2`）都在同一实例上。连接时传 `database=` 再跨库查全报 `1046`；不传 database、所有查询用 `information_schema` 或 `<schema>.<table>` 全限定名。
- **只读门在客户端侧拦，不靠数据库权限。** 首关键字白名单（`SELECT/WITH/SHOW/DESC/DESCRIBE/EXPLAIN`）+ 全语句写关键字扫描 + 拒注释（防 `--` 截断绕过）+ 拒多语句 + 拒 `FOR UPDATE`（加锁）+ `autocommit=False`。写语句必须在到达 cursor 之前被拒，才能区分「安全门生效」与「数据库权限不足」。

## SPI-specific guidance

SPI is not a second UDC generator. Audit it by extension lifecycle:

```text
contract interface
  → extension-point registration
  → implementation discovery
  → runtime loading
  → invocation site
  → output/error behavior
```

Keep these separate:

```text
SPI platform contract
Customer plugin implementation
UDC generated application extension
```

Only connect them when the dependency, registration, or invocation is directly evidenced in code, configuration, logs, or runtime behavior.

## Minimal implementation shape

Keep the Agent-facing adapter small and explicit:

```python
@dataclass(frozen=True)
class OperationContract:
    operation_id: str
    method: str
    path: str
    request_type: str
    response_type: str
    write: bool
    evidence: list[dict]

@dataclass(frozen=True)
class OperationRequest:
    operation_id: str
    method: str
    path: str
    payload: object | None
    write: bool
    evidence: list[dict]
```

The registry describes known contracts. The adapter constructs requests. A separate executor owns transport, authentication, timeout, retry, and write policy. A separate verifier owns readback and evidence evaluation. Do not hide network side effects inside request builders.

## TDD and verification

For each new adapter behavior:

```text
RED    write a behavioral test and observe the expected failure
GREEN  implement the smallest contract-preserving behavior
VERIFY focused tests
REGRESS full offline suite
```

Tests should prove:

- exact route composition;
- literal operation IDs and parameter names;
- write/read classification;
- evidence is attached;
- request construction does not perform network I/O;
- unknown or unverified facts are not promoted to verified contracts;
- readback is tied to the same target.

Keep static/offline evidence separate from live environment evidence. A passing local test does not prove the test2 API is reachable or that a real write succeeded.

## Common failure modes

- **Wrong objective:** implementing a Java source generator because generated files are visible. Stop and return to platform operation.
- **Local generation as the deliverable:** answering a create-entity request by emitting golden-skeleton `.java` files locally. Skeletons are an audit preview of what the platform will generate; the deliverable is platform state — metadata row, platform system attributes, published tables/pages — produced through the design-time chain in `references/udc-design-time-write-chain.md`. The user names this pattern explicitly: generating code outside the platform leaves metadata/pages/table rows nonexistent, which makes the deliverable meaningless ("那你的意义是啥").
- **Wrong architecture:** treating UDC as the whole xiaozhua Agent. Put UDC beside SPI and other components.
- **False route certainty:** recording a controller method without reading its class/method annotations. Keep the route unresolved until both are known.
- **Binding flavour assumed platform-wide:** xiaozhua Boot ships BOTH `@MultiRequestBody` (binds by the parameter's local variable name — wrap the body under that name) and plain `@RequestBody` (flat body). The wrong pairing returns a validation error blaming absent FIELDS rather than the wrapper, so it reads like a wrong field name and sends you hunting DTO typos. Measure per endpoint: send both variants of the same minimal body and keep the one whose error advances to the next missing field.
- **Guessed sub-path read as a verb-only 405:** a literal segment can be swallowed by a sibling `/{id}` GET route (`POST /service/udc/application/create` → 405 via `/application/{id}`), while the real create route is the class ROOT (`POST /service/udc/application`). Take literal segments from `javap -v` constant-pool `Utf8` entries; 405 proves only that that exact path is mapped.
- **False call-chain certainty:** promoting an interface, service name, or similarly named frontend operation into a causal edge. Require executable evidence.
- **Identifier mismatch:** passing an application string ID where the DTO requires `Long appId`. Resolve the mapping first. UDC design-time routes take the numeric segment of the app name as the Long appId (write-chain LIVE evidence); the Spring failure mode is `BOOT_3000 NumberFormatException`, and the response `appId` field is the bare numeric form — normalize both sides to the numeric segment before comparing identity.
- **Gateway prefix has two shapes, not one:** design-time `/udc/...` routes compose as `/service/udc/...`, runtime `udc-runtime/...` routes as `/service/udc/udc-runtime/...`. A prefix helper that blindly prepends `/service` turns runtime routes into `/serviceudc-runtime/...` — every runtime call 404s while design-time calls pass, reading as "runtime contract wrong" when it is a composition bug. A full push test (fire every GET contract at a live app and tally PASS/UNVERIFIED/DENIED/FAIL) surfaces this class immediately; per-route spot checks miss it.
- **Write-as-construction:** allowing an adapter's `create_*` helper to send a request. Builders must be side-effect free.
- **HTTP-success fallacy:** accepting status 200 or returned ID without reading back the same target and checking the intended state.
- **Cross-module leakage:** assuming UDC uses SPI, or that a customer extension is platform core. Record the dependency only when evidenced.
- **Overclaiming from one version:** do not generalize one 5.3.x artifact or one customer application to all xiaozhua versions/apps.
- **Entity-level publish treated as the build gate:** when a physical-table deliverable stalls on `PublishStateUpdateDto.password`, stop — the real gate is the application build `POST /service/udc/runtime/deploy-normal` (`deployType:RELEASE`, body NAME-WRAPPED as `{"deployDto": {...}}`), which needs no password. See the deploy section of `references/udc-design-time-write-chain.md`.
- **publishState read as build status:** after a successful sandbox build the entity can still read `publishState: UNPUBLISH`; verify builds by their products (physical table in the app's own DB, deploy records in `udc_deploy_record`), never by publishState.
- **Physical table searched only in platform DBs:** generated tables land in the application's own database (`<appName>_test2`-style, from the app's Nacos `seeyon.datasource.database`), not in `udc_test2`/`udc_uat`; checking only the latter false-negatives the whole deploy.
- **Credential-gated BLOCKED accepted without checking local skills:** before treating a live route as NEEDS_HUMAN, enumerate local skill directories (e.g. `<HERMES_HOME>/skills/devops/<skill>/`) for `.pem`/`.env`/kubeconfig connection material and re-verify the access path with one real command; `~/.ssh` alone is not evidence of a missing credential.
- **自行取 token / 重登来"续期"会话 —— 禁止（用户明确要求）**：设计态 HTTP 调用确实用 web 设计器 cookie（`SY_ACCESS_TOKEN` + `SY_UID`），但**不要自己去调 `POST /service/ctp-user/auth/token`，不要从浏览器 cookie 里读 token，不要向浏览器注入 cookie，不要清站点存储**。平台的重登机制是「同一账号新登 → 旧 token 立即入黑名单」（`BOOT_1006 token黑名单`），一次重登会把其它浏览器 profile 里还活着的会话全部打死，且不可恢复。正确做法：**写操作走页面内 `fetch(..., {credentials:'include'})`**——用用户已登录页面自己的会话发请求，全程不接触 token 字符串。写前先用一条只读 GET 探针确认该页面会话有效（返回 `BOOT_0000` + 真实业务数据），再发写。会话真失效时，把浏览器窗口交给用户手动登录，或让用户提供独立凭据文件，**不要代登**。
- **多账号并存在同一平台会互相拉黑：** 引入第二个账号前必须先确认目标 app 的权限归属。实测后果不是"顶不上"这么简单——新账号登录即把原账号 token 打入黑名单，而新账号往往没目标 app 的设计态权限（直接落 `/403`），结果两头落空。顺序必须是：先验证权限 → 再决定是否登录。
- **写只走平台 HTTP 接口，DB 永远只读。** 所有变更必须是平台自己的 REST/GraphQL 调用（页面会话 `fetch` 或受控写通道）；数据库客户端只用于 `SELECT` 回读验证，**不执行任何 INSERT/UPDATE/DELETE/DDL**。给用户看方案或验安全门时，也别把 `DELETE FROM ...` 这类 SQL 当示例贴出来——他会直接理解为你要去改库。要证明安全门生效，描述「写语句在到达 cursor 之前被拒绝」即可，不必贴语句。
- **枚举/分组落库查错表会误判成「返回 SUCCESS 未落库」：** 分组写 `ctp_enum_category`（不是 `udc_enum_category`），枚举写 `ctp_enum`（不是 `udc_enum`）。返回的 id 要在两张候选表都查一遍再下结论。`name` 存 i18n JSON 字符串、`code` 才是英文编码，两者对调会得到 `BOOT_1001 枚举编码 不能为空` 这种指向错字段的报错。详见 `references/udc-enum-domain.md`。
- **Version identity across namespaces:** the same component may run different 5.3.x images per environment/namespace; record the running image tag per namespace as the live version identity and never substitute the locally cached artifact version for the deployed one.
- **Condition key = attribute name, not column name:** xiaozhua query conditions are keyed by entity attribute name (e.g. `frameSerialNumber`), never by physical column name (e.g. `kuangjialiushuihao`); passing a column name fails with an `属性[x]不存在` platform error.
- **Enum code is not a number:** an enum DTO's `getEnumCode()` returns the code string (e.g. `kj_status`); the numeric value comes from `getItemValue()`. Feeding the code into a numeric conversion throws NumberFormatException — read both accessors before converting.
- **Child-table lookups return empty, not defaults:** a sub-table queried by a parent id that has no rows — or by a cross-ID-domain key such as a related-order id used as an archive id — returns null/empty, and taking a field from it in the same expression NPEs. Null-check each child lookup and log the skip rather than letting the request fail.
- **Entity-to-table mapping is metadata, not naming:** resolve entity → physical table from `udc_entity`/`udc_attribute`. Several tables can back one business concept, and migrated rows often live in a different table than the code path queries; decide with row-count distribution, not with the table name.

## Required final report

```text
结论：PASS / FAIL / BLOCKED / UNVERIFIED
总系统：xiaozhua Agent
组件：UDC | BPM | SPI | Connector | Integration | Runtime | Workflow
环境：test2|uat，namespace，目标
静态契约：artifact/version/sha256，class，method，route，DTO
实时证据：request，response，readback
写入状态：未执行 | 已授权执行 | 已回读验证 | 未验证
调用链：仅列直接证实的边
未知项：认证、网关、payload、响应、发布、缓存、跨模块关系
```

## Reference

For the concrete test2 UDC Entity/Attribute extraction and operation-contract example, see `references/test2-udc-operation-contract.md`.

For the verified design-time write chain (create entity/attributes via the gateway, error-oracle field discovery, publish contract, javap-from-pod extraction), see `references/udc-design-time-write-chain.md`.

For driving the UDC designer through the user's already-logged-in browser session (page-side fetch write channel, CDP connection quirks, antd menu clicks, React input filling, PASS criteria), see `references/browser-session-operation.md`.

For the UDC enum domain (group/enum/item storage split across `ctp_enum` vs `udc_enum`, GraphQL op family, i18n `name` vs `code`, logical batch delete, reference scan before deletion), see `references/udc-enum-domain.md`.
