# standard-product｜AppService 调用约定与框架能力（环境无关）

> 本格只讲**包内怎么用**。不涉及任何具体应用/工程/环境。
> 适用：任何调用平台 AppService、或自己实现 AppService 的扩展代码。

分级：`VERIFIED_STATIC_BYTECODE`（javap + cfr 双路，见 §8）。

## 1. Capability

回答两件事：

- **怎么调**平台 AppService（方法命名与出入参的固定成套关系）
- 自己实现 AppService 时**框架已经替你做了什么**（幂等 / 事务 / 异常翻译 / 上下文）

不证：各业务方法的具体语义与校验（那是各域契约）；也不证运行期 AOP 织入顺序。

## 2. Version

- `com.seeyon:boot-starter-appservice`（框架侧）、`com.seeyon:udc-facade`（AppService 接口面示例）
- 签名取自 5.3.358 / 5.3.517

## 3. Input

- jar 坐标与包前缀：
  - 框架：`boot-starter-appservice`，`com/seeyon/boot/starter/appservice/`
  - 接口面示例：`udc-facade`，`com/seeyon/udc/api/`
- 命令：`extract_jar_symbols.py --jar <jar> --include <包前缀> --javap <javap> --cfr <cfr.jar> --limit 200 --emit <out>`

## 4. Required

无前置（纯静态读 jar）。

## 5. Execution

逐接口取方法签名，按「动词 → 出入参成套形态」归纳。见 §7。

## 6. Side Effects

只读 jar。

## 7. Known Constraints

### 7.1 AppService 方法的出入参是固定成套的（照抄，不要自创）

从接口面实测归纳出的成套关系（右侧为实测签名形态）：

| 语义 | 方法名（实测） | 签名 |
|---|---|---|
| 新建单个 | `create` | `SingleResponse<Long> create(SingleRequest<Dto>)` ← 返回新 id |
| 批量新建 | `createBatch` | `SingleResponse<Integer> createBatch(SingleRequest<List<Dto>>)` ← 返回影响行数 |
| 更新单个 | `update` | `SingleResponse<Integer> update(SingleRequest<Dto>)` |
| 批量更新 | `updateBatch` | `SingleResponse<Integer> updateBatch(SingleRequest<List<Dto>>)` |
| 按 id 删 | `deleteById` | `SingleResponse<Integer> deleteById(SingleRequest<Long>)` |
| 按 id 批删 | `deleteByIds` | `SingleResponse<Integer> deleteByIds(SingleRequest<List<Long>>)` |
| 按 id 查 | `selectById` | `SingleResponse<Dto> selectById(SingleRequest<Long>)` |
| 按 id 批量查 | `selectByIds` | `ListResponse<Dto> selectByIds(SingleRequest<List<Long>>)` |
| 条件分页 | `selectPageByCondition` | `PageResponse<Dto> selectPageByCondition(PageRequest)` |
| 条件列表 | `selectListByCondition` | `ListResponse<Dto> selectListByCondition(ListRequest)` |

三条要点：

- **入参恒为 `SingleRequest<T>`**：即使 T 是 `Long` / `List<Long>` / `Dto` / `List<Dto>`，也要包一层。
- **返回值类型编码语义**：写操作回 `Integer`（影响行数）或 `Long`（新 id）；读操作回 `Dto` / `List<Dto>`。
  「返回 Integer 的 update 回 0」即没有命中任何行，不要当成异常。
- **批量是一个方法，不是循环调用单个**：批量走 `SingleRequest<List<Dto>>`。

### 7.2 ★ 多参数方法是「多个 `SingleRequest` 平铺」，不是打包成一个

实测（注意第二/三参数也是 `SingleRequest`，只有 `Sort` 是裸的）：

```java
ListResponse<AttributeDto> selectListByTerm(SingleRequest<Long> entityId,
                                            SingleRequest<String> keyword,
                                            Sort sort);

SingleResponse<EntityDto> selectByName(SingleRequest<Long> appId,
                                       SingleRequest<String> name);

ListResponse<EntityDto> selectListByConditions(SingleRequest<Map<String, Object>> params,
                                               Sort sort);
```

⇒ 写在调用方时是 `service.selectByName(SingleRequest.from(appId), SingleRequest.from(name))`。
**不要**把它们塞进一个 DTO，也不要只包第一个参数。

### 7.3 框架替你做的四件事（自己实现 AppService 时不要重写）

#### 幂等

```java
public class CtpIdempotent extends BaseComponentEntity {
    public String getCommandId();   public String getBeanName();
    public String getMethodName();  public String getParam();
    public String getResult();      public IdempotentStatusEnum getStatus();
    public Date getExecuteTime();
}
public class CtpIdempotentService implements ApplicationListener<ModuleUnloadEvent> {
    public boolean create(CtpIdempotent entity);
    public void update(CtpIdempotent entity);
    public CtpIdempotent selectById(Long id);
    public CtpIdempotent selectOneByCondition(Map paramMap);
    public boolean timeOutCheck(CtpIdempotent idempotent);
    public void addIdempotentBean(Object target, String beanName);
    public String getIdempotentBeanName(Object target);
    public void removeCache(ClassLoader classLoader);
}
```

配套切面：`IdempotentAnnotationAdvisor` + `IdempotentMethodInterceptor`；
幂等记录按 `commandId / beanName / methodName / param / result / status / executeTime` 落库。

#### 事务

`TransactionMethodInterceptor` + `TransactionMethodLogAdvisor` —— 注解式，不要手写 `TransactionTemplate` 包一层。

#### 异常翻译

```java
public interface ExceptionHandler<T extends BaseResponse, EX extends Throwable> {
    void handle(ExceptionContext<?> context, EX throwable);
}
public class ExceptionHandlers implements InitializingBean {
    public void addHandler(ExceptionHandler<?> handler);
    public boolean handle(ExceptionContext<?> context, Throwable throwable);
    public boolean handle(ExceptionContext context, Throwable throwable, Class<?> throwableClazz);
}
public class ExceptionContext<T extends BaseResponse> {
    public Object getRequest();  public T getResponse();
}
```

已内置的处理器族：`BusinessExceptionHandler` / `RequestCheckExceptionHandler` / `RpcExceptionHandler` /
`ThrowableExceptionHandler`。数据库方言异常解析器：`DBExceptionParser`（接口）+ `MysqlExceptionParser` /
`KingBaseExceptionParser` / `DMExceptionParser`。

⇒ 业务代码**抛语义异常即可**，翻译成错误码/文案由框架按处理器链完成。
自己写 try/catch 再拼响应，会和框架链重复且顺序不可控。

#### 调用上下文

```java
public class AppServiceContext extends BaseContext {
    public MethodInvocation getMethodInvocation();
    public Object getTarget();            public Object getResult();
    public Throwable getTargetThrowable();
    public Set<String> getPlugins();
    public boolean isModuleAppService();
    public String getLoggerMethodName();  public String getMethodClassSimpleName();
    public MethodProxy getMethodProxy();
}
```

⇒ 在切面/处理器里想知道「谁调的、调了什么、结果是什么」，从 `AppServiceContext` 取，
不要自己往 ThreadLocal 塞。

### 7.4 接口面命名规律（便于在未知域里找方法）

- `select*` 读 / `create*` 增 / `update*` 改 / `delete*` 删；批量后缀 `Batch`/`ByIds`
- 分页必带 `Page`（`selectPageByCondition` → `PageResponse`）
- 树形/层级：`*4Tree`、`selectChildren*`、`selectParent*`、`selectRootId`
- 变体差异靠后缀区分（例：`create` vs `createBatch` vs `createBatch4System`）

## 8. Evidence

```
① 路径  docs/audit/artifacts/extension-surface-20261029/batch2/boot-starter-appservice.json
        （框架侧 30 类 / 136 方法）
        docs/audit/artifacts/extension-surface-20261029/batch2/udc-facade.json
        （接口面示例 10 接口 / 132 方法）
        两文件内只有 artifact 名与版本，无工程/环境信息
② 复现  uv run --no-project python tools/core/platform/extract_jar_symbols.py \
          --jar "<按 Maven 坐标 com.seeyon:<artifact>:<ver> 解析出的 jar>" \
          --include com/seeyon/boot/starter/appservice/ \
          --javap <javap> --cfr <cfr.jar> --limit 200 --emit <out1.json>
        （接口面同理，换 --jar 与 --include）
③ 校验  本格每个签名都能在对应 out.json 的 classes[].symbols.methods[] 里逐字找到；
        §7.2 的三个多参数方法在 batch2/udc-facade.json 里逐字可核对。
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 10 组「动词→签名」成套关系 | `VERIFIED_STATIC_BYTECODE`（接口面逐字） |
| 多参数平铺多个 `SingleRequest` | `VERIFIED_STATIC_BYTECODE`（`selectListByTerm`/`selectByName` 逐字） |
| 幂等族类与字段 | `VERIFIED_STATIC_BYTECODE` |
| 异常翻译链与方言解析器 | `VERIFIED_STATIC_BYTECODE` |
| `AppServiceContext` 取用面 | `VERIFIED_STATIC_BYTECODE` |
| 事务切面存在（方法级） | `VERIFIED_STATIC_BYTECODE`（类存在；织入顺序未证） |
| 编译/运行通过 | **UNVERIFIED** |

## 铁律

- AppService 入参恒为 `SingleRequest<T>`，T 是 `Long`/`List<Long>`/`Dto`/`List<Dto>` 都要包。
- 写操作返回 `Integer`（行数）或 `Long`（新 id）；`update` 回 0 表示没命中行，不是异常。
- 批量用 `createBatch`/`updateBatch`/`deleteByIds` 单个方法，不要循环调单个方法。
- 多参数方法是多个 `SingleRequest` 平铺 + 裸 `Sort`，不要打包成一个 DTO。
- 幂等/事务/异常翻译是框架 AOP：抛语义异常即可，不要自己写 try/catch 拼响应。
- 切面/处理器里要上下文信息就从 `AppServiceContext` 取，不要自建 ThreadLocal。
- 接口面命名有规律：`select*`/`create*`/`update*`/`delete*` + `Batch`/`ByIds`/`Page`/`4Tree`/`Children`/`Parent` 后缀。
