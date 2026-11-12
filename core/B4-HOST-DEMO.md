# B4 宿主演示验收记录（HUMAN 总控=小爪以 Hermes 宿主身份执行，2026-09-25 15:0x+08）

演示方式：`bootstrap()` 离线态 → 按 core/skills/udc-entity-dev.md 五段打法走"建客户信息实体"需求。

实测输出（真实执行，非复述）：
- [1] Skill 加载 4921B，五段（需求解析/deploy_plan/宿主执行/回读验证/异常路径）齐 ✓
- [2] deploy_plan 出 4 步：udc.entity.create → udc.entity.attribute.create → udc.page.create → udc.deploy.normal ✓
      （5 枚举值域 + 1 unknown 如实标 + 5 evidence 分级）
- [3] core/tools/udc/ 4 tool 声明与 4 步方案一一对齐 ✓
- [4] core/facts/udc/entity/create.md 九段式齐、证据等级逐段标 ✓
- [5] bootstrap schema=xiaozhua-host-bootstrap.v1（离线态，未动 test2）✓

判定：B4=PASS。样板链 A→B→演示全链跑通，第一阶段完成定义（A 八件+B 样板格+演示验收）达成。
边界：本次演示为 dry（不向 test2 发起真实写请求）；真实写链已在 09-24 验收单上 LIVE 实证过（实体 7670732978062038177 + 4 属性 + 2 页面 + RELEASE 构建 + 物理表）。
---

## 第二实体 LIVE 演示（CaigouDingdan 采购订单｜宿主=Hermes implementer 会话内直连网关）

执行时钟：2026-09-27 17:28:09–17:30:42 +08（S0 起 / S6 止，实测时钟）。执行主体：implementer 会话；
路径＝样板链 `bootstrap().deploy_plan()` 出方案 → 按 steps 直连 test2 网关写面 → 独立 GET 三面回读。
凭据仅按路径引用，值 0 入件（证据只记 http 状态/键名/长度）。

写步实测（HTTP 状态为响应实值）：
- S2 建实体 `POST /service/udc/entity` → HTTP 200 / BOOT_0000；新实体 id=`-8376021272002477082`
      （name=CaigouDingdan，caption=采购订单，stereotype=bill，publishState=UNPUBLISH，
      tableName=caigoudin_m3247780144342633966）
- S3 建属性 `POST /service/udc/entity/attribute` ×4（每属性一次、body=单个 AttributeDto）→ HTTP 200 ×4 / BOOT_0000 ×4：
      caigouNo/采购单号/STRING、gongyingshang/供应商/STRING、caigouJine/采购金额/DECIMAL、caigouDate/采购日期/DATE
- S4/S5 建页 `POST /service/udc/page-info/base-info/create` ×2（单 PageDefinitionDto/次）→ HTTP 200 ×2 / BOOT_0000 ×2：
      采购订单列表 LIST pageUrl=caigoudingdanlist（页 id `-3104612801349693289`）、
      采购订单详情 DETAIL pageUrl=caigoudingdandetail（页 id `3073615057074895394`）

三面回读（独立发 GET 自证，非转述写步响应）：
- 实体面 `GET /service/udc/entity/primary/select-by-appid/3289082814923688017` → HTTP 200/BOOT_0000：
      命中 name=CaigouDingdan 且该行 id 与 S2 新建 id 逐字节相等 ✓
- 属性面 `GET /service/udc/entity/attribute/select-all-by-entity-id/-8376021272002477082` → HTTP 200/BOOT_0000：
      4 业务属性全命中（entityId 指向本实体，sourceType=ENTITY）✓
- 页面面 `GET /service/udc/page-info/select-by-appId/3289082814923688017` → HTTP 200/BOOT_0000：
      2 新页 caption 全命中（采购订单列表 / 采购订单详情）✓

判定：第二实体端到端 LIVE 命中 = 样板链可复制性证明（同一 deploy_plan 链对第二个单据实体复用成功）。

照实标注（UNVERIFIED / 未做项，不臆造）：
- 未执行 `udc.deploy.normal`（RELEASE 构建）→ 物理表未生成、实体 publishState=UNPUBLISH（读面实值）；
      「物理表落库 / publishState 转正」本段不主张。
- 建页调用粒度：本轮实测该端点 @RequestBody 目标为单个 `PageDefinitionDto`（JSON 数组与「数组含 1 项」均返
      BOOT_3002「Failed to deserialize the value of property  to type PageDefinitionDto」），故按单对象 ×2 执行；
      与 `deployment.py` step3「一次提交含两项」声明不一致，差异如实登记（证据 S4S5-page-create.json）。
- 首次运行将 19 位 traceId 误当实体 id（新建 id 与 traceId 同数量级）→ 该轮 4 次属性写入挂错父实体
      （该 id 实测 UDC_ENTITY_0007「Entity does not exist」），已按正确 entityId 重发；两轮均留证。
- 凭据 `expires_epoch` 已过期约 17.4h，但实测平台仍接受（S0 探测 HTTP 200）→ 本轮未触发续期
      （refresh_done=false，S0-cred-refresh.json）。凭据窗口的实际有效期 UNVERIFIED。
- 证据目录：`session-20260927-170839-5ed7b91f/evidence/`（S0/S1/S2/S3/S4S5/S6/RUN-SUMMARY + runner 脚本）。


## 第二实体端到端 LIVE（2026-09-27 17:2x，live-demo2 线产出）

- 实体：`CaigouDingdan`（采购订单）id=`-8376021272002477082`（stereotype=bill，09-27 17:28 POST BOOT_0000）
- 属性×4：caigouNo/gongyingshang/caigouJine/caigouDate（四步全 BOOT_0000×2 http[200,200,200,200]）
- 页面对：LIST+DETAIL 各 200（S4S5 final_ok LIST=true/DETAIL=true）
- 回读三面独立验证（S6）：entity face 171 实体命中 CaigouDingdan 且 id 相等 ✓
- RUN-SUMMARY：phase2 corrected_entity_id 一致；证据件全落 `evidence/`（REQ/RESP/traceId）
- 判定：**样板可复制性证实**——换实体名/字段重跑同链路一次通过，非验收单特例。

---
## 第二 app 复现段（独立测试 app 6570299241515796755｜样板链跨 app 可复制性证明）

执行时钟：2026-09-27 18:20–18:22 +08（实测；S0 18:20 探测 → S6 18:21 回读 → S7 本段追加）。执行主体：implementer 会话，同一 `deploy_plan` 链在 HUMAN 指定的独立测试 app 上独立复现（凭据仅按路径引用，值 0 入件）。本段与上段（项目管理平台段）无共享写入；旧 app 3289082814923688017 本轮**零写**。

写步实测（HTTP 状态均为响应实值，非复述）：
- S2 建实体 `POST /service/udc/entity` → HTTP 200 / BOOT_0000；**新实体 id=`3187060300026821876`**
      （name=CaigouDingdan，caption=采购订单，stereotype=bill，publishState=UNPUBLISH，
       tableName=caigoudin_8769734205899931427，appId=6570299241515796755）
- S3 建属性 `POST /service/udc/entity/attribute` ×4（单 AttributeDto/次）→ HTTP 200 ×4 / BOOT_0000 ×4
      caigouNo/采购单号/STRING、gongyingshang/供应商/STRING、caigouJine/采购金额/DECIMAL、caigouDate/采购日期/DATE
- S4/S5 建页 `POST /service/udc/page-info/base-info/create` ×2（单 PageDefinitionDto/次）→ HTTP 200 ×2 / BOOT_0000 ×2
      采购订单列表 LIST pageUrl=caigoudingdanlist（relationGroupId=-1628690631771369740）、
      采购订单详情 DETAIL pageUrl=caigoudingdandetail（relationGroupId=-2053135960134621592）

三面回读（独立发 GET 自证，非转述写步响应）：
- 实体面 `GET /service/udc/entity/primary/select-by-appid/6570299241515796755` → 200/BOOT_0000；
      同名行 1 条且 id 与 S2 新建 id 逐字节相等 ✓（row.appId=6570299241515796755）
- 属性面 `GET /service/udc/entity/attribute/select-all-by-entity-id/3187060300026821876` → 200/BOOT_0000；
      4 业务属性全命中（entityId 指向本实体，sourceType=ENTITY）✓
- 页面面 `GET /service/udc/page-info/select-by-appId/6570299241515796755` → 200/BOOT_0000；
      2 新页 caption 命中（已展开 row.pageList[]）✓

判定：**跨 app 可复制性成立**——同一 `deploy_plan` 链在第二个 app 上独立复现出同名实体/属性/页面，且三面回读命中（与上段同口径）。

照实标注（UNVERIFIED/未做项）：
- 未执行 `udc.deploy.normal`（RELEASE 构建，不在步骤序）→ 新 app publishState=UNPUBLISH、物理表未生成（读面实值）。
- Nacos dataId / 独立库是否就绪 = UNVERIFIED、非阻塞（main ROUTE §7 scope 裁剪；本会话无 MSE 只读凭据）。
- 建页粒度：`deployment.py` step3 仍声明「一次提交两项」，与本段实测（单对象 ×2）不一致，差异同 R1 段登记。
- 凭据 `expires_epoch` 已过期约 17.5h 但实测平台仍接受（S0 探测 HTTP 200）→ 本轮未续期。
- 证据目录：`session-20260927-170839-5ed7b91f/evidence/R2-*`（S0/S1/S2/S3/S4S5/S6/RUN-SUMMARY + runner）。
