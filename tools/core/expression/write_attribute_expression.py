#!/usr/bin/env python
"""表达式写入器（公用）—— 默认值 / 计算值 / 取值范围，跨域复用。

这是「表达式公用层」的可执行出口。各域不再自己拼 ExpressionSaveDto，
只声明 domain + purpose，其余由本工具完成：

    schema(paramType) → bind schemas → 组 tokens → check → transform → 写库 → 回读

用法
----
    # 默认值：字段 f12doc = dateToString(系统日期, "yyyy-MM-dd")
    python tools/core/expression/write_attribute_expression.py \
        --app-id <appId> --entity-id <entityId> --field f12doc \
        --purpose default_value \
        --expr 'dateToString(system.currentDate, "yyyy-MM-dd")' \
        --i-have-write-authorization

    # 计算值：字段 f04bigint = f03int + f03int
    ... --field f04bigint --purpose calculated_value \
        --expr 'f03int + f03int'

    # 只校验不写（check + transform 都无副作用）
    ... --dry-run

表达式语法（本工具支持的子集，覆盖常用场景）
-------------------------------------------
    字面量      123   "文本"  true / false
    变量        f03int / f04bigint        → 自动从 schema 取 paramId 并绑定 schemas
    系统变量    system.currentDate        → SYSTEM token（带 system. 前缀）
    函数        name(arg1, arg2)           → FUNCTION token，参数递归解析
    运算符      + - * / % == != > < >= <= & | !
    括号        ( ... )
    正负号      前置 -

★ 必须记住的三条硬约束（本工具已内置闸门）
  1. 变量必须绑定 schemas —— 只给 paramId 不够，会报 FORMULA_6058
  2. resultTypeInfo 必须等于字段 dataType —— 不等必报 FORMULA_6901
  3. design / runtime 必须成对写 —— runtime 置空会导致设计器有值、页面空白

★ 两条值链互斥
  默认值 → default_value_expr_design / _runtime
  计算值 → expression_design_data / _runtime + calculate=COMPUTE
  写计算值时会把 default 对显式清空（IGNORE_NULL 语义下 null 不清，要用空字符串）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.udc.expression import (  # noqa: E402
    bind_schemas, build_constant_token, build_function_token, build_operator_token,
    build_system_token, build_variable_token, check_binding,
)
from components.udc.expression.dto import (  # noqa: E402
    build_save_dto, result_type_for, summarize, validate_against_data_type,
    validate_save_dto,
)
from components.udc.expression.mapping import get_slot  # noqa: E402
from components.udc.expression.operators import operator_values  # noqa: E402

DB = "udc_test2"

# ---------------------------------------------------------------- 表达式解析
_TOKEN_RE = re.compile(r"""
    \s*(?:
        (?P<num>-?\d+(?:\.\d+)?)
      | (?P<str>"[^"]*"|'[^']*')
      | (?P<ident>[A-Za-z_][A-Za-z0-9_.]*)
      | (?P<op><=|>=|==|!=|&&|\|\||[-+*/%<>!&|(),])
    )""", re.VERBOSE)

_OP_MAP = {"&&": "&", "||": "|"}


def _lex(text: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m:
            if text[pos].isspace():
                pos += 1
                continue
            raise ValueError("表达式第 %d 字符无法解析: %r" % (pos, text[pos:pos + 12]))
        pos = m.end()
        kind = m.lastgroup
        val = m.group(kind)
        out.append((kind, val))
    return out


class _Parser:
    """递归下降。precedence: ! > */% > +- > compare > & > |"""

    def __init__(self, tokens, var_resolver, schema_roots):
        self.t = tokens
        self.i = 0
        self.var_resolver = var_resolver   # name -> paramId
        self.roots = schema_roots

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def accept(self, val):
        if self.peek()[1] == val:
            self.i += 1
            return True
        return False

    def parse(self):
        node = self.parse_or()
        if self.i != len(self.t):
            raise ValueError("表达式未消费完，停在 %r" % (self.peek(),))
        return node

    def parse_or(self):
        node = self.parse_and()
        while self.peek()[1] == "|":
            self.take()
            node = ("bin", "|", node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_cmp()
        while self.peek()[1] == "&":
            self.take()
            node = ("bin", "&", node, self.parse_cmp())
        return node

    def parse_cmp(self):
        node = self.parse_add()
        while self.peek()[1] in ("==", "!=", ">", "<", ">=", "<="):
            op = self.take()[1]
            node = ("bin", op, node, self.parse_add())
        return node

    def parse_add(self):
        node = self.parse_mul()
        while self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            node = ("bin", op, node, self.parse_mul())
        return node

    def parse_mul(self):
        node = self.parse_unary()
        while self.peek()[1] in ("*", "/", "%"):
            op = self.take()[1]
            node = ("bin", op, node, self.parse_unary())
        return node

    def parse_unary(self):
        if self.peek()[1] == "!":
            self.take()
            return ("un", "!", self.parse_unary())
        if self.peek()[1] == "-":
            self.take()
            return ("un", "-", self.parse_unary())
        return self.parse_atom()

    def parse_atom(self):
        kind, val = self.take()
        if val == "(":
            node = self.parse_or()
            if not self.accept(")"):
                raise ValueError("括号不匹配")
            return node
        if kind == "num":
            return ("const", val)
        if kind == "str":
            # ★ 第三个元素标记「这是字符串字面量」——数字/字符串在 AST 里
            #   原本都是 ("const", v)，下游无法区分，导致字符串常量被当成数字。
            return ("const", val[1:-1], True)
        if kind == "ident":
            if val in ("true", "false"):
                return ("bool", val)
            if self.peek()[1] == "(":
                self.take()
                args = []
                if self.peek()[1] != ")":
                    args.append(self.parse_or())
                    while self.accept(","):
                        args.append(self.parse_or())
                if not self.accept(")"):
                    raise ValueError("函数 %s 缺右括号" % val)
                return ("fn", val, args)
            return ("var", val)
        raise ValueError("意外的 token: %r" % (val,))


def _to_tokens(node, var_resolver, sys_desc=None,
               entity: tuple[str, str] | None = None,
               field_desc: dict | None = None,
               _idx: list | None = None) -> list[dict]:
    """AST → token 列表（扁平序列，函数参数走 subOps）。

    sys_desc: 系统变量 name → 中文描述。传了就用中文 desc，
              让 expressionTranslation 显示成「日期转文本(系统日期,...)」
              而不是「日期转文本(日期转文本(system.currentDate,...)」。
    entity  : (实体名, 实体标题)。★★ 必须传 —— 实体字段 token 的 value 要是
              "实体名.字段名"，desc 要是 "实体标题.字段标题"。只给短名会过
              check/transform，但页面回显报 FORMULA_6058（见 schema_binding）。
    field_desc: 字段 code → 字段标题。
    _idx    : 共享的序号计数器（平台侧 g_l_index，从 1 开始）。
    """
    sys_desc = sys_desc or {}
    field_desc = field_desc or {}
    if _idx is None:
        _idx = [0]

    def _next_idx():
        _idx[0] += 1
        return _idx[0]

    def rec(n):
        return _to_tokens(n, var_resolver, sys_desc, entity, field_desc, _idx)

    kind = node[0]
    if kind == "const":
        v = str(node[1])
        # ★ 字符串字面量必须带引号，否则 transform 按数字推断类型：
        #   textToLong("123") 传裸 123 → FORMULA_6158 期望 STRING 实际 INTEGER
        #   node[2] == True 来自 lex 的 str token；数字常量不带这个标记，
        #   所以 fInt + 1 里的 1 不会被加引号。
        if len(node) > 2 and node[2]:
            v = '"%s"' % v
        return [build_constant_token(v)]
    if kind == "bool":
        return [build_operator_token(node[1], node[1])]
    if kind == "var":
        name = node[1]
        if name.startswith("system."):
            return [build_system_token(name, sys_desc.get(name, name))]
        pid = var_resolver(name)
        ent_name, ent_desc = entity if entity else (None, None)
        return [build_variable_token(
            pid, name, field_desc.get(name, name),
            entity_name=ent_name, entity_desc=ent_desc, index=_next_idx())]
    if kind == "fn":
        name, args = node[1], node[2]
        sub_ops = [rec(a) for a in args]
        return [build_function_token(name, name, sub_ops)]
    if kind == "bin":
        return rec(node[2]) + [build_operator_token(node[1], node[1])] + rec(node[3])
    if kind == "un":
        return [build_operator_token(node[1], node[1])] + rec(node[2])
    raise ValueError("未知 AST 节点 %r" % (kind,))


def _load_system_descriptions(client) -> dict[str, str]:
    """从 preset/list 取系统变量 name → description 映射。

    只为让 expressionTranslation 可读；取不到不影响功能（降级成 name）。
    """
    try:
        _, d = _post(client, "/service/udc/expression/preset/list",
                     {"terminalSupportType": "BACKEND"})
        groups = ((d.get("data") or {}).get("content") or {}).get("presetVariableInfo") or []
        out = {}
        for g in groups:
            for it in (g.get("items") or []):
                nm = it.get("name")
                if nm:
                    out[nm] = it.get("description") or nm
        return out
    except Exception:
        return {}


# ---------------------------------------------------------------- 基础设施
def _env():
    p = Path(r"<HERMES_HOME>\skills\seeyon\01-platform\seeyon-low-code-environment\.env")
    out = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, sep, v = line.partition("=")
            if sep:
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _db():
    from providers.mysql_readonly import MySQLConnectionAdapter
    e = _env()
    return MySQLConnectionAdapter(host=e.get("SEEYON_DB_HOST", ""),
                                  port=e.get("SEEYON_DB_PORT") or 3306,
                                  user=e.get("SEEYON_DB_USERNAME", ""),
                                  password=e.get("SEEYON_DB_PASSWORD", ""))


def _client(port: int):
    from providers.cdp import CdpClient
    c = CdpClient(port, allow_network=True, timeout=120)
    c.connect(url_substr="lowcode-test2")
    return c


def _post(client, path, body):
    js = ('(async () => { const r = await fetch(' + json.dumps(path) + ', '
          '{method:"POST", credentials:"include", '
          'headers:{"Content-Type":"application/json","Accept":"application/json"}, '
          'body: ' + json.dumps(json.dumps(body, ensure_ascii=False)) + '}); '
          'const t = await r.text(); return JSON.stringify({http:r.status, body:t}); })()')
    raw = json.loads(client.evaluate(js, await_promise=True))
    try:
        return raw["http"], json.loads(raw["body"])
    except Exception:
        return raw["http"], {"_raw": raw["body"][:400]}


def _find(nodes, name):
    for n in nodes:
        if n.get("name") == name:
            return n
        r = _find(n.get("children") or n.get("properties") or [], name)
        if r:
            return r
    return None


# ---------------------------------------------------------------- 主流程
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-id", required=True)
    ap.add_argument("--entity-id", required=True)
    ap.add_argument("--field", required=True, help="字段 name，如 f12doc")
    ap.add_argument("--purpose", required=True,
                    choices=["default_value", "calculated_value"])
    ap.add_argument("--expr", required=True, help="表达式文本")
    ap.add_argument("--terminal", default="BACKEND")
    ap.add_argument("--port", type=int, default=9250)
    ap.add_argument("--dry-run", action="store_true", help="只 check + transform，不写库")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    a = ap.parse_args()

    if not a.dry_run and not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization（或先用 --dry-run）")
        return 1

    slot = get_slot("entity", a.purpose)
    db = _db()
    row = db.query(
        f"SELECT id, name, caption, data_type FROM {DB}.udc_attribute "
        f"WHERE entity_id=%s AND name=%s", (a.entity_id, a.field))
    if not row:
        print("字段 %s 不存在（entity_id=%s）" % (a.field, a.entity_id))
        return 1
    f = row[0]
    print("字段: %s / %s  类型=%s  id=%s"
          % (f["name"], f["caption"], f["data_type"], f["id"]))

    try:
        expect_rt = result_type_for(f["data_type"])
    except ValueError as exc:
        print("❌ %s" % exc)
        return 1
    print("目标 resultTypeInfo: %s（由 dataType=%s 决定）" % (expect_rt, f["data_type"]))

    client = _client(a.port)
    try:
        # 1 schema
        _, d = _post(client, "/service/udc/expression/schema",
                     {"ids": [int(a.entity_id)], "paramType": slot.param_type,
                      "upsource": True, "serverName": "udc"})
        roots = (d.get("data") or {}).get("content") or []
        if d.get("code") != "BOOT_0000" or not roots:
            print("❌ schema 失败: %s" % json.dumps(d, ensure_ascii=False)[:300])
            return 1
        print("schema: %d 个根节点" % len(roots))

        # 2 解析表达式 → tokens
        def resolver(name):
            n = _find(roots, name)
            if not n:
                raise ValueError("schema 里没有字段 %r" % name)
            pid = (n.get("uniformityParams") or {}).get("paramId")
            if pid is None:
                raise ValueError("字段 %r 缺 paramId" % name)
            return pid

        ast = _Parser(_lex(a.expr), resolver, roots).parse()
        sys_desc = _load_system_descriptions(client) if "system." in a.expr else {}
        # ★ 实体上下文：字段 token 必须带 "实体.字段" 点路径，否则页面回显报 FORMULA_6058
        ent = None
        for root in roots or []:
            if (root.get("uniformityParams") or {}).get("paramCategory") == "Entity":
                ent = (root.get("name"), root.get("description") or root.get("name"))
                break
        if ent is None and roots:
            ent = (roots[0].get("name"), roots[0].get("description") or roots[0].get("name"))
        fdesc = {}

        def _collect(nodes, depth=0):
            if depth > 8:
                return
            for n in nodes or []:
                up = n.get("uniformityParams") or {}
                if up.get("paramCategory") == "Attr" and n.get("name"):
                    fdesc[n["name"]] = n.get("description") or n["name"]
                _collect(n.get("properties") or n.get("children") or [], depth + 1)

        _collect(roots)
        tokens = _to_tokens(ast, resolver, sys_desc, entity=ent, field_desc=fdesc)
        print("tokens: %s" % summarize({"tokens": tokens,
                                         "resultTypeInfo": expect_rt,
                                         "terminalSupportType": a.terminal}))

        # 3 绑定 schemas（FORMULA_6058 的唯一正解）
        schemas = bind_schemas(tokens, roots)
        print("schemas 绑定: %d 个 %s" % (len(schemas), [s.get("name") for s in schemas]))
        errs = check_binding(tokens, schemas)
        if errs:
            for e in errs:
                print("❌ %s" % e)
            return 1

        dto = build_save_dto(tokens, schemas=schemas, result_type=expect_rt,
                             terminal=a.terminal)
        errs = validate_save_dto(dto) + validate_against_data_type(dto, f["data_type"])
        print("本地校验: %s" % (errs or "OK"))
        if errs:
            return 1

        # 4 check
        _, r = _post(client, "/service/udc/expression/check", dto)
        ok = r.get("code") == "BOOT_0000" and (r.get("data") or {}).get("content") is True
        print("check: code=%s content=%s msg=%s"
              % (r.get("code"), (r.get("data") or {}).get("content"),
                 str(r.get("message"))[:80]))
        if not ok:
            print("❌ check 未通过，失败即停")
            return 1

        # 5 transform
        _, r = _post(client, "/service/udc/expression/transform", dto)
        ct = (r.get("data") or {}).get("content") or {}
        dd, rt = ct.get("designData") or {}, ct.get("runtimeData") or {}
        if r.get("code") != "BOOT_0000" or not rt.get("executableExpr"):
            print("❌ transform 失败: %s" % json.dumps(r, ensure_ascii=False)[:300])
            return 1
        print("transform: translation=%r runtime %d 字符"
              % (dd.get("expressionTranslation"), len(rt["executableExpr"])))
        if "context" not in dd:
            print("❌ designData 缺 context 键 —— 会让检测器 NPE，拒绝写入")
            return 1

        if a.dry_run:
            print("\n[dry-run] 不写库。designData 键: %s" % list(dd.keys()))
            return 0

        # 6 写库
        body = {"appId": a.app_id, "entityId": a.entity_id, "id": f["id"],
                "name": f["name"], "caption": f["caption"], "dataType": f["data_type"]}
        if slot.purpose == "calculated_value":
            body["expressionDesignData"] = json.dumps(dd, ensure_ascii=False)
            body["expressionRuntimeData"] = json.dumps(rt, ensure_ascii=False)
            body["calculate"] = "COMPUTE"
            body["defaultValueExpressionDesignData"] = ""
            body["defaultValueExpressionRuntimeData"] = ""
        else:
            body["defaultValueExpressionDesignData"] = json.dumps(dd, ensure_ascii=False)
            body["defaultValueExpressionRuntimeData"] = json.dumps(rt, ensure_ascii=False)
            body["defaultValueIsChange"] = False

        q = ("mutation graphqlLoader ($params0: udcEntityAttributeUpdatePostInputBody) "
             "{ data0: udcEntityAttributeUpdatePost(body: $params0) "
             "{ code data { content } message status } }")
        _, r = _post(client, "/service/udc/graphql?udcEntityAttributeUpdatePost",
                     {"query": q, "variables": {"params0": body}})
        d0 = (r.get("data") or {}).get("data0") or {}
        print("写库: code=%s status=%s msg=%s"
              % (d0.get("code"), d0.get("status"), str(d0.get("message"))[:80]))
        if d0.get("code") != "BOOT_0000" or d0.get("status") != 0:
            return 1
    finally:
        client.close()

    # 7 回读
    r = db.query(
        f"SELECT name, calculate, default_value_caption, "
        f"default_value_expr_design, default_value_expr_runtime, "
        f"expression_design_data, expression_runtime_data "
        f"FROM {DB}.udc_attribute WHERE id=%s", (f["id"],))[0]
    print("\n回读:")
    for k, v in r.items():
        if k == "name":
            continue
        if v in (None, ""):
            print("  %-30s 空" % k)
        elif isinstance(v, str) and len(v) > 40 and v.startswith("{"):
            try:
                j = json.loads(v)
                print("  %-30s %d 字符  translation=%r"
                      % (k, len(v), j.get("expressionTranslation")))
            except Exception:
                print("  %-30s %d 字符" % (k, len(v)))
        else:
            print("  %-30s %r" % (k, v))
    db.close()
    print("\n✅ 完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
