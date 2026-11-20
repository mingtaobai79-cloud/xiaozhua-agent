## 这个域只有 1 个类（为什么）

`com.seeyon.MyMojo` 是单个 Mojo 类（Maven 插件入口），三段类名、没有子包
—— 这也是当初按前缀分组会漏掉它的原因（见 `U0-index-query-guide.md` §12）。

**结论**：构建期工具，运行时不可调用。
