---
name: xiaozhua-low-code-environment
description: 连接并操作致远低代码环境的 Redis、MySQL、Kubernetes、Nacos 与跳板机；统一入口 + 客户配置隔离。
version: 0.3.0
author: operator-a, Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [xiaozhua, low-code, redis, mysql, kubernetes, nacos, uat, test2, config-isolation]
    related_skills: [xiaozhua-udc-runtime, xiaozhua-platform-operation]
---

本 Skill 是所有「致远低代码环境连接与运维操作」的入口：连服务器、看日志、查库、查缓存、查配置。UDC 运行态/生成机制/版本化 jar 审计用 `xiaozhua-udc-runtime`；平台 API 安全操作见 `xiaozhua-platform-operation`。

**设计原则：SKILL.md 不含任何客户/环境字面量。** 主机、端口、账号、认证方式、命名空间、库名、应用 ID 一律来自 `config/`，由 `scripts/` 解析后使用。换客户 = 换配置文件，不改 SKILL.md。

## When to Use

- 用户要求连接某致远低代码环境的 Redis / MySQL / Kubernetes / Nacos。
- 用户要求查看某环境的 Pod、日志、配置、资源状态。
- 用户要求通过 SSH 访问环境跳板机。
- 用户要求对指定环境执行明确的数据库、缓存或 Kubernetes 操作。

不要在环境未确认、凭据未就绪或目标资源不明确时执行写操作；不要把两个环境的 kubeconfig、命名空间或数据库连接混用。

## 配置层（唯一事实来源）

```text
config/environments.yaml          客户实例：非敏感连接参数 + auth 类型 + `_env:` 指针
config/environments.example.yaml  结构模板（可入 git，无客户数据）
.env                              仅凭据：*_PASSWORD / *_USERNAME / *_PEM / *_TOKEN
scripts/env.py                    解析 + 脱敏（唯一加载器）
scripts/conn.py                   统一操作入口
```

`<skill_dir>` = 本 Skill 目录。`config/environments.yaml` 与 `.env` 属客户实例，**不要提交到共享仓库**；新增环境复制 example 填值即可。

### 认证类型（每个资源显式声明）

| auth 值 | 含义 | 关键字段 |
|---|---|---|
| `key` | SSH 公钥 + 私钥 | `key_file`（私钥路径，可用 `<skill_dir>/xxx.pem`） |
| `password` | 账号 + 密码 | `username` / `username_env`、`password_env`（→ `.env`） |
| `kubeconfig` | kubeconfig 文件，不存凭据 | `kubeconfig`（本地路径，或 `jump:<远端路径>`） |
| `none` | 无鉴权 | — |
| `token` | 长期 API token | `token_env` |

敏感值一律用 `_env: XIAOZHUA_XXX` 指针（真实值在 `.env`）；非敏感连接参数（host/port/namespace/库名）直接写进 yaml。解析与脱敏由 `scripts/env.py` 统一处理。

## 统一操作入口：`scripts/conn.py`

所有连接操作都走这里，别在别处拼 ssh/kubectl/mysql 命令。

```bash
cd <skill_dir>
# 任意 python3；缺 pymysql/redis 依赖时脚本自动用 uv 临时注入

# 体检：ssh / kubernetes / redis / mysql / nacos 五项连通性 + 认证类型
python scripts/conn.py selftest [--env=test2] [--json]

# 跳板机执行任意命令（整串交给远端 shell，管道 / && / 重定向都生效）
python scripts/conn.py ssh "uname -a; ls /root/.kube/"

# Kubernetes（自动带该环境 --kubeconfig；namespace 默认由 context 决定）
python scripts/conn.py k8s get pods -o wide
python scripts/conn.py k8s get pods --ns=<ns>      # 仅明确要指定时才加

# Pod 诊断（describe + events + previous log + lastState/restartCount 一次拿到）
python scripts/conn.py pod <pod> [--ns=<ns>]

# 日志
python scripts/conn.py logs <pod> [--ns=<ns>] [--tail=N] [--grep=关键词] [--prev]

# 数据库（默认只读；写操作必须显式 --write）
python scripts/conn.py db "SELECT 1" --db=<schema>
python scripts/conn.py db "UPDATE ..." --db=<schema> --write

# Redis（无本机 redis-cli 依赖，走 python 客户端）
python scripts/conn.py redis ping
python scripts/conn.py redis scan "udc:*" 20
python scripts/conn.py redis get <key> | redis info

# Nacos 配置读取（按 key 自动脱敏）
python scripts/conn.py nacos <dataId> [--group=G] [--tenant=T]

# 打印解析后的配置（密码脱敏）
python scripts/conn.py show [--sub=mysql|redis|kubernetes|nacos|app|jump]
```

Python 侧复用：

```python
import sys; sys.path.insert(0, "<skill_dir>/scripts")
from env import load_env
cfg = load_env("test2")
cfg["mysql"]["host"]; cfg["kubernetes"]["kubeconfig"]
```

## 环境识别与执行路径

1. 从用户请求读取环境名；未提供而操作依赖环境时**必须询问**，不得猜测。
2. 默认环境解析顺序：`--env` 参数 → `XIAOZHUA_ENV` → `config/environments.yaml` 的 `default`。
3. Kubernetes 执行路径由配置决定：`kubeconfig: jump:<path>` = 经跳板机执行；本地路径 = 本机执行。本机没有 kubectl **不代表环境不可访问**——先看配置、再验证跳板机。
4. 某环境连接材料未配置时（host 为空），脚本明确报错并指出缺失字段，**不得用另一环境材料冒充**。但「Skill 未配置」≠「环境不可访问」：跳板机上常已按环境名备好 kubeconfig（`ls -la /root/.kube/`，常见 `config`/`configtest`/`configtest2`/`configuat` 并存），先列出来用目标环境那一份，再以它的实际 context 与 `get ns` 定命名空间；不要拿 test2 的 kubeconfig 查 uat 的 pod（同集群不同 ns，会静默返回空）。

## 应用 HTTP 路由约定

```text
{app.base_url}{app.service_prefix}/{applicationId}/{业务路径}
```

- `base_url` / `app_id` 由 `app.base_url_env`、`app.app_id_env` 从 `.env` 取；未设置时打印 hint，不静默回退。
- 拼接必须保留 `service_prefix`（默认 `/service`）；applicationId、微流程路径、方法 ID 按 class 注解原值保留，不凭业务名改写。
- 反查规则：`@RestApi` / `@RequestMapping("{applicationId}")` / `@PostMapping("<path>")` 原值拼接。
- 快速拼路由：`python scripts/conn.py route <appId> <业务路径>`。

### `/service/*` 返回 nginx 403 时的定性顺序

先分清「登录态过期」和「ingress 按来源 IP 拒绝」，否则会反复重建 token、白跑一小时：

| 观测 | 结论 |
|---|---|
| `/service/*` 全部 403（短 nginx 页）+ `/main/*`、`/{app}/remoteEntry.js` 200 | **静态面通、API 面被拒** → ingress 层拦截，不是 token 问题 |
| 换 UA / 加 Referer+Origin / 等冷却期 / 重启浏览器，仍全 403 | 排除 UA/CSRF/限流，指针指向来源 IP 白名单 |
| 带 `X-Forwarded-For: 127.0.0.1` 后同一请求 200 + 业务 envelope | 确认是 ingress 按 IP 判定 |

判定要点与纪律：

- **403 不能当路由命中证据**，但「同一请求加 XFF 后拿到业务 JSON」是判定 ingress 拦截的强证据；用一条已知能通的接口（如登录）做探针，不要拿业务写接口试。
- 页面上下文（CDP `Runtime.evaluate` 里的 `fetch`）**不能自发加 XFF**，浏览器侧照样 403 ⇒ 一旦 ingress 按 IP 拒，纯页面点击路径整体不可用；此时只能走脚本 HTTP + 手写头，页面点击仅用于「读内存/取证」，不要把「必须页面点击」的验收项挂在这里死循环。
- 这是环境侧 **misconfiguration（访问控制绕过），不是正常调用路径**：取证时如实登记「403 + 绕过后可通 + 绕法」，不要把带 XFF 的请求当成平台契约写进事实库，也不要因绕通就宣布页面通道可用。
- 若共享凭据文件里的 token 已被服务端拉黑（返回 `BOOT_1006 token黑名单`），**不要自己重新登录取 token**：本平台一次登录会让同一身份的旧 token 全部作废，自行签发会把其它浏览器 profile / worker / 脚本一起打死。正确做法是让用户在他的浏览器窗口通过 login 页面登录，再用**页面自己的会话**（`Runtime.evaluate` + `fetch(..., {credentials:'include'})`）取证。同一平台引入第二个账号前，先确认目标应用的设计态权限——平台级能通 ≠ 该 app 能进，无权限的账号顶不上，还会把原账号的 token 一起拉黑。详见 `chrome-profiles` skill 的 `references/session-login-and-token-safety.md`。


### 微前端子应用路由（BI / 流程 / 角色权限等外挂域）

设计器左导航的「BI、流程、操作权限、栏目、RPA」是 Module Federation 挂载的外部子应用（scope：`cdp-data`、`bpm`、`ctp-user`、`portal`、`cip-rpa`），不是 udc 自身代码。其后端 API **同样走网关 `{service_prefix}/{scope}/...`**，不是 `/cdp-data/*`、`/bpm/*`：

- ingress 通常只暴露一条 `{service_prefix}/(.*)` → gateway；没有 `/cdp-data/*`、`/bpm/*` 转发规则。
- `/cdp-data/*`、`/cdp-am/*`、`/cdp-df/*`、`/bpm/*` 直连会命中 OSS/CDN 静态桶：POST 返回 `<Error><Code>MethodNotAllowed`，GET 缺 key 返回 `NoSuchKey`，响应头带 `HostId: ...oss-...aliyuncs.com`。看到这种 XML 就是打到静态桶，不是后端。
- 内嵌 UDC 时 BI 真实基址是 `{service_prefix}/cdp-data/udc/*`。

判定路径是否真实存在：返回业务 JSON（哪怕 `status:2`）= 路由与处理器存在；`Whitelabel Error Page` = 未映射 404；OSS XML = 打到静态桶。

子应用 app 上下文（`appName`/`appId`）由宿主注入全局 `window.xcbpbi`，不是可手填字面量；直接深链 child-frame 页面时该全局常为空，子应用会渲染 `undefined.undefined` 并跳过数据请求。要拿真实请求必须经门户/设计器壳正常进入（抓法见 `chrome-profiles` skill）。

逐域取证细节见 `references/udc-micro-frontend-routes.md`。

### 设计器页面操作：REST 优先，CDP 兜底（用户明确偏好）

对设计器内容的任何修改（页面 schema、实体、菜单、微流程配置），**主路径是 REST 复现，页面点击只用于取证，CDP 只在 REST 无契约可用时兜底**。页面点击改的东西最终都要落成可复发的 REST 请求序列，这才是交付物。

**★ 契约到手 ≠ 可交付：必须再走一轮 CDP 真机操作验证（用户明确要求，别省）。** 光靠「CFR 反编译 DTO + REST 拼 JSON」会漏掉前端真实协议：前端**所有 UDC 接口都走 `POST /service/udc/graphql?<opName>`**（`udcApolloQuery`），例如实体属性真协议是 `udcAttributeGroupOperateBatchPost`（属性组数组、整表提交、字段全驼峰、`calculate` 是字符串枚举 `NORMAL|COMPUTE`）。
- **GraphQL 一律用批量 `graphqlLoader` 形态，别单 op 单发**：`mutation m($b: XInputBody){ d: op(body:$b) }` 会被服务端当成「body 缺失」（`BOOT_3000 Required request body is missing: …`），body 静默丢弃；包成 `mutation graphqlLoader ($params0: XInputBody){ data0: op(body: $params0){ code message status data{ content } } }` 才透传。批量形态还能一次带多 op（前端就是这么发的），也是抓包对照的基准。
- **数值字段传 JSON 数字**：`appId`/`entityId`/`attributeId`/`dataFlowId` 等 Long 字段传字符串会被校验器判为 null（`appId must not be null`），排查时先怀疑类型而不是缺字段。
- **REST 直觉拼的下划线键/数字枚举可能绕过服务端类型校验器**——写进去看着成功，真机一打开就报（如计算值「表达式返回值类型不匹配」，且字段语义标志与表达式互相矛盾）。所以每个域写完契约后，用 CDP 打开真实模块、真机点一次保存、抓真实载荷对照修正；**每一个新可用的接口 / 组件 / JSON 组装都要真机测一遍**（用户明确要求），不能只停在「契约拿到了」。**契约与真机载荷的差异就是交付前的必修项**。约定、op 目录与抓包工具见 `references/udc-frontend-graphql-ops.md`。

- **改一处 → 跑一次**：改完立刻复算检测看该条是否消失，再改下一处。批量改完统一验证，一旦结果变好便无法归因。
- 页面 schema 保存（`udcPageInfoUpdatePost`）、一致性检测（**先 `do/detection` 重算 + 轮询 `do/detection-state`，再读 `udcApplicationSearchDetectionPost`**；直接读读面得到的是上一轮快照，会误判成「检测器读发布镜像」）、构建入队/轮询（`udcRuntimeDeployNormalPost` / `udcRuntimeSearchDeployStatusDeployIdPost`）的完整 REST 协议、schema 结构规约（顶层即 PAGE、childById 不含 PAGE 自身）与检码字典，见 `references/udc-designer-save-detect-rest.md`。
- **检测读面 0 条 ≠ 0 阻断，必须先看 `do/detection-state` 终态**：`EXECUTING` 继续等；`SUCCESS` 时 0 条才是真通过；**`FAIL` 时读面必然返回空——那是「没有结果」不是「没有错误」**。把空读面当「某检码归零 / 检测通过」是本类任务最常见的假 PASS（等价于拿 HTTP 200 当 PASS）。要判「通道 FAIL 还是应用 FAIL」，用同一凭据、同一脚本再跑一个**已知正常应用**做对照：对照能到 SUCCESS 并读出 N 条 ⇒ 被测应用自身的元数据后处理异常，回头改字段是跑题；对照也 FAIL ⇒ 通道侧问题。有对照组才能把「改字段」和「修检测器」分开，别一上来在枚举/字段上找根因。
- 实体字段（必填/唯一/默认值/格式/枚举关联）与平台枚举(ctp_enum vs udc_enum)的 REST 写面、**平台内置域写端点的发现法**（`boot-starter-*` jar 不在 udc-web 契约里、`POST /service/udc/<域>` 即 create、错误链反推必填）、事件对象 / 参照配置 / 菜单默认页的 wizard 契约见 `references/udc-entity-ctpenum-and-constraints.md`。
- 微流程：节点/过滤条件结构、`checkSchema` 浅校验盲区（连缺 `structure` 的节点也过）、REST+GraphQL 写面、`MicroFlowDefinitionDto`/枚举、48 种节点 actionType 目录 + 10 类高频节点真机必填结构、真机建节点→checkSchema→**真机「检查」按钮（全应用一致性检测，比 checkSchema 严：逐节点 errors=0 仍可能报阻断）**→操作日志（`udcOperationLogSearch`）的完整闭环，见 `references/udc-microflow-authoring.md`。可复用探针：`scripts/udc_mf_probe.py`（create→checkSchema→oplog，确定性可反复跑）。
- **微流程落库前先备份原行，落库后立刻回读 `type`/`state`/`name` 对账。** `udcMicroflowUpdatePost` 的 body 要整行回传，任何从一个域横行的脚本（copy 自别处）都容易把 `type` 写死——标准流程被改成 `CUSTOM` 后编辑器仍能开、checkSchema 仍过，用户一看标题栏就会点到。用 `SELECT … FROM udc_microflow_info WHERE id=…` 回读，别信落库返回值。
- **微流程分类型、节点分域，建前先定对**：用户说的「标准节点流转」= `type=SERVICE(0)` 标准微流程（`service_interface='CustomMicroFlowAppService'`，**顶层 `output` 出参必填**且 `endNode.output` 同步），**不是** `type=CUSTOM(3)` 自定义微流程。**微流程节点与页面规则节点是两个几乎不相交的域**（仅 `BRANCH` 共用）：`ENTITY_SAVE`/`MESSAGE_INFO`/`MODAL`/`OPEN_PAGE`/`*_FRONT` 等属 `type=1` 前端域，**不能建进标准微流程**；标准域用 `CREATE_ENTITY`/`CHANGE_ENTITY`/`DELETE_ENTITY`/`RETRIEVE`。**页面规则（type=1）入口是 `/app-design/pagerules`（不是 `page-rule`/`rule/pagerule`，那些白屏），且必须绑页面（`sourceId`=页面 id，缺则报 `UDC_MICROFLOW_0015`）——页面规则依赖应用页面**。**用户明确要求：一条流程用 `runAfter` 融合所有节点，不要建一堆单节点流程**。`MicroFlowTypeEnum` 全值域、两域节点差集与判定口诀、标准专属节点结构、**微流程发布(state→RELEASE) ≠ 应用元数据更新**（04003 仍报，须再走应用构建）、检查/日志三层拉取、CDP 真机操作与实体属性真机保存协议、**页面规则域入口/绑页面/dataSchema 差异/28 种前端节点**，见 `references/udc-standard-microflow-realmachine.md`。
- **建微流程时 `jsonSchema` 一律留 NULL（本应用所有真实标准微流程都是 NULL）；节点结构必须逐字照抄真实 `type=0` 节点**——手写节点即使 `checkSchema` 过，真机打开仍会因缺子字段而画布崩（`TypeError ... reading 'map'`）。建完必须 CDP 真机打开验证渲染（含 `开始`/`结束`、无 `undefined.undefined`）；节点导致崩时用「已知正常流程 + 逐个追加你的节点」二分定位。另：微流程 `name` 禁下划线、`caption`/`name` 必须唯一、`type` 必须 `SERVICE(0)`、顶层 `output` 必填。详见 `references/udc-standard-microflow-realmachine.md` §11。
- **骨架必须取自本应用自己的真实流程，且样本池要排除「待修对象」与「自己建的测试流程」；抄完必须查两轮（§13，用户会点名问）。** 用别的应用流程当骨架会把对方的 appId/实体/DTO/上游节点 id 和中文业务描述一起带进来（渲染正常、`checkSchema` 过、不报错），每个节点挂的都是别人的数据；拿待修对象本身当样本 = 以脏洗脏，会把自己的污染当「权威值」固化。重建后跑两个独立审计并清零：(1) 节点 `desc/description/caption/title` 的业务描述残留；(2) 字符串值里的外部 DTO 全名/外部 appId/外部实体 id（含**扁平类名** `comseeyon…`，点式正则盖不住）。**页面规则（type=1）的清洗面比标准微流程宽——多出页面/控件、服务、生单规则、事件绑定四类**（`OPEN_PAGE` 的 `config` 是 JSON 字符串，里面有 `pageInfoId`/控件 id；`CALL_FRONT_FLOW`/`CALL_DATA_FLOW_FRONT`/`CALL_MICRO_FLOW` 分别绑页面规则/生单规则/微流程）。本应用权威取值：`app.caption` 来自 `udc_application.caption`、`pageInfo` 就是 `null`、`jsonSchema` 就是 `NULL`。`CALL_APP_SERVICE` 服务清单 op = `udcMicroflowSearchAppServiceByAppNamePost`（入参 `{appId, appName, needDynamicConnector:true}`，方法签名用 `udcMicroflowSearchMethodByNamePost`）——**每个 UDC 应用都自动有一批 `<实体名>AppService`**，别用 `content=null` 断「无服务」。
**★ 落库 update 时 `type`/`triggerType`/`state`/`sourceId`/`serviceInterface` 必须从 DB 原行回读，禁止硬编码**——写常量会把标准微流程（SERVICE/0）改成自定义（CUSTOM/3）、把草稿抬成正式；返回 `content:1` 和 `checkSchema errors=0` 都看不出，必须回读 DB 对账。真机「检查」= 全应用一致性检测（比 checkSchema 严），REST 链 `udcApplicationDoDetectionPost` → 轮询 `…DoDetectionStatePost` → `…SearchDetectionPost`。详见 §13。
- **表达式是横切能力**（分支条件、赋值方式、过滤条件、页面规则共用），取数走 `udcExpressionSystemVariableListGet`（系统变量全集，按 organization/date/env/plugin 分组）与 `udcExpressionSchemaPost`（`paramType` 值域 `ENTITY`/`ATTRIBUTE_SCOPE`/`CONFIG_PARAM`/`BASIC`；实体域需 `idsStr`，参数域返应用配置参数）；配置对象 `serverParams{appId, idsStr, paramType, extension(filterFieldIds 为字符串化 JSON), upsource}`，页面规则要 `unLoadPresetSchema:["APP_PARAM"]`。函数 op 名不是直觉名（可用集见文件）。完整契约与组装顺序见 `references/udc-expression-domain.md`。
- 「规则」域的另两条写链——扣减规则（`udc/deduction`）与生单规则（`udc/data-flow`，含映射规则的深嵌套契约与拼参顺序）见 `references/udc-deduction-and-dataflow-rules.md`。
- 「所选X已失效/已变更」有两类根因，先分类再改：**(a) 候选集为空**（数据源缺失）——事件投递候选池为空时报的就是「可投递的事件已失效」，根因是本应用 `udc_data_transfer_object` 里 `source IN (4,5)` 为 0（事件对象从未创建）；用 `udcDataTransferObjectCreateDtoPost`（`source=MICRO_FLOW_EVENT` + `attributes:[]`）建一个事件对象即可，**不是节点写错**。**(b) 候选集非空但匹配不上**——key/outputName 形态或类型不对。判定法：直接调面板加载 op 看 `data.content` 长度，非空才谈匹配。事件投递完整判定+建对象步骤见 `references/udc-standard-microflow-realmachine.md` §16。
- **验收口径分四层，只验红字=假验收**（用户反复点名后才补上）：① 结构红字（前端候选匹配）；② 必填完整——空值不产生红字文案，必须逐字段读面板实际值；③ 业务语义——同一字段被赋值多遍、裸常量/外部业务值当字段值，即使面板不报错也是不成立的数据；④ 外部残留清两层——标识符层（appId/DTO全名/字段id/扁平类名）与语义层（`desc/description/parentLabel` 里的外部业务描述）。宣布闭环前四层全过，对用户截图点名的每一处单独回验；被点名的问题修完前不要推进新任务。
- **微流程节点面板红字（「所选X已变更/已失效」）三层判定，应用级「检查」测不出来，必须 CDP 逐节点点开面板验**（用户会反复点名）：① 引用块自洽——`selectParam.key = outputName + id`、`outputName` 必须是真实上游节点 `output.name`，`description/id/javaType/name` 同源；② **节点形制不互串**（用户明确要求）——CREATE_VARIABLE 权威形制是 `paramType=ENTITY_OBJECT`+`structure{methodLegal}`（全库无 BASIC 型被 CHANGE_VARIABLE 引用的先例），CHANGE_VARIABLE 必须 `selectParam.nodeInfo{nodeId,actionType,entityCaption}` 回链上游 + `mappingType=value`；③ **类型链**——MAP_OPERATION 的 `selectMap` 上游 100% 是 `dataType=MAP`（来源仅 CREATE_MAP(53)/CALL_APP_SERVICE-MAP(19)，全库统计），**映射操作前必须先创建映射组**（用户原话）；手改 CALL_APP_SERVICE.output=MAP 会与 selectMethod.returnValue 矛盾继续红。复验工具：CDP 逐节点 JS 派发点击→读配置面板红字计数（scratch/panelcheck.js 模式），别只扫 body 全文（画布 5000px 宽，视口扫描会漏且误报）。**selectParam 两形态**：面板读取=扁平结构（无 `type:SelectParam` 外层）；`{type:SelectParam,selectParam:{…}}` wrapper 是保存/落库后的序列化形态——照真实库样本（wrapper 形态）手写 schema 会让面板报「请选择数据/所选已失效」，先去 wrapper 再验（2026-10-16 实测）。另：必填空值不产生红字文案（黄框），红字计数≠完整验收。
- CDP 用于读设计器内存态（`window.reduxStore.getState()`）、**真机操作验证**与前端真实请求取证；别在前端按钮（如「保存并提交」）上死磕——其 onClick 有闭包状态门，直接调会被静默拦截，此时改走 REST 保存。可复用工具：`scripts/cdp_realmachine.js`（`login` 注入 cookie / `capture` 导航并抓 `/service/` 请求+响应全量 / `eval` 执行脚本）、`scripts/extract_frontend_ops.py`（从 bundle chunk 提取 op 目录）。浏览器需先以 `--remote-debugging-port=9222` 启动。
- **设计器内容是独立 Module Federation 子应用**（远程包 `/udc/remoteEntry.js`，宿主是 `/main/*`）：宿主页的 `window.reduxStore.getState()` **不包含**编辑器自己的状态（`dataFlow`/`entityMetaData` 等切片常为空），别拿宿主 redux 判「规则没加载」；编辑器状态在其自身运行时里，页面上没有 iframe 可切。

## Redis

- 只读查看 key 用 `SCAN`，**不要用 `KEYS *`**；读业务 key 前先确认租户、应用和 key pattern。
- 禁止 `FLUSHDB` / `FLUSHALL`。
- 部分云 Redis 为 5.x，不支持 RESP3（`HELLO`）；`conn.py` 已固定 `protocol=2`。改为裸 redis-cli 时注意兼容。
- host/port/username/认证方式从配置读；不要把某个端点当所有应用的通用事实。
- 是否使用 ACL、database、TLS 依配置与运行实例为准。
- **UDC 运行态元数据在 Redis 只存「失效戳」**（key 形如 `{env}:Metadata:JSON:MD5:{appName}:udc@{EntityClass}@{TYPE}@{id}.json`，值是版本戳非正文）；枚举 code 缓存是 `CtpEnumCodeLocal::{appId}#{enumName}`。要正文查发布镜像/OSS 或设计态 MySQL。完整 key 模式 + 交互表（≈99 张 `udc_*`，设计态 vs `udc_rt_*` 运行态）+ 配置源(Nacos)与加密 assemble.jar 边界，见 `references/udc-runtime-store-keys.md`。

## MySQL / PolarDB

- 先确认应用绑定的库名，**不要根据应用 ID 或表名猜库**；库名候选见配置 `mysql.schemas`。
- 同一实例常按环境并列多套 schema（元数据域 / 用户域 / 组织域），跨域问题直接切库名、不换凭据。
- 只读优先 `information_schema`、`SHOW TABLES`、`DESCRIBE`、带明确条件的 `SELECT`。
- **数据库直连不等于业务成功证据**：写入后必须回读同一表、同一字段、同一时间窗口。
- 密码含特殊字符时不要拼进 JDBC URL 或命令参数；一律走 `_env` 指针对应的环境变量。
- 用 Python 直连取证：从 `scripts/env.py` 取已解析凭据，勿在脚本里写死 host/账号。独立探针脚本（要连「不在本 Skill 配置里」的库，如平台自己数据源定义指向的源库）先把 `.env` 载进 `os.environ` 再执行，否则 `os.environ['XIAOZHUA_DB_PASSWORD']` 直接 KeyError：

  ```bash
  python -c "import os;
  [os.environ.__setitem__(*l.strip().split('=',1)) for l in open(r'<skill_dir>/.env',encoding='utf-8') if '=' in l and not l.startswith('#')];
  exec(open('probe.py',encoding='utf-8').read())"
  ```

  探针只做 SELECT；凭据仍从数据源定义/Skill 配置读，不写进脚本。**探针脚本一律落盘到 scratch 目录再执行**（`write_file` 写 `.py` → `uv run --no-project --with pymysql python <path>`），不要用 `python - <<'PY'` 这类 heredoc：超过一分钟未获确认会被平台拦下（BLOCKED），且长脚本无法复用/逐步修正。查询也按「一次拉全列 + Python 里聚合」写，别用相关子查询逐表统计（跨上百张表会直接超时）。PolarDB/MySQL 5.7 **没有窗口函数**，`COUNT(*) OVER (PARTITION BY …)` 直接语法报错——分组统计一律拉回 Python 做。

  `information_schema.tables.TABLE_ROWS` 是估算值，需精确行数时对表 `COUNT(*)`；`CREATE_TIME` 可用来判实体/表的新旧（同名实体常并存多张历史表，靠它认哪张是后来的）。UDC 元数据侧的表名列是 `udc_entity.table_name`（**没有 `code` 列**），属性列名也不是 `column_name`——先 `SHOW COLUMNS` 取真实列名再写查询，别按常规命名猜。
- SQL 里 `LIKE '%xx%'` 通配符与 `%s` 占位符冲突（报 not enough arguments）：通配符写进 args 元组、占位符留在 SQL 里，不要混写。

角色与资源授权取证（通用查询形态，库名按环境配置替换）：

```sql
-- 元数据库：应用角色 + 资源授权
SELECT id, code, name, is_admin, type FROM udc_role WHERE app_id=<appId> AND is_deleted=0;
SELECT res.type, res.name, rr.role_id
FROM udc_role_resource rr
JOIN udc_resource res ON res.id = rr.resource_id AND res.app_id = <appId>
WHERE rr.role_id IN (...);
```

- 资源 `type`：0=菜单/入口，1=页面（列表/详情/审批/弹窗），2=按钮，5=布局外框；`data_type`（NORMAL/DETAIL/SEARCH_LIST/OTHER…）给出页面细分。
- **用户分配不在 `udc_role` 上**：运行态角色在用户域 `ctp_role`（其 `app_id` 存的是**应用 code 字符串**，不是数字 ID）。
- **成员归属实际落在 `ctp_entity_role`**：`entity_type='MEMBER'`、`entity_id=<用户 id>`、`role_code` = 角色 code。
- `ctp_user_role` / `ctp_user_data_permission` 对这些用户常是 0 行——按数字 id 查成员会**误判成「没分配」**，别把 0 行当真。数据权限另在 `ctp_user_data_permission`（也常空）。
- 应用 code → 中文名用 `ctp_application.app_name`；应用归属行在 `udc_application`（caption/name/save_as/source_app_id 可识别是否为 save_as 副本）。

只读取证助手：`xiaozhua-external-api-testing` skill 的 `scripts/db_readonly.py`（已改为读本 Skill 配置层）。解释器缺 pymysql 时用 `uv run --no-project --with pymysql python x.py`。

## Nacos

- 「无鉴权」**不等于**「公网可访问」，访问仍可能要求 VPN；先验证再断言。
- 配置查询必须同时明确 `tenant`（namespace）、`dataId`、`group` 三元组。
- 输出配置只显示非敏感键和值摘要；密码、token、accessKey、secretKey、私钥全部脱敏（`conn.py nacos` 已自动处理）。
- **修改后必须用同一三元组 GET 回读**，再检查应用启动/配置刷新日志；不能用 PUT/POST 返回成功、HTTP 200 或 Pod 重启代替配置生效验证。
- MSE 实例通常**没有可用的配置列表/搜索 API**：分页、`searchByDetailedInfo`、`/nacos/v2/*` 常报 400/404。因此只能拿运行实例证据确认真实三元组后精确读取，无法枚举配置；dataId 盲猜命中率低，不要拿「猜了几组都不中」当「配置不存在」的证据。
- **Open API 拿不到时，直接从运行 pod 的 Nacos 本地快照缓存读「实际生效的配置值」**——这是最可靠的运行实例证据，还顺带给出真实三元组：

  ```text
  /root/nacos/config/Config-fixed-<tenant>-<nacos_host>_nacos/snapshot-tenant/<namespace>/<group>/<dataId>
  ```

  在 pod 内 `grep -rl "<配置键>" /root/nacos/config` 先定位承载文件，再 `sed -n` 读上下文（能同时看到注释里的取值口径说明）。路径里的 `<tenant>`/`<namespace>`/`<group>`/`<dataId>` 就是运行时真实三元组，可直接回喂 `conn.py nacos`。
- namespace 探测用 `GET /nacos/v1/console/namespaces`；`configCount` 只反映该租户配置总数。
- 不要混淆 Nacos 控制台 URL 参数与 Open API 参数。

## Pod 诊断与日志

`conn.py pod` 一次拿到 describe、事件、previous 日志、lastState/restartCount。

- 重启根因必须以 `lastState.terminated.reason`、exit code、时间线、事件和 previous log **交叉确认**。
- `Readiness probe failed` 只能说明未就绪，**不能单独证明容器被它重启**。
- **`exitCode: 137` 不能确认内存超限**——它只是 `128+SIGKILL`，滚动发布删 pod、节点驱逐、内核 OOM killer 都长这样。`lastState.terminated.reason` 为 `OOMKilled` 才是内核判定，为 `Error` 即已排除 OOM。要定内存就三项一起查：`kubectl get events -A --field-selector reason=OOMKilling`、`kubectl get events -A | grep -iE 'evict|memorypressure'`、以及 `describe` 里的 request/limit。反向证据同样要取：启动参数带 `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=<dir>` 时去那个目录看有没有 hprof——没有就是**没发生过 JVM OOM**。容器启动命令常按发版重新生成（dump 路径带时间戳却不建目录），别把它当成 OOM 证据。另注意**滚动发布策略本身**就是高频重启源：`strategy.rollingUpdate` 的 `maxSurge`/`maxUnavailable` 非 0 + `imagePullPolicy: Always` + revision 很大 = 每次发版都换 pod，先排除它再谈资源。readiness 失败同样不能推 OOM。
- 取线上异常堆栈：先 `logs --grep="Exception: <关键词>"` 拿真实堆栈，不要靠读源码猜位置。
- 堆栈里的 `类名:行号` 是**编译期行号**，必须和部署镜像对应的提交比对，否则会把已修代码当未修。确认线上跑哪个提交：读 `deploy` 的 image tag，再与本地 `git log` 的版本提交时间对比；**版本号提交之后的提交默认不在该镜像里**，除非确认重新构建。
- 另一判据：把自己加的日志串在远端日志里计数——出现即说明该轮代码已上线，为 0 则未上线。
- 容器 FS 里没有前端静态资源：`udc`、`portal` pod 只有 `*-assemble.jar`，designer 前端 chunk 走 HTTP 取（见 `xiaozhua-udc-design-time-build`）；在 pod 里 find `*.js` 是空转。
- **运行期业务日志不在 stdout，而在容器文件系统里**，`kubectl logs` 常常只给启动期那几行；只有 `kubectl cp` 需要 tar。定位如下，别因为 `kubectl logs` 搜不到就断定「没报错」：

  ```text
  /var/log/webapps/<appName>/<appName>-info.log          当前活跃日志（容器停止时定格，之后不再写）
  /var/log/webapps/<appName>/<appName>-error.log         逐行失败原因原文
  /var/log/webapps/<appName>/<appName>-datainit.log
  /var/log/webapps/<appName>/<YYYY-MM-DD>/<appName>-info.log.<date>.<N>.zip   按大小轮转的压缩分片
  ```

  ```bash
  K="--kubeconfig=<env_kubeconfig> -n <ns>"; P=<当前 running 的 pod>
  # 先定位哪个分片含目标时段（以分片内首行时间为准，目录名只是日期）
  kubectl $K exec $P -- sh -c "for f in \$(ls /var/log/webapps/<app>/<date>/*.zip); do n=\$(unzip -p \$f 2>/dev/null | grep -cE '<关键词>'); echo \"\$n \$f\"; done" | sort -rn | head
  # 全部解包再拼时段，后续 grep 只对这份本地文件做，一次抓取多次复用
  kubectl $K exec $P -- sh -c "mkdir -p /tmp/z; rm -f /tmp/z/*; for f in \$(ls /var/log/webapps/<app>/<date>/*.zip); do unzip -o -q \$f -d /tmp/z 2>/dev/null; done; cat /tmp/z/* > /tmp/all.log; wc -l /tmp/all.log"
  ```

  容器内自带 `unzip`/`gunzip`/`zcat`。**滚动发布会带走旧 pod 的整个文件系统**，所以要立即抓；这类日志 `--previous` 也救不回来。日志目录按应用分，同一宿主上并存多个租户，只 grep 目标应用的子目录。**但同一个应用的 error.log 也是全应用共享的噪声池**——同一应用下并跑的其它功能（如同租户的数据迁移，成片 `BatchUpdateException`/`SQLSyntaxErrorException`/`UdcEntityCheckException`，以及重启期的批 `DUBBO Failed register`）会把 error.log 刷满，整段都可能属于那个功能而非本次问题。判定某行属于哪个功能：**按 logger 类名/包名（`<类>:<行号>|` 前缀）归类，不要按时间窗口就近归因**——先按类名过滤，再谈时间。目标功能的关键链（尤其前端微流程节点）可能根本不写应用日志，见 `xiaozhua-udc-page-debug`。`kubectl exec ... <cmd>` 里的裸 `(` `)` 会报 `syntax error near unexpected token`，口令包在 `sh -c "..."` 里时避免括号。

## Procedure

1. **识别目标环境。** 读取环境名；缺失且操作依赖环境时询问，不猜。完成标准：输出中明确记录环境名与命名空间来源。
2. **检查配置与凭据。** 跑 `conn.py selftest`；只输出变量名与脱敏状态，不输出值。完成标准：所有必需材料 ready，或明确列出阻塞项。
3. **执行连接验证。** Redis `ping`、MySQL `SELECT 1`、K8s `kubectl version --client` 后目标查询。完成标准：每项返回真实结果，失败保留原始错误摘要。
4. **执行用户指定操作。** 只在目标、环境、namespace、资源名、动作都明确时执行。完成标准：记录命令非敏感摘要、环境、退出码、关键结果。若命令被平台确认门拦下（BLOCKED），不要原样或换壳重试；把要做的事连命令摘要交用户说明，等明确授权。
5. **写操作二次确认。** 删除、覆盖、flush、truncate、update、insert、apply、patch、rollout restart、scale、exec 中的写操作，以及跳板机上的修改命令，执行前说明影响范围并获确认。完成标准：确认前不执行写命令。
6. **回读验证。** 对 DB / Redis / K8s 的状态改变，读同一目标确认结果；失败不得宣称成功。完成标准：有明确回读证据或明确报告未验证。

## Security Rules

- 不在 SKILL.md、脚本、日志、回答或命令回显中保存或复述密码、token、私钥、kubeconfig 内容。
- 不把凭据写进 `config/environments.yaml`；只用 `_env:` 指针 → `.env`。
- 不使用 `kubectl config view --raw`、`printenv`、`env`、`set` 输出敏感配置。
- 不把密码写入 URL、shell 历史、Git、临时文件或进程参数；优先环境变量。`conn.py` 输出统一走 `_scrub()` 替换已知凭据值。
- 连接失败区分 DNS / TCP / 认证 / 权限 / TLS / 命名空间错误，不要只报「服务器不可用」；不因连接成功就扩大权限。
- 内网连接可能需要 VPN；连接超时先查 VPN、DNS、端口、客户端，不靠反复重试绕过网络策略。

## Pitfalls

- **客户数据进了 SKILL.md 就是泄漏风险 + 换环境即失效。** 任何 host / IP / 账号 / 库名 / 命名空间 / 应用 ID 只能写进 `config/`。
- 环境未确认就执行，或把两套环境的 kubeconfig / 库连接混用。
- 本机没有 kubectl / redis-cli 不代表环境不可访问：前者看配置的跳板机路径，后者 `conn.py` 已内置 python 客户端。
- namespace 由 kubeconfig context 决定；不要凭经验或旧文档写 `-n`。要用时以实际 context / `get ns` 为准。
- **`namespace_hint` 可能不准，且错 context 会静默返回 `No resources found`，不是报错。** 拿不到目标 Pod 时先枚举实际 namespace，而不是断定「资源不存在」：

  ```bash
  # 看 context 自带的 ns，再列出真实 ns（hint 与它不一致时以这里为准）
  python scripts/conn.py ssh 'kubectl --kubeconfig=configtest2 config current-context; kubectl --kubeconfig=configtest2 get ns -o name'
  # 确认目标资源到底在哪个 ns，别只查一个
  python scripts/conn.py ssh 'for ns in $(kubectl --kubeconfig=configtest2 get ns -o name | sed "s|namespace/||"); do
    r=$(kubectl --kubeconfig=configtest2 -n $ns get pods -o name 2>/dev/null | grep <关键词>); [ -n "$r" ] && echo "== $ns" && echo "$r"; done'
  ```

  跨环境也会静默失败：同一集群里 test2 与 uat 是不同 namespace，用 test2 的材料查 uat 的 Pod 只会得到空结果。另注意应用 Pod 名是 `<applicationId>-<replicasetHash>-<suffix>`，**拿 applicationId 直接当 pod 名查会 NotFound**。
- **切环境只换 kubeconfig/namespace，别换服务器**：多环境常是**同一台跳板机、同一个集群、同一个 MySQL 实例、同一个 Nacos**。业务库按 `_test2` / `_uat` 后缀并列是常态，但**元数据库不一定遵守这个后缀对应**——同一实例上会并存多个 `udc*` schema，各自属于不同应用；`udc_uat` 完全可能是别的应用的库（特征：`udc_entity` 行数少、`app_id` 分布全是别的应用、`MAX(create_time)` 早已停更）。所以：
  - pod/日志侧换 `--kubeconfig=<uat>` + uat namespace；
  - **DB 侧不要拿「同名 `_uat`」当默认**。先用目标实体的表名/字段反查哪个 schema 真的有它：`SELECT TABLE_SCHEMA FROM columns WHERE TABLE_NAME='udc_entity'` 再逐个 `SELECT id,name,caption FROM <schema>.udc_entity WHERE table_name='<目标表>'`；命中不了就列各 `udc*` 的 `COUNT(*)` 与 `app_id` 分布，确认哪个是本应用的，或直接问用户要该环境的库名/应用 ID。
  - 拿不准时**不要用一个 schema 的空结果断言「该环境没有这个应用」**——那是选错库，不是环境缺数据。
- 跳板机上 `python scripts/conn.py ssh` 默认 180s 超时；逐 pod 扫日志（几十个 pod × 全量日志）会直接超时。改为**先把日志落到跳板机 `/tmp/*.log`**，后续 grep 都针对该文件，一次抓取多次复用；确实要长扫时显式提高 `timeout`。同理**别在容器里 `grep -r /`**（全盘递归同样直接超时），限定到具体目录（`/root/nacos`、`/app`、`/var/log/webapps/<app>`）并加深度/文件数限制。
- 任何重启原因必须有 lastState / 事件 / 日志证据，不能只看 Pod 当前状态。
- 数据库 / Redis 不是所有项目都用同一实例、库名、database 或认证模式——按配置核验，不要套用上一个项目。
- MySQL JDBC URL 只提供到实例级别；未确认库名时不要自行追加库名。
- 用户说「XX 管理员/XX 角色权限」时先用 LIKE 全租户搜角色名确认是否存在精确同名角色；找不到精确匹配就列出候选让用户定指认，别猜。
- Nacos 是无鉴权端点但可能要求 VPN；「无鉴权」≠「公网可访问」。
- `kubectl get pod` 是查询；`delete` / `apply` / `patch` / `exec` 必须走确认规则。
- 配置里某环境字段为空（如某环境未配置）时，脚本会明确报缺哪个字段——这是**预期行为**，不要用另一环境材料补齐。
- **别复用历史 Pod 名，也别假定编译产物目录还在**：应用 Pod 会被滚动替换（`<applicationId>-<rsHash>-<suffix>` 后缀变），失败有两种形态、都要改用「先取当前 running pod」：旧名报 `NotFound`（已消失）；pod 仍在但已终止报 `cannot exec into a container in a completed pod; current phase is Failed`（滚动发布留下的老副本或刚崩的副本，重试同一名字无用）。编译产物目录随重建消失——同一个 pod 里 `/A8C/base/autocode/<applicationId>` 可能整个不存在（`/A8C` 下只剩 `yarn`）。每次先 `get pods | grep <applicationId> | grep Running` 取当前 running pod，再 `ls -t /A8C/base/autocode/<applicationId>/ | head -1` 取最新时间戳目录。
- **手写扩展 Controller 在 ext jar 里，不在 metadata 快照里**：`jar tf /app/libs/BOOT-INF/lib/<appId>-ext-<ver>.jar | grep -E 'Controller|Listener|Handler|Api'` 先列候选，包名通常是 `extend/controller/`。**一次 base64 单行命令批量导出多个 class**（在 pod 内逐个 `jar xf` 会被确认门反复拦下，且外层 `sh -c` 嵌引号容易写错模式），取回本地 CFR 反编译整个目录；类名不含业务词时，用 Python 直接读 class 常量池搜业务中文关键词（如「草稿」「待办」）定位承载类，比逐个反编译快一个量级。**JVM 反编译一律带外 CFR，不走 rea MCP**——rea 无 JVM 字节码 provider（JEB provider 未运行时直接拒收 `.class`），rea 的 `analyze_web_bundle` 只用于前端 bundle（直连浏览器 CDP 端口）；沙箱（app-sandbox）的构建/部署机制、Redis 键模式与 REST/AppService 暴露面见 `references/udc-sandbox-build-deploy.md`。构建失败排查：**先打 `udcApplicationSearchDetectionPost` 检测面拿结构化 ERROR 清单（检码+path），再修**——检测在 doParallel 阶段并行执行，任一 ERROR 整体 FAIL 不进编译，构建日志只有「一致性检测未通过+行号」；协议与检码字典见 `references/udc-designer-save-detect-rest.md`。
- **发布是否真的成功，不看 HTTP 200 也不看资源表被刷**：唯一权威是 `udc_deploy_record.state`（1 成功 / 2 失败），运行态是否换版要靠 `remoteEntry.js` 与 `remoteEntry.<build_version>_*.js` 的 sha256 对齐来证。`/main/portal/{app}/{page}` 是 SPA 外壳，对不存在的 pageName 也返回同一 HTML 200，不能当可访问证据。失败发布会照样刷 `udc_resource`、推进 `udc_app_version.show_version`。完整判定矩阵、必查 SQL、产物身份取法与「应用自身缺陷 → BLOCKED 而非 FAIL」的定性口径见 `references/udc-publish-success-verification.md`。
- **改手写扩展代码前先找本地源码仓库**（形态 `<work>/<customer>/<appId>_<env>`），有源码就在源码上改，jar 只是它的构建产物；反编译只在无源码时兜底。外部系统调用的入口是**手写 Controller**（常在 `extend/controller/**` 的 `open/api/<动作>` 路径），平台内触发的通知才在事件监听/定时微流程——两条链互不覆盖，别把 Controller 的通知搬进微流程。改完 Java **必须全量 javac 编译验证**（`javac @argfile` 绕开 Windows 命令行长度；Lombok 仓**不能加 `-proc:none`**，否则 `log`/setter 全报「找不到符号」的假错；只编少数文件会因兄弟类缺 classpath 级联假错）。定位/编译/文案对齐/环境开关口径的完整规程见 `references/ext-source-build-verify.md`。
- **DTO 契约类不在本地 jar ≠ 不可得：去构件仓库取，别断言「本地不可得」。** udc-web 只挂自己的类，内层 DTO 常来自 `udc-common` 或域专用构件（如 `udc-dataflow`）；「本地 maven 无命中 + `pods/exec` 被确认门拦下」都不是「类不存在」的证据。按 GAV 从 Artifactory `libs-release` 直取构件（匿名可读），`unzip -l | grep <DtoName>` 确认类，再本地 CFR 反编译取 `private` 字段即得 JSON 契约（字段名=键名）。契约类齐了才能靠「POST 空 body → 错误链逐层补必填」拼出正确入参；枚举名错时错误链会直接回 `No enum constant <FQCN>.<VALUE>`，反编译该 Enum 取值域，别猜近义词。扣减/生单两条写链见 `references/udc-deduction-and-dataflow-rules.md`。
- 产物布局：`/A8C/base/autocode/<applicationId>/<时间戳>/{backend,frontend,extend,metadata}`；前端源码 `frontend/pc/src/{pages,microflows}/`，构建产物 `frontend/<appGuid>/*.js`，`backend/.../resources/metadata/json/` 是元数据快照。注意：ext 手工代码的**生成源**也以源码形式出现在该时间戳目录下，但那是构建时快照，可能与运行 pod 的 jar 版本不一致——引用行号/行为前先确认运行版本。
- **写 UDC 设计器嵌套 JSON（微流程 dataSchema、页面 schema、生单映射等）时，不要凭契约手写节点/结构——从库内或真机抓一个真实样本，只改 id/引用，其余字段逐字保留。** 契约只给了字段名，前端渲染器常还依赖契约里没暴露的子字段（如 `selectParam.customs/iconKey/parentLabel`），手写版 `checkSchema` 会过但真机一打开就崩（`TypeError ... reading 'map'`）。节点级崩溃用「已知正常流程 + 逐个追加你的节点」二分定位。验证通过后清理测试对象。
- 跳板机 SSH 偶发 `Connection timed out`（不是权限问题），重试即可。

### 「这是页面规则还是微流程判断的」——校验/报错文案落点反查

用户这样问时要给**精确落点**（哪个微流程、绑哪个页面、判定表达式原文），不要给笼统归因：

1. 在产物前端搜**用户看到的报错原文**（不是字段名）：`grep -rl "<报错文案>" frontend/pc/src`。命中 `frontend/pc/src/microflows/<id>.ts` 的就是承载该逻辑的微流程。
2. 由 `MFFRONTENDxxx` 这类 name 回 `udc_test2.udc_microflow_info` 取数字 `id` / `caption` / `trigger_type`（=2 前端触发）。
3. 反查绑定页面：`udc_page_schema.page_schema LIKE '%<微流程数字id>%'` → `page_id` → `udc_page_info.caption/page_url`。
4. 抠判定与文案：`data_schema` 里 `CONDITION` 节点的中文 `description` 就是判定表达式（形如 `页面规则.<页面名>.<实体>[单一记录].<字段>[数字].值 != 1`），`MESSAGE_INFO` 节点的 `showInfo.simple` 就是用户看到的原文。
5. **同一套判定常被复制进多个微流程**（不同入口各一份，文案可能只差「所有行」等字样）：改一处前按同一表达式/文案全量搜，列全命中再改。
6. 结论要分层表述：逻辑写在**微流程**里，而页面规则只是把该微流程挂成节点——「页面规则里的微流程节点」不是二选一。

## Verification

每次任务结束前检查：

- 环境明确，未混用连接材料；命名空间来自实际 context。
- 所有连接参数取自 `config/`；SKILL.md 与脚本中无客户 host / IP / 账号 / 库名 / 应用 ID 字面量。
- `conn.py selftest` 各项有真实返回，失败项已明确记录原因。
- 输出未包含密码、私钥、token、kubeconfig 内容。
- DB 改动后已回读同一表/字段/时间窗口；Nacos 改动后用同一三元组回读。
- 任何写操作都有用户确认与同目标回读验证。
- 结论区分：真实执行结果 / 静态推断 / 未验证。
