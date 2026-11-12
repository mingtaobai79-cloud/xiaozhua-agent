# standard-product｜前端平台包用法（@seeyon/ui · @seeyon/global · @seeyon/udc-runtime-core，环境无关）

> 本格只讲**包内怎么用**：导出面、props 增量、请求约定、路由约定。
> 不涉及任何具体应用/工程/环境。
> 适用：任何 UDC 自定义页面 / 前端扩展代码。

分级：`VERIFIED_STATIC`（node_modules 内 d.ts 逐字，见 §8）。

## 1. Capability

三个前端平台包的**导出面与用法约定**：

| 包 | 定位 | 实测导出量 |
|---|---|---|
| `@seeyon/ui` | 基于 antd 的 UI 组件库 | 94 个导出（93 个组件目录） |
| `@seeyon/global` | 平台运行时能力（请求/路由/事件/租户/打印/i18n） | 79 个导出组（符号≈220） |
| `@seeyon/udc-runtime-core` | UDC 页面运行时（入参/组件取值/微流程/表达式） | 67 行导出面（符号≈173） |

不证：真实浏览器中的渲染与交互（未起 dev server）；组件视觉表现。

## 2. Version

- `@seeyon/ui` 3.0.0-beta.73、`@seeyon/global` 3.8.0-beta.409、`@seeyon/udc-runtime-core` 6.0.0-beta.8
- 依赖的 antd 为 4.x（`@seeyon/ui` 的 props 大量 `Omit<AdXxxProps, ...>` 形态）

## 3. Input

- `node_modules/@seeyon/<pkg>/package.json` 与其 `typings`/`types` 指向的顶层 d.ts
- 逐组件 props：`@seeyon/ui/es/components/<组件>/{"index","<组件>"}.d.ts`
- 抽取：`extract_extension_surface.py`（读 node_modules 的 `@seeyon/*` 并解析导出面）

## 4. Required

前端工程已 `yarn install`（或任意含该版本包的 node_modules）；无网络、无登录。

## 5. Execution

枚举 `@seeyon/*` → 取顶层 d.ts → 解析 `export {..} from` / `export *` / `export declare`；
组件 props 逐文件读。见 §7。

## 6. Side Effects

只读 node_modules。

## 7. Known Constraints

### 7.1 组件一律从 `@seeyon/ui` 导入，不从 `antd` 导入

`@seeyon/ui/es/index.d.ts` 是显式白名单（94 个 `export {..} from './components/...'`）。
虽然 antd 装在同级，但它只是**传递依赖**（由平台包带进来），不受 lockfile 保护；
直接从 `antd` 导入等于依赖一个未声明包。

`@seeyon/ui` 的导出是**平铺的具名导出**（`Button`/`Table`/`Select`/`Modal`/`Form`/`Tag`/…），
没有默认导出。

### 7.2 组件 props = antd props + 平台增量，增量字段照抄 d.ts

代表性三例（逐字取自各自 d.ts）：

```ts
// Button —— Omit 掉 antd 的 onClick，换成支持返回值的形态；增量：防重复点击 / 图标位置 / 纯图标
type ButtonProps = Omit<AdButtonProps, 'onClick'>
                 & Omit<GenSchemaProps.Button, 'iconPosition' | 'icon'>
                 & {
  onClick?: (e: any, other: any) => any;
  isDebounce?: boolean;  delay?: number;  debounceOption?: any;
  iconPosition?: 'left' | 'right' | 'top';
  extra?: ReactNode;  onlyIcon?: boolean;
  renderInDesign?: boolean;  useOnlyClass?: boolean;  needStopClick?: boolean;
  title?: string;  domTitle?: string;  icon?: any | GenSchemaProps.Button['icon'];
  [k: string]: any;
};

// Table —— 增量：斑马纹 / 边框 / 百分比列宽的容器裁剪
type TableProps<T> = AntdTableProps<T> & {
  stripe?: boolean;  preventDrag?: boolean;
  containerCropWidth?: number;   // 计算百分比列宽时父容器要减去的宽度
  showHBorder?: boolean;  showVBorder?: boolean;
} & ResizeEvent;
// 静态成员：Table.Summary / Column / ColumnGroup / SELECTION_ALL / SELECTION_INVERT

// Select —— 增量：非受控模式 / 面板关闭重置 key
interface SelectProps extends antdSelectProps {
  pageTime?: string;
  isUnControlMode?: boolean;          // true 时值由内部托管
  resetKeyOnDropdownClose?: boolean;  // 默认 true
}
// 静态成员：Select.Option / Select.OptGroup
```

另有若干直接复用 antd：`message` 即 `export { message } from 'antd'`；
`Modal` 在 antd Modal 上加了 `destroyAllModal()`。

⇒ 看 props 读 `es/components/<组件>/*.d.ts`，不要按 antd 文档猜平台增量字段。

### 7.3 请求层 `ajax`：只认「平台响应格式」，否则一律 reject

```ts
const ajax: (url: string, data: any, settings: AjaxOptions) => Promise<any>;
const get:    (url: string, data?: any, options?: AjaxOptions) => Promise<any>;
const post:   (url: string, data?: any, options?: AjaxOptions) => Promise<any>;
const put:    (url: string, data?: any, options?: AjaxOptions) => Promise<any>;
const upload: (url: string, data?: any, options?: AjaxOptions) => Promise<any>;
```

`AjaxOptions`（节选，逐字来自 d.ts）：

```ts
interface AjaxOptions extends RequestInit {
  site?: string;  method?: string;
  headers?: Record<string, any>;
  contentType?: string | boolean;  dataType?: string;
  processData?: boolean;  useAjax?: boolean;   // 走 XHR
  cors?: boolean;  withCredentials?: boolean;  timeout?: number;
  proxy?: any;
  onUploadProgress?: <T>(e: T) => any;
  onProgress?: <T1, T2>(loaded: T1, total: T2) => any;
  body?: any;
  allowNoToken?: boolean;  responseType?: XMLHttpRequestResponseType;
  urlNeedModify?: boolean;  byH5?: boolean;
  currentAppVersion?: string;  appName?: string;  pageEnterTime?: number;
  blockActiveSessions?: boolean;  openFrom?: string;
  queryFields?: QueryFields;                 // 部分字段响应
  retry?: false | RetryOptions;              // {maxRetries,initialDelay,maxDelay,backoffFactor}
  showError?: boolean;                       // 默认 true
}
interface RetryOptions {
  maxRetries?: number;  initialDelay?: number;
  maxDelay?: number;  backoffFactor?: number;
}
```

★ 关键行为约定：`ajax` 对响应做统一判定，**非平台格式直接 reject**（连 body 都拿不到）。
所以后端若返回自定义结构（如 `{success:true, content}`），页面会表现为「Network 200 但界面报失败」。

两条正确处置：

```
① 双格式 unwrap（过渡期兼容）
   status === 0        → data.content        （平台格式）
   success === true    → content             （自定义格式）
   否则 throw
② 改原生 fetch + credentials:'include'，自己解析
   注意：网关对外前缀是 /service，fetch 不走 ajax 时必须自己写全
```

### 7.4 页内跳转用 `useSyHistory`，不用 `window.location.href`

```ts
declare function useSyHistory(): (options: Omit<SyLinkModel, 'children'>) => void;
declare const SyLink: FC<SyLinkModel>;
export { SyLink, useSyHistory, pushStateFn as openTabLink };

interface SyLinkModel {
  url: string;  children: any;  params?: Record<string, any>;
  callback?: () => void;  isNewTab?: boolean;
  tabTitle?: string;   // @deprecated
  className?: string;  isReplace?: boolean;
  updatePathNameBeforeChange?: boolean;
}
interface pushStateModel {
  currentHistory: any;  currentRoute?: any;
  url: string;  isNewTab?: boolean;  tabTitle?: string;  // tabTitle @deprecated
  params?: Record<string, any>;  isReplace?: boolean;
  updatePathNameBeforeChange?: boolean;
  menuKey?: string;  forceNoNew?: boolean;
  tabControl?: boolean;  forceTabRefresh?: boolean;
  callback?: () => void;
}
```

⇒ 整页 `location.href` 会重建门户（侧边栏/页签/应用包），进详情要等一次白屏。
`useSyHistory` 在同一路由内 push，页签保留、面包屑正确、返回键可用。
兜底顺序：`useSyHistory` → `openTabLink` → `location.href`。

### 7.5 请求/路由/存储等常用能力都在 `@seeyon/global`

导出面（节选，逐字）：

```
请求     ajax(get/post/put/upload) · getServiceRequest(serviceName, useGraphql?)
         queryLoader · mutationLoader · createLoader · getRequestByAppName · GraphqlLoader
         apollo
路由     useSyHistory · openTabLink · SyLink · SyRouter · setSyRouterLifeCycle
事件     eventOn · eventOnOnce · eventEmit · eventEmitAsyncResult · eventEmitBroadcast
         eventOff · registerBeforeEmitHook · removeBeforeEmitHook · useEventOn · EventBus
存储     storage · Cookies · cache
用户/租户 getCurrentUser · setCurrentUser · getTenantInfo · setTenantInfo · getTenant
         getTenantCodeFromUrl · getTenantHeaderInfo
i18n     i18n · initI18n · InitI18n4App · InitI18n4Component
         getLocaleValueByI18n · isI18nData · createLocale · getLocale
文件     fileUpload · downloadFileIframe · getFileUrlByStorageKey · getFileIdByStorageKey
         getDownloadUrlByStorageKey · getDownloadAuthParams · getAttachmentUrl
枚举     getCtpEnumOptions · getCtpEnumOptionsByRelation · filterCtpEnumData
打印     print · addBeforePrintCallback · addAfterPrintCallback · saveUdcPagePrintData
权限     RolePermissionContext · RolePermissionProvider · useRolePermission
水印     getWatermarkConfig
弹层     showRemoteDrawer · showRemoteModal · showLoading · hideLoading · showError
```

`export *` 转发三处：`./infra/runtime`、`./utils/attachment-slot`、`./utils/extends-slots/index`。

### 7.6 `@seeyon/udc-runtime-core` 是「页面运行时」能力的入口

按用途分组（逐字来自其 index.d.ts）：

```
页面入参/变量  getUdcPageInfo · getAppNameAndPageName · parsePageInParams
               useSubscribePageInParams · getPageRuntimeVariable
               useSubscribePageVariables · setPageVariable · getPageUdcSetting
组件取值/赋值  getComponentValue · setComponentValue · getComponentInfo
               getComponentViewState · setComponentViewState · getComponentUdcSetting
               getFormExtraParamMap
数据源         getValue · setValue · getGridData · getGridRowData · insertRow · deleteRow
               setViewState · setSubViewState · setData · clearValue
               getComponentIdsByFullName · batchSetComponentValidationMsg
               submitAsyncFields · getMetadata
运行时上下文   getComponentId · getRowIds · getRowRuntimeContext · getComponentRuntimeContext
               getFieldRuntimeContext · getUdcPageSignature · getUdcAppSignature
               getComponentRuntimeContext · generateRuntimeContextByRecordId
               createRowRuntimeContexts · generateTargetRuntimeContexts
微流程         callMicroflow · callCommonMicroFlow · eventActionHandlerExtend
表达式         execGeneralizedExpression · getExpressionVariableValue
校验           isValid · clearCrossComponentValidation · setCrossComponentValidation
弹层/导航      getUdcPopoverHandler · PopoverManager · navigator · openSimpleModal
               handleRelatedPage · servers
其它           getEventManager · track · getUdcSdk · addUdcAsset/getUdcAsset
               addUdcSetting/getUdcSetting/getRawUdcSetting · prefetchUdcPage
```

它还 `export * from '@seeyon/udc-core'` 与 `export * from '@seeyon/biz-expression-engine'` ——
即这两个包的导出面也经由它可用。

⇒ 要在自定义页面里「读平台页面数据 / 触发微流程 / 取表达式值」，走这一层，不要自己拼 graphql。

### 7.7 自定义页面的路由形态（平台约定，与具体应用无关）

```
/main/portal/<应用编码>/<页面标识>
```

`main/portal` 是固定主应用段；后两段分别由应用的编码与该页面在设计器里的标识决定。
本地 dev 与线上同一形态（本地把 host 换成 dev server 地址即可）。

### 7.8 引入平台未预置的三方库：四步缺一不可

平台对前端三方依赖严格管控，只预置一批「平台级」库（多应用共享）。
要加别的库：

```
① 前端工程下建 third_modules/，在其中安装依赖
② 跑 syf 的 multi-bundless-module 打包（yarn syf build-multiple-bundless-module）
③ webpack 覆盖文件里加 alias
   config.resolve.alias['<pkg>'] = path.resolve(__dirname,
       'third_modules/libs/<pkg>/<ver>/module.js');
④ tsconfig.json 加类型提示
   "paths": { "@third_modules/*": ["third_modules/node_modules/*"] }
```

四步任一缺失都表现为**构建期解析不到**（不是运行期报错）。
⇒ 能用平台预置库就优先用预置库；确需新增时四步一起做，不要只 `yarn add`。

### 7.9 页面入口文件恒为 `customPage.tsx`

自定义页面的代码入口是**固定文件名**，不是任意组件：

```
src/pages/<页面标识>/customPage.tsx
```

- 文件名固定为 `customPage.tsx`；页面标识与设计器里的「页面 URI」一致。
- 同目录可放该页私有的 `service.ts` / `api.ts`；**多个页面共用的请求层放 `src/pages/common/`**，不要各抄一份。
- 平台按页面标识定位这个文件来渲染，改名或改层级即「页面白屏/找不到入口」。
- PC 与移动端各有独立工程（`pc/` 与 `mobile/`），同名页面需在两端各自实现。

## 8. Evidence

```
① 路径  docs/audit/artifacts/extension-surface-20261029/surface.json
        → sources.frontend.seeyon_packages[].top_level_dts（50 个包的导出面逐字）
        该文件的 frontend 段与包 d.ts 一一对应，不含工程/环境信息
② 复现  uv run --no-project python tools/core/platform/extract_extension_surface.py \
          --frontend <任一含 @seeyon/* 的工程 pc 目录> --emit <out.json>
③ 校验  本格每个导出符号都能在 out.json 的 top_level_dts.reexport_by_module 里逐字命中；
        §7.2 的每个增量 props 都能在 @seeyon/ui/es/components/<组件>/*.d.ts 里逐字命中；
        §7.3/§7.4 的签名与字段名来自 utils/ajax/index.d.ts、components/link/index.d.ts。
```

## 9. Verified

| 项 | 等级 |
|---|---|
| `@seeyon/ui` 94 导出 / 93 组件目录 | `VERIFIED_STATIC`（index.d.ts 逐行） |
| Button/Table/Select 增量 props | `VERIFIED_STATIC`（各自 d.ts 逐字） |
| `@seeyon/global` 79 导出组与分类 | `VERIFIED_STATIC`（index.d.ts 逐行） |
| `ajax` 签名与 `AjaxOptions` 字段 | `VERIFIED_STATIC`（d.ts 逐字） |
| `useSyHistory`/`openTabLink` 与 `tabTitle` 已废弃 | `VERIFIED_STATIC`（d.ts 逐字） |
| `udc-runtime-core` 六组导出面 | `VERIFIED_STATIC`（index.d.ts 逐行） |
| `ajax` 对非平台响应 reject 的行为 | `VERIFIED_STATIC`（d.ts 注释 + 调用方实现交叉核对；未在浏览器复现） |
| 浏览器渲染/交互 | **UNVERIFIED**（未起 dev server） |

## 铁律

- 组件一律从 `@seeyon/ui` 导入，不从 `antd`（传递依赖，不受 lockfile 保护）。
- 组件增量 props 读 `es/components/<组件>/*.d.ts`，不按 antd 文档猜。
- `ajax` 只认平台响应格式，非平台格式直接 reject → 表现为「200 但报失败」；要么双格式 unwrap，要么改原生 fetch 并自己补 `/service` 前缀。
- 页内跳转用 `useSyHistory`（兜底 `openTabLink` → `location.href`），不要直接 `location.href` 白屏重载。
- 读页面数据/触发微流程/取表达式值走 `@seeyon/udc-runtime-core`，不要自己拼 graphql。
- 自定义页面路由恒为 `/main/portal/<应用编码>/<页面标识>`，`main/portal` 段固定。
- 三个包都只有具名导出，没有默认导出。
