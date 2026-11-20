# 35 · ★★★★★ AppService 真实渲染产物（LIVE 证据）

**证据等级：LIVE_RULE**（用真实 FreeMarker 2.3.32 + jar 内真实模板 + 真实工具类渲染）

**渲染条件**
```
模板：autocode/JAVA/2.9/templates/entity/appservice.java.ftl（在 udc-biz-5.3.605.jar 内）
引擎：FreeMarker 2.3.32（真实 jar 渲染）
数据：udcCodeConfig（112 个真实工具类）+ table 元数据（1 主表 + 4 字段 + 1 子表）
产物：8,251 字节，38 个方法
```

---

## 一、平台为「普通实体」生成的 38 个 AppService 方法

```java
public interface OrderAppService {

    // ===== Excel 导入导出 =====
    ListResponse<ExcelImportResultDto> importExcel(SingleRequest<ExcelImportTransDto> dto);
    SingleResponse<String> exportExcel(SingleRequest<ExcelDto> request);

    // ===== 创建（4 种）=====
    SingleResponse<Long>    create(SingleRequest<OrderDto> request);
    SingleResponse<OrderDto> createWithResult(SingleRequest<OrderDto> request);
    SingleResponse<Integer> createBatch(SingleRequest<List<OrderDto>> request);
    SingleResponse<ResultDto> create4Bpm(SingleRequest<OrderDto> request);   ★ 单据专用

    // ===== 更新（5 种）=====
    SingleResponse<Integer> update(SingleRequest<OrderDto> request);
    SingleResponse<Integer> updateWithFields(SingleRequest<Map<String,Object>> request);  ★ 指定字段
    SingleResponse<OrderDto> updateWithResult(SingleRequest<OrderDto> request);
    SingleResponse<Integer> updateBatch(SingleRequest<List<OrderDto>> request);
    SingleResponse<ResultDto> update4Bpm(SingleRequest<OrderDto> request);    ★ 单据专用
    SingleResponse<ForceUpdateResultDto> forceUpdate(SingleRequest<OrderDto> request);  ★ 跳过校验强更

    // ===== 删除（3 种）=====
    SingleResponse<Integer> deleteById(SingleRequest<Long> request);
    SingleResponse<Integer> deleteByIds(SingleRequest<List<Long>> request);
    SingleResponse<Integer> deleteByComplexConditions(SingleRequest<Map<String,Object>> request);

    // ===== 批量根操作 =====
    SingleResponse<Integer> operateRootBatch(SingleRequest<List<OrderDto>> request);
    SingleResponse<Long>    copyAndInsert(SingleRequest<Long> id);     ★ 复制插入
    SingleResponse<OrderDto> runtimeCopy(SingleRequest<Long> id);     ★ 运行时复制

    // ===== 校验 =====
    SingleResponse<OrderDto> validate(SingleRequest<OrderDto> request);
    SingleResponse<OrderDto> getDefaultValue(SingleRequest<Void> request);        ★ 默认值
    SingleResponse<OrderDto> getCascadeDefaultValue(SingleRequest<Void> request); ★ 级联默认值
    SingleResponse<OrderDto> processingTemplateData(SingleRequest<OrderDto> request); ★ 模板数据

    // ===== 查询 - 按 ID（4 种）=====
    SingleResponse<OrderDto> selectById(SingleRequest<Long> request);
    ListResponse<OrderDto>   selectByIds(SingleRequest<List<Long>> request);
    SingleResponse<OrderDto> selectCascadeById(SingleRequest<Long> request);        ★ 带子表
    SingleResponse<OrderDto> selectCascadeById4Bpm(SingleRequest<BillSearchRequestDto> request);
    ListResponse<OrderDto>   selectCascadeByIds(SingleRequest<List<Long>> request);

    // ===== 查询 - 按条件（6 种）=====
    SingleResponse<Integer>  selectCountByConditions(SingleRequest<Map<String,Object>> request);
    PageResponse<OrderDto>   selectPageByConditions(PageRequest request);
    ListResponse<OrderDto>   selectListByConditions(ListRequest request);
    SingleResponse<OrderDto> selectCascadeByConditions(SingleRequest<QueryConditionDto> request); ★

    // ===== 查询 - 复杂条件（5 种）=====
    ListResponse<OrderDto>   selectListByComplexConditions(ListRequest request);
    PageResponse<OrderDto>   selectPageByComplexConditions(PageRequest request);
    SingleResponse<Integer>  selectCountByComplexConditions(SingleRequest<Map<String,Object>> request);
    ListResponse<OrderDto>   selectCascadeListByConditions(SingleRequest<QueryConditionDto> request);

    // ===== 聚合函数查询（2 种）=====
    SingleResponse<String> selectFuncByConditions(SingleRequest<AggSelectParamDto> request);       ★ SUM/AVG/MAX/MIN/COUNT
    SingleResponse<String> selectListFuncByComplexConditions(SingleRequest<AggSelectParamDto> request);

    // ===== 动态 SQL（3 种）=====
    PageResponse<OrderDto>  dynamicSelect(SingleRequest<ProxyParamDto> request);         ★
    PageResponse<OrderDto>  dynamicJoinSelect(SingleRequest<ProxyJoinParamDto> request); ★ 多表 JOIN
    SingleResponse<Integer> dynamicCountJoinSelect(SingleRequest<ProxyJoinParamDto> request);
}
```

---

## 二、★★★★★ 关键结构事实

### 2.1 所有方法都包在 `SingleRequest` / `ListRequest` / `PageRequest` 里

```java
SingleResponse<Long> create(SingleRequest<OrderDto> request);
                    ↑                    ↑
                 统一返回包装          统一入参包装
```

**★ 这是平台的「运输层」契约，不是业务 DTO 的一部分。**
```java
SingleRequest<T>   →  SingleResponse<R>
ListRequest        →  ListResponse<T>
PageRequest        →  PageResponse<T>
```
**来源：`com.seeyon.boot.transport.*`**

### 2.2 三档查询：Conditions / ComplexConditions / Dynamic
```
Conditions          →  Map<String,Object> 或 ListRequest（字段等值/区间）
ComplexConditions   →  同样 Map，但支持 OR / 嵌套条件
DynamicSelect       →  ProxyParamDto（运行时拼 SQL，最灵活）
DynamicJoinSelect   →  ProxyJoinParamDto（多表 JOIN）
```

### 2.3 「Cascade」= 带子表
```
selectById         →  只查主表
selectCascadeById  →  主表 + 所有子表（主子表完整树）
```

### 2.4 「4Bpm」= 单据流程专用
```
create4Bpm → 返回 ResultDto（而不是 Long）
update4Bpm → 返回 ResultDto
```
**⇒ 单据（Bill）走 BPM 时用 `4Bpm` 系列，普通 CRUD 用普通系列。**

### 2.5 Excel 双向集成内置
```
importExcel(SingleRequest<ExcelImportTransDto>) → ListResponse<ExcelImportResultDto>
exportExcel(SingleRequest<ExcelDto>)            → SingleResponse<String>
```
**⇒ 平台为每个实体**默认**生成 Excel 导入导出，不需要手写。**

---

## 三、生成这个接口的模板结构（真实源码）

`appservice.java.ftl` 的分段：
```freemarker
interface ${appNamePackage}${entityNameCap}AppService {
    <#-- 1. 导入 -->
    <#-- 2. 创建 -->
    <#-- 3. 更新 -->
    <#-- 4. 删除 -->
    <#-- 5. 查询 -->
    <#-- 6. 条件查询 -->
    <#-- 7. 聚合函数 -->
    <#-- 8. 动态SQL -->
    <#-- 9. Excel -->
}
```

**★ 重要：这是「普通实体」的方法集。**
平台用 `EntityCodeUtils.getDefAllMethodName()` / `getChildEntityMethodName()` /
`getThirdEntityDefMethodName()` 区分主实体/子实体/第三方实体的方法集
（见 30 号文档 6.2 节）。

---

## 四、待验证

| 问题 | 状态 |
|---|---|
| 子实体的方法集与主实体差多少 | UNVERIFIED（需渲染子实体） |
| 单据（Bill）是否多出 submit/audit 等方法 | UNVERIFIED（需 Bill 模板） |
| `dynamicSelect` 的 ProxyParamDto 结构 | UNVERIFIED（需反编译 DTO） |
| 38 个方法是否全平台一致 | UNVERIFIED（需对比真实工程） |