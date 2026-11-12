"""设置域 · 自定义对象的三类资产必须分开且归位正确（与枚举同一模式）。

锁住 2026-10-21 落位的结构，防止以后又被摊平：

  实现   components/udc/setting/custom_object_constraints.py
  事实   core/facts/udc/setting/custom-object/create.md
  契约   docs/operation-contracts/udc/setting/custom-object-contracts.md
  脚本   tools/core/setting/custom_object_{reference_analysis,write,delete_precheck,delete_batch}.py
  skill  skills/seeyon-udc-setting/SKILL.md（须含自定义对象段落）
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

SETTING = ROOT / "components" / "udc" / "setting"
TOOLS = ROOT / "tools" / "core" / "setting"
FACTS = ROOT / "core" / "facts" / "udc" / "setting" / "custom-object"
CONTRACTS = ROOT / "docs" / "operation-contracts" / "udc" / "setting"
SKILL = ROOT / "skills" / "seeyon-udc-setting" / "SKILL.md"


def test_impl_in_setting_package():
    assert (SETTING / "custom_object_constraints.py").exists(), \
        "自定义对象实现须在 components/udc/setting/"


def test_fact_file_in_setting_domain():
    assert (FACTS / "create.md").exists(), f"缺事实格: {FACTS / 'create.md'}"
    txt = (FACTS / "create.md").read_text(encoding="utf-8")
    assert "udc_data_transfer_object" in txt, "事实格须写明落库表"
    assert "待删除清单" in txt, "事实格须保留待删除清单小节"


def test_contract_in_setting_domain():
    p = CONTRACTS / "custom-object-contracts.md"
    assert p.exists(), f"缺契约: {p}"
    txt = p.read_text(encoding="utf-8")
    for op in ("udcDataTransferObjectPost", "udcDataTransferObjectUpdatePost",
               "udcDataTransferObjectDeletePost"):
        assert op in txt, f"契约缺 operation: {op}"


def test_tools_all_present():
    for name in ("custom_object_reference_analysis.py", "custom_object_write.py",
                 "custom_object_delete_precheck.py", "custom_object_delete_batch.py",
                 "custom_object_relation_fields.py"):
        assert (TOOLS / name).exists(), f"缺脚本: {TOOLS / name}"


def test_field_fact_documents_real_endpoint():
    """字段落库事实：UpdatePost 不承载字段，真实端点是 UpdateDtoPost。"""
    p = FACTS / "fields.md"
    assert p.exists(), f"缺字段事实格: {p}"
    txt = p.read_text(encoding="utf-8")
    assert "udcDataTransferObjectUpdateDtoPost" in txt, "字段事实格须写明真实端点"
    assert "全量替换" in txt, "须写明 attributes 全量替换语义"
    assert "PRIMITIVE" in txt and "COMPOSITE" in txt, "须写明 dataTypeCategory 两个值"
    assert "OBJECT" in txt and "LIST" in txt, "须写明 type 两个值"
    assert "假成功" in txt, "须保留 UpdatePost 假成功的坑"


def test_relation_fields_tool_reads_before_writing():
    """组装工具必须先 SelectDtoGet 拉全文再整体回传（attributes 全量替换）。"""
    src = (TOOLS / "custom_object_relation_fields.py").read_text(encoding="utf-8")
    assert "udcDataTransferObjectSelectDtoGet" in src, "缺 SelectDtoGet"
    assert "udcDataTransferObjectUpdateDtoPost" in src, "缺真实字段端点"
    assert "--i-have-write-authorization" in src, "缺显式授权开关"
    i_read = src.index("def get_dto")
    i_write = src.index("udcDataTransferObjectUpdateDtoPost")
    assert i_read < i_write, "读 DTO 必须早于写"


def test_precheck_covers_four_reference_forms():
    """只查 name/caption 会漏 id 形式引用 —— 预检必须四种都查。"""
    src = (TOOLS / "custom_object_delete_precheck.py").read_text(encoding="utf-8")
    for form in ('"name"', '"caption"', '"id"', '"guid"'):
        assert form in src, f"预检缺引用形式: {form}"
    assert "method_valid" in src, "预检缺阳性对照判定"


def test_precheck_writes_full_backup():
    src = (TOOLS / "custom_object_delete_precheck.py").read_text(encoding="utf-8")
    assert "udc_data_transfer_object.json" in src, "预检必须落全量行备份"
    assert "SELECT *" in src, "备份须取全部列"


def test_batch_tool_is_readback_gated():
    """成功码不代表删掉了：批量删必须逐个回读 DB。"""
    src = (TOOLS / "custom_object_delete_batch.py").read_text(encoding="utf-8")
    assert "--i-have-write-authorization" in src, "批量删缺显式授权开关"
    assert "SELECT id" in src, "批量删缺回读查询"
    i_send = src.index("gql(client")
    i_read = src.index("SELECT id", i_send)
    assert i_read > i_send, "回读必须晚于删除请求"
    assert "progress.json" in src, "批量删须可续跑"


def test_skill_covers_custom_object():
    txt = SKILL.read_text(encoding="utf-8")
    assert "自定义对象" in txt, "设置域 skill 须覆盖自定义对象"
    for need in ("udcDataTransferObjectPost", "udcDataTransferObjectDeletePost",
                 "udc_data_transfer_object", "custom_object_reference_analysis.py"):
        assert need in txt, f"skill 缺关键事实: {need}"
    # 三条硬经验必须留在 skill 里，不能只写在 commit message
    assert "回读" in txt, "skill 须写明回读判定"
    assert "缓存" in txt, "skill 须写明页面缓存陷阱"


def test_skill_states_authorization_boundary():
    """删除取决于用户授权，不取决于脚本无引用结论。"""
    txt = SKILL.read_text(encoding="utf-8")
    assert "用户" in txt and ("授权" in txt), "skill 须写明授权边界"
