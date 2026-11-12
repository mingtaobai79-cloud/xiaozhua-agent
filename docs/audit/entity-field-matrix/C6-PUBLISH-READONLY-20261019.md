# C-6 第一段｜发布链路只读取证（零写、零发布）

2026-10-19｜test2｜app 8704025620829192834｜**仅只读，零发布**

## 结论先行
发布入口在「应用」子页二级子菜单；该 app **走不到发布那一步** —— 沙箱已失败，卡点=实体 `XzhExp950795` 后端代码生成 NumberFormatException。P3 403 的 ctp_role_application 零行是**结果不是原因**。

## 1. 发布入口在哪（页面实测）
路径：设计器左侧「应用」→ `app-basic-info?appId=8704025620829192834` → 二级子菜单 8 项：
`页面测试`/`沙箱测试`/**`发布版本(version)`**/`依赖设置`/`应用依赖`/`组件依赖`/`团队设置`/`应用主题`

- 「发布版本」= **纯历史记录表**（发布时间/上次测试版本/发布状态/失败原因），**无操作按钮**。现有 1 条：`2026-10-15 15:32:38｜V1.0.7｜发布成功`。
- 「页面测试」= ant-steps 进度条 `页面发布开始 … 页面未开始发布`，**不是按钮**。
- 顶层仅「检查/页面调试(beta)/测试/更多」；「更多」只含「数据字典」。全页遍历 **无「发布」按钮**。

**⇒ 发布不是手动点按钮，而是沙箱测试成功后平台自动触发**（沙箱日志末尾打印「发布失败/成功」）。入口 = 顶部「测试」→ 沙箱流水线。

**实测 REST（抓包原文）**：端点 `POST /service/udc/graphql`。就绪查询 `udcDeploymentAppReadyStatePost`〔`{"appId":"8704025620829192834"}` 242B〕；元数据读取 `udcApplicationGetInputPath`/`udcApplicationDetailGetInputPath`/`udcApplicationAppVersionAppGuidPostInputPath`/`udcSandboxSelectAppGetInputPath`。

**本段未点「测试」，流水线未启动，故未捕获到 publish/release/deploy 写接口。此为切片范围限制，非「接口不存在」。**

**补记（2026-10-19 main 裁定）**：`udcRuntimeDeployNormalPost` 早已是 LIVE PASS，见 `docs/audit/settings/SET-PUB-1-publish-chain-live.md` L17（`deployId=-3191446022183863452`，DB 已核对应 `udc_deploy_record` 10-18 01:41:44 行）。本文档原句「未抓到任何 publish/release/deploy 写接口」是**错误否定结论**，成因=写本文档时未检索仓库既有审计记录。已由 main 记入 `DRIFT-REVIEW.md` 第二类自纠。

## 2. 当前发布态（DB）
`udc_test2.udc_application`：publish_state=**1**｜app_version/custom/source=1.0.0｜cop_version=5.3｜version=2｜guid=2275741415570096882｜source_type/feature_type=0/3｜update_time=2026-10-17 15:48:32。分布 `0:7, 1:14`。

`udc_test2.udc_app_version` 该 app **2 条**：
- `id=5995459285049141477`：version=41、**state=2 失败**、show_version=**1.0.15**、deploy_time=2026-10-19 11:00:44、fail_reason=`NumberFormatException: For input string: "...entity.XzhExp950795"`
- `id=-1268511255652519052`：version=1、**state=1 成功**、show_version=**1.0.7**、deploy_time=2026-10-15 15:32:38、fail_reason=`udc发布成功`

## 3. ctp_role_application 零行（已确认）
表在 **`ctp_user_test2`** 库（不在 udc_test2）。列：`id,tenant_id,create_time,update_time,version,role_id,app_id,status,sort_number`。`WHERE app_id='8704025620829192834'` → **0 行**；全表 199 行。

## 4. 风险评估（STATIC）
**写哪些表**：`udc_app_version` 增/改一行（已实测）→ `udc_application` publish_state/update_time → `ctp_role_application` 发布成功后写权限行（**P3 403 的钥匙**）。平台：Redis `{env}:Metadata:*` + OSS `udc@*.json`。

**可逆性**：有版本历史 V1.0.7→V1.0.15，但**未见回滚/下架按钮**。

**对他组**：环境级写。沙箱失败时强行发布只新增失败记录；共享账号 test-account-1 会争沙箱锁。

**★ 关键**：现在点发布**必然失败**，根因 `XzhExp950795`（门户「小爪实验实体950795V2」）生成后端代码时把类全名当 Long 解析。**该实体不通 → 沙箱必失败 → 发布永不触发 → ctp_role_application 永远零行 → P3 403 永远解不了。不是权限问题，是实体/编码问题。**

## 5. 建议（等 main 裁决）
1. 先排查 `XzhExp950795`：为何类全名被当 Long（疑似编码列/雪花 ID 异常）。
2. 沙箱通过后发布自动发生，无手动按钮。
3. 第二段前先确认沙箱「生成后端代码」通过。

## 6. 行为声明
零写、零发布、零页面改动。仅页面导航、子菜单切换、只读 DOM、MySQL SELECT、bundle STATIC。未点击测试/发布/确定/上架/保存。
