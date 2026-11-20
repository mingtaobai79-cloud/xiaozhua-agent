## 这个域没有 facade（为什么）

`com.seeyon.ai` 共 237 个类，**没有 `*.api.*` / `*.appservice.*` 接口**。
它的结构是 `ai.core.infrastructure` / `ai.core.common` 这类内部实现包。

**这带来两个结论**：

1. AI 能力**不通过 AppService 对外提供**，Agent 不能按「引 facade 接口」的方式用它；
2. 若外部要用，只能走 HTTP（`ai-web` 的 Controller）或消息。

⚠️ 未取证：`ai` 是否有自己的 SPI 扩展点。需要时反编译 `ai-biz` 找 `*Provider` / `*Handler`。

另外注意：`com.seeyon.ai.core.common.JsonUtils` 是**私有副本**，
不要用它替代 `com.seeyon.boot.util.JsonUtils`（见 `U0` §3.1）。
