# standard-product｜前端组件签名与传参（自定义页面）

> 本格回答**「这个组件要传什么」**：101 个有完整 props 的组件 + 1686 个 props 类型 + 291 个函数签名，字段名/类型/是否必填全部逐字来自包内 d.ts。
> 只含包名、组件名与签名，不含应用/工程/环境与版本。包能力全貌见 `frontend-package-capability-index.md`；
> 三个高频包的用法增量见 `frontend-platform-packages.md`。

分级：`VERIFIED_STATIC`（d.ts 逐字抽取，见 §8）。

## 1. Capability

从「我要放一个 XX 组件」到「照抄这行传参」：
- 48 个有 d.ts 的包共 117 个对外组件，其中 **101 个有完整 props 字段**（86%）
- 1686 个 props 类型可查（含组件未挂上的，按类型名直接查字段）
- 291 个函数有参数表与返回类型（表达式函数库是大头）
- 三类通用形态（弹窗 / 受控 / 回调）可直接套用

## 2. Version

不记版本。包版本随应用漂移，需要时查证据件 `seeyon_packages[].version`。

## 3. Input

`pc/node_modules/@seeyon/*/**.d.ts`（工程实际解析到的依赖）。

## 4. Required

无。抽签名不需要 node/yarn。

## 5. Execution

```bash
python tools/core/platform/extract_extension_surface.py \
    --frontend <前端扩展工程 pc 目录> \
    --emit <surface.json> --emit-signatures <signatures.json>
```

签名扫描沿**所有** `from './x'`（import 与 export 都算）递归 —— 平台包常见
`import { X } from './components/x'; export { X };`，只跟 export 链会漏掉 props 定义。

## 6. Side Effects

只读 d.ts。

## 7. Known Constraints

### 7.1 业务组件 props 速查（必填字段逐字）

| 包 | 组件 | props 类型 | 必填字段 |
|---|---|---|---|
| `biz-excel-component` | `ExcelImportModal` | `ExcelImportModalProp` | `appId: string` `entityName: string` `onClose: () => void` `fileName: string` |
| `biz-excel-component` | `ExcelExportModal` | `ExcelExportModalProps` | `appId: string` `entityName: string` `fileName: string` `withData: boolean` `searchCondition: any` |
| `biz-org-selector` | `OrgSelector` | `OrgSelectorProps` | `visible: boolean` `onClose: () => void` `onOk: (value: ValueTypes, full: ValueWithName[]) => void` |
| `biz-org-tree` | `OrgTreeRuntime` | `OrgTreeRunTime` | `settings: OrgTreeSetting` |
| `biz-sider-tree` | `MenuTree` | `MenuTreeProps` | `treeProps: TreeProps & { treeData?: DataNode[]; … }` `headerLeft: ReactNode` |
| `biz-sider-tree` | `SiderTree`（default 导出，表内记 `_default`） | `ISiderTreeProps` | `title: React.ReactNode` `titleMenuTools: (nodeData: any) => React.ReactNode` |
| `biz-avatar` | `Avatar` | `AvatarProps` | `type: AvatarType` `size: number` `subType: AvatarType` |
| `biz-avatar` | `AvatarMore` | `MoreProps` | `size: number` `label: string` |
| `biz-watermark` | `WaterMark` | `WaterMarkProps` | `appId: string` `children: any` |
| `biz-qrcode` | `QrCodeCustom` / `Setting` | `IProps` | `appId: string` `appName: string` |
| `biz-serial-scheme` | `SerialScheme` | `ISerialSchemeProps` | `appName: string` |
| `biz-image-selector` | `ImageSelect` | `ImageSelectProps` | `appName: string` |
| `biz-expression` | `ExpressEditorModal` | `ExpressEditorModalProps` | `initialState: InitialStateProps` |
| `biz-expression` | `ExpressCondition` | `ExpressEditorExpressCondition` | `renderComps: (data?: any) => RenderCompsReturn` |
| `biz-extension-plan` | `ExTensionPlan` | `Props` | `appName: string` `managerOrgId: string \| any` |
| `global` | `SyLink` | `SyLinkModel` | `url: string` `children: any` |
| `ui` | `Collapse` | `ExtendCollapseProps` | `headerStyle: 'reserve' \| 'customer'` |
| `ui` | `FloatButton` | `FloatButtonProps` | `addOperates: AddOperates[]` |
| `ui` | `Button` | `ButtonProps` | 无必填（`onClick` / `isDebounce` / `delay` 等全可选） |
| `ui` | `DatePicker` | `PickerDateProps` | 无必填 |
| `ui` | `InputComponent` | `InputProps` | 无必填 |
| `ui` | `RadioComponent` | `RadioProps` | 无必填 |

> 完整 117 个对外组件、每个组件的全部字段（含可选）：`signatures.json` 的
> `packages[包].components[组件].props[]`，字段 = `{name, optional, type}`。
> 另 16 个组件没挂到字段，且**这 16 个就是真没有**：
> 13 个源码写死 `props: any`；`UtcPickerModel` 在 d.ts 里根本没定义（只在 .js.map 里）；
> `propsType`（biz-qrcode）是纯索引签名 `[index: string]: any`；`RouteProps` 是 react-router 的联合类型。
> 1686 个 props 类型里也能按名查到。

### 7.2 三类通用形态（照这个套，不要自创）

```
① 弹窗类      visible: boolean  +  onClose: () => void  +  onOk?: (value, full?) => void
             （OrgSelector 必带 visible/onClose/onOk；Excel 系用 onClose + onOk 或内部受控）

② 受控类      value?: T  +  onChange?: (value?: T, full?: F[], info?: ExtraInfo) => void
             （OrgSelectorInput / OrgSelectorTextarea 实测签名，三个入参依次是值、完整对象、附加信息）

③ 回调类      统一 on 前缀 + 箭头函数类型：onFetch?: (status, callbackData) => void
             onOk?: (val: any, callbackData?: any) => void
             awaitNext?: (storageKey: any, templateId: string) => Promise<any>
```

### 7.3 平台业务组件的两个「必然必填」

绝大多数 `biz-*` 组件内部要回平台取数，所以必填里一定有应用上下文：

- `appId: string` —— Excel 导入导出、水印、二维码
- `appName: string` —— 流水号、图片选择、扩展方案
- `appId + entityName` —— Excel 导入导出这一对是绑定实体的，缺一个组件拿不到数据

⇒ 在自定义页面里用这类组件，先把 `appId`（当前应用）与 `entityName`（当前实体）从前端运行时上下文取出来，
不要硬编码。取法见 `frontend-platform-packages.md` 的 `@seeyon/global` / `udc-runtime-core` 段。

### 7.4 表达式函数库（`@seeyon/biz-expression-engine`，可直接 import 调用）

这些不是组件，是纯函数，签名逐字：

```
判空/断言   isNull(value: any, dataType?: DataType): boolean
            isNotNull(value: any, dataType?: DataType): boolean
            conditionReturn(a: boolean, b: any, c: any): any

随机/标识   rand(): number          randBetween(min: number, max: number): number
            uniqueMark(): string    idGenerate(): string

集合/包含   contains(param1: any, param2: any, dataType: string): any
            notContains(param1: string[] | string, param2: string[] | string, dataType: string): boolean
            containsAny(param1: string[] | string, param2: string[] | string): boolean
            notContainsAny(param1: string[] | string, param2: string[] | string): boolean
            thereIn(param1: string[] | string, param2: string[] | string, dataType: string): boolean

日期差值    dateDiff(d1: number, d2: number): number
            hoursDiff(d1: number, d2: number): number
            minuteDiff(d1: number, d2: number): number
            timeMinuteDiff(d1: string, d2: string): number
            dataDifference(d1: number, d2: number): any

日期加减    addHour(d: number, hours: number): any
            addHourToTime(d: string, hours: string): string
            addMinutes(cur: number, minutes: number): any
            addMinuteToTime(cur: string, minutes: string): string

日期取值    year(d: number): any   month(d: number): any   day(d: number): any

格式转换    getTime(timeStr: string): Date
            getDate(dateStr: string): Date
            getDateTime(dateTimeStr: string): Date
            dateToString(date: number, fromatStr: string): any   // 参数名 fromatStr 原文如此
            stringToDate(dateStr: string, format?: string): any
```

> 注意 `d1/d2` 是 **number（时间戳）**，只有 `*ToTime` 系列收字符串。
> 传字符串进 `dateDiff` 会静默得到 NaN，这是最容易写错的一处。

### 7.5 全量查法

```bash
python - <<'EOF'
import json
d = json.load(open("docs/audit/artifacts/frontend-surface-<日期>/signatures.json", encoding="utf-8"))
p = d["sources"]["frontend"]["packages"]["@seeyon/biz-excel-component"]
print(json.dumps(p["components"]["ExcelImportModal"]["props"], ensure_ascii=False, indent=1))
EOF
```

键结构：`packages[包] = {components, props_types, functions, classes}`
- `components[名]` = `{propsType, props?: [{name, optional, type}], from}`
- `props_types[名]` = `{kind, fields[], extends?, from}`（没收进组件的纯类型）
- `functions[名]` = `{args, returns, from}`
- `classes[名]` = `{extends, methods[{name,args,returns}], from}`

### 7.6 props 从哪来（决定你该查哪份文档）

117 个组件的 props 只有四种来源，认清了才知道「照抄哪份定义」：

| 来源 | 特征（d.ts 原文） | 典型 | 字段怎么拿 |
|---|---|---|---|
| **包内自造** | `export interface XxxProps {` 直接写在本包 | `IUdcTableProps`（109 字段）、`MenuTreeProps`（36） | 本格 §7.1 或 `packages/<包>.md` |
| **antd 派生** | `type XType = React.FC<AlertProps> & {…}`，`AlertProps` 来自 `antd` | `Alert`/`Carousel`/`Descriptions`/`Menu`/`Rate`/`Statistic`/`Upload`/`Slider` | `signatures.json` 里已挂全字段并标 `propsFrom: antd:<文件>`；语义查 antd 文档 |
| **交叉扩展** | `Omit<TreeSelectProps<T>,'onChange'> & GenSchemaProps.TreeSelect & {…}` | `CusTomTreeSelectProps`、`ExtendCollapseProps` | 平台加的字段在 `props[]` 里，`propsExtends` 标了还继承自谁 |
| **真无类型** | 源码写 `props: any`，或类型只在 `.js.map` 里 | `Where`/`Condition`/`ModalWhere`/`UdcPageFrameWrapper`/`UtcPicker` | 只能读实现体；**别猜**，用 `any` 传或问原作者 |

判别口诀：
- `propsFrom` 字段存在 → 是外部包类型（antd / rc-slider / react-router-dom），字段已合并，但**版本跟随 node_modules 里的 antd 版本**
- `propsExtends` 字段存在 → 是 Omit/交叉派生，`props[]` 只含字面那部分，父类型字段要另外查
- 两者都没有且 `props` 为空 → 源码真没约束，当 `any` 用

平台设计态字段（只出现在 ui/biz 包的交叉类型里，antd 没有）：`dataType`、`hasError`、`customTheme`、
`displaySize`、`pageId`、`pageTime`、`appId`、`appName`、`entityName`。

## 8. Evidence

```
① 路径  docs/audit/artifacts/frontend-surface-20261102/signatures.json（1.0 MB）
        48 包 / 组件 117（完整 props 101）/ props 类型 1686 / 函数 291
② 复现  python tools/core/platform/extract_extension_surface.py \
            --frontend <pc> --emit <surface.json> --emit-signatures <signatures.json>
③ 校验  每个组件的 propsType 必在 props_types 里；每个字段的 type 必须能在同包 d.ts 命中
④ 抽验  ExcelImportModal 24 字段 / ExcelExportModal 23 / Avatar 26 / MenuTree 36，
        与包内 dist/components/*/index.d.ts 原文逐一对应
```

## 9. Verified

| 项 | 等级 | 说明 |
|---|---|---|
| 72 组件 props 字段（名/类型/可选） | VERIFIED_STATIC | d.ts 逐字 |
| 表达式引擎 30 个函数签名 | VERIFIED_STATIC | d.ts 逐字，参数名保留原文 |
| 组件的实际渲染行为 | 未验证 | 未起 dev server，只看声明面 |
| 未在表中的组件 props | 见证据件 | 部分组件 props 类型不在可达文件内 |

## 铁律

- 传参照 §7.1 抄，别按组件名猜字段；`propsType` 与组件名不同名是常态（`MenuTree` → `MenuTreeProps`）。
- `biz-*` 组件几乎必带 `appId` / `appName` / `entityName`，这些值从运行时上下文取，不要硬编码。
- 弹窗类永远 `visible + onClose + onOk`，受控类永远 `value + onChange(value, full, info)`。
- 表达式函数的时间参数是**时间戳 number**，字符串只进 `*ToTime` / `stringToDate`。
- `_default` 是 default 导出的占位名，按组件名查不到时试它。
