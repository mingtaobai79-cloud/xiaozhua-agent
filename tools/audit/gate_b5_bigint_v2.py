# -*- coding: utf-8 -*-
"""B5 闸门 v2：SLICE-B5-BIGINTEGER-static.md 一致性校验

v1 事故（本片自查发现，必须记账）：
  12 条注入只拦 4 条 —— N2/N3/N5/N8/N11 全部漏检（rc=2）。
  根因：数字断言写成 has_num(BODY, n)「正文里存在这个数」。
        文档里同一数字出现多次（3628 出现 4 次），改掉 1 处仍有 3 处蒙混；
        "**STATIC**" 同理，改掉表格 1 处，别处还在。
  这是 B4 教训「单边断言等于给自己出简单题」的第 3 次复发。

v2 设计（结构性修正，不是补几条断言）：
  ① 期望整行由基线现算：§4.2 / §4.3 / §一 / §6.1 的行按 B5-DB-FACTS.json 与
     B5-keysets.json 现算成完整字面行，再与文档逐行整行相等比对（不是"包含"）。
  ② 等级 token 做等价类约束：本片只用 STATIC / STATIC-存在 / LIVE/DB / VACUUM /
     UNVERIFIED / BLOCKED；裸 **LIVE** 与 **PASS** 必须 0 出现。
  ③ 键数从反解源现算。
  ④ 负向断言限定契约正文（§九 A/B 对照允许引用错口径）。

退出码：0 全过 / 1 有断言失败(注入被拦) / 2 漏检(注入未拦 或 等价改写被误判) / 3 锚点缺失
"""
import hashlib, json, pathlib, re, sys

REPO = pathlib.Path(r"<SEEYON_AGENT_ROOT>")
DOC = REPO / "docs/audit/entity-field-matrix/SLICE-B5-BIGINTEGER-static.md"
ASSET_E = REPO / "docs/audit/entity-field-matrix/assets/bundle-SEG-E_Etable.js.txt"
ASSET_T = REPO / "docs/audit/entity-field-matrix/assets/bundle-SEG-T_WB_range.js.txt"
ASSET_F = REPO / "docs/audit/entity-field-matrix/assets/bundle-SEG-F_ftable.js.txt"
FACTS = REPO / "docs/audit/artifacts/scratch-migrated/audit-slice-b5/B5-DB-FACTS.json"
KEYSETS = REPO / "docs/audit/artifacts/scratch-migrated/audit-slice-b5/B5-keysets.json"
BUNDLE = REPO / "docs/audit/artifacts/udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js"
EV1 = REPO / "docs/audit/entity-field-matrix/EVIDENCE-batch-contract-live.json"
EV2 = REPO / "docs/audit/entity-field-matrix/EVIDENCE-batch-update-live.json"

ANCHOR_E_INNER = "b1e75e105c0dedefeaec5301fec38d22bbde71df864dc36f47188004b9f1e84f"
SEG_E_SHA = "62869f1230be89074d5974a732eccc5edcb77044e7ea454118245628c589d645"
SEG_T_SHA = "f5483b41efaf6b55546d7f2f3aefb7c8bdd17472791b670ae19ee8527688901e"
SEG_F_SHA = "db90ee1f4d1f8c393de97533f8fdb0b478222e1d1501c0186b4aead08bf21221"
BUNDLE_SHA = "6051e1df6c574df74c842f9e4c0714fae5c7ff0df6e86e5ffa5b2d4f994f387d"
CACHE_SHA = "dec48b500e2c655a1ca279b17d5f6128c8871c1d266f12e49cf0d2ff23345f94"

PASS = 0
FAIL = 0
FAILED_NAMES = []

def ok(cond, name, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("PASS %s%s" % (name, ("  — " + detail) if detail else ""))
    else:
        FAIL += 1
        FAILED_NAMES.append(name)
        print("FAIL %s%s" % (name, ("  — " + detail) if detail else ""))

def sha(b):
    return hashlib.sha256(b).hexdigest()

anchors = {"doc": DOC, "asset_E": ASSET_E, "asset_T": ASSET_T, "asset_F": ASSET_F,
           "facts": FACTS, "keysets": KEYSETS, "bundle": BUNDLE, "ev1": EV1, "ev2": EV2}
for k, p in anchors.items():
    if not p.exists():
        print("ANCHOR NOT FOUND: %s -> %s" % (k, p))
        sys.exit(3)

txt = DOC.read_text(encoding="utf-8")
facts = json.loads(FACTS.read_text(encoding="utf-8"))
keys = json.loads(KEYSETS.read_text(encoding="utf-8"))

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

INJ_TABLE = {
    "N1":  ("| **BIGINTEGER** | **4576** |", "| **BIGINTEGER** | **4577** |",
            "BIGINTEGER 总数 4576→4577"),
    "N2":  ("| **BIGINTEGER** | **4576** | 3628 / 948 / **0** |",
            "| **BIGINTEGER** | **4576** | 3628 / 948 / **1** |",
            "BIGINTEGER min/max 非空 0→1"),
    "N3":  ("`E[BigInteger]` **17 键**", "`E[BigInteger]` **16 键**", "E 表键数 17→16"),
    "N4":  ('[a.BigInteger]:{min:"-9007199254740991"', '[a.BigInteger]:{min:"-9007199254740992"',
            "WB 下界 −1"),
    "N5":  ("| **STATIC：值域边界** | WB 区间表", "| **LIVE：值域边界** | WB 区间表",
            "STATIC 类型标签改成 LIVE"),
    "N6":  ('5 条"非空"全是空壳', '5 条"非空"全是**已配置**', "空壳→已配置"),
    "N7":  ("**键集与 Integer 完全相同**（集合级）", "**键集与 Integer 完全不同**（集合级）",
            "键集相同→不同"),
    "N8":  ("| BIGINTEGER | 1（系统） | 3628 | **3628** | 0 | 0 |",
            "| BIGINTEGER | 1（系统） | 3629 | **3628** | 0 | 0 |",
            "交叉表系统字段 3628→3629"),
    "N9":  ('1. **不得**说"BigInteger 支持值域配置"', '1. **可以**说"BigInteger 支持值域配置"',
            "禁用句式反转"),
    "N10": ("BIGINTEGER 27 = 系统 18 + 业务 9", "BIGINTEGER 28 = 系统 18 + 业务 9",
            "本应用 27→28"),
    "N11": ("| batch DTO 无 BigInteger 字段实例 | **VACUUM** | §5.1 全量正则提取 |",
            "| batch DTO 无 BigInteger 字段实例 | **PASS** | §5.1 全量正则提取 |",
            "VACUUM 冒充 PASS"),
    "N12": (ANCHOR_E_INNER, "0" * 64, "段 sha256 锚被改"),
    "N13": ("| **INTEGER** | **3539** | 2829 / 709 / **1** |",
            "| **INTEGER** | **3539** | 2829 / 709 / **0** |",
            "INTEGER min 非空 1→0"),
    "N14": ("BIGINTEGER 业务字段(948)：max_length 全部 = '20'",
            "BIGINTEGER 业务字段(948)：max_length 全部 = '19'",
            "max_length 20→19"),
    # ★ rc=2 码位可达性专用：语义无害的等价改写（闸门按设计不该抓）
    #   与 --selfcheck 区别：
    #     --selfcheck          期望 rc=0（证明闸门不过度敏感，防假阳性）
    #     --inject SELFCHECK   期望 rc=2（证明"注入已施加但零 FAIL"这条码位真实可达）
    "SELFCHECK": ("## 一、一句话结论\n", "## 一、一句话结论 \n",
                  "等价改写（标题行加尾随空格，语义无害）——2 码位可达性验证"),
}

if SELFCHECK:
    txt = txt.replace("## 一、一句话结论\n", "## 一、一句话结论 \n", 1)

if INJECT:
    if INJECT not in INJ_TABLE:
        print("INJECT KEY NOT FOUND: %s（可用: %s）" % (INJECT, ",".join(sorted(INJ_TABLE))))
        sys.exit(3)
    old, new, desc = INJ_TABLE[INJECT]
    if old not in txt:
        print("INJECT NO-OP（锚点未命中）: %s" % INJECT)
        sys.exit(3)
    txt = txt.replace(old, new, 1)
    print("== 注入 %s: %s ==" % (INJECT, desc))

LINESET = set(l.rstrip() for l in txt.split("\n"))
BODY = txt.split("## 九、")[0]

def has_line(s):
    return s.rstrip() in LINESET

ok(sha(BUNDLE.read_bytes()) == BUNDLE_SHA, "A1 整文件 sha256 锚")
seg_e = ASSET_E.read_text(encoding="utf-8")
ok(sha(seg_e.encode()) == SEG_E_SHA, "A2 SEG-E 段 sha256")
ok(sha(seg_e[2:-1].encode()) == ANCHOR_E_INNER, "A3 SEG-E 内层 == auditor 已钉死锚（跨组互证）")
ok(sha(ASSET_T.read_bytes()) == SEG_T_SHA, "A4 SEG-T(WB) 段 sha256")
ok(sha(ASSET_F.read_bytes()) == SEG_F_SHA, "A5 SEG-F(f表) 段 sha256")
for nm, val in [("A6 SEG-E 内层锚", ANCHOR_E_INNER),
                ("A7 SEG-E 段锚", SEG_E_SHA),
                ("A8 SEG-T 段锚", SEG_T_SHA),
                ("A9 整文件锚", BUNDLE_SHA),
                ("A10 cache 原件锚（差异必须记账）", CACHE_SHA)]:
    ok(val in BODY, nm + " 已载入正文")

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

E_BI, E_IN = keys["E_BigInteger"]["raw"], keys["E_Integer"]["raw"]
F_BI, F_IN = keys["f_BigInteger"]["raw"], keys["f_Integer"]["raw"]
kb, ki, fb, fi = top_keys(E_BI), top_keys(E_IN), top_keys(F_BI), top_keys(F_IN)

ok(len(kb) == 17, "B1 E[BigInteger] 键数=17（现算）", str(len(kb)))
ok(len(fb) == 6, "B2 f[BigInteger] 键数=6（现算）", str(len(fb)))
ok(set(kb) == set(ki), "B3 E 层键集 BigInteger == Integer（集合级）")
ok(set(fb) == set(fi), "B4 f 层键集 BigInteger == Integer（集合级）")
ok(kb != ki, "B5 E 层键序不同（键集同、顺序异）")
ok("min" in kb and "max" in kb, "B6 E[BigInteger] 含 min/max")
ok("min" in fb and "max" in fb, "B7 f[BigInteger] 含 min/max")
ok(keys["f_minmax_count"] == 7, "B8 f 层 min/max 出现在 7/16 张表")
ok(keys["E_minmax_count"] == 7, "B9 E 层 min/max 出现在 7/14 张表")
ok("BigInteger" in keys["f_tables_with_min_max"], "B10 BigInteger 在 f 层值域组内")
ok("BigInteger" in keys["E_tables_with_min_max"], "B11 BigInteger 在 E 层值域组内")
ok(sorted(keys["f_tables_with_min_max"]) == sorted(keys["E_tables_with_min_max"]),
   "B12 f/E 两层值域组集合一致")
ok('dataType:"BIGINTEGER"' in E_BI, "B13 E[BigInteger].dataType=BIGINTEGER")
ok('dataType:"INTEGER"' in E_IN, "B14 E[Integer].dataType=INTEGER")
ok('defaultValue:""' in E_BI, "B15 E[BigInteger].defaultValue 默认空串")
ok("defaultValue:0" in E_IN, "B16 E[Integer].defaultValue 默认 0")
ok("defaultValue:p" in F_BI and "defaultValue:p" in F_IN, "B17 f 层两者默认同为占位 p")

wb = ASSET_T.read_text(encoding="utf-8")
ok('min:"-9007199254740991"' in wb and 'max:"9007199254740991"' in wb,
   "B18 WB BigInteger 边界 ±(2^53−1)，字符串形态")
ok("min:-2147483648" in wb and "max:2147483647" in wb, "B19 WB Integer 边界 ±2^31，数值形态")
ok(has_line('   [a.BigInteger]:{min:"-9007199254740991",max:"9007199254740991"},'),
   "B20 正文 WB 表 BigInteger 行逐字一致")
ok(has_line('   [a.Integer]:{min:-2147483648,max:2147483647},'),
   "B21 正文 WB 表 Integer 行逐字一致")
ok(("`E[BigInteger]` **%d 键**" % len(kb)) in BODY, "B22 正文 E 键数与现算一致(%d)" % len(kb))
ok(("`f[BigInteger]` **%d 键**" % len(fb)) in BODY, "B23 正文 f 键数与现算一致(%d)" % len(fb))

# ---- 偏移口径（auditor 045650Z §五 提醒：字符偏移 vs 字节偏移 差恒 67252，必须可机验）----
_txt = BUNDLE.read_bytes().decode("utf-8")
_raw = BUNDLE.read_bytes()
SEGS = [("SEG-E", 'E={[a.String]:{dataType:"STRING"'), ("SEG-T", 'T={[a.String]:{min:0,max:4e3}'),
        ("SEG-F", 'f={[a.String]:{defaultValue:p,')]
_anchor = json.loads((REPO / "docs/audit/artifacts/scratch-migrated/audit-slice-b5/B5-anchors.json").read_text(encoding="utf-8"))
ok(all((_raw.find(m.encode()) - _txt.find(m)) == 67252 for _, m in SEGS),
   "B24 字符偏移与字节偏移差恒 67252（三个段落起点逐个实测）")
ok(all(_anchor[k]["offset_start"] == _txt.find(m) for k, m in
       [("SEG-E_Etable", SEGS[0][1]), ("SEG-T_WB_range", SEGS[1][1]), ("SEG-F_ftable", SEGS[2][1])]),
   "B25 B5-anchors.json 记录的 offset_start 确为字符偏移（与正文表一致）")
ok("字符偏移（非字节）" in BODY, "B26 正文表头已标明偏移口径（防读者误判自相矛盾）")

ok(facts["counts"]["BIGINTEGER"] == 4576, "C1 BIGINTEGER 总数=4576")
ok(facts["counts"]["INTEGER"] == 3539, "C2 INTEGER 总数=3539（B2 基线）")
ok(facts["is_system_counts"]["BIGINTEGER"]["1"] == 3628, "C3 BIGINTEGER 系统=3628")
ok(facts["is_system_counts"]["BIGINTEGER"]["0"] == 948, "C4 BIGINTEGER 业务=948")
ok(facts["is_system_counts"]["INTEGER"]["1"] == 2824, "C5 INTEGER 系统=2824")
ok(facts["is_system_counts"]["INTEGER"]["0"] == 715, "C6 INTEGER 业务=715")

sbi = facts["states"]["BIGINTEGER"]
sin = facts["states"]["INTEGER"]

def row42(dtname, cnt, mn, mx, mn_ne, mx_ne):
    return "| **%s** | **%d** | %d / %d / **%d** | %d / %d / **%d** |" % (
        dtname, cnt, mn["null_n"], mn["empty_n"], mn_ne, mx["null_n"], mx["empty_n"], mx_ne)

exp_bi = row42("BIGINTEGER", facts["counts"]["BIGINTEGER"], sbi["all_min"], sbi["all_max"],
               sbi["all_min"]["nonempty_n"], sbi["all_max"]["nonempty_n"])
exp_in = row42("INTEGER", facts["counts"]["INTEGER"], sin["all_min"], sin["all_max"],
               sin["all_min"]["nonempty_n"], sin["all_max"]["nonempty_n"])
ok(has_line(exp_bi), "C7 §4.2 BIGINTEGER 行逐字一致", exp_bi)
ok(has_line(exp_in), "C8 §4.2 INTEGER 行逐字一致", exp_in)
ok(sbi["all_min"]["nonempty_n"] == 0 and sbi["all_max"]["nonempty_n"] == 0,
   "C9 BIGINTEGER min/max 非空均为 0")
ok(sin["all_min"]["nonempty_n"] == 1 and sin["all_max"]["nonempty_n"] == 0,
   "C10 INTEGER min 非空=1 / max 非空=0（B2 基线）")

def row43(dtname, syslbl, total, mn_null, mn_empty, mn_ne):
    # 列序：total | min NULL | min 空串 | min 非空
    # 加粗规则：三态中数值最大的那一格加粗（文档以此突出主体）
    vals = [mn_null, mn_empty, mn_ne]
    mx = max(vals)
    idx = vals.index(mx)
    cells = [str(mn_null), str(mn_empty), str(mn_ne)]
    cells[idx] = "**%d**" % mx
    return "| %s | %s | %d | %s | %s | %s |" % (dtname, syslbl, total, cells[0], cells[1], cells[2])

for dtkey, dtname, sysflag, syslbl in [
    ("BIGINTEGER", "BIGINTEGER", 1, "1（系统）"),
    ("BIGINTEGER", "BIGINTEGER", 0, "0（业务）"),
    ("INTEGER", "INTEGER", 1, "1（系统）"),
    ("INTEGER", "INTEGER", 0, "0（业务）"),
]:
    mn = facts["states"][dtkey]["sys_" + str(sysflag)]["min"]
    exp = row43(dtname, syslbl, mn["total"], mn["null_n"], mn["empty_n"], mn["nonempty_n"])
    ok(has_line(exp), "C11 §4.3 行逐字一致 [%s %s]" % (dtname, syslbl), exp)

ok(sbi["sys_1"]["min"]["null_n"] == sbi["sys_1"]["min"]["total"], "C12 BIGINTEGER 系统字段 min 全 NULL")
ok(sbi["sys_0"]["min"]["empty_n"] == sbi["sys_0"]["min"]["total"], "C13 BIGINTEGER 业务字段 min 全空串")
ok(sin["sys_1"]["min"]["null_n"] == sin["sys_1"]["min"]["total"], "C14 INTEGER 系统字段 min 全 NULL")
_b = sin["sys_0"]["min"]
ok(_b["empty_n"] + _b["null_n"] + _b["nonempty_n"] == _b["total"],
   "C15 INTEGER 业务字段 min 三态之和=总数（5 个 NULL 例外如实保留）",
   "%d+%d+%d=%d" % (_b["empty_n"], _b["null_n"], _b["nonempty_n"], _b["total"]))

vd = facts["vse_nonempty_distinct"]["BIGINTEGER"]
ok(facts["vse_empty_shell_count_BIGINTEGER"] == 5, "C16 BIGINTEGER vse 非空 5 条全空壳")
ok(len(vd) == 1 and vd[0]["vse"] == '{"min":"","max":""}',
   "C17 BIGINTEGER 非空 vse 去重仅 1 值（空壳原文）")
ok(facts["vse_empty_shell_count_INTEGER"] == 1, "C18 INTEGER vse 非空 1 条也是空壳")
ok(has_line('{"min":"","max":""}    →  5 条'), "C19 正文 vse 去重分布行逐字一致")
ok(has_line("（去重后仅此 1 种值）"), "C20 正文声明去重仅 1 值")

ok(facts["max_length_dist_business"]["BIGINTEGER"][0]["ml"] == "20", "C21 BIGINTEGER 业务 max_length=20")
ok(facts["max_length_dist_business"]["INTEGER"][0]["ml"] == "10", "C22 INTEGER 业务 max_length=10")
ok(has_line("BIGINTEGER 业务字段(948)：max_length 全部 = '20'"), "C23 正文 max_length 行逐字一致")
ok(has_line("INTEGER   业务字段(715)：max_length 全部 = '10'"), "C24 正文 INTEGER max_length 行逐字一致")

r = facts["integer_min_nonempty_rows"]
ok(len(r) == 1 and r[0]["name"] == "gongGuanZhangHuID" and r[0]["min"] == "0",
   "C25 INTEGER 唯一非空 min = 共管账户ID 的 '0'")

ok(facts["app_bigint"]["total"] == 27, "C26 本应用 BIGINTEGER=27")
ok(facts["app_bigint"]["system"] == 18 and facts["app_bigint"]["business"] == 9,
   "C27 本应用 18 系统 + 9 业务")
ok(has_line("BIGINTEGER 27 = 系统 18 + 业务 9"), "C28 正文本应用拆分行逐字一致")
ok(facts["total_all_types"] == 67864, "C29 全库总行数=67864")

ok("**VACUUM**" in BODY, "D1 正文存在 VACUUM 判定")
ok(BODY.count("**VACUUM**") == 3, "D3 VACUUM 恰好 3 处（§一 + §5.1 结论 + §6.1 证据表）",
   "count=%d" % BODY.count("**VACUUM**"))
ok("**PASS**" not in BODY, "D3 正文不得出现 **PASS**（本片无 PASS 级结论）")
ok("**LIVE**" not in BODY, "D4 正文不得出现裸 **LIVE**（只允许 **LIVE/DB**）")
ok(BODY.count("**LIVE/DB**") >= 4, "D5 LIVE/DB 标注存在", "count=%d" % BODY.count("**LIVE/DB**"))
ok("**STATIC**" in BODY, "D6 STATIC 标注存在")
ok("**STATIC-存在**" in BODY, "D7 WB 表用 STATIC-存在（不主张生效）")
ok("**UNVERIFIED**" in BODY, "D8 UNVERIFIED 标注存在")
ok("**BLOCKED**" in BODY, "D9 BLOCKED 标注存在")

CONCL = [
    "| **STATIC：BigInteger 类型表键集** | `E[BigInteger]` **17 键**、`f[BigInteger]` **6 键**，**键集与 Integer 完全相同**（集合级），仅 `dataType` 字面量与 `defaultValue` 默认值两处不同 | **STATIC** |",
    "| **STATIC：min/max 归属** | `min`/`max` 同时出现在 **7/14** 张 E 表与 7/16 张 f 表，BigInteger **在组内**（与 Integer/Decimal/Currency/Date/Time/DateTime 同组） | **STATIC** |",
    "| **STATIC：值域边界** | WB 区间表：BigInteger = **±9007199254740991（2^53−1，字符串形态）**；Integer = ±2147483648/2147483647（数值形态） | **STATIC** |",
    "| **DB：BigInteger 全库** | **4576** 行；`min` 非空 **0**、`max` 非空 **0**；与 INTEGER **3539** 行 / min 非空 **1** / max 非空 **0** 同表对照 | **LIVE/DB** |",
    "| **DB：vse 非空** | 5 条\"非空\"全是空壳 `{\"min\":\"\",\"max\":\"\"}`，去重后仅 1 种值 ⇒ **非空 ≠ 配过值域** | **LIVE/DB** |",
    "| **契约对照：batch DTO** | 两份 EVIDENCE 中**无任何字段级 BIGINTEGER 实例**（DTO 的 dataType 仅见 STRING/INTEGER/CTPENUM/ENTITY/DATETIME/BOOLEAN） | **VACUUM** |",
    "| **触发条件充分性** | BigInteger 与 Integer 键集相同 ⇒ 键集**无类型判别力**，无法由键集反推\"当前是 BigInteger\" | **UNVERIFIED** |",
    "| **页面可交互配值域** | 需页面腿，登录态冻结 | **BLOCKED** |",
]
for n, line in enumerate(CONCL, 1):
    ok(has_line(line), "E%d §一 结论行逐字一致 [%d/8]" % (n, n))

GRADE_ROWS = [
    "| E[BigInteger] 17 键 / f[BigInteger] 6 键 | **STATIC** | SEG-E、SEG-F 段落级反解 + 双 sha256 |",
    "| BigInteger 与 Integer 键集恒等 | **STATIC** | 集合比对（不是比键数） |",
    "| min/max 在 7/14 类型表内，BigInteger 在组内 | **STATIC** | 14 表逐表扫 |",
    "| WB 边界 ±(2^53−1)，形态为字符串 | **STATIC-存在** | SEG-T 段落；**未找到调用点**，不主张生效 |",
    "| BIGINTEGER 全库 4576，min/max 非空 0/0 | **LIVE/DB** | SELECT 原文见 §4.2 |",
    "| min NULL=系统字段数、空串=业务字段数（零残差） | **LIVE/DB** | 交叉表 §4.3 |",
    "| vse 非空 5 条全空壳 | **LIVE/DB** | 去重仅 1 值 §4.4 |",
    "| 本应用 27 个 BIGINTEGER（18 系统 + 9 业务），全部未配值域 | **LIVE/DB** | §4.7 |",
    "| batch DTO 无 BigInteger 字段实例 | **VACUUM** | §5.1 全量正则提取 |",
    "| BigInteger 字段的请求 DTO 实际形态 | **UNVERIFIED** | 无实例，需页面腿 |",
    "| 触发条件（何时走重建分支） | **UNVERIFIED** | 沿用 B4 结论，n=1 |",
    "| 页面可交互配值域 | **BLOCKED** | 登录态冻结 |",
]

def _sec61_data_rows(t):
    """从文档动态抽取 §6.1 表的数据行（不含表头与分隔行）。
    比对表必须覆盖全表：覆盖数由文档现算，不能由闸门自己说了算。"""
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
        if set(cells[0]) <= set("-: "):      # 分隔行
            continue
        if cells[0] == "结论":                # 表头
            continue
        rows.append(s)
    return rows

_doc_rows = _sec61_data_rows(txt)
ok(len(GRADE_ROWS) == len(_doc_rows),
   "F0 §6.1 比对表必须覆盖全表（比对表 %d 条 vs 文档 %d 数据行）" % (len(GRADE_ROWS), len(_doc_rows)))
for n, line in enumerate(GRADE_ROWS, 1):
    ok(has_line(line), "F%d §6.1 等级行逐字一致 [%d/%d]" % (n, n, len(GRADE_ROWS)))

ok("## 九、" in txt, "G1 存在 §九（负向断言作用域分界）")
NEG = [
    (r"\| \*\*BIGINTEGER\*\* \| \*\*4577", "BIGINTEGER 总数 4577"),
    (r"\| \*\*BIGINTEGER\*\* \| \*\*4576\*\* \| \d+ / \d+ / \*\*1\*\* \|", "BigInteger min/max 非空写成 1"),
    (r"已配置", "把空壳说成已配置"),
    (r"9007199254740992", "WB 边界多 1"),
    (r"键集与 Integer 完全不同", "键集相同被说成不同"),
    (r"\*\*可以\*\*说", "禁用句式被反转"),
    (r"BIGINTEGER 28 = 系统 18", "本应用计数改错"),
    (r"\*\*LIVE\*\*", "出现裸 LIVE"),
    (r"\*\*PASS\*\*", "出现 PASS（本片无此等级）"),
]
for pat, desc in NEG:
    ok(re.search(pat, BODY) is None, "H1 负向：正文不含「%s」" % desc)

def dtypes_of(p):
    s = p.read_text(encoding="utf-8")
    return set(re.findall(r'"dataType"\s*:\s*"([A-Z_]+)"', s)), s

dt1, raw1 = dtypes_of(EV1)
dt2, raw2 = dtypes_of(EV2)
ok("BIGINTEGER" not in dt1, "I1 ev1 DTO dataType 无 BIGINTEGER", str(sorted(dt1)))
ok("BIGINTEGER" not in dt2, "I2 ev2 DTO dataType 无 BIGINTEGER", str(sorted(dt2)))
ok("BIGINTEGER" in raw1 and "BIGINTEGER" in raw2,
   "I3 EVIDENCE 文本内确实含 BIGINTEGER（系统变量 dataType）——grep 会假阳性")
ok("defaultValueSystemVariable" in raw1, "I4 该 BIGINTEGER 出现在 defaultValueSystemVariable 内")
ok("currentUserId" in raw1, "I5 系统变量名为 currentUserId（登录人员ID）")

# ---------------- 6. 结构性存在断言（防"整段删除"绕过，auditor 045917Z §三 ②③）----------------
# 整段删除是文档闸门最经典的绕过路径（B4 的 M7 同类）。
# 只断言"某标题存在"不够——必须断言段内**关键条目的编号与首句**都在。
ok(BODY.count("### 6.2") == 1, "J1 §6.2「明确不主张」段存在")
for n, head in enumerate([
    "1. **不得**说\"BigInteger 支持值域配置\"",
    "2. **不得**说\"键数/键集能判别 BigInteger\"",
    "3. **不得**说\"WB 边界生效\"",
    "4. **不得**说\"BigInteger 提交必传字符串\"",
    "5. **不得**把 vse 非空的 5 条当\"已配值域\"",
    "6. **不得**把系统字段的 `min IS NULL` 与业务字段的 `min=''` 合并成",
], 1):
    ok(head in BODY, "J2 §6.2 第 %d 条禁令仍在（整段删除防护）" % n)
ok(BODY.count("### 5.2") == 1, "J3 §5.2「grep 假阳性」段存在")
for n, frag in enumerate([
    "「BIGINTEGER」在 EVIDENCE 里出现过，但不是字段类型",
    "这是**系统变量自身的数据类型声明**",
    "用 `grep BIGINTEGER` 会得到\"存在 BigInteger 契约\"的假阳性",
], 1):
    ok(frag in BODY, "J4 §5.2 关键说明第 %d 句仍在（最诚实处理不得被静默抹掉）" % n)
ok(BODY.count("#### ") >= 0 and "### 6.1 证据等级" in BODY, "J5 §6.1 证据等级段存在")

print()
print("SUMMARY PASS=%d FAIL=%d" % (PASS, FAIL))
if FAILED_NAMES:
    print("FAILED: " + " | ".join(FAILED_NAMES[:10]))

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
print("GATE PASS  (B5：BigInteger STATIC 反解 + DB 回读 + 契约 VACUUM)")
sys.exit(0)
