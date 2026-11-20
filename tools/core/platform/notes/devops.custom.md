## 这个域没有 facade（为什么）

`com.seeyon.devops` 共 245 个类，包结构是 `devops.starter`，
即**运维/监控的 starter 组件**（健康检查、指标上报、灰度）。没有业务 AppService。

**结论**：运行时框架能力，业务代码不需要调。

它有 4 个事件类，用于运维侧监听，不在业务链路里。
