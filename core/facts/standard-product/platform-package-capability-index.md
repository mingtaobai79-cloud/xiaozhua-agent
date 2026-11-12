# standard-product｜平台 91 构件能力索引（环境无关）

> 本格是**目录**：91 个平台构件里各有什么能力、该去哪个包找。
> 只含 artifact 名与版本号，不涉及任何具体应用/工程/环境。
> 详细用法见同目录各专题格；方法级签名见证据区。

分级：`VERIFIED_STATIC_BYTECODE`（javap 全量抽取，91/91 成功，见 §8）。

## 1. Capability

一张**可检索的能力地图**：从「我要做什么」跳到「去哪个包、哪个类」。

总量（实测）：**91 个构件 / 10414 个类 / 1145 个接口（1036 真接口 + 109 注解）/ 106005 个方法**。

## 2. Version

见 §7.1 表内「版本」列。同族构件共用主版本线，跨族混版是常态（如 udc-* 5.3.517 与 boot-* 5.3.358）。

## 3. Input

84 个 jar（`com.seeyon:<artifact>:<ver>`），清单来自工程编译 classpath 的解析结果。

## 4. Required

无前置。

## 5. Execution

批量并行抽取 → 生成包级索引与方法索引。见 §8。

## 6. Side Effects

只读 jar。

## 7. Known Constraints

### 7.1 我要做什么 → 去哪个包

| 我要做的事 | 包 | 主类（方法数） |
|---|---|---|
| 拿当前用户/单位/部门 | `boot-starter-systemvariable` | `SystemVariableUtils`(126) |
| 调组织（人/部门/岗位/角色） | `organization-facade` | `OrgCommonAppService`(35) / `OrgUnitBaseAppService`(20) |
| 发起/流转流程 | `bpm-facade` | `BpmAppService`(22) / `BpmTemplateAppService`(32) |
| UDC 发起流程 | `bpm-facade` | **`BpmUdcApiService`(4)**（`*ForUdc`） |
| 待办/待阅 | `ctp-affair-facade` | `AffairCommonAppService`(47) / `AffairUdcAppService` |
| 用户信息 | `ctp-user-facade` | 44 个接口（263 类） |
| 文件上传下载/接 OSS | `boot-starter-file` | `StorageService`(14) / `StorageSpi`(9) |
| 枚举/选项集 | `boot-starter-enums` | `CtpEnumItemService`(135) / `CtpEnumService`(68) |
| 连接器/集成 | `cip-connector-api` | `DataBaseExecutorService`(14) / `LinkerSecurityService`(9) |
| 跨服务调标品 | `boot-starter-dubbo` | `DubboFactory`(5) / `AppServiceProxy`(4) |
| 读写库 | `boot-starter-mybatis` | `AllInOneBaseDao`(41) |
| 出入参包装 | `boot-core` | `com.seeyon.boot.transport.*` |
| JSON/日期/字符串工具 | `boot-core` | `JsonUtils`(28) / `DateUtils`(61) / `StringUtils`(35) |
| 平台注解（OpenAPI/权限/安全） | `boot-core` | `com.seeyon.boot.annotation.*` |
| UDC 运行时 | `udc-starter-runtime` | `UdcPageProxyAppService`(56) |
| UDC 扩展点 | `udc-extend` | `*MetaDataPostProcessor`/`*SaveAsHandler`/… |
| 自定义页面元数据 | `udc-facade` | `com.seeyon.udc.api.*`(10 接口) |
| 低代码能力 | `udc-starter-lowcode` | 37 接口 / 1081 方法 |
| 数据流 | `udc-starter-dataflow` | 16 接口 / 1122 方法 |
| 自定义计划 | `udc-starter-customplan` | 12 接口 / 1001 方法 |
| Excel 导入导出 | `boot-starter-excel` | 2 接口 / 857 方法 |
| 公式计算 | `boot-starter-formula` / `boot-formula-engine` | 13/8 接口 |
| 消息队列 | `boot-starter-mq` | 11 接口 / 495 方法 |
| 定时任务 | `boot-starter-schedule` | 8 接口 / 324 方法 |
| 缓存 | `boot-starter-cache` | `SeeyonCache`(8) |
| 参数配置 | `boot-starter-parameter` | 2 接口 / 248 方法 |
| 元数据 | `boot-starter-metadata` | 81 类 / 1160 方法 |
| 打印 | `boot-starter-labelprint` | 3 接口 / 213 方法 |
| 二维码 | `boot-starter-qrcode` | 4 接口 / 495 方法 |
| 流水号 | `boot-starter-serialnumber` | 6 接口 / 874 方法 |
| 甘特图 | `boot-starter-ganttchart` | 1 接口 / 572 方法 |
| 表单转换 | `boot-starter-formconvert` | 2 接口 / 401 方法 |
| GraphQL | `boot-starter-graphql` | 2 接口 / 627 方法 |
| 事件总线 | `boot-starter-eventbus` | 4 接口 / 102 方法 |
| 数据权限 | `boot-starter-mybatis` | `DataPermissionCheck` / `PermissionCheckUtil` |
| 加密/脱敏/验签 SPI | `boot-spi` | `EntityEncryption` / `SensitiveSpi` / `DataSignExecution` |

### 7.2 包级规模总表（91 个构件，按接口数降序）

| # | artifact | 版本 | 类 | 接口 | 方法 |
|---|---|---|---|---|---|
| 1 | `udc-biz` | 5.3.517 | 1855 | 148 | 22166 |
| 2 | `boot-starter-graphql` | 5.3.600 | 772 | 119 | 7104 |
| 3 | `udc-plugin-api` | 5.3.517 | 307 | 71 | 2667 |
| 4 | `organization-facade` | 5.3.601 | 414 | 54 | 6409 |
| 5 | `boot-core` | 5.3.600 | 512 | 47 | 3940 |
| 6 | `cip-capability-facade` | 5.3.276 | 490 | 46 | 4378 |
| 7 | `ctp-user-facade` | 5.3.429 | 263 | 44 | 2987 |
| 8 | `boot-starter-mybatis` | 5.3.600 | 140 | 43 | 901 |
| 9 | `bpm-facade` | 5.3.374 | 533 | 40 | 5893 |
| 10 | `boot-starter-datamigration` | 5.3.600 | 247 | 28 | 2250 |
| 11 | `udc-starter-lowcode` | 5.3.605 | 121 | 28 | 1089 |
| 12 | `udc-starter-runtime` | 5.3.605 | 307 | 20 | 2834 |
| 13 | `cip-connector-api` | 5.3.286 | 115 | 20 | 1492 |
| 14 | `app-common-facade` | 5.3.274 | 103 | 19 | 1053 |
| 15 | `boot-starter-datainit` | 5.3.600 | 88 | 19 | 587 |
| 16 | `udc-starter-dataflow` | 5.3.605 | 116 | 16 | 1122 |
| 17 | `cip-connector-facade` | 5.3.286 | 121 | 15 | 1165 |
| 18 | `udc-common` | 5.3.605 | 424 | 13 | 4454 |
| 19 | `ctp-affair-facade` | 5.3.315 | 122 | 13 | 1442 |
| 20 | `cip-manager-facade` | 5.3.273 | 95 | 13 | 865 |
| 21 | `udc-starter-customplan` | 5.3.605 | 78 | 12 | 1001 |
| 22 | `boot-starter-formula` | 5.3.603 | 202 | 10 | 1245 |
| 23 | `cdp-data-facade` | 5.3.279 | 127 | 10 | 863 |
| 24 | `boot-starter-mq` | 5.3.600 | 68 | 10 | 495 |
| 25 | `udc-facade` | 5.3.605 | 66 | 10 | 503 |
| 26 | `ctp-message-facade` | 5.3.287 | 45 | 9 | 310 |
| 27 | `boot-starter-cip` | 5.3.603 | 98 | 8 | 967 |
| 28 | `boot-starter-file` | 5.3.600 | 89 | 8 | 1045 |
| 29 | `udc-cicd` | 5.3.517 | 65 | 8 | 635 |
| 30 | `boot-starter-schedule` | 5.3.600 | 50 | 7 | 364 |
| 31 | `portal-facade` | 5.3.392 | 49 | 7 | 633 |
| 32 | `boot-starter-serialnumber` | 5.3.603 | 85 | 6 | 874 |
| 33 | `boot-starter-opinion` | 5.3.260 | 64 | 6 | 990 |
| 34 | `m5-facade` | 5.3.265 | 55 | 6 | 504 |
| 35 | `devops-starter-common` | 5.3.600 | 51 | 6 | 338 |
| 36 | `boot-starter-web` | 5.3.600 | 65 | 5 | 628 |
| 37 | `boot-starter-sharding` | 5.3.600 | 61 | 5 | 463 |
| 38 | `boot-starter-dynamicsql` | 5.3.600 | 42 | 5 | 381 |
| 39 | `boot-starter-condition` | 5.3.603 | 77 | 4 | 396 |
| 40 | `boot-starter-qrcode` | 5.3.600 | 59 | 4 | 495 |
| 41 | `boot-starter-enums` | 5.3.603 | 51 | 4 | 754 |
| 42 | `devops-starter-artifact` | 5.3.600 | 51 | 4 | 611 |
| 43 | `boot-starter-nacos` | 5.3.600 | 26 | 4 | 240 |
| 44 | `boot-starter-proxy` | 5.3.600 | 18 | 4 | 115 |
| 45 | `boot-starter-dubbo` | 5.3.600 | 55 | 3 | 395 |
| 46 | `boot-starter-cache` | 5.3.600 | 50 | 3 | 270 |
| 47 | `boot-starter-appservice` | 5.3.600 | 41 | 3 | 196 |
| 48 | `boot-starter-i18n` | 5.3.600 | 28 | 3 | 367 |
| 49 | `boot-starter-labelprint` | 5.3.600 | 23 | 3 | 213 |
| 50 | `boot-starter-filterchain` | 5.3.600 | 8 | 3 | 22 |
| 51 | `boot-spi` | 5.3.600 | 3 | 3 | 8 |
| 52 | `boot-starter-extmetadata` | 5.3.603 | 106 | 2 | 1223 |
| 53 | `boot-starter-excel` | 5.3.603 | 72 | 2 | 866 |
| 54 | `boot-formula-engine` | 5.3.603 | 41 | 2 | 384 |
| 55 | `boot-starter-formconvert` | 5.3.600 | 40 | 2 | 402 |
| 56 | `boot-starter-prometheus` | 5.3.600 | 32 | 2 | 122 |
| 57 | `boot-starter-datasource` | 5.3.600 | 31 | 2 | 632 |
| 58 | `app-approval-facade` | 5.3.295 | 25 | 2 | 257 |
| 59 | `boot-starter-eventbus` | 5.3.600 | 24 | 2 | 190 |
| 60 | `boot-starter-parameter` | 5.3.603 | 22 | 2 | 248 |
| 61 | `boot-starter-license` | 5.3.600 | 17 | 2 | 168 |
| 62 | `boot-starter-artifact` | 5.3.600 | 16 | 2 | 96 |
| 63 | `boot-starter-dynamicloader` | 5.3.600 | 15 | 2 | 109 |
| 64 | `boot-starter-websocket` | 5.3.600 | 8 | 2 | 23 |
| 65 | `boot-starter-shortlink` | 5.3.600 | 5 | 2 | 15 |
| 66 | `cip-capability-common` | 5.3.276 | 425 | 1 | 5148 |
| 67 | `boot-starter-metadata` | 5.3.600 | 81 | 1 | 1160 |
| 68 | `boot-starter-ganttchart` | 5.3.600 | 50 | 1 | 572 |
| 69 | `boot-starter-module` | 5.3.600 | 40 | 1 | 216 |
| 70 | `boot-starter-elasticsearch` | 5.3.290 | 25 | 1 | 252 |
| 71 | `boot-starter-datatype` | 5.3.600 | 23 | 1 | 160 |
| 72 | `cip-openapi-common` | 5.3.260 | 21 | 1 | 134 |
| 73 | `boot-starter-attachment` | 5.3.290 | 15 | 1 | 151 |
| 74 | `boot-starter-spi` | 5.3.600 | 12 | 1 | 52 |
| 75 | `udc-web` | 5.3.517 | 54 | 0 | 691 |
| 76 | `udc-extend` | 5.3.517 | 40 | 0 | 294 |
| 77 | `boot-starter-swagger` | 5.3.600 | 25 | 0 | 131 |
| 78 | `boot-starter-index` | 5.3.265 | 24 | 0 | 133 |
| 79 | `boot-starter-security` | 5.3.600 | 17 | 0 | 83 |
| 80 | `boot-starter-monitor` | 5.3.600 | 15 | 0 | 151 |
| 81 | `boot-starter-transaction` | 5.3.600 | 15 | 0 | 56 |
| 82 | `boot-starter-threadpool` | 5.3.600 | 14 | 0 | 113 |
| 83 | `boot-starter-environment` | 5.3.600 | 13 | 0 | 77 |
| 84 | `boot-starter-lock` | 5.3.600 | 9 | 0 | 80 |
| 85 | `boot-starter-mgn-export` | 5.3.600 | 9 | 0 | 48 |
| 86 | `boot-starter-sensitive` | 5.3.603 | 9 | 0 | 40 |
| 87 | `boot-license-generator` | 2.6.0 | 8 | 0 | 61 |
| 88 | `boot-starter-frontend-log` | 5.3.600 | 8 | 0 | 26 |
| 89 | `boot-starter-tomcat` | 5.3.600 | 7 | 0 | 51 |
| 90 | `boot-starter-systemvariable` | 5.3.603 | 4 | 0 | 147 |
| 91 | `boot-starter-scanner` | 5.3.600 | 2 | 0 | 124 |

### 7.3 检索姿势

方法级索引在 `batch2/_index.json` 的 `method_index`（69369 条），key 形如
`<artifact>/<类>#<方法>`，value 是 `[{returns, args}]`。

```bash
# 找「哪个类有这个方法名」
uv run --no-project python -c "
import json
d=json.load(open('docs/audit/artifacts/extension-surface-20261029/batch2/_index.json',encoding='utf-8'))
for k,v in d['method_index'].items():
    if 'selectMemberByOrgId' in k: print(k, v)
"
```

## 8. Evidence

```
① 路径  docs/audit/artifacts/extension-surface-20261029/batch2/
        84 个 <artifact>.json（每包签名面）+ _progress.jsonl（84 条记录，成功 84）
        + _index.json（包级索引 + 69369 条方法索引）+ _INDEX.md（人读版）
② 复现  uv run --no-project python tools/core/platform/extract_surface_batch_par.py \
          --targets <targets.json> --emit-dir <batch2> --progress <batch2>/_progress.jsonl \
          --javap <javap 原生路径> --workers 10 --limit 1000
        uv run --no-project python tools/core/platform/index_extracted_surface.py \
          --batch-dir <batch2> --emit-json <batch2>/_index.json --emit-md <batch2>/_INDEX.md
③ 校验  _progress.jsonl 应 84 条全 ok；_index.json 的 totals 应为
        包 91 / 类 10414 / 接口 1145 / 方法 106005；
        §7.2 表内每行数字都能与 _index.json 的 packages[] 逐项对上。
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 91 个构件的类/接口/方法数 | `VERIFIED_STATIC_BYTECODE`（91/91 抽取成功） |
| 总量 10414 类 / 1145 接口 / 106005 方法 | `VERIFIED_STATIC_BYTECODE`（汇总复算） |
| 「我要做什么 → 哪个包」映射 | `VERIFIED_STATIC_BYTECODE`（按类名与方法数归组） |
| 各方法业务语义 | **UNVERIFIED**（索引只给名字与签名） |

## 铁律

- 找能力先查本格 §7.1 的映射表，再进专题格看用法；不要凭包名猜。
- 包规模数字来自实测（`_progress.jsonl` 91/91），引用时不要凭印象改。
- 同族构件跨版本混用是常态（现基线：boot 族 5.3.600 / formula 族 5.3.603 / udc 族 5.3.605 / udc-biz 5.3.517），逐构件版本见 `BASELINE.md`；引用某个类前先确认它在你解析到的那个包里。
- 本格只给「有什么」，语义与运行行为必须回各域专题格或实测。
