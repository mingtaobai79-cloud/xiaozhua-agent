"""P3.1 循环作用域与循环项引用。

## 语料事实（526 个 FOR_EACH，不得推翻）

**循环项不是独立变量，就是 FOR_EACH 节点自己的出参**：

```json
// FOR_EACH 节点
"output": {"name": "_FOR_EACH_qNax8p", "dataType": "BIGINTEGER"/"DTO",
           "type": "OBJECT", "desc": "循环对象"}
"selectParam": {... 源列表 ...}      // 「选择列表」
"targetName": "循环对象"

// 循环体内引用循环项（37 条真实样本一致）
"value": {"type":"SelectParam","selectParam":{
    "outputName": "_FOR_EACH_qNax8p", "position": "parent",
    "nodeInfo": {"nodeId": "ForEach_Q2aynk", "type": "FOR_EACH"},
    "iconKey": "LinedCirculation"}}
```

所以「循环变量」这个概念在平台上是**出参名**：作用域 = 该节点及其所有后代。
不存在额外的 itemName/变量注册。

## 元素类型推导

FOR_EACH 出参类型 = 源列表的**元素**类型：

| 源列表出参 | dataType | type | FOR_EACH 出参 dataType |
|---|---|---|---|
| DTO 列表 | DTO | ARRAY | DTO（元素是 DTO） |
| BIGINTEGER 列表 | BIGINTEGER | ARRAY | BIGINTEGER |
| STRING 列表 | STRING | ARRAY | STRING |

字段路径 `item.id` 只在元素是 DTO 时合法（`401` 类错误：
对 BIGINTEGER 循环项取 `.id` → 平台无此字段）。

## 与 G20 的关系（不能破坏）

G20：写操作对象必须引用**活动节点**出参，不能直引控制节点（FOR_EACH / BRANCH）。
语料 103/103 写操作全是活动节点（RETRIEVE 95 / CREATE_VARIABLE 4 / FLOW 3 / BUSINESS 1），
0 例直引 FOR_EACH —— 直引会让平台生成 `int → Dto` 的代码，Java 编译失败。

**所以循环项引用不能"顺便"解决写操作对象**。正确链路恒定是：

```
FOR_EACH 当前项
   ↓  (只用于取 ID 之类的标量字段)
RETRIEVE(IDS, 当前项.id)      ← 活动节点承接
   ↓
CHANGE_ENTITY(引用 RETRIEVE 出参)
```

本模块**只**负责让「循环项字段引用」合法且类型正确，
并在有人试图把循环项当写操作对象时，由 G20 继续拦住。
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any


class ScopeError(ValueError):
    """循环作用域非法（越界引用 / 元素非 DTO / 字段不存在）。"""


# 元素类型 = DTO 时才有字段可引用
_DTO_TYPES = frozenset({"DTO"})


@dataclass
class LoopFrame:
    """一个循环作用域。

    alias: 逻辑图别名（如 "eachDs"）
    node_id: 平台 nodeId（ForEach_xxx）
    output_name: 出参名（_FOR_EACH_xxx）—— 这就是「循环项」的引用名
    elem_type: 元素 dataType（DTO / BIGINTEGER / STRING ...）
    elem_dto: 元素是 DTO 时的 DTO 全名
    elem_fields: {字段名: 元数据}（仅 DTO）
    """
    alias: str
    node_id: str
    output_name: str
    elem_type: str = "STRING"
    elem_dto: str = ""
    elem_fields: dict = dc_field(default_factory=dict)
    caption: str = ""

    @property
    def is_dto(self) -> bool:
        return self.elem_type in _DTO_TYPES

    def field_meta(self, field: str) -> dict:
        if not self.is_dto:
            raise ScopeError(
                "循环 %r 的元素类型是 %s（不是 DTO），不能取字段 %r —— "
                "只有元素是对象时才有字段" % (self.alias, self.elem_type, field))
        fm = self.elem_fields.get(field)
        if fm is None:
            raise ScopeError("循环 %r 的元素类型 %s 没有字段 %r（可用：%s）"
                             % (self.alias, self.elem_dto or self.elem_type, field,
                                sorted(self.elem_fields)[:12]))
        return fm


class LoopScopeStack:
    """嵌套循环的作用域栈。

    ★ 隔离规则（不能妥协）：
      - 内层可见外层（可以引用外层循环项），但外层**不可见**内层
      - 同名 alias 禁止（会产生歧义：到底指哪一层）
      - 退出循环即弹出，循环外引用直接 ScopeError
    """

    def __init__(self):
        self._stack: list[LoopFrame] = []

    # ---------------- 进出 ----------------
    def push(self, frame: LoopFrame) -> None:
        if any(f.alias == frame.alias for f in self._stack):
            raise ScopeError("循环别名 %r 在外层作用域已存在（嵌套循环必须用不同别名）"
                             % frame.alias)
        self._stack.append(frame)

    def pop(self) -> LoopFrame:
        if not self._stack:
            raise ScopeError("循环作用域栈为空，不能 pop")
        return self._stack.pop()

    def __len__(self) -> int:
        return len(self._stack)

    def depth(self) -> int:
        return len(self._stack)

    def current(self) -> LoopFrame | None:
        return self._stack[-1] if self._stack else None

    # ---------------- 查找 ----------------
    def find(self, alias: str) -> LoopFrame | None:
        """就近查找（内层优先；同名已被 push 拦住，所以不会歧义）。"""
        for f in reversed(self._stack):
            if f.alias == alias:
                return f
        return None

    def require(self, alias: str) -> LoopFrame:
        f = self.find(alias)
        if f is None:
            raise ScopeError(
                "循环变量 %r 不在当前作用域（当前：%s）—— "
                "循环外引用、或引用了未声明的循环项"
                % (alias, [x.alias for x in self._stack] or "（无，不在任何循环内）"))
        return f

    def aliases(self) -> list[str]:
        return [f.alias for f in self._stack]


# ---------------------------------------------------------------- 元素类型推导
def loop_frame_from(list_output: dict, list_structure: dict | None, *,
                    alias: str, node_id: str, output_name: str,
                    caption: str = "") -> LoopFrame:
    """由源列表的出参推导循环项（元素）类型。

    ★ 元素类型 = 列表出参的 dataType，但 `type` 会从 ARRAY 变 OBJECT
      （循环项是单个元素，不是列表）。这里只取类型，不改节点。
    """
    o = list_output or {}
    st = list_structure or {}
    dt = str(o.get("dataType") or "STRING").upper()
    if dt == "DTO":
        dto = st.get("id") or o.get("id") or ""
        return LoopFrame(alias=alias, node_id=node_id, output_name=output_name,
                         elem_type="DTO", elem_dto=dto,
                         elem_fields=dict(st.get("attributes") or {}),
                         caption=caption)
    return LoopFrame(alias=alias, node_id=node_id, output_name=output_name,
                     elem_type=dt, elem_dto="", elem_fields={}, caption=caption)


def parse_loop_item_ref(spec: Any) -> tuple[str, str | None]:
    """解析 DSL 里的循环项引用形态。

    支持三种写法（都归一成 (alias, field)）：
      {"item": "eachDs"}                      → ("eachDs", None)         整项
      {"item": "eachDs", "field": "id"}       → ("eachDs", "id")
      {"field": {"source": "eachDs", "path": "id"}}  → ("eachDs", "id")

    ★ 不认 `{"field": "eachDs.id"}`：普通节点引用也是这个形状，
      靠后缀猜会与真实节点别名冲突（例如有个别名就叫 eachDs.id 的节点）。
      循环项必须显式写 `item`，宁可啰嗦一点。
    """
    if not isinstance(spec, dict):
        raise ScopeError("循环项引用必须是对象，得到 %r" % type(spec).__name__)
    if "item" in spec:
        alias = spec["item"]
        if not isinstance(alias, str) or not alias:
            raise ScopeError("item 必须是非空字符串，得到 %r" % (alias,))
        field = spec.get("field")
        return alias, (field or None)
    f = spec.get("field")
    if isinstance(f, dict) and "source" in f:
        return f["source"], (f.get("path") or None)
    raise ScopeError("无法识别循环项引用：%r（用 {\"item\":\"<别名>\", \"field\":\"<字段>\"} "
                     "或 {\"field\":{\"source\":\"<别名>\",\"path\":\"<字段>\"}}）"
                     % (spec,))


def is_loop_item_ref(spec: Any) -> bool:
    """是否循环项引用（供 DSL 分派用）。"""
    if not isinstance(spec, dict):
        return False
    if "item" in spec:
        return True
    f = spec.get("field")
    return isinstance(f, dict) and "source" in f
