"""Shared pytest fixtures for the seeyon-agent test suite.

客户场景证据（golden 样本等）已于 2026-10-09 迁出仓库
（见 config/environments.yaml customer_evidence_root）。
依赖它的测试通过环境变量拿到仓库外证据根；根不存在时相关测试自动 skip，
保证「仓库干净」与「测试可跑」两个目标互不牺牲。
"""

import os
from pathlib import Path

_CUSTOMER_EVIDENCE_ROOT = Path(r"<EVIDENCE_ROOT>/seeyon-customer-evidence")

import pytest


def _customer_evidence_available() -> bool:
    return (_CUSTOMER_EVIDENCE_ROOT / "fixtures-golden").is_dir()


# 客户 golden 样本证据根（仅测试进程内生效，不写入任何仓库文件）
os.environ.setdefault("SEEYON_CUSTOMER_EVIDENCE_ROOT", str(_CUSTOMER_EVIDENCE_ROOT))

requires_customer_evidence = pytest.mark.skipif(
    not _customer_evidence_available(),
    reason="customer evidence root not present (migrated out of repo 2026-10-09)",
)

# 脚本式自检文件：模块级顺序执行并以 sys.exit 结束，被 pytest 收集会
# 触发 INTERNALERROR(SystemExit) 打崩整场收集（实测 2026-10-30：2158 → 0）。
# 它们不是 pytest 用例，仍可直接 `python tests/xxx.py` 运行。
collect_ignore_glob = [
    "test_composer.py",
    "test_template_residue.py",
    "test_construction_skeleton.py",
    "test_live_readonly_offline.py",
]
