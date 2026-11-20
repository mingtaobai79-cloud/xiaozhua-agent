# 38 · ★★★★★ Service 三层架构真实解剖（LIVE 证据）

**证据来源**：`rendered_go/entity__baseservice.java.ftl.out`（21,981 B）+
`rendered_go/entity__appserviceImpl.java.ftl.out`（20,608 B）
**证据等级：LIVE_RULE**

---

## 一、★★★★★ 三层架构（实证）

```
┌─────────────────────────────────────────────────────────┐
│  Controller                                             │
│      ↓ 调                                                 │
│  OrderAppServiceImpl  implements OrderAppService         │
│      ↑ 注入 private OrderService domainService           │
│      ↓ 纯委托：domainService.xxx(request.getData())      │
│  OrderService extends <BaseService 父类>                 │
│      ↑ 注入 private DemoOrderDao demoDao                 │
│      ↓ demoDao.selectPageByConditions(...)               │
│  DemoOrderDao extends AbstractAllInOneBaseDao<Order>     │
│      ↓ 运行时动态拼 SQL                                   │
│  MyBatis → DB                                           │
└─────────────────────────────────────────────────────────┘
```

### ★★★ 关键事实：AppServiceImpl 是**纯委托层**

```java
public class OrderAppServiceImpl implements OrderAppService {

    @Autowired
    private OrderService domainService;      ← 字段名固定 "domainService"

    @Override
    public SingleResponse<Integer> createBatch(SingleRequest<List<OrderDto>> request) {
        return SingleResponse.from(domainService.createBatch(request.getData()));  ← 一行
    }

    @Override
    public SingleResponse<Long> create(SingleRequest<OrderDto> request) {
        domainService.createWithResult(request.getData());
        return SingleResponse.from(request.getData().getId());   ← 写回 id 后取
    }
}
```

**⇒ 业务逻辑**全在** `OrderService`（BaseService），AppServiceImpl 只做：
1. 解包 `SingleRequest.getData()`
2. 调 `domainService.xxx()`
3. 包 `SingleResponse.from()`**

**⇒ 扩展业务时必须改 `OrderService`，不是 `OrderAppServiceImpl`。**

---

## 二、★★★★★ 注解栈（40 个方法的真实注解统计）

| 注解 | 次数 | 作用 |
|---|---|---|
| `@Override` | 40 | — |
| `@AppServiceOperation` | 39 | 操作元数据：`value`（中文描述）+ `returnValue`（返回说明） |
| `@Transactional` | 16 | `rollbackFor = Exception.class` |
| `@RecycleSerialNumber` | 12 | **回收流水号**（删除/更新时） |
| `@AppService.ValidationGroup` | 9 | `Create.class` / `Update.class` 分组校验 |
| `@Autowired` | 3 | 注入 |
| `@Lazy` | 1 | 延迟注入 |
| `@Custom` | 2 | 自定义属性 |

### 注解栈真实样例

```java
@Override
@Transactional(rollbackFor = Exception.class)
@AppService.ValidationGroup(value = AppService.ValidationGroup.Update.class)
@AppServiceOperation(value = "更新订单聚合实体数据", returnValue = "订单修改成功条数")
@RecycleSerialNumber
public SingleResponse<Integer> update(SingleRequest<OrderDto> request) {
    return SingleResponse.from(domainService.update(request.getData()));
}
```

**★ 固定顺序**：`@Override` → `@Transactional` → `@ValidationGroup` → `@AppServiceOperation` → `@RecycleSerialNumber`

**★ `@RecycleSerialNumber` 出现 12 次**，是所有「会改数据」的方法（update/delete/batch）都有
→ **平台自动回收流水号**（serial number recycle），不需要手写。

---

## 三、★★★★★ BaseService（OrderService）的 25 个方法

### 3.1 十个生命周期钩子（★ 最重要的扩展点）

```java
public void beforeSelect(List<OrderDto> DtoList)                          ← 查询前
public void afterSelect(List<OrderDto> DtoList)                           ← 查询后
public void beforeCreate(List<OrderDto> DtoList)                          ← 创建前
public void middleCreate(List<OrderDto> DtoList)                          ← 创建中
public void afterCreate(List<OrderDto> DtoList)                           ← 创建后
public void beforeUpdate(List<OrderDto> DtoList)                          ← 更新前
public void afterUpdate(List<OrderDto> DtoList, Map<Long,OrderDto> oldDtoMap)  ← 带旧值！
public void beforeDelete(List<OrderDto> DtoList)                          ← 删除前
public void afterDelete(List<OrderDto> DtoList)                           ← 删除后
public void preCreateBatch(List<OrderDto> DtoList)                        ← 批量创建前
public void preCopyBatch(List<OrderDto> DtoList)                           ← 批量复制前
public void preUpdateBatch(List<OrderDto> DtoList)                         ← 批量更新前
```

**★★★★★ `afterUpdate` 带 `oldDtoMap`（旧值 Map）—— 这是「改前改后对比」的官方入口。**

### 3.2 表达式相关钩子（4 个）

```java
public void beforeExecuteDefaultValueExpression(List<OrderDto> DtoList)
public void afterExecuteExpression(List<OrderDto> DtoList)
public void afterBeforeEventCheck(List<OrderDto> DtoList)
public void resolveDefaultValueNotAllowedModify(OrderDto orderDto)
```

### 3.3 DTO 转换与工具（5 个）

```java
public static OrderDto deepCopy(OrderDto orderDto)
public static void dto2dto(OrderDto from, OrderDto to)
public static OrderDto dto2dto(OrderDto from)
public void handleEntityDefaultValue(OrderDto from)
protected void resolveDefaultValueDesensitizationAndEncryption(List<OrderDto> orderDtoList)  ← 脱敏加密
```

### 3.4 核心 CRUD（5 个）

```java
public PageData<OrderDto> selectPageByConditions(PageInfo pageInfo, Map<String,Object> columnMap, Sort sort)
public OrderDto getDefaultValue()
public OrderDto getCascadeDefaultValue(String cascadeDefaultValueKey)
public void assertjsr303(OrderDto orderDto)      ← 内部调 check(orderDto)
```

### 3.5 ★★★★ `selectPageByConditions` 的完整实现（分页真相）

```java
public PageData<OrderDto> selectPageByConditions(PageInfo pageInfo,
                                                 Map<String, Object> columnMap,
                                                 Sort sort) {
    PageData<Order> pageData = demoDao.selectPageByConditions(pageInfo, columnMap, sort);
    PageData<OrderDto> pageDataDto = pageData.to(OrderDto.class);   ← ★★★ 转换
    return pageDataDto;
}
```

**★★★★★ 三条关键事实：**
```
1. DAO 返回的是 PageData<Entity>，不是 DTO
2. 用 PageData.to(OrderDto.class) 做实体→DTO 批量转换
3. 入参是 (PageInfo, Map<String,Object> columnMap, Sort) —— 不是 QueryConditionDto
```

### 3.6 ★★★★★ 六个 `@Autowired` 注入（真实依赖）

```java
@Autowired private BusinessEventHelper  businessEventHelper;   ← 业务事件
@Autowired private DemoOrderDao         demoDao;               ← DAO 字段名 = {uncap appName}Dao
@Autowired private ExpressionEvaluator  expressionEvaluator;   ← ★ 表达式求值器
@Autowired private MessageRepository    messageRepository;     ← i18n 消息
@Autowired private UdcSerialConfigService serialConfigService;  ← 流水号
@Autowired private OrderDetailService   orderDetailService;    ← ★ 子表 Service（自动注入！）
```

**★★★★★ `OrderDetailService` 被自动注入 —— 主子表的子表 Service 是自动依赖。**
**⇒ 主子表操作时直接调 `orderDetailService`，不用手动查子表。**

---

## 四、★★★★★ OrderService 的类声明

```java
@Service
@Slf4j
public class OrderService extends <OrderDto>{   ← ⚠ 父类模板变量为空（我的模型缺 superService）
```

**正常应为**：`extends AbstractOrderService` 或 `BaseService<Order, OrderDto>`
**⇒ 待用真实 `superService` 变量复核（UNVERIFIED）**

---

## 五、★★★★★ 完整调用链（从 AppService 到 DB）

```
HTTP/微流程
   ↓
OrderAppServiceImpl.createBatch(SingleRequest<List<OrderDto>>)
   ↓ request.getData()
OrderService.createBatch(List<OrderDto>)             [继承自父类]
   ↓ 钩子：preCreateBatch → beforeCreate → ...
   ↓ ExpressionEvaluator 计算表达式字段
   ↓ 校验（assertjsr303）
   ↓ BeanCopier / dto2entity 转换
DemoOrderDao.insertBatch(...)                         [AbstractAllInOneBaseDao]
   ↓ 动态拼 SQL（按元数据）
MyBatis → DB
   ↓ 返回
OrderService 钩子：afterCreate → 事件发布（businessEventHelper）
   ↓
AppServiceImpl: SingleResponse.from(结果)
```

---

## 六、待验证

| 问题 | 状态 |
|---|---|
| `OrderService extends <对什么>` | UNVERIFIED（superService 变量缺失） |
| `AbstractAllInOneBaseDao` 的实际方法 | 待反编译 |
| `PageData.to()` 的转换实现 | 待反编译 |
| `ExpressionEvaluator` 的接口 | 待反编译 |
| `@RecycleSerialNumber` 的行为 | 待反编译 |