---
name: seeyon-excel-import-export-migration
description: Seeyon V8 Excel import/export migration patterns for existing ServiceImpl/controller implementations, sheet mapping, enum/member conversion, template sheets, and JDK 8 compatibility.
---
# Seeyon Excel import/export migration

Use this skill when migrating, fixing, or extending Excel-based import/export in a Seeyon V8 SPI project.

## Default shape
- Keep the import/export methods in the existing `*ServiceImpl` class when the project already follows that pattern.
- Keep the controller thin: inject the service interface plus the impl only when the endpoint needs the concrete helper method.
- Do not invent a new layer or helper module just to move a single Excel workflow.

## Column order is the contract
- Reads and writes are POSITIONAL: `ExcelUtils.readExcel(InputStream, DTO.class, sheetIndex)` wraps EasyExcel and, on the reader side, only sets `headRowNumber` — the header TEXT is never matched. Column `i` maps to the `i`-th `@ExcelColumn` field in declaration order, and the writer emits `@ExcelColumn.value()` in that same order. The DTO's field order IS the sheet's column contract, i.e. what the user sees in the template.
- Add a new column by adding the field at the intended position in the DTO; never reorder existing fields unless the workbook layout is allowed to move.
- One sheet = one DTO shared by import, export and template. Audit all three flows before claiming a change is consistent: an import-only or export-only DTO with an extra column in the MIDDLE shifts every later value one field over (dates/numbers come back null or garbled, with no error). An extra TRAILING sheet is harmless — sheets are addressed by index — an extra middle column is not.
- Before telling the user an exported file can be edited and re-imported, diff the export DTO columns against the import DTO and state whether that sheet actually round-trips; do not assume it.
- To re-verify the mechanism on a new platform build: `javap -p -c` the `ExcelUtils` class from `boot-core-<ver>.jar` and read `setHead(...)` — declared fields + `ExcelColumn.value()` + reader-side `headRowNumber` only. Audit recipe and the sheet↔DTO map: `references/sheet-dto-contract.md`.

## First-pass checklist
1. Identify the actual sheet contract in the current code.
2. Separate business sheets from template-only helper sheets.
3. Map each Excel column to the persisted DTO/entity field.
4. Determine whether each field is stored as:
   - raw text
   - numeric value
   - enum item ID
   - member/user ID list
   - foreign key to another configuration table
5. Verify the code compiles on JDK 8.

## Import rules
- Read the workbook once, then parse each sheet by index.
- Only process the sheets that carry business data.
- If there is a helper/config sheet, treat it as template metadata unless the old system explicitly imports from it.
- For each main row:
  - validate the business key first
  - query existing records by the business key
  - update when found, create when missing
  - save the parent first, then child rows
  - if child rows are replaced wholesale, delete old children before rebuilding
- **CRITICAL — update does not cascade children**: `appService.update(parentDto)` only updates the parent record. The platform `updateBase()` source reveals why: internally it calls `selectCascadeById` to get old data, then `mergeMapData(oldMap, newMap)` diffs old vs new by id. New child DTOs built from Excel rows have no id, so the merge phase discards them before `recursiveUpdate` ever runs. The `create()` path bypasses merge diff, so it cascades fine. This is the #1 cause of "import update loses child data" bugs in Seeyon V8 migrations.
- **Fix: use Dao.createBatch, NOT childAppService.create**: The intuitive fix is `childAppService.create(childDto)` after `update()`, but this hits **aggregate-root validation** — the child AppService validates that parentId references a valid aggregate root and rejects standalone creates. The correct bypass is:
  1. Convert each child DTO to its Entity via `BeanUtil.copyProperties(dto, Entity.class)`
  2. Set `entity.setId(null)` and `entity.setParentId(parentId)`
  3. Call `childDao.createBatch(List<Entity>)` — `BaseMybatisDao` exposes `createBatch(List<T>)`, `createBatchNoClob`, `createBatchIgnoreTime`
  4. Clear the parent DTO's child lists (`setChildDtoList(Collections.emptyList())`) before calling `appService.update(parentDto)` to avoid mergeMapData interference
  This bypasses all Service-layer validation while keeping the batch in one DB round-trip.
- Convert display values back to persisted IDs:
  - member names → member IDs
  - enum text → enum item IDs
  - currency Chinese name → exchange-rate record ID
- **Never let a conversion helper fall back silently.** The platform helpers drop unresolved entries — `getMemberIdsByName` returns a string missing those names, `getEnumItemIdByCodeAndValue` returns `0L` — so a non-blank 姓名 or 枚举文字 that does not match imports as an empty field with no error, and the user reports "导入之后这个字段丢了". Wrap every conversion so a filled cell that cannot be resolved throws `BusinessException(ErrorCode.BUSINESS_ERROR).addError(...)` naming the business key + column + offending value; for enums also list that enum's allowed values (`items.stream().map(name).collect(Collectors.joining("、"))`) so the user can fix the workbook in one pass. Blank cells stay allowed (blank → skip / empty). Log the resolved 姓名→ID (and enum text→ID) pairs for every import row. Lookup internals, the "field went missing after import" diagnosis tree and the enable-state probe are in `references/member-and-enum-lookups.md`.
- Rule-driven derived fields (a 运算规则 column selecting 加/减/乘/除) computed during import: guard the division branch for a zero divisor. `BigDecimal.divide` throws `ArithmeticException: / by zero`, and both operands usually come from cells that may be blank — `parseBigDecimal(blank)` returns `ZERO` — so a row with 0 in both rate columns aborts the entire import. Agreed behaviour: divisor 0 and dividend 0 → result `ZERO` plus a warning log (that period has no rate); divisor 0 and dividend non-zero → `throw new BusinessException(ErrorCode.BUSINESS_ERROR).addError("核算大类【x】的物流费率运算规则为除法，但境外物流费率为0（开始时间：…，结束时间：…），无法计算，请检查【物流费率】页签的数据")`; otherwise keep `divide(scale, RoundingMode.HALF_UP)`. A bare `divide()` is a latent crash for every customer dataset, not only the one in hand.

## Export rules
- Reverse every import transformation:
  - member IDs → names
  - enum item IDs → display text
  - foreign key IDs → readable labels when the template expects them
- Preserve blank helper fields only if the template needs them.
- Build each output sheet from the persisted model, not from the import DTO.

## Template sheet guidance
- A template sheet that lists departments, business units, currencies, or other dictionary values is usually just a reference/helper sheet.
- If the old system never reads that sheet during import, it is not part of the business payload.
- Do not over-model a dropdown/reference sheet as a required import sheet unless the runtime actually consumes it.
- If a helper sheet is only for humans, keep it out of the import parser even if it is exported with the workbook.

## Response contract hygiene
- If the codebase already uses `SingleResponse<T>` for API results, keep import/export endpoints on that shape instead of mixing in `AjaxResult`.
- Prefer `throw new BusinessException(ErrorCode.BUSINESS_ERROR).addError(...)` for validation and lookup failures that should abort the flow.
- Return success payloads with the concrete data the caller needs (for example, file `storageKey`), not a mixed status wrapper plus extra map fields unless the contract truly needs them.

## Wrapper / query pitfalls
- `Wrapper` is normally built on the entity class, not the DTO class.
- Use entity field names in criteria.
- Common pattern:
  - `new Wrapper(Entity.class)`
  - `wrapper.createCriteria().andEqualTo("field", value)`
  - `wrapper.createCriteria().andGreaterThanOrEqualTo("startTime", now)`
  - `wrapper.createCriteria().andLessThanOrEqualTo("endTime", now)`
  - reserve `andCondition("field<=", value)` style only when the API explicitly expects condition fragments
  - `wrapper.orderBy("createTime").desc()`
- If the service returns DTOs from `selectListByWrapper`, that is fine; the query still targets the entity.
- For effective-date records, filter with the current time explicitly:
  - `startTime <= now`
  - `endTime >= now`
- If the end time can be null in legacy data, add a null-friendly fallback instead of assuming every row is bounded.

## JDK 8 compatibility rules
- Avoid Java 9+ APIs in migrated code.
- Replace:
  - `InputStream.readAllBytes()` → `ByteArrayOutputStream` copy loop
  - `String.isBlank()` → `StrUtil.isBlank(...)` or project `StringUtils.isBlank(...)`
  - `Stream.toList()` → `collect(Collectors.toList())`
  - `List.of(...)`, `Map.of(...)`, `Set.of(...)` → mutable collections / `Collections.singletonList(...)`
- Do not assume the build target will forgive newer syntax just because the local JDK runs it.

## Verification
- Compile after the edit. If the new column comes from a UDC designer change that has not been published yet, expect exactly one class of remaining error from the full javac run — the missing `getXxx`/`setXxx` accessors for that field; treat it as "field not built yet" in the report, and treat any other error as a real defect to fix first.
- When the user hands over the actual workbook that failed to import, parse that file and dry-run it against every validation in the import path instead of inferring from code alone — recipe in `references/import-data-preflight.md`. Report all blockers in one pass (fixing the crash exposes the next rejection), and save any corrected workbook under a NEW filename rather than overwriting the user's data file.
- If the task touches Excel parsing, check all sheet indexes and column mappings once more.
- If the task touches lookup data, verify the source table/service for the helper sheet or dictionary list.
- If you introduced a new helper method, confirm the controller still calls the intended service path.

## Reference notes
- See `references/sheet-dto-contract.md` for the positional column contract: how `ExcelUtils`/EasyExcel maps columns, the sheet↔DTO audit table (which DTO each of the import/export/template flows uses), the export-round-trip trap, and coding a column before the platform is rebuilt.
- See `references/seeyon-excel-import-export-migration.md` for session-specific examples, including the multi-sheet import/export split, the helper/config sheet source, and the JDK 8 byte-copy fix.
- See `references/seeyon-dao-introspection.md` for how to discover Dao/Entity methods via javap on platform jars (BaseMybatisDao.createBatch, field names, etc.).
- See `references/import-data-preflight.md` for the workbook dry-run recipe: read the user's real .xlsx without installing anything (`uv run --with openpyxl`), mirror each import validation against the sheets, and report every blocker at once.
- See `references/member-and-enum-lookups.md` for why member/enum lookups silently drop values (the `is_enable = 1` filter, i18n JSON name matching, swallowed SQL exceptions, the `0L` fallback), the diagnosis tree for "字段导入后变空", and the strict-conversion + enable-state-probe pattern.
