"""变量与 schema 的绑定 —— FORMULA_6058 的唯一正解。

★★ 2026-10-23 重大更正：`schemas` 必须是**实体 OBJECT 树**，且 token.value 必须
   **带实体前缀的点路径**。早期版本用「扁平字段节点 + 短名」能过 check/transform，
   但生成的 designData 是扁平的，**页面回显直接报 FORMULA_6058**：

       变量:整数字段 在上下文中不存在，请确认!

   三维对照实验（test2，实体 ysFullEntity / 字段 f03int，表达式 `f03int + f03int`）
   ---------------------------------------------------------------------------
   组合                          check        transform 产物            页面
   A 扁平字段节点 + value=f03int  BOOT_0000    context 扁平/type=INTEGER   报错
   B 实体树     + value=f03int    FORMULA_6058 ——                          -
   C 实体树     + value=实体.字段  BOOT_0000    context OBJECT 树/点路径    正常

   ⇒ 只有 C 是对的。B 的报错文案与页面报错**一字不差**，说明页面回显走的是
     「树 + 点路径」这条解析通路。

   客户真实配置也印证 C：`context=[{name:"税率配置表", type:"OBJECT",
   properties:[{name:"shuilv", ...}]}]`，`tokens[].value="shuilvpeizhibiao.shuilv"`，
   `desc="税率配置表.税率"`，并带 `controlData/subOps/g_l_index`。

★ 教训：**check/transform 通过 + DB 回读正确 ≠ 功能可用。**
  这三步都过，页面照样报错。验收必须看页面渲染。

历史（仍然成立的部分）
----------------------
`ExpressionSaveDto.schemas` 里没有字段节点时，`VariableCheckFilter` 报 FORMULA_6058
—— 它是拿 token 去 **schemas 树**里找，不是拿 paramId 去库里查。
系统变量不需要 schemas：SYSTEM 走 `ExpressionPresetRunner.loadSystemVariable` 全局表。
"""
from __future__ import annotations

from .token import TOKEN_TYPE_FUNCTION, TOKEN_TYPE_VARIABLE

# 精简节点需要的键。★ properties 必须保留，否则实体树退化成扁平节点。
MINIMAL_SCHEMA_KEYS: tuple[str, ...] = (
    "name", "description", "type", "selectable", "uniformityParams",
)
TREE_SCHEMA_KEYS: tuple[str, ...] = MINIMAL_SCHEMA_KEYS + ("enableDataI18n", "properties")

ENTITY_CATEGORY = "Entity"
ATTR_CATEGORY = "Attr"


def iter_tokens(tokens, _depth: int = 0):
    """深度遍历 token 树（展开 FUNCTION.subOps）。"""
    if _depth > 12:
        return
    for t in tokens or []:
        if not isinstance(t, dict):
            continue
        yield t
        if t.get("type") == TOKEN_TYPE_FUNCTION:
            for group in (t.get("subOps") or []):
                for sub in iter_tokens(group, _depth + 1):
                    yield sub


def variable_tokens(tokens) -> list[dict]:
    """所有 VARIABLE token（含函数参数里的）。"""
    return [t for t in iter_tokens(tokens) if t.get("type") == TOKEN_TYPE_VARIABLE]


def required_param_ids(tokens) -> tuple[str, ...]:
    """本次表达式需要绑定的 paramId 集合（按出现顺序去重）。"""
    seen, out = set(), []
    for t in variable_tokens(tokens):
        pid = str(t.get("paramId") or "")
        if pid and pid not in seen:
            seen.add(pid)
            out.append(pid)
    return tuple(out)


def _walk(nodes, depth=0, root=None, acc=None):
    """把 schema 树摊平成 paramId → (节点, 所属实体根)。"""
    if acc is None:
        acc = {}
    if depth > 12:
        return acc
    for n in nodes or []:
        if not isinstance(n, dict):
            continue
        up = n.get("uniformityParams") or {}
        pid = up.get("paramId")
        cat = up.get("paramCategory")
        this_root = n if cat == ENTITY_CATEGORY else (root or n)
        if pid is not None:
            acc.setdefault(str(pid), (n, this_root))
        kids = n.get("children") or n.get("properties") or []
        _walk(kids, depth + 1, this_root, acc)
    return acc


def _index_nodes(nodes, depth=0, acc=None):
    """兼容旧接口：paramId → 节点（丢父子关系）。"""
    if acc is None:
        acc = {}
    if depth > 12:
        return acc
    for n in nodes or []:
        up = n.get("uniformityParams") or {}
        pid = up.get("paramId")
        if pid is not None:
            acc.setdefault(str(pid), n)
        kids = n.get("children") or n.get("properties") or []
        _index_nodes(kids, depth + 1, acc)
    return acc


def minimal_node(node: dict) -> dict:
    """抽出最小可绑定节点（扁平形态，仅用于旧通路 / 校验）。"""
    out = {}
    for k in MINIMAL_SCHEMA_KEYS:
        if k in node:
            out[k] = node[k]
    if "uniformityParams" not in out:
        raise ValueError("节点缺 uniformityParams，无法绑定：%r" % node.get("name"))
    return out


def tree_node(node: dict, properties: list | None = None) -> dict:
    """实体根节点：保留 properties（这才是变量能被子节点引用的前提）。"""
    out = {k: node[k] for k in TREE_SCHEMA_KEYS if k in node}
    out.pop("properties", None)
    if "uniformityParams" not in out:
        raise ValueError("实体节点缺 uniformityParams：%r" % node.get("name"))
    out.setdefault("type", "OBJECT")
    out.setdefault("selectable", True)
    out["properties"] = properties or []
    return out


def bind_schemas(tokens, schema_nodes, *, minimal: bool = True,
                 as_tree: bool = True) -> list[dict]:
    """按 tokens 里用到的变量，从 schema 树里取出要绑定的节点。

    as_tree=True（默认，2026-10-23 起）：返回**按实体分组的 OBJECT 树**，
      只有这种形态能让 transform 生成点路径 token、页面才能回显。
    as_tree=False：返回扁平字段节点（旧行为，页面会报 FORMULA_6058，
      仅保留给"只要 check 通过"的兼容场景）。

    缺任何一个变量的节点都抛错 —— 不要静默放过（放过就是 FORMULA_6058）。
    """
    index = _walk(schema_nodes)
    needed = required_param_ids(tokens)
    missing = [p for p in needed if p not in index]
    if missing:
        raise ValueError(
            "这些 paramId 在 schema 树里找不到节点：%s。"
            "变量必须能对应到一个具体字段节点（实体根节点不能替代）" % ", ".join(missing)
        )

    if not as_tree:
        out = []
        for pid in needed:
            node = index[pid][0]
            out.append(minimal_node(node) if minimal else node)
        return out

    groups: dict[int, tuple[dict, list]] = {}
    order: list[int] = []
    for pid in needed:
        node, root = index[pid]
        key = id(root)
        if key not in groups:
            groups[key] = (root, [])
            order.append(key)
        groups[key][1].append(node)

    out = []
    for key in order:
        root, fields = groups[key]
        kids = [minimal_node(f) if minimal else dict(f) for f in fields]
        out.append(tree_node(root, kids))
    return out


def entity_of(node: dict) -> str | None:
    """从实体根节点取 name（拼点路径用）。"""
    up = node.get("uniformityParams") or {}
    return node.get("name") if up.get("paramCategory") == ENTITY_CATEGORY else None


def check_binding(tokens, schemas) -> list[str]:
    """校验 schemas 是否覆盖了所有变量。返回错误列表，空 = 通过。"""
    errs = []
    have = set()
    for n in _index_nodes(schemas).values():
        up = n.get("uniformityParams") or {}
        if up.get("paramId") is not None:
            have.add(str(up["paramId"]))
    for pid in required_param_ids(tokens):
        if pid not in have:
            errs.append(
                "paramId=%s 的变量已在 token 中使用，但 schemas 里没有它的节点"
                "（会报 FORMULA_6058）" % pid
            )
    # 树形态检查：有 VARIABLE 时 schemas 必须是 OBJECT 树，且 token 必须是点路径
    if variable_tokens(tokens) and schemas:
        if not any((s.get("type") == "OBJECT" and s.get("properties"))
                   for s in schemas if isinstance(s, dict)):
            errs.append(
                "schemas 里没有 OBJECT 树节点 —— 扁平字段节点会让页面回显报 "
                "FORMULA_6058（check/transform 却会通过，属假绿）")
    for t in variable_tokens(tokens):
        v = str(t.get("value") or "")
        if schemas and "." not in v:
            errs.append(
                "token.value=%r 缺实体前缀 —— 树形态下必须是 '实体.字段'，"
                "否则页面报「变量:xxx 在上下文中不存在」" % v)
    return errs
