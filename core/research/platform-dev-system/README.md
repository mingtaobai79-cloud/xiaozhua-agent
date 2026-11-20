# Seeyon 平台开发体系知识库

> 目标：让 Agent 能从业务需求出发，自主回答「用什么能力、生成什么、调什么方法、数据怎么写、有什么风险、怎么验证」。

---

## 目录结构

```
core/research/platform-dev-system/     研究报告（未审计，不得作为 Agent 知识）
├── README.md                          本文件
├── progress.md                        进度与轮次记录
├── statistics-registry.md             统计口径登记表
├── evidence-map.md                    证据地图（什么有证据、什么缺）
├── dependency-map.md                  专题依赖关系
├── 01-metadata.md                     专题 1：应用与元数据
├── 02-codegen.md                      专题 2：代码生成
├── 03-persistence.md                  专题 3：生成物与持久化
├── 04-expression.md                   专题 4：表达式与运行时
├── 05-interface-integration.md        专题 5：接口调用
├── 06-components.md                   专题 6：基础组件
├── 07-business-capability-bridge.md   专题 7：业务能力关联
├── evaluation/                        评估集
├── cases/                             端到端案例
└── unresolved/                        未解决问题

core/facts/platform-dev-system/        正式知识（经审计后才写入）
```

**⚠️ 硬规则：`core/research/` 下的内容不得被 Agent 直接检索为知识。**
必须经过证据审计、升级到 `core/facts/` 后才能进入推荐链路。

---

## 七个专题

| # | 专题 | 核心问题 | 状态 |
|---|---|---|---|
| 1 | 应用与元数据 | 有哪些元数据对象、怎么组合、怎么参与生成 | 第一轮完成 |
| 2 | 代码生成 | CodeTask→Template→资源→产物→部署 | 未开始 |
| 3 | 生成物与持久化 | 三层职责、CRUD、主键、主子表、单据、事务 | 未开始 |
| 4 | 表达式与运行时 | 定义→解析→代码生成→运行时调用 | 未开始 |
| 5 | 接口调用 | Dubbo/Autowired/泛化/微流程/第三方 | 未开始 |
| 6 | 基础组件 | 用什么、怎么用、什么时候不能用 | 未开始 |
| 7 | 业务能力关联 | 业务意图→能力→方法→验证 | 未开始 |

---

## 证据等级

| 等级 | 含义 | 判定 |
|---|---|---|
| `STATIC_RULE` | 文档/配置/模板清单静态声明 | 能在文件里逐字找到 |
| `VERIFIED_STATIC_BYTECODE` | 字节码/反编译核实的结构与实现 | 签名库命中 + 调用关系闭合 |
| `LIVE_RULE` | 真实环境执行并观察到结果 | 有响应体/DB 结果/生成产物 |
| `UNVERIFIED` | 尚未证实 | 只有推测 |
| `BLOCKED` | 缺资产无法推进 | 明确缺什么 |

**不可逾越的边界：**
1. 方法签名只证明方法存在
2. 类名不证明类用途
3. 模板清单不证明选择机制
4. 方法存在不证明被调用
5. 被调用不证明完整业务行为
6. 静态调用关系不能代替运行验证
7. 生成产物不能单独证明模板内部机制

---

## 数据源

| 资产 | 路径 | 规模 |
|---|---|---|
| 类/方法签名 | `docs/audit/signatures.txt.gz` | 245709 行 / 21389 类 / 224320 方法 |
| 平台资源包 | `docs/audit/reference/udc-platform-5.3.517.tar.gz` | 404 条目 |
| 表面索引 | `docs/audit/reference/surface-index.tar.gz` | 100+ 文件 |
| AppService 清单 | `docs/audit/reference/svc-app-service.txt.gz` | 830 接口 / 9343 方法 |
| 反编译源码 | `docs/audit/modules/decompiled/` | 212 .java |
| 统计脚本 | `scripts/research/stats_registry.py` | 可复现 |

**平台版本：** `udc-platform-5.3.517`

---

## 当前阻塞

| 阻塞 | 影响 | 状态 |
|---|---|---|
| 无平台 jar 本体 | 无法反编译方法体 | 需用户提供路径 |
| 无 .ftl 模板内容 | 无法看模板语法 | 需 jar |
| 无 CFR 工具 | 同上 | 可安装（需批准） |
| test2 写操作未批准 | 无法验证运行时行为 | 全部挂起 |

**不影响静态研究，继续推进。**
