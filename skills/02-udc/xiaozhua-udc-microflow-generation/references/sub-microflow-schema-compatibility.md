# SUB_MICROFLOW_SCHEMA_COMPATIBILITY_CHECK

**一句话**：子流程改了入参/出参契约后，调用方的 `mfService` 不一致会在**构建期一致性检测**被拦；
单流程发布（checkSchema）**不拦**。

## 证据分级

| 级别 | 内容 |
|---|---|
| **VERIFIED**（真实运行） | 契约不一致时构建 11 秒 FAIL：「发布失败: Business Error[一致性检测未通过]」，位置 `AbstractDeployService.doParallel(AbstractDeployService.java:242)`；刷新调用节点后重新构建 SUCCESS；运行期新契约生效（读侧 `processed_rows=424242`）。 |
| **BYTECODE_VERIFIED**（反编译） | `MicroFlowComponentUtils.checkMfService` 在 `isDetection() && GLOBAL && !isSubApp` 时，逐字比对 `mfService.input/output` 与子流程 schema 的 `input/output`；`compare()` 只比 **dataType / type / id**；`mfService.path` 必须以子流程 `name` 结尾。 |
| **UNVERIFIED** | `MICRO_FLOW_CHANGE` 这个**具体错误码**与本次笼统文案的对应关系——平台只回了「一致性检测未通过」，没带明细。字节码里的枚举名不能当成已捕获的运行错误码。 |

## 实测链（2026-11-02，P5-S1）

```
Child 出参 STRING  → Parent 发布/构建/执行 全通（taskId=CHILD-OUT）
Child 出参改 BIGINTEGER(424242) 并发布
Parent 未刷新直接 publish → 通过              ← 单流程 checkSchema 不做全局比对
触发构建                → 11s FAIL [一致性检测未通过]
刷新（重读契约→重建节点，回读 dataType=BIGINTEGER）→ 发布通过、构建 SUCCESS
再跑一轮                → processed_rows=424242
```

## 对工作的影响

1. **「属性已更新，请重新选择」不是提示性文字，是硬闸门**——只重发 API 不改 `mfService` 会导致构建一直失败。
2. 改 desc / name / javaType **不会**触发（`compare` 不比这些），只有 dataType / type / id 变化才会。
3. 排错顺序：构建期报「一致性检测未通过」时，先查最近是否有子流程契约变更、被调用方是否刷新。

## 相关

- `node-sub-microflow.md`（节点结构、语料、入参出参形态）
- 反编译：`docs/audit/artifacts/decompiled/cfr-r28/d4/com/seeyon/udc/microflow/util/MicroFlowComponentUtils.java:1836-1905`
