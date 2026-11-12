# -*- coding: utf-8 -*-
"""落位测试：平台「包用法」事实（环境无关）+ 仓内 skill + 证据必须齐。

锁住五件事：
  ① 四格环境无关事实在 core/facts/standard-product/，且各有「## 铁律」区块
  ② 仓内 skill skills/02-udc/xiaozhua-extension-usage/SKILL.md 存在且在 skills/README.md 登记
  ③ 三格后端事实**不得**出现工程/环境标识（客户 appId、本机工程路径）——这是本轮返工的主因
  ④ 证据区存在方法签名件，且**签名件本身**不含工程/环境标识
  ⑤ core/facts/INDEX.md 已登记这四格
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACT_DIR = ROOT / "core" / "facts" / "standard-product"
EVID = ROOT / "docs" / "audit" / "artifacts" / "extension-surface-20261029"
SKILL = ROOT / "skills" / "02-udc" / "xiaozhua-extension-usage" / "SKILL.md"

FACTS = [
    "platform-package-capability-index.md",
    "transport-usage.md",
    "appservice-usage.md",
    "dao-and-mybatis.md",
    "standard-product-appservice-surfaces.md",
    "dubbo-cross-service.md",
    "boot-core-utils-and-annotations.md",
    "udc-runtime-and-extend-packages.md",
    "frontend-platform-packages.md",
    "frontend-package-capability-index.md",
    "frontend-component-signatures.md",
    "udc-microflow-extend-interfaces.md",
]

# 后端分层必须每层都有事实（用户点名的三层 + 标品接口面 + 跨服务）
BACKEND_LAYERS = {
    "dao-and-mybatis.md": ["AllInOneBaseDao", "BaseMybatisDao"],
    "appservice-usage.md": ["SingleRequest", "AppServiceContext"],
    "standard-product-appservice-surfaces.md": [
        "OrgCommonAppService", "BpmAppService", "BpmUdcApiService",
        "AffairCommonAppService", "StorageService", "CtpEnumItemService",
        "SystemVariableUtils", "LinkerAppService",
    ],
    "dubbo-cross-service.md": ["DubboFactory", "AppServiceProxy"],
    "boot-core-utils-and-annotations.md": ["JsonUtils", "OpenApi", "EntityEncryption"],
}

# 前端分层必须每层都有事实
FRONTEND_LAYERS = {
    "frontend-platform-packages.md": [
        "@seeyon/ui", "@seeyon/global", "@seeyon/udc-runtime-core",
        "customPage.tsx", "useSyHistory", "third_modules",
    ],
    # 50 包能力地图：必须覆盖能力映射、SDK 桥、递归铁律、无类型包四件事
    "frontend-package-capability-index.md": [
        "@seeyon/biz-org-selector", "@seeyon/biz-excel-component",
        "getComiSDK", "re-export", "mbiz-new-report",
    ],
    # 组件传参：必须同时有 props 表、三类形态、表达式函数和三件套铁律
    "frontend-component-signatures.md": [
        "ExcelImportModalProp", "OrgSelectorProps", "visible", "onClose", "onOk",
        "addHour", "dateDiff", "appId",
    ],
    # 自定义微流程接口：四族 + 被调入口 + 组织构造 + transport 铁律
    "udc-microflow-extend-interfaces.md": [
        "MetaDataPostProcessor", "SaveAsHandler", "ImporterBase", "TransportHandler",
        "invokeAppServiceMethod", "MicroFlowRestPathMetadataDto",
        "MicroFlowOrgPeopleService", "getData().getContent()",
    ],
}

# 环境/工程标识形态（结论区禁用）
# SYNTHETIC-FIXTURE: 本行是**判据定义**（客户标识识别用的正则），不是泄漏数据。
# 第 49 轮收紧「词根+分隔符+数字」判据后，这条定义会命中它自己 —— 按第 47 轮判据
# 「脱敏规则只能引用不能复写」，凡必须复写处一律打行级标记，不做文件级豁免。
RE_CUSTOMER_APP = re.compile(r"datamigration(?!9000000000000000\d{3})\d{6,}")  # SYNTHETIC-FIXTURE
RE_LOCAL_PROJECT = re.compile(r"[A-Za-z]:[/\\](?:work|repo|software)[/\\]", re.I)
RE_ORG = re.compile("changhong" + "it" + r"|长虹" + "佳华")
# 本地仓库 / 本地制品路径：结论区只写 Maven 坐标，不写任何本机路径
RE_LOCAL_REPO = re.compile(r"<repo>|~/\.m2|\.m2[/\\]repository|D:/repo|repo/CHIT", re.I)


def _fact_texts():
    for f in FACTS:
        p = FACT_DIR / f
        assert p.exists(), f"事实件缺失：{p}"
        yield f, p.read_text(encoding="utf-8", errors="replace")


def test_facts_exist_and_have_iron_rules():
    for f, t in _fact_texts():
        assert "## 铁律" in t, f"{f} 缺 `## 铁律` 区块"
        for sec in ("## 1. Capability", "## 8. Evidence", "## 9. Verified"):
            assert sec in t, f"{f} 缺 {sec}"


def test_facts_are_environment_neutral():
    """结论区不得带工程/环境标识 —— 换环境仍要成立。"""
    for f, t in _fact_texts():
        bad = []
        if RE_CUSTOMER_APP.search(t):
            bad.append("客户应用名")
        if RE_LOCAL_PROJECT.search(t):
            bad.append("本机工程路径")
        if RE_ORG.search(t):
            bad.append("客户组织")
        if RE_LOCAL_REPO.search(t):
            bad.append("本地仓库/制品路径")
        assert not bad, f"{f} 含环境相关标识：{bad}"


def test_backend_facts_only_describe_package_usage():
    """后端三格只讲包内用法：引用了包名/类名，且不引用具体工程构件版本组合。"""
    for f in ("transport-usage.md", "appservice-usage.md", "udc-runtime-and-extend-packages.md"):
        t = (FACT_DIR / f).read_text(encoding="utf-8", errors="replace")
        assert "com.seeyon" in t, f"{f} 未引用平台包路径"
        # 不允许出现「本工程 parent pom」这类叙述
        for banned in ("parent pom", "ext 工程自己的 pom"):
            assert banned not in t, f"{f} 出现工程相关叙述：{banned}"


def test_repo_skill_exists_and_registered():
    assert SKILL.exists(), f"仓内 skill 缺失：{SKILL.relative_to(ROOT)}"
    t = SKILL.read_text(encoding="utf-8", errors="replace")
    assert t.startswith("---"), "SKILL.md 缺 YAML frontmatter"
    assert "name: xiaozhua-extension-usage" in t, "SKILL.md name 不符"
    assert "## When to Use" in t, "SKILL.md 缺 `## When to Use`"
    # skill 不得内联事实全文：应指向仓库事实路径
    assert "core/facts/standard-product/" in t, "SKILL.md 未指向事实格（单向引用）"
    # 必须在 skills/README.md 登记
    readme = (ROOT / "skills" / "README.md").read_text(encoding="utf-8", errors="replace")
    assert "xiaozhua-extension-usage" in readme, "skills/README.md 未登记该 skill"


def test_evidence_symbols_present_and_neutral():
    """证据必须齐：batch2 的标品构件（>=84，含后补的 udc-biz 等）+ 单独保留的 udc-extend，
    且证据本身不含工程/环境标识。"""
    assert EVID.is_dir(), f"缺证据目录 {EVID.relative_to(ROOT)}"
    b2 = EVID / "batch2"
    syms = sorted(p for p in b2.glob("*.json") if not p.name.startswith("_"))
    assert len(syms) >= 84, f"batch2 签名件至少 84 个（实有 {len(syms)}）"
    # 后补的关键构件必须在（udc-biz 曾整包漏抽，导致扩展点数不出来）
    for must in ("udc-biz", "udc-web", "udc-cicd", "app-approval-facade", "m5-facade"):
        assert (b2 / f"{must}.json").exists(), f"batch2 缺 {must}.json"
    # udc-extend 不在 84 包清单内，必须单独保留
    keep = EVID / "symbols-udc-extend.json"
    assert keep.exists(), "symbols-udc-extend.json 缺失（该包未被 batch2 覆盖，不可删）"
    for s in syms + [keep]:
        t = s.read_text(encoding="utf-8", errors="replace")
        assert not RE_CUSTOMER_APP.search(t), f"{s.name} 含客户应用名（签名件应环境无关）"
        assert "jar_path_hint" in t, f"{s.name} 缺 jar_path_hint（无法追溯 artifact）"


def test_fact_evidence_references_exist():
    """事实格 §8 引用的证据文件必须真实存在 —— 防止改了引用却没改文件、或删了文件没改引用。"""
    for fname, _ in _fact_texts():
        t = (FACT_DIR / fname).read_text(encoding="utf-8", errors="replace")
        # 宽松匹配：batch2/ 后面任何不含空白与分隔符的 token，非 ASCII 也要抓
        for ref in set(re.findall(r"batch2/([^\s`'\"()（）\[\]，。、；]+)", t)):
            ref = ref.rstrip(".,;:")
            if not ref.endswith(".json"):
                continue
            if "<" in ref or ">" in ref:      # <artifact>.json 这类占位符，不是真实引用
                continue
            p = EVID / "batch2" / ref
            assert p.exists(), f"{fname} 引用了不存在的证据：batch2/{ref}"
        # symbols-*.json 同样宽松，覆盖非 ASCII 名
        for ref in set(re.findall(r"(symbols-[^\s`'\"()（）\[\]，。、；]+\.json)", t)):
            if "<" in ref or ">" in ref:
                continue
            p = EVID / ref
            assert p.exists(), f"{fname} 引用了不存在的证据：{ref}"


def test_engineering_evidence_is_marked_not_conclusion():
    """工程相关采集产物留在证据区，且 README 明确标注不作结论引用。"""
    rd = EVID / "README.md"
    assert rd.exists(), "证据目录缺 README（未标注哪些是环境证据）"
    t = rd.read_text(encoding="utf-8", errors="replace")
    assert "surface.json" in t, "README 未说明 surface.json 的性质"
    assert "不作结论引用" in t or "环境证据" in t, "README 未标注该产物不作结论引用"


def test_backend_layers_all_recorded():
    """后端三层（Dao/Service/AppService）+ 标品接口面 + 跨服务，每层都要有事实。"""
    for fname, needles in BACKEND_LAYERS.items():
        t = (FACT_DIR / fname).read_text(encoding="utf-8", errors="replace")
        for n in needles:
            assert n in t, f"{fname} 缺后端分层要素：{n}"


def test_frontend_layers_all_recorded():
    """前端：组件层/请求层/运行时层/入口文件/跳转/三方库，每层都要有事实。"""
    for fname, needles in FRONTEND_LAYERS.items():
        t = (FACT_DIR / fname).read_text(encoding="utf-8", errors="replace")
        for n in needles:
            assert n in t, f"{fname} 缺前端分层要素：{n}"


def test_batch_evidence_complete():
    """84 个包的抽取必须全成功，且汇总数字与索引一致。"""
    import json
    b2 = EVID / "batch2"
    prog = b2 / "_progress.jsonl"
    assert prog.exists(), "缺 batch2/_progress.jsonl"
    rows = [json.loads(l) for l in prog.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 84, f"应 84 条记录，实有 {len(rows)}"
    assert all(r.get("ok") for r in rows), "存在抽取失败的包"
    assert all((r.get("methods") or 0) > 0 for r in rows), "存在方法数为 0 的包（解析器失效）"

    idx = b2 / "_index.json"
    assert idx.exists(), "缺 batch2/_index.json"
    d = json.loads(idx.read_text(encoding="utf-8"))
    tot = d["totals"]
    assert tot["packages"] == 84, f"索引包数 {tot['packages']} != 84"
    assert tot["classes"] > 7000, f"类总数异常：{tot['classes']}"
    assert tot["methods"] > 70000, f"方法总数异常：{tot['methods']}"
    # 方法索引必须真的建起来了
    assert len(d["method_index"]) > 60000, f"方法索引过少：{len(d['method_index'])}"


def test_index_registered():
    idx = (ROOT / "core" / "facts" / "INDEX.md").read_text(encoding="utf-8", errors="replace")
    assert "transport-usage.md" in idx, "INDEX.md 未登记 transport-usage.md"
    assert "frontend-platform-packages.md" in idx, "INDEX.md 未登记 frontend-platform-packages.md"
    # 旧的、已删除的路径不应还挂在 INDEX 里
    assert "udc/extension/（4 格" not in idx, "INDEX.md 仍指向已删除的 udc/extension 目录"


def test_old_env_dependent_facts_removed():
    """旧的四格（带工程信息）必须已删除，不能再被检索到。"""
    old = ROOT / "core" / "facts" / "udc" / "extension"
    assert not old.exists(), f"旧目录仍存在：{old.relative_to(ROOT)}"
    for name in ("dependency-surface.md", "backend-extension-contract.md",
                 "frontend-component-usage.md", "project-layout-and-git.md"):
        assert not (old / name).exists(), f"旧事实件仍存在：{name}"


# ---------------------------------------------------------------- 前端 50 包能力面

EXTRACTOR = ROOT / "tools" / "core" / "platform" / "extract_extension_surface.py"


def _latest_frontend_surface():
    cands = sorted((ROOT / "docs" / "audit" / "artifacts").glob("frontend-surface-*/surface.json"))
    assert cands, "缺前端抽取产物 docs/audit/artifacts/frontend-surface-*/surface.json"
    return cands[-1]


def test_frontend_extractor_recurses_and_gates():
    """前端抽取必须递归 + 有失败闸门。

    历史事故：入口 d.ts 多为 `export * from './x'` 壳，只解析一层会得到 0 符号却 exit 0，
    证据区因此躺着 47/50 个空壳包却看着全绿。递归与闸门缺一不可。
    """
    t = EXTRACTOR.read_text(encoding="utf-8", errors="replace")
    assert "def parse_dts_exports_deep" in t, "抽取器缺递归解析函数"
    assert "parse_dts_exports_deep(cand, pkg)" in t, "find_xiaozhua_packages 未调用递归解析"
    assert "RE_EXPORT_ANY" in t, "缺 `export {A}`（先 import 再导出，无 from）解析"
    assert "RE_DECL_TOP" in t, "缺文件级 declare（无 export 前缀）解析"
    assert "return 5" in t, "缺「有 d.ts 却 0 符号」的失败闸门"


def test_frontend_surface_artifact_complete():
    import json
    p = _latest_frontend_surface()
    d = json.loads(p.read_text(encoding="utf-8"))
    pkgs = d["sources"]["frontend"]["xiaozhua_packages"]
    assert len(pkgs) == 50, f"应 50 个 @seeyon 包，实有 {len(pkgs)}"
    empty = [x["package"] for x in pkgs
             if (x.get("symbols") or {}).get("files_scanned")
             and not (x.get("symbols") or {}).get("symbol_count")]
    assert not empty, f"存在有 d.ts 却 0 符号的空壳包：{empty}"
    total = sum(x["symbols"]["symbol_count"] for x in pkgs)
    assert total > 1800, f"导出符号总数异常：{total}"
    by = {x["package"]: x["symbols"]["symbol_count"] for x in pkgs}
    for name, floor in (("@seeyon/udc-runtime-core", 400), ("@seeyon/global", 300),
                        ("@seeyon/ui", 100), ("@seeyon/biz-org-selector", 200)):
        assert by.get(name, 0) >= floor, f"{name} 符号过少（{by.get(name)}），递归可能失效"
    for x in pkgs:
        s = x.get("symbols") or {}
        if s.get("symbol_count"):
            assert s.get("entry", "").endswith(".d.ts"), f"{x['package']} 入口不是 .d.ts"


def test_frontend_index_registered():
    idx = (ROOT / "core" / "facts" / "INDEX.md").read_text(encoding="utf-8", errors="replace")
    assert "frontend-package-capability-index.md" in idx, "INDEX.md 未登记前端 50 包能力地图"


def test_frontend_signatures_artifact_complete():
    """组件签名面：props 字段必须真抽到（不是只有类型名）。"""
    import json
    cands = sorted((ROOT / "docs" / "audit" / "artifacts").glob("frontend-surface-*/signatures.json"))
    assert cands, "缺签名产物 signatures.json"
    d = json.loads(cands[-1].read_text(encoding="utf-8"))
    pk = d["sources"]["frontend"]["packages"]
    assert len(pk) >= 45, f"签名包数过少：{len(pk)}"
    n_comp = sum(len(p.get("components", {})) for p in pk.values())
    n_props = sum(len(p.get("props_types", {})) for p in pk.values())
    n_fn = sum(len(p.get("functions", {})) for p in pk.values())
    assert n_comp >= 100, f"组件数过少：{n_comp}（组件声明形态解析可能失效）"
    assert n_props >= 600, f"props 类型过少：{n_props}"
    assert n_fn >= 250, f"函数签名过少：{n_fn}"
    # 抽验：ExcelImportModal 的 24 个字段必须逐字在
    ex = pk["@seeyon/biz-excel-component"]["components"]["ExcelImportModal"]
    names = {f["name"] for f in ex.get("props") or []}
    for must in ("appId", "entityName", "fileName", "onClose"):
        assert must in names, f"ExcelImportModal 缺必填字段 {must}"
    # 表达式引擎的函数签名必须带参数表
    fn = pk["@seeyon/biz-expression-engine"]["functions"]
    assert "addHour" in fn and "d" in fn["addHour"]["args"], "addHour 签名缺参数名"


def test_frontend_component_props_coverage():
    """组件 props 覆盖率：抽到字段才算数；antd 派生必须标来源。

    踩过的坑：组件数看着够，但一半组件的 props 是空的（`React.FC<AlertProps>` 里的
    AlertProps 来自 antd，只扫包内 d.ts 就抽不到），等于「知道组件存在但不知道怎么传参」。
    """
    import json

    cands = sorted((ROOT / "docs" / "audit" / "artifacts").glob("frontend-surface-*/signatures.json"))
    assert cands, "缺签名产物 signatures.json"
    d = json.loads(cands[-1].read_text(encoding="utf-8"))
    pk = d["sources"]["frontend"]["packages"]
    comps = [(n, c, i) for n, p in pk.items() for c, i in (p.get("components") or {}).items()]
    withp = [x for x in comps if x[2].get("props")]
    ratio = len(withp) / len(comps)
    assert len(withp) >= 100, f"有 props 的组件只有 {len(withp)} 个（< 100）"
    assert ratio >= 0.85, f"props 覆盖率 {ratio:.0%}（< 85%）——外部类型解析可能失效"

    # antd / rc-slider 派生的必须标 propsFrom，否则下游分不清字段归属
    from_ext = [x for x in withp if x[2].get("propsFrom")]
    assert len(from_ext) >= 12, f"标了 propsFrom 的只有 {len(from_ext)} 个"

    ui = pk.get("@seeyon/ui") or {}
    alert = (ui.get("components") or {}).get("Alert") or {}
    assert (alert.get("propsFrom") or "").startswith("antd:"), "Alert 的 propsFrom 没指向 antd"
    names = {f["name"] for f in alert.get("props") or []}
    for must in ("message", "description", "closable", "onClose", "showIcon"):
        assert must in names, f"Alert 缺 antd 字段 {must}"

    # 泛型类型别名必须能展开（`type CusTomTreeSelectProps<T> = Omit<…> & {…}`）
    ts = (ui.get("components") or {}).get("TreeSelect") or {}
    ts_names = {f["name"] for f in ts.get("props") or []}
    for must in ("pageId", "dataType", "displaySize"):
        assert must in ts_names, f"TreeSelect 缺平台扩展字段 {must}（泛型别名未展开）"


def test_backend_interfaces_artifact_complete():
    """自定义微流程接口面：四族扩展点必须齐，否则写扩展会挂错钩子。"""
    import json
    p = ROOT / "docs" / "audit" / "artifacts" / "extension-surface-20261029" / "interfaces.json"
    assert p.exists(), "缺 interfaces.json（后端接口面未归纳）"
    d = json.loads(p.read_text(encoding="utf-8"))
    cs = d["classes"]
    assert len(cs) >= 1000, f"类数过少：{len(cs)}"
    n_m = sum(len(c["methods"]) for c in cs.values())
    assert n_m >= 10000, f"方法数过少：{n_m}"
    for fam in ("MetaDataPostProcessor", "SaveAsHandler", "ImporterBase", "TransportHandler"):
        hit = [fq for fq in cs if fq.split(".")[-1].endswith(fam)]
        assert len(hit) >= 5, f"四族 {fam} 只找到 {len(hit)} 个类"
    # 四族接口契约（每个只有 1 个 abstract）+ 传参对象必须都在
    ifaces = {fq.split(".")[-1]: fq for fq, c in cs.items() if c["kind"] == "interface"}
    for it in ("AppMetaDataContextPostProcess", "SaveAsHandler", "Importable", "TransportHandler"):
        assert it in ifaces, f"缺接口契约 {it}（udc-plugin-api 可能未纳入抽取）"
    td = [fq for fq in cs if fq.endswith("schema.TransportData")]
    assert td, "缺 TransportData（导入/另存为的唯一入参）"
    bt = [fq for fq in cs if fq.endswith("BaseTransportData")]
    assert bt, "缺 BaseTransportData"
    assert any(m["name"] == "getIdMap" for m in cs[bt[0]]["methods"]), "BaseTransportData 缺 getIdMap"
    # 接口全量清单必须与 interfaces.json 对齐（成文覆盖率不能再只有 4 个）
    inv = ROOT / "docs/audit/artifacts/extension-surface-20261029/interface-inventory.md"
    assert inv.exists(), "缺 interface-inventory.md（841 个接口没有成文清单）"
    ifs = [fq for fq, c in cs.items() if c.get("kind") == "interface"]
    txt = inv.read_text(encoding="utf-8")
    assert f"{len(ifs)} 个接口" in txt, f"清单声明的接口数与 JSON 不符（JSON {len(ifs)} 个）"
    # UDC 可 implements 扩展点不能只剩传输族 4 个
    udc_abs = [fq for fq, c in cs.items()
               if c.get("kind") == "interface" and fq.startswith("com.seeyon.udc")
               and not fq.split(".")[-1].endswith("AppService")
               and any("abstract" in m.get("modifiers", "") for m in c["methods"])]
    assert len(udc_abs) >= 140, f"UDC 可 implements 接口只认出 {len(udc_abs)} 个，预期 >= 140"
    for must in ("DeployBeforeService", "AppFeatureHandler", "ApplicationInnerReference",
                 "UdcDataType", "DetectionTask", "LateralAuthChecker", "CodeTask",
                 "PartDetectionTask", "I18nHandler", "TypeMapping", "ElementRepository",
                 "Interpreter", "CopyHandler", "TypeChangeSqlResolver", "Template"):
        assert any(fq.endswith(must) for fq in udc_abs), f"UDC 扩展点缺 {must}"
    # 落地表（接口 × 平台实现）必须存在且条数对齐
    extp = ROOT / "docs/audit/artifacts/extension-surface-20261029/extension-points.md"
    assert extp.exists(), "缺 extension-points.md（扩展点 × 平台实现落地表）"
    etxt = extp.read_text(encoding="utf-8")
    assert f"共 {len(udc_abs)} 个带 abstract" in etxt, \
        f"落地表声明的扩展点数与 JSON 不符（JSON {len(udc_abs)} 个）"
    anno_n = len([fq for fq in udc_abs
                  if any("java.lang.annotation.Annotation" in str(x) for x in (cs[fq].get("extends") or []))])
    real_n = len(udc_abs) - anno_n
    assert f"**{real_n} 个是真接口**" in etxt, f"落地表声明的真接口数不符（应为 {real_n}）"
    assert f"**{anno_n} 个是注解" in etxt, f"落地表声明的注解数不符（应为 {anno_n}）"
    # 微流程被调入口必须登记
    entry = [fq for fq in cs if fq.endswith("MicroFlowProxyAppMicroFlow")]
    assert entry, "缺 MicroFlowProxyAppMicroFlow"
    assert any(m["name"] == "invokeAppServiceMethod" for m in cs[entry[0]]["methods"]), \
        "MicroFlowProxyAppMicroFlow 缺 invokeAppServiceMethod"
    assert "invokeAppServiceMethod" in d["method_index"], "method_index 未登记 invokeAppServiceMethod"


def test_all_udc_artifacts_are_indexed():
    """磁盘上每个带 jar 的 udc-* 构件都必须在 interfaces.json 的 sources 里。

    踩过的坑：batch2 的目标清单只列了 6 个 udc 包，漏掉 udc-biz（2380 类，
    平台全部 TransportHandler / Importer / SaveAsHandler 真实现都在里面），
    于是「有 68 个扩展点却数不出实现类」。清单本身不可信，只认磁盘。
    """
    import json
    import pytest

    repo = Path("D:/repo/CHIT/com/seeyon")
    if not repo.exists():
        pytest.skip("本机没有 jar 仓库，跳过构件完整性检查")
    want = {p.name for p in repo.glob("udc-*") if list(p.glob("*/*.jar"))}
    if not want:
        pytest.skip("jar 仓库里没有 udc-* 构件")
    src = ROOT / "docs/audit/artifacts/extension-surface-20261029/interfaces.json"
    got = set(json.loads(src.read_text(encoding="utf-8"))["sources"])
    missing = sorted(want - got)
    assert not missing, f"这些 udc 构件在盘上但没进索引：{missing}"


def test_extension_project_skeleton_fact():
    """扩展工程骨架事实格：五模块职责齐、INDEX 已登记。"""
    p = FACT_DIR / "extension-project-skeleton.md"
    assert p.exists(), "缺 extension-project-skeleton.md（扩展工程骨架）"
    t = p.read_text(encoding="utf-8", errors="replace")
    for mod in ("-facade", "-biz", "-web", "-ext", "-assemble"):
        assert mod in t, f"骨架格缺模块 {mod}"
    for sec in ("## 1. Capability", "## 7. Known Constraints", "## 9. Verified"):
        assert sec in t, f"骨架格缺段落 {sec}"
    idx = (ROOT / "core" / "facts" / "INDEX.md").read_text(encoding="utf-8", errors="replace")
    assert "extension-project-skeleton.md" in idx, "INDEX 未登记扩展工程骨架格"


DECISION_MUST = [
    # 部署与发布
    "DeployBeforeService", "AppMetaDataContextPostProcess", "MetadataHandleService", "ContextListener",
    "ApplicationShelfService", "PipeLineService", "DeployService",
    # 代码生成
    "CodeTask", "TransportHandler", "CodeContextAware", "CodeParamInterceptor", "FileResolver",
    "SqlResolver", "UdcDataBaseSqlGenerator", "TypeChangeSqlResolver", "TypeUpdateAuthChecker",
    "DbCodeHandler", "Interpreter", "Template", "I18nHandler", "ElementRepository",
    "BaseDesignMetadataQueryService",
    # 导入导出与复制
    "Importable", "SaveAsHandler", "SplitHandler", "SchemaFilter", "TenantDataFilter",
    "CopyHandler", "EntityCopyResolver", "ApplicationInnerReference", "ReferenceParser", "ReferenceStore",
    # 权限
    "ExtendAppOperationAuthCheck", "AuthCheck", "LateralAuthChecker", "LimitCountCheck",
    # 检测
    "DetectionTask", "PartDetectionTask", "FrontDeployDetectionTask", "DetectionMetadataAware",
    "SourceDetectionSupport", "DetectionRuleSupport", "ExprConsistencyValidator", "ExprConsistencyFilter",
    # 微流程
    "MicroFlowSimpleComponentCascadeHandler", "MicroFlowSubComponentHandler", "MicroFlowComponentHandler",
    "NodeParser", "MicroflowNodeParser", "PresetTemplateHandler", "MicroFlowSchemaDeterminer",
    "MicroFlowLastVersionMetadataEnabler", "ReferenceComponentProcessor", "ConnectorFullNameExtractor",
    "DynamicDependencyFullNameModifier",
    # 日志审计
    "OperationRecordService", "UdcAuditLogService", "LogService",
    # 应用特性与运行期
    "AppFeature", "AppFeatureHandler", "UdcDataType", "TypeHelper", "MappingMode",
    "DeductionSearchMethodType", "LastVersionMetadataManagerService", "Compatible",
    "CompatibilityOutput", "SchemaGenerator", "MigrateCallback", "LazyCacheAdapter",
    "NpmSyncDataService", "UdcTreeQueryService", "PluginExecutor", "PluginHandler",
]


def test_decision_table_interfaces_are_real():
    """决策表点名的每个接口必须在 interfaces.json 里真实存在、是 interface、且不是注解。

    防的是「按场景表瞎编接口名」——表是给人照着写代码的，名字错一个字就直接编译不过。
    """
    import json

    p = FACT_DIR / "extension-point-decision-table.md"
    assert p.exists(), "缺 extension-point-decision-table.md（扩展点决策表）"
    t = p.read_text(encoding="utf-8", errors="replace")
    for sec in ("## 1. Capability", "### 7.2 场景 → 钩子（部署与发布）",
                "### 7.10 选钩子的三条判断顺序", "## 8. Evidence"):
        assert sec in t, f"决策表缺段落 {sec}"
    src = ROOT / "docs/audit/artifacts/extension-surface-20261029/interfaces.json"
    cs = json.loads(src.read_text(encoding="utf-8"))["classes"]
    by_simple: dict[str, list] = {}
    for fq, c in cs.items():
        by_simple.setdefault(fq.split(".")[-1], []).append(c)
    bad = []
    for name in DECISION_MUST:
        if name not in t:
            bad.append(f"{name}（决策表里没出现）")
            continue
        cands = by_simple.get(name) or []
        if not cands:
            bad.append(f"{name}（interfaces.json 里没有）")
            continue
        real = [c for c in cands if c.get("kind") == "interface"
                and not any("java.lang.annotation.Annotation" in str(x) for x in (c.get("extends") or []))]
        if not real:
            bad.append(f"{name}（不是接口，可能是注解）")
    assert not bad, "决策表有问题项：" + "; ".join(bad[:10])
    idx = (ROOT / "core" / "facts" / "INDEX.md").read_text(encoding="utf-8", errors="replace")
    assert "extension-point-decision-table.md" in idx, "INDEX 未登记扩展点决策表"


def test_domain_surfaces_cover_nine_domains():
    """9 个标品域的逐字签名表必须齐（dubbo/bpm/组织/mybatis/datasource/连接器/事项/单据转文档/表达式/变量）。"""
    d = ROOT / "docs/audit/artifacts/extension-surface-20261029/domains"
    assert d.is_dir(), "缺 domains/ 逐字签名表"
    must = {
        "dubbo": "DubboFactory", "bpm": "BpmAppService", "organization": "OrgCommonAppService",
        "mybatis": "AllInOneBaseDao", "datasource": None, "connector": "LinkerAppService",
        "affair": "AffairUdcAppService", "formconvert": "FormConvertAppService",
        "formula": "ExpressionAppService", "systemvariable": "SystemVariableUtils",
        "file": "StorageService",
    }
    for name, probe in must.items():
        p = d / f"{name}.md"
        assert p.exists(), f"缺 domains/{name}.md"
        t = p.read_text(encoding="utf-8", errors="replace")
        assert len(t) > 2000, f"domains/{name}.md 内容过少（{len(t)} B）"
        if probe:
            assert probe in t, f"domains/{name}.md 里没有 {probe}"
    # 抽查逐字签名：BPM send 的入参/返回类型必须完整出现（不是方法名级）
    bpm = (d / "bpm.md").read_text(encoding="utf-8", errors="replace")
    assert "SingleRequest<com.seeyon.bpm.dto.operation.openapi.BpmSendDto>" in bpm, "bpm.md 缺 send 逐字入参"
    assert "SingleResponse<com.seeyon.bpm.dto.operation.openapi.BpmSendResultDto>" in bpm, "bpm.md 缺 send 逐字返回"


# 扩展工程 pom 里声明的标品依赖（用户截图逐项录入，86 个 com.seeyon 构件）
SCREENSHOT_PKGS = """
app-approval-facade app-common-facade boot-core boot-formula-engine boot-license-generator boot-spi
boot-starter-appservice boot-starter-artifact boot-starter-attachment boot-starter-cache
boot-starter-cip boot-starter-condition boot-starter-datainit boot-starter-datamigration
boot-starter-datasource boot-starter-datatype boot-starter-dubbo boot-starter-dynamicloader
boot-starter-dynamicsql boot-starter-elasticsearch boot-starter-enums boot-starter-environment
boot-starter-eventbus boot-starter-excel boot-starter-extmetadata boot-starter-file
boot-starter-filterchain boot-starter-formconvert boot-starter-formula boot-starter-frontend-log
boot-starter-ganttchart boot-starter-graphql boot-starter-i18n boot-starter-index
boot-starter-labelprint boot-starter-license boot-starter-lock boot-starter-metadata
boot-starter-mgn-export boot-starter-module boot-starter-monitor boot-starter-mq
boot-starter-mybatis boot-starter-nacos boot-starter-opinion boot-starter-parameter
boot-starter-prometheus boot-starter-proxy boot-starter-qrcode boot-starter-scanner
boot-starter-schedule boot-starter-security boot-starter-sensitive boot-starter-serialnumber
boot-starter-sharding boot-starter-shortlink boot-starter-spi boot-starter-swagger
boot-starter-systemvariable boot-starter-threadpool boot-starter-tomcat boot-starter-transaction
boot-starter-web boot-starter-websocket bpm-facade cdp-data-facade cip-capability-common
cip-capability-facade cip-connector-api cip-connector-facade cip-manager-facade
cip-openapi-common ctp-affair-facade ctp-message-facade ctp-user-facade
devops-starter-artifact devops-starter-common m5-facade organization-facade portal-facade
udc-common udc-facade udc-starter-customplan udc-starter-dataflow udc-starter-lowcode
udc-starter-runtime
""".split()


def test_every_screenshot_package_has_surface():
    """截图里 86 个标品构件必须逐个有签名表，且文件总数与索引构件数一致。

    踩过的坑：只按「业务域」合并导出，看起来覆盖了 bpm/组织/连接器，
    实际截图里的 boot-starter-* 一大半没有对应文件。
    """
    import json

    d = ROOT / "docs/audit/artifacts/extension-surface-20261029/packages"
    assert d.is_dir(), "缺 packages/ 逐构件签名表"
    # README.md 是目录入口（2026-11-07 补），不是构件签名表，不能计入构件数
    parts = [p for p in d.glob("*.md") if p.name != "README.md"]
    files = {p.stem for p in parts}
    missing = [p for p in SCREENSHOT_PKGS if p not in files]
    assert not missing, f"截图里这些构件没有签名表：{missing}"
    src = json.loads((ROOT / "docs/audit/artifacts/extension-surface-20261029/interfaces.json")
                     .read_text(encoding="utf-8"))["sources"]
    assert len(files) == len(src), f"packages 文件数 {len(files)} != 索引构件数 {len(src)}"
    # 抽查：每个文件必须有内容，且最大的几个不能是空壳
    thin = [p.name for p in parts if p.stat().st_size < 500]
    assert not thin, f"这些构件签名表过小（可能是空壳）：{thin}"
    for probe, needle in (("bpm-facade", "BpmAppService"),
                          ("organization-facade", "OrgCommonAppService"),
                          ("boot-starter-mybatis", "AllInOneBaseDao"),
                          ("cip-connector-api", "DataBaseExecutorService"),
                          ("cip-connector-facade", "LinkerAppService"),
                          ("ctp-affair-facade", "AffairUdcAppService")):
        t = (d / f"{probe}.md").read_text(encoding="utf-8", errors="replace")
        assert needle in t, f"{probe}.md 里没有 {needle}"


# 平台自有 SPI 键 → 必须能查到的实现方法（沿 extends 找父接口）
REG_KEYS = {
    "com.seeyon.boot.init.ComponentInitializer": "initialize",
    "com.seeyon.boot.log.init.LogInitializer": "init",
    "com.seeyon.boot.loader.ComponentDynamicRegister": "register",
    "com.seeyon.boot.loader.ComponentDynamicLoader": "isComponent",
    "com.seeyon.boot.starter.formula.parser.semantic.function.FunctionSemanticAnalyzer": "analyze",
    "com.seeyon.boot.starter.formula.parser.scriptbuilder.ExtensionFunctionScriptBuilder": "build",
    "com.seeyon.udc.expression.codegen.interpreter.function.ExtensionFunctionInterpreter": "interpret",
    "com.seeyon.boot.starter.formula.parser.semantic.caller.CallerSemanticAnalyzer": "getOperatorName",
}


def test_registration_mechanism_fact():
    """注册机制格必须存在，且 8 个平台 SPI 键在 spring.factories 实测里真的出现过。

    踩过的坑：只查「接口有没有实现」，不查「平台怎么发现实现」——
    结果写完扩展点编译通过、运行时静默不生效。
    """
    import json

    p = FACT_DIR / "extension-registration-mechanisms.md"
    assert p.exists(), "缺 extension-registration-mechanisms.md（注册机制格）"
    t = p.read_text(encoding="utf-8", errors="replace")
    for sec in ("## 1. Capability", "### 7.2 平台自有 SPI 键全表",
                "### 7.3 自定义表达式函数：三件套必须同时注册",
                "### 7.4 平台不用 Java SPI（反证）", "## 8. Evidence"):
        assert sec in t, f"注册机制格缺段落 {sec}"

    root = ROOT / "docs/audit/artifacts/extension-surface-20261029"
    scan = json.loads((root / "registration-scan.json").read_text(encoding="utf-8"))
    seen: dict[str, list] = {}
    for pkg, r in scan["jars"].items():
        for k, v in (r.get("spring_factories") or {}).items():
            seen.setdefault(k, []).extend(x.rstrip(",") for x in v)

    cs = json.loads((root / "interfaces.json").read_text(encoding="utf-8"))["classes"]
    bad = []
    for key, method in REG_KEYS.items():
        if key not in seen:
            bad.append(f"{key}（spring.factories 里没出现过）")
            continue
        if key not in t:
            bad.append(f"{key}（注册机制格里没写）")
            continue
        c = cs.get(key)
        if not c or c.get("kind") != "interface":
            bad.append(f"{key}（interfaces.json 里不是接口）")
            continue
        names = {m["name"] for m in c["methods"]}
        for parent in (c.get("extends") or []):
            pc = cs.get(parent)
            if pc:
                names |= {m["name"] for m in pc["methods"]}
        if method not in names:
            bad.append(f"{key}（查不到方法 {method}）")
    assert not bad, "注册键有问题：" + "; ".join(bad[:6])

    # 反证：平台不用 Java SPI —— services 条目必须极少且全是第三方
    svc = [i for r in scan["jars"].values() for i in (r.get("services") or {})]
    assert len(svc) <= 4, f"META-INF/services 条目 {len(svc)} 个，与「平台不用 Java SPI」结论矛盾"
    assert not any(s.startswith("com.seeyon.udc") for s in svc), f"UDC 接口出现在 Java SPI 里：{svc}"

    idx = (ROOT / "core" / "facts" / "INDEX.md").read_text(encoding="utf-8", errors="replace")
    assert "extension-registration-mechanisms.md" in idx, "INDEX 未登记注册机制格"


def test_consumer_scan_fact():
    """扩展点引用面：跨包/零引用三级必须与 JSON 一致，8 个零引用要逐一点名。

    踩过的坑：只查「有没有实现」不够——没有实现的 27 个里，有的连调用方都没有，
    写了也白写。这个格用常量池引用把「会不会被调」分出三级。
    """
    import json

    p = FACT_DIR / "extension-point-consumers.md"
    assert p.exists(), "缺 extension-point-consumers.md（引用面格）"
    t = p.read_text(encoding="utf-8", errors="replace")
    for sec in ("## 1. Capability", "### 7.1 三级证据强度",
                "### 7.3 真扩展点的引用数", "### 7.4 零引用的 8 个",
                "### 7.5 同名不同包是这轮最大的坑", "## 8. Evidence"):
        assert sec in t, f"引用面格缺段落 {sec}"

    art = ROOT / "docs/audit/artifacts/extension-surface-20261029/consumers.json"
    assert art.exists(), "缺 consumers.json"
    d = json.loads(art.read_text(encoding="utf-8"))
    rows = d["rows"]
    cross = [r for r in rows if r["cross_count"]]
    zero = [r for r in rows if not r["ref_count"]]
    assert len(cross) >= 150, f"跨包引用只有 {len(cross)} 个（< 150）"
    assert len(zero) <= 10, f"零引用 {len(zero)} 个（> 10，扫描可能失效）"
    # 格子里声明三级数字
    assert f"**154**" in t or f"| **{len(cross)}** |" in t or "154" in t, "格子未写跨包引用数"
    assert f"**{len(zero)}**" in t or f"| **{len(zero)}**" in t, f"格子未写零引用数 {len(zero)}"
    # 每个零引用接口的短名必须被点名
    for r in zero:
        assert r["simple"] in t, f"零引用接口 {r['iface']} 没写进格子"
    # 同名不同包必须揭示（这是最坑的一条）
    assert t.count("BaseNode") >= 2, "格子没揭示 BaseNode 同名不同包"
    assert t.count("ApplicationInnerReference") >= 2, "格子没揭示 ApplicationInnerReference 同名不同包"


def test_dto_fields_fact():
    """入参 DTO 字段表：761 个 DTO 的字段必须真抽到，BpmSendDto 逐字核对。

    坑：只给方法签名 `SingleRequest<BpmSendDto>` 等于不会用——不知道 DTO 里有什么字段。
    """
    import re

    p = FACT_DIR / "appservice-dto-fields.md"
    assert p.exists(), "缺 appservice-dto-fields.md（DTO 字段格）"
    t = p.read_text(encoding="utf-8", errors="replace")
    for sec in ("## 1. Capability", "### 7.1 全量在哪", "### 7.2 高频 DTO 速查",
                "### 7.3 三个坑", "## 8. Evidence"):
        assert sec in t, f"DTO 格缺段落 {sec}"

    d = ROOT / "docs/audit/artifacts/extension-surface-20261029/dto-fields"
    assert (d / "README.md").exists(), "缺 dto-fields/README.md"
    files = {x.stem for x in d.glob("*.md")} - {"README"}
    assert len(files) >= 10, f"DTO 域文件只有 {len(files)} 个"

    total = 0
    for x in files:
        total += len(re.findall(r"^## `", (d / f"{x}.md").read_text(encoding="utf-8", errors="replace"), re.M))
    assert total >= 700, f"DTO 总数 {total}（< 700，抽取口径可能坏了）"

    # BpmSendDto 逐字核对（这是「怎么发起流程」的直接答案）
    bpm = (d / "bpm.md").read_text(encoding="utf-8", errors="replace")
    seg = bpm.split("## `BpmSendDto`")
    assert len(seg) > 1, "bpm.md 里没有 BpmSendDto"
    body = seg[1][:1400]
    for f in ("templateCode", "templateId", "currentUserId", "orgId",
              "parameterData", "caseId", "sendPolicy"):
        assert f"`{f}`" in body, f"BpmSendDto 缺字段 {f}"
    # 嵌套 DTO 的**类型**必须出现在字段类型列里（字段名是 bpmCommentDto）
    assert "`bpmCommentDto`" in body, "BpmSendDto 缺嵌套字段 bpmCommentDto"
    assert "`com.seeyon.bpm.dto.BpmCommentDto`" in body, "bpmCommentDto 的类型没抽出来"


def test_enums_and_constants_fact():
    """枚举与常量：758 个枚举、5965 个带值常量必须真抓到。

    踩过的坑：① javap 把 enum 输出成 `final class X extends java.lang.Enum<X>`，
    不还原就全被当 class（漏 758 个）；② javap 默认不显示常量值，要加 -constants（漏 10257 个）。
    """
    import json

    p = FACT_DIR / "enums-and-constants.md"
    assert p.exists(), "缺 enums-and-constants.md"
    t = p.read_text(encoding="utf-8", errors="replace")
    for sec in ("## 1. Capability", "### 7.1 高频常量类", "### 7.2 枚举怎么用",
                "### 7.4 拿不到的东西：枚举的自定义值", "## 8. Evidence"):
        assert sec in t, f"枚举格缺段落 {sec}"

    art = ROOT / "docs/audit/artifacts/extension-surface-20261029"
    d = json.loads((art / "interfaces.json").read_text(encoding="utf-8"))
    cs = d["classes"]
    enums = [c for c in cs.values() if c.get("kind") == "enum"]
    assert len(enums) >= 700, f"枚举只有 {len(enums)} 个（< 700，enum 还原失效）"
    assert sum(1 for c in enums if c.get("constants")) >= 700, "枚举常量没抽到"
    vals = [f for c in cs.values() for f in (c.get("fields") or []) if "value" in f]
    assert len(vals) >= 8000, f"带字面值的字段只有 {len(vals)}（< 8000，-constants 没生效）"

    cm = art / "constants.md"
    assert cm.exists(), "缺 constants.md"
    ct = cm.read_text(encoding="utf-8", errors="replace")
    n_cls = ct.count("### `")
    assert n_cls >= 100, f"常量类只有 {n_cls} 个"
    for must in ("ConsistenceErrorCode", "UDC_CE_0001", "FeatureConstant", "enterpriseInfo"):
        assert must in ct, f"constants.md 缺 {must}"


def test_platform_annotations_fact():
    """平台注解：109 个注解的 @Target/@Retention 必须真解出来（不是常量池编号）。

    踩过的坑：javap -v 的 RuntimeVisibleAnnotations 是 `#20(#7=[e#21.#22])` 这种
    常量池引用，不 deref 就会得到 `#22` 而不是 `TYPE`；剥类型描述符的 `^L` 正则
    还会把 LOCAL_VARIABLE 剥成 OCAL_VARIABLE。
    """
    p = FACT_DIR / "platform-annotations.md"
    assert p.exists(), "缺 platform-annotations.md"
    t = p.read_text(encoding="utf-8", errors="replace")
    for sec in ("## 1. Capability", "### 7.1 最重要的发现", "### 7.2 按 @Target 分组",
                "### 7.3 @Retention", "## 8. Evidence"):
        assert sec in t, f"注解格缺段落 {sec}"

    ann = ROOT / "docs/audit/artifacts/extension-surface-20261029/annotations.md"
    assert ann.exists(), "缺 annotations.md"
    a = ann.read_text(encoding="utf-8", errors="replace")
    rows = a.count("| `")  # 粗略：明细表行
    assert rows >= 200, f"annotations.md 明细过少（{rows}）"
    # 不能出现未解引用的常量池编号
    assert "#22 |" not in a and "| #14 |" not in a, "注解 Target 还是常量池编号，deref 失效"
    assert " OCAL_VARIABLE" not in a, "LOCAL_VARIABLE 首字母被剥掉了"
    # Spring 元注解这条通路必须揭示
    for must in ("Service, Primary", "Component"):
        assert must in a, f"annotations.md 缺元注解证据 {must}"
    for anno in ("AppService", "Importer", "ConsistencyDetection"):
        assert anno in a, f"annotations.md 缺 {anno}"
    # @Target 必须是语义值不是编号
    for tgt in ("TYPE", "METHOD", "FIELD"):
        assert tgt in a, f"annotations.md 缺 @Target 值 {tgt}"


def test_registration_discovery_chain():
    """注册链路的静态闭环：@BootApp 扫描范围必须覆盖 ext 包，子类型扫描不能吹成通用通路。

    为什么重要：ext 包能不能被扫到，决定「贴了 @Importer 到底生不生效」。
    这条链靠 javap -v 解 @BootApp 的 ComponentScan 参数证实，不靠猜。
    """
    import json

    p = FACT_DIR / "extension-registration-mechanisms.md"
    t = p.read_text(encoding="utf-8", errors="replace")
    # @BootApp 的逐字配置必须落进格子
    for must in ('basePackages = "com.seeyon"', "excludeFilters", "SeeyonBeanNameGenerator",
                 "Apps.isMonolithic", "CtpAppBeanNameModifier"):
        assert must in t, f"注册格缺扫描链证据 {must}"
    assert "§7.7" in t or "7.7 子类型扫描" in t, "缺子类型扫描节"
    assert "不是给业务扩展点用的通用注册机制" in t, "子类型扫描的结论没写清"

    # 扫描产物必须存在且只有极少数类型（防止有人把它当成万用通路）
    sd = ROOT / "docs/audit/artifacts/extension-surface-20261029/subtype-discovery.json"
    assert sd.exists(), "缺 subtype-discovery.json"
    d = json.loads(sd.read_text(encoding="utf-8"))
    assert d["total_types"] <= 6, f"子类型扫描类型数 {d['total_types']} 过多，结论要重写"
    types = set(d["scanned_types"])
    assert any("UdcBaseEntity" in x for x in types), "缺 UdcBaseEntity（实体发现）"
    assert any("AppBeanNameModifier" in x for x in types), "缺 AppBeanNameModifier（Bean 名改写）"


def test_service_business_flow_fact():
    """Service 业务流转：必须抽到业务层（不只是门面转发），且覆盖客户应用。

    坑：业务 Service 是具体类（domain/service/XxxService），不是 XxxServiceImpl；
    只扫 *Impl 会得到 151 KB 的纯转发，扫不到 646 KB 的真实业务。
    """
    p = FACT_DIR / "service-business-flow.md"
    assert p.exists(), "缺 service-business-flow.md"
    t = p.read_text(encoding="utf-8", errors="replace")
    for sec in ("## 1. Capability", "### 7.1 产物在哪", "### 7.2 典型流转一",
                "### 7.5 拿不到的东西", "## 8. Evidence"):
        assert sec in t, f"流转格缺段落 {sec}"

    d = ROOT / "docs/audit/artifacts/service-flow-20261103"
    assert d.is_dir(), "缺 service-flow-20261103 目录"
    files = {x.name: x for x in d.glob("*.md")}
    assert "udc-biz-appservice.md" in files, "缺门面层产物"
    assert "udc-biz-domain.md" in files, "缺业务层产物"
    # 业务层必须显著大于门面层（证明真抽到了 domain 层）
    app = files["udc-biz-appservice.md"].stat().st_size
    dom = files["udc-biz-domain.md"].stat().st_size
    assert dom > app * 2, f"业务层 {dom} 不比门面层 {app} 大 2 倍，可能没抽到 domain"
    # 客户应用 biz 必须有
    cust = [n for n in files if n.endswith("-biz.md")]
    assert len(cust) >= 3, f"客户应用 biz 只有 {len(cust)} 份"

    dom_text = files["udc-biz-domain.md"].read_text(encoding="utf-8", errors="replace")
    assert "AppCollaborationEntityDao" in dom_text, "业务层缺 Dao 调用证据"
    assert "publishAfterTransaction" in dom_text or "EventBus" in dom_text, "业务层缺事件证据"
    # 门面层必须体现「转发」语义
    app_text = files["udc-biz-appservice.md"].read_text(encoding="utf-8", errors="replace")
    assert "AppServiceImpl" in app_text


def test_business_action_index_fact():
    """业务动作索引：2258 个方法按动作归类，且必须诚实标注 254 个无实现。

    坑：322 个 AppService 只有 68 个在仓库有实现类（46 个 udc-biz），
    BPM/组织/事项/连接器的实现在平台服务端——索引必须写清，否则会让人以为全能追。
    """
    p = FACT_DIR / "business-action-index.md"
    assert p.exists(), "缺 business-action-index.md"
    t = p.read_text(encoding="utf-8", errors="replace")
    for sec in ("## 1. Capability", "### 7.1 覆盖现实", "### 7.2 动作分布",
                "### 7.3 典型动作速查", "## 8. Evidence"):
        assert sec in t, f"动作索引格缺段落 {sec}"
    assert "已拿到实现类" in t, "没写清实现来源（应从 Artifactory 下 21 个 *-biz）"
    assert "没有 `-sources.jar`" in t or "无 sources" in t, "没说明是反编译不是源码"

    ai = ROOT / "docs/audit/artifacts/extension-surface-20261029/action-index.md"
    assert ai.exists(), "缺 action-index.md"
    a = ai.read_text(encoding="utf-8", errors="replace")
    for must in ("## 覆盖现实", "## 动作分布", "## 发布", "## 创建", "## 查询", "## 怎么用"):
        assert must in a, f"action-index.md 缺段落 {must}"
    assert "2300" in a or "2258" in a, "方法总数没写"
    # 发布类的关键方法必须能查到，且带 DTO 和流转
    assert "`deployNormal`" in a and "`DeployNormalDto`" in a, "缺 deployNormal 条目"
    assert "ApplicationService(deploy)" in a, "deployNormal 缺流转"
    # 查询类必须聚合而不是逐条（否则文件爆炸）
    assert "按接口聚合" in a, "查询类没聚合"
    # 诚实边界
    assert "impl-map" in a or "BpmApiAppServiceImpl" in a, "action-index 没体现实现映射"
    # BPM 核心 send 必须追到实现（命名不规则，靠猜会漏）
    assert "`BpmApiAppServiceImpl`" in a, "BpmAppService.send 没追到 BpmApiAppServiceImpl"


def test_appservice_invocation_fact():
    """AppService 调用通路：泛化调用必须写清 10 字段和 6 层 Bean 查找。"""
    p = FACT_DIR / "appservice-invocation.md"
    assert p.exists(), "缺 appservice-invocation.md"
    t = p.read_text(encoding="utf-8", errors="replace")
    for sec in ("## 1. Capability", "### 5.2 方式二：泛化调用",
                "### 5.3 泛化调用怎么找到 Bean", "### 7.2 命名不规则", "## 8. Evidence"):
        assert sec in t, f"调用通路格缺段落 {sec}"
    for f in ("interfaceName", "methodName", "paramType", "genericType",
              "subGenericType", "paramJson", "beanName", "returnJson", "bodyZip"):
        assert f in t, f"AppServiceInvokeDto 缺字段 {f}"
    assert "BOOT_4014" in t, "没写找不到 Bean 的报错码"
    assert "BpmApiAppServiceImpl" in t, "没写命名不规则的反例"
    assert "SingleRequest.from" in t, "没写构造方式"


def test_api_usage_cards_fact():
    """接口使用卡：必须带平台自己写的字段说明，且诚实标注必填未知。"""
    p = FACT_DIR / "api-usage-cards.md"
    assert p.exists(), "缺 api-usage-cards.md"
    t = p.read_text(encoding="utf-8", errors="replace")
    for sec in ("## 1. Capability", "### 7.1 字段说明的真正来源",
                "### 7.2 扫注解的两个坑", "### 7.4 没有必填标记", "## 8. Evidence"):
        assert sec in t, f"使用卡格缺段落 {sec}"
    assert "@DtoAttribute" in t, "没写字段说明的真正来源"
    assert "javap 必须带 `-p`" in t, "没写 -p 的坑"
    assert "GBK" in t, "没写编码坑"

    d = ROOT / "docs/audit/artifacts/api-usage"
    assert d.is_dir(), "缺 api-usage 目录"
    files = list(d.glob("*.md"))
    assert len(files) >= 8, f"域文件只有 {len(files)} 份"
    bpm = (d / "bpm.md")
    assert bpm.exists(), "缺 bpm 使用卡"
    b = bpm.read_text(encoding="utf-8", errors="replace")
    assert "怎么调" in b, "卡片缺「怎么调」章节"
    assert "SingleRequest.from" in b, "卡片缺调用模板"
    assert "getData().getContent()" in b, "卡片缺取值链"
    # 字段说明必须来自 @DtoAttribute（不是我们编的）
    assert "模板code/模板ID两者传其一" in b, "BpmSendDto.templateId 的平台说明丢了"
    assert "泛化调用" in b and "interfaceName" in b, "卡片缺泛化调用模板"

    meta = ROOT / "docs/audit/artifacts/extension-surface-20261029/dto-meta.json"
    assert meta.exists(), "缺 dto-meta.json"
    m = json.loads(meta.read_text(encoding="utf-8"))
    assert m["with_meta"] > 1000, f"dto-meta 只覆盖 {m['with_meta']} 个 DTO"


def test_contract_probes_compile():
    """契约探针：用真实 jar 编译手写调用代码。

    这是唯一能证明「按文档写的代码真能编译」的证据——
    静态抽取只能证明签名长这样，编译才能排除接口全名/方法名/字段名/取值链写错。
    classpath 由 probe_contracts.py 从 interfaces.json 的 pkg 字段自动推导。
    """
    probe_dir = ROOT / "tools/core/platform/probe_contracts"
    javas = sorted(probe_dir.glob("*.java"))
    assert len(javas) >= 2, f"探针只有 {len(javas)} 个"

    javac = Path("D:/software/java/bin/javac.exe")
    repo = Path("D:/repo/CHIT")
    if not javac.exists() or not repo.is_dir():
        pytest.skip("无 javac 或 jar 仓库（换机器时正常跳过）")

    import subprocess
    import tempfile
    out = Path(tempfile.mkdtemp(prefix="probe-out-"))
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools/core/platform/probe_contracts.py"),
         "--src", str(probe_dir), "--repo", str(repo),
         "--interfaces", str(EVID / "interfaces.json"), "--out", str(out)],
        capture_output=True, text=True, timeout=600, cwd=str(ROOT),
        encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"探针编译失败：\n{r.stdout[-2000:]}\n{r.stderr[-1000:]}"
    assert len(list(out.glob("*.class"))) >= 2, "没产出 .class"


def test_skill_navigation_points_to_real_files():
    """skill 是入口，引用的路径必须真实存在，数字必须与索引一致。

    踩过的坑：SKILL.md 里写「84 个包 / 758 个接口」，实际早变了；
    或 references 里写了文件名但没建。这条闸门两个都防。
    """
    skill_dir = ROOT / "skills/02-udc/xiaozhua-extension-usage"
    skill = skill_dir / "SKILL.md"
    assert skill.exists(), "缺 SKILL.md"
    t = skill.read_text(encoding="utf-8", errors="replace")

    # 2.0 新增章节
    for sec in ("## 一、导航", "## 三、后端：两条调用通路",
                "## 五、扩展点", "## 九、写完怎么验", "## 十一、references"):
        assert sec in t, f"SKILL.md 缺章节 {sec}"

    # references 必须在磁盘上
    refs = re.findall(r"`references/([\w.-]+\.md)`", t)
    assert len(refs) >= 3, f"SKILL.md 只引用了 {len(refs)} 个 reference"
    for r in refs:
        assert (skill_dir / "references" / r).exists(), f"引用了不存在的 reference：{r}"

    # 导航表里的产物路径必须存在（取几个关键的）
    D = ROOT / "docs/audit/artifacts/extension-surface-20261029"
    for p in (D / "action-index.md", D / "interfaces.json",
              D / "impl-map.json", D / "dto-meta.json"):
        assert p.exists(), f"导航指向的产物不存在：{p.name}"
    assert (ROOT / "docs/audit/artifacts/api-usage").is_dir(), "导航指向的 api-usage 不存在"
    assert (ROOT / "docs/audit/artifacts/service-flow-20261103").is_dir(), "导航指向的 service-flow 不存在"
    assert (ROOT / "tools/core/platform/probe_contracts.py").exists(), "导航指向的 probe_contracts 不存在"

    # evidence-index 的数字不能漂移
    ev = (skill_dir / "references/evidence-index.md").read_text(encoding="utf-8", errors="replace")
    cs = json.loads((D / "interfaces.json").read_text(encoding="utf-8"))["classes"]
    n_iface = sum(1 for c in cs.values() if c.get("kind") == "interface")
    n_svc = sum(1 for k, c in cs.items()
                if c.get("kind") == "interface" and k.split(".")[-1].endswith("AppService"))
    assert f"{n_iface} 接口" in ev, f"evidence-index 的接口数 {n_iface} 没同步"
    assert f"{n_svc} AppService" in ev, f"evidence-index 的 AppService 数 {n_svc} 没同步"

    # cookbook 必须包含三个编译验证过的动作
    cb = (skill_dir / "references/appservice-cookbook.md").read_text(encoding="utf-8", errors="replace")
    for act in ("发起流程", "建实体", "发布应用", "文件上传", "分页查询", "泛化调用"):
        assert act in cb, f"cookbook 缺动作 {act}"
    assert "DeployNormalDto" in cb and "没有 appId" in cb, "cookbook 缺部署 DTO 的纠正"


if __name__ == "__main__":
    sys.exit("用 pytest 跑：uv run --no-project python -m pytest tests/udc/test_extension_usage_assets.py -q")
