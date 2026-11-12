# R2 实体环｜证据件（test2 活体 · 2026-09-30 18:14 CST）

> 性质：写路径 R2（建实体）环 LIVE 证据。main 裁定 R1 = 设计态草稿面 PASS 后发 R2 HANDOFF
> （dedupe=`r2-entity-handoff-v1`，session `session-20260930-152536-efab788e`）。
> 仓库 `<SEEYON_AGENT_ROOT>`，HEAD `cf45180`。test2 镜像 5.3.496。
> **终态：R2 = LIVE PASS**（实体 + ≥1 字段建成，双回读命中同一目标，非空业务样本，traceId 在盘）。
> 凭据 0 入件（§8 自检）。

## 0. 环境与时钟（实测）
| 项 | 实测值 |
|---|---|
| 网关 | `{config键 gateway_base}`（test2，值 0 入件） |
| 宿主 | T2 = `znxmglptcopy5791640252914287064`（running_profile:test2） |
| **数字 appId（_to_app_id 自算，不硬编码）** | `5791640252914287064`（T2 末尾数字串；`deployment.py::_to_app_id` 规则） |
| 探针时钟 | 2026-09-30 17:56–18:14 CST |
| 凭据 | `shared-credentials/ctp-user-login.json`（值 0 入件，sha256_16 `392fb61b…`）；17:56 登录换 cookie（len 327，值 0 入件） |
| 实体命名 | `ZzprobeR2` / caption `zzprobe20260930R2`（E6 zzprobe 前缀） |

## 1. 建实体（`udc.entity.create`，收口契约 `entity/create.md` §3/§5）
端点：**`POST {gateway_base}/service/udc/entity`**（平台服务面，无 appId 网关前缀；body `EntityDto`）。
**前缀修正（普通可逆，单步内自修，交 main 知会）**：ROUTE E-R2 写的是
`/service/{T2数字appId}/udc/entity`（网关宿主前缀），实测两次返回
**HTTP 200 / 信封 `code=server_404 / status=3`「5791640252914287064 服务不存在，请重启服务或重新发布应用后再试」**
（T2 宿主运行时服务未发布，与 R1 custom-app `status:2` 同根的环境宿主绑定阻塞）→ 回退 `create.md` 收口契约形态
`/service/udc/entity`（body.appId = 数字 T2NUM 指定宿主）→ **200 / BOOT_0000 / SUCCESS**。

| # | URL 形态 | body（EntityDto，逐字在 jsonl） | HTTP | envelope | traceId | 结果 |
|---|---|---|---|---|---|---|
| c1 | `/service/{T2NUM}/udc/entity`（ROUTE 形态） | `appId=T2NUM,name=ZzprobeR2,caption=zzprobe20260930R2,stereotype=bill,entityNature=MAIN,features=basic,approve,organization,billBasic,termination,suspend,nullify,multiplicity=ONE2MANY,category=ENTITY,parentEntityId=0,superior=0,validate=true` | 200 | `server_404 / status=3` | n/a | 宿主服务未发布 |
| **c2** | **`/service/udc/entity`（create.md 收口形态）** | 同上 | 200 | **BOOT_0000 / status=0** | `3253879429058791612` | **实体建成，`data.content="-324146415073342494"`（= entityId，取 `data.content`，非 traceId —— skill 坑①）** |

## 2. 建属性（`udc.entity.attribute.create`，≥1 字段，单 AttributeDto）
端点：`POST /service/udc/entity/attribute`（T2 网关前缀同 server_404 → 回退无前缀收口形态）。
body = `{"appId": T2NUM, "entityId": -324146415073342494, "name": "ZzprobeR2FieldA", "caption": "zzprobe字段A", "dataType": "STRING"}`。

| # | URL 形态 | HTTP | envelope | traceId | 结果 |
|---|---|---|---|---|---|
| a1 | `/service/{T2NUM}/udc/entity/attribute` | 200 | `server_404 / status=3` | n/a | 宿主服务未发布 |
| **a2** | **`/service/udc/entity/attribute`** | 200 | **BOOT_0000 / status=0** | `3253881685174913212` | **字段建成，`data.content="-8300366849300533454"`（= 属性 id）** |

## 3. 回读同一目标（独立重发，不采信写步响应转述；skill 三面回读纪律）
| 回读 | URL | HTTP | 命中 | traceId | 断言 |
|---|---|---|---|---|---|
| 实体 by appId（预检→建成→复证三次独立重发） | `GET /service/udc/entity/primary/select-by-appid/{T2NUM}` | 200/BOOT_0000 | 行 `id=-324146415073342494, name=ZzprobeR2, guid=6233922445365373130, tableName=zzprober2_6233922445365373130, publishState=UNPUBLISH, appId=T2NUM`（行数 48→49） | `3253878133689944252`（预检）/ `3253879449426331836` / `3253894632135723196`（复证） | **非空业务样本，id/guid/tableName/publishState 全非空** |
| 字段 by entityId（两次独立重发） | `GET /service/udc/entity/attribute/select-all-by-entity-id/{entityId}` | 200/BOOT_0000 | 行 `id=-8300366849300533454, name=ZzprobeR2FieldA, dataType=STRING, caption=zzprobe字段A, **entityId=-324146415073342494（归属正确，非孤儿）**`（48 条，含单据族系统字段） | `3253879455902337212` / `3253881694654040252` / `3253894642202052796`（复证） | **≥1 字段非空，且 entityId 归属 = 刚建实体（排除孤儿挂接）** |

- **口径如实登记**：实体行 `fullName` 键存在但**设计态 UNPUBLISH 回读为 null**（未发布不 mint；
  同回显 `guid`/`tableName` 非空）→ 非空断言按 `id + guid + tableName + publishState` 取，不冒充 fullName 非空。

## 4. 异常轮如实登记（不藏、不删）
- 首次全链脚本（17:58:46）在 record 前崩溃（NameError），但 POST 已发出 → 先做 **precheck**
  （select-by-appid 48 行无 ZzprobeR2 → 坐实未建成）再安全重发（17:58:47 c2 唯一一次实际建成）。
- 复证脚本首版（18:10）login 缺 body → `BOOT_3000`（Required request body is missing）→ 无新 cookie →
  回读 `BOOT_1006`（SSO 重定向信封）；**该轮 3 条记录留盘如实，复证改走 17:56 session cookie 重发成功（18:13:54）**。
- 凭据 401 未出现，未刷新（E2「401 才刷新，先探测」纪律遵守）。

## 5. 失败四类归因（本轮）
| 类 | 命中 | 证据 |
|---|---|---|
| 环境/宿主绑定 | **是（网关宿主前缀形态）** | c1/a1：`/service/{T2NUM}/…` → `server_404/status=3`「服务不存在，请重启服务或重新发布应用」= T2 宿主运行时未发布（与 R1 同根环境阻塞，但 **create.md 收口契约的无前缀形态可绕开**，实体正常落到 T2 宿主） |
| 参数错 | 否 | c2/a2 全字段一次成功（BOOT_0000） |
| 权限不足 | 否 | 全程 200，无 401/403 |
| 接口不存在 | 否 | 端点均 200（server_404 是业务信封非 4xx；无前缀形态 BOOT_0000 坐实端点在） |

## 6. Side Effects + 回滚（不可逆写 → 清单报 main，不自行删）
- **本轮实建（非零）**：1 实体 + 1 字段（宿主 = T2，设计态 UNPUBLISH，未落物理表 —— 物理表由 RELEASE 构建触发，本轮未做）。
- **回滚清单（待 main 确认，不自行删）**：
  1. 字段：`POST /service/udc/entity/attribute/delete` body = `-8300366849300533454`（属性 id；registry `udc.entity.attribute.delete` 在盘 L31）；
  2. 实体：**registry 无实体级 delete op**（`udc.entity.*` 仅 create/update/search/attribute.*）→ 实体删除端点 **UNVERIFIED**，须 main 裁定（或环境侧给 delete 端点/走宿主管理面）；字段删后实体可留置。
  3. 连带留置：R1 草稿 `dataId=1 @ T2`（main 已裁留置）。
- **实体/字段 deleteByIds 清单 = [属性 -8300366849300533454] + [实体 -324146415073342494（删除端点 UNVERIFIED）]，终态收口时交 main 裁。**

## 7. 交付绑定锚（实测）
| 项 | 值 |
|---|---|
| HEAD | `cf45180` |
| 原始 jsonl | `R2-entity-create-{20260930175632,175730,175744,175846,180101,180159,181000,181353}.jsonl`（8 件） |
| 本证据件 | `evidence/R2-entity-create-20260930.md` |
| 九段式格 | `write-chain.md` R2 段（本轮新建，九段式填实） |
| STATUS 追加 | §八.8（R2 实体环） |
| 实体/字段 id | `-324146415073342494` / `-8300366849300533454`（均取 `data.content`，非 traceId） |

## 8. 脱敏自检（凭据 0 入件 · 实测）
- 自检脚本（`implementer/probe/_tmp_r2_leakcheck.py` 存盘）：比对 live 敏感值（loginName/password，值不回显）
  + 全 evidence JWT 长串扫描 → **1 处命中（17:56 login 件 Set-Cookie 回显 token，len 311）→ 已脱敏为
  `<REDACTED_CREDENTIAL>`；session 临时件（含 cookie 值）已删除** → 复核 **0 命中（CLEAN）**。
- 交付件 grep：`loginName/password/cookie 值 = 0`；仅 cred 文件路径 + sha256_16 + cookie 长度入件。
