"""三段式提示词（拆解 → 确认 → 组装）回归测试。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.construction.business_plan import confirm_plan  # noqa: E402
from components.construction.host_llm_prompt import (  # noqa: E402
    render_assemble, render_clarify,
)

PLAN = {"elements": [
    {"key": "poSync", "capability": "每天同步合同PO关系", "purpose": "SYNC",
     "inputShape": "PAGE_CONDITION", "outputShape": "STATUS_ONLY",
     "persistTo": "采购合同PO关系", "persistMode": "UPSERT",
     "persistKey": ["contractNo"], "trigger": "SCHEDULE",
     "scheduleCron": "0 0 1 * * ?", "timeRange": "LAST_7_DAYS",
     "gap": ["NO_HTTP_NODE"]},
]}


def test_clarify_prompt_has_no_node_vocabulary():
    """第一段只做业务拆解，不能出现节点组装指令。"""
    system, user = render_clarify("把合同数据同步进来，每天跑一次")
    assert "IntentDraft" not in system, "第一段不该提 IntentDraft"
    assert "业务要素表" in user or "业务要素" in system
    assert "purpose" in system and "outputShape" in system


def test_clarify_prompt_forbids_guessing():
    system, _ = render_clarify("同步合同")
    assert "不要猜" in system or "宁可问" in system


def test_assemble_refuses_unconfirmed():
    """未确认的计划不许进组装 —— 这是核心闸门。"""
    try:
        render_assemble({"elements": PLAN["elements"]})
    except ValueError as e:
        assert "未确认" in str(e)
    else:
        raise AssertionError("未确认计划竟然进了组装段")


def test_assemble_renders_confirmed_plan():
    confirmed = confirm_plan(PLAN)
    system, user = render_assemble(confirmed)
    assert "已确认的业务计划" in user
    # 关键要素必须出现在组装提示里，避免 LLM 重新猜
    assert "STATUS_ONLY" in user
    assert "LAST_7_DAYS" in user
    assert "采购合同PO关系" in user
    # 缺口要显式告知，不许在画布上拼
    assert "NO_HTTP_NODE" in user
    assert "CUSTOM_EXT" in user


def test_assemble_warns_not_to_build_http_on_canvas():
    confirmed = confirm_plan(PLAN)
    _, user = render_assemble(confirmed)
    assert "不要试图用画布节点拼" in user


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(list(globals().items())):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print("PASS", name)
        except Exception as ex:  # noqa: BLE001
            fails += 1
            print("FAIL", name, "->", ex)
    print()
    print("FAILS", fails)
    sys.exit(1 if fails else 0)
