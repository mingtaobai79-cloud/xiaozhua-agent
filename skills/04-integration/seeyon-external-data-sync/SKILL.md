---
name: seeyon-external-data-sync
description: "Use for 2小爪 UDC integrations with external data APIs."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [2小爪, udc, sync, api, dto, data-quality, kubernetes]
    related_skills: [seeyon-low-code-environment, seeyon-udc-runtime]
---

# 2小爪 External Data Synchronization

## When to use

Use this skill for 2小爪 UDC custom microflows or AppServices that pull ERP, invoice, bill-pool, tax-cloud, or other third-party data and persist it through generated AppService DTOs.

Typical tasks:

- trace a generated microflow Controller into a custom AppService;
- verify the real route, request DTO, external API payload, and persistence mapping;
- prevent `null`, literal `"null"`, invalid numeric values, and malformed dates from entering UDC entities;
- verify that every source row was inserted or updated and no row was silently skipped;
- diagnose slow synchronous syncs, timeouts, and resource pressure.

## Evidence-first workflow

1. Identify the exact environment, namespace, application ID, deployed Pod, and code revision.
2. Inspect the generated Controller before constructing a URL. Record the literal values of `@RestApi`, `@RequestMapping`, and `@PostMapping`/`@GetMapping`. A custom AppService method name is not evidence of an HTTP route.
3. Follow the call chain:

   ```text
   generated Controller
   → generated API interface
   → custom AppService implementation
   → request DTO conversion
   → external HTTP client
   → response DTO
   → covrData/covrPiaojuchimingxiData
   → generated entity AppService
   → physical entity table
   ```

4. Inspect external response DTO types and generated entity DTO setter signatures before changing mappings. Do not coerce every field to String.
5. Capture the external response count/IDs, local pre-state, persistence response, and local post-state. HTTP 200 or `Boolean.TRUE` alone is not proof of complete synchronization.
6. For live verification, use a narrow time range first, then compare source IDs to local IDs programmatically. Report missing, duplicated, inserted, and updated rows separately.

## Route and Controller rules

- Preserve route segments exactly as decompiled; do not infer them from Chinese captions, Java method names, or a neighboring application.
- Generated microflow Controllers commonly have an application-level request mapping and a method-level mapping. The externally reachable route usually includes the platform `/service/{applicationId}/` prefix, but verify the gateway prefix in the target environment.
- If a route returns 404, inspect the deployed/generated Controller and route registration before changing DTOs or retrying guessed paths.
- If the route returns a framework error such as Base64/date parsing, treat that as evidence that the route was reached; then inspect the request DTO serialization contract.

## DTO and field mapping rules

Implement all external-to-UDC mapping in the dedicated conversion method (`covrData`, `covrPiaojuchimingxiData`, or equivalent). Keep the mapping explicit and one source field per target field.

For String target fields:

```java
ConvertUtils.getString(sourceValue)
```

The converter should turn `null`, blank strings, and the literal string `null` (case-insensitive) into `""`, and trim ordinary values. This prevents literal `"null"` pollution in UDC text fields.

For numeric target fields:

- Preserve the generated DTO's numeric type (`BigDecimal`, `Integer`, `Long`, etc.).
- Do not write `""` into a numeric field.
- Use a safe numeric conversion such as `ConvertUtils.safeToBigDecimal` when the upstream API represents a number as text.
- Decide explicitly whether malformed/absent values should remain `null` or use a domain default; never let `String.valueOf(null)` create the literal `"null"`.

For Date target fields:

- Check blank input before parsing.
- Parse the source timezone explicitly when the API supplies an offset.
- On parse failure, log the source field name and record identifier without dumping secrets or the whole payload.
- Do not silently manufacture a default date.

For collections and child DTOs:

- Convert each child through its own mapping method.
- Preserve child IDs where the generated model expects them.
- Distinguish an absent child list from an intentionally empty list according to the AppService update semantics.

## Persistence and completeness

Before classifying a row as insert/update, query local records using the actual external stable identifier. If the external ID is not business-stable, confirm the business key (for example invoice code + invoice number) before relying on ID-only matching.

After `createBatch`/`updateBatch` or equivalent calls:

- inspect the returned `SingleResponse`/`ListResponse` when the API provides one;
- treat null responses, non-success codes, and exceptions as failures;
- keep per-batch counts and failed IDs;
- do not return success when any page or batch failed;
- re-read the same IDs after persistence for live verification.

For paginated external APIs:

- validate the initial response, total, page data, and every subsequent page;
- do not silently skip an empty/error page;
- avoid logging credentials in request DTO `toString()` output;
- record endpoint, time range, page number, page size, source count, and failure reason only.

## Runtime and performance cautions

Large synchronous syncs can block request threads and increase UDC memory pressure. Use narrow-range verification and monitor:

- Pod restart count and `lastState.terminated.reason`;
- `OOMKilled`/exit code 137;
- readiness/liveness probe failures;
- request duration and thread-pool saturation;
- gateway 5xx and Dubbo timeout logs.

If UDC is repeatedly OOM-killed, do not assume a restart fixes the data issue. Check JVM `-Xms/-Xmx`, native memory, agents, thread stacks, and the batch/page sizes. A gateway 500 may be a downstream UDC startup/readiness failure or an expired session token; distinguish these with gateway and UDC evidence.

## Verification report

Use this structure:

```text
结论：PASS / FAIL / BLOCKED / UNVERIFIED
环境：test2|uat, namespace, application, Pod
Controller：annotations and exact route
DTO：request/response/entity field types
调用链：Controller → AppService → external API → persistence
数据质量：source count, local found, missing, duplicate, insert/update counts
错误处理：page/batch response checks and secret-safe logging
运行态：Pod restart/OOM/readiness/gateway evidence
代码变更：files and focused diff
验证：focused tests, compile, live narrow-range test, DB readback
```

## Pitfalls

- Never infer a generated Controller route from a custom AppService method name.
- Never assume an HTTP 200 outer response means the microflow succeeded; inspect inner response data and database state.
- Never use `String.valueOf(nullableValue)` for persisted text fields.
- Never convert numeric/date DTO fields to strings merely to avoid nulls.
- Never write `null`/credentials through request DTO `toString()` into logs.
- Never claim all rows synchronized without a source-ID versus local-ID comparison.
- Never modify production/runtime entity tables directly as a substitute for fixing the mapping or metadata path.

See `references/external-sync-data-quality.md` for the reusable mapping checklist and evidence examples.
