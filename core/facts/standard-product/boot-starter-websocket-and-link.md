# WebSocket 推送 · 短链 · 前端日志 · 过滤链

## Capability

四个「小但有用」的 boot 组件，按用途分节：

```
boot-starter-websocket      服务端向前端推消息（配合 MQ 广播）
boot-starter-shortlink      长链接转短链 + 短链跳转
boot-starter-frontend-log   前端日志上报入口
boot-starter-filterchain    自研过滤器链（业务可插 Filter）
```

## Version

`websocket` / `shortlink` / `frontend-log` / `filterchain` 均 5.3.600（`shortlink` 视快照）。

## ★ 一、WebSocket 推送

```java
// 订阅侧：实现接口收前端消息
public interface ReceiveProcessService { void receiveMessage(TextMessage msg); }

// 发布侧（平台内部用它把 EventBus 事件推给前端）
EventBusPulisherMessageListener.messagePulisher(TextMessage);
EventBusPulisherMessageListener.syncMessagePulisher(SyncTextMessage);
```

常量（`Constants`）：

```
RECEIVE_KEY / CTP_MESSAGE_SUBSCRIBE_KEY / DEFAULT_PUSH_SERVICE
PUSH_ALL_USER_SERVICE / I18N_PUSH_SERVICE / COMMON_MESSAGE
```

⇒ 平台形态是 **Redis 广播 + WebSocket 端点**：`WebSocketRedisListener` 收 Redis 消息再推前端。
客开要推消息，走 `EventBus` / MQ，**不要自己维护 Session**。

## ★ 二、短链（shortlink）

```java
CtpShortLinkController
  void link(String code, HttpServletResponse resp);                       // 短链跳转
  SingleResponse<String> createLink(String url);                          // 生成短链

CtpShortLinkDao extends BaseMybatisDao<CtpShortLink>
实体：CtpShortLink        常量：ShortLinkConstant.REQ_PATH
```

## ★ 三、前端日志上报

```java
FrontendLogController.reportLog(MultiValueMap<String,String>, FrontendLogRequestDto);
HeaderConstants.HOST / USER_AGENT / REFERER
FrontendLogType（枚举，日志类型）
```

前端把浏览器日志 POST 上来，落到平台日志体系；后端不主动调它。

## ★ 四、过滤链（filterchain）

```java
public interface Filter<C extends BaseContext> extends Ordered, Named {
    void doFilter(C context, FilterChain<C> chain);
}

public abstract class BaseFilterChain<C extends BaseContext> implements FilterChain<C> {
    void doFilter(C);
}

BaseContext implements Serializable      // 链上传递的上下文
FilterBeanFactoryPostProcessor           // 自动收集 Filter bean 并按 @Order 排序
FilterchainProperties                    // 开关与配置
```

用法：定义自己的 `XxxContext extends BaseContext` → 写若干 `Filter<XxxContext>` 标 `@Order` →
`BaseFilterChain` 子类串起来。**不用自己写 Servlet Filter**。

## Side Effects

- WebSocket 推送是**广播语义**：同一用户多端都会收到，前端要做幂等。
- 短链是永久映射（`CtpShortLink` 表），生成的码不要复用给不同 url。
- 前端日志量不受控会打满日志盘，生产上要限流。

## Known Constraints

1. WebSocket 依赖 Redis 广播（`WebSocketRedisListener`）—— 单机模式也算能用，但多 pod 必须 Redis。
2. 短链跳转是 `void`（直接写 response），不是返回 302 之外的 body。
3. `filterchain` 是**业务级链**，与 Servlet 的 `javax.servlet.Filter` 无关，别混。
4. `filterchain` 的 `Filter` 带 `Ordered`，顺序由 `@Order` 决定，不写就按 bean 名。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `ReceiveProcessService` 1 方法 + 6 个常量 | `javap -p` | VERIFIED_STATIC_BYTECODE |
| `EventBusPulisherMessageListener` 2 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| `CtpShortLinkController` 2 方法 + Dao 泛型 | 同上 | VERIFIED_STATIC_BYTECODE |
| `FrontendLogController.reportLog` | 同上 | VERIFIED_STATIC_BYTECODE |
| `Filter`/`BaseFilterChain`/`BaseContext` 契约 | 同上 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 类与签名可复核
- ⚠️ 四个组件都未真机调用

## 给 Agent 的判据

```
要主动推消息给前端     → 走 EventBus/MQ，别自己管 WebSocket Session
要收前端发来的 ws 消息 → 实现 ReceiveProcessService.receiveMessage
要生成短链            → CtpShortLinkController.createLink(url)
要做业务过滤链         → Filter<YourContext> + BaseFilterChain，@Order 控序
```
