"""发行卫生：仓库里（git 跟踪的文件）不许出现客户/本机环境标识。

背景：这个仓库是「装到别人机器上的工具」，不是我们的工作区。
`git clone` 下来的人只该看到机制与占位符，`config/environments.local.yaml`
（真实主机/命名空间/appId/租户/桶名/凭据路径）留在本机、不进 git。

这里用黑名单扫发行面。发现命中时，正确做法不是加白名单，而是：
把值搬进 `config/environments.local.yaml` / `~/.xiaozhua/logs.yaml`，代码只留引用键。
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# 发行面（会被 clone / pip install / 打包进安装件的路径前缀）
# 装进包/被 import 的部分（严格零容忍）。core/facts 是知识库、不随安装件执行，
# 它的问题单列在 test_facts_evidence_hits_do_not_grow（只准减不准增）。
SHIPPED_PREFIXES = (
    "adapters/", "components/", "core/config_env.py", "config/", "installer/",
    "providers/",
    "README.md", "INSTALL.md", "CHANGELOG.md", "pyproject.toml", "VERSION",
)

# 硬标识：真实域名 / 真 appId / 凭据 / 本机目录 / kubeconfig 名。
# （`lowcode-test2.example.com` 这类占位主机不算——它带 .example.com，谁都能用。）
DENY = (
    "changhongit",
    "6419954374508955097",
    "8704025620829192834",
    "configtest2",
    "configuat",
    "多agent协助",
    "trVLY2sJKQPf",
)

# 历史遗留：功能数据里以真 appId 为键（连接器默认值/约束模块），删了会改行为。
# 不静默放过——每一条都登记在 docs/audit/customer-data-inventory.md，等迁移成
# config/ 引用键。新增文件不许再进这个集合。
LEGACY = {
    "components/udc/event_listener_constraints.py",
    "components/udc/attribute_expression_constraints.py",
    "components/udc/menu_constraints.py",
    "components/udc/microflow/gates.py",
    "core/facts/batch-modules-20260925.md",
    # 这份就是盘点表本身（登记了哪些标识、在哪个文件），内容必须能写出来
    "docs/audit/customer-data-inventory.md",
}


def _tracked_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=str(ROOT), capture_output=True, text=True, timeout=60
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"git 不可用：{exc}")
    if out.returncode != 0:
        pytest.skip("不是 git 工作树，跳过发行卫生检查")
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def test_no_customer_or_local_identifiers_in_shipped_files():
    hits: list[str] = []
    for rel in _tracked_files():
        rel = rel.replace("\\", "/")
        if not rel.startswith(SHIPPED_PREFIXES) or rel in LEGACY:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in DENY:
            if token in text:
                for no, line in enumerate(text.splitlines(), 1):
                    if token in line:
                        hits.append(f"{rel}:{no}: {token} -> {line.strip()[:90]}")
    assert not hits, "发行面出现客户/本机标识（搬到 local 覆盖层，别写进仓库）：\n" + "\n".join(hits[:40])


def test_local_overlay_is_not_tracked():
    """本机覆盖层必须不在 git 里；否则下一次 commit 又把环境带出去了。"""
    tracked = set(_tracked_files())
    for forbidden in ("config/environments.local.yaml", "config/logs.yaml", "config/udc-semantics-evidence.local.json"):
        assert forbidden not in tracked, f"{forbidden} 被跟踪了（应 gitignore）"


def test_config_dir_has_only_examples_and_skeletons():
    """config/ 里允许出现的是骨架与 .example；出现真实凭据文件就是事故。"""
    bad = [
        rel for rel in _tracked_files()
        if rel.startswith("config/") and (
            "credential" in rel.lower() and "example" not in rel.lower()
            or rel.lower().endswith((".pem", ".key", ".pfx"))
        )
    ]
    assert not bad, f"config/ 里混进了凭据类文件：{bad}"

# 知识库里已知的 LIVE 证据标识数（core/facts/**）。只准往下减，不准增。
BASELINE_FACTS_HITS = 216  # 2026-11-24 实测；只准减


def _facts_hits() -> list[str]:
    hits = []
    for rel in _tracked_files():
        rel = rel.replace("\\", "/")
        if not rel.startswith(("core/facts/", "definitions/", "scripts/", "docs/")) or rel in LEGACY:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in DENY:
            if token in text:
                hits.append(rel)
                break
    return hits


def test_facts_evidence_hits_do_not_grow():
    hits = _facts_hits()
    assert len(hits) <= BASELINE_FACTS_HITS, (
        f"core/facts 里的环境标识从 {BASELINE_FACTS_HITS} 涨到 {len(hits)} 份；"
        "新增证据请放仓外 customer-evidence，别把 LIVE 环境细节写进事实库。新命中："
        + ", ".join(sorted(hits)[:10]))
