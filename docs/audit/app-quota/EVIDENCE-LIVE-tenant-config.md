# SLICE-A1 平台自述接口 —— 原始响应留证

> 本文件记录 **2026-10-18 实际抓到的原始响应**，逐字保留，不做美化。
> 后续重放遇到 `BOOT_1006 token黑名单` 属同账号（test-account-1）被其他组踢下线的已知风险，
> **不得用后续失败覆盖本文件的成功证据**。

## 请求 1（成功，决定性证据）

```
GET https://lowcode-test2.example.com/service/udc/sandbox/tenant/config/-8112660841495312922
Cookie: <shared-credentials/test2-web-credential.json 的 cookie 字段，本文不落 secret>
Accept: application/json, text/plain, */*
Referer: https://lowcode-test2.example.com/main/
```

响应 **HTTP 200**，耗时 ~100ms，body 长度 **276**：

```json
{"status":0,"code":"BOOT_0000","message":"SUCCESS","traceId":"3278987915564157116","data":{"content":{"validate":true,"useTenantId":"-8112660841495312922","tenantCaption":"四川客户方信息产品有限责任公司","createAppNum":10,"runAppNum":15,"currentCreateAppNum":null,"currentRunAppNum":null}}}
```

关键读数：

| 字段 | 值 | 意义 |
|---|---|---|
| `createAppNum` | **10** | 本租户建应用上限 = 10（配额门读的就是这个字段） |
| `runAppNum` | 15 | 运行应用上限 |
| `useTenantId` | -8112660841495312922 | 确认行主键语义 = 租户ID |
| `currentCreateAppNum` | **null** | 未被 `configAllTenant`/`selectPageByConditions` 分支填充 → 证明走 `selectById → entityToDto` |
| `currentRunAppNum` | **null** | 同上 |

`current*` 两字段为 null 是**路径判据**：反编译里只有 `configAllTenant()`（L248-273）和
`selectPageByConditions()`（L275-300）会给这两个字段赋值；`selectById()` → `entityToDto()`（L233-241, L323-328）
不赋值。因此该响应确实来自 `selectById` 分支，即**直接按租户 id 打表**，不是"按 tenant_id 扫多行"。

## 请求 2（探路失败，记录前缀结论）

```
GET .../service/6419954374508955097/sandbox/tenant/config/-8112660841495312922
-> HTTP 200 {"status":3,"code":"server_404","message":"6419954374508955097 服务不存在，请重启服务或重新发布应用后再试！"}
```

```
GET .../service/sandbox/tenant/config/-8112660841495312922
-> HTTP 200 {"status":3,"code":"server_404","message":"sandbox 服务不存在，请重启服务或重新发布应用后再试！"}
```

结论：**网关不认 `sandbox` 作独立服务名，也不认应用 applicationId 前缀**；
`/service/udc/...` 才是可路由的命名空间（`sandbox` 挂在 `udc` 应用下）。

## 请求 3+（token 被拉黑）

```
GET .../service/udc/sandbox/tenant/config/-8112660841495312922
-> HTTP 200 {"status":3,"code":"BOOT_1006","message":"token黑名单","traceId":"n/a","data":null}
```

原因：本组与另外两组共用账号 `test-account-1`，互相踢下线（硬约束第 8 条已登记为已知风险）。
**未刷新 token、未重试**，避免进一步加剧互踢。

## Redis 侧同步证据（同一份数据的另一通道）

```
KEY  : sandbox/test2/tenant/config   (hash)
HKEYS: ['-8112660841495312922']
HGET -8112660841495312922 ->
  ["com.seeyon.boot.starter.sandbox.dto.SandboxTenantConfigDto",
   {"validate":true,"useTenantId":["java.lang.Long",-8112660841495312922],
    "tenantCaption":"四川客户方信息产品有限责任公司","createAppNum":10,"runAppNum":15}]
HGET -999 -> NULL（未命中）
```

**TTL 刷新证据**（证明 E1 的响应体就是 `selectById → putCache` 的同一份数据）：

| 时刻 | TTL(s) | 约合 |
|---|---|---|
| E1 调用前 | 204065 | 2.36 天 |
| E1 调用后 | 604790 | 7.00 天（= `expire(key, 7, DAYS)` 回写） |

`putCache()` 是 `entityToDto()` 内唯一写缓存处（`SandboxConfigService` L334-337）。
TTL 从 2.36 天跳回 7 天，说明读取链确实执行了 `selectById → entityToDto → putCache`，
而 `putCache` 写入的 `createAppNum` 就是 E1 返回的同一个 10。
