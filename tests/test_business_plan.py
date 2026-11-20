"""业务拆解计划校验 —— 回归测试。

每条用例都对应一次真实返工，不是凭空造的边界。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.construction.business_plan import (  # noqa: E402
    CLARIFY_RULES, STATUS_BLOCKED, STATUS_CONFIRMED, STATUS_NEED_CONFIRM,
    confirm_plan, plan_routes, plan_status, validate_plan,
)


def _elem(**kw):
    base = {"key": "x", "capability": "做点事", "purpose": "QUERY",
            "inputShape": "PAGE_CONDITION", "outputShape": "DATA_LIST",
            "trigger": "MANUAL"}
    base.update(kw)
    return base


def test_two_interfaces_same_name_one_writes_one_queries():
    """真实坑：两个接口都叫「XX查询」，一个写库一个只读。

    正确计划：purpose 显式区分 → 通过
    """
    plan = {"elements": [
        _elem(key="pull", purpose="SYNC", outputShape="STATUS_ONLY",
              persistTo="采购合同PO关系", persistMode="UPSERT",
              persistKey=["contractNo"], trigger="SCHEDULE",
              scheduleCron="0 0 1 * * ?", timeRange="LAST_7_DAYS"),
        _elem(key="queryPage", purpose="QUERY", outputShape="DATA_LIST"),
    ]}
    blocking, asks = validate_plan(plan)
    assert blocking == [], blocking
    assert asks == [], asks


def test_write_without_persist_target_asks():
    """写入型没说落哪张表 → 必须问，不能猜。"""
    plan = {"elements": [_elem(purpose="WRITE")]}
    blocking, asks = validate_plan(plan)
    assert blocking == []
    assert any("写到哪里" in a for a in asks), asks


def test_upsert_without_key_asks():
    """UPSERT 没给业务键 → 必须问（否则每次都插重复）。"""
    plan = {"elements": [_elem(purpose="SYNC", persistTo="表A",
                               persistMode="UPSERT", outputShape="STATUS_ONLY")]}
    blocking, asks = validate_plan(plan)
    assert any("业务键" in a for a in asks), asks


def test_query_with_persist_target_asks_contradiction():
    """标成 QUERY 却要落表 → 自相矛盾，必须回头问。"""
    plan = {"elements": [_elem(purpose="QUERY", persistTo="表A")]}
    blocking, asks = validate_plan(plan)
    assert any("确认是查询型" in a for a in asks), asks


def test_schedule_without_time_range_asks():
    """定时没给时间范围 → 正是「定时空跑」那个坑。"""
    plan = {"elements": [_elem(purpose="SYNC", persistTo="表A",
                               persistMode="INSERT", outputShape="STATUS_ONLY",
                               trigger="SCHEDULE", scheduleCron="0 0 1 * * ?")]}
    blocking, asks = validate_plan(plan)
    assert any("时间范围" in a for a in asks), asks


def test_schedule_without_cron_asks():
    plan = {"elements": [_elem(purpose="SYNC", persistTo="表A",
                               persistMode="INSERT", outputShape="STATUS_ONLY",
                               trigger="SCHEDULE", timeRange="LAST_7_DAYS")]}
    blocking, asks = validate_plan(plan)
    assert any("多久跑一次" in a for a in asks), asks


def test_missing_purpose_asks_write_or_query():
    """最贵的一维缺失 → 必须问，且问法要直指落不落库。"""
    plan = {"elements": [{"key": "a", "capability": "拉合同"}]}
    blocking, asks = validate_plan(plan)
    assert any("写入型" in a and "查询型" in a for a in asks), asks


def test_invalid_enum_is_blocking():
    plan = {"elements": [_elem(purpose="PULL")]}
    blocking, asks = validate_plan(plan)
    assert any("非法" in b for b in blocking), blocking


def test_status_only_vs_data_list():
    """「出参不是数据」→ STATUS_ONLY；留空必须问。"""
    plan = {"elements": [{"key": "a", "capability": "同步", "purpose": "SYNC",
                          "inputShape": "PAGE_CONDITION", "trigger": "MANUAL",
                          "persistTo": "表A", "persistMode": "INSERT"}]}
    blocking, asks = validate_plan(plan)
    assert any("出参返回什么" in a for a in asks), asks


def test_dependency_must_exist():
    plan = {"elements": [_elem(key="a", dependency="nope")]}
    blocking, asks = validate_plan(plan)
    assert any("不在能力清单里" in b for b in blocking), blocking


def test_empty_plan_blocked():
    blocking, asks = validate_plan({"elements": []})
    assert blocking and "没有任何业务要素" in blocking[0]


def test_status_progression():
    """未确认 → NEED_CONFIRM；确认后 → CONFIRMED；缺项 → NEED_CONFIRM。"""
    ok = {"elements": [_elem()]}
    assert plan_status(ok) == STATUS_NEED_CONFIRM
    confirmed = confirm_plan(ok)
    assert plan_status(confirmed) == STATUS_CONFIRMED

    bad = {"elements": [_elem(purpose="WRITE")]}
    assert plan_status(bad) == STATUS_NEED_CONFIRM

    blocked = {"elements": [_elem(purpose="PULL")]}
    assert plan_status(blocked) == STATUS_BLOCKED


def test_confirm_refuses_incomplete():
    """有未澄清项时，confirm 必须抛错，不许放行。"""
    bad = {"elements": [_elem(purpose="WRITE")]}
    try:
        confirm_plan(bad)
    except ValueError as e:
        assert "未澄清" in str(e)
    else:
        raise AssertionError("缺项计划竟然被确认了")


def test_routes_http_gap_goes_custom_ext():
    """调外部 HTTP → 平台无节点 → 必须 CUSTOM_EXT。"""
    plan = {"elements": [_elem(key="callApi", purpose="SYNC", persistTo="表A",
                               persistMode="INSERT", outputShape="STATUS_ONLY",
                               gap=["NO_HTTP_NODE"])]}
    routes = plan_routes(plan)
    assert routes[0]["route"] == "CUSTOM_EXT", routes


def test_routes_pure_query_stays_canvas():
    plan = {"elements": [_elem(key="q", purpose="QUERY")]}
    assert plan_routes(plan)[0]["route"] == "CANVAS"


def test_routes_schedule_with_dependency_is_mixed():
    plan = {"elements": [
        _elem(key="daily", purpose="SYNC", persistTo="表A", persistMode="INSERT",
              outputShape="STATUS_ONLY", trigger="SCHEDULE",
              scheduleCron="0 0 1 * * ?", timeRange="LAST_7_DAYS", dependency="pull"),
        _elem(key="pull", purpose="SYNC", persistTo="表A", persistMode="INSERT",
              outputShape="STATUS_ONLY"),
    ]}
    routes = {r["key"]: r["route"] for r in plan_routes(plan)}
    assert routes["daily"] == "CANVAS_PLUS_EXT", routes


def test_clarify_rules_mentions_three_traps():
    """提示词必须含三个反例，否则 LLM 会重犯。"""
    assert "绝不按名字判断" in CLARIFY_RULES
    assert "追问落不落表" in CLARIFY_RULES
    assert "STATUS_ONLY" in CLARIFY_RULES
    assert "NO_HTTP_NODE" in CLARIFY_RULES


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(list(globals().items())):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print("PASS", name)
        except Exception as e:  # noqa: BLE001
            fails += 1
            print("FAIL", name, "->", e)
    print()
    print("FAILS", fails)
    sys.exit(1 if fails else 0)
