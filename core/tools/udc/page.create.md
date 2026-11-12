# Tool 声明｜udc.page.create（deploy_plan step3）

> B2 样板件（`core/tools/`）· deploy_plan 4 步映射 之 3/4。
> 口径同 B1/step1；只描述执行契约，不实现代码；凭据 0 入仓；引 ROADMAP 限 §一~§七。
> **本 tool 含 B2 关键 registry-gap 纪律**（见"registry 状态"节，务必遵守）。

## 契约字段
| 字段 | 值 | 在盘依据 |
|---|---|---|
| op | `udc.page.create` | `deployment.py:158`（step3，L157-171；deployment 逻辑标签，**非 registry op-id**） |
| method | `POST` | 同上 |
| path | `/service/udc/page-info/base-info/create` | 同上（宿主拼 `{gateway_base}{prefix}`） |
| body schema | `[{appId, caption:"…列表", pageType:"LIST", masterEntityIds:"<entity_id>", pageUrl, curTerminalType:"PC", pageItems:[{pageUrl,urlType:"PC",menuName,actionType:"NORMAL",orderNo:1}]}, {…DETAIL…}]`（页面对=LIST+DETAIL） | `deployment.py` L158-171 原值 |
| verify 回读 | `GET /service/udc/page-info/select-by-appId/{appId}` → 回读新页 caption+relationGroupId | `deployment.py` step3 `verify` |

## registry 状态 + 证据等级（A4 口径 —— **registry-gap 纪律**）
- **registry status = `UNVERIFIED / registry-gap`**（**不编造 registry 条目**）：
  实测 `registry.py` `UdcOperationRegistry` **无 `udc.page.create` op-id**（registry 仅
  `udc.page_info.*` / `udc.page_log.*` / `udc.metadata.*` 等**读面**，页创建**写契约未登记**；
  本轮 `map_a7.py` grep `udc.page.create` = 0 命中，确认 registry-gap）。
- **页创建契约本身 = OBSERVED_LIVE**（非臆造）：`docs/audit/udc-design-time-deploy-write-contracts.md` §二
  "页面创建契约"——test2 建页 2 命中（验收单列表 LIST id `1871471844026226944` / 验收单详情 DETAIL
  id `2146495017352265083`，均 `BOOT_0000`）；必填链实测错误码：缺 `pageType`→`BOOT_1001`、
  缺 `pageUrl`→`BOOT_1001`、缺 `curTerminalType`→`BOOT_1000`「页面终端信息为空」、
  `actionType∈{NORMAL,INSERT,UPDATE,DELETE}`（VIEW 不存在→`BOOT_3002`）。
- **两事实分列（A4 §二 口径）**：**registry 未登记 = 契约登记面 UNVERIFIED**；
  **活体页创建成功 = 链级证据 OBSERVED_LIVE**。二者不合并、不把链级 LIVE 升格为 registry 登记。

## 写门事实
- 页创建为写动作；agent 侧 readonly 纪律下不出写，宿主授权执行（`layer.py:22` 写门机制，A1 §六）。
  （本 op 因 registry 未登记，写门在 registry 契约面上无对应登记项，纪律仍依层机制成立。）

> 与 B1/step1 同锚同一写门机制；本 tool 补 page 维度声明，**registry status 如实标 registry-gap（UNVERIFIED），
> 不编造**；页创建契约引 audit §二 在盘 OBSERVED_LIVE 证据。
