"""P2-3 数据引用解析器：把「业务意图」翻译成表达式 AST 可用的引用描述。

两条路径严格分开：

**静态路径**（本地推导，零接口）
    前序节点出参 → 逻辑图查找 → 该出参的 structure/entity 元数据 → 字段描述
    用于：引用自己在本次生成流程里创建的节点（最常见）

**动态路径**（按需接口 + 缓存）
    用户变量 / 实体属性 / 设置项 → LiveRefs 查询 → 最新元数据
    用于：引用流程外的平台对象（实体字段、子流程、生单规则…）

★ 缓存必须带应用范围（app_id），不能跨应用串数据 —— 不同应用可能有
  同名实体/同名字段但 id 完全不同，串了会生成指向错误 DTO 的表达式，
  而平台 check 仍可能通过（结构合法但语义错）。

★ 前序节点顺序裁决：表达式只能引用**在当前节点之前**已执行的节点出参。
  引用后序节点平台 check 会过（context 里给了就行），但运行期取不到值 ——
  这是"check 绿、跑起来空"的经典来源，必须在解析阶段就拦。
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any

from .expression_model import Expr, NodeField, SysVar


class ReferenceError_(ValueError):
    """引用解析失败（找不到/顺序非法/类型缺失）。"""


@dataclass
class ReferenceResolver:
    """逻辑图 + 元数据查询的统一入口。

    app_id / app_name 是缓存与查询的边界（跨应用串数据是本类的头号禁忌）。
    live_refs 可为 None（纯静态场景，比如单测）。
    """

    app_id: str
    app_name: str
    live_refs: Any = None
    _dto_cache: dict = dc_field(default_factory=dict)      # key: (app_id, entity_label)

    # ------------------------------------------------------------------ 逻辑图
    @staticmethod
    def ordered_nodes(nodes: list[dict]) -> list[dict]:
        """按执行顺序展开节点（含 BRANCH/FOR 子节点），子节点跟随宿主顺序。"""
        out: list[dict] = []

        def walk(seq):
            for n in seq or []:
                if not isinstance(n, dict):
                    continue
                out.append(n)
                # BRANCH 各分支
                for c in n.get("conditions") or []:
                    walk(c.get("nodes"))
                walk(n.get("nodes"))

        walk(nodes)
        return out

    def index_before(self, nodes: list[dict], before_node_id: str) -> dict:
        """返回 {outputName: node}，只含 before_node_id 之前（含嵌套位置）的节点。

        ★ 顺序语义：BRANCH 内某个分支的节点，只能引用「到它为止已执行」的节点。
        这里用扁平顺序近似（与平台编辑器顺序一致）；严格分支隔离由 G 闸门兜。
        """
        idx = None
        ordered = self.ordered_nodes(nodes)
        for i, n in enumerate(ordered):
            if n.get("nodeId") == before_node_id:
                idx = i
                break
        if idx is None:
            raise ReferenceError_("节点 %r 不在流程里" % before_node_id)
        avail = {}
        for n in ordered[:idx]:
            o = (n.get("output") or {})
            name = o.get("name")
            if name:
                avail[name] = n
        return avail

    # ------------------------------------------------------------------ 静态路径
    def field_ref_from_node(self, node: dict, field: str,
                            alias: str | None = None) -> NodeField:
        """前序节点出参字段引用（本地推导，不查接口）。

        node 需要 output.name 与 structure（entity/DTO 标识）。
        字段元数据优先取 node 自带的（构造器造节点时已写入 selectParam/attrs），
        缺失时才走动态路径兜底。
        """
        o = node.get("output") or {}
        name = o.get("name")
        if not name:
            raise ReferenceError_("节点 %r 没有 output.name，无法引用" % node.get("nodeId"))
        dto_id = (node.get("structure") or {}).get("id") or o.get("id") or ""
        fm = self._field_meta(node, field)
        if fm is None:
            # 兜底：按结构的实体查一次（带缓存）
            fm = self._lookup_field(node, field)
        ref = {
            "outputName": name,
            "field": field,
            "title": node.get("title") or node.get("caption") or name,
            "dto_id": dto_id,
            "is_array": o.get("type") == "ARRAY",
            "fields": {field: fm},
        }
        if alias:
            ref["title"] = alias
        dt = fm.get("dataType") or "STRING"
        return NodeField(ref, dtype=_normalize_type(dt))

    def _field_meta(self, node: dict, field: str) -> dict | None:
        """从节点自身携带的元数据里找字段（attrs/selectParam/output.properties）。"""
        # ★ BASIC 型变量/列表：字段就是它自己的值槽，没有实体结构。
        #   ⚠ 判据只能是 paramType == "BASIC"：
        #   早期版本还加了「有 dataType 且 structure 无 entityId」这一条，
        #   结果 RETRIEVE 节点（dataType 在 output 里、structure 只有 id/caption）
        #   被误判成 BASIC，返回 id=字段名（如 "数据源配置信息_1"），
        #   生成 context 时子节点名变成实体 caption → 平台报
        #   FORMULA_6058 "xxx.jdbcUrl does not exist in context"。
        if node.get("paramType") == "BASIC":
            title = node.get("title") or node.get("name")
            if field in (title, node.get("name")) and node.get("dataType"):
                return {"dataType": node["dataType"],
                        "id": field,
                        "caption": title or field}

        def scan(obj, depth=0):
            if depth > 8 or obj is None:
                return None
            if isinstance(obj, dict):
                # selectParam / customs 形态
                for key in ("selectParam",):
                    sp = obj.get(key)
                    if isinstance(sp, dict) and sp.get("name") == field:
                        return {"dataType": sp.get("dataType"),
                                "id": sp.get("id") or field,
                                "caption": sp.get("description") or sp.get("desc") or field}
                if obj.get("name") == field and obj.get("dataType"):
                    return {"dataType": obj["dataType"],
                            "id": obj.get("id") or field,
                            "caption": obj.get("caption") or obj.get("desc") or field}
                for v in obj.values():
                    r = scan(v, depth + 1)
                    if r:
                        return r
            elif isinstance(obj, list):
                for v in obj:
                    r = scan(v, depth + 1)
                    if r:
                        return r
            return None
        return scan(node)

    def _lookup_field(self, node: dict, field: str) -> dict:
        """动态兜底：按结构实体查全量属性（带 app 范围缓存）。

        ★ 有些节点没有 `structure`，但出参本身带 DTO 全名（如 LIST_OPERATION 的
          FIRST_ONE/LAST_ONE/PICK_ONE：真实 654 条样本里元素出参的 `output.id` 就是
          DTO 全名）。这种情况按 DTO 反查实体模型，否则「取元素后读字段」永远解析不了。
        """
        ent = node.get("structure") or {}
        label = ent.get("caption") or ent.get("id") or ""
        if not label:
            o = node.get("output") or {}
            dto = o.get("id") or o.get("javaType") or ""
            if dto:
                em = self.entity_model(dto)   # entity_model 同时接受实体标题与 DTO 全名
                attrs = em.get("attributes") or {}
                if field in attrs:
                    a = attrs[field]
                    return {"dataType": a.get("dataType") or "STRING",
                            "id": a.get("id") or field,
                            "caption": a.get("caption") or field}
                label = dto
        if not label:
            raise ReferenceError_("节点 %r 缺 structure，无法解析字段 %r"
                                  % (node.get("nodeId"), field))
        em = self.entity_model(label)
        attrs = em.get("attributes") or {}
        if field not in attrs:
            raise ReferenceError_("实体 %r 没有字段 %r（可选：%s）"
                                  % (label, field, list(attrs)[:8]))
        a = attrs[field]
        return {"dataType": a.get("dataType") or "STRING",
                "id": a.get("id") or field,
                "caption": a.get("caption") or field}

    # ------------------------------------------------------------------ 动态路径
    def entity_model(self, label: str) -> dict:
        """实体模型（带缓存，key 含 app_id）。"""
        key = (self.app_id, label)
        if key in self._dto_cache:
            return self._dto_cache[key]
        if self.live_refs is None:
            raise ReferenceError_("无 live_refs，无法查询实体 %r" % label)
        # label 可能是实体标题，也可能是 DTO 全名（节点 structure.id）
        if "." in label:
            em = self.live_refs.entity_model(self.app_id, self.app_name, dto_full=label)
        else:
            em = self.live_refs.entity_model(self.app_id, self.app_name, label=label)
        self._dto_cache[key] = em
        return em

    def sysvar(self, name: str, dtype: str) -> SysVar:
        """系统变量引用（全名，131 项目录见 facts/udc/expression/system-variables.md）。"""
        if not name:
            raise ReferenceError_("系统变量名不能为空")
        return SysVar(name, dtype=_normalize_type(dtype))

    # ------------------------------------------------------------------ 便捷
    def ref_from_output_name(self, nodes: list[dict], output_name: str, field: str,
                             before_node_id: str) -> NodeField:
        """按 outputName 找节点并造字段引用，同时校验顺序合法性。"""
        avail = self.index_before(nodes, before_node_id)
        node = avail.get(output_name)
        if node is None:
            raise ReferenceError_(
                "outputName=%r 引用非法：不在 %r 之前已执行节点内（可用：%s）"
                % (output_name, before_node_id, list(avail)[:8]))
        return self.field_ref_from_node(node, field)

    # ------------------------------------------------------------------ 逻辑图执行期
    def bind_scope(self, scope) -> None:
        """绑定执行作用域（逻辑图执行器注入），供 find_executed 判定「已执行」。"""
        self._scope = scope

    def find_executed(self, alias: str) -> dict | None:
        """按逻辑图别名找已执行节点（执行器每建一个节点就 register_alias）。"""
        return (getattr(self, "_aliases", None) or {}).get(alias)

    def register_alias(self, alias: str, node: dict) -> None:
        if not hasattr(self, "_aliases"):
            self._aliases = {}
        self._aliases[alias] = node

    def bind_flow_input(self, output: dict | None, fields: dict | None = None) -> None:
        """绑定流程入参声明（trigger.output 形态 + 实体字段表）。"""
        if not output:
            self._flow_input = None
            return
        self._flow_input = {"name": output.get("name"),
                            "title": output.get("desc") or "入参",
                            "dto_id": output.get("id") or "",
                            "fields": fields or {}}

    def input_ref(self, field: str | None = None, dtype: str = "STRING") -> NodeField:
        """流程入参引用（MANUAL 的 trigger.output）。"""
        inp = getattr(self, "_flow_input", None)
        if not inp:
            raise ReferenceError_(
                "本流程没有入参（trigger.paramType=NONE）；引用入参字段 %r 非法" % field)
        name = inp.get("name")
        fname = field or name
        meta = (inp.get("fields") or {}).get(fname) or {}
        dt = _normalize_type(meta.get("dataType") or dtype)
        ref = {"outputName": name, "title": inp.get("title") or "入参",
               "field": fname, "dto_id": inp.get("dto_id") or "",
               "fields": {fname: {"dataType": dt,
                                  "id": meta.get("id") or fname,
                                  "caption": meta.get("caption") or fname}}}
        return NodeField(ref, dtype=dt)


_TYPES = {"String": "STRING", "Integer": "INTEGER", "Long": "BIGINTEGER",
          "Boolean": "BOOLEAN", "BigDecimal": "DECIMAL", "Double": "DOUBLE",
          "Date": "DATE", "Time": "TIME"}


def _normalize_type(dt: str) -> str:
    """dataType 归一（平台保存态大写、回读态首字母大写两种都要认）。"""
    if not dt:
        return "STRING"
    up = str(dt).upper()
    return _TYPES.get(str(dt), up)
