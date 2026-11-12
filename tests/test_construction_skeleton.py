"""生成面（JavaSkeletonRenderer + PageDefinitionRenderer）离线确定性测试。

北极星：需求→实体模型→后端/前端骨架。全部离线、不联网、凭据无关；
断言基于 golden javap 实证声明（docs/audit/artifacts/customer-*）+ 契约边界。
"""
from pathlib import Path
import pytest

from components.construction import (
    ConstructionEvaluator, ConstructionRuleRegistry,
    NormalizedEntityModel, JavaSkeletonRenderer, PageDefinitionRenderer,
    PAGE_DEFINITION_FIELDS,
)

ROOT = Path(__file__).parents[1]


def _plan(model):
    registry = ConstructionRuleRegistry(ROOT / "docs" / "construction-rules").load()
    return ConstructionEvaluator(registry).plan(model)


def _model():
    return NormalizedEntityModel(
        "demoapp", None, "Customer",
        [
            {"name": "customerNo", "type": "String", "required": True},
            {"name": "amount", "type": "java.math.BigDecimal"},
            {"name": "flag", "type": "java.lang.Boolean"},
        ],
    )


def test_renderer_produces_all_required_artifact_skeletons():
    plan = _plan(_model())
    srcs = JavaSkeletonRenderer().render(plan, _model())
    by_type = {s.artifact_type: s for s in srcs}
    # 6 个 required artifact 都应有骨架
    for t in ("dto", "api", "entity", "domain_service", "app_service_impl", "dao"):
        assert t in by_type, f"{t} 缺骨架"


def test_dto_skeleton_uses_golden_baseclass_and_observed_types():
    plan = _plan(_model())
    srcs = {s.artifact_type: s for s in JavaSkeletonRenderer().render(plan, _model())}
    dto = srcs["dto"]
    assert "public class CustomerDto extends BaseRootDto" in dto.source
    # 观测类型才生成字段（golden javap 类型词表）
    assert "private java.lang.String customerNo;" in dto.source
    assert "private java.math.BigDecimal amount;" in dto.source
    assert "private java.lang.Boolean flag;" in dto.source


def test_unmapped_attribute_type_is_flagged_not_invented():
    model = NormalizedEntityModel("demoapp", None, "C2", [{"name": "weird", "type": "NoSuchJavaType"}])
    plan = _plan(model)
    dto = next(s for s in JavaSkeletonRenderer().render(plan, model) if s.artifact_type == "dto")
    # 未知类型不臆造字段，改留 UNVERIFIED 注释
    assert "private NoSuchJavaType weird;" not in dto.source
    assert "UNVERIFIED" in dto.source


def test_entity_skeleton_extends_baseentity():
    plan = _plan(_model())
    ent = next(s for s in JavaSkeletonRenderer().render(plan, _model()) if s.artifact_type == "entity")
    assert "public class Customer extends BaseEntity" in ent.source
    assert "com.seeyon.boot.domain.entity.BaseEntity" in ent.source


def test_service_skeleton_generics_bound_to_dto_fqn():
    plan = _plan(_model())
    svc = next(s for s in JavaSkeletonRenderer().render(plan, _model()) if s.artifact_type == "domain_service")
    assert "BaseEntityCurdService<com.seeyon.demoapp.dto.CustomerDto>" in svc.source


def test_dao_skeleton_is_interface_extending_base_mybatis_dao():
    plan = _plan(_model())
    dao = next(s for s in JavaSkeletonRenderer().render(plan, _model()) if s.artifact_type == "dao")
    assert "public interface DemoappCustomerDao" in dao.source  # stem 首字母大写
    assert "BaseMybatisDao<com.seeyon.demoapp.domain.entity.Customer>" in dao.source


def test_skeleton_method_bodies_are_marked_unverified():
    plan = _plan(_model())
    srcs = JavaSkeletonRenderer().render(plan, _model())
    for s in srcs:
        # 契约 caveat: generator causality UNKNOWN → 方法体不生成，留 UNVERIFIED
        assert "UNVERIFIED" in s.source or s.artifact_type in ("dto", "entity", "dao")


def test_page_definition_fills_only_observed_fields():
    model = NormalizedEntityModel("demoapp", None, "Customer")
    skel = PageDefinitionRenderer("demoapp").render(model)
    d = skel.to_dict()
    # 有证据的字段被填
    assert d["fields"]["masterEntity"] == "Customer"
    assert d["fields"]["appName"] == "demoapp"
    # pageUrl 是运行态路由，离线不可证 → 在 unverified
    assert "pageUrl" in d["unverified_fields"]
    # 字段集 = C2b LIVE 实证的 18(+1) 字段
    assert "pageUrl" in PAGE_DEFINITION_FIELDS


def test_page_definition_caption_filled_when_present():
    model = NormalizedEntityModel("demoapp", None, "Customer", [], caption="客户管理")
    skel = PageDefinitionRenderer("demoapp").render(model)
    assert skel.fields.get("caption") == "客户管理"


def test_page_definition_caption_unverified_when_absent():
    model = NormalizedEntityModel("demoapp", None, "Customer")
    skel = PageDefinitionRenderer("demoapp").render(model)
    assert "caption" in skel.unverified_fields


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
