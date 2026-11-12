# 设置域公共前置：取 appGuid

**证据等级**：LIVE（实跑 200 + BOOT_0000 + guid 回读；两次连发均成功）
**验证日期**：2026-10-23
**目标环境**：test2，`datamigration9000000000000000001`
**证据出处**：`core/facts/udc/entity/evidence/entity-surface-2026-10-23/capture-page-boot.json`
（设计器打开实体页时平台自身发出的请求，响应内含 `"guid":"2275741415570096882"`）

> 设置域 9 个子域（枚举 / 枚举项 / 自定义对象 / 属性集 / 选项集 / 参数 / 二维码 / 流水号 / Excel 模板）
> 的 `udc*Post` 都强制要 `appGuid`，缺则 `BOOT_1001` 或落成 `app_guid=-1`（页面查不到）。
> 各子域文件只写了「取自 `udc_application.guid`」——**那是表名列名，不是取法**。取法统一在本文件。

---

## 0. 一句话

```
appGuid ≠ appId。用 udcApplicationDetailGet 查，不要查库、不要猜。
```

## 1. 接口取法（推荐）

### 1.0 一条命令（推荐，已封装）

```bash
python scripts/udc_setting_create.py app-guid --app-id <appId>          # 取 appGuid（0.3s）
python scripts/udc_setting_create.py enum --app-id <id> --code X --caption 名称 \
    --items "PAUSE:暂停,BREAK:中断"                                      # 建枚举+枚举项（0.7s）
python scripts/udc_setting_create.py dto --app-id <id> --name X --caption 名称 \
    --fields "planCode:方案编码:STRING,mode:控制指令:CTPENUM@<enumId>"
python scripts/udc_setting_create.py verify --kind enum --app-id <id> --code X
python scripts/udc_setting_create.py delete-enum --app-id <id> --code X  # 逻辑删除(可恢复)
```

脚本内部固定了 appGuid 获取、i18n JSON、CTPENUM 三件套（dataType/relationApp/relationEntity）、
`UpdateDtoPost` 端点、5xx 重试与超时。**改为手拼 payload 前先看脚本是否已覆盖。**

### 1.1 手工调用

```
POST /service/udc/graphql?udcApplicationDetailGet
Content-Type: application/json
（需登录态 cookie）
```

```json
{
  "query": "query graphqlLoader ($p0: udcApplicationDetailGetInputPath) { data0: udcApplicationDetailGet(path: $p0) { code data { content { id name guid caption } } message status } }",
  "variables": { "p0": { "id": "<appId>" } }
}
```

响应：

```json
{"data":{"data0":{"code":"BOOT_0000","data":{"content":{
  "id":"8704025620829192834","name":"datamigration9000000000000000001",
  "guid":"2275741415570096882","caption":"数据迁移"}},"message":"SUCCESS","status":0}}}
```

取 `data.data0.data.content.guid` 即为 `appGuid`。

### 要点

- **`path.id` 传 appId**（不是 guid）；返回体里 `content.guid` 才是 appGuid。
- selection **只需 `guid`**，精简到 `{ id name guid caption }` 实测可行（len=238）。
- **偶发 `server_500`**：曾出现一次 `/udc/graphql 服务异常`，同一报文随后连发两次均 200 →
  属瞬时抖动/页签忙，**重试即可，不要改 payload**。设计器启动时用的是全字段选择
  （icon…copVersion 共 19 项），也可照抄。
- 走页面内 fetch（`credentials:'include'`），**curl 拿不到 token**（HttpOnly cookie）。
- 每次 fetch 必须带 `AbortController` 超时（10–15s）：服务端偶发挂死，不带超时会烧掉整个调用窗口。

## 2. 兜底：查库（仅在接口不可用时）

```sql
SELECT guid FROM udc_application WHERE id = '<appId>';
```

接口可用时不必查库——这是兜底，不是首选。

## 3. 各子域引用位置

| 子域 | 文件 |
|---|---|
| 枚举 | `enum/create.md`、`enum/enum-write-chain.md` |
| 自定义对象 | `custom-object/create.md` |
| 属性集 | `attribute-set/default-value-chain.md` |
| 选项集 | `option-set/create.md` |
| 参数 | `parameter/create.md` |
| 二维码 | `qrcode/create.md` |
| 流水号 | `serial/create.md` |
| Excel 模板 | `excel-template/create.md` |

## 4. 本应用实测值（test2 数据迁移）

| 项 | 值 |
|---|---|
| appId | `8704025620829192834` |
| appGuid | `2275741415570096882` |
| name | `datamigration9000000000000000001` |
| caption | 数据迁移 |

> 其他应用/环境的值必须现查，不要跨环境复用。
