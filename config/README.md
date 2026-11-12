# config/ — 环境与版本配置（唯一事实来源）

## 文件结构
- environments.yaml   环境清单（网关/appId/凭据引用/Maven 根）
- infra.yaml          公用基础设施（数据库/Redis/存储/Nacos），按环境覆盖
- artifact-versions.yaml   UDC 大版本族 + artifact 多版本清单
- apps/<app_id>.yaml  每个标配应用自己的配置（模板见 _template-app.yaml）

## 铁律
1. **通用性第一**：本仓库会被不同客户、不同电脑使用。机器相关值（D:/repo、C:/Users、本机 IP）只允许出现在本机配置或环境变量里，仓库文件零硬编码。代码、测试、文档、契约一律不得写死：绝对路径、版本号、网关 URL、appId、数据库/Redis/存储/Nacos 连接值、凭据。
2. 需要这些值时引用本目录配置键；解析顺序：应用配置(apps/) → 环境覆盖(infra/environments 的 environments 段) → 默认值 → 运行时注入(env/仓外凭据文件)。
3. 证据条目仍须保留 artifact + version + sha256——那是证据身份不是路径；来源 jar 路径按 path_template 组装。
4. UDC 不同大版本行为可能不同：版本族隔离（families），新族不覆盖旧族证据；行为差异登记在族内 behavior_diffs。
5. 每个标配应用一份 apps/<app_id>.yaml；客户业务明细按任务临时查询，不进长期事实库。
6. 凭据与连接串的**值**永不入 git：仓库里只有引用键（credential_ref / host_ref），值在运行时注入或仓外文件。

## 新增环境 / 新版本 / 新应用
- 新环境：改 environments.yaml + infra.yaml 的 environments 段，不改代码。
- 新 UDC 版本：artifact-versions.yaml 对应族加版本号 + 取证脚本生成该版本 javap 到 docs/audit/artifacts/<artifact>-<version>/。
- 新应用：复制 apps/_template-app.yaml 为 apps/<app_id>.yaml，按取证填。
