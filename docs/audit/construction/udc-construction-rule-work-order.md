# UDC Construction Rule Work Order

## Scope

只研究 UDC 平台本体及其构造物：UDC Artifact、反编译源码、前端编译物、Nacos 配置/元数据/SQL、数据库模型和运行时生成消费链。客户项目延后。

## Root architecture

```text
xiaozhua Agent
├── UDC
│   └── Construction Rules
│       ├── Application
│       ├── Data Model / Entity
│       ├── Field / Attribute
│       ├── Page / Widget / Layout
│       ├── Form / List
│       ├── MicroFlow / DataFlow
│       ├── Permission / Menu
│       ├── BPM Construction
│       ├── SPI Construction
│       ├── Connector Construction
│       └── Generate / Publish / Deploy
├── BPM
├── SPI
├── Connector
└── Other Platform Modules
```

## Rule record

每条规则必须至少包含：

- rule_id / domain / object_type
- frontend_entry / frontend_state / payload_shape
- backend_controller / dto / service
- fixed_template / dynamic_parameters
- dependencies / generated_artifacts
- metadata_or_sql / persistence_target
- runtime_consumer / references
- evidence_refs / artifact-version-sha256
- verification_level / gaps / limitations

## Execution order

1. 全量 UDC Artifact 与反编译源索引。
2. 前端入口与所有构造相关 chunk 的真实字节获取和静态分析。
3. Application → Entity → Field → Page 最小构造链。
4. MicroFlow/DataFlow 与生成器依赖链。
5. Permission/Menu 与 BPM/SPI/Connector 构造规则。
6. Nacos/SQL/数据库对象映射。
7. Generate → Persist → Runtime 消费闭环。
8. 最后使用客户项目做规则验证。

## Stop conditions

- 不根据客户项目推导平台规则。
- 不把静态类名、HTTP 200 或单个 SQL INSERT 直接升级成 VERIFIED_RULE。
- 不执行任何发布、部署、数据库/Redis 写入。
- 前端字节未取得时，明确记录 BLOCKED/UNVERIFIED，不用前端可达性替代内容分析。
