#!/usr/bin/env python3
"""installer/install.py — 把 Seeyon「角色 + 能力包」物化成各宿主可安装目录。

规格来源：installer/INSTALL-MANIFEST.md（§1 安装项 / §2 物化映射 / §3 H1 口径 / §4 校验项）。

设计边界
--------
- **纯 stdlib、离线、幂等**：不连网、不读凭据、不写凭据。
- **只在 `--target` 下写**：绝不在本仓内物化 `AGENTS.md` / `CLAUDE.md`
  （Hermes 写保护 fail-closed 清单 `{agents.md, claude.md, soul.md, .cursorrules}`，
  模板件因此只能叫 `.template.md`）。
- **不覆盖已存在的非本工具产物**：目标文件存在且首行不含本工具签名时，除非 `--force` 否则拒写。
- **`--dry-run` 是默认路径**：不加 `--write` 只打印计划，不改盘。

用法
----
    python installer/install.py --host all --target /tmp/seeyon-install --dry-run
    python installer/install.py --host hermes --target ~/seeyon-pkg --write
    python installer/install.py --host codex --target ../my-repo --write --force

产物（按宿主）
--------------
    hermes/       skills/seeyon-agent/SKILL.md      （frontmatter 原样）
                  mcp_servers.yaml                  （贴进 ~/.hermes/config.yaml 的 mcp_servers: 段）
    codex/        AGENTS.md                          （H1 按 §3 重写）
                  config.toml                        （[mcp_servers.seeyon]）
    claude-code/  CLAUDE.md                          （H1 按 §3 重写）
                  .mcp.json                          （{"mcpServers": {...}}）
    MANIFEST.json                                     （本次产物清单 + sha256，供校验/回滚）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

CANONICAL_VERSION = "5.3.517"
SCHEMA_ANCHOR = "seeyon-host-bootstrap.v1"
SIGNATURE = "generated-by: installer/install.py"

REPO_ROOT = Path(__file__).resolve().parents[1]

# 宿主 → 物化规则。`h1` 为 None 表示保留模板原 H1（Hermes 用 frontmatter，无需改写）。
HOSTS: dict[str, dict] = {
    "hermes": {
        "source": "adapters/hermes/Hermes-SKILL.md",
        # ★ 目录名必须等于 frontmatter 里的 `name`（seeyon-agent-hermes）。
        #   原来写 `skills/seeyon-agent/`，而仓库 `skills/seeyon-agent/` 是**另一个 skill**
        #   （v1 `seeyon-agent` 1.0.0，被 v2 的 `base:` 声明引用为只读基线）——
        #   装到宿主上会变成「目录叫 A、skill 叫 B」，和仓库现有 skill 撞名。
        "output": "skills/seeyon-agent-hermes/SKILL.md",
        "h1": None,
        "mcp_file": "mcp_servers.yaml",
        "mcp_format": "yaml",
    },
    "codex": {
        "source": "adapters/codex/AGENTS.template.md",
        "output": "AGENTS.md",
        "h1": "# AGENTS.md｜Seeyon Agent 宿主注册件（Canonical {v} · schema {s}）",
        "mcp_file": "config.toml",
        "mcp_format": "toml",
    },
    "claude-code": {
        "source": "adapters/claude-code/CLAUDE.template.md",
        "output": "CLAUDE.md",
        "h1": "# CLAUDE.md｜Seeyon Agent 宿主注册件（Canonical {v} · schema {s}）",
        "mcp_file": ".mcp.json",
        "mcp_format": "json",
    },
}

# 模板作者期的过程态标签，物化时必须消失（INSTALL-MANIFEST §3）。
PROCESS_TAGS = ("STAGED", "待放行", "待 main")

# 凭据面：安装件里一个都不许有（§4 第 5 项）。只匹配"看起来是值"的形态。
CRED_PATTERNS = (
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S{6,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\."),  # JWT
)

# MCP 片段只声明 server 名（`seeyon`），不列具体工具 —— 工具清单由
# `adapters/mcp/server.py` 的 `TOOL_KEYS` 决定（当前 54 个），
# 在这里硬编码一份必然过期（旧版曾写死 5 个 v1 时代的名字）。


# ------------------------------------------------------------------ 物化
def materialize(host: str, target: Path) -> list[dict]:
    """按宿主规则把模板写成安装件；返回写盘计划（未落盘）。"""
    spec = HOSTS[host]
    src = REPO_ROOT / spec["source"]
    if not src.is_file():
        raise SystemExit("源件不存在：%s" % src)

    text = src.read_text(encoding="utf-8")
    lines = text.split("\n")

    if spec["h1"] is not None:
        # 覆盖模板作者期 H1：跳过原 H1 行（可能带 STAGED 标签），插入安装态 H1。
        assert lines and lines[0].startswith("# "), "模板首行不是 H1：%s" % src
        new_h1 = spec["h1"].format(v=CANONICAL_VERSION, s=SCHEMA_ANCHOR)
        lines = [new_h1] + lines[1:]

    body = "\n".join(lines)
    # 过程态标签不许随安装件传播（§3）。
    leftover = [t for t in PROCESS_TAGS if t in body]
    if leftover:
        raise SystemExit(
            "物化后仍含过程态标签 %s —— 模板正文里有，需先清理模板：%s"
            % (leftover, spec["source"]))

    out_rel = spec["output"]
    # ★ Hermes 的 SKILL.md 必须以 `---` 开头（frontmatter 首行），
    #   在它前面插 HTML 注释会让宿主解析不出 name/description —— 实测踩到。
    #   签名改记进 MANIFEST.json，不进文件头。
    header = ""
    if host != "hermes":
        header = "<!-- %s | host=%s | canonical=%s | schema=%s -->\n" % (
            SIGNATURE, host, CANONICAL_VERSION, SCHEMA_ANCHOR)
    return [{
        "host": host,
        "path": out_rel,
        "content": header + body,
        "kind": "instruction",
    }]


def mcp_config(host: str, seeyon_root: str | None = None,
               portable: bool = False) -> dict:
    """生成宿主侧 MCP 注册片段（传输层 = adapters/mcp/server.py，stdio）。

    `seeyon_root` 给出时填真实路径（开箱可用）；`portable=True` 时改用
    `<SEEYON_AGENT_ROOT>` 占位符（跨机器分发，安装时再替换）。
    """
    python = sys.executable.replace("\\", "/")
    if portable or not seeyon_root:
        server = "<SEEYON_AGENT_ROOT>/adapters/mcp/server.py"
    else:
        server = seeyon_root.rstrip("/\\").replace("\\", "/") + "/adapters/mcp/server.py"
    spec = HOSTS[host]

    if spec["mcp_format"] == "yaml":
        # 贴进 ~/.hermes/config.yaml 顶层 mcp_servers: 段（本机实测格式，L714/L776）。
        content = (
            "# 贴进 ~/.hermes/config.yaml 的顶层 mcp_servers: 段\n"
            "  seeyon:\n"
            "    command: %s\n"
            "    args:\n"
            "      - %s\n"
            "    timeout: 180\n" % (python, server))
    elif spec["mcp_format"] == "toml":
        # Codex CLI：~/.codex/config.toml 的 [mcp_servers.<name>]。
        content = (
            "[mcp_servers.seeyon]\n"
            'command = "%s"\n'
            'args = ["%s"]\n' % (python, server))
    else:
        # Claude Code：项目根 .mcp.json。
        content = json.dumps(
            {"mcpServers": {"seeyon": {"command": python, "args": [server]}}},
            indent=2, ensure_ascii=False) + "\n"

    return {
        "host": host,
        "path": spec["mcp_file"],
        "content": content,
        "kind": "mcp-config",
    }


# ------------------------------------------------------------------ 校验
def verify(plan: list[dict]) -> list[str]:
    """§4 五项校验。返回问题列表，空 = 通过。"""
    problems = []
    by_host: dict[str, list[dict]] = {}
    for item in plan:
        by_host.setdefault(item["host"], []).append(item)

    for host, items in by_host.items():
        names = {i["path"] for i in items}

        # 1. 规范名指令件落地
        want = HOSTS[host]["output"]
        if want not in names:
            problems.append("%s: 缺规范名指令件 %s" % (host, want))

        # 2. 无 .template 残留
        for n in names:
            if ".template." in n:
                problems.append("%s: 产物里出现模板名 %s（模板不随安装落地）" % (host, n))

        for item in items:
            body = item["content"]

            # 3. H1 口径（仅指令件；MCP 配置无 H1）
            if item["kind"] == "instruction":
                first = body.split("\n")[1] if body.startswith("<!--") else body.split("\n")[0]
                if host != "hermes":
                    if CANONICAL_VERSION not in first or SCHEMA_ANCHOR not in first:
                        problems.append(
                            "%s: H1 缺版本锚/schema 锚 → %r" % (host, first[:80]))
                for tag in PROCESS_TAGS:
                    if tag in body:
                        problems.append("%s: %s 含过程态标签 %r" % (host, item["path"], tag))

            # 4. 凭据 0 入件
            for pat in CRED_PATTERNS:
                m = pat.search(body)
                if m:
                    problems.append(
                        "%s: %s 疑似含凭据值 → %r" % (host, item["path"], m.group(0)[:40]))

            # 5. MCP 片段必须声明全部 5 个工具可发现
            if item["kind"] == "mcp-config":
                if "seeyon" not in body:
                    problems.append("%s: MCP 片段里没有 server 名 seeyon" % host)

    # 跨宿主：三份 MCP 片段必须指向同一个传输层
    servers = {i["content"] for i in plan if i["kind"] == "mcp-config"}
    if len(servers) > 1:
        paths = {re.search(r"<SEEYON_AGENT_ROOT>[^\"'\s]*", s).group(0)
                 for s in servers if re.search(r"<SEEYON_AGENT_ROOT>[^\"'\s]*", s)}
        if len(paths) > 1:
            problems.append("三份 MCP 片段指向不同传输层：%s" % paths)

    return problems


# ------------------------------------------------------------------ 写盘
def write_plan(plan: list[dict], target: Path, force: bool) -> list[str]:
    written = []
    for item in plan:
        dst = target / item["host"] / item["path"]
        payload = item["content"].encode("utf-8")
        if dst.exists():
            # 幂等：内容逐字节一致就直接跳过（MCP 配置是 JSON/TOML，加不了签名注释）
            if dst.read_bytes() == payload:
                continue
            if not force:
                head = dst.read_text(encoding="utf-8", errors="replace")[:300]
                # Hermes 的 SKILL.md 不能带 HTML 注释签名（frontmatter 必须首行），
                # 用它 frontmatter 里的 name 认身份。
                owned = SIGNATURE in head or "seeyon-agent-hermes" in head
                if not owned:
                    raise SystemExit(
                        "拒绝覆盖非本工具产物：%s（加 --force 强制）" % dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(item["content"], encoding="utf-8", newline="")
        written.append(str(dst.relative_to(target)))
    return written


def build_manifest(plan: list[dict], target: Path) -> dict:
    files = []
    for item in plan:
        dst = target / item["host"] / item["path"]
        data = dst.read_bytes()
        files.append({
            "host": item["host"],
            "path": str(dst.relative_to(target)).replace("\\", "/"),
            "kind": item["kind"],
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    return {
        "canonical_version": CANONICAL_VERSION,
        "schema": SCHEMA_ANCHOR,
        "generator": SIGNATURE,
        "files": sorted(files, key=lambda f: f["path"]),
    }


# ------------------------------------------------------------------ main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="install.py",
        description="把 Seeyon 角色+能力包物化成各宿主可安装目录（离线、幂等）")
    ap.add_argument("--host", required=True,
                    choices=sorted(HOSTS) + ["all"], help="目标宿主")
    ap.add_argument("--target", required=True, type=Path,
                    help="输出根目录（必须在本仓之外）")
    ap.add_argument("--write", action="store_true", help="真正落盘（默认 dry-run）")
    ap.add_argument("--dry-run", action="store_true",
                    help="显式 dry-run（与默认行为相同，供脚本显式声明）")
    ap.add_argument("--force", action="store_true", help="允许覆盖非本工具产物")
    ap.add_argument("--seeyon-root", default=None,
                    help="Seeyon Agent 仓库根（写进 MCP 片段；默认用本脚本所在仓）")
    ap.add_argument("--portable", action="store_true",
                    help="MCP 片段用 <SEEYON_AGENT_ROOT> 占位符，不写本机绝对路径")
    args = ap.parse_args(argv)

    if args.write and args.dry_run:
        ap.error("--write 与 --dry-run 互斥")

    target = args.target.resolve()
    if target == REPO_ROOT or REPO_ROOT in target.parents:
        raise SystemExit(
            "拒绝在仓库内物化（会撞 AGENTS.md/CLAUDE.md 写保护）：%s" % target)

    hosts = sorted(HOSTS) if args.host == "all" else [args.host]

    plan: list[dict] = []
    for host in hosts:
        plan.extend(materialize(host, target))
        root = args.seeyon_root or str(REPO_ROOT)
        plan.append(mcp_config(host, root, args.portable))

    problems = verify(plan)
    if problems:
        print("校验未通过：", file=sys.stderr)
        for p in problems:
            print("  - %s" % p, file=sys.stderr)
        return 1

    print("计划（%d 个文件，%s）：" % (len(plan), "写盘" if args.write else "dry-run"))
    for item in plan:
        print("  [%s] %s/%s  %d B" % (
            item["kind"], item["host"], item["path"], len(item["content"].encode())))

    if not args.write:
        print("\n未落盘。加 --write 执行。")
        return 0

    written = write_plan(plan, target, args.force)
    manifest = build_manifest(plan, target)
    mf = target / "MANIFEST.json"
    mf.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                  encoding="utf-8", newline="")
    print("\n已写入 %d 个文件 → %s" % (len(written), target))
    print("清单：%s（%d 项）" % (mf, len(manifest["files"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
