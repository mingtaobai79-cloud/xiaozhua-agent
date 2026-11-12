"""需求解析器（RequirementParser）+ generate_from_requirement 端到端离线测试。

语义层边界：本层只做确定性规则解析（不调 LLM、不联网）；
宿主 LLM 的语义理解在宿主侧完成，解析不出/类型不识别 → UNVERIFIED，不臆造。
"""
from pathlib import Path

from components.construction.requirement_parser import RequirementParser
from seeyon_host_bootstrap import bootstrap

REQ = """新建实体SupplierContract，标题为供应商合同
- 合同编号：字符串
- 合同金额：金额
- 签订日期：日期
- 是否生效：是否
"""


def test_parser_extracts_entity_caption_and_fields():
    out = RequirementParser().parse(REQ, "demoapp")
    # 中文属性名按证据纪律标 UNVERIFIED（golden 生成物字段名是拼音/英文，转换规则无证据）
    assert out["status"] == "PASS_WITH_UNKNOWNS", out
    model = out["model"]
    assert model.entity_name == "SupplierContract"
    assert model.caption == "供应商合同"
    tv = out["type_verified"]
    assert tv["合同编号"] is True and tv["合同金额"] is True
    assert any("attribute-name-not-java-identifier" in u for u in out["unknowns"])


def test_parser_unverified_when_no_entity():
    out = RequirementParser().parse("帮我看看这个页面", "demoapp")
    assert out["status"] == "UNVERIFIED"
    assert "no entity name found" in out["reason"]


def test_parser_flags_unrecognized_type_not_invented():
    req = "新建实体Foo\n- bar：魔数"
    out = RequirementParser().parse(req, "demoapp")
    tv = out["type_verified"]
    assert tv.get("bar") is False                  # 类型未证实
    assert any("attribute-type-unverified" in u for u in out["unknowns"])


def test_chinese_entity_name_flagged_not_silently_used():
    out = RequirementParser().parse("新建实体供应商合同", "demoapp")
    assert out["status"] in ("PASS", "PASS_WITH_UNKNOWNS", "UNVERIFIED")
    assert any("entity-name-not-java-identifier" in u for u in out["unknowns"]) or out["status"] == "UNVERIFIED"


def test_bootstrap_generate_from_requirement_end_to_end():
    host = bootstrap()
    out = host["generate_from_requirement"](REQ, "demoapp")
    assert out["status"] == "PASS", out.get("parsed", out)
    assert len(out["backend"]["sources"]) == 8
    # 中文属性名不臆造进 DTO（骨架保留 UNVERIFIED 标注，等宿主确认拼音/英文字段名）
    dto = out["backend"]["sources"]["facade/dto/SupplierContractDto.java"]
    assert "UNVERIFIED" in dto
    assert out["frontend"]["fields"]["masterEntity"] == "SupplierContract"
    assert out["frontend"]["fields"]["caption"] == "供应商合同"


def test_bootstrap_generate_from_requirement_unverified_no_entity():
    host = bootstrap()
    out = host["generate_from_requirement"]("随便聊聊", "demoapp")
    assert out["status"] == "UNVERIFIED"
