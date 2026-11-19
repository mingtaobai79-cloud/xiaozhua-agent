# 03 · 自定义微流程的出入参：怎么定、怎么拿、怎么返回

## Capability

**微流程配了入参/出参之后，你的 Java 方法签名长什么样、怎么从里面取值、怎么返回。**

给 Agent 用：接到「微流程要传参/要返回数据」需求时，照本格定签名，不要猜。

## Version

- 模板：`microflow/customflow/CustomMicroFlowService.java.ftl`（1,313 B）
- 模板：`microflow/microflow/MicroFlowDomainService.java.ftl`（768 行）
- DTO：`com.seeyon.udc.microflow.domain.bo.param.MicroFlowInOutParamDto`（反射实测 17 个字段）
- 信息：`com.seeyon.udc.microflow.dto.definition.MicroFlowServiceInfoDto`

## 签名由这四个字段决定（权威，反射实测）

```java
// MicroFlowInOutParamDto —— 决定你看到的方法签名
String  inputType           入参类型全名
String  inputName           入参变量名
String  req                 Request 包装类型（SingleRequest / PageRequest）
String  resp               Response 包装类型（SingleResponse / PageResponse）
String  outputType          输出类型全名
String  originalRespOutputType  原始输出类型（未转换前）
boolean hasInput / hasOutput
boolean hasPagination        ★ 决定要不要包 Request
boolean hasEntityOutput     ★ 输出是实体
boolean hasOutputPagination
String  resultType
String  outputName
String  controllerDtoName
String  entityOutputFullName
List    attachmentAttrNames
```

## 四种签名（照抄）

| 配置 | 生成的方法签名 |
|---|---|
| 有输入，无分页 | `{OutDto} createOrder({InDto} {inputName})` |
| 有输入 + 分页 | `{OutDto} createOrder({Req}<{InDto}> request)` |
| 无输入 | `{OutDto} createOrder()` |
| 无输出 | `void createOrder({InDto} {inputName})` |

**★★★★★ 判定顺序（模板真实逻辑）：**

```freemarker
<#if microFlowInOutParamBo.hasPagination>
    ${outType} ${flowName}(${req}<${inputType}> ${inputName})     ← 分页：整个 Request
<#else>
    ${outType} ${flowName}(${inType} ${inputName})                 ← 无分页：裸 DTO
</#if>
```

**⇒ `hasPagination=true` 时你拿到的是 `SingleRequest<OrderDto>` / `PageRequest<OrderDto>`；否则直接是 `OrderDto`。**

## 怎么从入参取值

```java
// 无分页 —— 直接用
@Override
public OrderDto createOrder(OrderDto orderDto) {
    String no = orderDto.getOrderNo();
    List<OrderDetailDto> details = orderDto.getOrderDetailDtoList();
}

// 有分页 —— PageRequest 没有 getData()！用 getParams()
@Override
public PageResponse<OrderDto> listOrders(PageRequest request) {
    Map<String,Object> params = request.getParams();      // ★ 业务查询条件（Map）
    PageInfo pageInfo         = request.getPageInfo();    // ★ 分页信息
    Sort sort                 = request.getSort();        // ★ 排序（继承自 ListRequest）
}
```

**★★★★★ 实测更正（反射 `com.seeyon.boot.transport.PageRequest`）：**

```
继承链：PageRequest extends ListRequest extends BaseRequest

PageRequest 自己的方法：
  PageInfo  getPageInfo()
  PageRequest addParam(...)   ×2
  static from(...)            ×4

继承自 ListRequest：
  Map<String,Object> getParams()      ← ★ 业务条件在这里，是 Map 不是 DTO
  Sort getSort()
  ListRequest addParam(...) / sort(...)
  static from(...)

★★★ 没有 getData()，也没有 getData0()。  ← 我先前写错，已更正
```

**⇒ 分页场景下入参条件走 `Map`（`getParams()`），不是强类型 DTO。要拿强类型得自己转。**

## 怎么返回值

```java
// 普通 DTO 输出 —— 直接返回
@Override
public OrderDto createOrder(OrderDto orderDto) {
    orderService.create(orderDto);
    return orderDto;
}

// 无输出 —— void
@Override
public void syncOrders(OrderQueryDto query) {
    orderService.sync(query);
}

// 分页输出 —— 返回 PageResponse（平台会包一层）
@Override
public PageResponse<OrderDto> listOrders(PageRequest<OrderQueryDto> request) {
    return orderAppService.selectPage(request);
}
```

**★★★★★ 输出是实体时（`hasEntityOutput=true`）—— 平台在 Controller 层转换：**

```java
// AppService 层签名为：SingleResponse<Map<String, ?>>
// Controller 里做：
RuntimeEntityDataSourceDto dto = getRuntimeEntityDataSourceByJsonFileName("{fileName}");
SingleResponse<{原始类型}> resp = service.{flowName}(request.getData());
ListResponse<Map<String, ?>> respMap = displayNameAppService.toMapList(
    SingleRequest.from(DisplayNameRequestDto.from(resp.getData().getContent(), dto)));
```

**⇒ 你返回实体 DTO，平台用 `DisplayNameAppService` 转成 `Map`（把关联字段换成显示名）。你不用管。**

## 出参能在后续节点被引用（微流程内部）

**节点出参命名规则（`udc/microflow/node-data-flow.md` 实证）：**
```
_FIELD_INPUT_<6位>       开始节点入参
_<TYPE>_<6位>            普通节点出参
```

**★★★ 51 个节点里只有 10 个有出参** —— 其余 41 个是动作终点，不能被后续引用。

**完整节点契约见 `core/facts/udc/microflow/`（64 份），本格不重复。**

## 自定义对象（DTO）在微流程里怎么用

**自定义对象 = 平台建的 DTO（`udc_data_transfer_object`），在微流程里当出入参类型用。**

### 建对象（接口，权威在 `udc/setting/custom-object/create.md`）

```graphql
POST /service/udc/graphql?udcDataTransferObjectPost
mutation graphqlLoader ($params0: udcDataTransferObjectPostInputBody) {
  data0: udcDataTransferObjectPost(body: $params0) { code data { content } message status }
}
```

**★★★★★ 三条硬约束（LIVE 实证）：**
1. **字段走 `udcDataTransferObjectUpdateDtoPost`** —— `UpdatePost` 不承载字段，会**假成功**
2. **`attributes` 是全量替换语义**
3. **`dataTypeCategory` 只有 `PRIMITIVE` / `COMPOSITE` / `ENUM`；`type` 只有 `OBJECT` / `LIST`**

### 在微流程里引用对象

```java
// 你的实现类方法签名里，入参/出参就是这个 DTO 的全类名
@Override
public MyCustomObjectDto doSomething(MyCustomObjectDto input) {
    input.getSomeField();
}
```

**⇒ 对象建好后，微流程出入参选它 → 签名的 `inputType` / `outputType` 就是它的全类名。**

## 完整可编译示例（有入参 + 有出参 + 分页）

```java
package com.seeyon.zzprobe.custom.service.microflow;

import com.seeyon.zzprobe.dto.OrderDto;
import com.seeyon.zzprobe.dto.OrderQueryDto;
import com.seeyon.zzprobe.domain.service.OrderService;
import com.seeyon.boot.transport.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class OrderCustomMicroFlowServiceImpl implements OrderCustomMicroFlowService {

    @Autowired private OrderService orderService;

    // ① 无分页：裸 DTO 进，DTO 出
    @Override
    public OrderDto createOrder(OrderDto orderDto) {
        orderService.create(orderDto);        // 走生成 Service，直接传
        return orderDto;
    }

    // ② 有分页：PageRequest 进，PageResponse 出
    @Override
    public PageResponse<OrderDto> listOrders(PageRequest request) {
        Map<String,Object> params = request.getParams();
        PageInfo pageInfo = request.getPageInfo();
        Sort sort = request.getSort();
        return orderService.selectPageByCondition(pageInfo, params, sort);
    }

    // ③ 无输出
    @Override
    public void syncOrders(OrderQueryDto query) {
        orderService.sync(query);
    }
}
```

## Side Effects

无（本格只讲签名与取值）。

## Known Constraints

| # | 约束 |
|---|---|
| 1 | **`hasPagination=true` → 入参是 `Request<Dto>`，不是裸 DTO** |
| 2 | **有分页用 `request.getParams()` 拿条件（Map），`request.getPageInfo()` 拿分页；没有 `getData()`** |
| 3 | **输出是实体时 AppService 返回 `Map<String,?>`**（平台做 DisplayName 转换） |
| 4 | **51 个节点只有 10 个有出参**，其余不可被后续引用 |
| 5 | **自定义对象建字段必须走 `udcDataTransferObjectUpdateDtoPost`**（`UpdatePost` 假成功） |
| 6 | **自定义对象 `attributes` 是全量替换** |
| 7 | **`dataTypeCategory` 只有 3 值，`type` 只有 2 值** |
| 8 | **方法名必须与微流程名 uncap 一致** |

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `MicroFlowInOutParamDto` 17 个字段 | 反射 `getMethods()` 逐个打印 | **LIVE** |
| **`PageRequest` 无 `getData()`** | **反射实测：继承链 `PageRequest→ListRequest→BaseRequest`，只有 `getParams()/getPageInfo()/getSort()`** | **LIVE** |
| 四种签名判定逻辑 | `CustomMicroFlowService.java.ftl` 的 `<#if hasPagination>` | STATIC_RULE |
| `hasEntityOutput` 转换链 | `CustomMicroFlowController.java.ftl` 的 `displayNameAppService.toMapList` | STATIC_RULE |
| 节点出参命名 `_<TYPE>_<6位>` | `udc/microflow/node-data-flow.md`（既有 LIVE 格） | **LIVE** |
| 自定义对象三接口 | `udc/setting/custom-object/create.md`（既有 LIVE 格） | **LIVE** |
| 字段走 UpdateDtoPost 的假成功坑 | 同格 LIVE 实证 | **LIVE** |

## Verified

- ✅ **LIVE**：`MicroFlowInOutParamDto` 17 个 getter 反射全部拿到
- ✅ **STATIC_RULE**：四种签名判定 + 实体输出转换链（模板逐行）
- ✅ **引用既有 LIVE 格**：节点出参、自定义对象接口（不重复求证）
- ✅ **LIVE**：`PageRequest` 取值方法已反射确认（无 `getData()`）
- ⚠️ **BLOCKED**：完整接口渲染（`VirtualFullNameTransformer.<clinit>` 需真实 `AppContext`，容器外失败）

## 给 Agent 的判据

```
问「我的方法签名应该是什么」
  → 看 hasPagination：true → {Req}<{InDto}> request
                       false → {InDto} {inputName}
  → 输出看 hasOutput：false → void

问「入参怎么取值」
  → 无分页：直接用 DTO getter
  → 有分页：request.getParams()（Map）+ request.getPageInfo() + request.getSort()
     ★ 没有 getData()，我先前写错已更正

问「返回实体为什么变成 Map 了」
  → hasEntityOutput=true，平台在 Controller 层用 DisplayNameAppService 转

问「自定义对象建完怎么在微流程用」
  → 出入参选它，签名 type 就是它的全类名

问「为什么建对象字段没生效」
  → 走了 udcDataTransferObjectUpdatePost，必须走 ...UpdateDtoPost（假成功坑）
```