# -*- coding: utf-8 -*-
"""B6 闸门：SLICE-B6-DECIMAL-static.md 一致性校验（B5 v3 标准，不降档）

沿用 B5 教训，四条硬要求：
  ① 整行现算相等（不是 has_num 存在即过）
  ② 等级 token 等价类约束（禁裸 LIVE / 纯 PASS）
  ③ 注入矩阵 rc 与语义一致；锚点缺失 rc=3 不计入被拦
  ④ 四码位 rc 全表实测可达（D64）：0/1/2/3 各有一条打印出该码位自身的运行

退出码：0 全过 / 1 有断言失败(注入被拦) / 2 漏检(注入未拦) / 3 锚点缺失
"""
import hashlib, json, pathlib, re, sys

REPO = pathlib.Path(r"<SEEYON_AGENT_ROOT>")
DOC = REPO / "docs/audit/entity-field-matrix/SLICE-B6-DECIMAL-static.md"
ASSET_E = REPO / "docs/audit/entity-field-matrix/assets/bundle-SEG-E_Etable.js.txt"
ASSET_F = REPO / "docs/audit/entity-field-matrix/assets/bundle-SEG-F_ftable.js.txt"
ASSET_T = REPO / "docs/audit/entity-field-matrix/assets/bundle-SEG-T_WB_range.js.txt"
BUNDLE = REPO / "docs/audit/artifacts/udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js"
KEYS5 = REPO / "docs/audit/artifacts/scratch-migrated/audit-slice-b5/B5-keysets.json"
STATIC6 = REPO / "docs/audit/artifacts/scratch-migrated/audit-slice-b6/B6-static.json"
DB6 = REPO / "docs/audit/artifacts/scratch-migrated/audit-slice-b6/B6-db.json"
EV1 = REPO / "docs/audit/entity-field-matrix/EVIDENCE-batch-contract-live.json"
EV2 = REPO / "docs/audit/entity-field-matrix/EVIDENCE-batch-update-live.json"

ANCHOR_E_INNER = "b1e75e105c0dedefeaec5301fec38d22bbde71df864dc36f47188004b9f1e84f"
SEG_E_SHA = "62869f1230be89074d5974a732eccc5edcb77044e7ea454118245628c589d645"
SEG_T_SHA = "f5483b41efaf6b55546d7f2f3aefb7c8bdd17472791b670ae19ee8527688901e"
SEG_F_SHA = "db90ee1f4d1f8c393de97533f8fdb0b478222e1d1501c0186b4aead08bf21221"
BUNDLE_SHA = "6051e1df6c574df74c842f9e4c0714fae5c7ff0df6e86e5ffa5b2d4f994f387d"

PASS = 0
FAIL = 0
FAILED = []

def ok(cond, name, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("PASS %s%s" % (name, ("  — " + detail) if detail else ""))
    else:
        FAIL += 1
        FAILED.append(name)
        print("FAIL %s%s" % (name, ("  — " + detail) if detail else ""))

def sha(b):
    return hashlib.sha256(b).hexdigest()

anchors = {"doc": DOC, "asset_E": ASSET_E, "asset_F": ASSET_F, "asset_T": ASSET_T,
           "bundle": BUNDLE, "keys5": KEYS5, "static6": STATIC6, "db6": DB6,
           "ev1": EV1, "ev2": EV2}
for k, p in anchors.items():
    if not p.exists():
        print("ANCHOR NOT FOUND: %s -> %s" % (k, p))
        sys.exit(3)

txt = DOC.read_text(encoding="utf-8")
keys5 = json.loads(KEYS5.read_text(encoding="utf-8"))
st6 = json.loads(STATIC6.read_text(encoding="utf-8"))
db6 = json.loads(DB6.read_text(encoding="utf-8"))

argv = sys.argv[1:]
INJECT = None
SELFCHECK = False
i = 0
while i < len(argv):
    a = argv[i]
    if a == "--selfcheck":
        SELFCHECK = True
    elif a == "--inject":
        if i + 1 >= len(argv):
            print("--inject 缺少参数"); sys.exit(3)
        INJECT = argv[i + 1]; i += 1
    elif a.startswith("--inject="):
        INJECT = a.split("=", 1)[1]
    i += 1

# 注入表锚点必须真实存在（B5 v1 教训：锚点写错=未生效却计入矩阵）
INJ = {
    "N1":  ("| **DECIMAL** | **4529** |", "| **DECIMAL** | **4530** |", "DECIMAL 总数 4529→4530"),
    "N2":  ("| **DECIMAL** | **4529** | 19 / 4504 / **6** |", "| **DECIMAL** | **4529** | 19 / 4504 / **7** |",
            "DECIMAL min 非空 6→7"),
    "N3":  ("`E[Decimal]` **17 键**", "`E[Decimal]` **16 键**", "E 键数 17→16"),
    "N4":  ("`f[Decimal]` **7 键**", "`f[Decimal]` **6 键**", "f 键数 7→6"),
    "N5":  ("| **STATIC：DECIMAL vs Currency 键集** |", "| **LIVE：DECIMAL vs Currency 键集** |",
            "STATIC 改成 LIVE"),
    "N6":  ("`decimalDigits`", "`decimalDigit`", "精度键名少一个 s"),
    "N7":  ("| DECIMAL | 0（**无系统字段**） | 4529 | **6** |", "| DECIMAL | 4529 | 4529 | **6** |",
            "is_system 列被换成总数"),
    "N8":  ("| **CURRENCY** | **107** |", "| **CURRENCY** | **108** |", "CURRENCY 107→108"),
    "N9":  ('3. **不得**说"DECIMAL 的键集可判别它与 CURRENCY"', '3. **可以**说"DECIMAL 的键集可判别它与 CURRENCY"',
            "禁用句式反转"),
    "N10": ("与 `E[Currency]` **集合完全相等**", "与 `E[Currency]` **集合完全不等**", "键集相等→不等"),
    "N11": ("| **契约对照：batch DTO** | 两份 EVIDENCE 字段级 DTO 中 DECIMAL/CURRENCY 实例数 **0**；`decimalDigits` 在 DTO 层是**全员共有键** | **VACUUM** |",
            "| **契约对照：batch DTO** | 两份 EVIDENCE 字段级 DTO 中 DECIMAL/CURRENCY 实例数 **0**；`decimalDigits` 在 DTO 层是**全员共有键** | **PASS** |",
            "VACUUM 冒充 PASS"),
    "N12": (SEG_E_SHA, "0" * 64, "SEG-E sha256 被改"),
    "N13": ("| DECIMAL | 0（**无系统字段**） | 4529 | **6** |", "| DECIMAL | 0（**无系统字段**） | 4529 | **7** |",
            "交叉表 min 非空 6→7"),
    "N14": ("  4 位 2267 / 2 位 2130 / 6 位 51 / 10 位 49 / 8 位 18 /",
            "  4 位 2268 / 2 位 2130 / 6 位 51 / 10 位 49 / 8 位 18 /",
            "digits 2267→2268"),
    "SELFCHECK": ("## 一、一句话结论\n", "## 一、一句话结论 \n", "等价改写（标题加尾随空格）——2 码位可达性"),
}

if SELFCHECK:
    txt = txt.replace("## 一、一句话结论\n", "## 一、一句话结论 \n", 1)

if INJECT:
    if INJECT not in INJ:
        print("INJECT KEY NOT FOUND: %s（可用: %s）" % (INJECT, ",".join(sorted(INJ))))
        sys.exit(3)
    old, new, desc = INJ[INJECT]
    if old not in txt:
        print("INJECT NO-OP（锚点未命中）: %s" % INJECT)
        sys.exit(3)
    txt = txt.replace(old, new, 1)
    print("== 注入 %s: %s ==" % (INJECT, desc))

LINESET = set(l.rstrip() for l in txt.split("\n"))
BODY = txt.split("## 九、")[0]

def has_line(s):
    return s.rstrip() in LINESET

# ---------- 1. 反解源锚 ----------
ok(sha(BUNDLE.read_bytes()) == BUNDLE_SHA, "A1 整文件 sha256 锚")
ok(sha(ASSET_E.read_bytes()) == SEG_E_SHA, "A2 SEG-E 段 sha256")
ok(sha(ASSET_E.read_text(encoding="utf-8")[2:-1].encode()) == ANCHOR_E_INNER,
   "A3 SEG-E 内层 == auditor 锚（跨组互证）")
ok(sha(ASSET_F.read_bytes()) == SEG_F_SHA, "A4 SEG-F 段 sha256")
ok(sha(ASSET_T.read_bytes()) == SEG_T_SHA, "A5 SEG-T 段 sha256")
for nm, v in [("A6 SEG-E 锚", SEG_E_SHA), ("A7 SEG-F 锚", SEG_F_SHA), ("A8 整文件锚", BUNDLE_SHA)]:
    ok(v in BODY, nm + " 已载入正文")

# ---------- 2. 键集（从反解源现算） ----------
def top_keys(raw):
    body = raw[1:-1]; depth = 0; ins = False; esc = False; st = 0; outk = []
    for i, c in enumerate(body):
        if ins:
            if esc: esc = False
            elif c == chr(92): esc = True
            elif c == '"': ins = False
            continue
        if c == '"': ins = True
        elif c in "{[(": depth += 1
        elif c in "}])": depth -= 1
        elif c == "," and depth == 0:
            m = re.match(r"\s*([\w$]+)\s*:", body[st:i])
            if m: outk.append(m.group(1))
            st = i + 1
    m = re.match(r"\s*([\w$]+)\s*:", body[st:])
    if m: outk.append(m.group(1))
    return outk

ED = keys5["ALL_E_raw"]["Decimal"]; FD = keys5["ALL_f_raw"]["Decimal"]
EI = keys5["ALL_E_raw"]["Integer"]; FI = keys5["ALL_f_raw"]["Integer"]
EC = keys5["ALL_E_raw"]["Currency"]; FC = keys5["ALL_f_raw"]["Currency"]
kd, fd_ = top_keys(ED), top_keys(FD)
ki, fi = top_keys(EI), top_keys(FI)
kc, fc = top_keys(EC), top_keys(FC)

ok(len(kd) == 17, "B1 E[Decimal] 键数=17（现算）", str(len(kd)))
ok(len(fd_) == 7, "B2 f[Decimal] 键数=7（现算）", str(len(fd_)))
ok(set(kd) == set(kc), "B3 E 层 Decimal 键集 == Currency（完全相等）")
ok(set(fd_) != set(fc), "B4 f 层 Decimal 键集 != Currency（f 层可区分）")
ok(sorted(set(fd_) - set(fc)) == ["searchable"], "B5 f 层差集 = {searchable}",
   str(sorted(set(fd_) - set(fc))))
ok(set(kd) != set(ki), "B6 E 层 Decimal != Integer（可区分）")
ok(sorted(set(kd) - set(ki)) == ["decimalDigits"] and sorted(set(ki) - set(kd)) == ["uniqueness"],
   "B7 E 层 vs Integer 差集 = {decimalDigits} / {uniqueness}",
   "%s / %s" % (sorted(set(kd) - set(ki)), sorted(set(ki) - set(kd))))
ok("decimalDigits" in kd and "decimalDigits" in fd_, "B8 decimalDigits 在 E/f 两层都出现")
ok(sorted(st6["precision_keys"]["E_tables_with_precision"]) == ["Currency", "Decimal"],
   "B9 E 层含 decimalDigits 的类型仅 Currency/Decimal")
ok(sorted(st6["precision_keys"]["f_tables_with_precision"]) == ["Currency", "Decimal"],
   "B10 f 层含 decimalDigits 的类型仅 Currency/Decimal")
ok(st6["precision_keys"]["matched_keynames"] == ["decimalDigits"],
   "B11 全 14 表精度键名只有 decimalDigits（无 precision/scale）")
ok(st6["E_Decimal_kv"]["decimalDigits"] == "2", "B12 E[Decimal].decimalDigits 默认 2")
ok(st6["E_Decimal_kv"]["dataType"] == '"DECIMAL"', "B13 E[Decimal].dataType=DECIMAL")
ok(st6["f_Decimal_kv"]["decimalDigits"] == "2", "B14 f[Decimal].decimalDigits 默认 2")
ok("min" in kd and "max" in kd, "B15 E[Decimal] 含 min/max（值域 7/14 组内）")
ok(("`E[Decimal]` **%d 键**" % len(kd)) in BODY, "B16 正文 E 键数与现算一致(%d)" % len(kd))
ok(("`f[Decimal]` **%d 键**" % len(fd_)) in BODY, "B17 正文 f 键数与现算一致(%d)" % len(fd_))

# WB 边界（Decimal 与 BigInteger 相同，无判别力）
wb = ASSET_T.read_text(encoding="utf-8")
ok('[a.Decimal]:{min:"-9007199254740991",max:"9007199254740991"}' in wb,
   "B18 WB 表 Decimal 边界 ±(2^53−1)")
ok('  [a.Decimal]:{min:"-9007199254740991",max:"9007199254740991"}' in BODY,
   "B19 正文 WB Decimal 行存在（含两格缩进）")

# ---------- 3. DB 事实（整行现算） ----------
ok(db6["data_type_dist"][0]["data_type"] in ("STRING", "ENTITY"), "C1 全库最大类型分布合理")
ok(db6["counts"]["DECIMAL"] == 4529, "C2 DECIMAL 总数=4529", str(db6["counts"]["DECIMAL"]))
ok(db6["is_system_counts"]["DECIMAL"] == {"0": 4529}, "C3 DECIMAL 全部 is_system=0（无系统字段）")
ok(db6["counts"]["CURRENCY"] == 107, "C4 CURRENCY=107")
ok(db6["counts"]["INTEGER"] == 3539, "C5 INTEGER=3539（B2 基线）")
ok(db6["counts"]["BIGINTEGER"] == 4576, "C6 BIGINTEGER=4576（B5 基线）")
ok(db6["total_all_types"] == 67864, "C7 全库总行数=67864")

sd = db6["states"]["DECIMAL"]["all"]
si = db6["states"]["INTEGER"]["all"]
sbi = db6["states"]["BIGINTEGER"]["all"]
sc = db6["states"]["CURRENCY"]["all"]

def row(dt, cnt, mn, mx, mn_ne, mx_ne):
    return "| **%s** | **%d** | %d / %d / **%d** | %d / %d / **%d** |" % (
        dt, cnt, mn["null_n"], mn["empty_n"], mn_ne, mx["null_n"], mx["empty_n"], mx_ne)

ok(has_line(row("DECIMAL", db6["counts"]["DECIMAL"], sd["min"], sd["max"],
                sd["min"]["nonempty_n"], sd["max"]["nonempty_n"])),
   "C8 §4.2 DECIMAL 行逐字一致",
   row("DECIMAL", db6["counts"]["DECIMAL"], sd["min"], sd["max"],
       sd["min"]["nonempty_n"], sd["max"]["nonempty_n"]))
ok(has_line(row("CURRENCY", db6["counts"]["CURRENCY"], sc["min"], sc["max"],
                sc["min"]["nonempty_n"], sc["max"]["nonempty_n"])),
   "C9 §4.2 CURRENCY 行逐字一致",
   row("CURRENCY", db6["counts"]["CURRENCY"], sc["min"], sc["max"],
       sc["min"]["nonempty_n"], sc["max"]["nonempty_n"]))
ok(has_line(row("INTEGER", db6["counts"]["INTEGER"], si["min"], si["max"],
                si["min"]["nonempty_n"], si["max"]["nonempty_n"])),
   "C10 §4.2 INTEGER 行逐字一致")
ok(has_line(row("BIGINTEGER", db6["counts"]["BIGINTEGER"], sbi["min"], sbi["max"],
                sbi["min"]["nonempty_n"], sbi["max"]["nonempty_n"])),
   "C11 §4.2 BIGINTEGER 行逐字一致")

ok(sd["min"]["nonempty_n"] == 6, "C12 ★DECIMAL min 非空=6（唯一真配置类型）", str(sd["min"]["nonempty_n"]))
ok(sd["max"]["nonempty_n"] == 5, "C13 ★DECIMAL max 非空=5", str(sd["max"]["nonempty_n"]))
ok(si["min"]["nonempty_n"] == 1 and si["max"]["nonempty_n"] == 0, "C14 INTEGER 1/0（B2 基线）")
ok(sbi["min"]["nonempty_n"] == 0 and sbi["max"]["nonempty_n"] == 0, "C15 BIGINTEGER 0/0（B5 基线）")
ok(sc["min"]["nonempty_n"] == 0 and sc["max"]["nonempty_n"] == 0, "C16 CURRENCY 0/0")

# 交叉表（DECIMAL/CURRENCY 均只有 is_system=0；文档 §4.3 表列为
#   data_type | is_system=1（系统） | is_system=0（业务） | 非空 min）
def rowx(dt, sys1_n, sys0_n, mn_ne):
    # 文档加粗规则：DECIMAL 行标注「无系统字段」且非空 min 加粗；其余三行为纯数字不加粗
    if dt == "DECIMAL":
        return "| %s | 0（**无系统字段**） | %d | **%d** |" % (dt, sys0_n, mn_ne)
    return "| %s | %d | %d | %d |" % (dt, sys1_n, sys0_n, mn_ne)

d1 = db6["is_system_counts"]["DECIMAL"].get("1", 0)
d0 = db6["is_system_counts"]["DECIMAL"].get("0", 0)
ok(has_line(rowx("DECIMAL", d1, d0, db6["states"]["DECIMAL"]["all"]["min"]["nonempty_n"])),
   "C17 §4.3 DECIMAL 行逐字一致",
   rowx("DECIMAL", d1, d0, db6["states"]["DECIMAL"]["all"]["min"]["nonempty_n"]))
c1 = db6["is_system_counts"]["CURRENCY"].get("1", 0)
c0 = db6["is_system_counts"]["CURRENCY"].get("0", 0)
ok(has_line(rowx("CURRENCY", c1, c0, db6["states"]["CURRENCY"]["all"]["min"]["nonempty_n"])),
   "C18 §4.3 CURRENCY 行逐字一致",
   rowx("CURRENCY", c1, c0, db6["states"]["CURRENCY"]["all"]["min"]["nonempty_n"]))
i1 = db6["is_system_counts"]["INTEGER"].get("1", 0)
i0 = db6["is_system_counts"]["INTEGER"].get("0", 0)
ok(has_line(rowx("INTEGER", i1, i0, db6["states"]["INTEGER"]["all"]["min"]["nonempty_n"])),
   "C18b §4.3 INTEGER 行逐字一致")
b1 = db6["is_system_counts"]["BIGINTEGER"].get("1", 0)
b0 = db6["is_system_counts"]["BIGINTEGER"].get("0", 0)
ok(has_line(rowx("BIGINTEGER", b1, b0, db6["states"]["BIGINTEGER"]["all"]["min"]["nonempty_n"])),
   "C18c §4.3 BIGINTEGER 行逐字一致")

# 非空 min/max 真实样本（这是本片最有价值的事实）
rows = db6["decimal_minmax_nonempty_rows"]
ok(len(rows) == 6, "C19 DECIMAL 非空 min/max 行数=6", str(len(rows)))
ok(all(r["is_system"] == 0 for r in rows), "C20 这些行全部是业务字段")
ok(sum(1 for r in rows if r["min"] == "0" and r["max"] == "1") == 5,
   "C21 其中 5 条是 min=0 / max=1（税率统一调整 ×4 + 达成占比 ×1）")
ok(sum(1 for r in rows if r["min"] == "0" and r["max"] == "") == 1,
   "C22 1 条 min=0 / max 空（债权最高额限度）")
ok(sum(1 for r in rows if str(r["decimal_digits"]) == "2") == len(rows),
   "C23 这 6 条 decimal_digits 全部为 2")

# vse 空壳
vd = db6["vse_distinct"]["DECIMAL"]
ok(len(vd) == 1 and vd[0]["vse"] == '{"min":"","max":""}' and vd[0]["n"] == 8,
   "C24 DECIMAL vse 非空 8 条全是空壳（去重仅 1 值）",
   str([(r["vse"], r["n"]) for r in vd]))
ok(db6["vse_distinct"]["CURRENCY"] == [], "C25 CURRENCY vse 非空=0")

# decimal_digits 分布
dd = {str(r["decimal_digits"]): r["n"] for r in db6["decimal_digits_dist"]}
ok(dd.get("4") == 2267 and dd.get("2") == 2130, "C26 DECIMAL digits：4 位 2267 / 2 位 2130", str(dd))
ok(len(db6["decimal_digits_dist"]) == 10, "C27 DECIMAL digits 有 10 种取值", str(len(dd)))
ok(has_line("  4 位 2267 / 2 位 2130 / 6 位 51 / 10 位 49 / 8 位 18 /"), "C28 正文 digits 分布首行逐字一致")

# 本应用
ok(db6["app_decimal"]["total"] == 0, "C29 本应用 DECIMAL=0")
ok(has_line("| 本应用 DECIMAL 数 | **0** |"), "C30 正文本应用 DECIMAL 行逐字一致")

# ---------- 4. 等级等价类 ----------
ok("**VACUUM**" in BODY, "D1 正文含 VACUUM")
ok(BODY.count("**VACUUM**") >= 2, "D2 VACUUM 至少 2 处（结论表 + 证据表）", "count=%d" % BODY.count("**VACUUM**"))
ok("**PASS**" not in BODY, "D3 正文不得出现 **PASS**")
ok("**LIVE**" not in BODY, "D4 正文不得出现裸 **LIVE**")
ok(BODY.count("**LIVE/DB**") >= 3, "D5 LIVE/DB 存在", "count=%d" % BODY.count("**LIVE/DB**"))
ok("**STATIC**" in BODY, "D6 STATIC 存在")
ok("**UNVERIFIED**" in BODY, "D7 UNVERIFIED 存在")
ok("**BLOCKED**" in BODY, "D8 BLOCKED 存在")

# ---------- 5. §一 结论表逐字 ----------
CONCL = [
    "| **STATIC：DECIMAL vs Currency 键集** | `E[Decimal]` **17 键**，与 `E[Currency]` **集合完全相等**；`f[Decimal]` **7 键** vs `f[Currency]` **6 键**，差集仅 `{searchable}` | **STATIC** |",
    "| **STATIC：精度标度键** | 全 14 表精度键名**唯一为 `decimalDigits`**（无 precision/scale）；仅 Currency/Decimal 携带；E/f 默认值均 **2** | **STATIC** |",
    "| **STATIC：与 Integer/BigInteger 的关系** | E 层 D−I=`{decimalDigits}` / I−D=`{uniqueness}`；f 层差集更大（D 独有 `decimalDigits`+`searchable`，I 独有 `uniqueness`） | **STATIC** |",
    "| **DB：DECIMAL 全库** | **4529** 行，全部 `is_system=0`（无系统字段）；min 非空 **6**、max 非空 **5** | **LIVE/DB** |",
    "| **DB：值域真实样本** | 6 条中 **5 条 min=0/max=1**（税率统一调整 ×4 + 达成占比 ×1），1 条 min=0/max 空，全部 `decimal_digits=2` | **LIVE/DB** |",
    "| **契约对照：batch DTO** | 两份 EVIDENCE 字段级 DTO 中 DECIMAL/CURRENCY 实例数 **0**；`decimalDigits` 在 DTO 层是**全员共有键** | **VACUUM** |",
    "| **触发条件充分性** | Decimal 与 Currency 的 E 层键集恒等 ⇒ 键集无判别力 | **UNVERIFIED** |",
    "| **页面可交互配值域** | 需页面腿，登录态冻结 | **BLOCKED** |",
]
for n, line in enumerate(CONCL, 1):
    ok(has_line(line), "E%d §一 结论行逐字一致 [%d/8]" % (n, n))

# ---------- 6. 负向断言（§九 前） ----------
NEG = [
    (r"\| \*\*DECIMAL\*\* \| \*\*4530", "DECIMAL 总数 4530"),
    (r"\| \*\*DECIMAL\*\* \| \*\*4529\*\* \| \d+ / \d+ / \*\*[78]\*\* \|", "DECIMAL min 非空写成 7/8"),
    (r"键集与 Currency 完全不同", "键集相同说成不同"),
    (r"\*\*可以\*\*说", "禁用句式反转"),
    (r"\*\*LIVE\*\*", "裸 LIVE"),
    (r"\*\*PASS\*\*", "纯 PASS"),
    (r"decimalDigit[^s]", "精度键名少 s"),
    (r"CURRENCY\*\* \| \*\*108", "CURRENCY 108"),
]
for pat, desc in NEG:
    ok(re.search(pat, BODY) is None, "F1 负向：正文不含「%s」" % desc)

# ---------- 7. 整段删除防护（B5 J 组延续） ----------
ok(BODY.count("### 5.2") == 1, "G1 §5.2 段存在")
ok(BODY.count("### 6.2") == 1, "G2 §6.2 段存在")
for n, frag in enumerate([
    "1. **不得**说\"DECIMAL 有值域配置能力就是 DECIMAL 特有\"",
    "2. **不得**说\"decimalDigits 能判别字段类型\"",
    "3. **不得**说\"DECIMAL 的键集可判别它与 CURRENCY\"",
    "4. **不得**把 6 条非空 min 当作\"DECIMAL 普遍配值域\"",
], 1):
    ok(frag in BODY, "G3 §6.2 第 %d 条禁令仍在" % n)

# ---------- 9. §6.1 证据表整表逐行比对（main 051826Z 硬验收项①②） ----------
# B5 教训根因：GRADE_ROWS 只写 7 条而 §6.1 有 12 数据行 ⇒ 比对表本身被截断 ⇒ 5 行无覆盖。
# 因此这里除了 12 条逐行断言，另加 F0 长度断言：覆盖数由文档现算，不由闸门自己说了算。
GRADE_ROWS = [
    "| E[Decimal] 17 键 / f[Decimal] 7 键 | **STATIC** | SEG-E、SEG-F 段落级反解 + 双 sha256 |",
    "| E 层 Decimal 键集 == Currency（恒等） | **STATIC** | 集合比对 |",
    "| f 层 Decimal vs Currency 差集 = {searchable} | **STATIC** | 集合比对 |",
    "| 精度键唯一为 decimalDigits，仅 Decimal/Currency 携带 | **STATIC** | 14+16 表键名正则扫 |",
    "| DECIMAL 全库 4529，全部业务字段 | **LIVE/DB** | §4.3 |",
    "| min 非空 6 / max 非空 5（唯一成规模配置，占四类型 min 非空 7 条的 85.7%） | **LIVE/DB** | §4.4 |",
    "| vse 与 min/max 语义不重叠（同一行可同时有 min/max 真值 + vse 空壳） | **LIVE/DB** | §4.5 |",
    "| decimal_digits 实际分布 ≠ 模板默认 2 | **LIVE/DB** | §4.6 |",
    "| 本应用 DECIMAL=0 | **LIVE/DB** | §4.7 |",
    "| batch DTO 无 DECIMAL 实例 | **VACUUM** | §5.1 |",
    "| Decimal 的请求 DTO 实际形态 | **UNVERIFIED** | 无实例；两批已捕获 DTO（1 实体/2 组/16 字段）内 DECIMAL 实例为 0，但全库 4529 条 DECIMAL 字段表明该类型真实存在，仅本抓包面未覆盖 |",
    "| 页面可交互配值域 | **BLOCKED** | 登录态 |",
]

def _sec61_data_rows(t):
    """动态抽取 §6.1 表数据行（排除表头与分隔行）。"""
    try:
        sec = t.split("### 6.1 证据等级", 1)[1].split("### 6.2", 1)[0]
    except IndexError:
        return []
    rows = []
    for ln in sec.split("\n"):
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if set(cells[0]) <= set("-: "):
            continue
        if cells[0] == "结论":
            continue
        rows.append(s)
    return rows

# 等级序关系（auditor 052240Z §四-2）：白名单/黑名单只能禁"某几个 token"，
# 序关系才能表达"不许变高"。B6 的 LIVE/DB 是合法 token，D4 白名单堵不住 STATIC→LIVE/DB。
LEVEL_RANK = {"UNVERIFIED": 0, "BLOCKED": 0,
              "STATIC": 1, "STATIC-存在": 1, "VACUUM": 1,
              "LIVE/DB": 2}
_LVL_RE = re.compile(r"\*\*(STATIC-存在|STATIC|VACUUM|UNVERIFIED|BLOCKED|LIVE/DB)\*\*")
BASELINE_RANK = [LEVEL_RANK[_LVL_RE.search(r).group(1)] for r in GRADE_ROWS]

def _row_levels(t):
    """从文档 §6.1 现取每行等级 token（不依赖 GRADE_ROWS）。"""
    out = []
    for r in _sec61_data_rows(t):
        m = _LVL_RE.search(r)
        out.append(m.group(1) if m else None)
    return out

_doc_levels = _row_levels(txt)
_bad_up = [(i + 1, BASELINE_RANK[i], d)
           for i, d in enumerate(_doc_levels)
           if i < len(BASELINE_RANK) and d in LEVEL_RANK
           and LEVEL_RANK[d] > BASELINE_RANK[i]]
_bad_dn = [(i + 1, BASELINE_RANK[i], d)
           for i, d in enumerate(_doc_levels)
           if i < len(BASELINE_RANK) and d in LEVEL_RANK
           and LEVEL_RANK[d] < BASELINE_RANK[i]]
ok(not _bad_up, "F15 §6.1 等级不得升格（序关系绑定，非白名单）", "升格=%s" % (_bad_up[:3],))
ok(not _bad_dn, "F16 §6.1 等级不得降格（序关系绑定，非白名单）", "降格=%s" % (_bad_dn[:3],))

_doc_rows = _sec61_data_rows(txt)
ok(len(GRADE_ROWS) == len(_doc_rows),
   "F0 §6.1 比对表必须覆盖全表（比对表 %d 条 vs 文档 %d 数据行）" % (len(GRADE_ROWS), len(_doc_rows)))
for n, line in enumerate(GRADE_ROWS, 1):
    ok(has_line(line), "F%d §6.1 等级行逐字一致 [%d/%d]" % (n, n, len(GRADE_ROWS)))

# 等级分布计数（表中各等级行数固定，防整行被挪走）
# ★ 扩展为五等级全覆盖（auditor 053205Z §四 指正：原版只数 LIVE/DB 与 STATIC，
#   VACUUM/UNVERIFIED/BLOCKED 完全没数）
_LVL_KEYS = ["**LIVE/DB**", "**STATIC**", "**VACUUM**", "**UNVERIFIED**", "**BLOCKED**"]
_lv = sum(1 for r in GRADE_ROWS if "**LIVE/DB**" in r)
ok(_lv == 5, "F13 §6.1 中 LIVE/DB 行数=5", "count=%d" % _lv)
_st = sum(1 for r in GRADE_ROWS if "**STATIC**" in r and "LIVE" not in r)
ok(_st == 4, "F14 §6.1 中 STATIC 行数=4", "count=%d" % _st)
_va = sum(1 for r in GRADE_ROWS if "**VACUUM**" in r)
ok(_va == 1, "F13b §6.1 中 VACUUM 行数=1（仅第10行 batch DTO）", "count=%d" % _va)
_un = sum(1 for r in GRADE_ROWS if "**UNVERIFIED**" in r)
ok(_un == 1, "F13c §6.1 中 UNVERIFIED 行数=1（第11行维持，域不足以支撑 VACUUM）", "count=%d" % _un)
_bl = sum(1 for r in GRADE_ROWS if "**BLOCKED**" in r)
ok(_bl == 1, "F13d §6.1 中 BLOCKED 行数=1", "count=%d" % _bl)

# ---------- ★ F17 等级-主张语义绑定（第三来源，防跨级共谋）----------
# 为什么需要它：F0-F12（整行字面）与 F13/F14（分布计数）都挂在 GRADE_ROWS 上，
#   · 文档 + GRADE_ROWS 同步改 → 整行比对失效
#   · 再把某行等级换成另一行等级补平分布 → 计数也失效（实测 rc=0 全漏）
# F15/F16（序关系）的 BASELINE_RANK 同样来自 GRADE_ROWS，共谋下贡献为零。
# 故引入与 GRADE_ROWS 无关的第三结构：按「主张文本 → 应当的证据等级」绑定。
# 依据是**该主张只能由哪一类证据源验证**：
#   bundle/字节码可得 → STATIC；DB 回读可得 → LIVE/DB；域内无实例 → VACUUM；
#   不可观测 → UNVERIFIED/BLOCKED。攻击者要绕过，必须连这张语义表一起改。
CLAIM_LEVEL = [
    ("E[Decimal] 17 键 / f[Decimal] 7 键", "STATIC"),   # 来自 bundle 反解
    ("E 层 Decimal 键集 == Currency", "STATIC"),        # 来自 bundle 反解
    ("f 层 Decimal vs Currency 差集", "STATIC"),        # 来自 bundle 反解
    ("精度键唯一为 decimalDigits", "STATIC"),           # 来自 14+16 表扫描
    ("DECIMAL 全库 4529", "LIVE/DB"),                   # 来自 DB 回读
    ("min 非空 6 / max 非空 5", "LIVE/DB"),             # 来自 DB 回读
    ("vse 与 min/max 语义不重叠", "LIVE/DB"),           # 来自 DB 回读
    ("decimal_digits 实际分布", "LIVE/DB"),             # 来自 DB 回读
    ("本应用 DECIMAL=0", "LIVE/DB"),                    # 来自 DB 回读
    ("batch DTO 无 DECIMAL 实例", "VACUUM"),            # 域内零实例
    ("Decimal 的请求 DTO 实际形态", "UNVERIFIED"),      # 抓包域仅 16 字段，不足以支撑 VACUUM
    ("页面可交互配值域", "BLOCKED"),                    # 登录态阻塞
]

_f17_rows = _sec61_data_rows(txt)
_f17_bad = []
_f17_matched = 0
for i, r in enumerate(_f17_rows, 1):
    m = _LVL_RE.search(r)
    got = m.group(1) if m else None
    hit = [(claim, want) for claim, want in CLAIM_LEVEL if claim in r]
    if not hit:
        _f17_bad.append((i, "主张未登记于 CLAIM_LEVEL", r[:40]))
        continue
    claim, want = hit[0]
    _f17_matched += 1
    if got != want:
        _f17_bad.append((i, claim, "文档=%s 应为=%s" % (got, want)))
ok(not _f17_bad,
   "F17 §6.1 每行等级必须与主张的证据源类型一致（第三来源，防跨级共谋）",
   "不匹配=%s" % (_f17_bad[:3],))
ok(_f17_matched == len(_f17_rows),
   "F17b CLAIM_LEVEL 必须覆盖 §6.1 全部行（防新增行未登记）",
   "命中 %d / 文档 %d" % (_f17_matched, len(_f17_rows)))

# ---------- ★ F18 等级-事实来源反向推导 + 语义矛盾检查（auditor 054702Z §七 / main 整段）----------
# F17 的 CLAIM_LEVEL 是硬编码常量，与文档同在一个可写面内 ⇒ 五处同步改可绕（已实测 rc=0，双向都放）。
# F18 换一个不可同源篡改的依据：把每行主张绑定到**基线 JSON 里的事实键**，
# 再由「事实来自哪类源」反推它唯一可能的证据等级。改动等级必须连 JSON 一起造，而 JSON 是取证产物。
FACT_BIND = [
    # (文档行子串, 事实来源, 事实键路径, 期望值)
    ("E[Decimal] 17 键", "static", ("keysets", "Decimal", "E_n"), 17),
    ("f[Decimal] 7 键", "static", ("keysets", "Decimal", "f_n"), 7),
    ("E 层 Decimal 键集 == Currency", "static", ("diffs", "Currency", "E_set_equal"), True),
    ("f 层 Decimal vs Currency 差集", "static", ("diffs", "Currency", "f_only_in_Decimal"), ["searchable"]),
    ("精度键唯一为 decimalDigits", "static", ("precision_keys", "matched_keynames"), ["decimalDigits"]),
    ("DECIMAL 全库 4529", "db", ("counts", "DECIMAL"), 4529),
    ("min 非空 6", "db", ("states", "DECIMAL", "all", "min", "nonempty_n"), 6),
    ("max 非空 5", "db", ("states", "DECIMAL", "all", "max", "nonempty_n"), 5),
    ("decimal_digits 实际分布", "db", ("decimal_digits_dist",), None),
    ("本应用 DECIMAL=0", "db", ("app_decimal", "total"), 0),
    # ★ 补登记（F18d 抓出我漏登，不是它们没有事实支撑）：
    #   vse 与 min/max 语义不重叠 —— 事实来自 DB vse_distinct（8 条全空壳）与 min/max 非空 6 条
    ("vse 与 min/max 语义不重叠", "db", ("states", "DECIMAL", "all", "value_scope_expression", "nonempty_n"), 8),
    #   batch DTO 无 DECIMAL 实例 —— 事实来自 EVIDENCE 字段级全扫（B7-vacuum.json：
    #   48 实例 / DECIMAL 0 / CURRENCY 0），另有 H1 断言在闸门内独立守护
    ("batch DTO 无 DECIMAL 实例", "vacuum", ("verdict", "DECIMAL_instances"), 0),
]

def _dig(obj, path):
    cur = obj
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return "__MISSING__"
    return cur

STATIC_JSON = json.loads(STATIC6.read_text(encoding="utf-8"))
DB_JSON = json.loads(DB6.read_text(encoding="utf-8"))
VACUUM_JSON = json.loads((REPO / "docs/audit/artifacts/scratch-migrated/audit-slice-b7/B7-vacuum.json").read_text(encoding="utf-8"))
_SRC = {"static": STATIC_JSON, "db": DB_JSON, "vacuum": VACUUM_JSON}

_f18_bad = []
_f18_checked = 0
for claim, src, path, want in FACT_BIND:
    try:
        key = path[0]
        val = _dig(_SRC[src], path)
    except Exception as e:
        _f18_bad.append((claim, "取值异常", str(e)[:40]))
        continue
    if val == "__MISSING__":
        _f18_bad.append((claim, "事实键缺失", ".".join(map(str, path))))
        continue
    _f18_checked += 1
    if want is not None:
        if val != want:
            _f18_bad.append((claim, "数值不符", "JSON=%r 应为=%r" % (val, want)))
    if not any(claim in r for r in _f17_rows):
        _f18_bad.append((claim, "文档中无对应行", claim))
ok(not _f18_bad,
   "F18 §6.1 主张必须能绑定到基线 JSON 的真实事实键（不许凭空写数）",
   "异常=%s" % (_f18_bad[:3],))

# ★ F18c 等级-事实同源推导：文档给的等级必须等于「由事实来源类型唯一决定的等级」
# 这是 F18 的关键补强。只校验数值对不对不够 —— 攻击者可以让数值全对，只把等级改错。
# 事实来源类型 → 唯一可能的证据等级，是类型学约束，不是偏好：
#   bundle/字节码 → STATIC；DB 回读 → LIVE/DB；域内零实例（带域限定）→ VACUUM；
#   不可观测/阻塞 → UNVERIFIED/BLOCKED
SRC_TO_LEVEL = {"static": "STATIC", "db": "LIVE/DB", "vacuum": "VACUUM"}
_derived_bad = []
for claim, src, path, want in FACT_BIND:
    if src not in SRC_TO_LEVEL:
        continue
    hit = [r for r in _f17_rows if claim in r]
    if not hit:
        _derived_bad.append((claim, "文档无对应行"))
        continue
    got = _LVL_RE.search(hit[0]).group(1)
    exp = SRC_TO_LEVEL[src]
    if got != exp:
        _derived_bad.append({"主张": claim, "来源": src, "文档等级": got, "应为": exp})
ok(not _derived_bad,
   "F18c 等级必须由事实来源类型唯一决定（static→STATIC / db→LIVE-DB），不许跨源",
   "违规=%s" % (_derived_bad[:3],))

# ★ F18d 「无事实键可绑定」的行，等级只能是 UNVERIFIED 或 BLOCKED
# 这条不依赖 CLAIM_LEVEL（可同源篡改），而依赖 FACT_BIND 的实际可达性。
# ★ 第一版写错并留痕：「未登记进 FACT_BIND」≠「无事实支撑」。
#   实测抓到 vse/min-max 与 batch DTO 两行，它们其实都有 JSON 事实（vse_distinct / 全类型扫描），
#   只是我没登记。修正：显式声明「哪些主张是故意无事实键的」，而不是靠缺席推断。
NO_FACT_CLAIMS = (
    "Decimal 的请求 DTO 实际形态",   # 契约层形态，本片无任何 DECIMAL 实例可观测
    "页面可交互配值域",              # 登录态冻结，结构性受阻
)
_BOUND_CLAIMS = [c for c, _s, _p, _w in FACT_BIND]
_unbound_bad = []
_unbound_seen = []
for r in _f17_rows:
    m = _LVL_RE.search(r)
    got = m.group(1) if m else None
    claim_text = r.strip().strip("|").split("|")[0].strip()
    is_declared_no_fact = any(c in r for c in NO_FACT_CLAIMS)
    bound = any(b in r for b in _BOUND_CLAIMS)
    if is_declared_no_fact:
        _unbound_seen.append(claim_text[:30])
        if got not in ("UNVERIFIED", "BLOCKED"):
            _unbound_bad.append({"行": claim_text[:44], "等级": got,
                                 "原因": "已声明无事实键，等级必须是 UNVERIFIED/BLOCKED"})
    elif not bound:
        # 既没在 FACT_BIND，也没在 NO_FACT_CLAIMS 声明 → 漏登记，必须显式补
        _unbound_bad.append({"行": claim_text[:44], "等级": got,
                             "原因": "既无事实绑定也未声明无事实（漏登记）"})
ok(not _unbound_bad,
   "F18d 无事实键的行等级只能是 UNVERIFIED/BLOCKED；有事实的行必须登记进 FACT_BIND",
   "违规=%s" % (_unbound_bad[:3],))
ok(len(_unbound_seen) == len(NO_FACT_CLAIMS),
   "F18e NO_FACT_CLAIMS 全部在 §6.1 中找到对应行（防声明失效后静默跳过）",
   "命中 %d / 声明 %d" % (len(_unbound_seen), len(NO_FACT_CLAIMS)))
ok(_f18_checked == len(FACT_BIND),
   "F18b FACT_BIND 全部键可达（防写错路径后静默跳过）",
   "可达 %d / 声明 %d" % (_f18_checked, len(FACT_BIND)))

# ★ F19 语义矛盾检查（收窄版）：VACUUM 必须限定「域」
# 关键区分（我第一版写错过，在此留痕）：
#   第10行「batch DTO 无 DECIMAL 实例」= 域内 VACUUM，主张自带域限定（"batch DTO 这批"）⇒ 合法
#   第11行「Decimal 的请求 DTO 实际形态」= 类型契约层问题，若标 VACUUM 等于宣称「该类型不存在契约形态」
#     —— 与 DB count=4529 直接冲突 ⇒ 非法
# 判据：VACUUM 行的主张里必须出现域限定词（batch/这批/本次/已捕获/抓包/样本/DTO），
#       否则就是在拿小样本结论冒充平台级结论。
DB_COUNTS = DB_JSON["counts"]
DOMAIN_WORDS = ("batch", "这批", "本次", "已捕获", "抓包", "样本", "本片", "该批")
_contra = []
for r in _f17_rows:
    m = _LVL_RE.search(r)
    if not m or m.group(1) != "VACUUM":
        continue
    claim_text = r.strip().strip("|").split("|")[0].strip()
    if not any(w in claim_text for w in DOMAIN_WORDS):
        # 无域限定 → 检查是否涉及 DB 里大量存在的类型
        for ty, n in DB_COUNTS.items():
            if ty in claim_text and n > 0:
                _contra.append({"行": claim_text[:40], "等级": "VACUUM",
                                "矛盾": "无域限定却声称 VACUUM，而 %s 在 DB 有 %d 行" % (ty, n)})
ok(not _contra,
   "F19 VACUUM 行的主张必须自带域限定（防拿小样本结论冒充平台级结论）",
   "违规=%s" % (_contra[:2],))

# ---------- 8. VACUUM 支撑 ----------
def dtypes(p):
    s = p.read_text(encoding="utf-8")
    return set(re.findall(r'"dataType"\s*:\s*"([A-Z_]+)"', s)), s

d1, r1 = dtypes(EV1)
d2, r2 = dtypes(EV2)
ok("DECIMAL" not in d1 and "DECIMAL" not in d2, "H1 DTO dataType 无 DECIMAL", str(sorted(d1)))
ok("CURRENCY" not in d1 and "CURRENCY" not in d2, "H2 DTO dataType 无 CURRENCY")
ok("decimalDigits" in r1 and "decimalDigits" in r2, "H3 decimalDigits 在 DTO 层出现（全员共有键）")
ok('"decimalDigits": 0' in r2, "H4 INTEGER 的 DTO 里 decimalDigits=0（证全员共有）")

print()
print("SUMMARY PASS=%d FAIL=%d" % (PASS, FAIL))
if FAILED:
    print("FAILED: " + " | ".join(FAILED[:10]))

if INJECT:
    if FAIL == 0:
        print("GATE LEAK —— 注入 %s 未被拦截（rc=2）" % INJECT)
        sys.exit(2)
    print("GATE BLOCKED 注入 %s（rc=1）" % INJECT)
    sys.exit(1)
if SELFCHECK:
    if FAIL > 0:
        print("GATE FALSE-POSITIVE —— 等价改写被误判（rc=2）")
        sys.exit(2)
    print("GATE PASS (selfcheck: 等价改写放行)")
    sys.exit(0)
if FAIL > 0:
    print("GATE FAIL")
    sys.exit(1)
print("GATE PASS  (B6：DECIMAL STATIC 反解 + DB 回读 + 契约 VACUUM)")
sys.exit(0)
