"""UdcPlanner 必须覆盖 spec 里的每个对象，不能只处理每类第一个（复现 planner_skips_additional_objects）。

需求背景：订单应用有多实体/多页面/多微流程；dry-run 计划若漏对象，宿主会漏建。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from components.udc.planner import UdcPlanner
from components.udc.models import ApplicationSpec, EntitySpec, PageSpec, MicroFlowSpec


def _spec():
    return ApplicationSpec(
        "offlineaudit", "Offline audit",
        entities=[EntitySpec("EntityA"), EntitySpec("EntityB")],
        pages=[PageSpec("PageA"), PageSpec("PageB")],
        microflows=[MicroFlowSpec("FlowA"), MicroFlowSpec("FlowB")],
    )


def _steps():
    return UdcPlanner().plan(_spec())["steps"]


def test_plan_covers_every_entity():
    entities = [s["target"] for s in _steps() if s["action"] == "inspect_entity"]
    assert entities == ["EntityA", "EntityB"], f"漏对象：{entities}"


def test_plan_covers_every_page_and_microflow():
    assert [s["target"] for s in _steps() if s["action"] == "inspect_page"] == ["PageA", "PageB"]
    assert [s["target"] for s in _steps() if s["action"] == "inspect_microflow"] == ["FlowA", "FlowB"]


def test_plan_keeps_application_first_and_readonly():
    steps = _steps()
    assert steps[0] == {"action": "inspect_application", "target": "offlineaudit"}
    assert all(s["action"].startswith("inspect_") for s in steps)
