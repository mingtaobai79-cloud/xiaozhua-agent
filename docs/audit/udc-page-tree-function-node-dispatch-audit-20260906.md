# UDC PageTree / FunctionNode dispatch audit (2026-09-06)

结论：PARTIAL / STATIC_CHAIN_EXTENDED；Operation 实现准入仍未满足，真实调用 UNVERIFIED。

目标前端 fieldType：`udcMetaDataSelectFunctionNodeWithPageTreePost`

## 新增可核实事实

在 UDC runtime 5.3.517 artifact 中确认了 FunctionNode 的独立后端 REST 业务链：

```text
GET /udc-runtime/meta-data/select-function-node-tree/{appName}
  → UdcFunctionNodeController.selectFunctionNodeTreeMetaData(String appName)
  → UdcFunctionNodeAppService.selectFunctionNodeTreeMetaData(SingleRequest<String>)
  → UdcFunctionNodeService.selectFunctionNodeTreeMetaData(String appName)
```

证据：

- `docs/audit/artifacts/udc-runtime-5.3.517/UdcFunctionNodeController.javap.txt:14-16,85-125`
- `docs/audit/artifacts/udc-runtime-5.3.517/UdcFunctionNodeAppService.javap.txt:13-18,103-131`
- `docs/audit/artifacts/udc-runtime-5.3.517/UdcFunctionNodeService.javap.txt:621-740`

Controller annotations 静态确认：

- `@RequestMapping("udc-runtime/meta-data")`
- `@GetMapping("select-function-node-tree/{appName}")`
- 返回 `ListResponse<UdcFunctionNodeMetadataDto>`

AppService 静态确认：

- 接收 `SingleRequest<String>`，取出 appName
- 调用 `UdcFunctionNodeService.selectFunctionNodeTreeMetaData(appName)`
- 包装为 `ListResponse.from(list)`

## Domain Service 业务与数据来源

`UdcFunctionNodeService.selectFunctionNodeTreeMetaData` 的字节码确认：

1. 校验 appName 非空；
2. 组装 `param`：`appId=appName`、`type=ResourceTypeEnum.MENU`、`dataStatus=1`；
3. 以 `path`,`sortNumber` 排序调用 `select4Sentniel`；
4. `select4Sentniel` 使用 `CtpResourceCoreAppService.selectPageByConditions(PageRequest)`（Dubbo reference）分页读取资源；
5. 将 `CtpResourceDto` 转为 `UdcFunctionNodeMetadataDto`，用 `TreeNodeUtil.fastBuildTree(..., parentId, -1)` 构建树；
6. 创建 `UdcMetaDataSearchDto(appName)`，调用 `UdcPageInfoMetaDataService.selectPageInfoListByAppName` 获取页面元数据；
7. 调用 `UdcPageMetadata4OssService.getPageInfoListByAppNameWithoutSchema(appName)` 获取 OSS 页面信息，并按 menuCode 归组；
8. 递归把页面元数据写入 FunctionNode 的 `pageMetadataDtoList`，最终按 sortNo 排序。

证据：

- `UdcFunctionNodeService.javap.txt:621-740`：主方法调用顺序与树构建
- `UdcFunctionNodeService.javap.txt:800-889`：CtpResourceCoreAppService 分页读取
- `UdcFunctionNodeService.javap.txt:906-977`：按 menuCode 填充页面元数据
- `UdcFunctionNodeService.javap.txt:579-605`：依赖字段及 DubboReference

页面元数据链进一步确认：

```text
UdcPageInfoMetaDataService.selectPageInfoListByAppName
  → selectPageInfoList
  → MetadataQueryAppService.selectPageMetadataList
  → ResponseUtils.listResponseResolve
```

证据：`docs/audit/artifacts/extmetadata-5.3.318/UdcPageInfoMetaDataService.javap.txt:879-912,1241-1256`。

OSS 页面元数据链确认：

```text
UdcPageMetadata4OssService.getPageInfoListByAppNameWithoutSchema
  → SearchJsonMetadataDto.appName=appName
  → jsonFileName="udc@com.seeyon.udc.page.domain.entity.PageInfoEntity.json"
  → MetadataQueryAppService.selectJsonMetadata
  → ResponseUtils.responseResolve
  → PageInfoItemOssDto → UdcPageMetadataV2Dto
```

证据：`docs/audit/artifacts/extmetadata-5.3.318/UdcPageMetadata4OssService.javap.txt:45-58,907-949`。

## 事实等级与剩余缺口

| 链段 | 状态 | 说明 |
|---|---|---|
| UDC runtime REST controller → AppService | FACT_STATIC_BYTECODE | 精确类、方法、mapping、返回类型已确认 |
| AppService → UdcFunctionNodeService | FACT_STATIC_BYTECODE | 精确 invokevirtual 已确认 |
| Domain Service → CTP resource service | FACT_STATIC_BYTECODE | Dubbo `CtpResourceCoreAppService.selectPageByConditions` 已确认 |
| Domain Service → page metadata service | FACT_STATIC_BYTECODE | `selectPageInfoListByAppName` 已确认 |
| page metadata → MetadataQueryAppService | FACT_STATIC_BYTECODE | `selectPageMetadataList` 已确认 |
| Domain Service → OSS metadata service | FACT_STATIC_BYTECODE | `getPageInfoListByAppNameWithoutSchema` 已确认 |
| OSS metadata → JSON metadata service | FACT_STATIC_BYTECODE | `selectJsonMetadata` 与 JSON 文件名已确认 |
| FunctionNode DTO → REST ListResponse | FACT_STATIC_BYTECODE | `ListResponse<UdcFunctionNodeMetadataDto>` 已确认 |
| 前端 fieldType → 此 REST endpoint | UNVERIFIED | 现有前端证据显示 loader/body/response.content，尚无注册/dispatch 边 |
| 前端 GraphQL field → 此 REST endpoint | UNVERIFIED | GraphQL schema/resolver/operation metadata 未取得 |
| REST ListResponse → 前端 `response.content` + `functionNodes/pages[]` | UNVERIFIED | 可能为另一层 GraphQL 投影，尚无直接证据 |
| 运行环境真实请求 / Readback | UNVERIFIED | 未执行，缺少可用认证/运行入口证据 |

## 关键更正：目标 fieldType 的前端响应投影

重新读取原始前端 chunk 后确认，目标函数 `O(n)` 的 `queryFields` 是纯字符串 `"content"`，并直接返回 `i.content || []`。此前文档中把相邻函数 `B(n)`（fieldType `udcMetaDataSelectAllPageByAppPost`）的显式字段选择：`id/appId/name/caption/uniqueKey/functionNodes/pages{...}` 归到了目标 fieldType，属于证据归属错误。

因此，当前对目标 fieldType 只能确认：

- 请求参数形状（appId、hasAssociateApp、params.urlType/pageType、sort）；
- queryFields=`content`；
- 返回读取 `response.content`。

不能由该前端片段确认目标 fieldType 的 `functionNodes/pages[]` 字段投影；这些显式字段属于相邻 `udcMetaDataSelectAllPageByAppPost`。这进一步说明现阶段不能创建目标 Operation Contract。

原始证据：`docs/audit/frontend/chunks/src_constants_design_page-type_ts-src_services_app-design_template_ts-src_services_design_pag-93bb09.6494d14a.js`，目标字符串附近可见 `queryFields:"content"`，前一函数 B 的 fieldType 为 `udcMetaDataSelectAllPageByAppPost`。

## 实施决策

本轮不创建 `PageTreeOperationContract`、`UdcPageTreeAdapter` 或 `UdcPageTreeApplicationService`：虽然 REST 业务链已经显著闭合，但目标 fieldType 到该 endpoint/GraphQL resolver 仍未满足方案规定的事实准入；并且目标字段投影此前被相邻函数污染，必须降级为 UNVERIFIED。将静态 REST 链直接当作目标 fieldType 合同会越过架构门槛。

状态：

- AUDIT：PASS（新增静态证据已落盘）
- Operation implementation：SKIPPED（准入未满足，不是测试通过）
- Live readonly：UNVERIFIED
- Overall：BLOCKED（阻断为 fieldType 注册/GraphQL resolver/response 投影缺失，不是人工决策阻断）
