"""`components/construction/requirement_parser.py` 实体名解析的回归闸门。

**为什么有这个文件**：端到端验证（2026-11-08，走 MCP tools/call `xiaozhua_generate_from_requirement`）
发现这个能力的输入面几乎不可用 —— 最常见的两种写法都失败：

    「新建实体 PurchaseApply，含字段 code 文本」
      → entity_name = "新建"（第三个 pattern 把动词当名字吃掉）

    「新建一个实体 PurchaseApply」(带空格)
      → p1 匹配不到，落到 p3 → entity_name = "新建一个"

根因两条，都已修：
  ① 三个 `_ENTITY_PATTERNS` 都缺 `\\s*` —— 中文需求里「实体 X」几乎总带空格；
  ② p3 的捕获面是 `[\\w\\u4e00-\\u9fff]+`（贪婪中文），必须收紧到 Java 标识符。

外加一条：单行需求整句会被 `_FIELD_LINE` 当「字段名 类型」吞下，
产出 `attribute-name-not-java-identifier:新建一个实体` 这种垃圾字段 ——
修法是字段解析前先剥掉实体声明子句。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from components.construction.requirement_parser import (  # noqa: E402
    RequirementParser,
    _ENTITY_PATTERNS,
)

APP = "6419954374508955097"


def _parse(text):
    return RequirementParser().parse(text, APP)


# ---------------------------------------------------------------- 实体名识别
def test_新建实体_带空格也能抓到名字而不是动词():
    """最常见的中文写法。原版返回 entity_name="新建"。"""
    r = _parse("新建实体 PurchaseApply，含字段 code 文本")
    assert "model" in r, "没解析出实体名：%s" % r.get("reason")
    assert r["model"].entity_name == "PurchaseApply", (
        "实体名被解析成 %r —— p3 的贪婪中文捕获把动词吃进去了"
        % r["model"].entity_name)


def test_新建一个实体_带空格():
    r = _parse("新建一个实体 PurchaseApply")
    assert r["model"].entity_name == "PurchaseApply", (
        "实体名 = %r" % r["model"].entity_name)


def test_创建实体紧贴无空格():
    r = _parse("创建实体PurchaseApply")
    assert r["model"].entity_name == "PurchaseApply"


def test_实体名为X():
    r = _parse("实体名为 PurchaseApply\n- code：文本")
    assert r["model"].entity_name == "PurchaseApply"


def test_X实体_倒装句式():
    r = _parse("PurchaseApply 实体\n- code：文本")
    assert r["model"].entity_name == "PurchaseApply"


def test_没有实体名的需求必须如实报_UNVERIFIED():
    """「零臆造」红线：解析不出来就报，不要猜实体名。"""
    r = _parse("需要一个采购申请单，包含申请单号、申请人")
    assert r["status"] == "UNVERIFIED"
    assert r["reason"] == "no entity name found"


# ---------------------------------------------------------------- 字段解析
def test_单行声明不被当成字段行():
    """原版会把整句当「字段名 类型」，产出垃圾 attribute。"""
    r = _parse("新建一个实体 PurchaseApply")
    names = [a.name for a in r["model"].attributes] if r.get("model") else []
    for n in names:
        assert "新建" not in n, "字段名里混进了动词：%r（整句被当字段行吞了）" % n
        assert "实体" not in n, "字段名里混进了「实体」：%r" % n


def test_多行清单的字段与类型都解析正确():
    r = _parse("实体名为 PurchaseApply\n- code：文本\n- amount：金额\n- status：文本")
    got = {a.name: a.type for a in r["model"].attributes}
    assert got == {
        "code": "String",
        "amount": "java.math.BigDecimal",
        "status": "String",
    }, got


# ---------------------------------------------------------------- 反退化
def test_第三个_pattern_不许退回贪婪中文捕获():
    """p3（`X实体`）的捕获面必须是 Java 标识符 —— 退回 `[\\w\\u4e00-\\u9fff]+`
    就会重新把「新建」「新建一个」当实体名。"""
    p3 = _ENTITY_PATTERNS[2]
    m = p3.search("新建实体 PurchaseApply")
    assert m is None, (
        "p3 匹配到了 %r —— 「新建」不该被当成 X 实体 里的 X" % (m.group(1) if m else None))
    m2 = p3.search("PurchaseApply 实体")
    assert m2 and m2.group(1) == "PurchaseApply"
