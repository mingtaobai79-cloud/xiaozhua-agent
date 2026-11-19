# 04 · UDC 生成物的方法速查：注入之后能调什么

## Capability

**回答「我 `@Autowired` 了 `OrderService` / `OrderAppService`，然后能调哪些方法、传什么、拿回什么」。**

给 Agent 用：写自定义微流程时，**先来本格挑方法**，再去 01/02 看怎么注入。
不要猜方法名 —— 本格全部来自模板原文与字节码。

**本格与 02 的分工：02 讲「怎么注入 / 包路径 / Request 包装」；本格讲「有哪些方法」。**

## Version

| 来源 | 版本 |
|---|---|
| `{E}Service`（`BaseService` 继承链） | `udc-starter-lowcode-5.3.605.jar` javap |
| `{E}AppService` 模板 | `autocode/JAVA/2.9/templates/entity/appservice.java.ftl`（361 行） |
| `{E}Service` 钩子模板 | `autocode/JAVA/2.9/templates/entity/baseservice.java.ftl`（1279 行） |

## 一、三个层次，别用错

```
{E}Service        extends BaseEntityCurdService<{E}Dto>
                    ↑ 继承 QueryService + UpdateService（CRUD 全在这）
                    ↓ 自己覆写钩子（beforeCreate / afterUpdate ...）

{E}AppService     facade 接口，40 个方法，全部包 SingleRequest/PageResponse
                    ↑ 走 Dubbo + AOP + 事务 + 权限
```

| 我要 | 用 | 为什么 |
|---|---|---|
| 写业务逻辑、批量、事务内组合 | **`{E}Service`** | 直接传 DTO，无包装，能覆写钩子 |
| 跨模块 / 对外 / 要平台 AOP | **`{E}AppService`** | 带权限校验、操作日志、AppService 事务 |
| 只想查几条 | **`{E}Service`** | `selectListByConditions` 最省事 |

**⇒ 自定义微流程里 90% 用 `{E}Service`。** 只有要给别的应用调、或需要权限/日志时用 `{E}AppService`。

---

## 二、`{E}Service` 的 CRUD（来自 `UpdateService` / `QueryService`，全部实测字节码）

### 2.1 写（`UpdateService`）

```java
int create({E}Dto dto);                              // 建
int createBatch(List<{E}Dto> list);                   // 批量建
int update({E}Dto dto);                              // 改（发事件）
int updateNoEvents({E}Dto dto);                       // 改（不发事件）
int updateBatch(List<{E}Dto> list);                   // 批量改
int updateWithFields(Map<String,Object> fields);       // 按字段 map 改（必须含 id）
int deleteById(Long id);                             // 删
int deleteByIds(Collection<Long> ids);                // 批量删
```

**全部返回 `int` = 影响行数。** 不返回 DTO —— 要拿改后的对象用 `selectById` 重查。

**★★★★★ 三条：**

| # | 事实 |
|---|---|
| 1 | **`update` 会发事件，`updateNoEvents` 不发** —— 见 `transaction-beforeupdate-semantics.md` |
| 2 | **`updateWithFields` 的 Map 必须含 `id`**，否则抛「实体id不能为空」 |
| 3 | **`deleteById` 是物理删除还是逻辑删除取决于实体配置**，不假设 |

### 2.2 读（`QueryService` + `BaseCurdService`）

```java
// —— 按 id ——
{E}Dto          selectById(Long id);
List<{E}Dto>    selectByIds(Collection<Long> ids);
Enum            selectBillStatusById(Long id);         // 只取单据状态

// —— 按条件（Map，不是 DTO）——
List<{E}Dto>    selectListByConditions(Map<String,Object> cond, Sort sort);
PageData<{E}Dto> selectPageByConditions(PageInfo pageInfo, Map<String,Object> cond, Sort sort);
int             selectCountByConditions(Map<String,Object> cond);

// —— 单列精确匹配（最常用，别写成全表扫描）——
List<{E}Dto>    selectListByCondition(String column, Object value, Sort sort);

// —— 按父 id（子表专用）——
List<{E}Dto>    selectByParentId(Long parentId);
List<{E}Dto>    selectByParentIds(Collection<Long> parentIds);

// —— Wrapper（MyBatis 风格）——
List<{E}Dto>    selectListByWrapper(Wrapper wrapper);
PageData<{E}Dto> selectPageByWrapper(PageInfo pageInfo, Wrapper wrapper);

// —— 复杂条件（支持 or / in / 子查询）——
List<{E}Dto>    selectListByComplexConditions(Map<String,Object> cond, Sort sort);
PageData<{E}Dto> selectPageByComplexConditions(PageInfo p, Map<String,Object> cond, Sort sort);
int             selectCountByComplexConditions(Map<String,Object> cond);

// —— 动态条件（前端列筛选那套）——
List<{E}Dto>    selectListByDynamicConditions(Map<String,Object> cond, Sort sort);
List<{E}Dto>    selectListByDynamicConditions(List<SeeyonKeyMap> cond, Sort sort);

// —— 聚合（sum/max/count 单值）——
String          selectFuncByConditions(Map<String,Object> cond, Sort sort,
                                       String func, List<String> fields);
String          selectListFuncByComplexConditions(Map<String,Object> cond, Sort sort,
                                                  String func, List<String> fields);
```

**★★★★★ 选哪个（决策表）：**

| 场景 | 用 |
|---|---|
| 知道主键 | `selectById` |
| **一个字段精确匹配**（单号/编码） | **`selectListByCondition("orderNo", no, null)`** ← 最省事 |
| 多条件且都是等值 | `selectListByConditions(map, sort)` |
| 条件含 or / like / in / 区间 | `selectListByComplexConditions` |
| 前端表格列筛选 | `selectListByDynamicConditions` |
| 子表按主表 id 拿 | `selectByParentId(parentId)` |
| 要 sum/max | `selectFuncByConditions(...)` |

**⚠️ `selectListByConditions` 的 Map key 是 `snake_case` 列名还是 DTO 属性名，取决于实现；先小样本验一次，别批量跑。**

### 2.3 `PageData` 怎么取值（不是 PageResponse）

```java
PageData<{E}Dto> page = orderService.selectPageByConditions(pageInfo, cond, sort);

page.getContent();       // List<{E}Dto>  → 空则是空列表，不是 null
page.getTotal();         // long         总条数
```

**★ `PageData` 是 `{E}Service` 层的返回；`PageResponse` 是 `{E}AppService` 层的。两者别混。**

---

## 三、`{E}Service` 的可覆写钩子（`baseservice.java.ftl` 原文）

**这些是 `public` 方法，你继承 `{E}Service` 后覆写即可 —— 这是最干净的干预点。**

```java
// —— 查 ——
public void beforeSelect(List<{E}Dto> dtoList);
public void afterSelect(List<{E}Dto> dtoList);

// —— 建 ——
public void preCreateBatch(List<{E}Dto> dtoList);      // ★ 最早
public void beforeCreate(List<{E}Dto> dtoList);
public void middleCreate(List<{E}Dto> dtoList);
public void afterCreate(List<{E}Dto> dtoList);

// —— 改 ——
public void preUpdateBatch(List<{E}Dto> dtoList);      // ★ 最早，对象已 merge 完整
public void beforeUpdate(List<{E}Dto> dtoList);
public void afterUpdate(List<{E}Dto> dtoList, Map<Long, {E}Dto> oldDtoMap);

// —— 删 ——
public void beforeDelete(List<{E}Dto> dtoList);
public void afterDelete(List<{E}Dto> dtoList);

// —— 默认值 / 表达式 ——
public void beforeExecuteDefaultValueExpression(List<{E}Dto> dtoList);
public void afterExecuteExpression(List<{E}Dto> dtoList);
public void handleEntityDefaultValue({E}Dto dto);
public {E}Dto getDefaultValue();
public {E}Dto getCascadeDefaultValue(String key);

// —— 校验 ——
public void assertjsr303({E}Dto dto);
public void resolveDefaultValueNotAllowedModify({E}Dto dto);
public void afterBeforeEventCheck(List<{E}Dto> dtoList);

// —— 工具（static）——
public static {E}Dto deepCopy({E}Dto dto);
public static void    dto2dto({E}Dto from, {E}Dto to);
```

**★★★★★ 执行顺序（改数据要在 `pre*` 里）：**

```
preCreateBatch → beforeCreate → middleCreate → [写库] → afterCreate
preUpdateBatch → beforeUpdate → [写库] → afterUpdate
```

**`preUpdateBatch` 是最佳改数据点** —— 此时 DTO 已被 merge 补全为完整对象，且早于写库（详见第 7 格）。

**⚠️ 覆写 `{E}Service` 要让它被 Spring 替换**：生成的是 `@Service class OrderService extends BaseEntityCurdService`，
你要继承它并加 `@Service` + `@Primary`，或者用 `@Autowired(required=false)` 的替换模式 —— **具体见 01 的机制，别直接 `new`。**

---

## 四、`{E}AppService` 的 40 个方法（模板原文）

### 4.1 写（全部包 `SingleRequest`）

```java
SingleResponse<Long>    create(SingleRequest<{E}Dto> request);
SingleResponse<{E}Dto>  createWithResult(SingleRequest<{E}Dto> request);   // ★ 拿回完整对象
SingleResponse<Integer> createBatch(SingleRequest<List<{E}Dto>> request);

SingleResponse<Integer> update(SingleRequest<{E}Dto> request);
SingleResponse<{E}Dto>  updateWithResult(SingleRequest<{E}Dto> request);  // ★ 拿回完整对象
SingleResponse<Integer> updateBatch(SingleRequest<List<{E}Dto>> request);
SingleResponse<Integer> updateWithFields(SingleRequest<Map<String,Object>> request);

SingleResponse<Integer> deleteById(SingleRequest<Long> request);
SingleResponse<Integer> deleteByIds(SingleRequest<List<Long>> request);
SingleResponse<Integer> deleteByComplexConditions(SingleRequest<Map<String,Object>> request);

// BPM 专用
SingleResponse<ResultDto> create4Bpm(SingleRequest<{E}Dto> request);
SingleResponse<ResultDto> update4Bpm(SingleRequest<{E}Dto> request);

// 其他
SingleResponse<Integer> operateRootBatch(SingleRequest<List<{E}Dto>> request);
SingleResponse<Long>    copyAndInsert(SingleRequest<Long> id);
SingleResponse<{E}Dto>  runtimeCopy(SingleRequest<Long> id);
SingleResponse<{E}Dto>  validate(SingleRequest<{E}Dto> request);          // 只校验不落库
SingleResponse<ForceUpdateResultDto> forceUpdate(SingleRequest<{E}Dto> request);
```

**★★★ `createWithResult` / `updateWithResult` 是 AppService 独有的 —— 拿回带 id、带默认值的完整对象，比 `create` 好用。**

### 4.2 读

```java
SingleResponse<{E}Dto>   selectById(SingleRequest<Long> request);
ListResponse<{E}Dto>     selectByIds(SingleRequest<List<Long>> request);
SingleResponse<{E}Dto>   selectCascadeById(SingleRequest<Long> request);      // ★ 带子表
ListResponse<{E}Dto>     selectCascadeByIds(SingleRequest<List<Long>> request);
SingleResponse<{E}Dto>   selectCascadeByConditions(SingleRequest<QueryConditionDto> request);
ListResponse<{E}Dto>     selectCascadeListByConditions(SingleRequest<QueryConditionDto> request);

ListResponse<{E}Dto>     selectListByConditions(ListRequest request);
PageResponse<{E}Dto>     selectPageByConditions(PageRequest request);
SingleResponse<Integer>  selectCountByConditions(SingleRequest<Map<String,Object>> request);

ListResponse<{E}Dto>     selectListByComplexConditions(ListRequest request);
PageResponse<{E}Dto>     selectPageByComplexConditions(PageRequest request);
SingleResponse<Integer>  selectCountByComplexConditions(SingleRequest<Map<String,Object>> request);

// 动态 / 聚合
PageResponse<{E}Dto>     dynamicSelect(SingleRequest<ProxyParamDto> request);
PageResponse<{E}Dto>     dynamicJoinSelect(SingleRequest<ProxyJoinParamDto> request);
SingleResponse<Integer>  dynamicCountJoinSelect(SingleRequest<ProxyJoinParamDto> request);
SingleResponse<String>   selectFuncByConditions(SingleRequest<AggSelectParamDto> request);
SingleResponse<String>   selectListFuncByComplexConditions(SingleRequest<AggSelectParamDto> request);
```

**★★★ `selectCascadeById` vs `selectById` 的区别：cascade 版本会把子表一起带回来。
要完整单据用 cascade，只要主表用 `selectById`（更快）。**

### 4.3 导入导出 / 默认值

```java
ListResponse<ExcelImportResultDto> importExcel(SingleRequest<ExcelImportTransDto> request);
SingleResponse<String>             exportExcel(SingleRequest<ExcelDto> request);
SingleResponse<{E}Dto>             getDefaultValue(SingleRequest<Void> request);
SingleResponse<{E}Dto>             getCascadeDefaultValue(SingleRequest<Void> request);
SingleResponse<{E}Dto>             processingTemplateData(SingleRequest<{E}Dto> request);
```

---

## 五、`{E}Dao` —— 一般别直接用

```java
{appNamePackage}{E}Dao   extends BaseDao
```

**⇒ `{E}Service` 已经把 Dao 能力包好了。直接调 Dao 会绕过事件、钩子、权限。
只有 Service 没暴露的能力（特殊 SQL）才降到 Dao，且用 `EntityClassContext.withEntityClass` 包一层。**

---

## 六、完整可用示例

```java
package com.seeyon.zzprobe.custom.service.microflow;

import com.seeyon.zzprobe.domain.service.OrderService;
import com.seeyon.zzprobe.dto.OrderDto;
import com.seeyon.zzprobe.dto.OrderDetailDto;
import com.seeyon.boot.transport.PageData;
import com.seeyon.boot.transport.PageInfo;
import com.seeyon.boot.transport.Sort;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Map;

@Service
public class OrderCustomMicroFlowServiceImpl implements OrderCustomMicroFlowService {

    @Autowired private OrderService orderService;      // ★ 用 Service 层

    @Override
    public OrderDto createOrder(OrderDto dto) {

        // ① 查重（单列精确匹配，最省事）
        List<OrderDto> exist = orderService.selectListByCondition(
                "orderNo", dto.getOrderNo(), null);
        if (!exist.isEmpty()) {
            dto.setId(exist.get(0).getId());        // 走更新
            orderService.update(dto);
            return orderService.selectById(dto.getId());
        }

        // ② 建
        orderService.create(dto);

        // ③ 回读完整对象（含平台生成的 id / 默认值）
        return orderService.selectById(dto.getId());
    }

    // 分页查询
    public PageData<OrderDto> listOrders(PageInfo pageInfo, Map<String,Object> cond) {
        return orderService.selectPageByConditions(pageInfo, cond, null);
    }

    // 子表
    public List<OrderDetailDto> details(Long orderId) {
        // 主子表在 DTO 层是 {child}DtoList，随 cascade 一起回来
        OrderDto order = orderService.selectById(orderId);
        return order.getOrderDetailDtoList();
    }
}
```

---

## 七、Side Effects

| 方法 | 副作用 |
|---|---|
| `create` / `createBatch` | 写库、发 Before/AfterCreate 事件、触发默认值表达式 |
| `update` | 写库、发 Before/AfterUpdate 事件（**`updateNoEvents` 不发**） |
| `deleteById(s)` | 删库、发 Before/AfterDelete 事件 |
| `selectById` | 无（但会触发 `beforeSelect` / `afterSelect` 钩子） |
| `validate` | **不落库**，只跑校验 |
| `forceUpdate` | **绕过乐观锁强制写** —— 慎用 |

## 八、Known Constraints

| # | 约束 |
|---|---|
| 1 | **`{E}Service` 的写方法返回 `int`（行数），不返回 DTO**；要对象就 `selectById` 重查 |
| 2 | **`{E}AppService` 的方法全部要包 `SingleRequest` / `ListRequest` / `PageRequest`** |
| 3 | **`{E}Service` 返回 `PageData`，`{E}AppService` 返回 `PageResponse`** —— 两个不同的类 |
| 4 | **`updateWithFields` 的 Map 必须含 `id`** |
| 5 | **`update` 发事件，`updateNoEvents` 不发** |
| 6 | **`selectListByConditions` 的 Map key 类型未统一验证**（列名 vs 属性名），先小样本验 |
| 7 | **覆写 `{E}Service` 要能被 Spring 替换**（`@Primary` 或替换模式），别 `new` |
| 8 | **`forceUpdate` 绕过乐观锁**，生产慎用 |
| 9 | **别直接调 Dao** —— 绕过事件/钩子/权限 |

## 九、Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `UpdateService` 8 个写方法签名 | `javap -p BaseCurdService/UpdateService`（`udc-starter-lowcode-5.3.605.jar`） | **VERIFIED_STATIC_BYTECODE** |
| `QueryService` / `BaseCurdService` 20 个读方法 | 同上 javap 逐行 | **VERIFIED_STATIC_BYTECODE** |
| 40 个 `{E}AppService` 方法 | `entity/appservice.java.ftl` 361 行逐行读完 | **STATIC_RULE** |
| 24 个 `{E}Service` 钩子 | `entity/baseservice.java.ftl` 1279 行 `grep public` | **STATIC_RULE** |
| 继承链 `{E}Service → BaseEntityCurdService → BaseCurdService → QueryService + UpdateService` | javap class header | **VERIFIED_STATIC_BYTECODE** |

## 十、Verified

- ✅ **VERIFIED_STATIC_BYTECODE**：`UpdateService` / `QueryService` / `BaseCurdService` 全部方法签名（javap 逐个）
- ✅ **STATIC_RULE**：`appservice.java.ftl` 40 个方法、`baseservice.java.ftl` 24 个钩子（模板原文）
- ⚠️ **UNVERIFIED**：`selectListByConditions` 的 Map key 是列名还是 DTO 属性名
- ⚠️ **UNVERIFIED**：覆写 `{E}Service` 的真实替换机制（需一次真实生成 + 启动验证）

## 十一、给 Agent 的判据

```
问「我注入了 OrderService，能调什么」
  → CRUD：create/createBatch/update/updateBatch/updateNoEvents/deleteById/deleteByIds
  → 查：selectById/selectByIds/selectListByCondition/selectListByConditions
        /selectPageByConditions/selectByParentId/selectListByWrapper
  → 全部见本格 §二

问「建完怎么拿到 id」
  → Service 层：create 返回 int，id 在 dto 里（平台回写）或 selectById 重查
  → AppService 层：用 createWithResult（直接返回 DTO）

问「改一条单号匹配的记录」
  → selectListByCondition("orderNo", no, null) → 改 → update

问「要完整单据含子表」
  → AppService.selectCascadeById 或 DTO.get{Child}DtoList()

问「更新前改数据在哪改」
  → 覆写 {E}Service.preUpdateBatch(List<{E}Dto>)，最早且对象已完整
  → 详见 transaction-beforeupdate-semantics.md

问「校验但不想落库」
  → AppService.validate

问「分页怎么拿总数」
  → Service: PageData.getTotal() / getContent()
  → AppService: PageResponse.getData().getTotal()

问「能直接调 Dao 吗」
  → 尽量别。Service 已包装事件/钩子/权限，Dao 会绕过它们
```