# Seeyon Agent Operation Contracts

## Scope

本目录定义 Seeyon Agent 对平台能力的可调用边界。它不是源码生成规则，也不是审计报告。

```text
Capability Catalog
  = 平台有哪些能力、当前证据等级如何

Operation Contract
  = 某个能力具体如何被 Agent 请求、接收响应并回读验证

Gateway Access Contract
  = 所有平台请求如何经过 Gateway，包括路由、发现、Header、认证、错误和响应边界
```

关系：

```text
Capability Catalog
    ↓ selects a capability
Operation Contract
    ↓ uses shared transport boundary
Gateway Access Contract
    ↓
Gateway → Service Discovery → target service
```

## Current phase

```text
Gateway Access Contract v0.1 = IN PROGRESS
```

The current implementation target is a shared read-only Gateway access layer. UDC Generator/Metadata→Generator remains background research and is not a current delivery gate.


1. `UNKNOWN` 是合法状态，不得用命名相似性补全事实。
2. 静态 Controller 路由不等于 Gateway 外部路由。
3. 前端 GraphQL fieldType 不等于已验证的 HTTP 请求；必须记录 mapping evidence。
4. 写操作、发布、重启、清缓存必须显式授权，并对同一目标回读。
5. `Capability Catalog` 可以记录“可能存在的能力”；`Operation Contract` 只有在请求、响应和 readback 至少有证据时才升级。
6. UDC、BPM、Connector、Integration 是并列组件；Gateway 是共享平台访问层。
7. SPI 单独建模为 `contract → extension point → registration/loading → invocation → verification`，不混入 UDC 操作契约。

## Directory

```text
docs/operation-contracts/
├── gateway/gateway-access-v0.1.json
└── udc/
    ├── application/
    ├── bi/
    ├── column/
    ├── entity/
    ├── flow/
    ├── menu/
    ├── microflow/     ← 有子目录 README（13 份契约 + live-evidence 原件 51 件）
    ├── page/
    ├── publish/
    ├── resource/
    ├── role/
    ├── rule/
    ├── runtime/
    └── setting/       ← 有子目录 README（11 份 tab 契约，GraphQL 5 / REST 3 / 半开半合 2 / runbook 1）
```

`udc/microflow/` 与 `udc/setting/` 是本层已有子目录入口的两个域：
- `udc/microflow/README.md`：四组分类 + 三份大契约（map-node 80,400 B / state 39,013 B / runtime-engine 22,136 B）
  + 外部引用清单 + 「零外部引用为何仍不删」的判据。
- `udc/setting/README.md`：11 个 tab 按协议分组（**协议搞错是这一域最贵的错误**——拿 GraphQL 探 REST 端点
  必然 `FieldUndefined`，那是假阴性）+ 与 facts 侧 13 份事实格的对应表 + 三个协议坑（字段集/扩展实体半开半合、
  选项集与枚举两套表、参数 `Definiton` 少一个 i）。

★ **`udc/` 自身已有入口**：`docs/operation-contracts/udc/README.md`——14 个子域一览（合计 81 份 / 1,153,874 B，含各子域 README）、
9 份同名 `registry-entries.md` 的判断口径（**UDC-MERGE 已执行，128 条契约中 37 条照抄自这些文件**，
所以「供照抄」不是待办）、剩余 5 条未落库各自的原因，以及 11 个无入口子域的导航。
由 `tests/udc/test_operation_contracts_udc_layout.py` 守着。

子域入口闸门：`tests/udc/test_setting_contracts_layout.py`（setting）、`tests/udc/test_operation_contracts_udc_layout.py`（udc 整层）。
其余子域尚未逐一给入口，按需补比批量生成有用。

当前 P0 是 Gateway Access Contract v0.1；之后按 Application/Resource/Menu → Entity → Page → MicroFlow → Publish/Runtime 逐项落入 Operation Contract。
