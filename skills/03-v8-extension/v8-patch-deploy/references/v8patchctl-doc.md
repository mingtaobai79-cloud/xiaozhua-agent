# v8patchctl 补丁工具（官方文档镜像）

> 来源：https://open.seeyoncloud.com/v8doc/2303/2845.html （抓取于 2026-10-30）
> 本文档覆盖 v8patchctl 的完整使用方式，包括前端静态资源、组件库、Nodejs 离线包、客开组件包，以及后端镜像与 Maven 依赖上传。适用于 5.3.0 之前版本。

## 1. 前置准备

### 1.1 安装

直接将程序上传到操作系统的 bin 目录即可。二进制程序直接启动：

```bash
mv v8patchctl-linux-xxx /usr/local/bin/v8patchctl
v8patchctl -h          # 查看帮助
v8patchctl --version   # 版本，格式：分支-commitid-日期
```

### 1.2 基础依赖

- 可访问 Nacos
- 可访问容器镜像仓库
- 可访问对象存储，支持 OBS、OSS、minio
- 可访问 Kubernetes API（补丁包含后端镜像时）

## 2. 基础配置

### 2.1 Nacos 端点（初始化）

```bash
v8patchctl nacos add
# 交互录入：env / server_addr / username / password / namespace / describe

# 也可直接编辑 ~/.v8patchctl/nacos_endpoints.yaml：
# envs:
#   <env>:
#     server-addr: "<内网IP>.1:8848"
#     username: "nacos"
#     password: "xxx"
#     namespace: "<v8的nacos配置命名空间>"
#     describe: 备注

v8patchctl nacos list                    # 列出环境
v8patchctl nacos update --env <env>      # 更新
v8patchctl nacos remove --env <env>      # 删除
```

### 2.2 Nacos public 配置（对象存储）

支持 MinIO / OBS / OSS。

### 2.3 日志记录

默认记录在 `/var/log/v8patchctl/`，每次打包生成一个日志文件：`/var/log/v8patchctl/patchctl_<日期>_<时间>.log`

## 3. 命令概览

```bash
# 3.1 拉取 Nacos 公共配置（验证配置可用性，无副作用）
v8patchctl --env <env> pull-public

# 3.2 上传补丁（真正执行补丁更新操作）
v8patchctl --env <env> upload --zip ./your_patch.zip   # zip 支持本地路径或 http/https
```

### 3.3 常用参数

- `--zip`：补丁包路径（本地或 http/https）
- `--env`：环境名，对应 nacos_endpoints.yaml 中的 env
- `--prefix`：覆盖前端上传前缀（仅对常规前端补丁生效）
- `--dry-run`：仅打印行为，不实际上传/变更
- `--skip-backup`：跳过前端备份逻辑
- `--keep`：备份保留数量（默认 3）
- `--tmpdir`：指定临时目录
- `--namespace`：K8s namespace（覆盖配置）
- `--registry`：镜像仓库地址（覆盖配置）
- `--kubeconfig`：kubeconfig 路径（覆盖配置）
- `--version`：输出版本并退出

## 4. 前端补丁处理规则

### 4.1 常规前端补丁

结构：`<appname>/frontend/content/...`

- 上传到 `<appname>/` 前缀，支持 `--prefix` 覆盖
- 触发备份到 `__backup/<appname>/<timestamp>/`

### 4.2 组件库补丁（fe_comp/web/libs）

结构（固定）：`fe_comp/web/libs/...`

- 上传到 `libs/` 前缀
- 触发备份到 `__backup/libs/<timestamp>/`

### 4.3 Nodejs 离线包补丁（fe_comp/nodejs）

结构（固定）：`fe_comp/nodejs/...`

- 上传到 `frontend-dependencies/udc-offline-pkgs/` 前缀
- 不触发备份

### 4.4 客开 custom-extensions 离线包补丁

结构（固定）：`custom-extensions/...`

- 上传到 `custom-extensions` 前缀
- 触发备份到 `__backup/custom-extensions/<timestamp>/`

## 5. 后端补丁处理规则

### 5.1 后端镜像 tar

结构示例：`<appname>/backend/*.tar`

行为：
1. 通过 `skopeo` 读取 tar 中的镜像引用
2. 用「镜像 tag 包含 Deployment 名称」进行匹配
3. 以 Deployment 当前镜像为准构造目标镜像（仅替换 tag；registry 可由 `--registry` 覆盖）
4. 将镜像推送到目标仓库
5. 更新 K8s Deployment 镜像（namespace 来自配置或 `--namespace`）

匹配示例：
- 导入镜像：`dockerhub.kubekey.local/seeyon/seeyon:m5-5.6.13`
- Deployment：`m5`（tag 中包含 `m5`）
- 目标镜像：`<deployment 当前镜像的 registry/repo>:m5-5.6.13`

说明：如果同一个 tag 命中多个 Deployment，会报歧义错误。

### 5.2 Maven 依赖目录

结构示例（目录名固定为 `backend-dependencies`）：`<appname>/backend/backend-dependencies/...`

- 上传到对象存储 `maven-dependencies/` 前缀

## 6. 组合补丁

一个 zip 包可同时包含：常规前端 / `fe_comp/web/libs` / `fe_comp/nodejs` / `custom-extensions` / 后端镜像 tar / `backend-dependencies`。命中多种类型时，会依次执行多次上传与后端更新。

## 7. 常见操作示例

```bash
# 补丁更新（默认前缀）
v8patchctl --env <env> upload --zip ./patch.zip

# 干跑，演练不实际上传执行
v8patchctl --env <env> upload --zip ./patch.zip --dry-run

# 跳过备份
v8patchctl --env <env> upload --zip ./patch.zip --skip-backup

# 指定 K8s namespace 与 registry
v8patchctl --env <env> upload --zip ./patch.zip --namespace <ns> --registry registry.example.com
```

## 8. 故障排查

- 镜像未匹配：确保导入镜像 tag 中包含目标 Deployment 名称
- `Error loading trust policy: no policy.json`：skopeo 需要 `/etc/containers/policy.json`（内网全放行版见 SKILL.md §2）

## 9. 下载链接

v8patchctl 二进制（百度网盘，提取码 5h3v）：https://pan.baidu.com/s/1bNimPtPma688cmxBAIAdzg