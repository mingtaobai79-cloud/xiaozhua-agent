---
name: v8-patch-deploy
version: 0.1.0
author: xiaozhua-agent
license: MIT
description: Use when 打 V8 平台 BP 补丁（v8patchctl）：拉包校验、dry-run、上传、skopeo 修复。
tags: [xiaozhua, v8, patch, v8patchctl, skopeo, deploy]
metadata:
  hermes:
    tags: [xiaozhua, v8, patch, v8patchctl, skopeo, deploy]
    related_skills: [xiaozhua-low-code-environment, v8-workbench-client-setup]
---

# V8 平台补丁部署（v8patchctl）

给致远 V8 低代码平台的环境打官方补丁包（如 organization 5.3.601）的完整流程。覆盖：拉包、校验、v8patchctl 上传、skopeo policy.json 修复、工具安装、发布验证。

**本 SKILL 不写死环境名/IP/路径**：env 名（如 test2/uat）、目标机器、namespace、kubeconfig 路径、补丁包存放目录，全部以现场实际为准，每次任务先探测再执行（见 §0 现场探测）。流程本身是通用的，任何一套 V8 环境都照这个走。

## 0. 现场探测（每次任务第一步，别凭记忆）

打补丁前先弄清四件事：

1. **v8patchctl 在哪台机器**：在各候选机器上 `which v8patchctl && v8patchctl --version`。工具通常只装在其中一台运维机上；没有就按 §工具安装 装。
2. **env 列表**：`cat ~/.v8patchctl/nacos_endpoints.yaml` 看已配了哪些 env；目标环境没配就 `v8patchctl nacos add` 录入（要 Nacos 地址/账号/namespace）。
3. **kubeconfig 与 namespace**：`ls ~/.kube/` 或 `ls /root/ | grep -i kube` 找 kubeconfig；`kubectl --kubeconfig=<path> get ns` 列真实 namespace，再 `grep -i <app>` 找目标 Deployment 在哪个 ns。kubeconfig 没 current-context 不影响 get。
4. **磁盘水位**：`df -h /`。打补丁要容纳 zip + 解压临时目录 + 镜像 tar（可能是包体积的 2~3 倍）。

补丁包放哪以现场约定为准（/root、/data/v8/patchs 等），找不到就 `find / -maxdepth 3 -name 'BP_*.zip' -not -path '/proc/*' 2>/dev/null`。

## When to Use

用户给了一个 `BP_xxx_V5.3_X86_MICRO_<app>.zip` 的补丁下载链接（一般来自 open.seeyoncloud.com），要求打到某些环境。

## 标准流程（六步）

### 1. 拉补丁包到运维机（能直接拉就服务器上拉，别经过本机中转）

优先让 curl 直接跑在服务器上（内网→对象存储通常 10MB/s+，1GB 约 80 秒）：

```bash
curl -o <存放目录>/BP_organization.zip '<完整签名URL>'
```

**校验（必做）：**

```bash
ls -l <zip>                          # 字节数与本机下载/官方页对比，一字节不差
unzip -t <zip> | tail -2             # 期望 "No errors detected in compressed data"
unzip -l <zip> | head -30            # 顶层结构：应有 patch.properties 和 <appname>/ 目录
unzip -p <zip> patch.properties | grep -E 'patchnum|productversion|appkey|deploytype'   # 补丁元信息
```

**注意：**
- 签名 URL 里 `%3D` 等已编码字符**原样保留**，不要二次解码；用**单引号**包 URL，防 shell 吃掉 `%` 和 `&`。
- 同一 URL 若被重复启动 curl，会写坏文件（两个 curl 同时写同一目标）；发现残留先 `pkill -f BP_xxx && rm -f <zip>` 再重下。
- 签名 URL 有 Expires，过期后要重新生成，别拿旧链接反复试 403。
- OSS 链接对 HEAD 请求也校验签名——用 `curl -I` 预检会报 SignatureDoesNotMatch，**不代表链接坏了**，换 GET 试。

### 2. 前置：skopeo 的 policy.json 必须先建好

**v8patchctl 走到后端镜像推送那步会调用 skopeo，而 skopeo 强制要 `/etc/containers/policy.json`，没配过的机器第一次必踩。** 提前建：

```bash
mkdir -p /etc/containers
cat > /etc/containers/policy.json <<'EOF'
{
    "default": [
        {
            "type": "insecureAcceptAnything"
        }
    ]
}
EOF
```

内网私有仓库用 `insecureAcceptAnything` 是内网场景标准做法。若推镜像再报 TLS 证书错，v8patchctl 自带 `--dest-tls-verify=false` 自动回退，一般能自己过。

### 3. dry-run 演练（先打低风险环境）

```bash
v8patchctl --env <env> upload --zip <zip> --dry-run
```

读输出确认三件事：
- **补丁类型识别**：常见两类同时出现（如 organization 包 = `backend-dependencies` Maven 依赖 + `<app>.tar` 后端镜像）
- **镜像匹配**：`Matched source .../<app>:<ver> to deployment <app>` —— tag 必须包含 Deployment 名，否则报歧义
- **目标 namespace**：dry-run 会打出目标 namespace；**对照第 0 步用真实 kubeconfig 查到的 ns**，不一致就加 `--namespace <真实ns>` 覆盖

### 4. 正式上传

```bash
v8patchctl --env <env> upload --zip <zip>
```

预期输出顺序：Maven 依赖逐条 `Upload ok` → `Found N backend image tar files` → skopeo 推镜像 → 更新 Deployment。日志同时落在 `/var/log/v8patchctl/patchctl_<时间戳>.log`。

Maven 依赖是幂等上传，同版本重复跑会覆盖同名文件，不会出问题。

### 5. 验证

```bash
kubectl --kubeconfig=<kubeconfig> -n <ns> get deploy <app> -o wide   # 镜像应为 .../<app>:<新版本tag>
kubectl --kubeconfig=<kubeconfig> -n <ns> rollout status deploy <app>
kubectl --kubeconfig=<kubeconfig> -n <ns> get pods | grep <app>
```

三项全过 = 该环境打补丁完成。

### 6. 其余环境再来一遍

上一个环境验收通过后，同一条命令换 env：

```bash
v8patchctl --env <env2> upload --zip <zip> --dry-run
v8patchctl --env <env2> upload --zip <zip>
```

注意不同 env 的 namespace 通常是**另一个值**，dry-run 时再看一眼，别照抄上一个环境的。多环境共用同一个 zip，不用重拉。

## 工具安装（运维机上没有 v8patchctl 时）

1. **下载二进制**：官方文档给的百度网盘地址（见参考文档），文件名形如 `v8patchctl-linux-xxx`。本机下载后 scp 上去，或服务器直接 curl 可达的源。
2. **安装**：`mv v8patchctl-linux-xxx /usr/local/bin/v8patchctl && chmod +x /usr/local/bin/v8patchctl`
3. **验证**：`v8patchctl --version`（格式：`分支-commitid-日期`）、`v8patchctl -h`
4. **初始化环境配置**：`v8patchctl nacos add` 按提示录入每个环境的 Nacos 地址/账号/namespace；或直接编辑 `~/.v8patchctl/nacos_endpoints.yaml`。录完 `v8patchctl --env <env> pull-public` 验证配置可拉。
5. **前置依赖**：能通 Nacos、容器镜像仓库、对象存储（OBS/OSS/minio）；补丁含后端镜像时还要能通 K8s API，且**装 skopeo**（`yum install -y skopeo` 或 apt），并按第 2 步配好 policy.json。

## 补丁包结构速查（v8patchctl 自动分流）

```text
<appname>/frontend/content/...        → 常规前端，传 <appname>/ 前缀，自动备份
fe_comp/web/libs/...                  → 组件库，传 libs/ 前缀，自动备份
fe_comp/nodejs/...                    → nodejs 离线包，传 frontend-dependencies/udc-offline-pkgs/，不备份
custom-extensions/...                 → 客开扩展，传 custom-extensions 前缀，自动备份
<appname>/backend/*.tar              → 后端镜像，skopeo 推仓库 + 更新 Deployment（tag 须含 Deployment 名）
<appname>/backend/backend-dependencies/ → Maven 依赖，传 maven-dependencies/ 前缀
```

同一 zip 可混装多类，工具自动识别分流。补丁元信息看 zip 顶层的 `patch.properties`（patchnum/description/appkey/deploytype/productversion）。

## 历史手工流程（某环境没装 v8patchctl 时的对照）

老环境可能一直用手工流程打补丁，目录残留可当参照（每个补丁一个日期目录）：

```text
/root/<日期>/
├── BP_xxx_V5.3_X86_MICRO_xxx.zip   # 原始补丁包
├── patch.properties                 # 补丁元信息（patchnum/description/appkey/deploytype）
├── meta.properties
├── application.yaml
├── fe_comp/  <app>/  <app>.tar
└── _downloads/
```

老流程 = 手工 unzip → ossutil 传对象存储（先 cp 备份原目录）→ kubectl rollout restart deployment。**有 v8patchctl 后不再手工走这条路**，但目录结构可用于判断旧补丁类型。

## Troubleshooting

| 症状 | 原因 | 处置 |
|---|---|---|
| `Error loading trust policy: no policy.json` | skopeo 首次使用，缺 `/etc/containers/policy.json` | 按第 2 步建文件后重跑 |
| `open zip ...: no such file or directory` | zip 被挪走/误删，或路径写错 | 按第 0 步探测实际位置 |
| `403 SignatureDoesNotMatch`（GET 也报） | 签名 URL 过期或被改动 | 重新生成下载链接 |
| `curl -I` 报 403 | OSS 对 HEAD 也验签，属预期 | 不代表链接坏，直接 GET |
| dry-run 只打一行 `Logging to...` 就退出 | 正常 | 看后续 `Dry run:` 行，不是卡住 |
| 推镜像 TLS/cert 错 | 私有仓库证书 | 等自动 fallback，仍不行则 `--registry` 手动指定或检查 harbor 可达性 |
| 镜像 tag 匹配多个 Deployment | tag 不含 Deployment 名或含糊 | 报歧义错，检查 tar 里 manifest.json 的 repoTags |
| namespace 查不到 Deployment | kubeconfig 的 ns 和 dry-run 打的不一致 | `--namespace <真实ns>` 覆盖 |

## 经验教训（2026-10-30 实战沉淀）

- **rm 批量清理时反斜杠续行别把补丁包路径误包进去**——本次实际误删过一次，靠本机留的副本重拉的。重要下载件本机始终留一份副本。
- **工具位置和补丁包路径都可能被同事挪动**，每次以现场探测为准（§0），别只认上次会话的路径。
- **一台机器没有工具 ≠ 环境不可用**：先探测所有候选机器（跳板机/运维机），都没有再按 §工具安装 装。
- **kubeconfig 显示 current-context is not set 不影响使用**，直接 get 资源验证。

## 关键命令速查

```bash
# 现场探测
which v8patchctl && v8patchctl --version
cat ~/.v8patchctl/nacos_endpoints.yaml
kubectl --kubeconfig=<path> get ns
kubectl --kubeconfig=<path> get deploy -A | grep -i <app>
df -h /

# 补丁流程
v8patchctl --env <env> upload --zip <zip> --dry-run   # 演练
v8patchctl --env <env> upload --zip <zip>             # 正式打
cat /var/log/v8patchctl/patchctl_<ts>.log             # 看日志
kubectl --kubeconfig=<path> -n <ns> get deploy <app> -o wide
kubectl --kubeconfig=<path> -n <ns> rollout status deploy <app>
```

## 参考文档

- v8patchctl 官方完整文档：https://open.seeyoncloud.com/v8doc/2303/2845.html（本地镜像：references/v8patchctl-doc.md）
- 补丁工具二进制下载（百度网盘，提取码 5h3v）：https://pan.baidu.com/s/1bNimPtPma688cmxBAIAdzg
- 功能流程：前端静态资源/组件库/nodejs离线包/客开 custom-extensions → 对象存储；后端镜像 tar → skopeo 推仓库 + 更新 Deployment；backend-dependencies 目录 → OSS maven-dependencies/ 前缀。同一 zip 可混装多类，工具自动分流。