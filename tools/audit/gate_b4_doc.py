# -*- coding: utf-8 -*-
"""B4 文档闸门：从 EVIDENCE 反解 + 负向断言（不靠词面 grep 正文数字）

设计原则（吸取 round3 教训）：
  1. 数字不硬编码在断言里，一律从 EVIDENCE / bundle 反解后与正文对齐
  2. 每个关键结论绑定「正口径 + 负口径」两条，单点断言会被同义改写绕过
  3. 负向断言限定在 BODY（去掉标题/fence 无关区），并做归一化后再匹配

用法：
  python tools/audit/gate_b4_doc.py            # 校验
  python tools/audit/gate_b4_doc.py --inject N1 # 注入场景
退出码 0 = PASS，1 = FAIL（注入场景应当 1）
"""
import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(r"<XIAOZHUA_AGENT_ROOT>")
B4 = REPO / "docs/audit/entity-field-matrix/B4-KEYCOUNT-ORIGIN.md"
B2 = REPO / "docs/audit/entity-field-matrix/SLICE-B2-INTEGER-live.md"
E1 = REPO / "docs/audit/entity-field-matrix/EVIDENCE-batch-contract-live.json"
E2 = REPO / "docs/audit/entity-field-matrix/EVIDENCE-batch-update-live.json"

fails = []


def need(label, cond, extra=""):
    if not cond:
        fails.append(label)
    print(("PASS " if cond else "FAIL ") + label + ((" | " + str(extra)) if (not cond and extra) else ""))


def rows(ev):
    return [d for g in ev["request_full"]["variables"]["params0"] for d in g["attributeDtoList"]]


# ---------- 从 EVIDENCE 反解（不 grep） ----------
e1 = json.load(open(E1, encoding="utf-8"))
e2 = json.load(open(E2, encoding="utf-8"))
cr, ur = rows(e1), rows(e2)
allrows = cr + ur
k76 = set([d for d in ur if len(d) == 76][0])
k36 = set([d for d in ur if len(d) == 36][0])
k26 = set([d for d in cr if d.get("actionType") == "ADD"][0])
resp = e2["b2IntField_dto_response"]["dto"]
core = set(allrows[0])
for d in allrows:
    core &= set(d)

n_core, n36, n76, n26, n77 = len(core), len(k36), len(k76), len(k26), len(resp)
srv_only = len(set(resp) - k76)
fe_only = len(k76 - set(resp))
n_diff = len(k76 - k36)
need("E1 反解: 76=%d 36=%d 26=%d 响应=%d" % (n76, n36, n26, n77),
     (n76, n36, n26, n77) == (76, 36, 26, 77))
need("E2 反解: core=%d, 76=77-%d+%d" % (n_core, srv_only, fe_only),
     n_core == 19 and 77 - srv_only + fe_only == 76 and srv_only == 5 and fe_only == 4)
need("E3 反解: 76-36 = %d" % n_diff, n_diff == 40)

# ---------- 从 bundle 资产反解 14 张类型表（供 A12-A18 期望值，不硬编码） ----------
ASSET = REPO / "docs/audit/entity-field-matrix/assets/bundle-type-default-tables.js.txt"
BUNDLE = pathlib.Path(r"<HERMES_HOME>/cache/scratch/src_redux_store_ts.14dc061e.js")
if ASSET.exists():
    bsrc = ASSET.read_text(encoding="utf-8", errors="replace")
elif BUNDLE.exists():
    bsrc = BUNDLE.read_text(encoding="utf-8", errors="replace")
else:
    raise SystemExit("bundle 源不可用：asset 与 cache 均缺失")


def _blk(anchor):
    i = bsrc.find(anchor)
    if i < 0:
        raise SystemExit("anchor not found: " + anchor)
    k = bsrc.find("{", i)
    depth = 0
    for j in range(k, len(bsrc)):
        if bsrc[j] == "{":
            depth += 1
        elif bsrc[j] == "}":
            depth -= 1
            if depth == 0:
                return bsrc[k:j + 1]
    raise SystemExit("block not closed: " + anchor)


def _tk(block, t):
    m = re.search(r"\[a\.%s\]:\{" % t, block)
    if not m:
        return None
    k = m.end() - 1
    depth = 0
    for j in range(k, len(block)):
        if block[j] == "{":
            depth += 1
        elif block[j] == "}":
            depth -= 1
            if depth == 0:
                return set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*:", block[k:j + 1]))
    return None


E_BLK = _blk('E={[a.String]:{dataType:"STRING"')
TYPES = ["String", "MultilineString", "Integer", "BigInteger", "Decimal", "Currency",
         "Date", "Time", "DateTime", "Boolean", "Enum", "CtpEnum", "Entity", "Attachment"]
E_TABS = {t: _tk(E_BLK, t) for t in TYPES}
IDENT_REL_G = {"guid", "id", "relationApp", "relationCode", "relationEntity",
               "relationEntityCategory", "relationEntityName", "system"}
base = core | IDENT_REL_G
need("E4 反解 14 张类型表 + base=27",
     all(E_TABS[t] is not None for t in TYPES) and len(base) == 27,
     [t for t in TYPES if E_TABS[t] is None])

b4 = B4.read_text(encoding="utf-8")
b2 = B2.read_text(encoding="utf-8")


def norm(t):
    return re.sub(r"[ \t\u3000]+", " ", t)


b4n, b2n = norm(b4), norm(b2)


def strip_injection_table(text):
    """去掉「注入实测/闸门修正史」整段：里面字面写着错误值（77−6+4 / → 已证 等），
    是**描述注入用例**而非断言，必须豁免。

    这是同坑第三次复发（B4 §七 / B2 §10.2 各一次）：任何人写"我注入了什么"都会撞自己的负向断言。
    故这里用「从注入小节标题起，到下个一级标题或分隔线止」的宽松范围，不再死跟某一版措辞。
    """
    text = re.sub(r"\*\*(?:B4 闸门|B2 闸门)?注入(?:场景)?实测.*?(?=\n## |\n---\s*\n## |\Z)",
                  "", text, flags=re.S)
    text = re.sub(r"> \*\*闸门自身修正史.*?(?=\n\n[^>]|\n## )", "", text, flags=re.S)
    return text


NEG_WORDS = ("不", "非", "未", "并非", "而不是", "不能")


def has_unnegated(text, pattern, window=8):
    """命中但前 window 字符内出现否定词的，视为引用/反证，不算违规。"""
    for m in re.finditer(pattern, text):
        pre = text[max(0, m.start() - window):m.start()]
        if not any(w in pre for w in NEG_WORDS):
            return True
    return False


def strip_quoted(text):
    """去掉引号内与删除线内容——旧错误表述只允许以「被引用/被更正」形态出现。"""
    text = re.sub(r"~~.+?~~", "", text, flags=re.S)
    for q in (r"“[^”]*”", r"「[^」]*」", r'"[^"]*"'):
        text = re.sub(q, "", text)
    return text


b4n = strip_injection_table(b4n)
# b4s/b2s = 剥离引用后的版本（供「新增式错误断言」类负向检查；A 组也会用到）
b4s, b2s = strip_quoted(b4n), strip_quoted(b2n)

# ---------- A 组：正口径（必须存在，且数字必须与反解一致） ----------
need("A1 B4 含 76 的来源等式 77−5+4（正）且不含 77−6 改写（负）",
     bool(re.search(r"77\s*[−-]\s*5\s*\+\s*4", b4n)) and not re.search(r"77\s*[−-]\s*6", b4n))
need("A2 B4 含 36 的代数式 core∪E∪IDENT", "core" in b4n and "E[Integer]" in b4n and "IDENT_REL" in b4n)
need("A3 B4 写出 core=19 与反解一致", f"= 19 键" in b4n or "19 键" in b4n, n_core)
need("A4 B4 写出 76−36=40 与反解一致", f"40 键" in b4n, n_diff)
need("A5 B4 明确「8 键属 E[String]−E[Integer]」且无 13 键改写",
     "**8 键**属" in b4n and "13 键**属" not in b4n and "8 键**是类型专属" in b4n)
need("A6 B4 触发条件标 UNVERIFIED", "UNVERIFIED" in b4n)
need("A7 B4 给出证据分级表（LIVE/STATIC/UNVERIFIED 三者齐）",
     all(x in b4n for x in ("LIVE", "STATIC", "UNVERIFIED")))
need("A8 B4 给出可复核脚本路径", "tools/audit/b4_keycount_algebra.py" in b4n)

# B2 文档必须被同步更正
need("A9 B2 §3.3 已改为「回显直传 / 重建」口径",
     "原样回显直传" in b2n and "模板重建" in b2n)
need("A10 B2 三档表已去掉「派生键被前端省略」old 口径",
     "类型变更时，派生键被前端省略" not in b2n)
need("A11 B2 指向 B4 文档", "B4-KEYCOUNT-ORIGIN.md" in b2n)

# ---------- A12+ ：main 12:06 三条口径（auditor M9/M10 漏检点，必须落文档） ----------
accept = [t for t in TYPES if E_TABS[t] is not None and (base | E_TABS[t]) == k36]
need("A12 文档写出 3.4 无类型判别力 + 接受集 5/14（与反解一致）",
     "无类型判别力" in b4n or "没有类型判别力" in b4n,
     "缺失「无类型判别力」表述")
need("A13 文档写出的接受集成员与反解一致",
     all(t in b4n for t in accept) and "5/14" in b4n, accept)
need("A14 文档明确「不得推出 INTEGER 专属形态」",
     "不得由 3.4 推出" in b4n or "不是 INTEGER 的特征" in b4n)
need("A15 文档写出 MultilineString 陷阱（键数36但键集不等）",
     "MultilineString" in b4n and "陷阱" in b4n
     and "maxLength, minLength" in b4n)
need("A15b 负向：不得用「键数不同故不成立」解释 MultilineString（它的键数恰好相同）",
     not re.search(r"MultilineString[^\n。]{0,30}键数[^\n。]{0,10}不同", b4s))
need("A16 文档明确「比键集不是比键数」", "键集" in b4n and "不是比\"键数\"" in b4n)
need("A17 文档写 max/min 覆盖 7/14", "7/14" in b4n)
need("A18 文档写值域三层（键存在/有值/可交互配置）",
     all(x in b4n for x in ("键存在", "可交互配置")))
need("A19 文档含容斥写法", "容斥" in b4n and "19 + 17 + 8 − 8" in b4n)
need("A20 文档含方向边界（请求侧 + 响应侧 77/72 两形态）",
     "请求侧" in b4n and "响应侧" in b4n and "72" in b4n and "互不包含" in b4n)
need("A21 文档把 72 的接口名标为推断（不当事实）",
     "推断" in b4n and "udcEntityGet" in b4n)
need("A22 文档声明 bundle 段已落地仓库（可复现）",
     "assets/bundle-type-default-tables.js.txt" in b4n)

# ---------- B 组：负口径（必须 NOT 存在；正负绑定） ----------

need("B1 不出现「键数由 dataType 决定」类断言（否定语境豁免）",
     not has_unnegated(b4n + b2n, r"(键数|键集)\s*(由|随)\s*dataType\s*(决定|变|走)"))
need("B2 不出现未加引号的「40 键全是跟类型走」断言（引号/删除线内=引用，豁免）",
     not re.search(r"40\s*键[^。\n]{0,24}全(是|部)", b4s + b2s))
need("B3 不把 36 键的成因写成纯粹的「省略」（须有 重建/模板 口径同时在场）",
     ("重建" in b4n or "模板" in b4n))
need("B4 不出现「任何键数都能推成通用规则」类断言",
     not re.search(r"(36|26|76)\s*键.{0,16}(通用规则|恒为|一律)", b4n.replace("不能推成通用规则", "")))
need("B5 「充分条件/触发器」不得标成 已证/PASS/VERIFIED（UNVERIFIED 的 VERIFIED 子串不误伤）",
     not re.search(r"(充分条件|触发器)[^\n]{0,16}(已证|(?<!UN)PASS|(?<!UN)VERIFIED)", b4n + b2n))
need("B6 B2 不得残留「派生键在类型变更时被前端省略」（引号内也算残留，因其非证据语境）",
     "派生键在类型变更时被前端省略" not in b2n)

# ---------- B7 组：auditor M7/M9/M10 漏检点（新增式漂移 + 删除锚点） ----------
# M9：把 36 键说成 INTEGER 专属（main 口径 ②a 的反面）
need("B7a 负向：不得出现「36 键…INTEGER 专属形态」类断言",
     not re.search(r"36\s*键[^\n。]{0,24}INTEGER\s*专属", b4s))
need("B7b 负向：不得出现「精简 DTO 是 INTEGER 专属」变体",
     not re.search(r"(精简\s*DTO|36\s*键)[^\n。]{0,20}(唯一|只属|专属)于?\s*INTEGER", b4s))
# M10：把值域能力说成 INTEGER 独有（main 口径 ③ 的反面）
need("B7c 负向：不得出现「值域能力只有 INTEGER」类断言",
     not re.search(r"值域[^\n。]{0,16}(只有|仅)\s*INTEGER", b4s))
need("B7d 负向：不得出现「只有 INTEGER 有 max/min」变体",
     not re.search(r"(只有|仅)\s*INTEGER[^\n。]{0,16}(max|min|值域)", b4s))
# M7：删除触发条件锚点（结构性删除）——必须存在这四要素
need("B7e 删除锚点防护：五节标题须完整含「必要机制已证，充分条件 UNVERIFIED」",
     "## 五、触发条件：必要机制已证，充分条件 UNVERIFIED" in b4n)
need("B7e2 触发条件三要素仍全在（充分条件 + 三因素 + n=1）",
     ("充分条件" in b4n) and ("三因素" in b4n) and (("n=1" in b4n) or ("n = 1" in b4n)))
# 判别力边界三小节必须都在（防整段被删）
need("B7f 4.3 三小节全在（4.3.1/4.3.2/4.3.3）",
     all(x in b4n for x in ("4.3.1", "4.3.2", "4.3.3")))
need("B7g 方向边界小节在（防删 §〇）",
     "## 〇、方向边界" in b4n)

# ---------- 注入场景（证明闸门真会拦） ----------
# 退出码语义（防 $? 误导，main 12:11 要求）：
#   被拦   = 1  （child 判 FAIL ⇒ 闸门有效）
#   未命中 = 2  （child 仍 PASS ⇒ 闸门漏检，或 anchor 已失效）
#   锚点缺失/异常 = 3
INJECTIONS = {
    # N1：把触发条件从 UNVERIFIED 改成已证（锚点=正文实际写法）
    "N1": (B4, "充分条件仍 UNVERIFIED", "充分条件仍 已证"),
    # N2：把 76 来源等式改错（5→6）
    "N2": (B4, "77 − 5 + 4 = 76", "77 − 6 + 4 = 76"),
    # N3：把 8 键改成 13 键（复刻旧的错误归类）
    "N3": (B4, "40 键实际只有 **8 键**属", "40 键实际只有 **13 键**属"),
    # N4：恢复旧口径到 B2
    "N4": (B2, "**读接口对象原样回显直传**（77−5+4，等式精确）", "类型变更时，派生键被前端省略"),
    # M7：删掉触发条件整行（结构性删除）
    "M7": (B4, "## 五、触发条件：必要机制已证，充分条件 UNVERIFIED", "## 五、触发条件"),
    # M9：新增「36 键是 INTEGER 专属形态」错误断言
    "M9": (B4, "**判别力边界另有三条**", "36 键精简 DTO 是 INTEGER 专属形态。**判别力边界另有三条**"),
    # M10：新增「值域能力只有 INTEGER」错误断言
    "M10": (B4, "**判别力边界另有三条**", "值域能力只有 INTEGER 类型具备。**判别力边界另有三条**"),
    # M11：把接受集从 5/14 改成 2/14
    "M11": (B4, "5/14", "2/14"),
    # M12：把 MultilineString 陷阱改成「键数不同所以不成立」
    "M12": (B4, "E[MultilineString] − k36 = {maxLength, minLength}", "MultilineString 键数不同故不成立"),
    # SELFCHECK：语义无害的等价改写（只把全角空格换成普通空格）——闸门【应当】放行，
    # 用于证明「2 = 漏检」这个码位真实可达，而不是只写在代码里没人见过。
    "SELFCHECK": (B4, "**LIVE 已证**", "**LIVE** 已证"),
}

ap = argparse.ArgumentParser()
ap.add_argument("--inject", default="")
args = ap.parse_args()

if args.inject:
    if args.inject not in INJECTIONS:
        # 必须 3：`raise SystemExit("str")` 会让退出码=1，与被拦(1)撞码（main 12:26 指出的真 bug）
        print(f"unknown injection: {args.inject}  (known: {', '.join(INJECTIONS)})")
        raise SystemExit(3)
    path, old, new = INJECTIONS[args.inject]
    txt = path.read_text(encoding="utf-8")
    if old not in txt:
        print(f"[INJECT {args.inject}] ANCHOR-MISSING: {old!r}")
        raise SystemExit(3)
    mutated = txt.replace(old, new, 1)
    path.write_text(mutated, encoding="utf-8")
    rc = 3
    try:
        import subprocess
        r = subprocess.run([sys.executable, __file__], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        caught = r.returncode != 0
        print(f"[INJECT {args.inject}] child exit = {r.returncode}  => {'CAUGHT(拦下)' if caught else 'MISSED(漏检)'}")
        for line in r.stdout.splitlines():
            if line.startswith("FAIL"):
                print("   " + line)
        rc = 1 if caught else 2          # 1=被拦(好)，2=漏检(坏)
    finally:
        path.write_text(txt, encoding="utf-8")
        assert path.read_text(encoding="utf-8") == txt, "restore mismatch"
        print(f"[INJECT {args.inject}] restored byte-identical")
    raise SystemExit(rc)

print()
if fails:
    print("GATE FAILED:", len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("GATE PASS  (B4 文档：反解数字对齐 + 正负绑定 + B2 同步更正)")
