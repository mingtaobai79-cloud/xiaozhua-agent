# Seeyon Agent 骨架收敛与下一阶段实施计划

目标：先把现有只读骨架收敛为可信、可重复、证据不漂移的审计/诊断基础，再围绕 application_id `app9000000000000000001` 补齐定向静态证据和 test2 只读动态证据。

架构原则：Core、Profiles、Components、Providers、Workflows 五层；UDC、Runtime、Integration、SPI 并列；UDC Platform、Standard Product Application、Customer UDC Application、Extension Service 四类档案独立。外部 Provider 默认关闭网络，写操作保持 DENIED/dry-run，本计划不实现 executor。

## 当前骨架

- Core：agent、evidence、ports、provider contract、component registry 已有。
- Components：UDC、Runtime、Integration、evidence ledger、impact graph、dry-run、report schema 已有；SPI 尚为路由占位。
- Profiles：四类最小模型和 profile graph 已有；ProfileBuilder 未落地。
- Providers：HTTP/Kubernetes/Nacos/MySQL/Redis/storage discovery 的只读骨架已有。
- CLI 与 34 个测试文件已有。
- adapters/workflows/policies 尚未形成目录级实现。
- 当前实测：194 passed / 22 failed；主要是 Temp evidence 缺失和文档计数漂移。

## 目标骨架

```text
SeeyonAgent
├── Core: TaskRequest / Context / Result-Evidence-Status / Registry / PolicyGate / ReadOnlyOrchestrator
├── Profiles: 4类Profile / ProfileBuilder / ProfileEvidenceGraph
├── Components: UDC / Runtime / Integration / SPI
├── Providers: EvidenceBundle / Kubernetes / Nacos / MySQL / Redis / HTTP ReadOnly
└── Workflows: inspect_application / inspect_udc_object / inspect_runtime / inspect_boundary / build_report
```

## 执行阶段

### Phase 0：恢复可重复基线

- 建立 `tests/fixtures/udc-audit/` 稳定、脱敏的最小 evidence bundle。
- 新增 `components/evidence_bundle.py`，manifest 必须含 schema version、source、artifact/version/sha256、limitations。
- 修改 UDC catalog/analyzer 和测试，不再依赖 `<USER_HOME>/...
- 缺文件必须返回结构化 UNVERIFIED，不能用历史硬编码数字伪装事实。
- 更新 README/审计文档测试计数。
- 验收：全量 pytest=0；compileall、CLI smoke 通过。

### Phase 1：统一报告与安全闸门

- 收敛 `core/evidence.py`、`components/report_schema.py`。
- 新增 `core/policy.py`。
- 报告统一包含 status、verification_level、component、target、environment、application_id、facts、evidence、unverified、conflicts、limitations、next_actions。
- fixture/static 不能声明 LIVE；POST/PUT/PATCH/DELETE 和 kubectl exec/apply/delete 默认 DENIED。

### Phase 2：完成 ProfileBuilder

- 新增 `components/profiles/builder.py`、`schema.py` 和测试。
- 从 evidence bundle、Nacos manifest、应用源码档案生成四类独立 Profile。
- relation 必须有直接证据；Pod 名不能推断职责；Maven inventory 不能证明线上部署。
- CLI 增加/收敛 `profile-build`、`profile-graph`，正常、冲突、缺文件均输出单行 JSON 和稳定退出码。

### Phase 3：补齐 UDC inspect

真实实现：application、entity、field、page、page schema、microflow、dataflow、version、generated app、runtime metadata、deployment。

每项返回 status、evidence_refs、gaps、dependencies；证据不足时指出具体缺失文件/字段，不返回泛化成功。dry-run 必须调用 planner，但 executed=false、writes_performed=false。

### Phase 4：目标应用定向静态扫描

目标 application_id：`app9000000000000000001`。

优先目录：
- `<EVIDENCE_ROOT>\9000000000000000001_test2`
- 不存在时核对 `<PATH>

只扫描 Maven modules/dependencies、web/core/ext/biz/facade 关系、Controller→AppService→Entity/Runtime、ext 对 Integration/SPI 的真实调用、artifact/version/sha256、Nacos data_id 与 application_id 绑定。

输出应用 Profile JSON 和 boundary.md；每条关系保留源码/FQCN/方法/dependency locator。

### Phase 5：test2 只读动态取证

显式使用 `kubectl --kubeconfig=configtest2`，不擅自追加 namespace。

只读：Deployment/Pod/Image、环境变量与挂载、应用独立 Nacos、无副作用查询、MySQL schema/table/index/count、Redis pattern/type/TTL、日志/路由、artifact 版本/hash。

禁止：外部文件写入、apply/patch/delete、DDL/DML、Redis SET/DEL、发布、部署、重启。

### Phase 6：关键路径矩阵与决策包

矩阵：Application、Entity、Field、Page Schema、MicroFlow、DataFlow、Generate、Publish、Deploy、Runtime Metadata。

G0-G3 未通过继续只读审计；G0-G3 通过但 G4-G6 未通过只增强 dry-run；G0-G6 通过且用户确认 G7 后，才设计临时应用最小写入闭环。publish/deploy 始终单独确认。

## 立即执行顺序

1. Phase 0：修复 evidence fixture 和 22 个失败。
2. Phase 1：统一报告与 PolicyGate。
3. Phase 2：ProfileBuilder。
4. Phase 3：UDC inspect。
5. Phase 4：目标应用边界扫描。
6. Phase 5：test2 只读动态验证。
7. Phase 6：关键路径矩阵和方向决策。

执行纪律：Phase 0 单线程完成；后续一次只分配一个窄代码任务，父 Agent 必须读取落盘文件并实跑验证。不要再次用多个子 agent 同时修改共享工作区。
