# -*- coding: utf-8 -*-
"""构建可分发的干净仓库。

为什么不直接 push 主仓库：
  .git 有 522MB，历史里有 176MB 浏览器缓存和 163MB Chrome 组件包，
  且 scratch/ 含 test2 真实 appId 与域名。推到任何远端都是永久泄露。

清理策略（按用户口径：只推"别人能用来调平台"的东西）：
  1. 不进包：scratch/ _attic_pending/ build/ dist/ .venv/
  2. 不进包：docs/audit/artifacts（380MB 反编译）、docs/audit/evidence（客户抓包）
  3. 不进包：core/facts/**/evidence（页面抓包、内网 IP、客户域名）
  4. 不进包：tools/core/feishu（抓飞书 bug 表的一次性脚本，硬编码真实 TOKEN）
  5. 不进包：skills/06-delivery/<客户>-pmp（客户具体项目 a↔b 代码迁移）
  6. 技能归位：根目录 7 个 skill 移到对应分类目录
  7. 文本脱敏：域名 / appId / 内网 IP / 本机盘符路径 → 占位符

用法：
    python tools/core/delivery/build_public_repo.py --src <主仓库> --dst <干净仓库>
    python tools/core/delivery/build_public_repo.py --src . --dst ../xiaozhua-agent-public --check
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------- 排除规则

SKIP_TOP = {
    ".git", ".venv", "scratch", "_attic_pending", "build", "dist",
    "__pycache__", ".pytest_cache",
    "artifact-inventory.manifest.json", "http.json", "integration.json",
    "runtime.json", ".gitignore-public", "xiaozhua_agent.egg-info",
}

# 相对路径前缀（用 / 分隔），命中即整棵子树跳过
SKIP_PREFIX = (
    "docs/audit/artifacts",
    "docs/audit/evidence",
    "tools/core/feishu",
    "skills/06-delivery/" + "changhong" + "-pmp",
    # 抓飞书用的 CDP 脚本，硬编码真实 TOKEN（与 tools/core/feishu 同类）
    "tools/core/platform/cdp_feishu_fetch.py",
    # 客户页面导航抓包，含真实操作人姓名 42 处
    "docs/audit/column-discovery/raw-nav-capture-20261017.json",
)

# 目录名黑名单：出现在任何层级都跳过（客户抓包证据）
SKIP_DIRNAMES = {"evidence"}  # core/facts/**/evidence 等

# 单个文件超这个大小就不进仓库（防止再混进大 JSON）
MAX_FILE_MB = 2.0

# ---------------------------------------------------------------- 技能归位

SKILL_MOVES = {
    "sdd-protocol": "05-agent",
    "xiaozhua-agent": "05-agent",
    "xiaozhua-udc-application-app-inner": "02-udc",
    "xiaozhua-udc-microflow-node": "02-udc",
    "xiaozhua-udc-module-landing": "02-udc",
    "xiaozhua-udc-setting": "02-udc",
    "udc-trace-to-api": "02-udc",
}

# ---------------------------------------------------------------- 脱敏规则

# 顺序有讲究：先替换长串（域名），再处理 IP / 路径
SCRUBS: list[tuple[re.Pattern, str]] = [
    # 客户自定义 SPI 插件 jar 包名（名字里就带客户与测试环境）
    (re.compile(r"cip-spi-user-sso-[\w-]*" + "changhong" + r"[\w-]*", re.I), "cip-spi-user-sso-sample"),
    (re.compile(r"udc-plugin-[\w-]*" + "changhong" + r"[\w-]*", re.I), "udc-plugin-sample"),
    (re.compile(r"lowcode-test2\.\.\.", re.I), "lowcode-test2.example.com"),
    (re.compile(r"lowcode-test2\.[\w.-]*" + "changhong" + r"it\.com", re.I), "lowcode-test2.example.com"),
    (re.compile(r"[\w.-]*" + "changhong" + r"it\.com", re.I), "lowcode-test2.example.com"),
    (re.compile(r"\b163126498398523384\b"), "app9000000000000000001"),
    (re.compile(r"\b7988886308612688555\b"), "appGuid0000000000000001"),
    (re.compile(r"\b117498226330127667\b"), "app9000000000000000001"),
    # 内网 IP（172.16-31 / 192.168 / 10.x）
    (re.compile(r"\b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b"), "10.0.0.1"),
    (re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"), "10.0.0.1"),
    (re.compile(r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "10.0.0.1"),
    # 客户组织名（中文）：只替换成中性词，不动结构
    (re.compile("长虹" + "佳华|" + "长虹"), "客户组织"),
    # 已排除的 skill 名不应在 related_skills 里出现
    (re.compile(r",\s*" + "changhong" + r"-pmp"), ""),
    (re.compile(r"" + "changhong" + r"-pmp,\s*"), ""),
    # Nacos 命名空间名里的客户标识（xiaozhua-<客户>、<客户>-test2 形态）
    (re.compile(r"xiaozhua-[a-z0-9-]*" + "changhong" + r"[a-z0-9-]*", re.I), "xiaozhua-test2"),
    (re.compile(r"[a-z0-9-]*" + "changhong" + r"[a-z0-9-]*-test2", re.I), "xiaozhua-test2"),
    (re.compile(r"[a-z0-9-]*" + "changhong" + r"[a-z0-9-]*", re.I), "sample"),
    # 本机绝对路径
    (re.compile(r"[A-Za-z]:[\\/]work[\\/]chit[\\/]xiaozhua-agent"), "<XIAOZHUA_AGENT_ROOT>"),
    (re.compile(r"[A-Za-z]:[\\/]work[\\/]" + "changhong"), "<PROJECT_ROOT>"),
    (re.compile(r"[A-Za-z]:[\\/]work[\\/]chit"), "<EVIDENCE_ROOT>"),
    (re.compile(r"[A-Za-z]:[\\/]repo[\\/]CHIT"), "<MAVEN_REPO>"),
    (re.compile(r"[A-Za-z]:[\\/]software[\\/]hermes"), "<HERMES_HOME>"),
    (re.compile(r"[A-Za-z]:[\\/]software[\\/]多agent协助"), "<COLLAB_ROOT>"),
    (re.compile(r"[A-Za-z]:[\\/]software"), "<LOCAL_ROOT>"),
    # 其他盘符（E:/work、C:/Users 等）
    (re.compile(r"[A-Za-z]:[\\/]Users[\\/][^\s\"'<>|]{2,60}"), "<USER_HOME>/..."),
    # 兜底：剩余盘符路径（必须放最后）。负向断言排除 `http://`、`https://`、`ftp://`
    # 这类协议前缀 —— 否则 `http://127.0.0.1:9333` 会被当成盘符 `p:` 吃掉，
    # 把代码里的 URL 全毁掉（这一版曾经真的毁了 44 行）。
    (re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]+[A-Za-z0-9_.$\u4e00-\u9fff-]+[\\/][^\s\"'<>|]*"),
     "<PATH>"),
]

TEXT_EXT = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".toml", ".cfg",
            ".ini", ".sh", ".bat", ".ps1", ".csv", ".java", ".xml",
            ".javap", ".log", ".conf", ".properties"}

# 这些文件不做脱敏（会破坏功能，例如测试自己的正则）
SCRUB_EXEMPT = {
    # 脱敏工具自身：规则里必然写客户串
    "tools/core/delivery/build_public_repo.py",
    "tools/core/delivery/accept_package.py",
    "tools/core/audit/plan_deident.py",
    "tools/core/_meta/build_facts_skill.py",
    # 守卫测试：用拼接方式写客户串检测泄露，属正当用途
    "tests/test_deidentification.py",
    "tests/udc/test_extension_usage_assets.py",
    "tests/udc/test_application_app_inner_asset_layout.py",
    "tests/udc/test_fact_discoverability.py",
    "tests/udc/test_setting_operation_matrix.py",
    "tests/udc/test_spi_facts_layout.py",
}


def _skip_path(rel: str) -> tuple[bool, str]:
    """rel 用 / 分隔。返回 (是否跳过, 原因)。"""
    if rel.split("/")[0] in SKIP_TOP:
        return True, "顶层排除"
    for p in SKIP_PREFIX:
        if rel == p or rel.startswith(p + "/"):
            return True, "规则排除: " + p
    parts = rel.split("/")
    for d in parts[:-1]:
        if d in SKIP_DIRNAMES:
            return True, "证据目录: " + d
    return False, ""


def build(src: Path, dst: Path, check_only: bool = False) -> dict:
    stats = {"copied": 0, "moved": 0, "scrubbed_files": 0,
             "scrubbed_hits": 0, "skipped_big": [], "bytes": 0}

    if dst.exists():
        if check_only:
            print("目标已存在，--check 模式不重建：%s" % dst)
        else:
            shutil.rmtree(dst)
    if not dst.exists():
        dst.mkdir(parents=True)

    for f in src.rglob("*"):
        if not f.is_file():
            continue
        rel = str(f.relative_to(src)).replace("\\", "/")
        skip, _why = _skip_path(rel)
        if skip:
            continue
        if f.stat().st_size > MAX_FILE_MB * 1024 * 1024:
            stats["skipped_big"].append((rel, f.stat().st_size / 1024 / 1024))
            continue

        out_rel = rel
        # 技能归位
        parts = rel.split("/")
        if parts[0] == "skills" and len(parts) > 1 and parts[1] in SKILL_MOVES:
            out_rel = "/".join(["skills", SKILL_MOVES[parts[1]]] + parts[1:])
            stats["moved"] += 1

        tgt = dst / out_rel
        tgt.parent.mkdir(parents=True, exist_ok=True)

        if f.suffix.lower() in TEXT_EXT and rel not in SCRUB_EXEMPT:
            try:
                text = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    text = f.read_text(encoding="gbk")
                except (UnicodeDecodeError, OSError):
                    shutil.copy2(f, tgt)
                    stats["copied"] += 1
                    stats["bytes"] += tgt.stat().st_size
                    continue
            except OSError:
                shutil.copy2(f, tgt)
                stats["copied"] += 1
                stats["bytes"] += tgt.stat().st_size
                continue
            hits = 0
            for rx, repl in SCRUBS:
                text, n = rx.subn(repl, text)
                hits += n
            if hits:
                stats["scrubbed_files"] += 1
                stats["scrubbed_hits"] += hits
            tgt.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(f, tgt)
        stats["copied"] += 1
        stats["bytes"] += tgt.stat().st_size

    # 严格的 .gitignore
    (dst / ".gitignore").write_text(
        "# 一次性调试脚本\n/scratch/\n/_attic_pending/\n/build/\n/dist/\n"
        "# 证据快照（反编译产物 / 客户抓包）\n/docs/audit/artifacts/\n"
        "/docs/audit/evidence/\n"
        "# 本地环境\n/.venv/\n__pycache__/\n*.py[cod]\n.pytest_cache/\n*.egg-info/\n"
        "# 凭据（绝不入库）\n*credential*.json\n*cookies*.json\n*.token\n.env\n",
        encoding="utf-8")
    return stats


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="构建可分发的干净仓库")
    ap.add_argument("--src", type=Path, default=Path("."))
    ap.add_argument("--dst", type=Path, required=True)
    ap.add_argument("--check", action="store_true", help="只报告不重建")
    args = ap.parse_args(argv)

    src = args.src.resolve()
    dst = args.dst.resolve()
    st = build(src, dst, args.check)

    print("复制 %d 个文件，%.1f MB" % (st["copied"], st["bytes"] / 1024 / 1024))
    print("技能归位 %d 个文件" % st["moved"])
    print("脱敏 %d 个文件，共 %d 处" % (st["scrubbed_files"], st["scrubbed_hits"]))
    if st["skipped_big"]:
        print("跳过超大文件 %d 个：" % len(st["skipped_big"]))
        for r, s in sorted(st["skipped_big"], key=lambda x: -x[1])[:10]:
            print("   %6.2f MB  %s" % (s, r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
