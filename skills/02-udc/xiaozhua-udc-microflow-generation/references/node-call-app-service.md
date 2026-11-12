# CALL_APP_SERVICE（自定义服务）

> 2026-11-03 实测于 test2：**流水号组件 getSerialNumber 跑通，返回值落库**

## 1. 契约（活引用，禁止写死）

```
fullName : com.seeyon.boot.starter.serialnumber.appservice.SerialNumberAppService.getSerialNumber
md5      : 413b1d849eaae74b9b1f8e292e4d9fc8
param    : SingleRequest<SerialNumberDto>
return   : SingleResponse<java.lang.String>
app      : boot-starter-serialnumber（inApp=false, udcApp=false）
```

签名从 `LiveRefs.app_service_method()` 运行时拉，md5 与 V16 备份样本逐字一致。

## 2. 三个必须做对的细节

### 2.1 starter 服务不属于当前应用

真实节点里 `app.appName=boot-starter-serialnumber`、`inApp=false`。
写成当前 UDC 应用会让抽屉显示错归属、运行时找不到服务。
推导规则（构造器已实现）：

```
implClass 以 com.seeyon.boot.starter.<stem>. 开头  →  appName = boot-starter-<stem>
```

### 2.2 attrs 必须是**字段级** attrType

parameter 是 `SingleRequest<SerialNumberDto>` 时，真实节点的 attrType 是
`SerialNumberDto.serialSchemeCode`（字段），不是 DTO 全名。
只按 parameter 推会得到 DTO 级 attrType，字段映射对不上。
构造器已支持调用方传入字段级 attrType 覆盖。

### 2.3 简单类型返回值不能默认 DTO

`returnValue.item.itemType=java.lang.String` 时 `output.dataType` 必须是 `STRING`，
默认成 DTO 会让下游写节点按 DTO 处理。

## 3. 运行时证据

流程 `p6svc6sv01`：取流水号（方案 `ZxjContractNo`）→ 写 taskId，5 分钟一次。

```
09:46:00  HT2026111  source_table=SN
09:51:00  HT2026112  source_table=SN
09:56:00  HT2026113  source_table=SN
```

- 三次调用三次递增 → 服务真的被执行
- `ctp_serial_history` 同刻落记录（serial_value=HT2026111，scheme_id=-9200500489397925395）
- 值来自平台流水号组件，不是我们伪造的字符串

## 4. 流水号方案的两个服务端硬约束（2026-11-05 制造业全链暴露，逐层验证）

### 4.1 方案码必须 ≤ 20 字符

`getSerialNumber` 服务端校验 `serialSchemeCode` **1-20 字符**，超长直接拒：
「方案编码 个数必须在1和20之间」。坑在：平台为实体编码字段自动建的方案 code 是
「实体名前缀_id」（30+ 字符，如 `MfgProductionPl_5043588717645876680`），
`SELECT * FROM ctp_serial_scheme` 查得到、行也正常，**但经 AppService 取号必被拒**——
自动方案只供实体 Serial 字段（billCode）内部取号走（那条路不经过此校验，同一张
`ctp_serial_history` 都会落记录，别拿它当「此码可用」的证据）。
判据：取号前先 `SELECT LENGTH(code) FROM ctp_serial_scheme WHERE …`，>20 就自建短码方案。

### 4.2 自建方案（graphql `udcSerialSchemeCreateEasySchemePost`）有两个坏默认，建完必须修

接口：`POST /service/udc/graphql?udcSerialSchemeCreateEasySchemePost`，mutation
`graphqlLoader ($params0: udcSerialSchemeCreateEasySchemePostInputBody)`，入参
`UdcSerialSchemeCreateDto{hostAppName, code, name, appId, appGuid, id, guid}`，
返回 `data.data0.data.content` = 新方案 id。

1. **`appGuid` 传 "-1" 会落库成字面 '-1'**，取号报「数据不存在或无权限查看」。
   修：`UPDATE ctp_serial_scheme SET app_guid=<应用真实guid> WHERE code IN (…)`
   （真实 guid 从同应用已有方案行或 `udc_deploy_record.app_guid` 抄）。conn.py 默认只读，
   UPDATE 要加 `--write`。
2. **自动生成的号段 `is_flow=0`（非流水段）**，取号报「配置中没有流水号配置」——
   取号器按「流水段」找号段，找不到就报这个。修：`UPDATE ctp_serial_section SET is_flow=1
   WHERE serial_scheme_id IN (…)`。对照活样板（ZxjContractNo）：固定前缀段(type=0) +
   日期段(type=1, value=currentDate) + 流水段(type=3, is_flow=1)。

两层修完才会通。排障时错误信息逐层变化（长度→权限→配置）就是逐层靠近的信号，
别在一层上反复换方案。

## 5. 未覆盖

- 其它 starter 服务（file / enums / message）
- 多参数或复杂 DTO 入参
- 有副作用的服务（本例会消耗一个流水号，属可接受副作用）
