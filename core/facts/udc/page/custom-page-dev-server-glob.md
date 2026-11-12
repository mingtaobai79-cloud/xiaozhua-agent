# 自定义页面 dev server 只认启动时的目录快照

> 证据级：LIVE（2026-11-09，同一份源码在两个 dev server 上 404 / 200 对照）
> 一句话：`syf dev-udc-custom` 在**启动时一次性 glob 扫描** `src/pages/**/customPage.tsx`，
> 启动之后新建的页面目录永远不会被识别。不是构建问题，不是页面记录问题，重启即可。

## 一、故障表现

新建 `src/pages/<pageUrl>/customPage.tsx` 后：

```bash
curl http://localhost:3000/<appName>/custom-page-<pageUrl>.js
# HTTP 404
```

浏览器访问 `/main/portal/<appName>/<pageUrl>` 时，平台回落到**默认占位模板**：

```js
// custom-page-<pageUrl>.<时间戳>_<syf版本>_<appVer>.js
let t = () => p().createElement("h1", null, "hello world!")
```

页面能打开、无报错、但内容是 hello world —— 极易误判成「发布没生效」或
「平台读不到我的代码」。

## 二、根因

`node_modules/@seeyon/syf/bin/syf-builder/compiler/webpack/module_entry.js` 第 207 行：

```js
const customPageEntry = async options => {
  const customPages = glob.sync('src/pages/**/customPage.tsx', {...});
  for (const page of customPages) { ... }
}
```

扫描发生在 dev server 启动那一刻。`dev-udc-custom` 的注册在
`node_modules/@seeyon/syf/bin/index.js` 第 75 行，拿到端口后直接
`build_udc(cwd, {target:'customPage', development:true})` —— 整个生命周期只扫一次。

## 三、判据：真编译 vs fallback

**`HTTP 200` 不代表编译成功。** webpack dev server 会对未知路径返回 fallback，
两个不同页面的 URL 会返回**同一个** bundle。

正确判据 —— 比对**字节数**和**源码特征串**：

```bash
# 两个页面大小必须不同
curl -s "http://localhost:<port>/<appName>/custom-page-<pageA>.js" -o a.js
curl -s "http://localhost:<port>/<appName>/custom-page-<pageB>.js" -o b.js
wc -c a.js b.js

# 产物里必须能找到你写的业务文案
grep -c "你的页面标题" a.js     # > 0
grep -c "hello world" a.js      # == 0
```

实测对照（同一份源码，同一天）：

| dev server | custom-page-aeprobepage.js | 结论 |
|---|---|---|
| 3000（先启动，后建目录） | HTTP 404 | 目录不在扫描快照里 |
| 3001（同上） | HTTP 200 / 148,431 B | **fallback**，与 dymigration 同字节数 |
| 3002（建目录后启动） | HTTP 200 / 161,055 B | **真产物**，`接口验证自定义页` 命中 2 次 |

## 四、正确姿势

1. 建完 `src/pages/<pageUrl>/customPage.tsx`
2. **重启** `npm start`（不要指望热更新认出新目录）
3. 用 §三 的判据确认产物字节数与文案命中

页面目录结构（`pageUrl` 必须与平台页面记录一致）：

```
pc/src/pages/<pageUrl>/customPage.tsx      # 组件，default export
pc/src/pages/<pageUrl>/*.less              # 可选样式
```

产物命名两套并存，别混淆：

```
本地构建  npm run build        →  custom-page-<pageUrl>.<BUILD_VERSION>_<githash>_<appVer>.js
dev server                    →  custom-page-<pageUrl>.<部署时间戳>_<syf版本>_<appVer>.js
```

平台通过 `appDynamicImport(<appName>, "custom-page-<pageUrl>")` 动态加载，
`page-entry-<pageUrl>.<hash>.js` 里的 `React.lazy` 就指向它。

## 五、与「构建就生效」的关系

`npm run build` 产出的 dist 确实就是最终产物，**不存在额外的发布环节**。
但 dev 环境走的是 dev server 的代理（`webpack-overrides-custom.js` 把
`/<appName>/custom-page-*` 打到本地），所以在 dev 环境里，
「构建生效」的前提是 **dev server 已经认出这个页面目录**。

排查顺序固定为：目录在不在 → **dev server 重启没有** → 产物字节数 → 文案命中。
不要一上来就怀疑平台页面记录或部署链路。
