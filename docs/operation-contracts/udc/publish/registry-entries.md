# registry-entries — publish 域只读契约建议条目（供 UDC-MERGE 任务照抄）

不实际改 `registry.py`（冻结文件，本任务只读复核）。

## 结论：**0 条新增建议**（非真空域，但候选已被既有条目覆盖）

publish 域在本 jar（`udc-starter-runtime-5.3.517.jar`）内只有 **1 条只读候选**
（`UdcBaseAppInfoController.getDeployInfo`，见 `udc-publish-readonly-contracts.md` C1），
而该候选在 `registry.py` 中**已被登记两次**：
- `udc.application.deploy_info`（registry.py **L90**，application 域侧登记）
- `udc.appinfo.get_deploy_info`（registry.py **L110**，entity/appinfo 域侧登记）

两者与 C1 **同 class（class_sha256 `deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95`）、
同 method（`getDeployInfo`）、同 HTTP method（`GET`）、同 artifact/版本（udc-starter-runtime-5.3.517.jar, 5.3.517）**
→ 本域**不新增 key**（照抄 menu 域 P1/P2 先例的"已存在 → 不新增，只留域内证据映射"处置）。
**WRITE-EXCLUDED 的 W1（`/update-deploy-state`，POST 写）不得入 registry**（只读契约口径）。

> ⚠ 盘面漂移警示: 上表基于本轮实测 registry.py（`grep -c "UdcOperationContract(" = 49` 条，
> 与 5.3.517/5.3.260 合批后基线一致）。registry.py 属主控/并行会话的可写面、盘面会随提交漂移 →
> **MERGE 落库前必须对当时 registry.py 重新实测 key 唯一性**
> （`grep -n 'udc.application.deploy_info\|udc.appinfo.get_deploy_info' components/platform_operations/registry.py`），
> 勿以本文件时点断言为准。

## C1 ↔ registry.py L90 / L110 字段对账表（UdcOperationContract 10 字段）

| # | 字段 | L90 `udc.application.deploy_info` | L110 `udc.appinfo.get_deploy_info` | C1（本域候选，建议不新增） | 对账判定 |
|---|---|---|---|---|---|
| 1 | operation_id | `udc.application.deploy_info` | `udc.appinfo.get_deploy_info` | （域定位名 `udc.publish.deploy_info`，**不落地**） | 已有两条等价 key → **不新增第三条**（避免同实体三 ID） |
| 2 | method | `GET` | `GET` | `GET` | 同 |
| 3 | path | `{currentAppName}/app-info/deploy-info`（子类基路径 + 方法级，取 Normal 变体） | `deploy-info`（仅方法级原值，不拼前缀） | 方法级原值 `deploy-info`（**禁拼网关前缀**） | 逐字层面 C1 = L110；L90 = L110 + Normal 子类基路径（装配层差异，OBSERVATION） |
| 4 | request_type | `String currentAppName(PathVariable)` | `java.lang.String` | `String currentAppName(@PathVariable)` | 三者同参；表述详略不同 → **建议取 L90/最精确写法** |
| 5 | response_type | `SingleResponse<String>` | `com.seeyon.boot.transport.SingleResponse<java.lang.String>` | `com.seeyon.boot.transport.SingleResponse<java.lang.String>` | 同类型（简写 vs 全限定） |
| 6 | status | `VERIFIED_STATIC_BYTECODE` | `VERIFIED_STATIC_BYTECODE` | `VERIFIED_STATIC_BYTECODE` | 同（且本域独立复算 jar/class sha256 一致） |
| 7 | write | `False` | `False` | `False` | 同 |
| 8 | evidence | `appbasic_deploy_evidence`（javap=`docs/audit/artifacts/udc-app-basic/…UdcBaseAppInfoController.javap.txt`） | `ent_appinfo_evidence`（javap=`docs/audit/artifacts/udc-entity-5.3.517/…UdcBaseAppInfoController.javap.txt`） | 本域独立证据 = `r1-UdcBaseAppInfoController.javap.txt`（`docs/audit/artifacts/udc-publish-5.3.517/`） | **三份 javap 的 class_sha256 全等（deebcc39…）** → 保留既有 1 份即可，本域件作旁证/独立复算锚 |
| 9 | required_inputs | `("currentAppName",)` | `("currentAppName",)` | `("currentAppName",)` | 同 |
| 10 | verification_rules | 3 项（identity_matches / 响应非空 / 类级前缀因子类而异 UNVERIFIED） | 1 项（响应 SingleResponse 包裹 String；部署 context-path 需 LIVE 确认） | 建议并集 3 项（identity_matches + 非空 + 子类前缀装配 OBSERVATION/完整路由 UNVERIFIED） | **冲突=口径层 → 建议取并集并入既有条目**（不新增） |

**合并建议（可机械执行）**：MERGE 时对 `udc.application.deploy_info`（L90）与 `udc.appinfo.get_deploy_info`（L110）
按"同 class 同 class_sha256 同 method 同 path 语义"去重为 1 条（或保留双 ID 的既有分域登记现状不动），
`verification_rules` 取并集、`request_type` 取最精确写法、evidence 保留既有 1 份；
**本域提交物不新增任何 key**。

## 10 字段参照构造（**仅供字段对齐参照，MERGE 禁直接追加**）

```python
publish_deploy_info_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController", "method": "getDeployInfo", "class_sha256": "deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95", "javap": "docs/audit/artifacts/udc-publish-5.3.517/r1-UdcBaseAppInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
# ⚠ 参照行，勿追加：与 registry.py L90 udc.application.deploy_info / L110 udc.appinfo.get_deploy_info 同 key 语义（同 class_sha256 deebcc39…）
contracts["udc.publish.deploy_info"] = UdcOperationContract("udc.publish.deploy_info", "GET", "deploy-info", "String currentAppName(@PathVariable)", "SingleResponse<String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [publish_deploy_info_evidence], ("currentAppName",), ("同一 currentAppName 回读部署信息 JSON identity_matches", "响应 SingleResponse<String> 非空", "类级前缀因子类而异（FormAppInfoController={hostAppName}/dynamic-rest/com-seeyon/{currentAppName}/app-info，NormalAppInfoController={currentAppName}/app-info），完整路由 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

- 字段口径与 `components/platform_operations/models.py` `UdcOperationContract` 10 字段构造签名逐字段一致：
  `operation_id, method, path, request_type, response_type, status, write, evidence, required_inputs, verification_rules`
  （evidence 用 dict 列表、required_inputs/verification_rules 用元组、write=False、status=`OperationStatus.VERIFIED_STATIC_BYTECODE`）。
- 本域 `path` 只写**注解原值**（方法级 `deploy-info`，无前导 `/`），**禁拼网关 service 前缀**（离线不可确证）。
- **HYPOTHESIS / UNVERIFIED 标注条目已排除**：本域无此类条目需入库（L-C 常量池旁证、Spring 继承装配、
  跨构件 `udc-web` 的 `udc.deploy.*` 条目均**不作建议**，仅在本契约 OBSERVATION/边界段登记）。

## 不入建议清单（显式排除项）
| 项 | 原因 |
|---|---|
| `CustomApplicationController.updateDeployState`（`POST /update-deploy-state`） | **写形态**（修改应用发布状态）→ 只读契约口径外，仅本域契约 W1 段标注 |
| `domain/service.CustomApplicationService.publish` / `appservice.CustomApplicationAppService.updateDeployState` | 服务层方法，**非 HTTP 端点**（L-A/L-B 均未判为 mapping-bearing） |
| `event.publisher.*`（7 类） | **框架事件发布器**（EventPublisher/Helper/Entity/Business），与"应用发布"业务域无关，且非端点 |
| `api.DeployNoticeService` / `mq.DeployChangeEventListener` | 部署通知接口 / MQ 监听，**非 HTTP 端点** |
| `entity.CustomApplication.deploy_state` / `entity.BaseFormEntity.deploy_type,deploy_time` | 实体字段/DDL 常量，非端点 |
| registry L125/L128（`udc.deploy.normal` / `udc.deploy.search_status`，artifact=`udc-web-5.3.517.jar`，OBSERVED_LIVE） | **跨构件、跨证据等级**，不属本任务证据单元（任务边界=udc-starter-runtime 单 jar）→ 不引用、不合并 |

## 执行记录（回执行）

- **2026-10-19 主控复核**：`udc.publish.deploy_info` 已由 implementer 按本文件「10 字段参照构造」python 块**逐字节**照抄落库 `components/platform_operations/registry.py`（主控用 program 级 diff 比对整行，含 evidence dict 定义行，与源件 `BYTE-IDENTICAL`），插入位置 = `return cls(contracts)` 之前的 UDC-MERGE 批2 注释块。write=False、status=`OperationStatus.VERIFIED_STATIC_BYTECODE`，path 只写注解原值 `deploy-info`（未拼网关前缀）。
- **去重映射（不覆盖既有条目）**：与既有 `udc.appinfo.get_deploy_info`、`udc.application.deploy_info` 同 class_sha256（`deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95`）、同 method（GET）、同 path（`deploy-info`）→ 本域按分域登记别名入册，既有两条一字未动（先例：registry 同 path+method 的双 ID 分域登记）。
- **落库状态**：registry 有效键 HEAD `54bfdf9` 实测 76 → 追加本条与 page 域 1 条后 **78**（`UdcOperationRegistry.default().all()` 实测），本条全键 0 命中后新增，无 key 覆盖。`registry.py` sha256（落盘实测）= `8a6e0390ce81eb4f790a11e671bca7b7330213fc29158865b45bdd80f0144148`。
- **提交状态**：本条尚在 working-tree（`git status --porcelain` 显示 `M components/platform_operations/registry.py`），**待主控提交后回填 commit**（git 写操作本会话全禁）。
