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

★ **DSL 层 attrs 写字段映射 dict，composer 转字段级 attrType 必须用 `field_attr`**
（2026-11-04）：`{"kind":"call_app_service","method_full":"…","attrs":{"serialSchemeCode":{"const":"HT"}}}`。
composer 里 dict → 列表时，字段级 attrType 要用 `dto_attributes()` 拉真实 DTO 字段表 +
`field_attr()` 构造完整 16-20 键。**手搓简化键（name/id/fullName/javaType/dataType/type/desc
8 键）会缺 `filterDataType/filterType/filterFullName/relationApp/refId/relationEntity`，
前端字段下拉全部红字「所选数据已失效，请重新选择」**（`field_attr` docstring 已记这个坑）。

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

## 4. 方案码（serialSchemeCode）的三个坑（2026-11-05 LIVE 三连）

1. **长度 1-20 校验**：平台按实体自动生成的长码方案（`MfgProductionPl_5043588717645876680`，34字符）传给 getSerialNumber 直接被拒「方案编码 个数必须在1和20之间」。必须自建 ≤20 字符短码方案。
2. **建方案入口**：`POST /service/udc/graphql?udcSerialSchemeCreateEasySchemePost`，body=UdcSerialSchemeCreateDto{hostAppName, code, name, appId, appGuid, id, guid}。坑：appGuid 传 '-1' → 运行时报「数据不存在或无权限查看」，必须传应用真实 guid。
3. **号段必须落应用库且 is_flow=1**：createEasyScheme 建的 scheme 主行会同步到应用库，但 **sections 不会同步** → 报「配置中没有流水号配置」。且 section 必须 `is_flow=1`（createEasyScheme 默认建 is_flow=0 的非流水段，同样报此错）。修复：UPDATE ctp_serial_section SET is_flow=1 + 把 section INSERT 到应用库（id 非自增须显式给）。scheme 缓存（LoadingCache）需重启运行时（deploy-normal）才失效。

LIVE 验证（21:40）：7 个短码方案 mfg*No 全部真实取号递增（0001→0002），po_code/plan_code/receipt_code 落库为流水号，不再写死。

## 5. 未覆盖

- 其它 starter 服务（file / enums / message）
- 多参数或复杂 DTO 入参
- 有副作用的服务（本例会消耗一个流水号，属可接受副作用）
