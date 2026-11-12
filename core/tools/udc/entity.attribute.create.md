# Tool 声明｜udc.entity.attribute.create（deploy_plan step2）

> B2 样板件（`core/tools/`）· deploy_plan 4 步映射 之 2/4。
> 口径同 B1/step1；只描述执行契约，不实现代码；凭据 0 入仓；引 ROADMAP 限 §一~§七。

## 契约字段
| 字段 | 值 | 在盘依据 |
|---|---|---|
| op | `udc.entity.attribute.create` | `deployment.py:153`（step2，L152-156） |
| method | `POST` | 同上 |
| path | `/service/udc/entity/attribute` | 同上 |
| body schema | `[{name, caption, dataType}]`（逐属性；dataType 缺省由 `infer_datatype` 按名保守推断并进 `unknowns`，不臆造） | `deployment.py` L153 `body=attr_bodies`（L20-40 推断逻辑） |
| verify 回读 | `GET /service/udc/entity/attribute/select-all-by-entity-id/{entityId}` | `deployment.py` step2 `verify` |

## registry 状态 + 证据等级（A4 口径，引 registry.py 实值）
- **registry status = `UNKNOWN`**（`registry.py` 实值，本轮脚本实测；契约已登记但证据未达 STATIC/LIVE）。
- **A4 归并等级 = 未取证（不可归并实证层）**（A4 §二：UNKNOWN→单列"待补证"，不升 VERIFIED）。
- **写门事实**：`write=True` → `layer.py:22` → `DENIED` + `POLICY_DENIED`；agent 不出写，宿主授权执行。
- **推断纪律**：dataType 缺省按字段名保守推断（date→DATE、amount→DECIMAL、status→ENUM…），未命中进
  `unknowns` 交宿主确认，**不静默臆造**（deployment.py L81 `infer_datatype` + note 原值）。

## LIVE 实证（非臆造）
- 建属性 ×4（acceptanceDate/acceptor/conclusion/amount）全部 SUCCESS = **OBSERVED_LIVE**
  （`docs/audit/udc-design-time-deploy-write-contracts.md` §一 L14 逐字）。
- **注意**：契约 registry 登记为 UNKNOWN（未取证），但全链 LIVE 已实测成功——两事实分列，
  不把"全链 LIVE 成功"直接升格该单契约 registry 状态（A4 §二 口径：契约 status 与链级证据分开登记）。

> 与 B1/step1 同锚同一写门事实（layer.py:22）；本 tool 补 attribute 维度 tool 声明，不重复 B1 事实体。
