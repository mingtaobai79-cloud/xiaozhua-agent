"""实体规则域的两条硬约束（都是页面报错后才发现的）

事故 1（2026-10-23 用户截图）
------------------------------
规则条件写完后，页面「表达式设置」弹窗红字：

    变量 整数字段 在上下文中不存在，请确认！

而 `checkSchema` 返回 `check=True, errors=0` —— **后端校验通过，页面照样报错**。
根因：token 的 `desc` 只写了字段标题「整数字段」，缺实体标题前缀。
必须写「小爪验收实体全量.整数字段」。

★ 这和 `schema_binding` 里「实体树 + 点路径」是**同一条规则**，
  我在表达式域修过一次，在规则域又犯了一次 —— 所以这里用测试钉死。
  客户真实规则样本的 desc 也是完整路径：
  `微流程.查询单条数据(1).投标报备申请_1 [投标报备申请].流程类型`

事故 2
------
规则 schema 缺 `endNode`，画布上「结束」那一环不出现。
真实实体规则 schema 顶层必带：

    endNode = {id:"", name:"", type:"END", actionType:"END_NODE",
               nodeId:"MFEndNode", caption:"结束", ...}
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "core" / "entity"))

EID = "-2537349473285092530"
F03 = "-6040618203145140416"
ENT_NAME = "ysFull6956"
ENT_DESC = "小爪验收实体全量"
FIELDS = {"f03int": (F03, "INTEGER", "整数字段")}


def _mod():
    import importlib
    import write_entity_rule as m
    return importlib.reload(m)


def test_token_desc_carries_entity_prefix():
    """★ desc = 实体规则.开始.<实体标题>.<字段标题>；value = dto.dto.<字段>。"""
    m = _mod()
    tokens, schemas = m._compile(None, "1", EID, "f03int > 500",
                                 ENT_NAME, FIELDS, ENT_DESC)
    var = [t for t in tokens if t["type"] == "VARIABLE"]
    assert len(var) == 1
    assert var[0]["desc"] == "实体规则.开始.小爪验收实体全量.整数字段", \
        "desc 缺前缀 → 页面报「变量 xxx 在上下文中不存在」"
    assert var[0]["value"] == "dto.dto.f03int", \
        "实体规则的值路径是 dto.dto.<字段>（用户手配样本两级）"
    assert "paramId" not in var[0], "规则条件的 VARIABLE 不带 paramId"


def test_schema_root_is_start_node_not_entity():
    """context 根是「开始」节点（name=dto），实体挂在它的第一个属性上。"""
    m = _mod()
    _, schemas = m._compile(None, "1", EID, "f03int > 500",
                            ENT_NAME, FIELDS, ENT_DESC)
    root = schemas[0]
    assert root["name"] == "dto"
    assert root["description"] == "开始"
    assert root["type"] == "OBJECT"
    assert root["selectable"] is False
    assert root["uniformityParams"]["paramCategory"] == "ENTITY"
    assert root["uniformityParams"]["paramId"] == EID
    prop = root["properties"][0]
    assert prop["name"] == "dto"
    assert prop["description"] == ENT_DESC
    assert prop["uniformityParams"]["paramCategory"] == "OBJECT", \
        "属性层 paramCategory 是 OBJECT（对应 N() 的 Entity→Object）"
    assert [p["name"] for p in prop["properties"]] == ["f03int"]


def test_compile_without_entity_desc_still_keeps_prefix():
    """不传实体标题时 desc 仍带域前缀，只是少了实体段。"""
    m = _mod()
    tokens, _ = m._compile(None, "1", EID, "f03int > 1", ENT_NAME, FIELDS, "")
    var = [t for t in tokens if t["type"] == "VARIABLE"][0]
    assert var["desc"] == "实体规则.开始.整数字段"



def test_end_node_shape_matches_platform():
    """endNode 必须是 END/END_NODE/MFEndNode/结束 —— 缺了画布少一环。"""
    m = _mod()
    en = m.end_node()
    assert en["type"] == "END"
    assert en["actionType"] == "END_NODE"
    assert en["nodeId"] == "MFEndNode"
    assert en["caption"] == "结束"


def test_node_template_has_three_stage_shape():
    """三个节点：开始（隐式）+ 条件分支 + 结束。"""
    m = _mod()
    sc = m.node_template(EID, "1", "ruleTest", "测试规则")
    assert "endNode" in sc and sc["endNode"]["type"] == "END"
    assert len(sc["nodes"]) == 1
    br = sc["nodes"][0]
    assert br["type"] == "BRANCH"
    assert len(br["conditions"]) == 2
    assert [c["name"] for c in br["conditions"]] == ["ifBranch", "elseBranch"]
    # elseBranch 恒无条件
    assert br["conditions"][1]["expression"] is None
    # ★ 用户手配样本：input 是实体最简形态，trigger 被前端清成 {}
    inp = sc["input"]
    assert inp == {"dataType": "ENTITY", "type": "OBJECT",
                   "name": "dto", "id": EID}, \
        "input 是 {dataType:ENTITY,name:dto,id:实体id}，不是自造的 _FLOW_INPUT_xxx"
    assert sc["trigger"] == {}, "前端保存后 trigger 恒为 {}，补 MFStartNode 那套会被清掉"
    assert sc["sourceType"] == "PAGE"


def test_action_nodes_have_distinct_shapes():
    """★ 三种动作节点的键名各不相同（实测样本，不能混用）。"""
    m = _mod()
    info = (F03, "INTEGER", "整数字段 [整数]")

    dv = m.default_value_node(EID, "f03int", info, "", "s1")
    assert dv["actionType"] == "DEFAULT_VALUE"
    assert dv["type"] == "ACTIVITY"
    assert isinstance(dv["attrs"], list) and dv["attrs"], "默认值节点字段在 attrs 数组里"
    assert dv["attrs"][0]["param"]["name"] == "f03int"
    assert dv["attrs"][0]["param"]["path"] == [], "动作节点字段的 path 是空数组"
    assert dv["attrs"][0]["value"]["desc"] == "空值"
    assert "param" not in dv, "DEFAULT_VALUE 没有顶层 param"

    sm = m.show_message_node(F03, "f03int", info, "超限", "s2")
    assert sm["actionType"] == "SHOW_MESSAGE"
    assert sm["param"]["name"] == "f03int" and sm["level"] == "error"
    assert sm["value"]["simple"] == "超限"

    rq = m.required_node(F03, "f03int", info, "请填写", "s3")
    assert rq["actionType"] == "ATTRIBUTE_REQUIRED"
    assert isinstance(rq["params"], list), "必填节点字段是 params（复数数组）"
    assert rq["params"][0]["name"] == "f03int"


def test_group_type_maps_to_platform_enum():
    """CLI 的 group-type 三个值必须映射到平台枚举。"""
    src = (ROOT / "tools" / "core" / "entity" / "write_entity_rule.py").read_text(
        encoding="utf-8")
    assert '"validate": "VALIDATE"' in src
    assert '"default": "DEFAULT_VALUE"' in src
    assert '"assign": "ASSIGN_VALUE"' in src


def test_source_records_both_pitfalls():
    """两个坑必须写在源码里 —— 这是最贵的知识，别只留在对话里。"""
    src = (ROOT / "tools" / "core" / "entity" / "write_entity_rule.py").read_text(
        encoding="utf-8")
    assert "在上下文中不存在" in src
    assert "MFEndNode" in src
    assert "BOOT_0000" in src, "checkSchema 的成功码陷阱必须写明"


def test_assign_value_node_uses_assign_value_not_set_value(monkeypatch):
    """★ 分支动作节点：actionType 必须是 ASSIGN_VALUE。

    用 SET_VALUE 时 checkSchema 也返回 check=True errors=0 —— 但页面按
    「页面规则版」定义渲染（element 语义），是假绿。
    两者是前端 bundle 里同 type 的两份定义：
      t8 = 实体规则版（key: param + value）
      ez = 页面规则版（key: element + value）
    """
    m = _mod()
    monkeypatch.setattr(m, "_expr_const",
                        lambda *a, **k: {"schema": "{}", "title": "超限"})
    node = m.assign_value_node(None, "1", "-2537349473285092530",
                               "com.seeyon.x.dto.YDto", "f01text",
                               ("-4144494497326241617", "STRING", "文本字段"),
                               "超限", "If001")
    assert node["type"] == "ACTIVITY", "写 ASSIGN_VALUE 会被后端判「无效的数据」"
    assert node["actionType"] == "ASSIGN_VALUE", "写 SET_VALUE 能过校验但页面渲染错"
    assert node["param"] and "element" not in node
    assert node["value"]["desc"] == "超限"


def test_assign_value_param_has_caption_and_list_path(monkeypatch):
    """param 三项必填：caption 非空、path 必须是数组（字符串永远报缺）。"""
    m = _mod()
    monkeypatch.setattr(m, "_expr_const",
                        lambda *a, **k: {"schema": "{}", "title": "x"})
    node = m.assign_value_node(None, "1", "-1", "com.seeyon.x.dto.YDto", "f01text",
                               ("-414", "STRING", "文本字段"), "x", "s")
    p = node["param"]
    assert p["caption"] == "文本字段"
    assert isinstance(p["path"], list) and p["path"], \
        "path 给字符串时后端永远报 param.path 必填"
    assert p["path"][0]["fieldId"] == "-414"
    assert p["path"][0]["entity"]["id"] == "-1"


def test_source_documents_assign_value_traps():
    """「SET_VALUE 假绿」必须写在源码里，否则下次又会踩。"""
    src = (ROOT / "tools" / "core" / "entity" / "write_entity_rule.py").read_text(
        encoding="utf-8")
    assert "ASSIGN_VALUE" in src and "SET_VALUE" in src
    assert "假绿" in src or "页面规则版" in src
    assert "param.path" in src


def test_func_token_shape():
    """★ 函数 token：FUNCTION + subOps（二维数组，外层=参数序号）。

    实测合法样本（用户手配校验规则）：
      {"type":"FUNCTION","value":"isNull","desc":"为空",
       "subOps":[[<参数1 tokens>]]}
    """
    m = _mod()
    t = m._func_token('textToLong("123")', {}, "dto.dto.", "实体规则.开始.", False)
    assert len(t) == 1
    fn = t[0]
    assert fn["type"] == "FUNCTION"
    assert fn["value"] == "textToLong"
    assert fn["desc"] == "文本转长整数"
    assert isinstance(fn["subOps"], list) and len(fn["subOps"]) == 1
    assert fn["subOps"][0][0]["type"] == "CONSTANT"


def test_func_token_string_constant_keeps_quotes():
    """★ 字符串常量必须带引号，否则 transform 按数字推断类型。

    实测：textToLong("123") 传裸 123 →
      FORMULA_6158 函数:【文本转长整数】第 1 个参数类型不匹配 期望 STRING 实际 INTEGER
    """
    m = _mod()
    t = m._func_token('textToLong("123")', {}, "dto.dto.", "x.", False)
    const = t[0]["subOps"][0][0]
    assert const["value"] == '"123"', "裸 123 会被推断成 INTEGER"
    assert const["desc"] == "123"


def test_func_token_multi_params():
    """三参数函数：subOps 要按参数拆成三组。"""
    m = _mod()
    t = m._func_token('substring("abcdef", 1, 3)', {}, "dto.dto.", "x.", False)
    fn = t[0]
    assert fn["value"] == "substring" and fn["desc"] == "按长度截取字符串"
    assert len(fn["subOps"]) == 3, "subOps 外层长度 = 参数个数"


def test_func_token_unknown_function_returns_empty():
    """未知函数不吞掉，交给普通表达式路径处理。"""
    m = _mod()
    assert m._func_token("noSuchFunc(1)", {}, "dto.dto.", "x.", False) == []


def test_one_default_value_rule_per_entity():
    """★ 平台硬限制：同一实体只能有一条默认值规则。

    create 返回 UDC_MICROFLOW_0027「当前实体下已存在默认值规则，无法再次新建」。
    全库 type=2 AND group_type=3 只有 1 条，也是这个原因。
    源码里必须留下这条约束。
    """
    src = (ROOT / "tools" / "core" / "entity" / "write_entity_rule.py").read_text(
        encoding="utf-8")
    assert "DEFAULT_VALUE" in src
    assert "0027" in src or "只能有一条" in src or "已存在默认值规则" in src


def test_create_uses_release_state_not_draft():
    """★ state 必须是 20（RELEASE），写 DRAFT 建出来的规则在列表里查不到。

    实测：state=10 的规则不出现在 udcMicroflowSearchEntityRulePost 结果里，
    页面规则列表看不见，用户会以为没建成功（只有直接拼编辑器 URL 才进得去）。
    """
    src = (ROOT / "tools" / "core" / "entity" / "write_entity_rule.py").read_text(
        encoding="utf-8")
    assert '"state": 20' in src, "create 必须直接给 state=20"
    assert '"state": "DRAFT"' not in src, "DRAFT 建出来的规则列表查不到"
    assert "查不到" in src or "隐形" in src, "这个坑要写进注释"
