"""P6 临时件的登记状态必须与上级索引一致（不许一个说"待裁决"、一个说"已裁决"）。

背景：P6 要求「明确临时件，先登记再处理」。2026-11-07 的整理过程中，`docs/audit/README.md` §六
逐条给出了裁决（保留原地 / 不得移动 / 理由 / 谁在读），但 `recovery-checkpoint.md` 与
`next-direction-input.md` 自己的文件头**还写着「已登记待裁决」** ——
同一件事在同一仓库里有两个状态。后到的人按文件头读，就会以为这两份还能搬。

本测试守四件事：
1. 四份 P6 件都还在盘（裁决是"保留原地"）
2. 文件头状态必须是「已裁决」而非「待裁决」
3. 「被代码读取」的声明必须与代码实况一致（不是抄的旧话）
4. `plans/hermes/plans/` 双层嵌套的保留理由仍在 `docs/plans/README.md` 里
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs" / "audit"
IDX = AUDIT / "README.md"

P6_FILES = [
    AUDIT / "next-direction-input.md",
    AUDIT / "recovery-checkpoint.md",
    AUDIT / "udc-semantics" / "COMPLETION-METHOD-PROMPT.md",
    AUDIT / "udc-semantics" / "UNDERSTANDING-CHECKPOINT.md",
]


def test_all_p6_files_still_present():
    missing = [str(p.relative_to(ROOT)) for p in P6_FILES if not p.is_file()]
    assert not missing, "P6 裁决是「保留原地」，但这些不见了：%s" % missing


def test_headers_say_decided_not_pending():
    """文件头必须写「已裁决」，不许留「待裁决」。"""
    bad = []
    for p in P6_FILES:
        head = p.read_text(encoding="utf-8", errors="replace")[:900]
        if "待裁决" in head:
            bad.append("%s 头部仍写「待裁决」" % p.relative_to(ROOT))
        if "P6 裁决" not in head and "P6" not in head:
            bad.append("%s 头部没有 P6 裁决标记" % p.relative_to(ROOT))
    assert not bad, "P6 件头部状态与上级索引不一致：\n  " + "\n  ".join(bad)


def test_upper_index_registers_all_four():
    text = IDX.read_text(encoding="utf-8", errors="replace")
    missing = [p.name for p in P6_FILES if p.name not in text]
    assert not missing, "docs/audit/README.md 没登记这些 P6 件：%s" % missing
    assert "六、流水与检查点" in text, "docs/audit/README.md 缺 §六（P6 登记表）"


def test_code_read_claims_match_reality():
    """「仍被程序读取」不是抄来的旧话，必须与代码实况对得上。"""
    # ① recovery-checkpoint 在 fixture manifest 的 source_documents 里
    mf = ROOT / "tests" / "fixtures" / "udc-audit" / "manifest.json"
    assert mf.is_file(), "fixture manifest 不见了"
    src = json.loads(mf.read_text(encoding="utf-8")).get("source_documents", [])
    assert any("recovery-checkpoint.md" in s for s in src), (
        "manifest.source_documents 里没有 recovery-checkpoint.md —— 文件头的"
        "「仍被程序读取」已过期，应改为「已不被读取」并重走 P6 裁决")
    assert any("next-direction-input.md" in s for s in src), (
        "manifest.source_documents 里没有 next-direction-input.md")

    # ② audit_summary.py 的 REPORTS["next_direction"] 指向它
    a = (ROOT / "components" / "audit_summary.py").read_text(encoding="utf-8", errors="replace")
    assert re.search(r'"next_direction"\s*:\s*"next-direction-input\.md"', a), (
        "components/audit_summary.py 的 REPORTS[\"next_direction\"] 不再指向 "
        "next-direction-input.md —— 文件头的「仍被程序读取」已过期")

    # ③ 两份文件头都必须写明谁在读
    for p in (AUDIT / "recovery-checkpoint.md", AUDIT / "next-direction-input.md"):
        head = p.read_text(encoding="utf-8", errors="replace")[:900]
        assert "被程序读取" in head, "%s 头部没写「仍被程序读取」" % p.name


def test_hermes_nested_plans_reason_recorded():
    """plans/hermes/plans/ 双层嵌套：保留原位的理由必须还在。"""
    p = ROOT / "docs" / "plans" / "README.md"
    text = p.read_text(encoding="utf-8", errors="replace")
    assert "hermes/plans/" in text, "docs/plans/README.md 没登记 hermes/plans/ 双层嵌套"
    assert "双层嵌套" in text, "没写明这是双层嵌套（Hermes 侧 plan 目录被整目录拷入）"
    assert "未被任何代码读取" in text or "未被代码读取" in text, (
        "没记「未被任何代码读取」这条核对结论")
    nested = ROOT / "docs" / "plans" / "hermes" / "plans"
    assert nested.is_dir(), "docs/plans/hermes/plans/ 不见了（裁决是保留原位）"
