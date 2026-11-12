# Tool 声明｜udc.entity.create（deploy_plan step1）

> B2 样板件（`core/tools/`）· deploy_plan 4 步映射为 tool 声明 之 1/4。
> 口径：与 B1（`core/facts/udc/entity/create.md` f5476b8b）同一 step1 声明、同一写门事实、同一 audit 行号。
> 只描述执行契约，不实现代码（禁改 components/ core/ 运行代码）；凭据 0 入仓；引 ROADMAP 限 §一~§七。

## 契约字段
| 字段 | 值 | 在盘依据 |
|---|---|---|
| op | `udc.entity.create` | `deployment.py:144`（step1，L142-151） |
| method | `POST` | 同上 |
| path | `/service/udc/entity` | 同上（宿主拼 `{gateway_base}{prefix}`，audit §七 铁律 040402） |
| body schema | `{appId, name, caption, stereotype:"bill", entityNature:"MAIN", features:"basic,approve,…", multiplicity:"ONE2MANY", category:"ENTITY", parentEntityId:"0", superior:"0", validate:true}` | `deployment.py` L144-150 原值 |
| verify 回读 | `GET /service/udc/entity/{id}` → publishState/tableName | `deployment.py` step1 `verify` |

## registry 状态 + 证据等级（A4 口径，引 registry.py 实值）
- **registry status = `VERIFIED_STATIC_BYTECODE`**（`registry.py` `UdcOperationRegistry` 实值，本轮脚本实测）。
- **A4 归并等级 = STATIC**（VSB→STATIC，A4 §二）。
- **写门事实**：`write=True` → `layer.py:22` `contract.write or method!='GET' or not effective` →
  `OperationStatus.DENIED` + `ErrorKind.POLICY_DENIED`（A1 §六 / A4 §二）；agent 不出写，宿主授权执行。

## LIVE 实证（非臆造）
- `POST /service/udc/entity` → `BOOT_0000`，实体 id `7670732978062038177`（YanshouDan/验收单，stereotype=bill）
  = **OBSERVED_LIVE**（`docs/audit/udc-design-time-deploy-write-contracts.md` §一 L13 逐字）。

> 本 tool 与 B1 §1-§8 完全同锚（同一 op、同一 body、同一写门、同一 LIVE 行）；B2 只补"tool 声明"视角，
> 不重复 B1 事实体。
