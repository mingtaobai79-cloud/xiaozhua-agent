# 运行期 URL 面（LIVE `pods/log`）—— 平台操作面的「实际被调用」轴

- **证据等级**：`LIVE`（K8s API 只读 `GET pods/log`；无 exec / attach / portforward）
- **工具**：`tools/core/platform/k8s_pod_log_surface.py`（只 GET）
- **数据件**：`RUNTIME-URL-SURFACE.json`（**去客户业务明细**：appId / 页面键 / 表名 / 记录 id 全部占位化；pod 名不落盘）
- **窗口**：namespace 内 **32** 个 running pod × `tailLines=60000` ⇒ **1407** 条 `request url:` 行 / **421** 条 distinct 原始 URL；
  另有 udc pod `tailLines=250000` 单窗（**213073** 行 / 1095 条 URL 行 / 78617 条 `AppServiceLogFilter` 行 / 133 个 distinct biz 方法）
- **入口**：`AppContextFilter:50` 逐条打印 `request url:<path>, userId, platform, browser`

## 1. 面的切分

| 面 | distinct | 说明 |
| --- | --- | --- |
| 控制面 `/udc/**` | **271** | 设计态/元数据/部署类 op（与 674 端点契约同域） |
| 应用运行期 `/{appId}/**` | **150** | 部署后应用的运行期 REST 面（`/udc-runtime/*`、微流程服务、表单级联、文件、graphql…） |

控制面 271 条原始 URL 归一化（去实参）后为 **18 个模板**。

## 2. 模板级对账（归一化后与 674 端点契约逐字比对）

- `EXACT_T`（模板命中契约字面）**14 / 18**
- `MISS_T`（契约**没有**该字面）**4 / 18**：

| 契约外模板 | 状态 |
| --- | --- |
| `/udc/graphql` | **非 REST**（GraphQL 入口），不计入 REST 面 |
| `/udc/metadata/app-service-by-name` | **有实现**（见发现 A）—— 提供者不在 udc-web |
| `/udc/micro-flow-group/search-list` | **UNVERIFIED**（同线程无 biz 记录；见发现 B） |
| `/udc/micro-flow-group/select-by-appid/{arg}` | **无实现**（同线程无 biz 记录；见发现 B） |

> 原始口径补充：对 **271 条 distinct 原始 URL** 的对账为 `EXACT 10 / PARAM 258 / MISS 3`。

## 3. 运行期家族（`/{appId}/**`，23 个模板）

```
/{appId}/udc-runtime/app-draft/{create,exist,select}
/{appId}/udc-runtime/app-log/create-batch
/{appId}/udc-runtime/evn-check/build-info/{key}
/{appId}/udc-runtime/meta-data/select-host-and-only-page-pages
/{appId}/udc-runtime/meta-data/refer-and-metadata
/{appId}/graphql              /{appId}/file/details
/{appId}/enum-item/search-by-enum-codes
/{appId}/ctp-parameter/values
/{appId}/{key}/microflow/{key}          /{appId}/{key}/microflow/getProgressByPlan
/{appId}/{key}/filter-plan/{key}/{key}/{id}
/{appId}/{key}/refer/{key}/{key}/{id}   (+ /select-by-ids)
/{appId}/{key}/refer-carry/organization/org-member/{key}/select-cascade-list-by-conditions
/{appId}/{key}/refer-carry/{key}/{key}/{key}/select-cascade-list-by-conditions
/{appId}/{key}/{key}/{key}/{key}/{get-cascade-default-value|select-cascade-by-conditions|operate-root-batch}
/{appId}/{key}/{key}   /{appId}/{key}/{key}/{key}
```

⇒ **应用运行期的路由骨架首次整体落盘**：设计态（`/udc/**`）与运行态（`/{appId}/**`）是两个**互不重叠的路由根**，
运行态把 `appId` 作为第一段路径段（与「活体端点全 `POST /udc-runtime/*`」的既有结论一致，此处补上**路径骨架**）。

## 4. 发现 A：`/udc` 前缀下存在 **udc-web 之外的 REST 提供者**（LIVE × 字节码）

**LIVE（同线程关联，硬证据）**：

```
http-nio-80-exec-23  AppContextFilter:50   request url:/udc/metadata/app-service-by-name
http-nio-80-exec-23  AppServiceLogFilter:70  method : MetadataQueryAppService#selectAppServiceMetadataByFullName
```

- 同一 HTTP 线程、相隔 ~150ms：URL 行 → biz 方法行 ⇒ 该路由**确有实现**并进入了业务方法（窗口内 18 次）。
- 计数对比（213073 行单窗）：`/udc/metadata/` = **20**，`/udc/design-metadata/` = **0**。

**字节码（`docs/audit/artifacts/metadata-5.3.358/MetadataController.class`）**：

- 父类 = `com/seeyon/boot/starter/web/BaseComponentController`（`/udc` 前缀的注入基类）；
- 类级 `@RestApi` 路径字面 = `metadata`，含方法路径字面 `app-service-by-name` / `app-service-by-names`；
- 业务接口 = `com.seeyon.ctp.metadata.api.MetadataQueryAppService`（**ctp 平台侧**，非 udc-web）。

**对照**：udc-web 契约里同名 op 走的是 **另一个**提供者 ——
`UdcDesignMetadataController.selectAppServiceMetadataByFullName → /udc/design-metadata/app-service-by-name`（在契约内）。

⇒ **结论**：674 端点契约是**单构件（udc-web）视图**；运行期 `/udc` 前缀下并行存在 ctp metadata 提供者，
且**真实前端调用的是契约外的那一个**（20 : 0）。凡「按契约全量理解平台操作面」都会漏掉这条并行面。
**未验证**：`/udc` 前缀的**注入点未到方法级**（`BaseComponentController` 内无 `addPathPrefix`/`getAppName` 字面，
机制在装配期处理），故前缀机制记为**推断**；LIVE 事实（该 URL 被服务 + 进入 ctp 业务方法）为**硬证据**。

## 5. 发现 B：两条「被调用但契约没有」的路由

**(1) `/udc/micro-flow-group/select-by-appid/{arg}` —— 语义正确、字面不存在（无实现）**

- 契约里同名前缀方法的字面是 **`/udc/micro-flow-group/select-by-type`**
  （`MicroFlowGroupController.selectByAppId`，**平台源码自身的复制粘贴瑕疵**）；
- LIVE 同线程后续**无任何** `AppServiceLogFilter` 行 ⇒ 该请求未进业务方法（404 / 静默无效果）；
- 与第八轮「形近字面段陷阱」**互补**：那里是「读起来像 ⇒ 404」，这里是「**语义正确但字面不存在** ⇒ 无实现」。
  另注：`/udc/micro-flow-group/select-by-type`（那个瑕疵字面）**LIVE 确实被调用**，两字面在同一窗口并存。

**(2) `/udc/micro-flow-group/search-list` —— UNVERIFIED**

- 契约内该前缀只有 7 条路由（create / update / batch-move / delete / delete-batch / {microFlowGroupId} / select-by-type），
  **无 `search-list`**；而 `search-list` 在同仓其它 Controller（entity / attributeSet / data-transfer-object）中**确实存在** ⇒ 不是命名习惯问题；
- 同线程无 biz 记录 ⇒ 状态 **UNVERIFIED**；三种可能：(a) 部署的 udc-web 版本 ≠ 5.3.517；(b) 另一构件提供；(c) 死路径。

## 6. 限制（如实标注）

1. `AppContextFilter` **只打印 URL，不含 HTTP 状态码** ⇒ 「被调用」≠「成功」；
2. 同线程 URL→biz 关联可判定「**有实现**」（发现 A）与「**无实现**」（发现 B），是本轮唯一可用的强/弱区分手段；
3. pod 名内嵌客户应用名/appId ⇒ 数据件只落**计数**，不落任何 pod 名（清洗门：非 `source` 子树 **6 位以上数字串 = 0**）；
4. 客户业务明细（appId / 页面键 / 表名 / 记录 id）一律占位化，**不入库**；
5. 本通道只给「被调用的面」，**不能**替代构件扫描给出的「注册面」。

## 7. 复现

```bash
uv run --no-project python tools/core/platform/k8s_pod_log_surface.py            # 只读 GET pods/log
uv run --no-project python -m pytest tests/udc/test_runtime_url_surface.py -q
```

## 8. 发现 B 收口：`search-list` 的三选一 → 裁定为「死路径 / 无实现」（第十七轮）

第九轮把 `/udc/micro-flow-group/search-list` 记为 **UNVERIFIED**，三选一：
(a) 部署版本 ≠ 5.3.517；(b) 另一构件提供；(c) 死路径。本节逐支裁定。

**(a) 部署版本 ≠ 5.3.517 —— 证伪（第十轮）**：LIVE 部署 tag 全 ns 唯一打印
`request url:/udc/**` 的平台容器就是 `udc = 5.3.517`，与被审计 artifact 同版本。

**(b) 另一构件提供 —— 证伪（本轴·静态，仓内可复算）**
- **提供者唯一性**：对 jar 仓库（`<MAVEN_REPO>` 全量 **1518** jar）逐 class 直读字节码，
  声明类级 mapping `udc/micro-flow-group` 的 class **只有 1 个**
  = `udc-web-5.3.517.jar!/com/seeyon/udc/controller/MicroFlowGroupController.class`。
  该前缀下不存在第二个提供者 ⇒ 不可能「别的构件在此前缀下补了 search-list」。
- **该 class 的注册面完整且无此叶子**：用 `tools/core/decompile/enumerate_class_http_mappings.py`
  **直读 .class 二进制常量池**（不经 javap、不经 CFR，免疫文本视图截断）枚举 7 个方法，
  叶子字面量为 `create / update / batch-move / delete / delete-batch / {microFlowGroupId} / select-by-type`，
  **无 `search-list`、无 `select-by-appid`**；对照叶子 `select-by-type` / `batch-move`
  在同一扫描里**确有命中** ⇒ 0 命中不是扫描器空转。
- 同一份字节码还给出「方法名 ≠ 路由字面量」的已证实例：方法 `selectByAppId` 的
  `@PostMapping` 字面量是 **`select-by-type`** ⇒ 按语义猜路径不可靠，判据只能是逐字 `full_path`。

**(c) 死路径 / 无实现 —— 同 traceId 行数判据（本轴·LIVE，对照分组标定）**
第九轮只用「同线程无 biz 记录」定性。本节把它升级为**对照分组**并标定阈值：
以「同 traceId 在全窗口出现的行数」为量，AppContextFilter 打印请求 URL 后，
若该 traceId 被后续过滤器行（`SecurityService` / `AppServiceLogFilter` /
`DubboContextFilter` / `MetadataService` …）复用，说明请求进了处理链 ⇒ 有实现。

| 组 | 规则 | 模板数 | 实测 |
|---|---|---|---|
| 对照组 | 契约在案或字节码可证存在 | **16** | 同 traceId 行数最小 **2**（如 `/udc/microflow/findById` 恒 3、`/udc/micro-flow-group/select-by-type` 4~5） |
| 试验组 | 孤行（同 traceId 行数 = 1） | **2** | `/udc/micro-flow-group/search-list`、`/udc/micro-flow-group/select-by-appid/{arg}` |

**分组干净**：全窗口 18 个模板中，行数 = 1 的**恰好只有这 2 条**，无第三种取值混入。
其中 `select-by-appid` **另有第十轮独立裁定**（字面量已证为 `select-by-type` ⇒ 映射不存在），
它落在试验组即对该判据做了**正向标定**。

**裁定**：`search-list` 与 `select-by-appid` 同组、同判据 ⇒ **(a)(b) 均证伪后，
`/udc/micro-flow-group/search-list` 是一台前置被拦下、无 handler 跟进的调用 =
仅存在于调用方的「死路径」，平台侧无实现**。第 5 节把它留在 UNVERIFIED 的理由从此消失。

**（附）一次未完成的 LIVE 直证尝试，如实登记**：本意用「GET 打到只用 `@PostMapping`
映射的路径 ⇒ 405(路径存在) vs 404(未映射)」做直接判定（GET 永不匹配 `@PostMapping`，
故任何情况下都不会执行业务方法）。实测网关对该类未带应用前缀的路径一律由 OSS 静态返回
`404 NoSuchKey`；带上 `gateway_prefix` 后返回应用服务层 `server_404`（对照组
`/udc/microflow/search` 同样如此）。**即该通道无法给出路由级 404/405 区分**，
故本条**未取到**独立直证，不作证据；结论只建立在上面两轴之上。
凭据侧另记：`ctp-user-login.json` 的登录端点本次返回 `USER_0055`（用户名/密码认证失败 1 次，
失败 99 次后需验证码），**已停止重试**，未做任何后续尝试。

