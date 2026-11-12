# B2｜core/tools/ —— deploy_plan 4 步映射为 tool 声明

> 样板链 B 第 2 件（TASK-GOAL 交付物 B2）。把 `components/platform_operations/deployment.py`
> `build_deployment_plan()`（L115）的 4 步设计态写链，逐条固化为"tool 声明"（执行契约，非代码）。
> 口径与 B1（`core/facts/udc/entity/create.md` f5476b8b）一致：同一 step1 声明、同一写门事实、同一 audit 行号。
> 铁律：只描述执行契约、不实现代码（禁改 components/ core/ 运行代码）；凭据 0 入仓；
> 4 步全映射、不扩散到其他 op；引 ROADMAP 限 §一~§七。

## 4 步 tool 清单（deployment.py L142-178 实测 op 逻辑标签）

| # | op | 文件 | method/path | registry status（引 registry.py 实值，本轮实测） | A4 归并等级 | 写门 |
|---|---|---|---|---|---|---|
| 1 | `udc.entity.create` | `entity.create.md` | POST `/service/udc/entity` | `VERIFIED_STATIC_BYTECODE` | STATIC | DENIED/POLICY_DENIED |
| 2 | `udc.entity.attribute.create` | `entity.attribute.create.md` | POST `/service/udc/entity/attribute` | `UNKNOWN` | 未取证（不可归并实证层） | DENIED/POLICY_DENIED |
| 3 | `udc.page.create` | `page.create.md` | POST `/service/udc/page-info/base-info/create` | **`UNVERIFIED`/registry-gap（registry 无此 op-id，不编造）** | 链级 OBSERVED_LIVE（audit §二 建页 2 命中） | 写门机制（registry 未登记） |
| 4 | `udc.deploy.normal` | `deploy.normal.md` | POST `/service/udc/runtime/deploy-normal`（body 须包 `deployDto`） | `OBSERVED` | LIVE | DENIED/POLICY_DENIED |

## 关键纪律（B2 spec 锚点，务必遵守）
- **step3 `udc.page.create` = registry-gap**：`registry.py` `UdcOperationRegistry` **无该 op-id**
  （registry 仅 page_info/page_log/metadata 读面；页创建写契约未登记）。该 tool 的"registry status"
  字段填 **UNVERIFIED/registry-gap，不编造 registry 条目**；页创建契约本身引
  `docs/audit/udc-design-time-deploy-write-contracts.md` §二 标 **OBSERVED_LIVE**（test2 建页 2 命中
  `1871471844026226944`/`2146495017352265083`）。两事实分列，不合并。
- **registry status 一律引 registry.py 实值**（本轮 `implementer/map_a7.py` 逐条实测），不转述。
- **写门事实**：4 步全为写动作，agent 侧 readonly 纪律下不出写，宿主授权执行；
  `layer.py:22` `contract.write or method!='GET' or not effective` → `DENIED`+`POLICY_DENIED`（A1 §六）。
- **凭据 0 入仓**：各 tool 只描述 op/method/path/body schema/verify/写门，不引 token/凭据值。

## 与 B1 一致性
同一 step1 声明（`udc.entity.create` 的 body/verify/写门/LIVE 行）与 B1 §1-§8 完全同锚；
B2 补"tool 声明（执行契约）"视角，不重复 B1 事实体。

## 未直读/UNVERIFIED 登记（不臆造）
- step3 registry 未登记（registry-gap）、完整可拼前缀 UNVERIFIED（audit §三）；
- step4 生成物落 OSS、前端页是否随构建生成 → UNVERIFIED（audit §六）。
