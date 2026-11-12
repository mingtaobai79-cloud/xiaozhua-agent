"""闸门文档 ↔ 代码 双向契约。

为什么要有这条：技能（~/.hermes/skills）和仓库是**两套独立文件**，靠人同步必然漂移。
本轮就发生过真实漂移——技能里补了 G34/G35、脚本自检、glob 口径坑，
仓库里只有代码没有文档、只有 55 行草稿脚本没有正式版，直到用户问「seeyon agent
里面的东西补充了吗」才发现。

本测试断言两件事，任何一边单独改动都会失败：
  1. gates.py 里每个**真正会触发**的 G 编号，都能在 generation-gates.md 找到；
  2. 文档里写的 G 编号，在 gates.py 里真实存在（防止文档写了不存在的规则）。

★ 判"真正会触发"而不是"文本出现过"：G15 这类规则用 f-string 拼，
 单纯 grep 'G[0-9]+' 会因为注释里的提及而误判。取 problems.append 上下文更准。
"""
import ast
import os
import re

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES_PY = os.path.join(REPO, "components", "udc", "microflow", "gates.py")
GATES_MD = os.path.join(REPO, "core", "facts", "udc", "microflow",
                        "generation-gates.md")

# 历史遗留：G15 由专门段落记录（RETRIEVE 组合条件 GROUP 形态），
# 文档里确实写了，但只在一个 line 里出现过，用宽松匹配会漏。
# 这里不豁免任何编号——缺失就是缺失，要么补文档要么删代码。
_GATE_RE = re.compile(r"\bG(\d+)\b")


def _codes_in_source() -> set[str]:
    """gates.py 里所有**可能**产生的 G 编号（含 f-string / 拼接字符串）。

    用 AST 取全部字符串常量再匹配，避免用源码 grep 时被注释里的
    「G15: ...」这类提及骗到（注释里的编号不产生任何 problem）。
    """
    src = open(GATES_PY, encoding="utf-8", errors="replace").read()
    tree = ast.parse(src)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            # 只认形如 "G12 ..." / "G12 [%s]" / f"G15 {nid}: ..." 的开头，
            # 即编号后紧跟非字母字符（避免 G1 匹配到 G10）
            m = re.match(r"^G(\d+)(?![\d])", node.value.strip())
            if m:
                found.add("G" + m.group(1))
    return found


def _codes_in_doc() -> set[str]:
    """文档里**闸门清单表格**登记的编号。

    ★ 不能全文扫：G34 在后面的详解章节里也会出现，
      全文扫会让「表格里漏登记」这种真实漂移测不出来（实测踩过）。
      只认以 `| G<n>` 开头的表格行——那是唯一的权威登记处。
    """
    codes: set[str] = set()
    for line in open(GATES_MD, encoding="utf-8", errors="replace"):
        m = re.match(r"^\|\s*G(\d+)\b", line)
        if m:
            codes.add("G" + m.group(1))
    return codes


def test_every_code_gate_is_documented():
    """代码里有、文档里没写的闸门 = 知识只活在代码里，换人会漏。"""
    codes = _codes_in_source()
    doc = _codes_in_doc()
    missing = sorted(codes - doc, key=lambda s: int(s[1:]))
    assert not missing, (
        "gates.py 里这些闸门没有写进 generation-gates.md：%s\n"
        "（规则只活在代码里，下次遇到同类问题没人知道已有闸门）" % missing)


def test_every_documented_gate_exists_in_code():
    """文档里写了、代码里没有的闸门 = 误导，会被当成已覆盖。"""
    codes = _codes_in_source()
    doc = _codes_in_doc()
    phantom = sorted(doc - codes, key=lambda s: int(s[1:]))
    assert not phantom, (
        "generation-gates.md 写了这些闸门但 gates.py 里没有：%s\n"
        "（文档说已拦，实际不拦，比没文档更危险）" % phantom)


def test_parser_actually_finds_gates():
    """自检：解析器必须真的找到一批闸门，否则上面两条是空断言。"""
    codes = _codes_in_source()
    assert len(codes) >= 30, (
        "只解析出 %d 个闸门，AST 提取口径可能失效了：%s"
        % (len(codes), sorted(codes, key=lambda s: int(s[1:]))))
    # 本轮新增的两条必须在，作为阳性样本
    assert "G34" in codes and "G35" in codes, "G34/G35 未解析到"


def test_capability_script_is_committed_not_in_attic():
    """能力表生成脚本必须在正式 scripts/，不能在收容区或缺失。

    本轮真实事故：json 进了仓库，生成脚本却留在 _attic_pending/ 当草稿，
    导致别人拿到 json 却无法复现 / 无法在实体变更后重扫。
    """
    script = os.path.join(REPO, "scripts", "entity_write_capability.py")
    assert os.path.exists(script), (
        "scripts/entity_write_capability.py 缺失 —— 能力表 json 无法复现")
    src = open(script, encoding="utf-8", errors="replace").read()
    # 必须有自检（无自检 = 口径错也静默出表）
    assert "self_check" in src, "脚本缺三档自检"
    assert "return 2" in src, "自检失败必须返回非零退出码"


def test_capability_table_and_gates_agree():
    """能力表里的实体名，必须能被 gates._ENTITY_CAPS 读到（路径没漂）。"""
    from components.udc.microflow import gates
    assert gates._ENTITY_CAPS is not None, (
        "gates 加载不到 entity-write-capability.json —— G34/G35 会静默失效")
    assert (gates._ENTITY_CAPS.get("entities") or {}), "能力表 entities 为空"
