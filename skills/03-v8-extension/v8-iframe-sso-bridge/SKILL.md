---
name: v8-iframe-sso-bridge
description: Use when building iframe 跳板页 or 三方系统嵌入 V8 单点登录.
version: 1.0.0
---

# V8 iframe 跳板页单点（三方系统嵌入场景）

## 背景
三方系统把 V8 页面嵌进他们的 iframe，用户在三方门户点击完成单点。不是钉钉→V8 方向，而是三方父页面通过 postMessage 发 authCode。

## 交互协议（张平/钉钉侧提供，已定）
发：`{"type":"reqAuthCode","id":"唯一ID","channel":"seeyon","data":{"clientId":"dingtfp7grpdc9a2huti","corpId":"dingc6fe0934083fa30c4ac5d6980864d335"}}`
收：同 id、`code:200`、`data.authCode`。localStorage key 与生产父页面 origin 对方「晚一些给出」，跳板页留 CONFIG 占位不阻塞。

## 标品真实链路（源码证据，勿凭经验拼接）
- 移动插件单点入口地址由 cip-connector 生成（DingTalkApplicationProviderServiceImpl#getMobileUrlDto）：`{frontBaseRoute}/oauth/home?type=DING_TALK&corpId={corpId}&appId={appKey}&web={webIndexPage}`（type 是大写 DING_TALK，appId=钉钉 appKey，勿写成小写/漏 corpId）。
- 跳板页拿到 authCode 后追加 `&code={authCode}`；/oauth/home 有 code 直接换登录态，无 code 自行取免登码。
- 登录接口：`POST /ctp-user/auth/third`，body=CtpThirdLoginDto{thirdType:"DING_TALK", thirdAppId, thirdCode, clientType:"WEB"}；cookie 有效时返回 useCookies:true（可做会话探测）。
- 链路：/auth/third → dubbo 泛化 MobileSsoAppService#getMobilePluginSsoUserDto → DingTalkApplicationProviderServiceImpl#getMobileSsoUserDto → oapi.dingtalk.com/user/getuserinfo?access_token&code → userid → 用户映射 → 种 SY_ACCESS_TOKEN。
- m5 插件(m5-web)无独立免登接口，全部复用 ctp-user /auth/third。
- 失败时响应 code 前缀 `mobile-sso-err`；CONNECTOR_0083=配置空，0084=查钉钉用户失败。

## 已踩坑
- 首版误拼 `businessType=outsider&mobile=` 格式——那是 AuthController#thirdSsoBackend 给外部系统跳转用的，不是移动插件入口；被用户以真实 URL（10.0.0.1/oauth/home?appId=..&corpId=..&type=DING_TALK&web=..）纠正。参数名/大小写以 getMobileUrlDto 为准。
- /oauth/home 是 ctp-user 前端路由页，其 js 不在后端仓库；「页面是否消费 URL 上的 code 参数」需联调验证：直接开 /oauth/home?...&code=无效值 看 F12 是否发起 /auth/third。
- iframe 内 cookie 是第三方上下文，需 V8 配 sameSite=none + 全站 HTTPS，否则 SY_ACCESS_TOKEN 被浏览器丢弃。authCode 一次性，勿重放。
- localStorage 兜底通道只在写入方与跳板页同域时可读（跨域 iframe 各自隔离）；纯跨域场景 postMessage 是唯一可靠通道，lsKey 仅作为同域约定时的备用，勿当主链路。
- 钉钉容器嵌入的 iframe 地址就是普通 URL：官方首页地址规则只要求 http/https + 公网可达，query 参数（webUrl/clientId 等）原样透传给页面，可以带。嵌套值必须 encodeURIComponent（/ → %2F），否则 & 被当成跳板页自己的参数分隔符截断。钉钉容器要求被嵌页面 HTTPS——http 页面在部分客户端被静默拦掉（iframe 白屏），先查协议再查代码。
- parentOrigins 的作用必须保留：收包时校验 event.origin、发包时作为 postMessage targetOrigin——authCode 是能换登录态的凭证，不校验来源时任何能把跳板页嵌进自己 iframe 的页面都能伪造回包或窃取出站消息。生产必须收敛为对方真实域名，不得长期 ['*']。
- Windows MSYS 终端启动 node 脚本必须用原生盘符路径 `node "<PATH>"`；`node /d/work/...` 不做路径转换，node 按字面路径找文件报 MODULE_NOT_FOUND。

## 部署/配置
- 跳板页部署在 V8 同域 nginx（如 /sso-bridge/index.html），不能放三方域。
- 白名单在 Nacos 的 gateway 配置里放行 /sso-bridge/** 和 /oauth/home（用户明确白名单在 nacos gateway）。
- 跳板页 CONFIG：clientId/corpId 已内置、parentOrigins 测试期 ['*'] 上生产换真实域名、lsKey 现为 seeyon_sso_authcode（与本地模拟页约定一致，生产 key 待对方给出后替换）、oauthHomePath 仅 frontBaseRoute 非根才改；webUrl 通过 URL 参数 encodeURIComponent 传入，代码里不写死业务地址。
- 跳板页有 mode=sso（拼 /oauth/home，默认）与 mode=api（直调 /auth/third，备用对照）、debug=1 联调日志。
- 产物目录：<SEEYON_AGENT_ROOT>\docs\deliverables\sso-bridge\（index.html 跳板页、server.js 本地静态服务、parent-simulator.html 三方父页面模拟器、oauth-home-stub.html 单点页桩、public/ 为 server.js 的静态根，改完 index.html 要 cp 进 public/）

## 本地全链路演练（无真 V8 也能验协议）
1. `node "<SEEYON_AGENT_ROOT>/docs/deliverables/sso-bridge/server.js" 8090` 起静态服务（0.0.0.0，改 server.js 后必须重启进程才生效）。
2. 钉钉/微信里打开 parent-simulator.html 链接（`http://<本机IP>:8090/parent-simulator.html`）：它内嵌跳板页 iframe、自动监听 reqAuthCode 并回 authCode（支持延迟/指定码/postMessage/localStorage/双通道三种模式），带全量通信日志。
3. 跳板页拿到码后拼单点地址跳 `/oauth/home?...`；本地 server.js 把该路径接管到 oauth-home-stub.html，页面显示收到的 type/appId/corpId/web/code 五参数，type=DING_TALK 且 code 存在即显示「链路验证通过」。
4. 演练只能验证协议收发与地址拼接；换登录态那段（/auth/third 种 cookie）必须把 index.html 部署到 V8 同域才能测。

- 待办：增强登录页（ctp-user 过期拦截壳，/login 替换静默重登）尚未写，等跳板联调通过后做。方案：壳页先带原 cookie 直调 /auth/third 探测——返回 useCookies:true 即静默回跳原地址；在 iframe 内则重定向回 /sso-bridge 重走免登；全失败才露真登录表单。原地址从 sessionStorage 或 redirectUri 参数取。

## 环境资源
- 标品源码：<PATH>
- Artifactory：http://10.0.0.1/artifactory/libs-release/com/seeyon/（ctp-user-web/biz 5.3.334、m5-web 5.3.265；jar 可下载反编译 javap 验证，javap 在 <LOCAL_ROOT>\java\bin）
- 本地 Maven 仓库：<MAVEN_REPO>、D:\repo-seeyon
- 联调环境：http://10.0.0.1（V8 前端）；钉钉测试页 origin 传 * 仅限本地