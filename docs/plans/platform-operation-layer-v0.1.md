# Seeyon Agent Platform Operation Layer v0.1 收口计划

## 当前目标

在不依赖 test2 网络的情况下，收口一个可测试的平台操作边界：

```text
OperationIntent
  → Capability / OperationContract
  → PlatformOperationLayer
  → Gateway/UDC Adapter
  → OperationResult
  → Evidence / Session
```

真实 `Agent → Gateway → UDC` 仍受 VPN 阻塞，不在本轮伪造 LIVE 结果。

## 模块与停止点

1. Intent / Contract
   - 固化 readonly intent、目标标识和上下文。
   - 合同区分 declared、available、blocked、effective。
   - 停止点：未知、blocked、写操作不能进入 effective execution。

2. Platform Operation Layer
   - 作为唯一 operation owner，绑定 session_id/run_id。
   - 只调用 Adapter，不拼 GraphQL、不处理底层 Gateway 细节。
   - 停止点：composition 测试能证明 Intent→Contract→Adapter→Result。

3. OperationResult / Evidence
   - 固化 PASS、BLOCKED、UNVERIFIED、FAIL。
   - 固化连接、发现、Gateway、UDC、业务、验证错误分层。
   - 停止点：失败和 evidence 均可结构化保存。

4. Safety / Regression
   - 保持 GET-only、默认不联网、敏感信息脱敏。
   - 停止点：本地 compile 和可用测试解释器验证通过；pytest 缺失则明确 BLOCKED。

## 本轮非目标

- 不恢复 VPN。
- 不执行真实外部请求。
- 不开放 POST/PUT/PATCH/DELETE。
- 不实现 Entity Create、Generator、Page、MicroFlow、BPM、SPI、Connector 或自主规划。
- 不重做 Session 存储。

## 验证门

```text
Core：Intent/Contract/Result schema
Composition：Layer→Adapter→Result
Safety：method/policy/redaction/blocked
Regression：现有模块不被破坏
Live：当前 BLOCKED，不以 Mock/fixture 冒充 PASS
```
