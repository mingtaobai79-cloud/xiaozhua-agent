# CHANGELOG

## 0.2.0 — 2026-11-23

安装与升级变成一条命令，跨平台（Windows / macOS / Linux）。

### 新增

- `scripts/install.ps1` —— Windows 一键装：
  `irm https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.ps1 | iex`
- `scripts/install.sh` —— macOS / Linux 一键装：
  `curl -fsSL .../scripts/install.sh | bash`
- `xiaozhua` 命令（`installer/selfupdate.py`，零第三方依赖）：
  - `xiaozhua update` 拉代码 → 快进合并 → 装依赖 → 重装宿主配置 → 真起 MCP 自检 → 记状态
  - `xiaozhua doctor` 体检（默认不联网，`--fetch` 才比落后提交）
  - `xiaozhua install` 转发 `installer/install.py`
  - `xiaozhua version`
- `tests/test_selfupdate.py` 11 条离线契约测试（含 `bash -n` 与文档 URL 同源校验）

### 行为细节（都是刻意的）

- **脏工作区不自动 stash**：本地改动可能是未提交证据，`update` 直接拒绝（退出码 3）
- `update` 每个失败态有独立退出码（2 非 git / 3 脏 / 4 分叉 / 5 依赖 / 6 宿主 / 7 自检）
- 安装全部落在 `~/.xiaozhua/{src,venv,pkg,bin}`，**不碰系统 Python**，卸载 = 删目录
- macOS：自动找 `python3.12`（系统自带 3.9 不够），避开 `readlink -f` 与 bash 4 语法
- Windows：`install.ps1` 存为 UTF-8 **带 BOM**（PS 5.1 否则按 GBK 读，中文变乱码并报"缺 }"）

### 清理

- 删除 34 个 `__pycache__` / `.pytest_cache`（不含 `.venv`）
- `docs/audit/p0-custom-trigger/cleanup-backup/` 入 `.gitignore`（原始抓包已汇总进审计文档，文件保留在盘上）

## 0.1.0 — 2026-11-12

首个可分发的 MCP 能力包。**54 个工具**：平台侧 42 个（21 个真机验证过），本地 12 个。

### 能力

- **setting 域**：枚举 / 枚举项 / 枚举分类 / 选项集分类 / 字段集 / 字段集字段 / 参数 /
  二维码 / 扩展选项 / 扩展字段 / 流水号方案 / 流水号段 / 事件 / 事件数据
- **entity 域**：DTO / 索引 / 参照配置 / 部署方案
- **application 域**：版本列表 / 构建信息 / 依赖增删 / 部署 body
- **flow 域**：微流程节点构造、闸门校验、触发器、发布（未真机验证）
- **page 域**：列表页 / 详情页 schema 骨架、自定义页面脚手架（未真机验证）
- **expression 域**：89 个预设函数目录、表达式校验与过滤
- **本地工具**：仓库状态与同步、代码落点、工程形态、SPI 目录、需求生成骨架

### 真机验证（test2）

本轮新增验证 9 个工具并修复 4 个真 bug。

**验证通过（闭环 = create → 回读 → delete）**

| 工具 | 入口 |
|---|---|
| `serial_scheme_body` / `serial_section` | `udcSerialSchemeCreatePost` |
| `dto_body` | `udcDataTransferObjectPost` |
| `scalability_field_body` | `udcScalabilityPost` |
| `index_body` | `udcIndexPost` |
| `refer_config_body` | `udcReferConfigCreateConfigInfoPost` |
| `event_body` | `udcEventPost` |
| `event_data_body` | `udcEventCreateWithDataPost` |
| `app_version_list` | REST `search-app-edition` |
| `app_build_info` | `udcSandboxBuildInfoAppGet` |
| `app_dependency_body` | `udcApplicationDependentApplicationCreateBatchPost` |

### 修复

1. **`app_build_info` 参数类型** —— `udcSandboxBuildInfoAppGetInputBody` 在平台上不存在，
   必须是 `Map`。按名称猜 InputBody 在这个 operation 上不成立（`path:` 入参，平台未生成该类型）。
2. **`PageFetch` 命中 `/login/` 标签页** —— 同一浏览器同时开着登录页和工作页时会挑中登录页，
   请求全部打到登录页，平台回 `Unknown type xxxInputBody`，被误判成类型名写错。
   现在优先选非 `/login` 的页面。
3. **`scalability_field_body` 的 `dataTypeProperties`** —— 空字符串导致 `BOOT_3000`
   且 `message: null`（无任何线索）。缺省改为 `{}`；STRING/LONG/DATE/DOUBLE 四类实测均通过。
4. **`event_data_body`** —— `eventDataList` 必须是数组（传单对象报反序列化失败）；
   `attributes[].name` 增加回退到 `name` 键。

### 分发可用性

- **缺 pyyaml 时 `tools/list` 直接 internal error** —— 已改为延迟报错，
  缺依赖时仍能列出全部 54 个工具，只在真正读 config 时提示安装命令。
- **`pyproject.toml` 补 `websocket-client`** —— `PageFetch` 依赖它，原先未声明，
  远程装完一调用就 `ModuleNotFoundError`。
- **installer 删掉写死的 5 个 v1 工具名**。

### 已知不通

- `excel_template_body` / `excel_template_column`：test2 上
  `/service/udc/excel/template/create` 返回 Spring 404，
  `/udc/excel/template/create` 返回 OSS MethodNotAllowed。契约标 LIVE PASS，实测链路缺失。

### 操作纪律问题

- **误删 test2 应用依赖 `cip-manager`**（该行 `enableDelete: true`，平台允许删，
  界面为绿色「移除」）。已补回，**版本未变（5.3.273）**，仅行 id 变化。
  详见 `docs/audit/INCIDENT-20261112-deleted-builtin-dependency.md`。
  教训：验证删接口要 create 自己的数据再删，不要拿现成配置当试验品。

### 测试

`3172 passed / 23 skipped`（3195 collected）。
