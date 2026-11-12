# standard-product｜平台传输层 transport 用法（环境无关）

> 本格只讲**包内怎么用**，不涉及任何具体工程/环境。
> 适用：任何基于该平台的 Java 扩展代码（客开 extend、标品插件、AppService 实现）。

分级：`VERIFIED_STATIC_BYTECODE`（javap + cfr 双路，见 §8）。

## 1. Capability

平台所有跨层调用的**统一包装协议**。出入参不是裸对象，而是这几个包装类：

| 语义 | 请求侧 | 响应侧 |
|---|---|---|
| 单对象 | `SingleRequest<T>` | `SingleResponse<T>` |
| 列表 | `ListRequest` / `ListDtoRequest` | `ListResponse<T>` |
| 分页 | `PageRequest` / `PageDtoRequest<T>` | `PageResponse<T>` |
| 分页元信息 | `PageInfo` | `PageData<T>` / `PageScan*` |
| 排序 | `Sort`（`Sort.Order` / `Sort.Direction`） | — |

不证：各业务接口对哪个包装类的偏好（那是各域契约的事）；也不证运行期序列化细节。

## 2. Version

- `com.seeyon:boot-core`（transporter 包 `com.seeyon.boot.transport`）
- 本格签名取自 5.3.358；`transport` 包跨 5.3.x 稳定（同族构件均是同一主版本线）

## 3. Input

- jar：`com.seeyon/boot-core/<ver>/boot-core-<ver>.jar`
- 抽取命令（环境无关，只给 artifact 坐标）：
  `extract_jar_symbols.py --jar <boot-core jar> --include com/seeyon/boot/transport/ --javap <javap> --cfr <cfr.jar> --limit 200 --emit <out>`
- ⚠ `--limit` 要 ≥ 实际类数：该包实测 33 个类，按字母序取前 30 会**漏掉 `SingleRequest`/`SingleResponse`/`Sort`**
  （字母序靠后）——实测踩过，是本仓同类缺陷的第 3 次复现。

## 4. Required

无前置（纯静态读 jar）。

## 5. Execution

逐类 javap + cfr 双路抽取，按类名归并签名。见 §8。

## 6. Side Effects

只读 jar。

## 7. Known Constraints（API 形态，逐字取自字节码）

### 7.1 `SingleRequest<T>` —— 单对象请求

```java
public class SingleRequest<T> extends BaseRequest {
    public static <T> SingleRequest<T> from(T dto);
    public void check();
    public T getData();
    public void setData(T data);
}
```

### 7.2 `SingleResponse<T>` —— 单对象响应（★ 两层取值）

```java
public class SingleResponse<T> extends BaseResponse {
    public static <T> SingleResponse<T> from(T dto);
    public static <T> SingleResponse<T> ok();
    public SingleResponse buildProcessingResponse();
    public SingleData<T> getData();          // ← 返回 SingleData，不是 T
    public void setData(SingleData<T> data);
}
public class SingleData<T> implements Serializable {
    public static <T> SingleData<T> from(T data);
    public T getContent();                   // ← 真正的值在这一层
    public void setContent(T content);
}
```

⇒ **取值必须两层**：`resp.getData().getContent()`。
写 `resp.getData().getId()` 或 `resp.getData() <= 0` 都编译不过。

### 7.3 `ListResponse<T>` —— 列表响应（同样是两层）

```java
public class ListResponse<T> extends BaseResponse {
    public static <T> ListResponse<T> from(List<T> dtoList);
    public ListResponse buildProcessingResponse();
    public ListData<T> getData();            // ← ListData
    public void setData(ListData<T> data);
}
public class ListData<T> implements Serializable {
    public static <T> ListData<T> from(List<T> data);
    public List<T> getContent();             // ← List<T> 在这层
    public void setContent(List<T> content);
}
```

### 7.4 `ListRequest` —— 列表请求（条件 + 排序）

```java
public class ListRequest extends BaseRequest {
    public static ListRequest from();
    public static ListRequest from(Map<String, Object> params);
    public static ListRequest from(Map<String, Object> map, Sort sort);   // ★ 第二参是本包的 Sort
    public ListRequest addParam(String paramKey, Object paramValue);
    public ListRequest sort(Sort sort);
    public Map<String, Object> getParams();
    public Sort getSort();
}
```

⚠ 二维签名里没有第二个重载接受 Spring 的 Sort —— 只有**本包 `com.seeyon.boot.transport.Sort`**。
把 `org.springframework.data.domain.Sort` 传进去是编译期错误。

### 7.5 `Sort` —— 排序（本包自有类型）

```java
public class Sort implements Serializable, Iterable<Order> {
    public Sort by(String... properties);
    public Sort by(Direction direction, String... properties);
    public Sort by(List<Order> orders);
    public Sort by(Order... orders);
    public boolean isSorted();
    public boolean isUnsorted();
    public List<Order> getOrders();
    public Iterator<Order> iterator();
}
```
嵌套类型：`Sort.Order`、`Sort.Direction`。

### 7.6 分页三件套

```java
public class PageInfo implements Serializable {
    public int getPageSize();      public void setPageSize(int);
    public int getPageNumber();    public void setPageNumber(int);
    public int getPages();         public void setPages(int);
    public int getTotal();         public void setTotal(int);
    public boolean isNeedTotal();  public void setNeedTotal(boolean);
    public boolean isNeedMore();   public void setNeedMore(boolean);
}

public class PageRequest extends ListRequest {          // ← 继承 ListRequest，故 addParam 可用
    public static PageRequest from();
    public static PageRequest from(PageInfo pageInfo);
    public static PageRequest from(PageInfo pageInfo, Map<String, Object> map);
    public static PageRequest from(PageInfo pageInfo, Map<String, Object> map, Sort sort);
    public PageRequest addParam(String paramKey, Object paramValue);
    public PageInfo getPageInfo();
}

public class PageDtoRequest<T> extends BaseRequest {    // ← 泛型版，params 是强类型 DTO
    public static <T> PageDtoRequest<T> from(PageInfo pageInfo, T params);
    public static <T> PageDtoRequest<T> from(PageInfo pageInfo, T params, Sort sort);
    public T getParams();
    public Sort getSort();
    public PageInfo getPageInfo();
}

public class PageResponse<T> extends BaseResponse {
    public static <T> PageResponse<T> from(PageData<T> pageData);
    public PageData<T> getData();          // ← PageData<T>
}
```

⇒ 分页请求二选一：**Map 版** `PageRequest`（配 `PageInfo` + `Map`），
或 **DTO 版** `PageDtoRequest<T>`（配 `PageInfo` + 强类型 DTO）。不要自己拼 `{page,size}`。

### 7.7 `BaseResponse` —— 响应基类（成功判定在这层）

```java
public class BaseResponse implements Serializable {
    public boolean success();
    public boolean failure();
    public boolean processing();
    public BaseResponse buildResponse(Exception e);
    public int getStatus();     public String getCode();
    public String getMessage(); public String getTraceId();
}
```

⇒ 判定成功用 `success()` 或 `getStatus()`，排障带 `getTraceId()` 与 `getCode()`。
`BaseRequest` 基类只提供 `toString()`；`BaseDto` 另有 `check()` / `setValidate(boolean)` / `isValidate()`。

### 7.8 构造响应统一用静态工厂，不要 new

三个响应类都提供 `from(...)` 静态工厂（`SingleResponse.from(dto)` / `ListResponse.from(list)` /
`PageResponse.from(pageData)`），`SingleResponse` 另有 `ok()`。
响应侧开到「处理中」用 `buildProcessingResponse()`。

## 8. Evidence

```
① 路径  docs/audit/artifacts/extension-surface-20261029/batch2/boot-core.json（整包 507 类 / 3783 方法）
        （33 类 / 195 方法，javap+cfr 双路；文件内只有 artifact 名与版本，无工程/环境信息）
② 复现  uv run --no-project python tools/core/platform/extract_jar_symbols.py \
          --jar "<按 Maven 坐标 com.seeyon:<artifact>:<ver> 解析出的 jar>" \
          --include com/seeyon/boot/transport/ \
          --javap <javap 原生路径> --cfr <cfr.jar> --limit 200 \
          --emit <out.json>
③ 校验  复核三件事：摘要行 `classes=33 with_symbols=33 routes=['javap','cfr']`；
        本格每个签名都能在 out.json 的 classes[].symbols.methods[] 里逐字找到；
        本格引用的类名都在 classes[].symbols.name 里（含 SingleRequest/SingleResponse/Sort）。
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 33 类 195 方法签名 | `VERIFIED_STATIC_BYTECODE`（javap+cfr 双路） |
| `SingleResponse`/`ListResponse` 两层取值 | `VERIFIED_STATIC_BYTECODE`（`getData()` 返回类型逐字） |
| `ListRequest` 只接受本包 `Sort` | `VERIFIED_STATIC_BYTECODE`（重载签名里无 Spring Sort） |
| `PageRequest extends ListRequest` / `PageDtoRequest` 泛型版 | `VERIFIED_STATIC_BYTECODE`（extends 子句逐字） |
| 编译通过 | **UNVERIFIED**（未编译） |
| 运行期序列化行为 | 不属本格 |

## 铁律

- 出入参一律套 `SingleRequest`/`SingleResponse`/`ListRequest`/`ListResponse`，不要自造返回结构。
- 响应取真实值要两层：`SingleResponse.getData()` 得 `SingleData<T>` 再 `.getContent()`；`ListResponse` 同理得 `ListData<T>`。
- `Sort` 用 `com.seeyon.boot.transport.Sort`（含 `Sort.Order`/`Sort.Direction`），不是 Spring 的 `Sort`。
- 分页请求二选一：`PageRequest`（`PageInfo`+`Map`）或 `PageDtoRequest<T>`（`PageInfo`+强类型 DTO），不要自拼 `{page,size}`。
- 成功判定用 `BaseResponse.success()`/`getStatus()`，排障带上 `getTraceId()` 与 `getCode()`。
- 响应构造用静态工厂 `from(...)`/`ok()`，不要 new；「处理中」用 `buildProcessingResponse()`。
- 抽取这类包时 `--limit` 必须 ≥ 类总数，否则按字母序漏掉靠后的类（实测漏过 `SingleRequest`/`SingleResponse`/`Sort`）。
