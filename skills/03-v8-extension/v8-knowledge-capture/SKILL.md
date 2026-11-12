---
name: v8-knowledge-capture
description: 把员工确认过的经验写入 V8 知识库。用户说“归档知识库、新增知识库、总结到知识库、沉淀到知识库、写成知识库文章”时使用。先展示正文，确认后再写入；不要用于检索、问答或自动保存未确认对话。
---

# V8 知识沉淀

用户说归档知识库、新增知识库、总结到知识库、沉淀到知识库或写成知识库文章时，都按本 Skill 写入，不要改走知识检索，也不要调用任何 MCP 工具传正文。这些说法表示保存一篇经验，不是查询已有资料。

不要向员工索要 UUID 或姓名。身份已经写在 v8-workbench 的 MCP 地址里。

确认后把 Markdown 保存成本地文件，只用下面的 POST 提交。命令自己读文件并编码，不要把文件内容或 Base64 贴进对话、工具参数或 MCP。远程 MCP 读不到员工电脑上的文件，模型抄写长参数会被截断，内网网关还会重置含 `.../` 或连续 SQL 的原文请求。

```bash
python3 - 待归档.md "文档标题" << 'PY'
import base64, json, sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

file_path, title = sys.argv[1], sys.argv[2]
home = Path.home()
url = ""
opencode = home / ".config/opencode/opencode.json"
if opencode.is_file():
    data = json.loads(opencode.read_text(encoding="utf-8"))
    url = str(((data.get("mcp") or {}).get("v8-workbench") or {}).get("url") or "")
if "v8_user_id=" not in url:
    codex = home / ".codex/config.toml"
    if codex.is_file():
        section = codex.read_text(encoding="utf-8").split("[mcp_servers.v8-workbench]", 1)[-1]
        for line in section.splitlines():
            if line.strip().startswith("["):
                break
            if line.strip().startswith("url"):
                url = line.split("=", 1)[-1].strip().strip('"').strip("'")
                break
parsed = urlsplit(url)
if "v8_user_id=" not in parsed.query or "v8_display_name=" not in parsed.query:
    raise SystemExit("未找到已绑定身份的工作台地址，请先安装工作台并填写姓名。")
target = urlunsplit((parsed.scheme, parsed.netloc, "/api/knowledge/archive", parsed.query, ""))
raw = Path(file_path).read_bytes()
body = json.dumps({"title": title, "content": "b64:" + base64.b64encode(raw).decode()}, ensure_ascii=False).encode()
with urlopen(Request(target, data=body, headers={"Content-Type": "application/json"}, method="POST"), timeout=60) as response:
    print(response.read().decode())
PY
```

macOS、Linux、Windows 都用这条命令，只要本机有 python3。返回 `queued` 表示已写入并进入索引队列。这条 POST 会自动记入使用统计，不要再调用 MCP 补记。需要立刻检索时，等索引完成后再用 `search_v8_knowledge` 验证。
