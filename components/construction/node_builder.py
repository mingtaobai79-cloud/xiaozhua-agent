"""定义驱动的节点构造器核心框架。

架构：结构来自 node_templates/（V16 真实流程骨架），字段来自 definitions/（真实定义含 md5），
引用按链路顺序（符号表：前序出参注册 → 后序引用解析）。
禁止凭空拼字段 / 手写 id/md5 / 整包并行写。
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import uuid
from typing import Any

TPL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      "fixtures", "microflow", "node_templates")
DEF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                       "definitions")

# 24 类节点：模板文件名 → actionType（模板文件名即 actionType，除个别）
# EVENT_DELIVERY / TYPE_CONVERT 无模板，需单独构造


def load_templates(tpl_dir: str = TPL_DIR) -> dict[str, dict[str, Any]]:
    """加载所有节点模板（取每类字段最全的一条）。"""
    tpls: dict[str, dict[str, Any]] = {}
    for fn in os.listdir(tpl_dir):
        if fn == "_index.json" or not fn.endswith(".json"):
            continue
        action = fn[:-5]
        d = json.load(open(os.path.join(tpl_dir, fn), encoding="utf-8"))
        nodes = d if isinstance(d, list) else [d]
        tpls[action] = nodes[0]
    return tpls


def load_definition(path: str) -> Any:
    with open(os.path.join(DEF_DIR, path), encoding="utf-8") as fh:
        return json.load(fh)


def load_entity(dto_short: str) -> dict[str, Any]:
    """加载实体定义（definitions/entities/<dto>.json），含 attributes/md5/entity/relationEntityId。"""
    return load_definition(f"entities/{dto_short}.json")


class NodeBuilder:
    """按链路顺序生成节点，维护符号表。"""

    def __init__(self, app_id: str, app_name: str, tpl_dir: str = TPL_DIR):
        self.app_id = app_id
        self.app_name = app_name
        self.templates = load_templates(tpl_dir)
        self.symtab: dict[str, dict[str, Any]] = {}  # output_name -> 出参信息
        self.nodes: list[dict[str, Any]] = []
        # ★ 稳定 id 种子：composer.step() 每次进入某个别名时设成该别名。
        #   同一张逻辑图重复 compose → nodeId / 出参名 / 引用名完全一致，
        #   重发等于「原地更新」而不是「整图换节点」。
        self.node_key: str | None = None
        self._key_seq: dict[tuple[str, str], int] = {}

    # ---- 符号表 ----
    def register(self, node: dict[str, Any]) -> dict[str, Any]:
        out = node.get("output")
        if out and out.get("name"):
            self.symtab[out["name"]] = {
                "nodeId": node.get("nodeId"),
                "dataType": out.get("dataType"),
                "javaType": out.get("javaType"),
                "dtoFullName": out.get("id"),
                "caption": out.get("desc"),
                "actionType": node.get("actionType"),
                "type": out.get("type"),
            }
        return node

    def output_name(self, node: dict[str, Any]) -> str | None:
        out = node.get("output")
        return out.get("name") if out else None

    # ---- 基础 ----
    def _new_id(self, action: str) -> str:
        """节点 id。有别名种子时按 (action, alias, 第几次) 派生，可重复；否则随机。"""
        key = self.node_key
        if key:
            n = self._key_seq.get((key, action), 0)
            self._key_seq[(key, action)] = n + 1
            seed = "%s|%s|%d" % (action, key, n)
            return "%s_%s" % (action, hashlib.md5(seed.encode("utf-8")).hexdigest()[:6])
        return f"{action}_{uuid.uuid4().hex[:6]}"

    def _app_ref(self, in_app: bool = True, app_id: str | None = None,
                 app_name: str | None = None, caption: str = "") -> dict[str, Any]:
        return {
            "appId": app_id or (self.app_id if in_app else None),
            "appName": app_name or (self.app_name if in_app else None),
            "caption": caption, "inApp": in_app, "udcApp": in_app,
            "dynamicDependency": False,
        }

    def build(self, action: str, caption: str | None = None, **overrides) -> dict[str, Any]:
        """从模板取骨架，替换 nodeId + output.name，应用 overrides。"""
        if action not in self.templates:
            raise KeyError(f"模板缺失: {action}（先在 node_templates/ 补或单独构造）")
        node = copy.deepcopy(self.templates[action])
        node["nodeId"] = self._new_id(action)
        if caption is not None:
            node["caption"] = caption
        # output.name 唯一化
        out = node.get("output")
        if isinstance(out, dict) and out.get("name"):
            out["name"] = "_" + node["nodeId"]
        # 应用 overrides（显式覆盖）
        for k, v in overrides.items():
            if v is not None:
                node[k] = v
        # ★ 与生产保存态同形：剥掉前端新建态残留字段
        #   （真实 643 条流程里从未出现的键，见 contract_gate.normalize_node）
        try:
            from components.udc.microflow.contract_gate import normalize_node
            normalize_node(node)
        except ImportError:
            pass
        self.register(node)
        self.nodes.append(node)
        return node

    def finish(self, trigger: dict[str, Any], end_node: dict[str, Any],
               input_dto: dict[str, Any] | None = None,
               output_dto: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "endNode": end_node,
            "output": output_dto,
            "input": input_dto,
            "sourceType": "PAGE",
            "trigger": trigger,
            "nodes": self.nodes,
        }
