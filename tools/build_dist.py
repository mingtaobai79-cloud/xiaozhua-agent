#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""tools/build_dist.py — 打一个可分发的 Seeyon Agent 能力包（zip）。

**为什么不打 wheel**：这个仓库的主体不是 Python 包，而是**角色能力包** ——
`core/facts/` 1.4 MB 事实文档、`skills/`、`adapters/` 三宿主适配、`docs/` 契约层。
这些都是运行时读取的数据文件，塞进 wheel 的 `package_data` 会扭曲包结构，
装完还得靠 `importlib.resources` 到处找路径。分发 zip 解压即用，三宿主通用。

包内结构（保持仓库相对路径，installer / MCP server 都不需要改路径推导）::

    seeyon-agent-<version>/
      INSTALL.md           首次接入指引（从 HOW-TO-CONNECT 裁剪）
      MANIFEST.json        文件清单 + sha256 + 统计
      VERSION              版本号
      python/              可选：内置解释器提示（不打包 venv）
      <仓库内容>

排除：.git / .venv / __pycache__ / tests / scratch / _attic_pending /
      docs/audit（百万行审计产物，不进分发包）

用法::

    python tools/build_dist.py                 # 写到 dist/seeyon-agent-<ver>.zip
    python tools/build_dist.py --out D:/tmp    # 指定输出目录
    python tools/build_dist.py --verify FILE   # 校验已有包的完整性
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO / "VERSION"

# 不进分发包
EXCLUDE_DIRS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "tests", "scratch", "_attic_pending", "dist", "build", "node_modules",
    ".idea", ".vscode",
}
EXCLUDE_PREFIXES = (
    "docs/audit/",            # 百万行审计产物
    "core/facts/spi/evidence/",  # 13 份原始证据，体积大且非运行时必需
)
EXCLUDE_SUFFIXES = (".pyc", ".pyo", ".log", ".bak", ".tmp")
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db", "SOUL.md"}

# 必须进包（缺了不算可分发）
REQUIRED = [
    "README.md",
    "pyproject.toml",
    "seeyon_host_bootstrap.py",
    "adapters/mcp/server.py",
    "adapters/mcp/DESIGN.md",
    "installer/install.py",
    "docs/operation-contracts/mcp/TOOLS.md",
    "docs/operation-contracts/mcp/HOW-TO-CONNECT.md",
]

INSTALL_MD = """# Seeyon Agent 能力包 {version}

> 生成时间：{built}
> 包内文件：{n_files} 个 / {size_mb:.1f} MB（压缩后 {zip_mb:.1f} MB）

## 一、解压后先做这三步

```bash
# 1) 建虚拟环境（需要 Python 3.12+）
python -m venv .venv
.venv/Scripts/activate          # Windows
# source .venv/bin/activate     # Linux / macOS

# 2) 装依赖
pip install -e .

# 3) 自检（不联网，应打印出能力数）
python -c "from seeyon_host_bootstrap import bootstrap; print(len(bootstrap()))"
```

能打印出数字就说明装配正常。

## 二、接进宿主

**Hermes** — 贴进 `~/.hermes/config.yaml` 顶层：

```yaml
mcp_servers:
  seeyon:
    command: <包根目录>/.venv/Scripts/python.exe
    args:
      - <包根目录>/adapters/mcp/server.py
    timeout: 180
```

**Codex** — `~/.codex/config.toml`：

```toml
[mcp_servers.seeyon]
command = "<包根目录>/.venv/Scripts/python.exe"
args = ["<包根目录>/adapters/mcp/server.py"]
```

**Claude Code** — 项目根 `.mcp.json`：

```json
{{
  "mcpServers": {{
    "seeyon": {{
      "command": "<包根目录>/.venv/Scripts/python.exe",
      "args": ["<包根目录>/adapters/mcp/server.py"]
    }}
  }}
}}
```

或者一条命令生成三宿主配置：

```bash
python installer/install.py --host all --target <输出目录> --portable
```

## 三、验证

配完重启宿主，调：

```
seeyon_capability_index()
```

返回 `domain_count: 9`、`summary.契约合计: 133` 就是通了。

## 四、包内有什么

```
seeyon_host_bootstrap.py      能力装配入口（MCP 工具就是它的能力投影）
adapters/mcp/server.py        MCP 传输层（stdio JSON-RPC 2.0）
adapters/{{hermes,codex,claude-code}}/   三宿主适配件
components/                   能力实现（44 个工具的构造器都在这）
core/facts/                   事实层（{n_facts} 份 markdown，回答"实际长什么样"）
docs/operation-contracts/     契约层
docs/operation-contracts/mcp/TOOLS.md          44 个工具权威清单
docs/operation-contracts/mcp/HOW-TO-CONNECT.md 接入详解 + 六条边界
installer/install.py          三宿主安装器
tools/gen_mcp_manifest.py     改了工具面就重跑它
```

## 五、边界

```
① 全部工具只出 data，不落库。落库由宿主拿 body 自己去 POST。
② 4 个凭据工具（microflow_publish / expression_verify / expression_filter /
   entity_rule_publish）强制 host+cookie 必填，不传调不起来。
③ 菜单（menu 域）不提供工具：只推进了建节点，页面控件组件不会用。
④ 首次接入务必读 docs/operation-contracts/mcp/HOW-TO-CONNECT.md 的「六条边界」。
```

## 六、完整性校验

```bash
python tools/build_dist.py --verify <本包路径>   # 需要本包内的 tools/
```

或直接看 `MANIFEST.json` 里的 `sha256` 逐文件比对。
"""


def _version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    import re
    m = re.search(r'^version\s*=\s*"([^"]+)"',
                  (REPO / "pyproject.toml").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else "0.0.0"


def _included(rel: str) -> bool:
    parts = rel.split("/")
    if any(p in EXCLUDE_DIRS for p in parts[:-1]):
        return False
    if parts[0] in EXCLUDE_DIRS:
        return False
    if any(rel.startswith(p) for p in EXCLUDE_PREFIXES):
        return False
    if rel.endswith(EXCLUDE_SUFFIXES):
        return False
    if parts[-1] in EXCLUDE_NAMES:
        return False
    return True


def _walk() -> list[Path]:
    out = []
    for p in sorted(REPO.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(REPO).as_posix()
        if _included(rel):
            out.append(p)
    return out


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(out_dir: Path) -> Path:
    version = _version()
    files = _walk()
    total = sum(f.stat().st_size for f in files)

    missing = [r for r in REQUIRED if not (REPO / r).exists()]
    if missing:
        raise SystemExit("缺必需文件，拒绝打包：%s" % missing)

    n_facts = len(list((REPO / "core" / "facts").rglob("*.md")))
    built = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / ("seeyon-agent-%s.zip" % version)

    manifest = {"name": "seeyon-agent", "version": version, "built": built,
                "file_count": len(files), "total_bytes": total, "files": {}}

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        root = "seeyon-agent-%s" % version
        for f in files:
            rel = f.relative_to(REPO).as_posix()
            z.write(f, "%s/%s" % (root, rel))
            manifest["files"][rel] = {"bytes": f.stat().st_size, "sha256": _sha256(f)}
        if "VERSION" not in manifest["files"]:
            z.writestr("%s/VERSION" % root, version + "\n")
        if "MANIFEST.json" not in manifest["files"]:
            z.writestr("%s/MANIFEST.json" % root,
                       json.dumps(manifest, ensure_ascii=False, indent=2))
        if "INSTALL.md" not in manifest["files"]:
            z.writestr("%s/INSTALL.md" % root,
                       INSTALL_MD.format(
                           version=version, built=built, n_files=len(files),
                           size_mb=total / 1048576,
                           zip_mb=total / 1048576 * 0.3,
                           n_facts=n_facts))

    zip_mb = target.stat().st_size / 1048576
    print("已写 %s" % target)
    print("  版本      %s" % version)
    print("  文件      %d 个 / %.1f MB（原始）" % (len(files), total / 1048576))
    print("  压缩后    %.1f MB（压缩率 %.0f%%）" % (zip_mb, 100 * zip_mb / (total / 1048576)))
    print("  事实文档  %d 份" % n_facts)
    print("  sha256    %s" % _sha256(target))
    return target


def verify(path: Path) -> int:
    if not path.exists():
        print("FAIL: 文件不存在 %s" % path)
        return 1
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        manifest_name = [n for n in names if n.endswith("/MANIFEST.json")]
        if not manifest_name:
            print("FAIL: 包里没有 MANIFEST.json")
            return 1
        manifest = json.loads(z.read(manifest_name[0]).decode("utf-8"))
        root = manifest_name[0].rsplit("/", 1)[0]
        bad = []
        for rel, meta in manifest["files"].items():
            entry = "%s/%s" % (root, rel)
            if entry not in names:
                bad.append((rel, "缺失"))
                continue
            data = z.read(entry)
            if hashlib.sha256(data).hexdigest() != meta["sha256"]:
                bad.append((rel, "sha256 不符"))
        print("包      %s" % path)
        print("版本    %s" % manifest["version"])
        print("文件    %d 个（清单声明）" % manifest["file_count"])
        if bad:
            print("FAIL: %d 个文件不一致" % len(bad))
            for rel, why in bad[:20]:
                print("  %s  %s" % (rel, why))
            return 1
        print("OK: 全部文件 sha256 一致")
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="打分发 zip")
    ap.add_argument("--out", default=str(REPO / "dist"), help="输出目录")
    ap.add_argument("--verify", metavar="FILE", help="校验已有包")
    a = ap.parse_args()
    if a.verify:
        return verify(Path(a.verify))
    build(Path(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
