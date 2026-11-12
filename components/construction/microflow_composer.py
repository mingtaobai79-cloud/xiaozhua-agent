"""微流程组装器 —— 用构造器 + 活引用组装完整 schema，不再手拼节点。

设计动机（实测得出）：
    构造器 22/22 契约合规 ≠ 构造器能用。
    scratch/rebuild_v3.py 里 19 个节点全是手拼 dict，从没用过构造器，
    所以「构造器合规」和「能发布」是两条从没接上的链。
    本模块就是那条接上的链。

三条铁律（照抄测试出来的结论，不是设计偏好）：
  1. **只走构造器**：每个节点的字段形态由 components/construction 的构造器决定，
     组装器只负责编排顺序和引用关系，不自己拼字段。
  2. **外部引用全活取**：实体/子流程/服务一律经 LiveRefs，
     组装器只接受「标签/名字」，不接受 id。查不到即抛（G7）。
  3. **出门前过闸门**：finish() 里跑 G1-G12 + 契约闸门，不合规直接抛，
     绝不产出可发布的违规 schema。

用法：
    from components.udc.microflow.live_refs import LiveRefs
    from components.construction.node_builder import NodeBuilder
    from components.construction.microflow_composer import MicroflowComposer

    comp = MicroflowComposer(builder, refs, app_id=APP, app_name=APP_NAME)
    comp.step("CREATE_VARIABLE", alias="vText", title="vText",
              data_type="STRING", value="PAY-1")
    comp.step("RETRIEVE", alias="r1", entity="小爪验收实体全量",
              cond_field="f01text", right="k")
    comp.step("CHANGE_VARIABLE", alias="m1", target="vText", from_node="r1")
    schema = comp.finish(end_from="vText")
"""
from __future__ import annotations

from typing import Any

from .microflow_fields import constant, entity_structure, field_attr, simple
from .node_builder import NodeBuilder

# ★ 常量字面量有两个语境，不能混用（实测 643 条生产流程）：
#   - 查询条件 `condition[].conditions[].rightParams[]`
#       → `constant()` = {"type": "CONSTANT", "value": ...}   （大写，193 次）
#   - 值槽位 `value` / `attrs[].value` / `entries[].value`
#       → `simple()`   = {"type": "Simple", "simple": ..., "desc": ...}  （322 次）
#   把 constant() 用到值槽位 → checkSchema 报
#   `value.type DATA_INVALID`（组装路径实测踩过）。
#   `CONSTANT` 在 value 槽位里**出现 0 次**，不是可选写法，是错的。


def _has_out_param(trg: dict | None) -> bool:
    """MANUAL/事件 trigger 是否声明了对外出参（paramType 非 NONE 且 type 为 MANUAL）。"""
    if not isinstance(trg, dict):
        return False
    return (trg.get("type") == "MANUAL"
            and trg.get("paramType") not in (None, "", "NONE"))


def _is_nodeless(trg: dict | None) -> bool:
    """定时/事件任务允许无节点链（CUSTOM 型），但 SERVICE 型必须有节点。"""
    return isinstance(trg, dict) and trg.get("type") in ("SCHEDULE", "BUSINESS_EVENT")


def _rid6() -> str:
    import random as _r
    import string as _s
    return "".join(_r.choices(_s.ascii_letters + _s.digits, k=6))


def _val(v):
    """值槽位（value / attrs[].value / entries[].value）的常量：必须 Simple。"""
    if isinstance(v, dict):
        return v
    return simple(v)


def _cond_val(v):
    """查询条件 rightParams 的常量：必须 CONSTANT。"""
    if isinstance(v, dict):
        return v
    return constant(v)
from . import microflow_nodes_v2 as V2
from . import microflow_nodes_extra as X
from . import microflow_nodes_svc as S
from .microflow_fields import field_attr


class ComposeError(RuntimeError):
    """组装失败。任何一条都是「不许生成」，不做降级。"""


class MicroflowComposer:
    def __init__(self, builder: NodeBuilder, refs, *, app_id: str, app_name: str):
        self.b = builder
        self.refs = refs
        self.app_id = str(app_id)
        self.app_name = app_name
        self.nodes: list[dict] = []
        self.by_alias: dict[str, dict] = {}
        self._entities: dict[str, dict] = {}

    # ---------------- 外部引用：全部活取 ----------------
    def entity(self, label: str = "", dto_full: str = "") -> dict:
        """按标签取实体模型（含属性表）。查不到抛 ComposeError。"""
        key = label or dto_full
        if key in self._entities:
            return self._entities[key]
        if self.refs is None:
            raise ComposeError("需要实体 %r 但没有 LiveRefs（禁止写死）" % key)
        try:
            m = self.refs.entity_model(self.app_id, self.app_name,
                                       label=label, dto_full=dto_full)
        except LookupError as e:
            raise ComposeError("实体活引用失败: %s" % e)
        if not m.get("attributes"):
            raise ComposeError("实体 %r 属性表为空，无法生成字段引用" % key)
        self._entities[key] = m
        return m

    def _node(self, alias: str) -> dict:
        if alias not in self.by_alias:
            raise ComposeError("引用不存在的节点别名 %r（可用：%s）"
                               % (alias, sorted(self.by_alias)))
        return self.by_alias[alias]

    def _add(self, node: dict, alias: str) -> dict:
        if alias in self.by_alias:
            raise ComposeError("别名重复: %r" % alias)
        node = node[0] if isinstance(node, list) else node
        self.nodes.append(node)
        self.by_alias[alias] = node
        return node

    # ---------------- 节点步骤 ----------------
    def step(self, kind: str, alias: str, **kw) -> dict:
        """按 kind 分派到对应构造器。所有外部引用都用标签/别名传，不传 id。"""
        handler = getattr(self, "_st_" + kind.lower(), None)
        if handler is None:
            raise ComposeError("组装器未支持节点类型 %r（先在 _st_%s 实现）"
                               % (kind, kind.lower()))
        # ★ 别名即稳定 id 种子：同一张逻辑图重复 compose，nodeId / 出参名完全一致。
        #   否则每次重发都换一遍节点 id，设计器会报「所选 xxx 已变更」，
        #   页面规则等外部引用也会断链（2026-11-02 实测）。
        if not hasattr(self.b, "_new_id"):
            return handler(alias, **kw)
        prev = getattr(self.b, "node_key", None)
        self.b.node_key = alias
        try:
            return handler(alias, **kw)
        finally:
            self.b.node_key = prev

    # -- 变量 --
    def _st_create_variable(self, alias, *, title, data_type="STRING",
                            value=None, caption="创建变量",
                            entity=None, other_type=None, fields=None, **_) -> dict:
        """创建变量。entity=标签 → 实体型；other_type="SYSTEM_PAGE_INFO" → 分页对象；
        否则基本类型。fields={字段名:值} 仅在 entity 形态下生效（走 attrs 字段映射），
        用来造一个**尚未落库（无 id）**的实体对象。"""
        if entity:
            m = self.entity(entity)
            pairs = self._field_pairs(m, fields, entity) if fields else None
            attrs = None
            if pairs:
                # ★ create_variable 的 attrs 要 [{attrType, value}]，
                #   而 _field_pairs 返回的是 [(字段名, 值字典)]（create_entity 用）。
                #   直接把 tuple 塞进去会让闸门崩：'tuple' object has no attribute 'get'。
                attrs = [{"attrType": field_attr(m, fname, sort=i), "value": val}
                         for i, (fname, val) in enumerate(pairs)]
            return self._add(V2.create_variable(self.b, title, caption=caption,
                                                entity=m, attrs=attrs), alias)
        if other_type:
            return self._add(V2.create_variable(self.b, title, caption=caption,
                                                other_type=other_type), alias)
        return self._add(V2.create_variable(self.b, title, data_type, _val(value),
                                            caption=caption), alias)

    def _st_change_variable(self, alias, *, target, value=None, from_node=None,
                            field="", caption="修改变量", set_fields=None,
                            entity=None, **_) -> dict:
        """修改变量。set_fields={字段名:值} 走字段级映射（335 次真实用法），
        否则整体赋值（717 次）。"""
        tgt = self._node(target)
        if set_fields:
            if not entity:
                raise ComposeError("字段级映射（set_fields）必须同时给 entity 标签")
            m = self.entity(entity)
            pairs = {k: (v if isinstance(v, dict) else _val(v))
                     for k, v in set_fields.items()}
            return self._add(V2.change_variable(self.b, tgt, caption=caption,
                                                field_values=pairs,
                                                entity_model=m), alias)
        if from_node:
            # 取值来自前序节点字段（真实引用，不是常量）
            ref = self.refs_field(self._node(from_node), field) if field else None
            if ref is None:
                ref = self._out_ref(self._node(from_node))
            return self._add(V2.change_variable(self.b, tgt, ref, caption=caption), alias)
        return self._add(V2.change_variable(self.b, tgt, _val(value),
                                            caption=caption), alias)

    # -- 列表 --
    def _st_create_list(self, alias, *, title, data_type="STRING",
                        default_value=None, caption="创建列表", **_) -> dict:
        return self._add(X.create_list(self.b, title, data_type,
                                       caption=caption,
                                       default_value=default_value), alias)

    def _st_change_list(self, alias, *, list_node, from_node=None, action="ADD",
                        count_attrs=None, count_fields=None,
                        caption="修改变量(列表)", **_) -> dict:
        act = (action or "ADD").upper()
        src = self._node(from_node) if from_node else None
        if count_fields:
            from .microflow_fields import field_attr
            dto = ((src or {}).get("output") or {}).get("id") or ""
            m = self.entity(dto_full=dto)
            count_attrs = [field_attr(m, f) for f in count_fields]
        if act == "REMOVE" and not count_attrs:
            # 真实 8 条 REMOVE 样本的 countAttrs 就是元素 DTO 的 id 字段
            dto = ((src or {}).get("output") or {}).get("id") or ""
            if not dto:
                raise ComposeError("CHANGE_LIST REMOVE 需要元素 DTO（from_node 出参 id）")
            m = self.entity(dto_full=dto)
            a = (m.get("attributes") or {}).get("id") or {}
            count_attrs = [{
                "id": dto + ".id", "fullName": dto + ".id", "name": "id",
                "javaType": a.get("javaType") or "java.lang.Long",
                "dataType": a.get("dataType") or "BIGINTEGER",
                "type": "OBJECT", "desc": a.get("caption") or "ID",
                "relationApp": self.app_name, "refApp": self.app_name,
                "multiSelect": False, "dtoType": "CUSTOM",
                "label": (a.get("caption") or "ID"),
            }]
        return self._add(X.change_list(self.b, self._node(list_node), src,
                                       action=act, caption=caption,
                                       count_attrs=count_attrs), alias)

    def _st_create_list_entity(self, alias, *, entity, title=None,
                               caption="创建列表", **_) -> dict:
        """创建「实体对象列表」（空列表 paramType=ENTITY_OBJECT + value=[]）。
        与 create_list 的区别：元素是实体对象，可被 CREATE_BATCH_ENTITY 直接消费。"""
        m = self.entity(entity)
        return self._add(X.create_list_entity(self.b, m,
                                              title or (m["caption"] + "列表"),
                                              caption=caption), alias)

    def _st_change_list_add(self, alias, *, list_node, item,
                            caption="列表添加元素", **_) -> dict:
        """往实体对象列表追加一个元素（action=ADD）。
        这是「造无 id 新对象列表」的唯一路径：CREATE_VARIABLE 造对象 → 本节点入列表。"""
        return self._add(X.change_list_add(self.b, self._node(list_node),
                                           self._node(item), caption=caption), alias)

    def _filter_expression(self, list_node: dict, spec: dict | None):
        """过滤条件：按字段 + 操作符 + 常量，编译成平台 expression。

        平台 check/transform 对含「过滤条件」字段引用的表达式**完全可用**
        （实测 executableExpr 与设计器逐字节一致），不需要进设计器点确定。
        """
        from .microflow_filter import (build_filter_expression, build_ast_expression,
                                       parse_filter_spec)
        from components.udc.microflow.expression_transport import CurlBackend
        if not isinstance(spec, dict) or not (spec.get("field") or spec.get("expr")):
            raise ComposeError("FILTER 需要 filter={field,op,right} 或 filter={expr:{...}}")
        if self.refs is None:
            raise ComposeError("FILTER 需要 LiveRefs（拿实体属性与平台编译）")
        dto = (list_node.get("output") or {}).get("id") or ""
        if not dto:
            raise ComposeError("FILTER 的上游列表没有 DTO 信息")
        m = self.entity(dto_full=dto)
        if spec.get("expr"):
            # 任意布尔表达式（算术/函数/逻辑组合）
            ast = parse_filter_spec(spec["expr"], dto_full=dto,
                                    list_desc=list_node.get("caption") or "列表",
                                    entity_model=m)
            return build_ast_expression(
                dto_full=dto, list_desc=list_node.get("caption") or "列表",
                entity_model=m, ast=ast,
                backend=CurlBackend(self.refs.host, self.refs.cookie))
        rv = spec.get("right")
        if isinstance(rv, dict):
            rv = rv.get("const", rv.get("value"))
        return build_filter_expression(
            dto_full=dto, list_desc=list_node.get("caption") or "列表",
            entity_model=m, field=spec["field"], op=spec.get("op") or "EQ",
            const=rv, backend=CurlBackend(self.refs.host, self.refs.cookie))

    def _st_page_info(self, alias, *, page_number=1, page_size=20,
                      need_total=True, caption="分页参数", **_) -> dict:
        """创建分页参数对象（PageInfo），供查询多条数据 pagination 使用。"""
        from .microflow_nodes_v2 import create_variable_page_info
        return self._add(create_variable_page_info(self.b, page_number=page_number,
                                                   page_size=page_size,
                                                   need_total=need_total, caption=caption),
                         alias)

    def _sort_params(self, m: dict, sort_by, sort_dir="ASC"):
        """把字段名转成平台的 sortParams[{sortType, attrType}]（attrType 是字段活引用）。"""
        if not sort_by:
            return None
        from .microflow_fields import field_attr
        names = sort_by if isinstance(sort_by, (list, tuple)) else [sort_by]
        dirs = sort_dir if isinstance(sort_dir, (list, tuple)) else [sort_dir] * len(names)
        attrs = m.get("attributes") or {}
        out = []
        for f, d in zip(names, dirs):
            if f not in attrs:
                raise ComposeError("实体 %s 没有字段 %r（可用：%s）"
                                   % (m.get("label") or m.get("name"), f, sorted(attrs)))
            out.append({"sortType": d, "attrType": field_attr(m, f)})
        return out

    def _st_list_operation(self, alias, *, list_node, op_type="SIZE",
                           title="列表处理后结果", caption="列表处理",
                           sort_by=None, sort_dir="ASC", count_fields=None,
                           index_value=None, second_list=None, filter=None,
                           group_by=None, **_) -> dict:
        """列表操作。SORT 用 sort_by+sort_dir，SUM/MIN/MAX/MAP 用 count_fields，
        PICK_ONE 用 index_value —— 字段级参数在这里转成平台 attrType（需要活引用）。"""
        src = self._node(list_node)
        dto = (src.get("output") or {}).get("id")
        attrs = {}
        if dto and (sort_by or count_fields):
            if self.refs is None:
                raise ComposeError("列表操作需要字段属性但没有 LiveRefs")
            attrs = self.refs.dto_attributes(self.app_id, self.app_name, dto) or {}

        def _attr(name):
            from .microflow_fields import field_attr
            if name not in attrs:
                raise ComposeError("实体 %s 没有字段 %r（可用：%s）"
                                   % (dto, name, sorted(attrs)))
            return field_attr({"attributes": attrs, "refApp": self.app_name}, name)

        sort_params = None
        if sort_by:
            names = sort_by if isinstance(sort_by, (list, tuple)) else [sort_by]
            dirs = sort_dir if isinstance(sort_dir, (list, tuple)) else [sort_dir] * len(names)
            sort_params = [{"sortType": d, "attrType": _attr(f)}
                           for f, d in zip(names, dirs)]
        count_attrs = [_attr(f) for f in (count_fields or [])] or None
        expr = None
        if op_type == "FILTER":
            expr = self._filter_expression(src, filter)
        gb = None
        if op_type == "GROUP_AND_SUM":
            names = group_by if isinstance(group_by, (list, tuple)) else [group_by]
            if not names or not names[0]:
                raise ComposeError("GROUP_AND_SUM 需要 group_by（分组字段）")
            gb = [_attr(f) for f in names]
        return self._add(X.list_operation(self.b, src, op_type=op_type, title=title,
                                          caption=caption, sort_params=sort_params,
                                          count_attrs=count_attrs,
                                          index_value=index_value,
                                          second_node=self._node(second_list) if second_list else None,
                                          expression=expr, group_by=gb),
                         alias)

    def _st_custom_error(self, alias, *, message="运行验证失败",
                         error_type="GLOBAL", caption="自定义错误", **_) -> dict:
        """自定义错误节点。

        ★ 让流程在**设计好的条件**下主动失败，是「可断言」的前提：
          没有它只能验证「跑通了」，验证不了「结果对不对」。
        """
        return self._add(X.custom_error(self.b, message,
                                        error_type=error_type,
                                        caption=caption), alias)

    # -- 实体查询/读写 --
    def _st_retrieve(self, alias, *, entity, cond_field="", right="", right_value=None,
                     by_id_from=None, from_field="", caption="查询单条数据",
                     null_handling="CONTINUE", null_message="", **_) -> dict:
        """查询单条。by_id_from 给前序节点别名即走 ID 查询（fetchType=IDS，246 次真实用法），
        否则走条件查询（fetchType=CONDITION，375 次）。"""
        m = self.entity(entity)
        if by_id_from:
            src = self._node(by_id_from)
            id_ref = self._id_ref(src, m, from_field)
            return self._add(V2.retrieve(self.b, m, "", None, caption=caption,
                                         id_value=id_ref,
                                         null_handling=null_handling,
                                         null_message=null_message), alias)
        rv = self._cond_right(right_value, right)
        if cond_field and cond_field not in (m.get("attributes") or {}):
            raise ComposeError("字段 %r 不存在于实体 %r（真实字段：%s）"
                               % (cond_field, entity,
                                  sorted(m.get("attributes") or {})[:12]))
        return self._add(V2.retrieve(self.b, m, cond_field, rv, caption=caption,
                                     null_handling=null_handling,
                                     null_message=null_message), alias)

    def _id_ref(self, src_node, entity_model, from_field=""):
        """构造 ID 查询的 value（引用前序节点的 ID 字段）。

        ★ 两种来源形态完全不同：
          a) 来源是 DTO 对象（RETRIEVE/CREATE_VARIABLE 实体）→ 取 <output>.id，
             走完整 SelectParam（id/dtoType/path 都填）。
          b) 来源是 BASIC 标量（CREATE_ENTITY 的 output 是 BIGINTEGER 插入 ID）
             → 整个值就是这个标量本身，**不能再取字段**，
             且 id/dtoType 必须空串（G17：BASIC 引用带 DTO 字段 = PageInfo 模板残留，
             构建期报错或运行时取到 null）。
        """
        o = src_node.get("output") or {}
        if not o.get("name"):
            raise ComposeError("前序节点没有 output.name，不能作为 ID 来源")
        # ── 分支 b：BASIC 标量直接当 ID ──────────────────────────────
        is_basic = (o.get("dataType") or "").upper() in (
            "BOOLEAN", "STRING", "BIGINTEGER", "DECIMAL", "DATETIME", "INTEGER") \
            and not o.get("dtoType")
        if is_basic:
            if from_field and from_field != "id":
                raise ComposeError(
                    "前序节点 %r 是 BASIC 标量，没有字段 %r 可取；"
                    "直接就是 ID 值本身（不要传 from_field）"
                    % (src_node.get("nodeId"), from_field))
            nm = o["name"]
            return {"type": "SelectParam", "selectParam": {
                "id": "", "dtoType": "", "javaType": o.get("javaType"),
                "dataType": o.get("dataType"), "type": "OBJECT",
                "desc": o.get("desc") or o.get("description")
                        or src_node.get("caption") or "",
                "name": nm, "key": nm, "path": nm,
                "outputName": nm, "position": "parent",
                "udcApp": True, "multiSelect": False,
                "customs": {"basicType": True},
            }}
        ent = src_node.get("structure") or {}
        dto = ent.get("id") or ent.get("fullName") or o.get("id")
        fname = from_field or "id"
        # ★ from_field 是前序节点（by_id_from）的字段，不是目标实体字段。
        #   字段元数据从前序节点的实体模型取，否则「按售后.orderId 查订单」会
        #   误报 orderId 不在订单实体（§4.29 循环内同源，循环外也适用）。
        src_label = ent.get("label") or ent.get("caption")
        src_model = self.entity(label=src_label) if src_label else None
        src_attrs = (src_model or {}).get("attributes") or {}
        f = src_attrs.get(fname)
        if f is None:
            raise ComposeError("前序节点 %r 实体 %r 的字段 %r 不存在（可用：%s）"
                               % (src_node.get("nodeId"), src_label, fname,
                                  sorted(src_attrs)[:12]))
        # ★ 字段级引用铁律（§4.22）：name=纯字段名（不是 outputName.fname），
        #   relationEntity=字段所属实体，appName=字段 refApp，否则 04004
        #   「实体属性已更改」。
        return {"type": "SelectParam", "selectParam": {
            "description": f.get("caption") or fname,
            "key": "%s%s" % (o["name"], f["id"]),
            "name": fname,
            "id": f["id"], "appName": f.get("refApp"),
            "position": "children",
            "path": "%s.%s" % (str(dto).replace(".", ""), fname),
            "outputName": o["name"], "dataType": f["dataType"],
            "type": "OBJECT", "javaType": f["javaType"],
            "dtoType": (src_model or {}).get("dtoType") or "MASTER_ENTITY",
            "relationEntity": (src_model or {}).get("relationEntityId"),
            "udcApp": True, "multiSelect": False,
            "customs": {"basicType": False}, "iconKey": "LinedCheckCircle",
            "parentLabel": "", "disabled": False, "isLeaf": True,
            "nodeInfo": {"nodeId": src_node["nodeId"], "type": "ACTIVITY",
                         "actionType": src_node.get("actionType")},
        }}

    def _cond_right(self, right_value, right=""):
        """条件右值归一：DSL 的 {"const": x} → 平台 CONSTANT。

        ★ 直接透传 {"const": ...} 时，平台把 rightParams 解析成空 value/空 desc，
          条件静默失效 —— 运行时返回整张表而 success 仍为 true（2026-11-02 实测）。
        """
        if isinstance(right_value, dict):
            if "const" in right_value and "type" not in right_value:
                v = "" if right_value["const"] is None else str(right_value["const"])
                return {"type": "CONSTANT", "value": v,
                        "desc": right_value.get("desc") or v}
            return right_value
        return _cond_val(right)

    def _st_retrieve_array(self, alias, *, entity, cond_field="", right="",
                           right_value=None, caption="查询多条数据",
                           fetch_type="CONDITION", ids_from=None,
                           sort_by=None, sort_dir="ASC", page_info_from=None, **_) -> dict:
        m = self.entity(entity)
        rv = self._cond_right(right_value, right)
        if (fetch_type == "CONDITION" and cond_field
                and cond_field not in (m.get("attributes") or {})):
            raise ComposeError("字段 %r 不存在于实体 %r" % (cond_field, entity))
        # cond_field=None = 占位（调用方随后写组合条件，如 enabled==true && id!=入参）
        return self._add(V2.retrieve_array(self.b, m, cond_field, rv, caption=caption,
                                           fetch_type=fetch_type,
                                           ids_node=self._node(ids_from) if ids_from else None,
                                           sort_params=self._sort_params(m, sort_by, sort_dir),
                                           page_info_node=self._node(page_info_from)
                                           if page_info_from else None),
                         alias)

    def _st_create_entity(self, alias, *, entity, fields, caption="插入数据", **_) -> dict:
        """fields: {字段名: 值} 或 [(字段名, 值)]。字段名必须是实体的真实字段。"""
        m = self.entity(entity)
        pairs = self._field_pairs(m, fields, entity)
        return self._add(V2.create_entity(self.b, m, pairs, caption=caption), alias)

    def _st_change_entity(self, alias, *, entity, from_node, fields,
                          caption="更新数据", **_) -> dict:
        m = self.entity(entity)
        pairs = self._field_pairs(m, fields, entity)
        return self._add(V2.change_entity(self.b, m, self._node(from_node), pairs,
                                          caption=caption), alias)

    def _st_delete_entity(self, alias, *, entity, cond_field="", right="",
                          right_value=None, from_node=None, caption="删除数据", **_) -> dict:
        """删除数据。两种模式（平台只有这两种，语料 deleteType: CONDITION 10 / SELECT_PARAM 9 / IDS 1）：

          from_node 给了 → SELECT_PARAM：删除该节点出参指向的那条记录（动态 ID 唯一可用路径）
          否则          → CONDITION：按条件批量删（右值**只能是常量**）

        ★ 2026-11-02 实测：CONDITION 模式的右值填 SelectParam（节点引用）会
          publish 被拒 `BOOT_1001 Parameter Error`，且响应里没有任何字段级提示。
          也就是说「按动态 ID 删除」不能写条件引用，必须走 SELECT_PARAM。
        """
        m = self.entity(entity)
        if from_node:
            src = self._node(from_node)
            return self._add(V2.delete_entity_by_param(
                self.b, m, self._out_ref(src)["selectParam"],
                caption=caption), alias)
        if not cond_field:
            raise ComposeError("delete_entity 需要 cond_field（CONDITION 模式）"
                               "或 from_node（SELECT_PARAM 模式）")
        rv = self._cond_right(right_value, right)
        if cond_field not in (m.get("attributes") or {}):
            raise ComposeError("字段 %r 不存在于实体 %r" % (cond_field, entity))
        return self._add(V2.delete_entity(self.b, m, cond_field, rv,
                                          caption=caption), alias)

    def _st_create_batch_entity(self, alias, *, entity, list_node,
                                caption="批量插入数据", **_) -> dict:
        m = self.entity(entity)
        return self._add(X.create_batch_entity(self.b, m, self._node(list_node), [],
                                               caption=caption), alias)

    def _st_change_batch_entity(self, alias, *, entity, list_node,
                                caption="批量更新数据", **_) -> dict:
        m = self.entity(entity)
        return self._add(X.change_batch_entity(self.b, m, self._node(list_node), [],
                                               caption=caption), alias)

    # -- 映射 --
    def _st_create_map(self, alias, *, title="vMap", key_type="STRING",
                       value_type="STRING", caption="创建映射组", **_) -> dict:
        return self._add(X.create_map(self.b, title, caption=caption,
                                      key_type=key_type, value_type=value_type), alias)

    def _st_map_operation(self, alias, *, map_node, op_type="PUT",
                          key_value=None, value_value=None, result_title="映射取值",
                          data_type="STRING", caption="Map操作", **_) -> dict:
        kv = _val(key_value)
        vv = _val(value_value)
        return self._add(X.map_operation(self.b, self._node(map_node), kv, vv,
                                         op_type=op_type, caption=caption,
                                         result_title=result_title,
                                         data_type=data_type), alias)

    # -- 加工 --
    def _st_convert_data(self, alias, *, from_node, convert_type, title,
                         caption="数据转换", **_) -> dict:
        return self._add(X.convert_data(self.b, self._node(from_node),
                                        convert_type, title, caption=caption), alias)

    def _st_data_mapping(self, alias, *, entity, from_node, caption="数据转换",
                         src_field="name", dst_field=None, **_) -> dict:
        """dataSource 字段映射。src_field/dst_field 指定映射行两端字段
        （默认 name→name 只适用于有 name 字段的实体；其它实体必须显式给）。"""
        m = self.entity(entity)
        return self._add(S.data_mapping(self.b, m, self._node(from_node),
                                        caption=caption, src_field=src_field,
                                        dst_field=dst_field), alias)

    # -- 服务/子流程 --
    def _st_publish_business_event(self, alias, *, event, attrs=None,
                                   caption="事件投递", **_) -> dict:
        """事件投递（应用内 IN_APP）。

        `event` 必须是活引用对象（udcMicroflowSearchEventListPost 返回的行，
        含 fullName/caption/source/dtoType/udcApp），跨应用不可复用，禁止写死。
        `attrs` 是事件 DTO 的字段映射（[{attrType, value}]），由调用方按事件元数据构造。
        """
        if not isinstance(event, dict) or not event.get("fullName"):
            raise ComposeError("事件投递需要活引用事件对象（缺 fullName）：%r" % (event,))
        return self._add(X.publish_business_event(self.b, event, attrs or [],
                                                  caption=caption), alias)

    def _st_call_data_flow(self, alias, *, entity, rule, condition=None,
                           out_desc="生单结果", data_source_type="CONDITION",
                           caption="执行生单规则", **_) -> dict:
        """执行生单规则。

        `rule` 必须是活引用（LiveRefs.data_flow_candidates 的列表行），
        `dataFlowMappingId` / `dataFlow.id` 都取**列表行 id**（DataFlowMapping 主键）——
        前端保存时 `merge:{dataFlowMappingId:"dataFlow.id"}` 强制两者相等，
        运行时也只读 dataFlowMappingId。
        `condition` 在 CONDITION 模式（默认）下必填且不能为空数组——
        运行时 `buildConditionInfo(..., required=true)`。
        """
        if not isinstance(rule, dict):
            raise ComposeError("生单规则需要活引用对象：%r" % (rule,))
        m = self.entity(entity)
        return self._add(X.call_data_flow(self.b, entity_structure(m), rule, condition,
                                          out_desc, caption=caption,
                                          data_source_type=data_source_type), alias)

    def _st_break(self, alias, caption="跳出循环", **_) -> dict:
        """跳出循环（BREAK）。只能放在 FOR / FOR_EACH / FOR_COUNT 的 body 里。"""
        return self._add(V2.break_node(self.b, caption=caption), alias)

    def _st_call_app_service(self, alias, *, method_full, attrs=None,
                             caption="自定义服务", app_name=None,
                             app_caption=None, **_) -> dict:
        """method_full 是完整类.方法名；签名运行时拉（含 md5）。"""
        if self.refs is None:
            raise ComposeError("需要服务 %r 但没有 LiveRefs（禁止写死）" % method_full)
        try:
            svc = self.refs.app_service_method(self.app_id, self.app_name, method_full)
        except LookupError as e:
            raise ComposeError("服务活引用失败: %s" % e)
        # ★ DSL 层 attrs 是字段映射 dict（{字段: {const/field: 值}}），构造器要的是
        #   字段级 attrType 列表。必须用 field_attr 拉真实字段元数据（16-20 键），
        #   手搓简化键会缺 filterDataType/filterType/filterFullName/relationApp，
        #   前端「所选数据已失效，请重新选择」（field_attr docstring 已记）。
        if isinstance(attrs, dict):
            dto = ((svc.get("parameter") or {}).get("item") or {}).get("itemType") or ""
            em = {"attributes": (self.refs.dto_attributes(self.app_id, self.app_name, dto)
                                 if dto else {}), "refApp": "udc"}
            conv = []
            for i, (f, v) in enumerate(attrs.items()):
                at = field_attr(em, f, sort=i)
                val = v
                if isinstance(v, dict) and "const" in v:
                    val = simple(v["const"])
                conv.append({"attrType": at, "value": val})
            attrs = conv
        # ★ 传活引用签名，不走磁盘写死的 definitions/services/*.json
        #   （磁盘那份是单应用专有，换应用直接崩）
        return self._add(S.call_app_service(self.b, method_full, attrs or [],
                                            caption=caption, app_name=app_name,
                                            app_caption=app_caption,
                                            select_method=svc), alias)

    def _st_sub_microflow(self, alias, *, sub_name="", sub_id="",
                          attrs=None, value=None, out_desc=None, inputs=None,
                          caption="子微流程", **_) -> dict:
        if self.refs is None:
            raise ComposeError("需要子微流程但没有 LiveRefs（禁止写死）")
        try:
            mf = self.refs.find_sub_mf(self.app_id, name=sub_name, mf_id=sub_id)
        except LookupError as e:
            raise ComposeError("子微流程活引用失败: %s" % e)
        # ★ 入参/出参契约必须读子流程**当前**定义：
        #   checkMfService 会逐字比对 mfService.input/output 与子流程 schema 的
        #   input/output，任一处不同就报 MICRO_FLOW_CHANGE（相当于设计器的「属性已变更，
        #   请重新选择」提示）。早期这里写死 hasInput/hasOutput=False，
        #   只能调用无参子流程，一遇带参子流程发布必被拒。
        detail = getattr(self.refs, "microflow_detail", None)
        if not callable(detail):
            raise ComposeError("UNVERIFIED: 子微流程详情接口不可用")
        det = detail(mf.get("id"))
        if not isinstance(det, dict) or "input" not in det or "output" not in det:
            raise ComposeError("UNVERIFIED: 子微流程入出参契约缺失")
        inp, outp = det.get("input"), det.get("output")
        svc = {"id": str(mf.get("id")), "name": mf.get("name"),
               "caption": mf.get("caption"), "appId": self.app_id,
               "appCaption": None, "appName": None,
               "description": mf.get("caption") or "",
               "hasInput": bool(inp), "hasOutput": bool(outp), "hostPath": None,
               "input": inp, "method": "POST",
               "output": outp, "path": "/microflow/" + str(mf.get("name")),
               "triggerType": det.get("triggerType") or mf.get("triggerType") or "MANUAL",
               "type": mf.get("type") or "SERVICE", "restType": "POST"}
        if inputs:
            attrs = self._sub_input_attrs(inp, inputs)
        # ★ 标量入参 value 的 desc 要体现「子流程入参字段名」，不是父流程变量名。
        #   否则前端「参数」栏显示父流程变量名（reqId），用户看不到映射到子流程哪个入参
        #   （MF-00 的「采购申请ID」）。key/name/outputName 仍指向父流程变量，只改 desc。
        if value is not None and inp:
            in_desc = (inp.get("desc") or inp.get("description") or "").strip()
            if in_desc:
                sp = value.get("selectParam") or {}
                sp["desc"] = in_desc
                sp["description"] = in_desc
                _dt = (inp.get("dataType") or "STRING").upper()
                _label = {"STRING": "文本", "BIGINTEGER": "长整数", "INTEGER": "整数",
                          "DECIMAL": "小数", "BOOLEAN": "布尔",
                          "DATETIME": "日期时间", "DATE": "日期"}.get(_dt, "文本")
                value["desc"] = "%s [%s]" % (in_desc, _label)
        return self._add(S.sub_microflow(self.b, svc, attrs, caption=caption,
                                         value=value, out_desc=out_desc), alias)

    def _sub_input_attrs(self, inp: dict | None, inputs: dict) -> list:
        """子微流程 DTO 入参：{字段: {const: x}} → mappingType=attrs 的字段级映射。

        真实形态（112 条语料）：attrType 是**子流程入参 DTO 的字段**（不是父流程的），
        value 是 Simple（常量）或 SelectParam（引用）。
        """
        dto = (inp or {}).get("id")
        if not dto:
            raise ComposeError("子微流程没有 DTO 入参，不能用 inputs 按字段映射")
        em = {"attributes": self.refs.dto_attributes(self.app_id, self.app_name, dto),
              "refApp": self.app_name}
        out = []
        for i, (fname, spec) in enumerate(inputs.items()):
            if fname not in em["attributes"]:
                raise ComposeError("子流程入参 DTO 没有字段 %r（可用：%s）"
                                   % (fname, sorted(em["attributes"])))
            if not isinstance(spec, dict):
                spec = {"const": spec}
            if "const" in spec:
                v = simple(spec["const"])
            else:
                raise ComposeError("子流程入参 %r 目前只支持 {const: 值}" % fname)
            out.append({"attrType": field_attr(em, fname, sort=i), "value": v})
        return out

    # ---------------- 引用辅助 ----------------
    def _out_ref(self, node: dict) -> dict:
        """引用前序节点的输出（SelectParam 对象级）。

        照抄真实 endNode.value.selectParam 结构（303 个真实样本统计）：
          javaType/dataType/type/name/key/outputName/description/position 恒有(303)
          id 302、dtoType 298、path 286、appName 171、udcApp 160

        ★ `dtoType` 必填 —— 缺它 checkSchema 直接报
          `root.endNode.value.selectParam.dtoType PROPERTY_IS_REQUIRED`（实测踩过）。
        """
        if (node.get("actionType") == "SUB_MICROFLOW"
                and (node.get("mfService") or {}).get("hasOutput") is False):
            raise ComposeError("子流程无出参，不能作为引用源")
        o = node.get("output") or {}
        if not o.get("name"):
            raise ComposeError("节点 %r 没有 output.name，不能作为引用源"
                               % (node.get("nodeId")))
        ent = node.get("structure") or {}
        # ★ BASIC 型节点（BASIC 变量）：structure 是 PageInfo 模板残留，不能拿来当 DTO。
        #   真实 endNode 引用 BASIC 变量的形态（-92053058823）：name=key=path=outputName，
        #   id=""，dtoType=""，无 nodeInfo。
        is_basic = (o.get("dataType") or "").upper() in (
            "BOOLEAN", "STRING", "BIGINTEGER", "DECIMAL", "DATETIME", "INTEGER") \
            and not (o.get("dtoType"))
        if is_basic:
            nm = o["name"]
            ref = {
                "id": "", "javaType": o.get("javaType"),
                "dataType": o.get("dataType"), "type": "OBJECT",
                "dtoType": "", "desc": o.get("desc") or o.get("description")
                                    or node.get("caption"),
                "name": nm, "key": nm, "path": nm,
                "outputName": nm, "position": "parent",
            }
            return {"type": "SelectParam", "selectParam": ref}
        dto = o.get("id") or ent.get("id") or ent.get("fullName")
        dto_type = o.get("dtoType") or ent.get("dtoType") or "MASTER_ENTITY"
        path = str(dto or "").replace(".", "")
        ref = {
            "id": dto, "javaType": o.get("javaType"), "dataType": o.get("dataType"),
            "type": o.get("type", "OBJECT"), "dtoType": dto_type,
            "desc": node.get("caption"), "description": node.get("title")
            or node.get("caption"),
            "name": path, "key": o["name"] + str(dto),
            "outputName": o["name"], "position": "parent",
            "path": path,
            "appName": o.get("appName"), "udcApp": o.get("udcApp", True),
            "parentLabel": "",
            "nodeInfo": {"nodeId": node["nodeId"], "type": "ACTIVITY",
                         "actionType": node.get("actionType"),
                         "entityCaption": ent.get("label")},
        }
        if ent.get("relationEntity"):
            ref["relationEntity"] = ent["relationEntity"]
            ref["relationEntityFullName"] = ent.get("entity")
        return {"type": "SelectParam", "selectParam": ref}

    def refs_field(self, node: dict, field: str) -> dict | None:
        """引用前序节点输出的某个字段（真实字段引用，带 id/javaType）。"""
        if not field:
            return None
        o = node.get("output") or {}
        ent = node.get("structure") or {}
        dto = ent.get("id") or ent.get("fullName")
        if not dto:
            return None
        m = None
        for cand in self._entities.values():
            # ★ structure.id 是 **DTO 全名**，而实体模型的 fullName 也是 DTO 全名
            #   （entity_model 适配过），entity 字段是 domain 全名。
            #   早期只比 fullName，一旦别的调用方塞进 domain 名就查不到 →
            #   返回 None → attrs 落成悬空引用（G2）。
            if cand.get("fullName") == dto or cand.get("entity") == dto:
                m = cand
                break
        if m is None:
            # 兜底：按 dto 反查 LiveRefs（带缓存），供跨节点场景使用
            lr = self.refs
            if lr is not None and hasattr(lr, "entity_model"):
                try:
                    got = lr.entity_model(str(self.app_id), self.app_name, dto_full=dto)
                    if got:
                        self._entities[dto] = got
                        m = got
                except Exception:
                    m = None
        if m is None or field not in (m.get("attributes") or {}):
            return None
        a = m["attributes"][field]
        return {"type": "SelectParam",
                "selectParam": {
                    "id": a["id"], "javaType": a["javaType"],
                    "dataType": a["dataType"], "type": "OBJECT",
                    "desc": a.get("caption") or field,
                    # ★ name 必须是**纯字段名**。写成 "<outputName>.<field>" 时，
                    #   平台编译期把它当 DTO 的嵌套类去解析，直接
                    #   「找不到符号: 类 _CREATE_VARIABLE_xxx」构建失败（实测）。
                    #   真实样本（xzhAllNodesV16）name="f03int"，outputName 单独给。
                    "name": field,
                    "key": "%s%s" % (o.get("name"), a["id"]),
                    "path": "%s.%s" % (ent.get("key") or "", field),
                    "position": "children", "outputName": o.get("name"),
                    "appName": self.app_name,
                    "nodeInfo": {"nodeId": node["nodeId"], "type": "ACTIVITY",
                                 "actionType": node.get("actionType")},
                    "disabled": False}}

    def _field_pairs(self, m: dict, fields: Any, label: str) -> list[tuple[str, dict]]:
        """把 {字段名: 值} 规范成 [(字段名, 值字典)]，字段名必须在实体里存在。"""
        if isinstance(fields, dict):
            items = list(fields.items())
        else:
            items = list(fields or [])
        attrs = m.get("attributes") or {}
        out = []
        for fname, val in items:
            if fname not in attrs:
                raise ComposeError("字段 %r 不存在于实体 %r（真实字段：%s）"
                                   % (fname, label, sorted(attrs)[:12]))
            out.append((fname, _val(val)))
        return out

    # ---------------- 触发方式（走仓库 microflow_triggers）----------------
    def trigger_manual(self, *, node_id: str = "MFStartNode", param_type: str = "NONE",
                       output: dict | None = None, caption: str = "手动触发",
                       basic: str | None = None, entity_object: dict | None = None,
                       default_object: dict | None = None) -> dict:
        """服务定义（MANUAL）。SERVICE+MANUAL 才有出入参。"""
        from .microflow_triggers import manual_trigger
        # ★ 参数显示名称（设计器「参数名称」必填框）绑的是 trigger.desc；
        #   不传就是空黄框，UI 判为未填。默认取 output.desc/description。
        return manual_trigger(node_id=node_id, param_type=param_type, output=output,
                              caption=caption, basic=basic,
                              entity_object=entity_object,
                              default_object=default_object,
                              desc=(output or {}).get("desc")
                                   or (output or {}).get("description") or "")

    def trigger_schedule(self, *, job_caption: str, cycle_type: str = "DAY",
                         rotation_type: str = "DAY", value: str = "1",
                         node_id: str = "", day_of_week: int = 1) -> dict:
        """定时任务（SCHEDULE）。

        ★ 定时任务**无出入参**（trigger.output=null，endNode.output=null）——
          这是 24 条真实生产样本的一致形态，不要给它加出参。
        ★ cycle_type：DAY(19/24 最常用) / SIMPLE(自定义周期) / HOUR / WEEK / MONTH / YEAR。
          SIMPLE 时用 rotation_type(MINUTE/HOUR/DAY) + value=N。
        """
        from .microflow_triggers import schedule_trigger
        return schedule_trigger(node_id=node_id or ("SERVICE_" + _rid6()),
                                job_caption=job_caption, cycle_type=cycle_type,
                                rotation_type=rotation_type, value=value,
                                day_of_week=day_of_week)

    def trigger_event(self, *, event: dict, node_id: str = "",
                      out_param_name: str = "事件数据") -> dict:
        """事件监听（BUSINESS_EVENT）。★ 无对外出入参（endNode.output=null）。"""
        from .microflow_triggers import event_trigger
        return event_trigger(node_id=node_id or ("SERVICE_" + _rid6()),
                             event=event, out_param_name=out_param_name)

    def trigger_mf_event(self, *, event: dict, node_id: str = "",
                         out_param_name: str = "事件数据") -> dict:
        """应用内微流程事件监听（MICRO_FLOW_EVENT 源，如 XzhVerifyEvent）。

        event 是活引用（udcMicroflowSearchEventListPost 行，含 fullName/caption），
        需已补 eventDataFullName/eventMfCustomDtoName/name/sourceId/appName。
        ★ 无对外出入参（endNode.output=null，input=trigger.output）。"""
        from .microflow_triggers import mf_event_trigger
        return mf_event_trigger(node_id=node_id or ("SERVICE_" + _rid6()),
                                event=event, out_param_name=out_param_name)

    # ---------------- 收尾 ----------------
    def finish(self, *, end_from: str = "", trigger: dict | None = None,
               gate: bool = True, basic_out: str | None = None,
               out_desc: str = "流程返回") -> dict:
        """组装 schema 并过闸门。不合规抛 ComposeError（绝不产出违规 schema）。

        ★ 出入参按触发方式决定（24 条真实生产定时任务 + 643 条流程校准）：
          | 触发 | endNode | 顶层 input/output |
          |---|---|---|
          | MANUAL（服务定义） | 有 output + value(SelectParam 引用末节点) + mappingType/paramType | 有 |
          | SCHEDULE（定时任务） | **只有 9 键，output=null，无 value** | 都是 null |
          | BUSINESS_EVENT（事件监听） | output=null | 都是 null |
        给定时/事件加出入参会让 checkSchema 报 root.endNode.value.value PROPERTY_IS_REQUIRED
        —— 真实样本里 24/24 定时任务的 endNode 只有 {id,name,type,actionType,nodeId,
        caption,description,input,output} 这 9 个键。
        """
        if not self.nodes and not _is_nodeless(trigger):
            raise ComposeError("没有任何节点，拒绝生成空流程")

        trg = trigger if trigger is not None else self.trigger_manual()
        ttype = (trg or {}).get("type")

        # endNode 必须在顶层（type=END/actionType=END_NODE），绝不进 nodes
        if ttype in ("SCHEDULE", "BUSINESS_EVENT"):
            # 无出入参：9 键最小形态，照抄 24 条真实生产样本
            end_node = {"id": "", "name": "", "type": "END", "actionType": "END_NODE",
                        "nodeId": "MFEndNode", "caption": "结束", "description": "",
                        "input": None, "output": None}
            # ★ BUSINESS_EVENT 的顶层 input = trigger.output（事件数据入参）；
            #   SCHEDULE 才是 input=null。填错会让部署阶段「一致性检测未通过」。
            ev_in = (trg.get("output") if ttype == "BUSINESS_EVENT" else None)
            schema = {"endNode": end_node, "output": None, "input": ev_in,
                      "sourceType": "PAGE", "trigger": trg, "nodes": self.nodes}
        else:
            end_out = {"id": None, "javaType": "java.lang.String", "dataType": "STRING",
                       "type": "OBJECT", "desc": out_desc, "dtoType": None,
                       "udcApp": None, "hasPagination": None,
                       "name": "_FLOW_OUTPUT_" + _rid6()}
            end_value = None
            if basic_out:
                # ★ BASIC 出参（244 条真实样本）：
                #   endNode.paramType=BASIC + basic=<dataType>，
                #   value 引用一个 BASIC 型变量节点（其 output.dataType == basic_out）。
                #   output.name 必须真实（前端按 name 注册变量表）。
                from .microflow_triggers import _JAVA_TYPE
                jt = _JAVA_TYPE.get(basic_out, "java.lang.String")
                o = self._node(end_from).get("output") or {}
                if o.get("dataType") != basic_out:
                    raise ComposeError(
                        "basic_out=%r 但引用节点的 output.dataType=%r，类型不匹配"
                        % (basic_out, o.get("dataType")))
                nm = "_FLOW_OUTPUT_" + _rid6()
                end_out = {"id": None, "javaType": jt, "dataType": basic_out,
                           "type": "OBJECT", "desc": out_desc, "dtoType": None,
                           "udcApp": None, "hasPagination": None, "name": nm}
                sp = dict(self._out_ref(self._node(end_from))["selectParam"])
                sp.update({"javaType": jt, "dataType": basic_out, "dtoType": "",
                           "id": "", "desc": out_desc, "description": out_desc})
                end_value = {"type": "SelectParam", "selectParam": sp, "desc": out_desc}
            elif end_from:
                src = self._node(end_from)
                end_value = dict(self._out_ref(src), type="SelectParam")
                o = src.get("output") or {}
                end_out = dict(end_out, id=o.get("id"), javaType=o.get("javaType"),
                               dataType=o.get("dataType"), type=o.get("type", "OBJECT"))
            elif _has_out_param(trg):
                # MANUAL 带出参但没指定引用源 → 必须拦，否则 checkSchema 报
                # root.endNode.value.value PROPERTY_IS_REQUIRED（实测踩过）
                raise ComposeError(
                    "MANUAL 有出参时必须传 end_from 指定末节点引用源，"
                    "否则 endNode.value 为空会被 checkSchema 拒")

            end_node = {"id": "", "name": "", "type": "END", "actionType": "END_NODE",
                        "nodeId": "MFEndNode", "caption": "结束", "description": "",
                        "input": None, "output": end_out, "outPutDesc": None,
                        "mappingType": "BASIC", "paramType": "BASIC",
                        "basic": basic_out or "STRING",
                        "isArray": False, "desc": out_desc,
                        "hasPagination": None,
                        "value": end_value, "isCompleted": True}
            schema = {"endNode": end_node, "output": end_out,
                      "input": (trg or {}).get("output"),
                      "sourceType": "PAGE", "trigger": trg, "nodes": self.nodes}

        if gate:
            self._run_gates(schema)
        # P6：生成时就能看见「这个节点类型还没有运行证据」，不阻塞构建
        try:
            from ..udc.microflow.capability_registry import advisory as _adv
            self.advisories = _adv(schema)
        except Exception:
            self.advisories = ["UNVERIFIED: capability advisory unavailable"]
        return schema

    def _run_gates(self, schema: dict) -> None:
        """出门闸门：G1-G12 + 引用完整性 + 契约同形。任一不过即抛。"""
        problems: list[str] = []
        try:
            from components.udc.microflow.gates import (
                run_gates, run_end_gate, run_leak_gate, run_order_gate)
            for fn in (run_gates, run_end_gate, run_leak_gate, run_order_gate):
                try:
                    problems += fn(schema)
                except Exception as e:
                    problems.append("闸门 %s 异常: %s" % (fn.__name__, e))
        except ImportError as e:
            raise ComposeError("闸门模块不可用，拒绝产出: %s" % e)

        try:
            from components.udc.microflow.contract_gate import check_schema
            problems += check_schema(schema)
        except ImportError as e:
            raise ComposeError("契约闸门不可用，拒绝产出: %s" % e)

        # 引用完整性：别名机制保证，这里再机械核一遍
        # ★ known 必须递归遍历（含分支/循环体内节点）：
        #   早期只取 self.nodes 顶层，循环体内节点不算 known →
        #   循环内 attrs 引用本体 RETRIEVE 一律被误判"引用悬空"。
        from components.udc.microflow.gates import _walk_nodes as _wn
        known = {n.get("nodeId") for n in _wn(schema.get("nodes"))}
        known |= {"MFStartNode", "MFEndNode"}
        leaks = []

        def scan(obj, path="root"):
            if isinstance(obj, dict):
                if obj.get("type") == "SelectParam":
                    sp = obj.get("selectParam") or {}
                    ni = (sp.get("nodeInfo") or {}).get("nodeId")
                    if ni and ni not in known:
                        leaks.append((path, ni))
                for k, v in obj.items():
                    scan(v, path + "." + str(k))
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    scan(v, "%s[%d]" % (path, i))

        scan(schema)
        for p, ni in leaks[:10]:
            problems.append("引用悬空 %s -> %s" % (p, ni))

        if problems:
            msg = "组装闸门拦截 %d 项：\n  " % len(problems) + "\n  ".join(problems[:20])
            raise ComposeError(msg)
