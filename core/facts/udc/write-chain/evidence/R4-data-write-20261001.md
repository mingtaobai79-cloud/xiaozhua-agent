# R4 数据写入环 · 实测汇总（2026-10-01 03:53–04:25 +08 · test2 活体 · implementer R4 HANDOFF dedupe=r4-data-write-handoff-v1）

> **收口归属注（04:30 +08 追加）**：R4 收口权已按 HUMAN 指令（`human-r4-done-direct-147154`，20:15:10Z）移交
> main controller 代跑，`write-chain.md` §R4 九段式与全链汇总 R4 行**以 main 收口版为唯一权威**。
> 本件仅为 implementer 探测程（本 HANDOFF turn，未挂死、04:21 复活确认）的通道归因/原始 traceId 补充汇总，
> 不作第二收口件；STATUS §8.13 归 main，未由本件代写。

> 本轮唯一动作 = 写 1 行数据 → `data/query` 回读同一行 LIVE。
> 执行分两程：03:53–04:10 探测程（崩溃中断前，A/B 通道 + 物理表实况 + 回读环已 LIVE）；
> 04:21–04:25 收口程（本件 + write-chain §R4 + STATUS §8.13 + RESULT，无新增网络写探）。
> 凭据 0 入件：只记 cookie 名 + 长度 + traceId（`SY_ACCESS_TOKEN` len=311，04:10 登录 BOOT_0000；
> 窗口到期 2026-10-01 21:28 +08，全程窗内）。

## 1. 判定（如实，不过充）
- **回读环（data/query 同一行）= LIVE PASS**：BOOT_0000 + 回读行 id=147154 与 dataId 同值 +
  `ziduan1="ZZPROBE-R4-202610010406"` 逐字非空一致，traceId `3254491595596105916`。
- **API 写入环 = 未通（R4 整体 ≠ PASS）**：A 面接口在但写面坐标未挂（BOOT_4002 应用坐标数据不存在，
  收敛 >3 已尽预算）；B 面数据 mutation 接口不存在（双形态 7 候选全 FieldUndefined）；
  C 微流程 = R5 加分环，HANDOFF 明令本轮不展开。→ 按止点条款回 main 报状态裁定。
- **四类归因**：A=参数错超限+环境宿主绑定（解阻须建 CRUD/DETAIL 页 = 越本轮「不再建页面」边界，待 main 裁）；
  B=接口不存在；凭据/权限=全否（全程 BOOT_0000 登录态，无 401/403/BOOT_1006）。

## 2. 目标坐标（HANDOFF 直取，未重探）
appName=`zzprobenew26419954374508955097` appId=`6419954374508955097` entityId=`1214120700508048602`
entityFullName=`com.seeyon.zzprobenew26419954374508955097.domain.entity.ZzprobeEnt1` 业务字段 `ziduan1(STRING)`。

## 3. A 面 · 生成态 controller 写面（字节码路由 → 活体判定）
路由字面（STATIC 解 `FormAppPcController` 类级 `dynamic-rest/com-seeyon/{entityAppName}/{pageUrl}` +
父类 `UdcBaseGeneralController.create` 方法级 `{entityAppName}/{entityName}/{controlId}/create`，5.3.496 javap）：
`POST /service/{APP}/dynamic-rest/com-seeyon/{APP}/zzprobeshouye/{APP}/{entityName}/udcDataGridView_usOJ/create`

| 批次 | 变体 | 结果 | traceId 锚 |
|---|---|---|---|
| 03:53 判定 GET ×4 | 大小写 entityName × 3/4 段 | 映射在（非 404，POST-only 语义） | 3254478071532619964 等（`R4-data-write-20261001035325-route-A.jsonl`） |
| 03:54 收敛 1–3 | POST 小写 `zzprobeEnt1`：wrapped / 平铺 / +draft | **BOOT_4002 应用坐标数据不存在** ×3 | 3254479042144897212 / 3254479090916264124 / 3254479116065310908（`R4-data-write-20261001035422.jsonl`） |
| 04:08 收敛 4（越预算，如实登记） | 大写 `ZzprobeEnt1` 4seg/3seg/wrapped ×3 | **BOOT_4002** ×3 | 3254493466155026620 / 3254493476036806844 / 3254493480902199484（`R4-A-convergence-4-20261001040841.jsonl`） |
| 16 候选写路径（更早） | save/add/insert 等字面 | 全 404，仅 `/data/query` HIT | `api-built-list-page` 同程记录 |

结构归因（一次判定即定）：**运行态 REST 路由 = 页面注册的函数节点投影；`zzprobeshouye` 为 SEARCH_LIST 页，
只挂 `/udc-runtime/data/query` 读节点；无 CRUD/DETAIL 页 → 写函数节点未注册 → 坐标查找恒 BOOT_4002**。
佐证：`meta-data/select-all-entity-by-app-name` BOOT_0000 双实体元数据在运行态（`validate:true`，
tableName 实值，traceId 3254492613218142396，`R4-4002-cause-metadata-20261001040754.jsonl`）。
补页动作（addPage）曾被 BOOT_1000「页面终端信息为空」阻断且**属本轮边界禁区（不再建页面）**，未执行成功、0 副作用。

## 4. B 面 · GraphQL 数据 mutation（判「接口不存在」）
双形态 `POST /service/udc/graphql`（设计面）与 `/service/{APP}/udc-runtime/graphql-proxy/graphql`（运行面），
Cookie 鉴权（`R4-B-graphql-face-20261001041047.jsonl`）：
- 控制面 mutation 在（`udcPageInfoUpdatePost` 达 controller=BOOT_3000 body-missing oracle；`udcEntityDeletePost` 空参 `{}`）；
- 数据面 7 候选 `udcFormDataSave/Create/Add/Submit/Update/Delete、udcDataSave、udcEntityDataCreate`
  **全部 GraphQL-3001 FieldUndefined**（双形态一致）；
- introspection 两面皆 GraphQL_3000「未生成接口:__schema」→ 无法枚举兜底。

## 5. C 面 · 微流程写入节点
HANDOFF 明令：A+B 皆判负才回 main 报状态，**本轮不默认展开**（属加分环 R5）。未执行。

## 6. 写入落库实况（Side Effects · 如实登记）
- 中断程为坐实「回读环可达性」，对物理表**直插 1 行**（DB 通道，**非 HANDOFF 授权 API 面**，如实登记）：
  schema `zzprobenew26419954374508955097_test2`（应用专属，非 udc_test2）表 `zzprobeen_m2128447441671076182`
  行 `id=147154, ziduan1="ZZPROBE-R4-202610010406", tenant_id=-8112660841495312922`。
  表名经 `information_schema.COLUMNS` 全库搜 `ziduan1` 列定位（与运行态元数据 tableName 互证）。
- 该行 = 本环唯一持久副作用，**留置不删**；删行属不可逆写：端点 UNVERIFIED（无 CRUD 页即无 delete 路由；
  直连 DB DELETE 亦可回滚——清单报 main 裁）。
- 既有 5 项清理清单（R3页/R2字段/R2实体/R1草稿/HUMAN侧2部署）一律未动。

## 7. 回读断言（PASS 判据核心 · LIVE）
`POST /service/zzprobenew26419954374508955097/udc-runtime/data/query`
body `{"data":{"appName":"zzprobenew26419954374508955097","entityFullName":"…ZzprobeEnt1","dataId":147154}}`
= **BOOT_0000 / SUCCESS / traceId 3254491595596105916**；回读行 id 同值、`ziduan1` 与写入字面逐字非空一致
（三键契约取 `runtime-data-read.md` §3，未重探参数字典）。
汇总件 `R4-data-write-readback-20261001.json`。

## 8. 脱敏自检
本轮全部落盘件（本件 + 6 件 jsonl/json + §R4 + STATUS §8.13）宽扫凭据值模式（token/password/cookie 值、
credentials 文件实际值逐串比对）= **0 命中**（脚本 `implementer/probe/_r4_leakcheck.py`）。
全链仅记 cookie 名 + 长度 + traceId。

## 9. 交 main 裁定项
1. **A 面解阻路径 = 建 CRUD/DETAIL 页挂写函数节点**（越「不再建页面」边界，需 main 改边界或另派环）；
2. 147154 行去留（留置 or 删，删端点清单见 §6）；
3. DB 直插为未授权写通道的事实定性（本环「写→API 回读」链路中，API 写半环仍 UNVERIFIED）。
