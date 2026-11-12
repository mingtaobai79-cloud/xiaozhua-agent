# 部署态裁定 —— 平台构件版本 + 微流程分组路由（第十轮）

> **本文件回答第九轮留下的候选 (iv)**：`/udc/micro-flow-group/search-list` 是否能用
> 「部署版本 ≠ 5.3.517」解释。结论：**不能**（服务镜像级 + 部署态字节码级双重证伪）。
> 证据等级：**LIVE**（K8s API 只读 / 部署态 javap 逐 class）。仅平台面，无客户业务明细。

## 1. 平台构件部署 tag（LIVE，19 个构件）

来源：K8s API 只读 `GET /api/v1/namespaces/<ns>/pods` → `spec.containers[].image`（2026-10-15，第十轮）。
落在 `DEPLOYED-COMPONENT-TAGS.json`（客户应用 pod 名/镜像名含客户标识 ⇒ **只落平台构件，不落客户名**）。

| 构件 | 部署 tag | 构件 | 部署 tag |
| --- | --- | --- | --- |
| **udc** | **5.3.517** | ctp-user | 5.3.429 |
| bpm | 5.3.374 | ctp-affair | 5.3.315 |
| organization | 5.3.368 | ctp-message | 5.3.287 |
| portal | 5.3.392 | ctp-media | 5.3.261 |
| app-common | 5.3.274 | ctp-webapi-gateway | 5.3.266 |
| app-approval | 5.3.291 | cip-connector | 5.3.286 |
| cdp-data | 5.3.279 | cip-capability | 5.3.276 |
| cdp-schedule | 5.3.273 | cip-manager | 5.3.273 |
| m5 | 5.3.265 | cip-convert | 5.3.261 |
| cip-openapi-gateway | 5.3.265 | | |

**交叉校验（3/3 一致）**：`COMPLETION-METHOD-PROMPT.md` §环境 里声明的运行时版本
`bpm-facade-5.3.374` / `organization-facade-5.3.368` / `ctp-user-facade-5.3.429`
与 LIVE 镜像 tag **逐条相等** ⇒ 该文档的运行时版本口径可信，不是抄来的。

## 2. 裁定 (iv)：假设「部署 udc-web 版本 ≠ 5.3.517」——**证伪**

- **服务镜像级（LIVE）**：`udc` 容器镜像 tag = **5.3.517**，与被审计的本地 artifact `udc-web-5.3.517.jar` **同版本**；
- **谁在打印控制面 URL（LIVE）**：全 ns 只读日志通道里，**唯一**打印 `request url:/udc/**` 的平台 pod
  就是这个 `udc` 容器（tag 5.3.517，该类 URL **360** 条）⇒ 第九轮的「真实请求 URL 面」**全部出自 5.3.517 这个构件**；
- **部署态字节码级（LIVE）**：`udc-assemble-5.3.517-deployed/DEPLOYED-VERSION-NOTE.md` 记录，
  部署态胖包里 `udc-web-5.3.517.jar` sha256 前 8 = `0d6b0a65`、136930 bytes，且逐 class 与本地 5.3.517 一致。

⇒ 因此 `search-list` **不能**再用「跑的是别的版本」解释。第九轮把它记为 UNVERIFIED 的那一支已被排除。

## 3. 裁定 发现 B（部署态字节码，不是本地静态推断）

对象：部署态 `com.seeyon.udc.controller.MicroFlowGroupController`
（`MicroFlowReadPlane.javap.txt`，`javap -v -p`，JDK8，class major=52）。

| 事实 | 部署态字节码 |
| --- | --- |
| 类级映射 | `#89`/`#90` = `@RequestMapping("udc/micro-flow-group")` |
| `selectByAppId` 的方法注解 | `#30(#31=s#84)` = `@RestApiOperation("获取应用下所有分组信息")`；`#33(#31=[s#85])` = `@PostMapping({ "select-by-type" })`（PostMapping 值 = `#85` = **select-by-type**） |
| `selectByAppId` 的方法体 | `invokevirtual MicroFlowGroupAppService.**selectByType**(SingleRequest)` |
| `select-by-appid` 字面 | 该类常量池**不存在** |
| `search-list` 字面 | 该类常量池**不存在**（全文件亦 0 命中） |

**结论（比第九轮更精确，修正一处措辞）**：
1. `/udc/micro-flow-group/select-by-appid/{id}` **必然 404** —— 不是「方法没有实现」，
   而是**实现挂在另一个字面下**（方法名 `selectByAppId`、映射字面 `select-by-type`、方法体调 `selectByType`，
   三处不一致 = 平台源码复制粘贴瑕疵）。第九轮记的「同线程无 biz 行 ⇒ 无实现」结论方向正确，
   但**措辞需更正**：方法存在、映射字面不存在；
2. `/udc/micro-flow-group/search-list` **在本 Controller 的部署态字节码里不存在**，
   而 `search-list` 在同类其它 Controller（entity / attributeSet / data-transfer-object）中确实存在
   ⇒ 非命名习惯；结合 §2，剩余解释收窄为 **(a) `/udc` 前缀下其它构件提供**（与发现 A 同型）
   或 **(b) 死路径**（前端调用不存在的路由，与 `select-by-appid` 同型）。**二选一仍 UNVERIFIED**。

## 4. 限制（如实记）

1. **本轮未再观测到这两条路由**：全 ns 日志**不带 `tailLines`**（取全部保留日志，6 个 pod 有信号）后
   `micro-flow-group` 命中 **0** ⇒ 第九轮窗口已滚出保留区，**没有新的同线程证据**；
2. 镜像 tag 只证构件版本，不证 jar 内每个 class；载体级证据是本文件的部署态 javap（仅微流程读面类）；
3. `search-list` 的 (a)/(b) 区分需要：`pods/exec` 提权（取胖包全量 class）或前端 bundle 侧找到该调用的来源页面。
