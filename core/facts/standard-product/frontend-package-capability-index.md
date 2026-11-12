# standard-product｜前端 50 包能力索引（环境无关）

> 本格是**目录**：UDC 前端扩展工程 `node_modules/@seeyon/*` 下 50 个包各有什么能力、该去哪个包找。
> 只含包名与导出符号，**不含**具体应用/工程/环境，也不含版本（同族包随应用漂移，版本只留在证据件里）。
> 后端 84 包索引见同目录 `platform-package-capability-index.md`；三个高频包（ui/global/udc-runtime-core）的
> 用法增量见 `frontend-platform-packages.md`。本格只回答「去哪个包、用哪个符号」。

分级：`VERIFIED_STATIC`（d.ts 递归抽取，50/50 处理，48 包有符号、2 包无类型，见 §8）。

## 1. Capability

一张**可检索的能力地图**：从「我要做什么」跳到「去哪个包、用哪个符号」。

总量（实测）：**50 个包 / 1953 个导出符号**（值级 828 / 类型级 1125）。

## 2. Version

本格**不记版本**。前端包按应用解析，同一应用内各包主版本线不一致是常态；需要版本时查证据件
`xiaozhua_packages[].version`，不要写进事实格。

## 3. Input

前端扩展工程 `pc/node_modules/@seeyon/*`（= 该工程**实际解析到**的依赖，不是平台全量构件）。

## 4. Required

无前置。抽 d.ts 不需要 node/yarn，纯文件读取。

## 5. Execution

```bash
python tools/core/platform/extract_extension_surface.py \
    --frontend <前端扩展工程 pc 目录> --emit <out.json>
```

递归解析：入口 d.ts → `export *` / `export {…} from` / `export {…}`（先 import 再导出）/
`declare const|function|class|interface|type|enum|namespace` / `export default X`。

## 6. Side Effects

只读 d.ts，不写工程、不装依赖、不连网。

## 7. Known Constraints

### 7.1 我要做什么 → 去哪个包

符号数 = 该包递归后的导出总数（值级/类型级合计）。

| 我要做的事 | 包（符号数） | 抓手符号 |
|---|---|---|
| 写自定义页面：页面入参/变量/数据源/组件代理 | `@seeyon/udc-runtime-core`（501） | `PageComponent` `EventManager` `BaseAggregator`；类型 `ComponentProxy` `DatasourceData` `BpmPageProps` |
| 发请求 / 路由 / 租户 / i18n / 打印 / 加解密 | `@seeyon/global`（373） | `AESEncrypt` `AESDecrypt` `InitI18n` `Context` `HTTPError`；类型 `AjaxOptions` `AppContext` `AttachmentStaticCommands` |
| 选人 / 选部门 / 选角色 | `@seeyon/biz-org-selector`（263） | `OrgSelector` `OrgMemberSelector` `OrgAutoComplete` `OrgInputSearchWithSelector` `OrgFuzzyMatchSearch` |
| 组织数据与权限核心（常量/工具/schema） | `@seeyon/biz-org-core`（186） | `OrgSelectorUtils` `SelectPeopleSchema` `commonUtils` `controlActions` |
| UI 基础组件（基于 antd） | `@seeyon/ui`（151） | `AntdDatePicker` `AntdTimePicker` `CheckboxComponent` `RadioComponent` `SwitchCmp` `TabsCmp` `Item` `Panel` |
| 组织树 | `@seeyon/biz-org-tree`（40） | `DepartmentTree` `InstitutionTree` `OrgTreeRuntime` |
| 侧边树 / 页面布局壳 | `@seeyon/biz-sider-tree`（27） | `MenuTree` `Providers` `defaultLayoutConfigs` `useCtxLayoutConf` |
| 表达式编辑 | `@seeyon/biz-expression`（17） | `ExpressEditorModal` `ExpressCondition` `ExpressEditorInputComponent` |
| 表达式求值（含内置函数库） | `@seeyon/biz-expression-engine`（106） | `ExpressExecuteEngine` + 内置 `abs` `avg` `addDay` `addHour` `allLineMatch` `traverseExpressionTokens` |
| 查询条件构造 | `@seeyon/biz-where`（6） | `Where` `Condition` `ModalWhere` `useWhere` |
| 快捷搜索 | `@seeyon/biz-quick-search`（22） | `SimpleSearch` `ExpandedSearch` `InputSearch` `IconSearch` |
| 页面搜索 | `@seeyon/biz-search`（11） | `EasySearch` `AsyncEasySearch` `CombinedForm` `Search` |
| Excel 导入导出 | `@seeyon/biz-excel-component`（4） | `ExcelImportModal` `ExcelExportModal` `ExcelSettingModal` |
| 报表 | `@seeyon/biz-report`（2）/ `@seeyon/mbiz-report`（2） | `BusinessComponent` `UiBusinessReportSchema` |
| 标签打印 | `@seeyon/biz-label-print`（4） | `LabelPrint` `UdcLabelPrint` `PrintTemplateManage` `PrintRecordList` |
| 二维码 | `@seeyon/biz-qrcode`（4） | `Qrcode` `QrCodeCustom` `QrcodeSetting` |
| 流水号 | `@seeyon/biz-serial-scheme`（3） | `SerialScheme` `SerialSchemeModal` |
| 表单转文档 | `@seeyon/biz-formconvert`（3） | `Formconvert` `FormconvertSettingCon` |
| 头像 | `@seeyon/biz-avatar`（8） | `Avatar` `AvatarList` `AvatarContainer` `AvatarOuter` `getColor` |
| 图标选择 | `@seeyon/biz-icon-library`（3） | `IconSelector` `InternalIconCreator` `useTransfer` |
| 图片选择 / 水印 / 远程组件 | `@seeyon/biz-image-selector`（1）/ `biz-watermark`（2）/ `biz-remote-component`（3） | `ImageSelect` / `WaterMark` / `RemoteComponent` `useDynamicScript` |
| 枚举选择 | `@seeyon/biz-enums`（3） | `EnumModal` `EnumItemTable` `Enums` |
| 数据日志 | `@seeyon/biz-udc-data-log`（8） | `List` `ListWithDetail` `OperatorDetail` `FieldDetail` |
| 运行态参数组件 | `@seeyon/biz-parameter`（1） | `Parameter` |
| 扩展方案数据 | `@seeyon/biz-extension-plan`（2） | `ExTensionPlan` |
| atomic 状态管理 | `@seeyon/atomic-state`（24） | `createAtomic` `createAtomicForm` `useAtomicState` `syncSetAtomicState` `RecoilNexus` |
| UDC 设计态/运行时共享常量与类型 | `@seeyon/udc-core`（106） | `DEFAULT_VIEW_STATE_KEYS` `UDC_ENTITY_FIELD_DATA_TYPE` `analysisComponentDependence` |
| 自定义控件开发（schema 结构约束） | `@seeyon/udc-asset-utils`（37） | 类型 `ControlSchema` `ControlSettingItem` `DiffPatcher` `BuiltinValidateRules`；值 `textOverflowOptions` |
| 微流程前端运行时 | `@seeyon/udc-microflow`（4） | `RuntimeEngine` `NodeRegistryManager` |
| 预置页面 | `@seeyon/udc-preset-page`（3） | `PresetPage` `UDC_PRESET_PAGES` `pageComponents` |
| 手写应用布局新建 | `@seeyon/createApp-newlayout`（7） | `createLayoutApp`；类型 `CreateLayoutAppParams` |
| 三方协同 SDK（13 个桥） | 见 §7.3 | 每包只 1 个工厂函数 |
| 构建脚手架（非运行时库） | `@seeyon/syf`（0） | **无 .d.ts，不可 import 任何符号** |

### 7.2 五条会直接写错代码的铁律

1. **50 个包里 13 个是三方 SDK 桥**，形态完全统一：单个工厂函数 `getXxxSDK()` / `xxxSdk()`
   返回 `Promise<{ name, api: {…} }>`。别指望在这类包上找组件或类型。
2. **符号高度集中**：前 5 个包（`udc-runtime-core` 501 / `global` 373 / `biz-org-selector` 263 /
   `biz-org-core` 186 / `ui` 151）占全部 1953 个符号的 **75.5%**。查不到东西先怀疑查错包。
3. **47/50 包的入口 d.ts 只是 re-export 壳**（`export * from './x'` / `import X …; export {X}`）。
   只解析入口一层会得到 **0 个符号却照样 exit 0** —— 抽取必须递归，且必须有不递归就失败的闸门。
4. **两个包不可 import 类型**：`@seeyon/syf`（构建脚手架，无 d.ts）、`@seeyon/mbiz-new-report`（无 d.ts）。
   在源码里写 `import type … from '@seeyon/syf'` 直接编译不过。
5. **业务组件普遍成对出现**「运行时组件 + `UiBusinessXxxSchema`（设计态 schema）」：
   实测 `biz-report`/`mbiz-report`（`BusinessComponent` + `UiBusinessReportSchema`）、
   `biz-qrcode`、`biz-org-tree`（`UiBusinessOrgTreeScheme`）。页面里用运行时组件，
   只有做设计器控件/配置面板才用 Schema。

### 7.3 三方协同 SDK 桥清单（13）

| 端 | 包 | 工厂函数 |
|---|---|---|
| PC | `@seeyon/biz-sdk-comi` | `getComiSDK` |
| PC | `@seeyon/biz-sdk-dingtalk` | `dingtalkSdk` |
| PC | `@seeyon/biz-sdk-feishu` | `getFeishuSDK` |
| PC | `@seeyon/biz-sdk-wework` | `weWorkPcSDK` |
| 桥接 | `@seeyon/js-sdk` | `createJsSdk` |
| 移动 | `@seeyon/mbiz-sdk-dingtalk` | `dingtalkMobileSdk` |
| 移动 | `@seeyon/mbiz-sdk-feishu` | `getFeishuMobileSDK` |
| 移动 | `@seeyon/mbiz-sdk-wework` | `wxWorkMobileSDK` |
| 移动 | `@seeyon/mbiz-sdk-fengsheng` | `getFengshengSDK` |
| 移动 | `@seeyon/mbiz-sdk-m3` | `getM3SDK` |
| 移动 | `@seeyon/mbiz-sdk-m5` | `getM5SDK` |
| 移动 | `@seeyon/mbiz-sdk-welink` | `getWelinkSDK` |
| 移动 | `@seeyon/mbiz-sdk-wxmini` | `getWxMiniSDK` |

### 7.4 值级 vs 类型级

828 个值级符号（`class`/`function`/`const`/`default`/`local-export` 等，可直接调用或实例化），
1125 个类型级符号（`interface`/`type`/`declare-interface` 等，只在编译期约束）。

注意：组件本体若以 `export default X` 导出且 X 在同文件声明，表中记到的是同名符号；
若只有 `export default SomeAnonymous`，则只留下 Props/类型名。**查具体 props 一律回包内 d.ts 路径**
（`symbols.symbols[名].from` 给出该符号来自哪个 d.ts）。

## 8. Evidence

```
① 路径  docs/audit/artifacts/frontend-surface-20261102/surface.json（472 KB）
        → sources.frontend.xiaozhua_packages[]：每包 version / typings / top_level_dts / symbols
        symbols 段含 entry、files_scanned、symbol_count、symbols{名:{kind,from}}、reexport_by_module
② 复现  python tools/core/platform/extract_extension_surface.py \
            --frontend <前端扩展工程 pc 目录> --emit <out.json>
③ 校验  每包 symbols.entry 必须指向盘上真实 d.ts；files_scanned>0 的包必须 symbol_count>0，
        否则脚本 exit 5（旧证据正因缺这条闸门躺着 47 个空壳却看着全绿）
④ 抽验  @seeyon/ui 151 / @seeyon/global 373 / @seeyon/udc-runtime-core 501 三个包与
        frontend-platform-packages.md 的导出量级一致（该格记的是顶层导出，本格是递归后全量）
```

## 9. Verified

| 项 | 等级 | 说明 |
|---|---|---|
| 50 包清单 + 符号表（1953） | VERIFIED_STATIC | 本机 d.ts 递归抽取，`EXIT=0`，48 包有符号 |
| 13 个 SDK 桥的单函数形态 | VERIFIED_STATIC | 每包 symbol_count=1 且 kind=`declare-const`/`local-export` |
| syf / mbiz-new-report 无 d.ts | VERIFIED_STATIC | `files_scanned=0`，脚本报 WARN 不报错 |
| 前 5 包占 75.5% | VERIFIED_STATIC | 501+373+263+186+151=1474 / 1953 |
| 组件的真实渲染与 props 行为 | 未验证 | 未起 dev server，只看 d.ts 声明面 |

## 铁律

- 查前端能力先查 §7.1 映射表，再进 `frontend-platform-packages.md` 看用法增量；不要凭包名猜能力。
- 50 个包里 13 个是三方 SDK 桥、每个只导 1 个工厂函数；别在 SDK 包里找组件或类型。
- 入口 d.ts 多为 re-export 壳（47/50）：符号必须递归取得，只解析一层等于 0 符号，且会假绿。
- `@seeyon/syf`、`@seeyon/mbiz-new-report` 无 d.ts，写 `import type … from` 直接编译不过。
- 本格只给「有什么」。组件渲染行为与 props 细节回包内 d.ts，用 `symbols.symbols[名].from` 定位文件。
- 包版本不写进本格（随应用漂移）；要版本查证据件 `xiaozhua_packages[].version`。
