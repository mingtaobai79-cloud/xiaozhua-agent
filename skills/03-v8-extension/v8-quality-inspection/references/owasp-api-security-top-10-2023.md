# OWASP API Security Top 10 (2023) 参考文档

> 来源：https://owasp.org/API-Security/editions/2023/en/0x11-t10/

## 概述

OWASP API Security Top 10 2023 专注于 API 层面的安全风险。与通用 OWASP Top 10 是独立维护的列表，API 密集系统需同时对照两份清单审计。

## 十大 API 安全风险

### API1:2023 - Broken Object Level Authorization (BOLA)
- **描述**：API 暴露处理对象标识符的端点，造成对象级访问控制的广泛攻击面。每个使用用户传入 ID 访问数据源的函数都应做对象级授权检查。
- **审计要点**：每个 API 端点的对象 ID 是否做了归属校验；不能仅依赖客户端传入的角色/用户 ID。
- **CWE 映射**：CWE-639（用户可控键越权）、CWE-284（不当访问控制）

### API2:2023 - Broken Authentication
- **描述**：认证机制实现不当，允许攻击者 compromise 认证令牌或利用实现缺陷临时/永久冒充其他用户身份。
- **审计要点**：令牌随机性、过期机制、刷新令牌安全、多因素认证。

### API3:2023 - Broken Object Property Level Authorization (BOPLA)
- **描述**：合并了 2019 版的 API3（过度数据暴露）和 API6（批量赋值），根因是对象属性级缺少或不正确的授权校验。
- **审计要点**：返回体是否过滤敏感字段；可更新字段是否白名单；防止 mass assignment。

### API4:2023 - Unrestricted Resource Consumption
- **描述**：API 请求消耗网络带宽、CPU、内存、存储等资源，以及邮件/SMS/电话等第三方付费服务。攻击可导致 DoS 或运营成本增加。
- **审计要点**：分页、限流（rate limiting）、配额（quota）、最大执行时间、最大请求体大小。

### API5:2023 - Broken Function Level Authorization
- **描述**：复杂访问控制策略（多层级、分组、角色）和管理功能与常规功能界限不清导致授权缺陷。
- **审计要点**：管理端点是否做了功能级授权检查；默认拒绝策略。

### API6:2023 - Unrestricted Access to Sensitive Business Flows
- **描述**：API 暴露的业务流程（购票、发评论等）未对自动化滥用做补偿控制。不一定源于实现 bug。
- **审计要点**：关键业务流程是否有人机验证、频率限制、业务防刷策略。

### API7:2023 - Server Side Request Forgery (SSRF)
- **描述**：API 在获取远程资源时未验证用户提供的 URI，攻击者可强制应用向意外目标发送请求。
- **审计要点**：URL 白名单、禁内网/元数据地址、DNS 重绑定防护。
- **注**：在 OWASP Top 10:2025 中 SSRF 已并入 A01，但在 API Top 10 中仍为独立类别。

### API8:2023 - Security Misconfiguration
- **描述**：API 及支持系统包含复杂配置，工程师可能遗漏或未遵循安全最佳实践。
- **审计要点**：默认配置、HTTP 方法限制、CORS、错误信息泄露、不必要的 HTTP 方法。

### API9:2023 - Improper Inventory Management
- **描述**：API 暴露的端点比传统 Web 应用更多，文档和版本管理至关重要。
- **审计要点**：API 版本管理、废弃端点是否下线、调试端点是否暴露、API 文档（OpenAPI/Swagger）是否更新。

### API10:2023 - Unsafe Consumption of APIs
- **描述**：开发者倾向于过度信任第三方 API 数据，采用较弱的安全标准。攻击者可针对集成的第三方服务间接 compromise 目标 API。
- **审计要点**：第三方 API 响应是否校验和净化；HTTPS 验证；对第三方 API 的数据信任级别。
