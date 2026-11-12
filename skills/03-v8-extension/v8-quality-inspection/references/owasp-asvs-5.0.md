# OWASP ASVS 5.0.0 参考文档

> 来源：https://github.com/OWASP/ASVS (v5.0.0, 2025-05-30 发布)
> 引用格式：v5.0.0-<chapter>.<section>.<requirement>（如 v5.0.0-1.2.5）

## 概述

OWASP 应用安全验证标准（ASVS）5.0.0 是对 4.0.3 的重大重构。章节重新组织，需求重新编号，新增三个独立章节。验证级别为 L1（基础）/L2（标准）/L3（高级），L1 适用于 L1/L2/L3，L2 适用于 L2/L3，L3 仅适用于 L3。

## 章节结构（V1~V16）

| 章节 | 名称 | 要求数 | L1 | L2 | L3 |
|------|------|--------|----|----|-----|
| V1 | Encoding and Sanitization（编码与净化） | 30 | 6 | 21 | 3 |
| V2 | Validation and Business Logic（验证与业务逻辑） | 12 | 5 | 5 | 2 |
| V3 | Web Frontend Security（Web 前端安全） | 31 | 7 | 11 | 13 |
| V4 | API and Web Service（API 与 Web 服务） | 16 | 2 | 5 | 9 |
| V5 | File Handling（文件处理） | 13 | 4 | 6 | 3 |
| V6 | Authentication（认证） | 47 | 12 | 19 | 16 |
| V7 | Session Management（会话管理） | 19 | 4 | 11 | 4 |
| V8 | Authorization（授权） | 13 | 3 | 4 | 6 |
| V9 | Self-contained Tokens（自包含令牌） | 7 | 3 | 4 | 0 |
| V10 | OAuth and OIDC | 36 | 5 | 19 | 12 |
| V11 | Cryptography（密码学） | 24 | 2 | 10 | 12 |
| V12 | Secure Communication（安全通信） | 12 | 2 | 6 | 4 |
| V13 | Configuration（配置） | 21 | 1 | 10 | 10 |
| V14 | Data Protection（数据保护） | 13 | 1 | 6 | 6 |
| V15 | Secure Coding and Architecture（安全编码与架构） | 21 | 2 | 9 | 10 |
| V16 | Security Logging and Error Handling（安全日志与错误处理） | 9+ | 0 | 9+ | 0+ |
| **合计** | | **324+** | **59** | **155+** | **110+** |

## 关键章节速查（审计高频引用）

### V1 - Encoding and Sanitization（编码与净化）
- V1.1 编码与净化架构（L2）
- V1.2 注入防护（L1~L2）：SQL 注入、OS 命令注入、LDAP/XPath/LaTeX/CSV 注入、ReDoS
- V1.3 净化（L1~L3）：HTML 净化、eval 禁用、SSRF 防护、模板注入、JNDI 注入
- V1.4 内存、字符串与非托管代码（L2）：缓冲区溢出、整数溢出、use-after-free
- V1.5 安全反序列化（L1~L3）：XXE 防护、反序列化白名单

### V3 - Web Frontend Security（Web 前端安全）
- V3.3 Cookie 设置：`Secure`/`SameSite`/`HttpOnly`/`__Host-` 前缀
- V3.4 浏览器安全机制头：HSTS、CSP（`object-src 'none'; base-uri 'none'`）、`X-Content-Type-Options`、`Referrer-Policy`、`frame-ancestors`、`Cross-Origin-Opener-Policy`
- V3.5 浏览器源分离：CORS 预检、安全 HTTP 方法、`postMessage` 验证、XSSI 防护
- V3.6 外部资源完整性：SRI

### V6 - Authentication（认证）
- V6.2 密码安全：最小 8 字符（建议 15+）、泄露密码检查、无字符类型限制、允许粘贴
- V6.3 通用认证：防凭证填充、无默认账户、MFA（L2+）
- V6.5 多因子认证：一次性使用、≥20 位熵、CSPRNG 生成、TOTP 时间源可信

### V7 - Session Management（会话管理）
- V7.2 基本安全：CSPRNG ≥128 位熵、认证后重新生成令牌
- V7.3 超时：不活动超时 + 绝对最大生命周期
- V7.4 终止：注销功能可见、账户禁用时终止所有会话

### V8 - Authorization（授权）
- V8.2 通用设计：功能级（L1）、数据级/IDOR/BOLA（L1）、字段级/BOPLA（L2）
- V8.3 操作级授权：服务层执行、变更即时生效
- V8.4 多租户：跨租户隔离

### V11 - Cryptography（密码学）
- V11.2 安全实现：行业验证的库、加密敏捷性、≥128 位安全、恒定时间操作
- V11.3 加密算法：禁用 ECB/PKCS#1 v1.5、使用 AES-GCM、认证加密
- V11.4 哈希：禁用 MD5、密码使用 KDF（bcrypt/argon2/scrypt）、签名哈希 ≥256 位
- V11.5 随机数：CSPRNG ≥128 位熵

### V13 - Configuration（配置）
- V13.3 密钥管理：KMS/HSM（L3）、最小权限、密钥轮换
- V13.4 信息泄露：无源码控制元数据、调试模式禁用、无目录列表、TRACE 禁用

### V15 - Secure Coding and Architecture（安全编码与架构）
- V15.1 文档：第三方组件漏洞修复时间框架、SBOM 清单
- V15.2 架构：组件不超期、依赖混淆攻击防护、危险功能额外保护
- V15.3 防御编码：字段子集返回、防止批量赋值、原型污染防护、HTTP 参数污染防护
- V15.4 安全并发：线程安全、TOCTOU 竞态、锁一致性、资源公平分配

## ASVS 5.0 vs 4.0.3 主要变化

1. 章节重组：从 14 章扩展到 16 章，新增 V9（自包含令牌）、V10（OAuth/OIDC 独立章节）
2. 需求重新编号：所有需求 ID 已更改，引用时必须使用 `v5.0.0-` 前缀
3. 验证级别保留：L1/L2/L3 三级体系不变
4. 内容更新：涵盖 OAuth 2.1、PKCE、DPoP、安全编码最佳实践等
5. CSV/PDF/Word 格式可用
