from components.construction.models import NormalizedEntityModel
from components.construction.registry import ConstructionRuleRegistry
from components.construction.evaluator import ConstructionEvaluator
from components.construction.fixtures import golden_application_id as _gid

# 黄金样本的应用标识是**仓外事实**（客户证据仓 xiaozhua-customer-evidence），
# 仓库内不硬编码客户名；期望值运行时解析，仓外缺失时退化为占位自洽校验。
_GID = _gid()

def registry():
    from pathlib import Path
    return ConstructionRuleRegistry(Path(__file__).resolve().parents[2] / "docs" / "construction-rules").load()

def test_customer_produces_eight_core_artifacts():
    plan = ConstructionEvaluator(registry()).plan(NormalizedEntityModel("demoapp", None, "Customer"))
    assert len(plan.artifacts) == 8
    assert [a.relative_path for a in plan.artifacts] == [
        "facade/dto/CustomerDto.java", "facade/api/CustomerAppService.java",
        "biz/domain/entity/Customer.java", "biz/domain/service/CustomerService.java",
        "biz/appservice/CustomerAppServiceImpl.java", "biz/domain/dao/DemoappCustomerDao.java",
        "web/controller/AbstractCustomerController.java", "web/controller/CustomerController.java"
    ]

def test_golden_hetongdangan_names_match():
    plan = ConstructionEvaluator(registry()).plan(NormalizedEntityModel(_GID, None, "Hetongdangan"))
    assert {a.fully_qualified_name for a in plan.artifacts} == {
        "com.seeyon." + _GID + ".api.HetongdanganAppService",
        "com.seeyon." + _GID + ".appservice.HetongdanganAppServiceImpl",
        "com.seeyon." + _GID + ".controller.AbstractHetongdanganController",
        "com.seeyon." + _GID + ".controller.HetongdanganController",
        "com.seeyon." + _GID + ".domain.dao." + _GID.capitalize() + "HetongdanganDao",
        "com.seeyon." + _GID + ".domain.entity.Hetongdangan",
        "com.seeyon." + _GID + ".domain.service.HetongdanganService",
        "com.seeyon." + _GID + ".dto.HetongdanganDto"
    }

def test_invalid_entity_name_is_blocked_not_fixed():
    plan = ConstructionEvaluator(registry()).plan(NormalizedEntityModel("demoapp", None, "bad-name"))
    assert plan.blocked

def test_unknown_attribute_type_is_preserved():
    plan = ConstructionEvaluator(registry()).plan(NormalizedEntityModel("demoapp", None, "Customer", [dict(name="x", type="UNKNOWN")]))
    assert any("attribute:x:type" in x for x in plan.unknown)
