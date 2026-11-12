# registry-entries — resource 域只读契约建议条目（供 UDC-MERGE 任务照抄）

不实际改 `registry.py`（冻结文件，本任务只读复核）。字段顺序与 `models.py` `UdcOperationContract` 10 字段构造签名逐字段一致：
`operation_id, method, path, request_type, response_type, status, write, evidence, required_inputs, verification_rules`。

## 结论：**5 条新增建议**（本域非真空；无既有条目可去重）

去重实测（本轮，registry.py 只读）：全表 **49** 条 `UdcOperationContract`，逐条 operation_id 实测**无**
`attachment` / `download` / `dynamic` / `jar` / `template` / `resource` 形态条目
（`grep -o 'contracts\["[^"]*"\]' components/platform_operations/registry.py` 全量输出逐条核对；
唯一含 `dynamic` 的是 `udc.bi.ganttchart_running_dynamic_select_by_entity`，属 ganttchart 构建件、与资源/文件面无涉）
→ **5 条候选全部为新增**，无 key 冲突、无需合并。
**写形态 5 条（create/create-batch/delete/delete-by-guids/upload）不得入 registry**（只读契约口径）。

> ⚠ 盘面漂移警示: 上表基于本轮实测 registry.py（49 条；与 5.3.517/5.3.260 合批后基线一致）。
> MERGE 落库前必须对当时 registry.py 重新实测 key 唯一性（`grep -c 'UdcOperationContract(' registry.py`
> + 逐 key `grep -n 'contracts["<op>"'`），勿以本文件时点断言为准。
>
> ⚠ 口径边界（主控/审计必读，非验收变更）: **C2**（`POST` 查询）与 **C5**（`POST` 导出）为**非 GET 形态**，
> 按 R2 HANDOFF「只读候选（GET 查询/下载/列表类）」口径属边界项，本文件仍给出构造（对照 registry L86
> `udc.application.search.no_page` 同形态 POST 查询 write=False 先例）；**若 main 采严格 GET-only 口径，
> 仅取 C1/C3/C4 三条，C2/C5 降为契约内标注**。该取舍属主控范围，本文件不自行裁定。

## 建议构造调用（可直接并入 `UdcOperationRegistry.default()`）

```python
res_attachment_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.AttachmentTemplateController", "method": "selectByGuid", "class_sha256": "72241cb3ae302c91cd3baba690eaa25656adcedc13e7cdf25413deebd31444f3", "javap": "docs/audit/artifacts/udc-resource-5.3.517/r1-AttachmentTemplateController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.attachment.template_get_by_guid"] = UdcOperationContract("udc.attachment.template_get_by_guid", "GET", "udc-runtime/attachment-template/{guid}", "Long guid(@PathVariable)", "SingleResponse<CommonFileDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [res_attachment_evidence], ("guid",), ("同一 guid 回读附件模板记录 identity_matches", "响应 SingleResponse<CommonFileDto> 非空", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

res_attachment_guids = dict(res_attachment_evidence, method="selectByGuids")
contracts["udc.attachment.template_list_by_guids"] = UdcOperationContract("udc.attachment.template_list_by_guids", "POST", "udc-runtime/attachment-template/select-by-guids", "List<Long> guids(@RequestBody)", "ListResponse<CommonFileDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [res_attachment_guids], ("guids",), ("同一 guids 集合回读列表长度一致 identity_matches", "响应 ListResponse<CommonFileDto> 非空（或条件致空亦自证）", "POST 查询形态（对照 registry L86 先例，write=False）；网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

res_attachment_app = dict(res_attachment_evidence, method="selectByAppId")
contracts["udc.attachment.template_list_by_app_id"] = UdcOperationContract("udc.attachment.template_list_by_app_id", "GET", "udc-runtime/attachment-template/app/{appId}", "Long appId(@PathVariable)", "ListResponse<CommonFileDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [res_attachment_app], ("appId",), ("同一 appId 回读附件模板列表 identity_matches", "响应 ListResponse<CommonFileDto> 非空", "源码 @ParameterInfo 文案为「附件模板guid」与形参名 appId 不符（逐字照录，语义待 LIVE 确认）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

res_jar_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.DynamicJarController", "method": "download", "class_sha256": "0eb1fd79e96e09eb0122c0aafd77d8922ee3163f46f5436a44c98b476726def2", "javap": "docs/audit/artifacts/udc-resource-5.3.517/r1-DynamicJarController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.jar.download"] = UdcOperationContract("udc.jar.download", "GET", "udc-runtime/dynamic/jar/download", "HttpServletRequest + HttpServletResponse（无参数注解）", "void（Servlet 流式下载，无 transport envelope）", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [res_jar_evidence], (), ("HTTP 200 + Content-Type/Content-Length 类响应头", "落盘字节非空（不适用 envelope 判据；下载对象离线不可确证，LIVE 需先确证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

res_jar_app = dict(res_jar_evidence, method="downloadApp")
contracts["udc.jar.export_app"] = UdcOperationContract("udc.jar.export_app", "POST", "udc-runtime/dynamic/jar/download/{appName}", "String appName(@PathVariable)", "SingleResponse<String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [res_jar_app], ("appName",), ("同一 appName 回读导出结果 identity_matches", "响应 SingleResponse<String> 非空（jar 名/路径或摘要）", "POST 导出形态（非 GET，是否属只读边界由主控裁定）；副作用未确证（离线无写库/写盘证据）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

## 逐字段说明（本域特有口径）
| 字段 | 取值规则 |
|---|---|
| operation_id | `udc.<域>.<操作>`；本域域段取 `attachment`（附件模板面）与 `jar`（jar 包下载导出面） |
| method | javap verb 原值（`GET` / `POST` 逐字） |
| path | 类级 `@RequestMapping` value + 方法级注解 value **逐字拼接**；**禁拼网关前缀**；类级基路径均无前导 `/`、方法级前导 `/` 混用（照录） |
| request_type | 参数名 + 类型 + 绑定注解（`@PathVariable` / `@RequestBody` 按 javap 原值）；C4 无参数注解，照录为 servlet 两参 |
| response_type | 完整泛型写法；C4 为 `void`（Servlet 流式下载，如实标注非 envelope 形态） |
| status | `OperationStatus.VERIFIED_STATIC_BYTECODE`（C4/C5 同；C5 的「副作用未确证」写在 verification_rules，不降级 status） |
| write | `False`（5 条均只读；写形态 5 条已在契约 W 段排除，不入本文件） |
| evidence | dict 列表，逐条含 source/artifact/version/class/method/class_sha256/javap/evidence_level（八键，与 registry 既有条目同构） |
| required_inputs | 路径变量/入参名元组；C4 无入参 → `()` |
| verification_rules | 含 identity_matches 回读 + 网关前缀 UNVERIFIED 如实标注；C3 另加 `ParameterInfo` 文案不符的旁证项；C5 另加副作用未确证项 |

## 排除与不入建议清单（显式）
| 项 | 原因 |
|---|---|
| `AttachmentTemplateController.create / createBatch / delete / deleteByGuids` | **写形态**（创建/删除）→ 只读口径外，仅契约 W 段标注 |
| `RuntimeCOLISplitController.upload`（`upload/result`，MultipartFile） | **上传动作（写）** → 仅标注 |
| `DynamicJarController.importJar`（`/import`，storageKey） / `RuntimeCOLISplitController.upgrade`（`upgrade`） | **写（导入/升级）** 且端点路径无 resource 词干 → 未入本域表，仅契约 W 段备注 |
| `DynamicJarController.getRequestStatus`（`import/status/{requestId}`） | 只读端点但**无本域词干** → 词干口径外（边界登记，如主控认为属 jar 导入面可另开 HANDOFF 扩表） |
| `ResourcePermissionService` / `UdcDynamicResourceServiceImpl` / `AttachmentTemplateRtService` / `AttachmentTemplateRtAppService` / `AttachmentTemplateRtEntityDao` / `AttachmentTemplateDto` / `ExternalFileEvent` | **服务/DAO/实体/DTO/事件层**，非 HTTP 端点（L-A 命中但非 mapping-bearing） |
| `UdcRestPathParse` / `MicroFlowRestPathParser` / `proxy.dto.*Path*` / `FormAppMbController`/`FormAppPcController`（`{pageUrl}`） | **`path`/`url` 伪命中族**（REST 路径解析 / 页面路径变量），非静态资源面 |

## 执行记录（回执行）

- **2026-10-09**：5 条建议（C1–C5：`udc.attachment.template_get_by_guid` / `template_list_by_guids` / `template_list_by_app_id` / `udc.jar.download` / `udc.jar.export_app`）已由 implementer 按本文件「建议构造调用」python 块逐字段照抄落库 `components/platform_operations/registry.py`（插入位置：bi 域 ganttchart 批次之后、`return cls(contracts)` 之前，L146-159 注释块「UDC-MERGE 批2（resource 域, main ROUTE 2026-10-09）」。写 False、分级 VERIFIED_STATIC_BYTECODE，键名与值未做任何臆造。
- 落库时点 registry.py 基线复测：具体 `UdcOperationContract` 构造 48 条 + 3 条 replace 别名 + 1 条通用循环 = 有效键 51，5 条新键全键 0 命中（净新增确认，无 key 冲突），落库后具体构造 53 条、有效键 56。
- 全量测试 `<XIAOZHUA_AGENT_ROOT>/.venv/Scripts/python.exe -m pytest tests/ -q`：**395 passed**（基线 395，全绿；exit=0；tests/ 零改动；落盘证据 implementer/_scratch/r1_test_output.txt）。
- 本文件其余内容（结论 / 构造 / 逐字段说明 / 排除清单）为建议件原文，未改动。

- **2026-10-19 主控复核（回执行校正）**：上述 5 条（C1–C5）已含于 commit `ca05e0d`（`feat(udc-merge): 批2 registry 落库 — resource 域 5 条净新增`），不再是 working-tree 状态；当时回执行写的「待主控提交回填 commit」由此行回填。主控 program 级逐行 diff 复核：5 条契约构造行 + 5 个 evidence 定义行与本文源块 `BYTE-IDENTICAL`（零改写）。当前 HEAD `54bfdf9` 有效键实测 **76**；追加 publish/page 两域各 1 条后 **78**。清单位置以此为准，历史行「有效键 56」为其时点记录，不改写。
