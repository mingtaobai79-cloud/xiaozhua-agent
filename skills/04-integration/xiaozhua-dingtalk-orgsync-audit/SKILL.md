---
name: xiaozhua-dingtalk-orgsync-audit
description: "Use when auditing DingTalk-to-Seeyon organization sync."
version: 1.0.0
author: 小爪 🐾
tags: [xiaozhua, v8, dingtalk, organization-sync, spi, java, audit]
---

# xiaozhua V8 DingTalk Organization-Sync Audit

## Purpose

Use this class-level workflow when reviewing or building a DingTalk organization synchronization SPI for xiaozhua V8. Establish what the code supports, what the tenant exposes, and what remains unverified—without fabricating provider fields or live results.

## Workflow

### 1. Establish scope and repository identity

- Verify the exact user-facing Windows path with Python `pathlib`.
- Distinguish an outer folder from the actual Maven project root.
- Inventory README, docs, source, resources, DTO mapping, tests, build files, and runtime configuration.
- If Git is absent, say so; do not infer clean/dirty status.
- Do not use broad cleanup, staging, reset, or overwrite in a mixed workspace.

### 2. Audit the organization-tree contract

Treat the organization as a tree. `department/listsub` returns direct children, not the complete recursive tree. Verify that implementation:

1. starts from the configured root department;
2. traverses with a queue or recursion plus a visited set;
3. persists stable external department ID, name, parent ID, sort, and enable state;
4. separately calls `department/get` when detail fields are required;
5. handles pagination/errors and avoids duplicate department visits.

Do not claim department-detail support if the source only calls `listsub`.

### 3. Audit users and multi-department employment

For every discovered department, verify paginated `user/list` retrieval. Deduplicate the person entity by `userid`, but preserve one employment/department relation per `(userid, dept_id)`.

`dept_id_list` proves multi-department membership. It does not, by itself, prove which department is the main department. Never silently treat `dept_id_list[0]` as a formal main-post rule. If the code does that, label it as a heuristic/gap and explain the risk.

Check stable identity, employee number, name, phone, email, gender, active state, hire date, department relation, relation sort, department leadership, and idempotent upsert behavior.

### 4. Separate HR attributes into independent contracts

Audit these as distinct data domains:

- main department;
- job/title or 职务;
- position/post or 岗位;
- rank/grade or 职级;
- employee roster fields;
- transfer history/events.

Do not infer dedicated HRM support from a generic `title` field in `user/list`. HRM endpoints and roster fields are permission- and tenant-dependent. Candidate endpoints/fields must be verified against current documentation and, when authorized, a real tenant response.

### 5. Map to xiaozhua V8 middle-table DTOs

Trace actual DTO setters and callback calls. Verify root institution and department parent-code semantics, stable `thirdId` and code rules, user identity versus employment identity, main-post flag source, multi-post uniqueness, sort and enable flags, field loss, batch limits, full versus snapshot/incremental semantics, and `markComplete` behavior.

For this SPI contract, the data callback is the only persistence boundary: write through `batchSaveOrg`, `batchSavePosition`, `batchSaveDuty`, `batchSaveLevel`, and `batchSaveMember`; never access the middle-table database directly. The normal pull order is organization/department → post → duty → level → member, followed by `executeSyncToOrgModel(linkerCode)`. Full pull additionally calls `markComplete(linkerCode)`; increment pull must not.

Before implementing dimensions, inspect the exact `cip-connector-api` jar with `javap` (or decompile it) and verify the request/DTO methods. Do not infer that a generic member DTO is enough: `MemberInfoSpiDto` has `postCode`, `dutyCode`, and `levelCode`, while the callback exposes separate dimension batch methods.

Unsupported values must remain explicit gaps; never invent a mapping merely to make the DTO appear complete. For tenant-specific missing HR data, use the following explicit fallback policy when the user requests it: post/position = parsed actual value first, then `user.title`/extension aliases, then create/use a stable `默认岗位`; duty and level = parsed actual value when present, otherwise stable `默认职务`/`默认职级`. Emit the corresponding dimension dictionary before member records and deduplicate by stable external code/name. This is a business fallback, not evidence that DingTalk supplied the value.

### 5a. JDK 8 compatibility for generated clients

If the deployment runtime is JDK 8, set Maven compiler source/target to `1.8` and avoid `java.net.http.*`, `java.time.Duration` in HTTP-client construction, and other JDK 9+ APIs. Use `HttpURLConnection` with explicit connect/read timeouts and buffered UTF-8 request/response handling. Re-scan the changed sources and compile with `javac -source 1.8 -target 1.8` against the exact V8 API jar.

### 5b. Department details are a separate fetch

`department/listsub` provides tree traversal/child basics; it does not prove that detail fields were synchronized. When the mapping needs member counts, owner, group ID, hidden/external flags, or custom attrs, call `department/get` for every discovered department, merge detail over the child record, then map. Keep the root department detail separate from the synthetic root institution DTO.

### 5c. Main-department evidence boundary

`dept_id_list` establishes multi-department membership only. Do not describe its first element as an official main department. If HRM roster/main-department data is unavailable, either leave the main flag unconfirmed or make the heuristic explicitly configurable and label it as such. A `title`/`extension` field can be a fallback for display/job text, but it is not proof of formal HRM post, duty, or rank master data.


### 6. Use an evidence ladder

Report each conclusion with both a fact class and evidence level:

- `FACT`: directly observed in source, config, docs, or live response.
- `OBSERVATION`: behavior observed but not fully explained.
- `HYPOTHESIS`: proposed interpretation requiring verification.
- `FOCUSED VERIFIED`: source/contract/build/test slice completed.
- `REGRESSION VERIFIED`: relevant regression suite completed.
- `LIVE VERIFIED`: real DingTalk read-only request completed and parsed.
- `BLOCKED`: credentials, permissions, build runtime, or environment prevented the check.
- `UNVERIFIED`: relevant path was not exercised.

A successful source inspection is not live evidence. A token authentication failure is not automatically a product defect.

### 7. Perform safe live smoke tests

Only run live tests after the user explicitly provides or authorizes a temporary token. Use read-only endpoints. Keep secrets process-local or in an environment variable; never write them to source, YAML, logs, reports, or fixtures. Redact token values in output.

Minimum smoke sequence:

1. get root direct children;
2. select a returned department ID and get department detail;
3. list users for that department with pagination fields visible;
4. inspect `dept_id_list` and deduplicate relation shapes;
5. if HRM testing is requested, require `appAgentId` and sample `userid` values.

Record endpoint, HTTP status, provider error code/message, response keys, counts, pagination, and redacted field names. Do not dump personal data unnecessarily.

### 8. Provide copyable curl

Use placeholders exactly and give commands for requested endpoints. Prefer `${DINGTALK_TOKEN}` rather than embedding secrets. Include JSON content type and the correct legacy/new API host and authentication header for each endpoint. Explain that HRM endpoint availability depends on tenant authorization.

### 9. Verify implementation claims

For Java projects, inspect the required Java/Maven version and run the real build/tests when prerequisites exist. If a prerequisite is missing, report `BLOCKED` and continue with static/source evidence; never substitute imagined build output. When live testing is unavailable, provide the exact next command the user can run, but label it unverified.

## Common pitfalls

- Calling `listsub` once and claiming a complete organization tree.
- Treating `user/list` as a source for job/rank dictionaries.
- Treating `title` as equivalent to formal HRM position/rank.
- Treating `dept_id_list[0]` as guaranteed main department.
- Deduplicating users in a way that discards secondary department relations.
- Claiming HRM support because curl examples exist but no client/mapping code exists.
- Writing a temporary token into config or repository files.
- Calling a failed build setup a product failure.
- Reporting an unexecuted live request as real organization data.

## Reference

For the endpoint, field, mapping, and evidence matrix, see `references/dingtalk-orgsync-contract.md`.
For the verified callback contract, fallback policy, JDK 8 client pattern, and tenant smoke observations, see `references/dingtalk-v8-orgsync-implementation.md`.
