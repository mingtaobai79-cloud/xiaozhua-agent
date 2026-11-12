# C-9｜DATE 类型探针 — BLOCKED（第 3 次：9223 实例无登录态）

2026-10-20 12:02｜app `8704025620829192834`｜entity `4796455827714164161` (migrationPlan)
**状态：BLOCKED**｜写授权 **consumed 0 / 剩余 1**｜DB 43 行原状｜**非挂死**（renderer 健康）

## 0. 结论
`zzprobeDate01` **未创建**。HANDOFF 第一步只读确认失败：9223 现有页面会话**没有 test2 登录态**，导航目标页被 SSO 302 到登录页。与前两次「renderer 挂死」是不同故障。

## 1. 只读确认证据（⚠ 证据性质先声明）
**本轮 stdout 未落盘**（`node c9step1.js` / `c9redir.js` 输出仅终端打印，未重定向文件）⇒ 下述运行时判据**不可独立复算**。凡能从脚本 + 既有文件复原的标『复原』；其余仅为当轮观察，不冒充可复算证据。

**导航链（复原：`c9redir.js` L26-27 监听 `Page.frameNavigated` + `Network` Document 请求）**
```
lowcode-test2/.../udc/app-design/entity?appId=8704025620829192834
 → uatsso.客户方.com/esc-sso/oauth2.0/authorize?client_id=3fa73130e3a3804fb659...
 → uatsso.客户方.com/esc-sso/login            (302)
 → uatsso.客户方.com/esc-sso/login/page       (302)
```
**cookie 实况（复原：`Network.getCookies` 按域查询）**
```
lowcode-test2.example.com -> 0 个
uatsso.客户方.com        -> 2 个 (pg-rl, browserId)
```
⇒ 9223 实例从未登录 test2；human 11:51 的登录落在另一 profile，未流入 `cdp-A-平台基础`。

**loginPage=true 的判定来源 = `c9redir.js` L46**（含『账号密码』分支），非 `c9step1.js`。后者 L77 当时缺该分支（已按补证修），故本轮结论采用 redir 的判定。

## 2. renderer 健康（关键区分）
```
PRE_BASELINE: 2       ← 登录页 1+1 -> 2（复原：c9step1.js L41-42 显式求值）
DIALOGS: []           ← 无 alert 锁死（复原：c9redir.js L28 监听）
状态轮询 15 次正常返回（当轮观察）
```
⇒ 本次**不是**域绑定前挂死；CDP 与环境交互正常，纯粹缺登录态。

## 3. 三次 BLOCKED 根因分列（防混淆）
| 次 | commit | 根因 | renderer |
|---|---|---|---|
| 1 | `2fcf0b7` | 页面不进设计器（当时误判凭据已排除） | 挂死 |
| 2 | `89a5309` | 全新 profile + 9240 仍挂死；凭据结论更正 UNVERIFIED | 挂死 |
| 3 | `d9bcb37` | 9223 实例 0 cookie → SSO 跳登录页 | **健康** |

⚠ **`BLOCKED-DIAGNOSIS.txt` [SUPERSEDED by `89a5309` §4]**：含已作废结论「凭据已证有效，排除」。正文保留不改（存史），仅在本报告与 manifest 对应行标注取代关系。

## 4. 凭据有效性（沿用上轮更正，未推翻）
匿名 `GET /main/portal` 同样 200/11714（SPA 外壳），HTTP 层不证鉴权 ⇒ shared-credentials token 状态仍 **UNVERIFIED**。本轮按 HANDOFF 禁读/禁注入，未触碰凭据文件。

## 5. 写计数
```
授权写 consumed 0 / 剩余 1
页面保存点击 0（本轮）｜落库 0｜/service 0｜graphql 0｜重启 0
```
DB 实测：entity **43** 行、max_order **43**、`zzprobeDate01` **0** 行。

## 6. 需 human：把登录态放进 9223 实例
**A**｜在 9223 窗口（user-data-dir=`<HERMES_HOME>\cache\scratch\cdp-A-平台基础`）手动完成 notes 登录并停在设计器页。
**B**｜明确解禁 G1，允许我用 shared-credentials 在 9223 内建会话（本 HANDOFF 明令禁止，未做）。

## 7. 恢复后执行
`c9step1.js`（已修 L77 正则，`node --check` 通过；未运行）只读确认 → 通过后跑 `c9run3.js` **G2-G12 主体**（跳过 G1 注入段）。
保存闸门不变：Ctrl+A `modifiers:2` → 清空循环 `value===''` → 重读 `input.value` 精确等于 `zzprobeDate01` 才保存。

预查仍有效：`zzprobeDate01` 全库 **0** 行。DATE 先例为**全库 1364 行**（`max_length=20`/`dd=0`/DatePicker），**本 app 首个** DATE 字段。

**存档**：`artifacts/c9-20261020/`（probe/auth/dialog/run3/step1/redir + manifest sha256）
