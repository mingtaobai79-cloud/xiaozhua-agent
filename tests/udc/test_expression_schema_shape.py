"""表达式 schema 形态：必须锁定「实体 OBJECT 树 + 点路径 token」。

真实事故（2026-10-23）
----------------------
用户截图：计算设置弹窗红字
    「变量:整数字段 在上下文中不存在，请确认!」

而我当时的验收记录写的是 **LIVE PASS**。为什么？
因为我验的是 check=BOOT_0000 / transform 成功 / DB 回读有值 ——
**这三步全过，页面照样报错。**

三维对照实验（test2，实体 ysFull6956 / f03int，表达式 `f03int + f03int`）
--------------------------------------------------------------------------
  组合                          check         transform 产物           页面
  A 扁平字段节点 + value=f03int  BOOT_0000     context 扁平/INTEGER     报错
  B 实体树     + value=f03int    FORMULA_6058  ——                       -
  C 实体树     + value=实体.字段  BOOT_0000     OBJECT 树 / 点路径       正常

⇒ 下面每条测试都在钉住 C，并且要能咬住 A（假绿）和 B（真错）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.expression.schema_binding import (  # noqa: E402
    bind_schemas,
    check_binding,
    tree_node,
)
from components.udc.expression.token import build_variable_token  # noqa: E402

ENTITY = "ysFull6956"
ENTITY_DESC = "小爪验收实体全量"
EID = "-2537349473285092530"
F03 = "-6040618203145140416"
F04 = "4894426588496688945"


def _schema_tree():
    """模拟 POST /expression/schema 返回的 content（实体根 + 字段）。"""
    return [{
        "name": ENTITY, "description": ENTITY_DESC, "type": "OBJECT",
        "selectable": True, "enableDataI18n": False,
        "uniformityParams": {"paramId": EID, "paramCategory": "Entity"},
        "properties": [
            {"name": "f03int", "description": "整数字段", "type": "INTEGER",
             "selectable": True, "enableDataI18n": False,
             "uniformityParams": {"paramId": F03, "paramCategory": "Attr"}},
            {"name": "f04bigint", "description": "大整数字段", "type": "BIGINTEGER",
             "selectable": True, "enableDataI18n": False,
             "uniformityParams": {"paramId": F04, "paramCategory": "Attr"}},
        ],
    }]


def _tokens_point_path():
    return [
        build_variable_token(F03, "f03int", "整数字段",
                             entity_name=ENTITY, entity_desc=ENTITY_DESC, index=1),
        {"uid": "u2", "type": "OPERATOR", "value": "+", "desc": "+"},
        build_variable_token(F03, "f03int", "整数字段",
                             entity_name=ENTITY, entity_desc=ENTITY_DESC, index=2),
    ]


# ---------------------------------------------------------------- token
def test_variable_token_gets_entity_prefix():
    t = build_variable_token(F03, "f03int", "整数字段",
                             entity_name=ENTITY, entity_desc=ENTITY_DESC)
    assert t["value"] == "%s.f03int" % ENTITY
    assert t["desc"] == "%s.整数字段" % ENTITY_DESC


def test_variable_token_does_not_double_prefix():
    t = build_variable_token(F03, "%s.f03int" % ENTITY, "%s.整数字段" % ENTITY_DESC,
                             entity_name=ENTITY, entity_desc=ENTITY_DESC)
    assert t["value"].count(".") == 1


def test_variable_token_without_entity_keeps_short_name():
    """应用参数（CONFIG_PARAM）不带实体前缀，这是合法的。"""
    t = build_variable_token("123", "zxjPageSize", "分页大小")
    assert t["value"] == "zxjPageSize"


def test_variable_token_requires_param_id():
    try:
        build_variable_token(None, "f03int", "整数字段")
    except ValueError as exc:
        assert "paramId" in str(exc)
    else:
        raise AssertionError("缺 paramId 必须报错")


# ---------------------------------------------------------------- schemas
def test_bind_schemas_returns_object_tree():
    """★ 核心：schemas 必须是 OBJECT 树，不能是扁平字段节点。"""
    out = bind_schemas(_tokens_point_path(), _schema_tree())
    assert len(out) == 1, "按实体分组，应只有一个根"
    root = out[0]
    assert root["type"] == "OBJECT"
    assert root["name"] == ENTITY
    assert isinstance(root.get("properties"), list) and root["properties"], \
        "properties 不能为空 —— 空了就退化成扁平节点，页面报 FORMULA_6058"
    assert [p["name"] for p in root["properties"]] == ["f03int"]


def test_bind_schemas_keeps_uniformity_params_on_children():
    out = bind_schemas(_tokens_point_path(), _schema_tree())
    child = out[0]["properties"][0]
    assert child["uniformityParams"]["paramId"] == F03
    assert child["uniformityParams"]["paramCategory"] == "Attr"


def test_bind_schemas_flat_mode_still_available_for_legacy():
    """as_tree=False 保留旧行为，但**默认必须是树**。"""
    flat = bind_schemas(_tokens_point_path(), _schema_tree(), as_tree=False)
    assert flat[0]["type"] == "INTEGER"
    assert "properties" not in flat[0]


def test_bind_schemas_groups_multiple_entities():
    """引用两个实体的字段时应出两个根。"""
    other = dict(_schema_tree()[0])
    other["name"] = "otherEntity"
    other["uniformityParams"] = {"paramId": "9", "paramCategory": "Entity"}
    other["properties"] = [{
        "name": "f01text", "description": "文本字段", "type": "STRING",
        "selectable": True, "enableDataI18n": False,
        "uniformityParams": {"paramId": "777", "paramCategory": "Attr"}}]
    toks = _tokens_point_path() + [
        build_variable_token("777", "f01text", "文本字段",
                             entity_name="otherEntity", entity_desc="另一实体")]
    out = bind_schemas(toks, _schema_tree() + [other])
    assert len(out) == 2


def test_bind_schemas_raises_on_unknown_param():
    toks = [build_variable_token("999999", "nope", "不存在", entity_name=ENTITY)]
    try:
        bind_schemas(toks, _schema_tree())
    except ValueError as exc:
        assert "999999" in str(exc)
    else:
        raise AssertionError("未知 paramId 必须抛错，不能静默放过")


# ---------------------------------------------------------------- 咬住假绿
def test_check_binding_bites_flat_schemas():
    """★ 咬住组合 A：扁平 schema 能过 check/transform，但页面会报错。
    本地校验必须判它不合格。"""
    toks = _tokens_point_path()
    flat = bind_schemas(toks, _schema_tree(), as_tree=False)
    errs = check_binding(toks, flat)
    assert errs, "扁平 schemas 必须被本地校验咬住（否则就是放行假绿）"
    assert any("OBJECT" in e or "FORMULA_6058" in e for e in errs)


def test_check_binding_bites_short_token_value():
    """★ 咬住组合 B：树形态下 token 用短名 → check 直接 FORMULA_6058。"""
    toks = [build_variable_token(F03, "f03int", "整数字段"),
            {"uid": "u2", "type": "OPERATOR", "value": "+", "desc": "+"},
            build_variable_token(F03, "f03int", "整数字段")]
    tree = bind_schemas(_tokens_point_path(), _schema_tree())
    errs = check_binding(toks, tree)
    assert errs, "短名 token + 树 schemas 必须被判不合格"
    assert any("实体前缀" in e or "点路径" in e for e in errs)


def test_check_binding_passes_for_correct_combination():
    """组合 C 必须零错误 —— 否则闸门会挡住正确写法。"""
    toks = _tokens_point_path()
    tree = bind_schemas(toks, _schema_tree())
    assert check_binding(toks, tree) == []


# ---------------------------------------------------------------- 文档化事实
def test_schema_binding_doc_records_the_three_way_comparison():
    """三维对照表必须写在模块 docstring 里 —— 这是最贵的知识。"""
    src = (ROOT / "components" / "udc" / "expression" / "schema_binding.py").read_text(
        encoding="utf-8")
    assert "FORMULA_6058" in src
    assert "在上下文中不存在" in src
    assert "OBJECT" in src
    for tag in ("A ", "B ", "C "):
        assert tag in src
    assert "check/transform 通过" in src, "必须写明「三步全过页面照样报错」"
