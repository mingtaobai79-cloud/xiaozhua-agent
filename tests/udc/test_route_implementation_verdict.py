# -*- coding: utf-8 -*-
"""发现 B 收口护栏：`/udc/micro-flow-group/search-list` 的「有实现 / 无实现」裁定。

**背景**：第九轮 LIVE 观测到该路由被调用，但 674 契约与部署态字节码都没有它的 mapping，
记为 UNVERIFIED（三选一）。第十七轮用两条独立轴收口：

轴 1（静态·提供者唯一性）：全 jar 仓库逐 class 直读字节码，声明类级 mapping
  `udc/micro-flow-group` 的 class **只有 1 个** ⇒ 「另一构件提供」支证伪。
轴 2（静态·注册面完整）：该 class 的 7 个方法里没有 `search-list` / `select-by-appid`，
  而对照叶子 `select-by-type` / `batch-move` 确有命中 ⇒ 0 命中不是扫描器空转。
轴 3（LIVE·对照分组）：以「同 traceId 行数」为量，对照组（16 条，契约/字节码可证存在）
  最小行数 = 2；试验组恰为 2 条孤行 = `search-list` 与 `select-by-appid`；
  后者另有第十轮独立裁定 ⇒ 判据被正向标定。

本护栏钉死：① 证据件可由复算器原样重现；② 证据件的关键判据（提供者数 = 1、
  目标叶子 0 命中、对照叶子有命中）；③ LIVE 对照组/试验组的分组与阈值；
  ④ 不得把 `search-list` 从 UNVERIFIED 悄悄升级为「已归位某构件」。

证据源全部**仓内耐久**（scratch 会被 24h 清理，故 LIVE 原件只留计数与模板）。
本文件只引平台构件 / 路由字面量，不含客户业务明细。
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'ROUTE-IMPLEMENTATION-VERDICT.json'
LIVE = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'LIVE-ROUTE-IMPLEMENTATION-CONTROL.json'
DOC = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'RUNTIME-URL-SURFACE.md'
TOOL = ROOT / 'tools' / 'core' / 'decompile' / 'enumerate_route_implementation.py'
CONTRACT = (ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-web-5.3.517-contracts'
            / '_api_full.json')
PLANES = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'METADATA-PLANES.json'

PREFIX_ROUTES = {
    '/udc/micro-flow-group/batch-move',
    '/udc/micro-flow-group/create',
    '/udc/micro-flow-group/delete',
    '/udc/micro-flow-group/delete-batch',
    '/udc/micro-flow-group/select-by-type',
    '/udc/micro-flow-group/update',
    '/udc/micro-flow-group/{microFlowGroupId}',
}
ABSENT_LEAVES = {'search-list', 'select-by-appid'}
PRESENT_LEAVES = {'select-by-type', 'batch-move'}


def _load_tool():
    spec = importlib.util.spec_from_file_location('route_impl', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _evid():
    return json.loads(EVID.read_text(encoding='utf-8'))


# ── 轴 1 · 提供者唯一性 ──────────────────────────────────────────────
def test_evidence_records_single_provider_for_class_mapping():
    a = _evid()['axis1_provider_uniqueness']
    assert a['provider_count'] == 1, a
    assert a['other_component_branch'] == 'REFUTED'
    (jar, member), = a['providers_declaring_class_mapping']
    assert jar.endswith('udc-web-5.3.517.jar'), jar
    assert member == 'com/seeyon/udc/controller/MicroFlowGroupController.class'


def test_contract_registers_exactly_the_seven_prefix_routes():
    e = _evid()['axis2_registered_leaves']
    assert set(e['contract_routes_under_prefix']) == PREFIX_ROUTES
    assert e['contract_route_count'] == 7


# ── 轴 2 · 注册面完整（目标叶子 0 命中 / 对照叶子有命中）────────────
def test_target_leaves_absent_from_provider_bytecode():
    hits = _evid()['axis2_registered_leaves']['target_leaf_literal_hits_in_providers']
    for leaf in ABSENT_LEAVES:
        assert hits[leaf] == [], f'{leaf} 不应在提供者字节码里出现'


def test_control_leaves_present_so_zero_hit_is_not_a_dead_scanner():
    hits = _evid()['axis2_registered_leaves']['target_leaf_literal_hits_in_providers']
    for leaf in PRESENT_LEAVES:
        assert hits[leaf], f'对照叶子 {leaf} 必须在同一次扫描里命中，否则 0 命中不可信'


# ── 轴 3 · LIVE 对照分组 ─────────────────────────────────────────────
def test_live_evidence_separates_control_from_test_group():
    d = json.loads(LIVE.read_text(encoding='utf-8'))
    ctrl = d['control_group_mapped_routes']
    test = d['test_group_unmapped_routes']
    assert ctrl['count'] == 16 and test['count'] == 2
    assert ctrl['min_trace_lines'] >= 2, '对照组最小同 traceId 行数必须 >= 2'
    assert set(test['templates']) == {
        '/udc/micro-flow-group/search-list',
        '/udc/micro-flow-group/select-by-appid/{arg}',
    }
    sep = d['clean_separation']
    assert sep['single_count'] == 2 and sep['multi_count'] == 16 and sep['total'] == 18
    assert sep['single_count'] + sep['multi_count'] == sep['total']


def test_live_evidence_admits_no_status_code_and_single_window():
    lim = ' '.join(json.loads(LIVE.read_text(encoding='utf-8'))['limitations'])
    assert 'HTTP 状态码' in lim
    assert '24h' in lim  # 原始日志在 scratch，会被清理 ⇒ 只留计数


# ── 端到端 · 证据件可由复算器原样重现 ────────────────────────────────
VOLATILE_KEYS = {'jars_scanned', 'jars_scanned_note'}


def _conclusion_surface(d):
    """结论面 = 证据件去掉**可变域**键（jars_scanned*）。

    jars_scanned 是本地 maven 仓库的计数，而该目录会被**其它工作流**写入
    （客户构件随构建落地：本轮实测 15:49-15:51 新增 3 个客户 jar，1518 -> 1521）。
    把它放进逐字比对，等于把环境指纹当契约 —— 会让护栏因外部写入而假失败。
    故：结论面逐字判等（providers / leaves / contract 路由全保留），
    扫描域另用「不得缩小」判据。
    """
    return {k: v for k, v in d.items() if k not in VOLATILE_KEYS}


def test_verdict_is_reproducible_by_the_tool(tmp_path):
    d = _evid()
    repo = d['repo_root']
    if not Path(repo).exists():
        pytest.skip(f'jar 仓库不可用（离线机器）: {repo}')
    out = tmp_path / 'rerun.json'
    r = subprocess.run([sys.executable, str(TOOL), '--repo-root', repo, '--emit', str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    got = json.loads(out.read_text(encoding='utf-8'))
    # ① 结论面逐字判等：裁定所需的一切（provider 唯一性 / 叶子命中 / 契约路由）不得变
    assert _conclusion_surface(got) == _conclusion_surface(d)
    # ★ 字节级：该件是复算产物。换行必须与证据件字节一致（此前靠 Windows 文本模式隐式转换，Linux 上会漂）。
    assert _strip_volatile(out.read_bytes()) == _strip_volatile(EVID.read_bytes()), (
        '复算输出与证据件非字节一致（生成处换行应显式为 newline=CRLF）')
    # ② 扫描域不得缩小：仓库只会变大（客户构件随构建落地），变小即说明扫描根写错
    assert got['jars_scanned'] >= d['jars_scanned'], '扫描域缩小 ⇒ 仓库根或递归有问题'
    # ③ 可变域键必须自带说明，避免被误当契约
    assert 'jars_scanned_note' in got


def test_guardrail_bites_on_an_lf_reserialization():
    """会咬自证：同一结论面换成 LF 后 parsed 等价，但字节必须不等。"""
    raw = EVID.read_bytes()
    assert raw.count(bytes([13, 10])) > 0, '证据件应为 CRLF'
    lf = raw.replace(bytes([13, 10]), bytes([10]))
    assert json.loads(lf.decode('utf-8')) == _evid()
    assert lf != raw


def test_evidence_marks_the_volatile_count_as_non_contract():
    """可变域计数必须显式标注为非契约，否则后人会重犯「把环境指纹当契约」的错。"""
    d = _evid()
    assert VOLATILE_KEYS <= set(d)
    assert '可变域' in d['jars_scanned_note']


def test_verdict_matches_contract_prefix_by_independent_read():
    """独立读契约复核：该前缀下的 7 条路由，且其中确实没有任何 search-list 形态。"""
    data = json.loads(CONTRACT.read_text(encoding='utf-8'))
    got = set()
    for body in data.values():
        for m in body.get('methods', []):
            fp = m.get('full_path') or ''
            if fp.startswith('/udc/micro-flow-group/'):
                got.add(fp)
    assert got == PREFIX_ROUTES
    assert not any('search-list' in r for r in got)


# ── 文档同步 / 反向护栏 ──────────────────────────────────────────────
def test_document_records_the_verdict_three_branches():
    t = DOC.read_text(encoding='utf-8')
    assert '## 8.' in t
    assert '另一构件提供' in t and '证伪' in t
    assert '(a)(b) 均证伪' in t
    assert '死路径' in t


def test_document_does_not_relocate_search_list_to_any_component():
    """反向护栏：不得把 search-list 说成「某构件提供」。

    反引号是文档里的常态写法（如 `search-list` 由 …），若按原样匹配，
    'search-list 由' 这种模式会被 '`search-list` 由' 轻易绕过（第十七轮实测踩过），
    故先把反引号 / 表意空格归一化、压平空白，再做子串匹配。
    """
    t = DOC.read_text(encoding='utf-8').replace('`', '').replace('　', ' ')
    t = ' '.join(t.split())
    for bad in ('search-list 由', 'search-list 归位', 'search-list 属 ',
                'search-list 提供者', 'search-list 在 udc-'):
        assert bad not in t, f'不得把 search-list 归位到任何构件: {bad!r}'
    # 也不得出现「提供者 = ... search-list」这类等式
    assert 'search-list = ' not in t


def test_evidence_carries_no_customer_identifiers():
    """清洗门：证据件不得含客户业务明细（长数字串 / 客户关键词）。"""
    for p in (EVID, LIVE):
        s = p.read_text(encoding='utf-8')
        for token in ('znxmglpt', 'test-account-1', 'sy_access_token'):
            assert token not in s, f'{p.name} 含敏感/客户串 {token!r}'
        import re
        assert not re.search(r'\d{15,}', s), f'{p.name} 含长数字串（疑似实参）'

# ── 轴 3 独立交叉复核：LIVE 分组 vs udc-web 674 契约 ────────────────────
def _norm_route(p):
    """把 `{...}` 占位归一为 `{arg}`，使 LIVE 模板与契约 full_path 可逐字比对。"""
    import re
    return re.sub(r'\{[^}]*\}', '{arg}', p)


def _contract_paths():
    data = json.loads(CONTRACT.read_text(encoding='utf-8'))
    return {_norm_route(m['full_path'])
            for body in data.values() for m in body.get('methods', [])
            if m.get('full_path')}


def test_test_group_has_zero_hits_in_udc_web_contract():
    """试验组 2 条必须与 udc-web 674 契约**逐字 0 命中**（与轴 2 字节码结论独立一致）。"""
    paths = _contract_paths()
    assert len(paths) == 674, len(paths)
    live = json.loads(LIVE.read_text(encoding='utf-8'))
    hits = [t for t in live['test_group_unmapped_routes']['templates']
            if _norm_route(t) in paths]
    assert hits == [], f'试验组不应在 udc-web 契约里命中: {hits}'


def test_control_group_cross_check_is_recorded_and_recomputable():
    """对照组的契约命中数必须与证据件登记的 `contract_cross_check` 一致（可独立复算）。"""
    paths = _contract_paths()
    live = json.loads(LIVE.read_text(encoding='utf-8'))
    cc = live['contract_cross_check']
    ctrl = live['control_group_mapped_routes']['templates']
    hit = [t for t in ctrl if _norm_route(t) in paths]
    miss = [t for t in ctrl if _norm_route(t) not in paths]
    assert cc['contract_distinct_full_paths'] == len(paths)
    assert cc['control_templates_in_contract'] == len(hit) == 14
    assert cc['test_templates_in_contract'] == 0
    # 未落进 674 的对照模板必须**恰好**是这 2 条，且各带另档契约背书
    assert sorted(miss) == ['/udc/graphql', '/udc/metadata/app-service-by-name'], miss
    backed = {x['template']: x['backing'] for x in cc['control_templates_not_in_udc_web_contract']}
    assert set(backed) == set(miss)
    assert 'PLATFORM-GRAPHQL-OPERATIONS' in backed['/udc/graphql']
    assert 'METADATA-PLANES' in backed['/udc/metadata/app-service-by-name']


def test_non_contract_control_is_backed_by_its_own_documented_plane():
    """`/udc/metadata/app-service-by-name` 的背书必须真的存在于 ctp metadata 面证据件里。"""
    planes = json.loads(PLANES.read_text(encoding='utf-8'))
    ctp = [p for p in planes['planes'] if 'ctp' in p.get('id', '')]
    assert len(ctp) == 1, ctp
    ctp = ctp[0]
    assert ctp['endpoints'] == 105 and ctp['distinct_leaves'] == 105
    assert 'app-service-by-name' in ctp['leaves']
    assert ctp['external_prefix'] == '/udc/metadata/'


# 声明为「可变域」的字段：不参与字节级比对（证据件自身 notes 已如此声明）。
# 可变域的原因：本地 maven 仓库会被其它工作流写入（客户构件随构建落地），
# 计数因此会漂移——但结论面（裁定依据）必须逐字不变。
_VOLATILE_FIELDS = ("jars_scanned",)


def _strip_volatile(raw: bytes) -> bytes:
    """剔除可变域字段后的字节内容（保持其余部分逐字节可比）。"""
    import re as _re
    text = raw.decode("utf-8")
    for field in _VOLATILE_FIELDS:
        text = _re.sub(rf'("{field}"\s*:\s*)\d+', r"\1<volatile>", text)
    return text.encode("utf-8")
