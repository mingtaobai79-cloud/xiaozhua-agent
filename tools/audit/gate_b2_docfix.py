# -*- coding: utf-8 -*-
"""B2 文档 + EVIDENCE 闸门（round3 升级版，替换 round2 版）

设计原则（auditor REVIEW_FEEDBACK-AC707DB-ACK 的 N1-N3 反例驱动）：
1. 从 EVIDENCE 反解：类型/键数/计数一律从 JSON 实测（isinstance），不 grep 正文数字
2. 负向断言：错口径必须"不存在"（'56 行 vse 被写过' 必须消失）
3. 分叉断言：domain_id 那句须同时出现 action_type + 字段 id + 实体 id，防被改成"任何值都不可用"
4. 无 sys.exit 的检查不算闸门：本脚本用退出码表达
"""
import json, pathlib, sys, re

DOC = pathlib.Path(r"<SEEYON_AGENT_ROOT>/docs/audit/entity-field-matrix/SLICE-B2-INTEGER-live.md")
EV_CREATE = pathlib.Path(r"<SEEYON_AGENT_ROOT>/docs/audit/entity-field-matrix/EVIDENCE-batch-contract-live.json")
EV_UPDATE = pathlib.Path(r"<SEEYON_AGENT_ROOT>/docs/audit/entity-field-matrix/EVIDENCE-batch-update-live.json")

txt = DOC.read_text(encoding="utf-8")
# 契约正文 = §十（round3 收口说明，会引用错口径做对照）之前的部分；负向断言只查正文
BODY = txt.split("## 十、round3 收口")[0]
fails = []


def need(label, cond, extra=""):
    if not cond:
        fails.append(label + " " + str(extra))
    print(("PASS " if cond else "FAIL ") + label + ((" | " + str(extra)) if (not cond and extra) else ""))


# ============ A. 从 EVIDENCE 反解（不 grep 正文） ============
ev1 = json.load(open(EV_CREATE, encoding="utf-8"))
ev2 = json.load(open(EV_UPDATE, encoding="utf-8"))


def all_dtos(ev):
    out = []
    for g in ev["request_full"]["variables"]["params0"]:
        for d in g["attributeDtoList"]:
            out.append(d)
    return out


d1, d2 = all_dtos(ev1), all_dtos(ev2)
dtos = d1 + d2
need("A0 DTO 总数=30", len(dtos) == 30, "got %d" % len(dtos))

for k in ["id", "entityId", "appId", "uniqueKey", "dataType", "actionType"]:
    vals = [d[k] for d in dtos if k in d and d[k] is not None]
    ok = bool(vals) and all(isinstance(v, str) for v in vals)
    bad = [type(v).__name__ for v in vals if not isinstance(v, str)][:3]
    need("A1 %s 恒 str (n=%d)" % (k, len(vals)), ok, bad)

for k in ["updateTime", "maxLength", "minLength", "orderNo"]:
    vals = [d[k] for d in dtos if k in d and d[k] is not None]
    ok = bool(vals) and all(isinstance(v, int) and not isinstance(v, bool) for v in vals)
    bad = [type(v).__name__ for v in vals if not isinstance(v, int)][:3]
    need("A2 %s 恒 int (n=%d)" % (k, len(vals)), ok, bad)

ct_int = [d for d in dtos if isinstance(d.get("createTime"), int)]
ct_str = [d for d in dtos if isinstance(d.get("createTime"), str)]
need("A3a createTime int 条数=29", len(ct_int) == 29, "got %d" % len(ct_int))
need("A3b createTime str 条数=1", len(ct_str) == 1, "got %d" % len(ct_str))
need("A3c 唯一 str 那条是 ADD",
     bool(ct_str) and ct_str[0].get("actionType") == "ADD",
     ct_str[0].get("actionType") if ct_str else None)

dv = [d.get("defaultValue") for d in dtos]
n_none = sum(1 for v in dv if v is None)
n_str = sum(1 for v in dv if isinstance(v, str))
n_int = sum(1 for v in dv if isinstance(v, int) and not isinstance(v, bool))
need("A4a defaultValue None=22", n_none == 22, "got %d" % n_none)
need("A4b defaultValue str=7", n_str == 7, "got %d" % n_str)
need("A4c defaultValue int=1", n_int == 1, "got %d" % n_int)

pairs = [(d.get("uniqueKey"), d.get("id")) for d in dtos if d.get("id") is not None]
eq = sum(1 for uk, i in pairs if str(uk) == str(i))
need("A5 uniqueKey==id 全等 29/29", eq == len(pairs) == 29, "eq=%d/%d" % (eq, len(pairs)))

adds = [d for d in d1 if d.get("actionType") == "ADD"]
add_kc = sorted({len(x) for x in adds})
need("A6a ADD 恰 1 条且 26 键", len(adds) == 1 and add_kc == [26], "n=%d keys=%s" % (len(adds), add_kc))
short = [d for d in d2 if len(d) == 36]
need("A6b UPDATE-精简 36 键 恰 1 条", len(short) == 1, "got %d" % len(short))
full = [d for d in dtos if len(d) == 76]
need("A6c UPDATE-全量 76 键 28 条", len(full) == 28, "got %d" % len(full))

resp = ev2["b2IntField_dto_response"]["dto"]
need("A7a 响应 maxLength=10", resp.get("maxLength") == 10, repr(resp.get("maxLength")))
need("A7b 响应 minLength=0", resp.get("minLength") == 0, repr(resp.get("minLength")))
need("A7c 响应 orderNo=17", resp.get("orderNo") == 17, repr(resp.get("orderNo")))
need("A7d 响应 vse=None", resp.get("valueScopeExpression") is None)
need("A7e 补键 41 个",
     ev2["server_side_reconciliation"]["keys_only_in_response"]["count"] == 41,
     ev2["server_side_reconciliation"]["keys_only_in_response"]["count"])

req = ev2["b2IntField_dto_request"]["dto"]
need("A8a 请求无 maxLength", "maxLength" not in req)
need("A8b 请求无 minLength", "minLength" not in req)
need("A8c 请求无 valueScopeExpression", "valueScopeExpression" not in req)

# ============ B. 文档断言（语义绑定 + 负向 + 分叉） ============
# ===== round4 升级：B 组从「关键词共现」改为「用 A 组反解结果生成期望文本再比对」 =====
# 教训（auditor 11:54 + main 12:11）：只验关键词共现时，删掉 updateTime / 删掉 type=1 分支
# 换一种不撞精确词串的写法就能溜过。改为：先算出完整成员集合，再要求正文**逐成员在场且不跨组**。

# 反解：按 **每条 DTO 上该键的实际类型** 归组。
# 注意 createTime 是特例（29 条 int + ADD 那条 str），必须双向处理：
#   createTime_int_guard = 除 ADD 外全部 int ⇒ 归 int 组
#   同时它「在 ADD 那条是 str」是唯一例外，不能因此把它整体挪进 str 组（R1half 的漏洞点）
ALL_KEYS = set()
for d in dtos:
    ALL_KEYS |= set(d)

STR_KEYS, INT_KEYS, MIXED_KEYS = [], [], []
for k in sorted(ALL_KEYS):
    vals = [d[k] for d in dtos if k in d and d[k] is not None]
    if not vals:
        continue
    is_str = all(isinstance(v, str) for v in vals)
    is_int = all(isinstance(v, int) and not isinstance(v, bool) for v in vals)
    if is_str and not is_int:
        STR_KEYS.append(k)
    elif is_int and not is_str:
        INT_KEYS.append(k)
    else:
        MIXED_KEYS.append(k)

# 闸门只对「稳定单型」键做组断言；混合型（如 createTime）单列，用分母断言兜住
need("B0a 反解出稳定 str 键组（非空）", len(STR_KEYS) >= 6, STR_KEYS)
need("B0b 反解出稳定 int 键组（非空）", len(INT_KEYS) >= 4, INT_KEYS)
need("B0c ★ 两稳定组交集必须为空（集合级，不是文本级）",
     not (set(STR_KEYS) & set(INT_KEYS)), sorted(set(STR_KEYS) & set(INT_KEYS)))
need("B0d 混合型键已单列（createTime）", "createTime" in MIXED_KEYS, MIXED_KEYS)

# ① 期望文本由反解生成：str 组整句 + int 组整句，两组成员必须各自完整、且不得交叉
def _group_line(keys):
    return "、".join("`%s`" % k for k in keys)

# ★ round4 核心：从文档「恒为 str」/「恒为 int」两行**解析出键集合**，再与反解集合比对。
# 这是 auditor R1half 的闭合点：旧实现只在段内文本里找 int 组成员，
# 有人往 str 组追加 createTime 时，两行自相矛盾却因"int 段还在"而通过。
m_str = re.search(r"\*\*恒为 str\*\*[：:]([^\n]*)", txt)
m_int = re.search(r"\*\*恒为 int\*\*[：:]([^\n]*)", txt)
seg_str = m_str.group(1) if m_str else ""
seg_int = m_int.group(1) if m_int else ""
need("B1a-1 存在「恒为 str」段", bool(seg_str))
need("B1a-2 存在「恒为 int」段", bool(seg_int))


def parse_keys(seg):
    """从一段文本里抽反引号包住的字段名（忽略 29/30 这类分母）。"""
    return set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", seg))


doc_str = parse_keys(seg_str)
doc_int = parse_keys(seg_int)

# c) 缺口1 闭合：两行解析出的集合交集必须为空（这是 R1half 的唯一拦点）
overlap = doc_str & doc_int
need("B1a-3 ★ str段/int段 解析集合交集必须为空（R1half 闭合）",
     not overlap, sorted(overlap))

# 与反解比对：文档声明的是**代表性键集**，不要求列全部键。
# 判据改为三件事（这才是反解比对，而不是关键词共现）：
#   ① 文档 str 段每个键都必须在反解里是「稳定 str」（错归类被抓）
#   ② 文档 int 段每个键都必须在反解里是「稳定 int」或混合型且以 int 为主导（错归类被抓）
#   ③ 反解里的稳定 str/int 组代表键必须都在本文档声明到场（删键被抓）
STR_UNIVERSE = set(STR_KEYS)
INT_UNIVERSE = set(INT_KEYS) | set(MIXED_KEYS)

wrong_str = sorted(doc_str - STR_UNIVERSE)
need("B1a-4 str 段每个键反解均为稳定 str（错归类被抓）", not wrong_str,
     {"不在稳定str集": wrong_str})

wrong_int = sorted(doc_int - INT_UNIVERSE)
need("B1a-5 int 段每个键反解均为稳定 int/混合型（错归类被抓）", not wrong_int,
     {"不在稳定int集": wrong_int})

# 代表键必须到场（删 updateTime / 删 actionType 会被抓）
REQUIRED_STR = {"id", "entityId", "appId", "uniqueKey", "dataType", "actionType"}
REQUIRED_INT = {"createTime", "updateTime", "maxLength", "minLength", "orderNo"}
miss_str = sorted(REQUIRED_STR - doc_str)
miss_int = sorted(REQUIRED_INT - doc_int)
need("B1a-5b str 段代表键全部到场（删 actionType 会被抓）", not miss_str, miss_str)
need("B1a-5c int 段代表键全部到场（删 updateTime 会被抓）", not miss_int, miss_int)

# 交叉污染（在集合级已被 B1a-3 覆盖，这里再给一条可读性更强的诊断）
need("B1a-6 str 段不得出现 int 组键 / int 段不得出现 str 组键",
     not (doc_str & INT_UNIVERSE) and not (doc_int & STR_UNIVERSE),
     {"int键混入str段": sorted(doc_str & INT_UNIVERSE),
      "str键混入int段": sorted(doc_int & STR_UNIVERSE)})

# ★ auditor 最小硬判据（round2→round3 反复出错的那个键）：createTime 必须在 int 段、且不在 str 段。
# 这条不依赖任何推断，直接读两行解析结果 —— 作为 B1a-3/4/5 之外的独立兜底。
need("B1a-6b ★ createTime 必须在 int 段且不在 str 段（auditor 最小硬判据）",
     ("createTime" in doc_int) and ("createTime" not in doc_str),
     {"in_int": "createTime" in doc_int, "in_str": "createTime" in doc_str})

# createTime 两位数分母必须与反解一致（29/30）
need("B1a-7 createTime 分母表述与反解一致 (%d/%d)" % (len(ct_int), len(dtos)),
     "`createTime`(%d/%d)" % (len(ct_int), len(dtos)) in txt,
     "expect `createTime`(%d/%d)" % (len(ct_int), len(dtos)))

need("B1b ADD 例外表述", "`createTime` 在**ADD 那一条**传 **str**" in txt)
need("B1c 负向：旧错句(把 createTime 归到 str 组)已删",
     "`id` / `entityId` / `appId` / `createTime` 是 **str**" not in txt)

need("B2a 三态数字", "`null` **22** / `str` **7** / `int` **1**" in txt)
need("B2b 三态并存结论", "三态并存" in txt)

need("B3a 3483", "NULL = 3483" in txt)
need("B3b 空串 55", "空串 '' = 55" in txt)
need("B3c 非空 1", "非空 = 1" in txt)
_neg = txt.replace("此前写「56 行 vse 被写过」口径错", "")
# 正文里有一处自引用（"此前写「56 行 vse 被写过」口径错"），先剔自引用再判
need("B3d 负向：正口径'56 行 vse 被写过'已消失(正文)",
     "56 行 vse 被写过" not in BODY.replace("此前写「56 行 vse 被写过」口径错", ""))
need("B3e 区分句", "「字段被初始化」≠「值域被配过」" in txt)
need("B3f 负向：'非空 vse = 56' 不存在(正文)", "非空 vse = 56" not in BODY)
need("B3g 正口径 '非空 vse = 1 例' 存在", "**非空 vse = 1 例**" in txt)
need("B1d 负向：'恒为 str**：`createTime`' 不存在",
     "**恒为 str**：`createTime`" not in txt)


m = re.search(r"禁用单锚：`domain_id`.*?§2\.4\.1）", txt, re.S)
seg = m.group(0) if m else ""
need("B4a 分叉段落存在", bool(seg))

# ④ round4 升级：两分支各自「完整句式」，不是关键词共现
# 期望：type=1 → 字段 id ；type=3 → 实体 id（方向不可互换）
BRANCH = [
    ("type=1", "字段 id", "实体 id"),
    ("type=3", "实体 id", "字段 id"),
]


def branch_binding_ok(branch_key, want, forbidden):
    """d) 缺口2 闭合（R4b）：校验分支**绑定关系**，不是字样共现。

    要求：
      1. 必须存在 `type=N ... → want` 的完整箭头句式
      2. 该分支的**同一窗口内**不得把 forbidden 当作落点（R4b 的「也」「同样」类挂错锚）
    返回 (ok, 诊断)
    """
    arrow = re.compile(re.escape(branch_key) + r"[^\n]{0,60}?(?:→|->|＝|=)\s*\**\s*" + re.escape(want))
    if not arrow.search(seg):
        return False, "缺 `%s ... → %s` 箭头句式" % (branch_key, want)

    # 该分支出现的每个位置，取到下一个分支键/换行前的窗口，检查有没有错挂 forbidden
    for mm in re.finditer(re.escape(branch_key), seg):
        tail = seg[mm.start():]
        # 窗口止于下一个 type=N 或空行
        nxt = re.search(r"`?type=[13]`?", tail[1:])
        win = tail[: (nxt.start() + 1) if nxt else min(len(tail), 160)]
        if want not in win:
            continue
        # 错挂检测：窗口内出现 forbidden 且不在否定语境
        if re.search(re.escape(forbidden), win):
            pre = win[max(0, win.find(forbidden) - 12): win.find(forbidden)]
            if not re.search(r"[不非未]|而不是|禁止|不能", pre):
                return False, "`%s` 分支错挂 `%s`：%s" % (branch_key, forbidden, win.strip()[:90])
        return True, None
    return False, "未找到含 `%s` 的 `%s` 分支窗口" % (want, branch_key)


if seg:
    need("B4b 含 action_type（唯一可靠锚之一）", "action_type" in seg)
    need("B4c 含 log_element/时间窗+module+sub_module 类锚", ("log_element" in seg) or ("module" in seg))
    for bk, want, forb in BRANCH:
        ok, diag = branch_binding_ok(bk, want, forb)
        need("B4d %s 分支绑定：→ %s 且未错挂 %s（R4b 闭合）" % (bk, want, forb), ok, diag)
    need("B4e 两分支都在场", ("type=1" in seg) and ("type=3" in seg))
    need("B4f 负向：明确否定'任何值都不可用'", '不能写"domain_id 任何值都不可用"' in seg)
need("B4g 负向：裸句'禁用 domain_id=字段id；'已消失", "禁用 `domain_id=字段id`；" not in txt)
# 注意：§10.2 注入结果表里字面写着该串（描述注入用例，非断言）——须先剔除描述区再判
_txt_no_selftest = re.sub(r"\*\*负向注入验证.*?(?=\n### |\n## |\Z)", "", txt, flags=re.S)
need("B4h 负向：不得把 domain_id 说成「永不使用任何值」（自测描述区豁免）",
     "永不使用任何值" not in _txt_no_selftest)

# B4i：新增式漂移的结构防护（R6 类）。
# 「新增一句没见过的错话」无法用负向字符串穷举，改为约束段落**必须**以分叉声明开头，
# 且在这句分叉声明之前不允许出现对 domain_id 的绝对化判断（任何值都不可用/一律/只能/永不）。
if seg:
    head = seg[: seg.find("type=1")] if "type=1" in seg else seg[:120]
    absolute = re.search(r"(任何值都不可用|一律(?!按时间窗)|只能|永不|完全不|毫无)", head)
    need("B4i 分叉声明之前不得出现对 domain_id 的绝对化断言（R6 类新增式漂移防护）",
         not absolute, {"head": head.strip()[:120], "hit": absolute.group(0) if absolute else None})
    need("B4j 段落必须以分叉（随 action_type）开局，不是先下绝对结论",
         bool(re.match(r"\s*`?domain_id`?\s*\*\*随\s*action_type\s*分叉", seg))
         or "随 action_type 分叉" in head)

    # B4k：R6 类——绝对化断言可能被塞在段落**前文**（seg 窗口之外）。
    # 故把 domain 段落的前 300 字一并纳入扫描（紧邻上下文才是同一话题）。
    _pre = txt[max(0, m.start() - 300): m.start()] if m else ""
    _abs_any = re.search(r"domain_id[^\n]{0,40}(任何值都不可用|一律|只能|永不|完全不|毫无)", _pre)
    need("B4k 段落前文不得出现对 domain_id 的绝对化断言（R6 类新增式漂移）",
         not _abs_any, {"pre_tail": _pre[-120:].strip(), "hit": _abs_any.group(0)[:80] if _abs_any else None})

need("B5a after 中间态声明", "after 列是前端提交/中间态，不等于落库值" in txt)
need("B5b min_length 3539/3539", "3539/3539" in txt)
need("B5c 字面 null 0 行", "字面 **0 行**" in txt)

need("B6a 撤回污染链仍在", "**该推断是错的，已撤回**" in txt)
need("B6b 旧污染断言不复现",
     "字段类型的 UPDATE 不写 `udc_operation_log`（或至少本次未写）" not in txt)
need("B6c 值域定性", "**定性：入口层未打开，不是能力层不支持。**" in txt)
need("B6d 反例失效申报", "D26 的「STRING 反例」已失效" in txt)
need("B6e 三档键集", "UPDATE-精简" in txt and "UPDATE-全量" in txt)
need("B6f 单样本限制", "一个样本" in txt)
need("B6g uniqueKey=id 表述", "不是随机串" in txt)

need("B7a CREATE 标 ADD/CREATE", ev1["_meta"].get("action") == "ADD/CREATE", ev1["_meta"].get("action"))
need("B7b UPDATE 标 UPDATE", ev2["_meta"].get("action") == "UPDATE")
need("B7c CREATE postDataLen=30003", ev1["_meta"]["postDataLen"] == 30003)
need("B7d UPDATE postDataLen=30259", ev2["_meta"]["requestBodyLen"] == 30259)
need("B7e CREATE ADD 26 键", ev1["b2IntField_add_dto"]["key_count"] == 26)
need("B7f 请求36键", ev2["b2IntField_dto_request"]["key_count"] == 36)
need("B7g 响应77键", ev2["b2IntField_dto_response"]["key_count"] == 77)

print()
if fails:
    print("GATE FAILED:", len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)

# ============ round4 注入模式：验证 B 组反解期望比对真能拦 ============
# 退出码语义：被拦=1 / 未命中(漏检)=2 / 锚点缺失=3
INJECTIONS = {
    # ===== auditor 验收单：4 条既有绑定（b 项，不得退步）=====
    "R1b": (r"\*\*恒为 int\*\*", "**恒为 str**"),                    # 抹掉 int 组 → 应 B1a-2/3/5 命中
    "R2": (r"`createTime`\(29/30\)", "`createTime`(30/30)"),          # 抹掉 ADD 例外 → B1a-7
    "R3": (r"\*\*非空 vse = 1 例\*\*", "**非空 vse = 56 例**"),        # → B3f/B3g
    "R4": (r'但\*\*也不能写"domain_id 任何值都不可用"\*\*', "但**可以**"),  # 删否定句 → B4f

    # ===== c) 缺口1：R1half（str 组追加 createTime，int 组保留）=====
    "R1half": (r"(\*\*恒为 str\*\*：`id`[^\n]*?`actionType`)", r"\1、`createTime`"),

    # ===== d) 缺口2：R4b（type=3 错挂字段id）=====
    "R4b": (r"`type=3`\(批量 UPDATE\) → \*\*实体 id\*\*",
            "`type=3`(批量 UPDATE) → **实体 id**（也用字段 id）"),

    # ===== e) 新增式漂移（auditor 允许降级，本轮已闭合，不降级）=====
    "R5": (r"\*\*恒为 int\*\*：", "**恒为 int**（STRING 专属形态）："),
    "R6": (r"禁用单锚：`domain_id`",
           "`domain_id` 任何值都不可用，一律按时间窗查。禁用单锚：`domain_id`"),

    # ===== 结构性：删锚点 / 交叉污染（自查用）=====
    "M1": (r"`updateTime`\(28/28\)、", ""),                            # 删 int 组成员
    "M2": (r"`type=1`\(CREATE\) → \*\*字段 id\*\*", "`type=1`(CREATE) 待查"),
    "M3": (r'不能写"domain_id 任何值都不可用"', "domain_id 永不使用任何值"),
    "M4": (r"`createTime` 在\*\*ADD 那一条\*\*传 \*\*str\*\*", "`createTime` 恒为 int"),
}

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "--inject":
    name = sys.argv[2]
    if name not in INJECTIONS:
        print("unknown injection:", name)
        sys.exit(3)
    old, new = INJECTIONS[name]
    raw = DOC.read_text(encoding="utf-8")
    if not re.search(old, raw):
        print(f"[INJECT {name}] ANCHOR-MISSING: {old!r}")
        sys.exit(3)
    DOC.write_text(re.sub(old, new, raw, count=1), encoding="utf-8")
    rc = 3
    try:
        import subprocess
        r = subprocess.run([sys.executable, str(pathlib.Path(__file__)), "--child"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        caught = r.returncode != 0
        print(f"[INJECT {name}] child exit = {r.returncode}  => {'CAUGHT(拦下)' if caught else 'MISSED(漏检)'}")
        for line in r.stdout.splitlines():
            if line.startswith("FAIL"):
                print("   " + line[:100])
        rc = 1 if caught else 2
    finally:
        DOC.write_text(raw, encoding="utf-8")
        assert DOC.read_text(encoding="utf-8") == raw, "restore mismatch"
        print(f"[INJECT {name}] restored byte-identical")
    sys.exit(rc)

print("GATE PASS  (%d chars doc, %d DTOs cross-checked)" % (len(txt), len(dtos)))
