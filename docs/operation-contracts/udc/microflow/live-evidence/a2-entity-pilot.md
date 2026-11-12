# A2 LIVE 试点（EntityController 23 条契约路径段）活体事实
取证：2026-09-18 01:18 CST（token exp 01:21:53，有效窗口内）· 只读 GET · 凭据引用只脱敏（SY_ACCESS_TOKEN 明文不落对话/报告）
target: https://lowcode-test2.example.com · gateway service = udc（活体确证）

token 已穿透 SSO 墙（不再 302 uatsso）。三条 EntityController 契约路径段活体探测：

| 端点（23 条契约之一） | 活体响应 | 判定 |
|---|---|---|
| GET /service/udc/entity/search/term?appId=app9000000000000000001&term=a | 405 Method Not Allowed | 端点存在，GET 不允许（该契约实为 POST） |
| GET /service/udc/entity/select-by-appid/tree/{appId} | BOOT_3000 Failed to convert String→Long (NumberFormatException: "app9000000000000000001") | 端点存在但 {appId} 需 Long 型；字符串型 applicationId 不匹配 |
| GET /service/udc/application/{appId} | BOOT_3000 同上 | 端点存在但 {id} 需 Long 型 |

## 判定（证据等级纪律）
- 三条均**非业务成功**（405 / 400 校验错），A2 不判 PASS，维持 UNVERIFIED。
- 精确缺口：test2 部署态 entity/application 端点的 path 变量要求 **Long 型 id**，而本任务 application_id
  `app9000000000000000001` 是字符串型（字母+数字）。要拿到 LIVE PASS 的"同一 target 回读 identity_matches=true"，
  须以 **Long 型实体 id / 数字型 application id** 作 target（如 test2 里某真实数字型 app 的实体 id），
  或经 P1（VPN 恢复后 kubectl 取部署态 jar）确证部署态哪些只读端点接受字符串型 applicationId。
- 微流程 C1/C2/C3 的 meta-data/datatype/app-log 路径段在 test2 404（Whitelabel，本地 5.3.517 静态 vs 部署态路径差异），
  与上条同因：需 P1 确证部署态路径后方可谈 A2 LIVE。
- 不据活体结果改写静态契约路径原文；本地 5.3.517 与 test2 部署态分列，A6 报告项。

## 对 A2 收口的影响
- A2（≥1 条 test2 LIVE PASS）当前 = **UNVERIFIED / 单分支 BLOCKED**，阻塞原因：
  参数类型（Long 型 id）+ 微流程路径段部署态 404，均待 P1（部署态 jar）确证；P1 SSH 206:22 网络 BLOCKED（无 VPN）。
- 未达 A2 不写 FINAL；A2 如实报 UNVERIFIED + 精确缺口，其余 A1/A3/A4/A5 可离线收口。

raw：docs/operation-contracts/udc/microflow/live-evidence/a2_live_readback_20260917T160331Z.md（C1/C2/C3 微流程段）
本次试点原始输出记于 main/worker（临时），业务事实以本文件为准。
