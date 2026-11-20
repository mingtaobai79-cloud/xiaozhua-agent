"""用真实需求回归：验证拆解层能否自动问出「哪个接口入库」这类问题。

需求原文取自真实项目（客户信息已脱敏，只保留业务语义）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.construction.business_plan import (  # noqa: E402
    STATUS_BLOCKED, STATUS_CONFIRMED, STATUS_NEED_CONFIRM,
    confirm_plan, plan_routes, plan_status, validate_plan,
)

# ── 场景一：LLM 按名字猜错（两个都当查询）——必须被拦下 ──
WRONG_GUESS = {
    "elements": [
        {"key": "contractInfo", "capability": "拉合同明细", "purpose": "QUERY",
         "inputShape": "PAGE_CONDITION", "outputShape": "DATA_LIST", "trigger": "MANUAL"},
        {"key": "contractPo", "capability": "拉合同PO关系", "purpose": "QUERY",
         "inputShape": "PAGE_CONDITION", "outputShape": "DATA_LIST", "trigger": "MANUAL"},
    ]
}

# ── 场景二：用户澄清后的正确形态 ──
RIGHT_PLAN = {
    "elements": [
        {"key": "contractPoSync", "capability": "每天同步销售合同与PO关系明细",
         "purpose": "SYNC", "inputShape": "PAGE_CONDITION",
         "outputShape": "STATUS_ONLY",              # ★ 出参不是数据
         "persistTo": "采购合同PO关系", "persistMode": "UPSERT",
         "persistKey": ["contractNo", "poNumber"],
         "trigger": "SCHEDULE", "scheduleCron": "0 0 1 * * ?",
         "timeRange": "LAST_7_DAYS",
         "gap": ["NO_HTTP_NODE"]},
        {"key": "contractInfoQuery", "capability": "分页查询合同明细（不落库）",
         "purpose": "QUERY", "inputShape": "PAGE_CONDITION",
         "outputShape": "DATA_LIST",
         "trigger": "MANUAL", "gap": ["NO_HTTP_NODE"]},
        {"key": "dailySync", "capability": "每天定时触发同步",
         "purpose": "SYNC", "inputShape": "NONE",
         "outputShape": "NONE", "persistTo": "采购合同PO关系",
         "persistMode": "UPSERT", "persistKey": ["contractNo"],
         "trigger": "SCHEDULE", "scheduleCron": "0 0 1 * * ?",
         "timeRange": "LAST_7_DAYS", "dependency": "contractPoSync"},
    ]
}


def test_wrong_guess_is_stopped():
    """按名字猜成「两个都是查询」时，计划必须停在 NEED_CONFIRM 之前就被问。

    实际上这个形态本身字段是齐全的（QUERY 不要求 persist），
    所以不会被 blocking 拦 —— 这是关键：结构合法但业务错。
    因此必须靠 confirm 环节的人为确认来兜住。
    """
    blocking, asks = validate_plan(WRONG_GUESS)
    assert blocking == [], blocking
    # 结构合法 → 但没人确认过，所以状态必须是 NEED_CONFIRM
    assert plan_status(WRONG_GUESS) == STATUS_NEED_CONFIRM
    # 未确认不许进组装
    assert WRONG_GUESS.get("confirmedBy") is None


def test_missing_output_shape_asked():
    """如果连出参形态都没填，必须被问 —— 这是「出参不是数据」的入口。"""
    plan = {"elements": [{"key": "a", "capability": "同步", "purpose": "SYNC",
                          "inputShape": "PAGE_CONDITION", "trigger": "MANUAL",
                          "persistTo": "表A", "persistMode": "INSERT"}]}
    blocking, asks = validate_plan(plan)
    assert any("出参返回什么" in a for a in asks), asks


def test_right_plan_ready_and_routes():
    blocking, asks = validate_plan(RIGHT_PLAN)
    assert blocking == [], blocking
    assert asks == [], asks
    assert plan_status(RIGHT_PLAN) == STATUS_NEED_CONFIRM

    confirmed = confirm_plan(RIGHT_PLAN)
    assert plan_status(confirmed) == STATUS_CONFIRMED

    routes = {r["key"]: r["route"] for r in plan_routes(confirmed)}
    # 调外部 HTTP → 必须 CUSTOM_EXT
    assert routes["contractPoSync"] == "CUSTOM_EXT", routes
    assert routes["contractInfoQuery"] == "CUSTOM_EXT", routes
    # 定时壳调子流程 → 混合
    assert routes["dailySync"] == "CANVAS_PLUS_EXT", routes


def test_user_quote_maps_to_status_only():
    """用户原话「出参不是数据而是同步接口」→ 必须是 STATUS_ONLY 而非 DATA_LIST。"""
    e = RIGHT_PLAN["elements"][0]
    assert e["outputShape"] == "STATUS_ONLY"
    assert e["purpose"] == "SYNC"
    assert e["persistTo"] == "采购合同PO关系"
    # 且必须是定时 + 有时间范围（否则定时空跑）
    assert e["trigger"] == "SCHEDULE"
    assert e["timeRange"] == "LAST_7_DAYS"


def test_no_http_node_gap_recorded():
    """平台无 HTTP 节点这条硬约束必须落在 gap 里，不能靠记忆。"""
    for e in RIGHT_PLAN["elements"]:
        if e["key"] in ("contractPoSync", "contractInfoQuery"):
            assert "NO_HTTP_NODE" in e["gap"], e


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
