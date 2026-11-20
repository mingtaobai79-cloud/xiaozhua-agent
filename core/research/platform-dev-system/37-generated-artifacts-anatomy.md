# 37 · ★★★★★ 生成物真实内容解剖（LIVE 证据）

**证据来源**：`D:/software/hermes/cache/scratch/rendered_go/`（141 个真实渲染产物）
**证据等级：LIVE_RULE**

---

## 一、DAO —— 543 字节，一个空接口

```java
package com.example.demo.domain.dao;

import com.example.demo.domain.entity.Order;
import com.example.demo.dto.OrderDto;
import com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao;
import org.apache.ibatis.annotations.Select;
import org.springframework.stereotype.Component;
import java.util.Map;
import java.util.List;

/**
* 订单 dao 接口
*/
    public interface DemoOrderDao extends AbstractAllInOneBaseDao<Order>{
}
```

### ★★★★★ 三条硬结论

```
1. DAO 是**空接口**，零方法
2. 继承 AbstractAllInOneBaseDao<Entity>（泛型参数是**实体**，不是 DTO）
3. 类名 = {appNamePackage}{EntityName}Dao  →  DemoOrderDao
```

**⇒ 平台**不生成**任何 CRUD 方法签名到 DAO。所有能力来自 `AbstractAllInOneBaseDao` 的运行时实现。**
**⇒ 「生成器生成 DAO 的 CRUD 方法」是错的。**

---

## 二、MyBatis XML —— 246 字节，零条 SQL

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper PUBLIC
        "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.example.demo.domain.dao.DemoOrderDao">
</mapper>
```

### ★★★★★ 硬结论

```
只在 <mapper namespace> 里绑定 DAO 全名，**没有任何 <select>/<insert>/<update>/<delete>**
```

**⇒ 平台**完全不做**静态 SQL 生成。全部 SQL 由 `AbstractAllInOneBaseDao` 在运行时按元数据动态拼装。**
**⇒ 我之前「mybatis.xml 里有 SQL」的推断，实测为 0 条 —— 已推翻。**

---

## 三、DTO —— 7,193 字节，结构完整

### 3.1 类头

```java
@DtoInfo(value = "订单", isPublic = true,
         entity = "com.example.demo.domain.entity.Order",
         customs = {@Custom(properties = {
             @CustomAttribute(name = "entityId", value = "0")})})
public class OrderDto extends com.seeyon.udc.common.dto.BaseRootDto {

    private static final long serialVersionUID = "1L"L;

    @DtoAttribute(hidden = true, value = "忽略属性")
    @JsonIgnore
    public static String[] ignoreProperties = {""};
```

**★ 关键注解**
```
@DtoInfo        元数据载体：caption / isPublic / entity 全名 / customs
@DtoAttribute   字段元数据载体（每个字段一个）
@JsonIgnore     忽略字段
```
**★ 父类**：`com.seeyon.udc.common.dto.BaseRootDto`（根 DTO）/ `BaseDetailDto`（明细 DTO）

### 3.2 `deepCopy` —— 主子表递归复制

```java
public OrderDto deepCopy(OrderDto orderDto){
    OrderDto copyOrderDto = BeanCopier.copy(orderDto, OrderDto.class);
    List<OrderDetailDto> orderDetailDtoList = orderDto.getOrderDetailDtoList();
    if(CollectionUtils.isNotEmpty(orderDetailDtoList)){
        List<OrderDetailDto> copyOrderDetailDtoList = new ArrayList<>();
        for(OrderDetailDto orderDetailDto:orderDetailDtoList){
            OrderDetailDto copyOrderDetailDto = orderDetailDto.deepCopy(orderDetailDto);
            copyOrderDetailDtoList.add(copyOrderDetailDto);
        }
        copyOrderDto.setOrderDetailDtoList(copyOrderDetailDtoList);
    }
    return copyOrderDto;
}
```
**★ 子表命名规则（已从 DtoCodeUtil 反编译确认）**
```
子表 entityName = orderDetail
  → DTO 类名     OrderDetailDto
  → 列表变量名   orderDetailDtoList    (handleOneToManyEntityName4Dto = uncap + "DtoList")
  → getter       getOrderDetailDtoList (handleOneToManyCapEntityName4Dto = cap + "DtoList")
```

### 3.3 `toMap` —— DTO 转 Map（供动态 SQL / 表达式用）

```java
public Map<String,Object> toMap(){
    Map<String, Object> map = Maps.newHashMapWithExpectedSize(4);
    Object value = null;
    value = getId();
    map.put("id", Objects.isNull(value) ? value
            : com.seeyon.boot.starter.udcrt.util.UdcReflectUtil.bean2map(getId())); // LONG
    ...
    map.put("orderDetail", getOrderDetailDtoList().stream()
            .map(OrderDetailDto::toMap).collect(Collectors.toList()));
    return map;
}
```
**★ 每个字段都做 `Objects.isNull` 判断 + `UdcReflectUtil.bean2map` 转换**
**★ 子表用 `stream().map(Dto::toMap)` 递归**

### 3.4 `defaultValue` —— 系统函数默认值

```java
public static OrderDto defaultValue(){
    OrderDto dto = new OrderDto();
    dto.setOrderNo((String)SystemFunctionUtil.getSystemValueByFunc(""));
    dto.setAmount((BigDecimal)SystemFunctionUtil.getSystemValueByFunc(""));
    dto.setCreateDate((Date)SystemFunctionUtil.getSystemValueByFunc(""));
    return dto;
}
```
**★ 每个非主键字段都有 `SystemFunctionUtil.getSystemValueByFunc(func)` 调用**
**⇒ 默认值来自「系统函数」，不是硬编码。`func` 字符串来自元数据。**

### 3.5 字段声明

```java
@DtoAttribute(value = "订单号", example = "",
    customs = {@Custom(properties = {
        @CustomAttribute(name = "id", value = "1207111225"),
        @CustomAttribute(name = "guid", value = "1234293792"),
        @CustomAttribute(name = "useSnapshot", value = "false"),
        @CustomAttribute(name = "dataType", value = "STRING")})})
private STRING orderNo;
```

**★ 字段级元数据完整嵌入 `@CustomAttribute`**
```
id / guid / useSnapshot / dataType  —— 这 4 个是必备 CustomAttribute
```
**⚠ 注意：`private STRING orderNo` 的 `STRING` 是模板 bug 或我的模型问题**（应是 `String`）。
正常情况应为 `javaType`。待用真实元数据复核。

---

## 四、BaseService —— 21,981 字节（最大产物之一）

待解剖（下一步）。

---

## 五、AppServiceImpl —— 20,608 字节

待解剖。

---

## 六、★★★ 命名规则汇总（已实证）

| 产物 | 命名规则 | 实例 |
|---|---|---|
| Entity | `{Cap}{entityName}` | `Order` |
| DTO | `{Cap}{entityName}Dto` | `OrderDto` |
| 子表 DTO 列表变量 | `{uncap}{childName}DtoList` | `orderDetailDtoList` |
| 子表 getter | `get{Cap}{childName}DtoList` | `getOrderDetailDtoList` |
| DAO | `{appNamePackage}{Cap}{entityName}Dao` | `DemoOrderDao` |
| DAO 泛型 | `<Entity>` 不是 DTO | `AbstractAllInOneBaseDao<Order>` |
| AppService | `{Cap}{entityName}AppService` | `OrderAppService` |
| MyBatis namespace | DAO 全名 | `com.example.demo.domain.dao.DemoOrderDao` |

---

## 七、待验证

| 问题 | 状态 |
|---|---|
| `private STRING orderNo` 是否正确 | UNVERIFIED（疑似模型字段映射问题） |
| BaseService 生成的完整方法 | 待读产物 |
| AppServiceImpl 的完整实现逻辑 | 待读产物 |
| `AbstractAllInOneBaseDao` 的实际能力 | 待反编译 |
| 系统函数 `getSystemValueByFunc` 的参数来源 | UNVERIFIED |