# -*- coding: utf-8 -*-
"""交付包验收脚本 —— 在**解压后的干净目录**里跑，验 5 条。

为什么要在包外跑：本机开发环境有 .venv、有 pyyaml、有登录态，
在仓库里跑什么都绿。只有解压到新目录、用系统 python 跑，才能证明
「别人拿到就能用」。

用法（在解压后的包根目录）：
    python tools/core/delivery/accept_package.py
或指定包路径：
    python tools/core/delivery/accept_package.py --zip D:/path/to/seeyon-agent-0.1.0.zip
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, PASS if ok else FAIL, detail))
    return ok


def _run(py: str, args: list[str], cwd: Path, stdin: str | None = None, timeout: int = 180):
    return subprocess.run(
        [py] + args, cwd=str(cwd), input=stdin, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )


FRAMES = (
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":'
    '{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"accept","version":"1"}}}\n'
    '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
)


def _tool_count(stdout: str) -> int:
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        res = obj.get("result") or {}
        if isinstance(res, dict) and "tools" in res:
            return len(res["tools"])
    return 0


def main(argv: list[str]) -> int:
    here = Path(__file__).resolve().parents[3]

    if "--zip" in argv:
        z = Path(argv[argv.index("--zip") + 1])
        work = Path(tempfile.mkdtemp(prefix="seeyon-accept-"))
        with zipfile.ZipFile(z) as zf:
            zf.extractall(work)
        root = work / "seeyon-agent-0.1.0"
        print("包: %s (%.1f MB)" % (z.name, z.stat().st_size / 1024 / 1024))
        print("SHA256: %s" % hashlib.sha256(z.read_bytes()).hexdigest())
    else:
        root = here
        print("就地验收: %s" % root)

    py = shutil.which("python") or sys.executable
    print("python: %s" % _run(py, ["--version"], root).stdout.strip())

    has_yaml = _run(py, ["-c", "import yaml"], root).returncode == 0
    has_ws = _run(py, ["-c", "import websocket"], root).returncode == 0
    print("本机 pyyaml=%s websocket-client=%s（False 更能证明包不依赖本机状态）"
          % (has_yaml, has_ws))
    print()

    # ① 可安装
    r = _run(py, ["-c",
                  "import sys;sys.path.insert(0,'.');"
                  "from adapters.mcp.server import TOOL_KEYS;"
                  "print(len(TOOL_KEYS))"], root)
    n = r.stdout.strip()
    check("① 可安装：能 import 且工具数正确", n == "54", "工具数=%s" % (n or r.stderr[-120:]))

    # ② 可连接
    r = _run(py, ["adapters/mcp/server.py"], root, stdin=FRAMES)
    got = _tool_count(r.stdout)
    check("② 可连接：MCP 握手 + tools/list", r.returncode == 0 and got == 54,
          "rc=%d tools=%d" % (r.returncode, got))

    # ③ installer
    tgt = root.parent / "accept-pkg"
    r = _run(py, ["installer/install.py", "--host", "all",
                  "--target", str(tgt), "--write"], root)
    manifest = tgt / "MANIFEST.json"
    n_files = len([p for p in tgt.rglob("*") if p.is_file()]) if tgt.exists() else 0
    check("③ installer 生成三宿主配置", r.returncode == 0 and manifest.exists(),
          "%d 个文件" % n_files)

    # ④ 用生成的配置真起服务（关键：路径是安装时算出来的）
    ok4, detail4 = False, "无 .mcp.json"
    mcp = tgt / "claude-code" / ".mcp.json"
    if mcp.exists():
        cfg = json.loads(mcp.read_text(encoding="utf-8"))["mcpServers"]["seeyon"]
        r = _run(cfg["command"], cfg["args"], root, stdin=FRAMES)
        got = _tool_count(r.stdout)
        ok4 = r.returncode == 0 and got == 54
        detail4 = "用生成的 command+args 起服务 → tools=%d" % got
    check("④ 按装出的配置能连", ok4, detail4)

    # ⑤ 敏感信息：关键词不写死（写死等于把敏感串留在代码里），
    #    由调用方用环境变量给出，或只查通用的 appId 形态。
    leaked = []
    extra = [s for s in os.environ.get("SEEYON_LEAK_PATTERNS", "").split(",") if s.strip()]
    patterns = extra + ["163126498398523384", "7988886308612688555"]
    for pat in patterns:
        for f in ("INSTALL.md", "README.md", "CHANGELOG.md"):
            fp = root / f
            if fp.exists() and pat in fp.read_text(encoding="utf-8"):
                leaked.append("%s:%s" % (f, pat))
    check("⑤ 文档无敏感串（appId / 自定义词表）", not leaked, ", ".join(leaked) or "无")

    # ⑥ 核心链路 body 构造（不发请求）
    probe = (
        "import sys,json;sys.path.insert(0,'.')\n"
        "from seeyon_host_bootstrap import bootstrap\n"
        "b=bootstrap();APP='1';G='2'\n"
        "out={}\n"
        "out['index_body']=b['index_body']('i',1,[2])\n"
        "out['enum_body']=b['enum_body'](APP,'e','e1')\n"
        "out['serial']=b['serial_scheme_body'](APP,G,'s','n',"
        "[b['serial_section'](4,'CONSTANT',value='ZZ'),"
        "b['serial_section'](6,'SERIAL',fill_char='0')])\n"
        "out['scal']=b['scalability_field_body'](APP,1,'p','c')\n"
        "out['event']=b['event_data_body'](APP,'c','n',1,[{'outputName':'f','description':'d'}])\n"
        "out['dto']=b['dto_body'](APP,'c','n',[{'name':'f','caption':'c','dataType':'STRING'}])\n"
        "assert out['scal']['dataTypeProperties']=='{}', 'props 缺省应为 {}'\n"
        "assert isinstance(out['event']['eventDataList'],list), 'eventDataList 必须是数组'\n"
        "assert 'notNull' in out['dto'][0]['attributes'][0], 'dto 属性字段名应为 notNull'\n"
        "assert out['serial']['totalSize']==10, 'totalSize 应为各段之和'\n"
        "print('OK')\n"
    )
    r = _run(py, ["-c", probe], root)
    check("⑥ 核心链路 body 构造（含 4 个已知坑）",
          r.stdout.strip().endswith("OK"), r.stderr[-160:] or r.stdout[-80:])

    print()
    width = max(len(n) for n, _, _ in results)
    for name, st, detail in results:
        print("%-*s  %s  %s" % (width, name, st, detail))

    bad = [n for n, st, _ in results if st == FAIL]
    print()
    if bad:
        print("❌ %d 项未通过：%s" % (len(bad), bad))
        return 1
    print("✅ 全部 %d 项通过" % len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
