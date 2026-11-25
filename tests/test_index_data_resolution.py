"""签名库/表面索引的定位与发行回归。

背景（0.2.7 的线上故障）：
`xiaozhua_platform_class_search` / `platform_class_methods` 在装机环境里报
「signatures.txt.gz 不存在（缺件，索引不可用）」。

根因：签名库躺在 `docs/audit/` 下，而 `docs/` 是工作区，安装时被
`installer/selfupdate.py::IGNORE_DIRS` 整个排除 —— 装机树里根本没有这个文件，
代码却只认那一个路径。

约定（本测试钉住）：
1. 索引数据放在 `fixtures/reference/`（发行树，安装时会被复制）；
2. 解析顺序由 `core.index_data.resolve()` 统一，兼容工作区旧路径；
3. 缺件时的报错必须给出可执行的自修路径，而不是一句「缺件」。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.index_data import candidates, missing_message, resolve  # noqa: E402

SIG = "signatures.txt.gz"


def test_signature_index_is_shipped_with_product():
    """签名库必须在 fixtures/reference/（发行位置），不能只躺在 docs/。"""
    shipped = ROOT / "fixtures" / "reference" / SIG
    assert shipped.is_file(), f"发行位置缺签名库：{shipped}"
    assert shipped.stat().st_size > 1_000_000, "签名库体积异常（应是 MB 级）"

    tracked = subprocess.run(
        ["git", "ls-files", "fixtures/reference"], cwd=str(ROOT),
        capture_output=True, text=True, timeout=60,
    ).stdout
    assert f"fixtures/reference/{SIG}" in tracked, "签名库没进 git —— 装机时拿不到"


def test_resolve_prefers_shipped_location():
    got = resolve(SIG)
    assert got is not None
    assert got.parent.name == "reference", f"应命中发行位置，实际 {got}"


def test_resolve_returns_none_for_missing():
    assert resolve("nope-not-exist.txt.gz") is None


def test_missing_message_is_actionable():
    msg = missing_message(SIG)
    assert "缺件" in msg
    for hint in ("xiaozhua update", "XIAOZHUA_INDEX_DIR", "~/.xiaozhua/data"):
        assert hint in msg, f"缺件提示缺少自修路径：{hint}"
    # 必须列出自试过的路径，否则用户没法判断是路径算错还是真没装
    assert any(str(p) in msg for p in candidates(SIG))


def test_install_keeps_fixtures_but_drops_docs():
    """安装排除列表：docs 是工作区（要排除），fixtures 是发行数据（必须保留）。"""
    src = (ROOT / "installer" / "selfupdate.py").read_text(encoding="utf-8")
    assert '"docs"' in src or "'docs'" in src, "IGORE_DIRS 里应仍有 docs"
    assert '"fixtures"' not in src and "'fixtures'" not in src, (
        "fixtures/ 被排除的话，装机树就没有签名库与表面索引了"
    )


def test_tools_do_not_hardcode_docs_path():
    """两个工具都不能再直接拼 docs/audit 路径（那正是故障来源）。"""
    for rel in (
        "components/construction/platform_class_index.py",
        "components/construction/business_action_index.py",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert 'docs" / "audit"' not in text, f"{rel} 又写死了 docs/audit 路径"
        assert "resolve(" in text, f"{rel} 未经 core.index_data.resolve 解析"


@pytest.mark.parametrize("term,bucket", [("Utils", "util"), ("AppService", "appservice")])
def test_platform_class_search_works_offline(term: str, bucket: str):
    """索引真实可用：能搜到类，且带上方法数（不是空壳）。"""
    from components.construction import platform_class_index as idx

    res = idx.search(term=term, bucket=bucket)
    assert res.get("total", 0) > 0, f"{term} 无结果"
    assert res["hits"], "结果为空"
    assert res["level"] == "VERIFIED_STATIC_BYTECODE", "证据等级应标明是字节码级"


def test_platform_class_methods_works_offline():
    from components.construction import platform_class_index as idx

    first = idx.search(term="JsonUtils", bucket="util")
    assert first.get("hits"), "先要能搜到类"
    cls = first["hits"][0]["name"]
    got = idx.methods_of(cls)
    assert got.get("total", 0) > 0, f"{cls} 方法为空"
    names = [m["name"] for m in got["methods"]]
    for expected in ("toJson", "fromJson"):
        assert expected in names, f"{cls} 缺 {expected}"

# ── 覆盖度：签名库是全量 21389 类，不能只索引 util/AppService/SPI（2669）──

def test_index_covers_all_classes_not_just_curated_buckets():
    from components.construction import platform_class_index as idx

    s = idx.stats()
    assert s["classes"] >= 21_000, f"只索引了 {s['classes']} 类 —— 全量应是 21389"
    assert s["methods"] >= 220_000, f"方法数 {s['methods']} 不足（应 224320）"
    other = s["byBucket"].get("other", 0)
    assert other >= 18_000, f"非常用桶类 {other} 个未入索引"


def test_udc_dto_and_enum_are_searchable():
    """UDC 的 DTO/枚举以前全查不到（bucket 过滤），这是实际踩到的坑。"""
    from components.construction import platform_class_index as idx

    r = idx.search(term="UdcPageInfoSearchDto", limit=3)
    assert r["total"] >= 1, "udc DTO 查不到"
    assert r["hits"][0]["name"] == "com.seeyon.udc.common.dto.UdcPageInfoSearchDto"

    e = idx.search(term="PageUrlTypeEnum", limit=3)
    assert e["total"] >= 1, "udc 枚举查不到"

    m = idx.methods_of("com.seeyon.udc.common.dto.UdcPageInfoSearchDto")
    assert m["total"] > 0, "DTO 方法列为空"


def test_two_signature_copies_do_not_drift():
    """docs/ 与 fixtures/ 各有一份时，必须字节一致（否则线上/工作区结论会不同）。"""
    import hashlib

    a = ROOT / "docs" / "audit" / SIG
    b = ROOT / "fixtures" / "reference" / SIG
    if not a.exists():
        pytest.skip("工作区没有 docs 副本")
    assert hashlib.sha256(a.read_bytes()).hexdigest() == hashlib.sha256(b.read_bytes()).hexdigest(), (
        "两份签名库不一致：改了 javap 快照后忘了同步另一份"
    )
