---
name: seeyon-agent
description: "Use when driving Seeyon UDC development tasks from Hermes: dispatch requirements, generate backend/frontend skeletons, run readonly live probes against test2."
version: 1.0.0
---

# Seeyon Agent（Hermes 宿主接入）

Seeyon Agent 是**嵌入宿主的组件**，不是独立 agent。通过 `seeyon_host_bootstrap.bootstrap()` 装配，宿主（Hermes/CC/Codex）注入 context/session/policy。

## 初始化（一次）

```python
import sys; sys.path.insert(0, r"<SEEYON_AGENT_ROOT>")
from seeyon_host_bootstrap import bootstrap
host = bootstrap(credential_file=r"<仓外凭据路径>", allow_network=True)   # 活体
host = bootstrap()                                                        # 离线
```

## 四个能力

| 能力 | 用途 | 边界 |
|---|---|---|
| `host["dispatch"](intent, target)` | 需求→路由→组件→证据化结果 | 只读 |
| `host["generate"](app_id, entity, attrs)` | 后端 8 类 Java 骨架 + 前端页面定义 | 声明级，方法体 UNVERIFIED |
| `host["live_probe"](cred_file)` | test2 4 端点只读 POST 双发 | 默认关，allow_network=True 才联网 |
| `host["agent"]` | 原始 SeeyonAgent（宿主注入 context/session/policy） | 三 Port 协议 |

## 红线

- 写操作一律 DENIED（policy gate），不绕过、不写生产
- 凭据仅路径引用，token 明文 0 入产物/会话/git
- 静态/UNVERIFIED 结论不得报成 LIVE PASS
- token 有时效（test2 operator token ~19h 窗口），临期从 HUMAN 处取新值刷新凭据文件

## 测试

```bash
cd <SEEYON_AGENT_ROOT>
.venv\Scripts\python.exe -m pytest tests -q          # 361 offline 全绿
.venv\Scripts\python.exe run_live_readonly.py --credential-file <path> --allow-network   # 活体 4 端点
.venv\Scripts\python.exe run_multi_live_test.py --allow-network --credential-file <path> # 三类多轮
```
