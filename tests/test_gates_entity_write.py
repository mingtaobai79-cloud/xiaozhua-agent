"""G34/G35：CREATE_ENTITY 实体可写性闸门。

证据来源（源码级，2026-11-02）：
  - 平台把 CREATE_ENTITY 编译成 `xxxAppService.create(SingleRequest)`；
    实体无 create() → 构建期「找不到符号」
  - 实体字段配了默认值表达式且 requireNull=false 时，
    preCreateBatch → executeExpression* 会**无条件覆盖**传入值

能力表由构建产物 metadata zip 扫描得到（entity-write-capability.json）。
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow import gates  # noqa: E402


def _ce(entity: str, caption: str = "插入") -> dict:
    return {
        "nodeId": "CE_" + entity,
        "actionType": "CREATE_ENTITY",
        "caption": caption,
        "structure": {"id": "com.seeyon.x.domain.entity." + entity},
        "output": {"id": "com.seeyon.x.dto.%sDto" % entity,
                   "dataType": "BIGINTEGER", "name": "v"},
        "mappingType": "attrs",
        "attrs": [{"attrType": {"name": "a", "id": "1", "javaType": "int",
                                "dataType": "INTEGER"},
                   "value": {"type": "Simple", "simple": 1}}],
    }


def _schema(node: dict) -> dict:
    return {"nodes": [node],
            "endNode": {"nodeId": "MFEndNode", "type": "END",
                        "actionType": "END_NODE", "caption": "结束"}}


def _hits(schema: dict) -> list[str]:
    return [p for p in gates.run_gates(schema) if p.startswith(("G34", "G35"))]


def test_capability_table_is_loaded():
    """能力表必须能读到，否则 G34/G35 静默失效。"""
    assert gates._ENTITY_CAPS is not None, "entity-write-capability.json 缺失 → 闸门失效"
    ents = gates._ENTITY_CAPS.get("entities") or {}
    assert len(ents) >= 20, "实体能力表条目过少：%d" % len(ents)


def test_g34_entity_without_create_is_blocked():
    """无 create() 的实体必须被 G34 拦（否则构建期「找不到符号」）。"""
    without = gates._ENTITY_CAPS.get("entities_without_create") or []
    assert without, "能力表里应有 no-create 实体样本"
    for ent in without[:3]:
        hits = _hits(_schema(_ce(ent)))
        assert any(h.startswith("G34") for h in hits), "%s 未被 G34 拦截" % ent


def test_g35_entity_with_override_expression_is_blocked():
    """字段配了 defaultOrExpression 且 requireNull=false 的实体必须被 G35 拦。"""
    ents = gates._ENTITY_CAPS.get("entities") or {}
    # YsFull6956 是实锤样本：20 个字段被 currentYear() 覆盖，撞自身约束永远插不进去
    ys = ents.get("YsFull6956")
    assert ys and ys["fields"], "能力表应含 YsFull6956 的表达式字段"
    hits = _hits(_schema(_ce("YsFull6956")))
    assert any(h.startswith("G35") for h in hits), "YsFull6956 未被 G35 拦截"
    msg = [h for h in hits if h.startswith("G35")][0]
    assert "f03int" in msg or "f05dec" in msg


def test_g35_ignores_system_fields():
    """updater/creator 等系统字段的表达式是平台惯例，不该被 G35 拦。"""
    # MigrationCheckpoint 的表达式只在 updater 上
    assert not _hits(_schema(_ce("MigrationCheckpoint"))), \
        "MigrationCheckpoint 只有系统字段表达式，不应被拦"


def test_clean_entity_passes():
    """没有 create 问题、也没有业务字段表达式的实体会放行。"""
    assert not _hits(_schema(_ce("ExpTypeBase2")))


def test_capability_table_matches_selective_reality():
    """能力表的关键事实（用于防止扫描脚本回归）。"""
    ents = gates._ENTITY_CAPS["entities"]
    # 无 create 的 6 个
    for ent in ("Asongda", "Asongdaasongda", "MigrationBatchItem",
                "MigrationLog", "MigrationPlanField", "MigrationPlanJoin"):
        assert ents[ent]["has_create"] is False, "%s 应无 create" % ent
    # 有 create 的
    for ent in ("YsFull6956", "MigrationCheckpoint", "ExpTypeBase2"):
        assert ents[ent]["has_create"] is True, "%s 应有 create" % ent
