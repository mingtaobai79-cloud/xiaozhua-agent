# 平台能力覆盖清单（v1）

> 生成时间：2026-11-17
> 数据来源：`udc-starter-lowcode-5.3.517.jar` + `boot-core-5.3.358.jar` CFR 反编译
> 证据等级：`VERIFIED_STATIC_SOURCE`（源码级）
> 用途：回答「平台已经覆盖哪些开发能力」，供 Agent 检索和开发者对照

---

## 0. 资产盘点

| 资产 | 路径 | 反编译产物 |
|---|---|---|
| `udc-starter-lowcode-5.3.517.jar` | `D:/repo/CHIT/com/seeyon/udc-starter-lowcode/5.3.517/` | **121 个 java** |
| `boot-core-5.3.358.jar` | `D:/repo/CHIT/com/seeyon/boot-core/5.3.358/` | **512 个 java** |
| 反编译工具 | `C:/Users/白明涛/AppData/Local/Temp/cfr.jar` | CFR 0.152 |
| 产物目录 | `D:/software/hermes/cache/scratch/lowcode-src` | — |
| | `D:/software/hermes/cache/scratch/bootcore-src` | — |

**⚠️ `boot-core` 本机最新是 5.3.358，不是 5.3.517。**
**⇒ `Ids` / `SnowflakeIDGenerator` / `NetAddressIdWorker` 三个类在各版本中字节数均为 4278，判断未变。**
**⇒ 但 `boot-core` 其他类可能存在版本差异，标注 `VERSION_CAVEAT`。**

---

## 1. lowcode 包结构（121 个类，按目录）

| 类数 | 包 | 职责 |
|---|---|---|
| **14** | `core` | **核心：EntityMeta / AttributeMeta / BaseCurdService / QueryService / UpdateService / EntityBeanContainer / EntityRelationHandler** |
| **13** | `callback` | **回调接口：全部扩展点** |
| **13** | `util` | 工具：`DtoConvertUtil` / `EntityMetaUtil` / `ReflectFieldUtil` |
| **12** | `dto` | DTO：`ApprovalContext` / `MapConditionDto` / `EntityChangeDto` / `AggEntityChangeDto` |
| **10** | `cache` | 缓存：`CacheAspect` / `EntityCacheManager` / Redis 相关 |
| 7 | `annotation` | 缓存注解：`@ECacheable` / `@ECachePut` / `@ECacheEvict` / `@RCacheable` / `@PriorityCache` / `@ENoCache` / `@MethodBizProxy` |
| 6 | `context` | `OperateContext`（操作上下文） |
| 6 | `helper` | `DtoFieldHelper` / `EntityEventHelper` / `EventContainer` |
| 4 | `disruptor` | 高性能队列（日志/事件异步） |
| 4 | `interceptor` | `EventBusMethodLogInterceptor` / `EventBusMethodPointcutAdvisor` |
| 4 | `processor` | `AppStartUpManager` / `AppStartUpProcessor` / `DataProcessor` / `EventHandlerBeanPostProcessor` |
| 4 | `service` | `BaseEntityCurdService` 等 |
| 4 | `visitor` | `DataVisitor` / `DataPreVisitor` / `DataSnapshotVisitor` / `DataMonitorVisitor` |
| 3 | `enums` | 枚举 |
| 3 | `exception/thrower` | `EntityExceptionThrower` |
| 2 | `api` / `config` / `exception` / `listener` / `log` | 杂项 |
| 1 | `appservice` / `aspect` | 单类 |

---

## 2. ★★★ 回调接口全表（13 个，全部扩展点）

**这是开发者介入平台行为的唯一合法入口。**

### 2.1 `MethodCallBack` —— 10 个方法（最重要）

```java
default public void beforeSelect(List<D> dtos)
default public void afterSelect(List<D> dtos)
default public void beforeCreate(List<D> dtos)
default public void middleCreate(List<D> dtos)                       ← create 链里的中间层
default public void afterCreate(List<D> dtos)
default public void beforeUpdate(List<D> dtos)
default public void afterUpdate(List<D> newDtoList, Map<Long,D> oldMap)   ← 带旧值
default public void beforeDelete(List<D> dtos)
default public void afterDelete(List<D> dtos)
default public D    getDefaultValue()                                ← ★ 默认值入口（接表达式）
```

**⇒ 全部是 `default` 方法 → 只实现需要的，不用全写。**
**⇒ `afterUpdate` 独有 `oldMap` 参数 → 更新时能拿到旧值。**
**⇒ `getDefaultValue()` 是表达式/默认值的接入点。**

### 2.2 `ApprovalCallBack`（单据审批，6 方法）

```java
void beforeApprovalCreate(...)
void beforeApprovalCreateValidate(...)      ← 校验阶段
void afterApprovalCreate(...)
void beforeApprovalUpdate(...)
void beforeApprovalUpdateValidate(...)
void afterApprovalUpdate(...)
```

**⇒ 单据的创建/更新各有「前置 + 前置校验 + 后置」三段。**

### 2.3 `ApprovalCallBackExt`（扩展版，6 方法，同名）

### 2.4 其他 callback

| 接口 | 方法数 | 方法名 |
|---|---|---|
| `PreCreateCallBack` | 1 | `preCreateBatch(List)` |
| `PreUpdateCallBack` | 1 | `preUpdateBatch(List)` |
| `PreCopyCallBack` | 1 | `preCopyBatch(...)` |
| `ValidateCallBack` | 1 | **`assertjsr303(...)`** ← JSR-303 校验 |
| `BillStateCallBack` | 1 | **`checkBillState(...)`** |
| `PermissionCallBack` | 2 | **`buildInitialValue(...)`** / **`requiredValidate(...)`** |
| `SecretCallBack` | 1 | `checkSecret(Collection)` |
| `EntityRuntimeLogCallBack` | **28** | `beginCreateLog` / `resetInsertAndOrderNoLog` / `beginPreCreateBatchLog` / `endePreCreateBatchLog` … |

**⇒ `PermissionCallBack.requiredValidate` 说明「必填校验」也在 callback 层，不是注解。**
**⇒ `PermissionCallBack.buildInitialValue` 是「初始值构建」，与 `getDefaultValue` 可能配合。**
**⇒ `EntityRuntimeLogCallBack` 28 个方法 → 运行时日志是细粒度埋点，可用来做审计。**

---

## 3. core 包（14 个类）

| 类 | 方法数 | 说明 |
|---|---|---|
| **`EntityMeta`** | **34** | 实体元数据（`getChildren` / `getEntityType` / `getAttributes` / `getFullName` / `getRelationType` / `getDtoListName` / `isSortField`）|
| **`AttributeMeta`** | **26** | 属性元数据（`getName` / `getDataType` / `getRealDataType` / `getMaskType` / `getCaption`）|
| **`BaseCurdService`** | **19** | 查询接口（default 方法） |
| **`EntityRelationHandler`** | **7** | 实体关系处理 |
| **`EntityBeanContainer`** | 6 | `findDao(Class)` / `findService(Class)` / `findDto(...)` |
| `QueryService` | 3 | 查询 |
| `UpdateService` | 8 | 更新 |
| `BaseService` | 2 | `getEntityClass()` |
| `AsyncTaskExecutor` | 4 | 异步任务 |
| `AsyncTaskExecutionListener` | 2 | 异步监听 |
| `DataTransferService` | 0 | 数据传输（Excel 导入） |

### 3.1 `BaseCurdService` 的 19 个方法（查询能力全集）

```java
List<D> selectListByCondition(String column, Object value, Sort sort)
List<D> selectByParentId(Long parentId)                              ← 默认按 orderNo 升序
List<D> selectByParentIdIgnoreSort(Long parentId)
List<D> selectByParentIds(Collection<Long> parentIds)
List<D> selectByParentIdsIgnoreSort(Collection<Long> parentIds)
int     selectCountByWrapper(Wrapper wrapper)
int     selectCountByConditions(Map<String,Object> map)
List<D> selectListByWrapper(Wrapper wrapper)
List<D> selectListByConditions(Map<String,Object> paramMap, Sort sort)
List<D> selectPageByWrapper(PageInfo pageInfo, Wrapper wrapper)
List<D> selectPageByConditions(PageInfo pageInfo, Map<String,Object> columnMap, Sort sort)
List<D> selectListByComplexConditions(Map<String,Object> map, Sort sort)
List<D> selectPageByComplexConditions(PageInfo pageInfo, Map<String,Object> map, Sort sort)
int     selectCountByComplexConditions(Map<String,Object> map)
List<D> selectListFuncByComplexConditions(Map<String,Object> paramMap, Sort sort, String funcName, List<String>...)
D       selectFuncByConditions(Map<String,Object> paramMap, Sort sort, String funcName, List<String>...)
List<D> selectListByDynamicConditions(Map<String,Object> paramMap, Sort sort)
List<D> selectListByDynamicConditions(List<SeeyonKeyMap> columnMap, Sort sort)
```

**★★ 重大发现：IN 查询自动分批**

```java
default public List<D> selectListByCondition(String column, Object value, Sort sort) {
    Object mapper = this.getMapper();
    if (this.selectExceedsOneThousandRecordsByInCondition(column, value)) {  // IN_ 前缀 + >1000 条
        List valueList = (List) value;
        if (CollectionUtils.size(valueList) > 9999) {
            throw BusinessException.message("条件IN查询数量超过9999条, 请检查设计是否合理!");
        }
        List partition = Lists.partition(valueList, 999);          // ★ 每批 999
        ArrayList totalList = new ArrayList();
        for (List segList : partition) {
            List segEntityList = EntityClassContext.withEntityClass(
                mapper, this.getEntityClass(),
                () -> mapper.selectListByCondition(column, segList, sort));
            totalList.addAll(segEntityList);
        }
        return BeanCopier.copyList(totalList, this.getDtoClass());
    }
    ...
}
```

**⇒ 用 `"IN_parentId"` 这种 `IN_` 前缀，平台会自动分 999 条一批，最多 9999 条。**
**⇒ 超 9999 条直接抛业务异常 → 这是硬限制。**
**⇒ 这是**开发者不写循环也能安全批量查**的平台能力。**

---

## 4. util 包（13 个类，核心 3 个）

### 4.1 `DtoConvertUtil`（15 个方法）

```java
// 字段重置（递归遍历）
resetInsertHandle(EntityMeta, DTO parentDto, BiConsumer<DTO,DTO>) : DTO
// 遍历
forEach(EntityMeta, DTO, Consumer<DTO>) : DTO
forEach(EntityMeta, List<DTO>, BiConsumer<EntityMeta,List<DTO>>) : void
// 转 Map
listToMap(EntityMeta, List) : Map<Long,D>
listToMap(EntityMeta, List, Consumer) : Map
listToMap(EntityMeta, List, Predicate) : Map
listToMap(EntityMeta, List, Consumer, BiConsumer, Predicate) : Map
defaultUpdateListToMap(EntityMeta, List) : Map          ← 更新用，含 throwActionTypeIfAbsent
mergeMapData(EntityMeta, Map, Map) : List
// 分组
groupByAction(List) : Map                               ← 按 ActionType 分组
// 其他
fixActionTypeByDFS(EntityMeta, List)                    ← DFS 修正 actionType
```

**★★ `listToMap` 有 ID 冲突检测：**

```java
Sets.SetView intersectionIds = Sets.intersection(dataMap.keySet(), listToMap.keySet());
if (CollectionUtils.isNotEmpty(intersectionIds)) {
    throw new BusinessException().addError("聚合根内id冲突:" + intersectionIds);
}
```

**⇒ 主子表里主表和子表 ID 重复会直接抛异常。**

### 4.2 `DtoFieldHelper`（17 个方法）★ 核心

| 方法 | 关键行为 |
|---|---|
| **`resetInsert(parentDto, subDto)`** | **生成主键 `Ids.gidLong()` + 回填 `parentId` + 设 actionType=INSERT** |
| `throwActionTypeIfAbsent(dto)` | actionType 为 null 直接抛；UPDATE 时 id 必须非空 |
| `setIdIfAbsent(dto)` | 只在 id 为 null 或 `NULL_ID` 时生成 |
| **`setParentIdIfAbsent(parentDto, dtoList)`** | 回填 parentId（含冲突重设 ID）|
| `setActionTypeIfAbsent(dto, type)` | 补默认 actionType |
| `setActionType(dto, type)` | 强制设 actionType |
| `resetChildNormal(dto)` | 子表置 NORMAL |
| `resetId(parentDto, subDto)` | 强制重生成 ID（复制场景）|
| `set1ToNDtoList(parentDto, entityMeta, mergedSubDtoList)` | 按 `RelationType` 处理 One2One / One2Many |
| **`setSubEntityOrderNo(entityMeta, dtoList)`** | **`orderNo = (i+1) * 10000`** |
| `diffDataByList(...)` | 聚合级变更差异 |
| `diffDataByMap(...)` | 实体级变更差异 |
| `extractAttrChange(...)` | 字段级差异（含 `__emptyFields`）|
| `isEmptyOrZero(obj)` / `isEmpty(obj)` | 空值判断（含 0、NONE、空集合）|
| `listEnableExtField(entityMeta)` | EXT 实体可用扩展字段 |
| `isContentField(attributeMeta)` | 判断 CONTENT 类型字段 |

### 4.3 `EntityMetaUtil`（9 个方法）

```java
forEachMeta(EntityMeta, Consumer<EntityMeta>) : void          ← 遍历实体树所有节点
toDtoClassMetaMap(EntityMeta) : Map<Class, EntityMeta>        ← DTO 类 → 元数据
```

---

## 5. ★★★ 主键生成（`boot-core`）

### 5.1 `Ids` 的 4 个生成方法

| 方法 | 底层 | 纯雪花？ | 可反解时间？ |
|---|---|---|---|
| **`Ids.gidString()`** | `generator.generateString()` → `nextId()` | ✅ | ✅ |
| **`Ids.gidLong()`** | `generator.generateLong()` → **`nextId() + 随机long`** | ❌ | ❌ |
| `Ids.uuidLong()` | `UUID.randomUUID().getMostSignificantBits()` | — | ❌ |
| `Ids.uuidAbsLong()` | UUID 取绝对值 | — | ❌ |

**⇒★★ `gidLong()` 加了 `ThreadLocalRandom.nextLong()`，位布局被打乱。**
**⇒ 平台实体主键用的是 `gidLong()` → 主键**不可反解时间、不单调递增、可能为负**。**

### 5.2 雪花位布局（`SnowflakeIDGenerator`）

```
epoch = 1596816000000  (2020-08-08 00:00:00 +08:00)
时间戳    40 位  bit 24-63   34.8 年 → 到约 2055 年
sequence   9 位  bit 15-23   0-511/毫秒
centerId   3 位  bit 12-14   0-7（系统属性 CENTER_ID）
workerId  12 位  bit  0-11   0-4095
```

### 5.3 workerId 来源

```java
String ip = IpUtils.getFirstNoLoopbackIPV4Address();
this.workerId = Ipv4Util.ipv4ToLong(ip) & 0xFFF;   // IP 低 12 位
```

**⇒ 不是配置，是从本机 IP 推导。容器化部署 IP 变 → workerId 变。**

### 5.4 `analyzeDate(Long id)`

```java
public static Date analyzeDate(Long id) {
    return NetAddressIdWorker.INSTANCE.analyze(id).getDate();
}
```

**⇒ 但这个方法对 `gidLong()` 的结果无效（位已打乱），只对 `gidString()` 有效。**

---

## 6. 扩展点全景（4 类）

### 6.1 回调接口（13 个，见第 2 节）

### 6.2 可覆写方法（6 个，`invokevirtual` 可覆写）

```
preCreateBatch / beforeCreate / afterBeforeEventCheck
middleCreate   / getMapper    / afterCreate
```

### 6.3 SPI / 处理器（processor 包）

| 类 | 职责 |
|---|---|
| `AppStartUpManager` | 应用启动管理 |
| `AppStartUpProcessor` | 应用启动处理（7 个方法） |
| **`DataProcessor`** | `dataProcess(OperateContext)` / `flowProcess(OperateContext)` |
| `EventHandlerBeanPostProcessor` | 事件 handler 自动注册 |

### 6.4 访问器（visitor 包）

```
DataVisitor           match(OperateContext) / visit(OperateContext)
DataPreVisitor
DataSnapshotVisitor
DataMonitorVisitor
```

**⇒ `OperateContext` 是贯穿 CRUD 全链的上下文，4 个 visitor 围绕它做拦截。**

### 6.5 监听器（listener 包）

```
OperateListener          onOperate(OperateContext)
DefaultOperateListener   （默认实现）
```

### 6.6 缓存注解（7 个）

```
@ECacheable    @ECachePut    @ECacheEvict
@RCacheable    @PriorityCache  @ENoCache
@MethodBizProxy
```

**⇒ 平台自带 Redis 缓存体系（`cache` 包 10 个类），不用自己接。**

---

## 7. 单据状态机字段规范（`IGNORE_FIELDS` 反推）

**每个业务动作都有「操作人 + 时间 + 原因 + 状态」四件套：**

| 动作 | 字段组 |
|---|---|
| **终止** | `terminatorId` / `terminateTime` / `terminateReason` / `terminateStatusType` |
| **取消终止** | `cancelTerminatorId` / `cancelTerminateTime` / `cancelTerminateReason` |
| **作废** | `nullifyId` / `nullifyTime` / `nullifyReason` / `nullifyStatusType` |
| **取消作废** | `cancelNullifyId` / `cancelNullifyTime` / `cancelNullifyReason` |
| **挂起** | `suspenderId` / `suspendTime` / `suspendReason` / `suspendStatusType` |
| **取消挂起** | `cancelSuspenderId` / `cancelSuspendTime` / `cancelSuspendReason` |
| **发送** | `sendState` / `caseSendTime` / `caseSender` / `caseSenderInstitution` / `caseSenderDepartment` / `caseSenderPost` |
| **流程** | `caseId` / `caseTitle` / `templateId` / `statusType` |
| **草稿** | `draft` |

**⇒ 直接照这个命名开发单据状态字段，与平台一致。**

---

## 8. 核心 5 类方法总计

| 类 | 方法数 |
|---|---|
| `BaseEntityCurdService` | **75** |
| `BaseCurdService` | 19 |
| `DtoConvertUtil` | 15 |
| `DtoFieldHelper` | 17 |
| `EntityMetaUtil` | 9 |
| **合计** | **135** |

---

## 9. 已明确的开发约束（可直接用）

### 9.1 主子表写入

```
1. DTO 必须带 actionType（null 直接抛异常）
   UPDATE 时 id 必须非空
2. 子表行必须带 actionType：
   INSERT → 新增
   UPDATE → 修改
   DELETE → 删除
   NORMAL → 不删不改
3. 主表和子表 ID 不能冲突（聚合根内 id 冲突会抛异常）
4. 主键由 Ids.gidLong() 在内存预生成，不依赖 DB 自增
5. 子表 parentId 由平台自动回填，不用手动设
```

### 9.2 查询

```
6. IN 查询用 "IN_字段名" 前缀 → 自动分批 999/批
7. 单次 IN 最多 9999 条，超了抛异常
8. selectByParentId 默认按 orderNo 升序
9. 子表 orderNo 平台按 (i+1)*10000 自动生成
```

### 9.3 扩展

```
10. 改主子表递归逻辑 → 做不到（recursiveCreate 是 private）
11. 只能通过：13 个 callback 接口 / 6 个可覆写方法 / visitor / listener
12. 单据审批必须走 ApprovalCallBack，不在 BaseEntityCurdService 里
13. 必填校验在 PermissionCallBack.requiredValidate，不是注解
```

---

## 10. 仍未覆盖（下一轮）

| 项 | 状态 |
|---|---|
| `recursiveUpdate` 内部实现 | 源码可读，未提取 |
| `create4Bpm` / `update4Bpm` 完整链 | 源码可读，未提取 |
| `EntityMeta` 34 个方法逐个用途 | 未展开 |
| `AttributeMeta` 26 个方法逐个用途 | 未展开 |
| 表达式与 `getDefaultValue()` 的衔接 | 未追 |
| `boot-core` 其他 512 个类 | 只用了 `Ids` 相关 3 个 |
