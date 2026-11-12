# UDC 自定义页面（手写整页）实操

适用：设计器表达不了的整页交互（复杂表格、流式下载、定时轮询、自绘弹窗）。
不适用：设计器能配的表单/列表/审批 —— 那走配置型客开，不要手写 React。

## 1. 代码从哪来、放哪

每个 UDC 应用一个前端仓库，与后端仓库并列：

```
git clone <gitlab>/<组>/frontend/<appId>.git
<appId>_frontend/
├── pc/      PC 端扩展工程
│   ├── src/pages/<页面标识>/customPage.tsx   ← 页面入口，必须默认导出组件
│   ├── third_modules/                        ← 平台包之外的三方库
│   ├── webpack-overrides-custom.js           ← 调试环境地址 + alias
│   ├── .npmrc                                ← 内网 registry
│   ├── .nvmrc                                ← node 版本
│   └── package.json                          ← syf dev-udc-custom / build-udc-custom
└── mobile/  移动端，结构同 pc/
```

**命名规则（最容易写错的一条）**：`customPage.tsx` 是**固定文件名**，随页面标识变化的是**目录名**。
页面标识 `nwbysym` → `pc/src/pages/nwbysym/customPage.tsx`。
入口文件名不是页面标识，别写成 `nwbysym.tsx`。

一个页面目录的常规三件套：

```
customPage.tsx        页面组件（默认导出）
service.ts            请求层
index.module.less     样式（CSS Module）
```

## 2. 环境与依赖

- node/yarn 版本读 `pc/.nvmrc` 与 `package.json` 的 `packageManager`，不要用本机默认版本硬装。
- registry 读 `pc/.npmrc`（通常是内网地址）。装之前先探连通性：
  `curl -s -m 8 -o /dev/null -w "%{http_code}" <registry>/@seeyon%2fsyf`，200 才继续。
- `yarn install`；没有 yarn 时 `npm install --no-audit --no-fund --legacy-peer-deps` 也能装（peer 冲突常见，加 `--legacy-peer-deps`）。

## 3. 本地调试

`webpack-overrides-custom.js` 里有两个必须对的点：

```js
const hostName = "https://<测试环境域名>";   // 登录态与后端接口都从这里反代
```

devServer 会把 `/<appId>/custom-page*` 指向本地 3000，其余请求反代到 hostName。

```bash
cd pc && yarn start        # = syf dev-udc-custom
```

浏览器：

```
http://localhost:3000/login                                     ← 走真环境登录
http://localhost:3000/main/portal/<appId>/<页面标识>            ← 打开自定义页面
```

`main/portal` 固定，第二段是应用编码，第三段是页面标识（=设计器「查看页面属性」里的页面 URI）。
**白屏先查两件事**：`customPage.tsx` 有没有默认导出；页面标识目录名是否与 URI 一致。

起来没起来的判定（别只看进程还在）：

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/    # 301 → 跳登录，说明服务正常
netstat -ano | grep -E ":3000\s"                                   # LISTENING
tail -20 dev-server.log     # 要有 <页面标识>.js [emitted] 和 「compiled successfully」
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/main/portal/<appId>/<页面标识>   # 200
```

dev server 是 watch 模式，改完源码 `tail dev-server.log` 应出现一次 `compiled successfully in xxx ms`，
看到这条再让用户刷新，否则他在看旧代码。

本机没有 yarn 时按 `.npmrc` 的内网源装（版本对齐 `packageManager`）：

```bash
npm install -g yarn@<版本> --registry <registry>
```

## 4. 三方库

平台包之外的一律走 `third_modules`，不要往 `node_modules` 里直接装（UDC 对依赖有管控，多应用共享平台级包）：

```bash
cd pc && mkdir -p third_modules && cd third_modules
npm init -y && yarn add <lib>
cd .. && yarn syf build-multiple-bundless-module      # 打成 bundless 模块
```

再在 `webpack-overrides-custom.js` 加 alias 指向 `third_modules/libs/<lib>/<ver>/module.js`，
`tsconfig.json` 的 `paths` 加 `"@third_modules/*": ["third_modules/node_modules/*"]`。

能用平台包就别引三方库：`@seeyon/ui`（PC 组件）、`@seeyon/mui`（移动）、
`@seeyon/global`（`ajax` / `i18n` / `OpenWindow` / 事件总线 / 权限 / 租户）。

## 5. 请求约定

工程里既有页面的写法就是契约，照抄：

```ts
import { ajax } from '@seeyon/global';
const res = await ajax.post(`/<appId>/<业务前缀>/<动作>`, params);
if (get(res, 'status') === 0) return get(res, 'data.content');
```

- 路径**必须带应用编码**（`/<appId>/...`），否则平台路由不注册、请求被拦。
- **`ajax` 会自动补 `/service` 网关前缀，原生 `fetch` 不会。** 网关对外的真实路径是
  `/service/<appId>/...`；自己 `fetch` 时少写 `/service` 会被前置网关截走，返回 404 且
  `Content-Type: application/xml`、响应头带 `X-Oss-*` —— 看到这三个特征就直接判定「没到后端」，
  不要去查 Controller。用一个常量派生两套前缀：

  ```ts
export const BASE = `/<appId>/extend/<业务>`;
 export const SERVICE_BASE = `/service${BASE}`;   // 只给原生 fetch / <a href> 用
  ```

- 后端查询端点**同时接受 GET 与 POST**（`@RequestMapping(method = {GET, POST})`）。
  页面走 `ajax.post` 时若后端只声明 `@GetMapping`，Spring 匹配到路径但方法不允许 → **405**，
  报错里没有业务信息，很容易误判成权限或网关问题。写页面与写后端在同一次改动里对齐方法。
- `ajax` 的 `get`/`post` **签名同构**：`(url, data?, options?)` —— 第二个参数是数据（GET 时自动拼成
  query string），第三个才是 `AjaxOptions`。所以查询类直接 `ajax.get(url, params)` 就行；
  不要写成 `ajax.get(url, { params })`，那会把 `params` 当成一个同名字段发出去。
  签名以 `node_modules/@seeyon/global/dist/utils/ajax/index.d.ts` 为准，不要凭印象或旧文档。
- **测试期优先改前端适配，不要卡在后端发版上。** 后端只有 `@GetMapping` 而页面发 POST 时报 405，
  最快路径是把该查询改成 `ajax.get`（旧后端立刻能通），后端再补 `{GET, POST}` 双支持；
  两条路都留。因为「等一个含修复的镜像」把一次联调拖成一整轮发布，是本类任务最常见的浪费。
- **第三种「假故障」是未登录**：`curl` 直连接口会拿到
  `{"status":2,"code":"BOOT_1006","data":{"content":{"redirectUrl":"...esc-sso..."}}}` ——
  这是 SSO 网关在拦，不是接口坏。反过来说，浏览器里能拿到 405/404 就证明当时是登录态、请求真的
  到了后端。用 curl 复现接口问题前先带登录 cookie，否则会把「未登录」误读成「实现有问题」。

## 6. 流式下载（大文件导出）

`ajax` 拿不到二进制流，用原生 `fetch` + `blob` 触发下载：

```ts
const resp = await fetch(url, { method: 'GET', credentials: 'include' });
const blob = await resp.blob();
const a = document.createElement('a');
a.href = URL.createObjectURL(blob);
a.download = fileName;   // 从 Content-Disposition 里取，取不到再自己拼
a.click();
URL.revokeObjectURL(a.href);
```

后端配 `ResponseEntity<StreamingResponseBody>` + keyset 分页流式写，
前置 UTF-8 BOM、CSV 按 RFC4180 转义。**不要用标品导出**（一次性装内存，大数据量又慢又 OOM）。

## 7. 定时轮询

UDC 页面规则微流程是**同步执行**，没有轮询/长任务能力。需要进度刷新时页面自己 `setInterval`：

```ts
useEffect(() => {
  let alive = true;
  const timer = setInterval(async () => { if (alive) setData(await fetchProgress()); }, 3000);
  return () => { alive = false; clearInterval(timer); };   // 必须清，否则切页后还在打接口
}, [key]);
```

轮询失败静默（不弹 message），否则网络抖动会让页面一直闪错误提示。

## 8. 组件与样式

- **UI 一律用 `@seeyon/ui`，它本身就是 antd 的封装**，`Card` / `Statistic` / `Table` / `Progress` /
  `Tag` / `Modal` / `Space` / `Select` / `Input` / `Empty` / `Tooltip` / `Button` 全都有（400+ 组件）。
  手写原生 `input`/`select`/`button`/`table` 会和标品视觉脱节，用户会直接说「好丑」。
- 不确定某个组件的 props 时**去读它自己的类型声明，不要改用手写原生元素**：

  ```bash
  ls node_modules/@seeyon/ui/es                    # 组件清单
  sed -n '1,40p' node_modules/@seeyon/ui/es/index.d.ts   # 顶层具名导出（import { Button, Table } from '@seeyon/ui'）
  head -20 node_modules/@seeyon/ui/es/components/table/index.d.ts
  ```

  多数组件直接复用 antd 的 `Props` 类型（`import type { ProgressProps } from 'antd'`），
  按 antd 文档写即可，构建时 tsc 会兜住。
- 样式只写页面级布局（padding / 间距 / 省略号 / 分页条），**不要覆盖组件内部类名**，
  也不要用 `:global(.ant-xxx)` 去改组件皮肤 —— 会与标品主题互相污染。
- 危险操作（停止、归档）用 `Modal.confirm` 做二次确认，`okButtonProps` 给 `danger`，
  不要让用户一次点击就触发。
- 异步动作要有可见状态：按钮 `loading`、表格 `loading`、成功/失败 `message`、
  前置条件不满足时按钮 `disabled` 并给出说明。没有状态反馈的按钮等于坏按钮。

## 9. 构建发布

```bash
cd pc
BUILD_VERSION=<版本号>-local yarn build      # = syf build-udc-custom，产物 dist/
```

**`BUILD_VERSION` 必填**：`syf build-udc-custom` 在 `isProduction=true` 时读环境变量，缺了直接抛
`can not build without BUILD_VERSION argument`（见 `node_modules/@seeyon/syf/bin/syf-builder/build_udc.js`）。
这个变量平时由流水线注入，本地必须自己传，否则会误判成代码编译失败。

产物形如 `dist/custom-page-<页面标识>.<tag>.js` 并登记进 `dist/custom-page-manifest.json`；
交付前确认目标页面的 js 真的产出了，再报「页面已构建」。构建通过不等于线上生效 ——
前端产物随应用发布流程走，与后端同一个应用版本，未发布时浏览器仍在跑旧代码。

交付前至少跑通四件事：`yarn start` 能起、页面能渲染、按钮能调通接口、`yarn build` 成功。
