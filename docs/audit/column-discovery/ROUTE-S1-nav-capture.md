# ROUTE-S1｜栏目 nav 首屏抓包（域定位）

切片：main HANDOFF S1 — 域定位首屏抓包
执行：implementer（单切片，只观察不写）
时间：2026-10-17 15:0x–15:15 +08
环境：test2 `https://lowcode-test2.example.com`
应用：`8704025620829192834`（datamigration，本应用栏目为空 → 同时取有数据的应用做交叉验证）
原始抓包：`docs/audit/column-discovery/raw-nav-capture-20261017.json`（160,797B，24 条请求全量含 body/response）

---

## 一、结论先行（域定位）

**「栏目」在设计器里的真实对象名是 `Portlet`，不是 Column / Portal。**
这是本域此前被判 VACUUM 的根因：历史 DB 扫描用的关键词是 `column` / `portal`，而平台表族与 API 一律叫 `portlet`，0 命中不代表不存在。

| 层 | 真实身份 | 证据等级 |
|---|---|---|
| 前端导航 | `/app-design/page-manage/portlet`，`MENUS_PORTLET`，type=`portlet` | LIVE（本次打开）+ STATIC（bundle 常量） |
| 前端渲染组件 | `page-manage_main_portlet_tsx`（455B 壳）→ 动态加载栏目列表 | STATIC（remoteEntry chunk 映射） |
| 读接口 | GraphQL `udcPortletSelectByAppIdAppGet(path:{appId})` | LIVE（首屏真实调用，可复放） |
| 主表 | `udc_portlet`（157 行全库，本应用 0 行） | LIVE（DB 实测） |
| 分组表 | `udc_portlet_group`（0 行全库） | LIVE（DB 实测） |
| 栏目的页面实体 | `udc_page_info.page_type='PORTLET'` | LIVE（DB 实测，5/5 抽样命中） |

**明确排除**：`udc_page_layout`（外框）不是栏目落点。栏目行 `page_relation_id` 对 `udc_page_layout.id` 命中 0/131，对 `udc_page_info.relation_group_id` 命中 136/136。

---

## 二、完成标准逐项核对

### 1) 页面打开证据（DOM）✅

CDP 新开 target → `Page.navigate` 到
`https://lowcode-test2.example.com/main/child-frame/udc/app-design/page-manage/portlet?appId=8704025620829192834`

- `location.href` = 上述 URL，`document.title` = 「数据迁移」
- `iframe` = 空数组（非 iframe 嵌套，微前端 runtime 直接挂载）
- 左导航可见 9 项：`应用 | 实体 | 菜单 | 规则 | 流程 | BI | 栏目 | 设置 | 角色`（注意：bundle 静态清单是 15 项，运行时只渲染 9 项 —— 版本边界，见 §五）
- 右栏 tab 文本：`栏目列表` / `暂无结果` / `欢迎来到栏目空间` / `请创建栏目`
- 页面顶部有 `检查 | 页面调试(beta) | 测试 | 更多` 工具条

DOM 文本（`document.body.innerText` 节选）：
```
应用 | 实体 | 菜单 | 规则 | 流程 | BI | 栏目 | 设置 | 角色 | 数据迁移(1.0) | 栏目 | 检查 | 页面调试(beta) | 测试 | 更多 | 栏目列表 | 暂无结果 | 欢迎来到栏目空间 | 请创建栏目 | 检查 | 设计日志 | 微流程运行日志 | 生单规则运行日志 | 扣减规则运行日志
```

> 本应用栏目为 0 条，页面显示空态，符合 DB `SELECT COUNT(*) FROM udc_portlet WHERE app_id=8704025620829192834` = **0**。

### 2) 首屏请求清单（24 条，含可复放信息）✅

全部 24 条的 URL / method / postData / response 已落盘原始 JSON。栏目域直接相关的只有 1 条读接口，其余 23 条为设计器外壳通用请求（部署态、主题、i18n、沙箱、协作成员、日志字典等）。

**栏目列表主请求（唯一驱动「栏目」页面的数据请求）**

- URL：`POST https://lowcode-test2.example.com/service/udc/graphql?udcPortletSelectByAppIdAppGet`
- Headers：`Content-Type: application/json`（`credentials: include`，cookie 鉴权，token 走 `shared-credentials/test2-web-credential.json`，不落盘）
- Body（原样）：

```json
{"query":"query udcPortletSelectByAppIdAppGet(\n  $path: udcPortletSelectByAppIdAppGetInputPath\n) {\n  udcPortletSelectByAppIdAppGet(path: $path) {\n    code\n    data {\n      content {\n        appId\n        groupId\n        guid\n        id\n        name\n        orderNo\n        category\n        portletList{\n          appId\n          groupId\n          guid\n          id\n          name\n          orderNo\n          pageRelationId\n          publishState\n          terminalType\n          type\n          category\n          originalId\n        }\n        pageRelationId\n        publishState\n        terminalType\n        type\n        originalId\n      }\n    }\n    message\n    status\n  }\n}","variables":{"path":{"appId":"8704025620829192834"}}}
```

- Response（本应用）：`{"data":{"udcPortletSelectByAppIdAppGet":{"code":"BOOT_0000","data":{"content":[]},"message":"SUCCESS","status":0}}}` —— 空数组，与页面空态一致。

**同一 query 换有数据的应用（appId=3289082814923688017，znxmglpt 平台应用）只读复放，验证返回结构与语义：**

- `httpStatus=200`，`code=BOOT_0000`，`status=0`，`content.length=6`（6 个顶层节点 = 分组 + 未分组栏目混排）
- 顶层节点样例：`{"id":"4090526305626128654","name":"销售员门户","type":"GROUP","terminalType":"PC","category":"ADVANCED","publishState":"UNPUBLISH","pageRelationId":null,"portletList":[ ... ]}`
- 子节点样例：`{"id":"324380332261928630","name":"销售员户头报表","type":"PORTLET","groupId":"4090526305626128654","pageRelationId":"-4316793748850968742","terminalType":"ALL","publishState":"UNPUBLISH","category":"ADVANCED","originalId":"0"}`

**关键语义（LIVE 实测，非推测）**：该 query 返回的是**两层树** —— 外层是栏目分组（`type=GROUP`）或未分组栏目，内层 `portletList` 才是栏目本体（`type=PORTLET`）。`pageRelationId` 只有 `type=PORTLET` 节点才有值，`type=GROUP` 节点恒为 `null`。

**其余 23 条首屏请求（与本域无关，仅登记以证明「首屏已全捕获」）**

| 次数 | 请求 |
|---|---|
| 13x | `POST /service/udc/graphql`（graphqlLoader 批处理：应用部署态、`udcApplicationGet`、`udcApplicationAppFeatureAppGet`、`udcCollaborationAppGet`、`udcSandboxSelectAppGet`、`udcSandboxBuildInfoAppGet`、`udcDeploymentAppReadyStatePost`、`udcApplicationAppVersionAppGuidPost`、`udcOperationLogSearchInitDataAppGet`、`udcOperationLogSearch` 等） |
| 2x | `GET /service/app-common/i18n/resource` |
| 2x | `POST /service/app-common/graphql`（`appCommonThemeSelectDefaultGet`） |
| 2x | `GET /service/app-common/theme/style` |
| 1x | `GET /service/app-common/expression/system/values/date` |
| 1x | `POST /service/ctp-application/appcenter/search-app-edition` |
| 1x | `GET /service/udc/application/user-role` |
| 1x | `GET /service/udc/sandbox/delta-build-info/8704025620829192834` |
| 1x | `POST /service/udc/application/search/front-detection` |

**额外收获（顺带证明栏目在平台内部的正式命名）**：`udcOperationLogSearchInitDataAppGet` 返回的 `subModuleMap` 里明确登记了
`"栏目节点": "PORTLET"` 和 `"栏目分组": "PORTLET_GROUP"`，
且模块枚举另含 `"栏目页面": "PORTLET_PAGE"`、`"PC门户": "PC_PORTAL"`、`"移动门户": "MOBILE_PORTAL"`、`"PC门户空间": "PC_PORTAL_SPACE"`。
这是平台自己给出的操作日志域枚举，属于「栏目域对象清单」的**直接权威证据**（LIVE，非反编译推断）。

### 3) 对象身份初步结论 + 证据等级 ✅

| 候选 | 结论 | 证据 |
|---|---|---|
| `udc_page_layout`（外框） | ❌ **排除** | 栏目 `page_relation_id` 对 `page_layout.id` LEFT JOIN 命中 **0/131** |
| `udc_page_group`（页面分组） | ❌ **排除** | 栏目有独立分组表 `udc_portlet_group`，与页面分组不同族 |
| 门户 ctp 对象 | ⚠️ 部分相关但非同层 | 平台枚举里确实存在 `PC_PORTAL / PC_PORTAL_SPACE / MOBILE_PORTAL`，但它们是「门户承载空间」，栏目是被门户引用的内容单元；本次首屏未触达门户服务 |
| **`udc_portlet`（栏目本体）** | ✅ **命中** | 首屏 `udcPortletSelectByAppIdAppGet` 直接读它，字段一一对应 |

**字段级对照（REST 返回字段 ↔ DB 列，逐字对齐）**

| GraphQL 字段 | `udc_portlet` 列 | 类型 | 备注 |
|---|---|---|---|
| `id` | `id` | bigint(20) PK | |
| `appId` | `app_id` | bigint(20) NOT NULL | 唯一键组成 |
| `groupId` | `group_id` | bigint(20) NULL | 指向 `udc_portlet_group.id` |
| `guid` | `guid` | bigint(20) NOT NULL | |
| `name` | `name` | varchar(100) | 唯一键组成 `(app_id,name,type)` |
| `orderNo` | `order_no` | int(11) | |
| `pageRelationId` | `page_relation_id` | bigint(20) NULL | **关键外键，见下** |
| `terminalType` | `terminal_type` | smallint(6) | 枚举：0/1/2 |
| `type` | `type` | smallint(6) | 0=分组，1=栏目 |
| `category` | `category` | smallint(6) | 1 = ADVANCED（基础/高级） |
| `originalId` | `original_id` | bigint(20) | 复制来源 |
| `publishState` | `publish_state` | smallint(6) | 1 = 已发布 / 0 = 未发布 |
| **`udc_portlet` 独有、接口未返** | `template_type` | smallint(6) | 栏目模板类型（建栏目表单里的「模板」字段） |
| **`udc_portlet` 独有、接口未返** | `backup_code` / `owner_code` | varchar | 数据备份标识 / 所有者 |
| **DB 无、接口无** | — | — | 分组信息由 `udc_portlet_group` 提供，`portletList` 是应用层拼装 |

> 字段对照属**结构对齐**（同名字段 + DB 列注释一一吻合），不是契约声明。契约必须等下一片落表取证后再写，本片不写契约。

**`page_relation_id` 的真实指向（这是本片最容易被"经验"带偏的地方，已实测钉死）**

| 假设 | 验证 | 结果 |
|---|---|---|
| → `udc_page_info.id` | `LEFT JOIN udc_page_info ON id=page_relation_id` | **0/131 命中** ❌ |
| → `udc_page_layout.id` | `LEFT JOIN udc_page_layout ON id=page_relation_id` | **0/131 命中** ❌ |
| → `udc_page_schema.id` | `LEFT JOIN udc_page_schema ON id=page_relation_id` | **0/131 命中** ❌ |
| → `udc_page_info.relation_group_id` | `LEFT JOIN udc_page_info ON relation_group_id=page_relation_id` | **136/136 命中** ✅ |

`udc_page_info.relation_group_id` 全库 1568 行中 1498 个不同值（非唯一，一对多），因此**一个`relation_group_id` 可挂多条 page_info**（PC/移动等多端页面共享同一关联组）。抽样验证 `page_type` 恒为 `'PORTLET'`：

```
portlet_id=4962856294174186123  portlet_name=本部总营销考核排名  page_relation_id=-1545141838521587058
  → page_info_id=-9039204883171751078  caption=本部总营销考核排名  page_type=PORTLET
portlet_id=-8182365102651823306 portlet_name=平台项目库存      page_relation_id=-1935285280853217506
  → page_info_id=-8325243624542712067  caption=平台项目库存      page_type=PORTLET
```

**结论：栏目本体 = `udc_portlet`；栏目内容 = 挂在该行 `page_relation_id` 关联组下的 `udc_page_info(page_type='PORTLET')` 页面。**

---

## 三、完整可复放操作序列

```bash
# 1. 确认 Edge 9222 可用
curl -s http://127.0.0.1:9222/json/version

# 2. 抓包（脚本已在 scratch，逻辑：Target.createTarget → Network.enable → Page.navigate → 等 26s → 落 JSON）
node <HERMES_HOME>/cache/scratch/colcap.js <输出路径>

# 3. DB 只读校验（凭据由 conn.py 从 shared-credentials 读取，不打印）
uv run --no-project --with pymysql python \
  "<HERMES_HOME>/skills/seeyon/01-platform/xiaozhua-low-code-environment/scripts/conn.py" \
  db "SHOW TABLES LIKE '%portlet%'" --env=test2 --db=udc_test2
```

抓包脚本 `colcap.js` 只做了 `Network.enable` + `Page.navigate` + `Runtime.evaluate` 读 DOM，**无任何点击、无任何写操作**。

---

## 四、证据等级汇总

| 结论 | 等级 | 判据 |
|---|---|---|
| 栏目 nav 页面可打开、显示空态 | **LIVE** | CDP 实际导航 + DOM 文本 |
| 首屏请求 24 条全捕获 | **LIVE** | Network 域实测，含 response body |
| `udcPortletSelectByAppIdAppGet` 是栏目列表唯一读接口 | **LIVE** | 首屏实测 + 换应用复放返回 6 节点 |
| `udc_portlet` / `udc_portlet_group` 表存在及结构 | **LIVE** | `SHOW CREATE TABLE` + 行数 |
| `page_relation_id` → `udc_page_info.relation_group_id` | **LIVE** | 4 种 JOIN 假设逐一实测，仅此命中 136/136 |
| `udc_page_layout` 是栏目落点 | **LIVE（否证）** | 0/131 命中 |
| 栏目域对象枚举（PORTLET/PORTLET_GROUP/PORTLET_PAGE/PC_PORTAL…） | **LIVE** | 平台 `subModuleMap` 自身返回 |
| 前端组件 `page-manage_main_portlet_tsx` | **STATIC** | 既有 bundle 审计（`APP-DESIGN-NAV-INVENTORY.md`），本次未重新拉取 bundle |
| 写接口（create/update/delete/sort） | **UNVERIFIED** | 本片只观察，未触发 |

---

## 五、偏差与边界（必须交回 main 判断）

1. **静态清单 15 项 vs 运行时 9 项不符**。`APP-DESIGN-NAV-INVENTORY.md`（基于 udc 5.3.496 bundle）列 15 个导航项，本次运行时只渲染 9 项（应用/实体/菜单/规则/流程/BI/栏目/设置/角色）。`config/environments.yaml` 记 test2 镜像 5.3.496，本地契约件是 5.3.517。**这是版本边界问题，不属于本域，不扩展处理**，仅登记。

2. **本应用栏目为空（0 行）**，因此「新建栏目 → 落表」只能留到下一片做写操作（需 main 授权，且按任务约束写操作只允许 zzprobe 或本应用）。本片用平台应用 `3289082814923688017` 只读复放补足了返回结构证据，但**该应用是客户/平台应用，未做任何写操作**。

3. **`udc_portlet_group` 全库 0 行**，而 `udc_portlet` 有 157 行 —— 说明未分组栏目是常态，`groupId=null` 合法。分组写入从未发生，`udc_portlet_group` 写链完全未取证。

4. **`template_type` 列存在但接口未返回**。建栏目表单有「模板(空白页面/公开模板/自定义模板)」字段（见 R6 证据），推测落 `template_type`，但**本片不猜字段**，标注为待取证。

5. **纠正一处历史负证据**：`docs/audit/udc-nine-modules-status.md` 第 17 行「无 udc_column/udc_portal 表」表述为真但**结论误导** —— 真实表是 `udc_portlet`。建议 main 授权后在下一版状态文档更正。

---

## 六、下一片建议（不自行执行，交 main 定）

- **S2（落表取证）**：在 zzprobe 或本应用页面点击「新建栏目」，抓 `PortletController.create` / `createPortlet` 的真实 body，DB 回读 `udc_portlet` 新增行，验证 `page_relation_id` 是否同步生成一条 `page_type='PORTLET'` 的 `udc_page_info`。
- 前置：需要 main 明确写操作授权边界（本应用 `datamigration9000000000000000001` 是否允许写）。
