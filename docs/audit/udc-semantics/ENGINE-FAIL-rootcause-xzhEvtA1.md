# 检测引擎 FAIL 根因 — xzhEvtA1 零属性 DTO 触发 NPE

时间：2026-10-17 22:50 +08
发现者：main（独立复核 implementer RESULT 时定位）
证据等级：STATIC（CFR 反编译）+ LIVE（DB 实测 + 跨应用 sweep + 网关响应）

## 1. 现象

本应用（8704025620829192834）一致性检测：
- `udcApplicationSearchDetectionPost` → HTTP 200 `BOOT_0000`，`data.content = []`
- 同轮 `do/detection-state` → `status: FAIL`，
  `message: "Business Error[应用元数据处理类[DtoCodeMetaDataPostProcessor]执行异常: null]"`，`count=0`

即：**content 为空是引擎异常产物（假阴性），不是 02104 归零。**

跨应用 sweep（main 22:44 独立执行，8 应用）：
```
datamigration        FAIL count=0  Business Error[DtoCodeMetaDataPostProcessor 执行异常: null]
xiangmuguanlicopy    FAIL count=0  (message 空)
yunyewu              FAIL count=0  (message 空)
znxmglpt             EXECUTING     (进行中)
xiangmuguanli        FAIL count=0  (message 空)
faccounts            FAIL count=0  (message 空)
caihonglian          FAIL count=0  (message 空)
sanfangricheng       FAIL count=0  (message 空)
```
→ 仅本应用带 `DtoCodeMetaDataPostProcessor` message，其余 FAIL 无 message（另一个独立原因，非本域范围）。

## 2. 根因链（STATIC，CFR 0.152 反编译 udc-biz.jar）

### 2.1 抛出点
`com.seeyon.udc.autocode.metadata.config.DtoCodeMetaDataPostProcessor`
（`udc-biz.jar`，方法 `postProcessAppMetaDataContext(AppContext)`，@Order(5) @AutomaticCode）：

```java
// line 58
List dtoList = this.dtoService.selectListWithAttributeByAppId(appContext.getAppInfo().getId());
// line 72
Table udcDtoMetadataDtoTable =
    this.entityDtoDesignMetadataQueryService.selectDtoTableByDtoMap(dtoMap.values(), appContext.getAppInfo());
```

### 2.2 属性为 null 的确切位置
`com.seeyon.udc.entity.domain.service.DataTransferObjectService#getDtoListWithAttrByOriginDtoList`
（同 jar）：

```java
// line 283-285
List attributeDtos = this.attributeService.selectByDtoIds(dtoIds);
Map<Long, List<DtoAttributeDto>> attrsMap =
    attributeDtos.stream().collect(Collectors.groupingBy(DtoAttributeDto::getDtoId));
dtos.forEach(dto -> dto.setAttributes((List)attrsMap.get(dto.getId())));   // ← 无属性 DTO 得 null
```
**没有属性的 DTO → `attrsMap.get(id)` 返回 null → `setAttributes(null)`。**

### 2.3 NPE 落点
`com.seeyon.udc.metadata.query.EntityDtoDesignMetadataQueryService#selectDtoTableByDtoMap`（同 jar）：

```java
List dtoAttributeList = CollectionUtils.emptyIfNull(dtoCollection).stream()
    .flatMap(i -> i.getAttributes().stream())     // ← attributes == null → NullPointerException
    ...
```
聚合根被 `emptyIfNull` 保护，但**内层 `i.getAttributes()` 没有**。NPE 的 message 为 null
→ 与 `执行异常: null` 完全吻合（BusinessException 包装 NPE 时 message 取 null）。

## 3. 触发对象（LIVE，DB 实测 udc_test2）

```
udc_data_transfer_object WHERE id = -2693480158292981536
  id               = -2693480158292981536
  name             = xzhEvtA1
  caption          = 小爪事件A1
  description      = 小爪测试事件对象A1
  app_id           = 8704025620829192834
  is_meta_data     = 1
  is_root          = 1
  source           = 4
  source_id        = 0
  publish_state    = 1
  create_time      = 2026-10-16 23:04:58
  update_time      = 2026-10-16 23:04:58
  version          = 0
udc_dto_attribute WHERE dto_id = -2693480158292981536  → 0 行
```

**全平台零属性 DTO 分布（证明唯一性）：**
```
SELECT app_id, COUNT(*) FROM udc_data_transfer_object d
WHERE NOT EXISTS (SELECT 1 FROM udc_dto_attribute a WHERE a.dto_id=d.id) GROUP BY app_id
→ {app_id: 8704025620829192834, c: 1}
全平台 DTO 总数 1425，零属性仅此 1 条
```

→ 本应用独有 1 条零属性 DTO，恰好是 `xzh*` 前缀（本域 10-16 事件域实验残留）。
→ 引擎异常最早留证 18:44:13，而该 DTO 创建于 10-16 23:04（早于异常窗口，但引擎当时可能未跑到该 DTO，
   或该轮检测被其他因素短路；时间上不构成矛盾）。

## 4. 与 02104 的关系（关键结论）

**02104 是否归零，当前无法判定** —— 检测引擎在跑到实体规则前就 NPE 中断了。
`content: []` 既不是"02104=0"，也不是"02104=1"，而是**无测量结果**。

必须先修引擎，才能测 02104。

## 5. 修复动作

最小可逆：清理 `xzhEvtA1`（本域 10-16 事件实验残留，非客户业务数据，全字段已 dump 于本文件 §3，可重建）。
不重启 pod（共享环境，影响其他 8 域，且不解决本应用的数据层根因）。

## 6. 未验证 / 边界

- 其余 7 应用 FAIL（无 message）的根因**不在本域范围**，未调查。
- `znxmglpt` 当时 EXECUTING，状态未收敛。
- 修复后本应用引擎是否恢复，取决于零属性 DTO 是否为唯一 NPE 源 — 待 LIVE 复测。
