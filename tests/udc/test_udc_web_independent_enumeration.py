"""udc-web 674 端点的**第二解析器**独立复核护栏（2026-10-15 第六轮）。

**为什么需要**：`_api_full.json` 里的 674 一直只有一条证据链 ——
`tools/core/decompile/extract_udc_web_methods.py` 按 `annotation.<Name>` 文本搜索 + descriptor 切块推导。
三轮前刚在这条链上修掉四类缺陷（A 重载覆盖 / B 取值越界 / C 幻影兜底 / D 声明门），
**即 674 本身正是那台刚被修过的机器的输出**。用同一台机器验证自己的输出，不是复核。

本文件用 `tools/core/decompile/enumerate_udc_web_http_methods.py`（按 javap 自身**缩进层级**解析
`RuntimeVisibleAnnotations` 块，与文本搜索是两条不同的轴）独立重算，再与契约对账。

**本轮实测（逐条一致，非抽样）**：54 类 / 660 带值 / 14 裸 / 合计 **674**；
逐条 `(类,方法,动词,full_path)` 集合**完全相同**（0 双向差）；裸 mapping 的 `(类,方法)`
集合相同；distinct op **673**；暴露面 **666**。两个仓内 javap 副本（GBK / UTF-8）结果一致。

**★ 本轮踩到并因此钉死的陷阱（勿删）**：第一版把独立解析器指向 scratch 快照
(`scratch/art517-contracts/`, 90 javap)，该快照**只有 52 个 udc-web Controller**
（缺 `ParameterController` / `UdcFileController`），于是得 `653 + 13 = 666` ——
**666 恰好等于暴露面数**。一个少扫 2 个类的残缺扫描会「看起来验证了暴露面」。
故本文件同时钉死这个巧合，防止它被当成暴露面的独立证据。

证据源全在**仓内**（不受 scratch 24h 清理影响）：
`docs/audit/artifacts/udc-web-5.3.517-javap/*.javap.txt`（54，GBK）与
`docs/audit/artifacts/udc-web-5.3.517-contracts/*.javap.txt`（54，UTF-8，同源）。
"""
import importlib.util
import json
from pathlib import Path

import pytest

from components.udc.graphql_op_naming import derive_ops, path_to_op

ROOT = Path(__file__).resolve().parents[2]
JAVAP_GBK = ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-web-5.3.517-javap'
JAVAP_UTF8 = ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-web-5.3.517-contracts'
API = JAVAP_UTF8 / '_api_full.json'
TOOL = ROOT / 'tools' / 'core' / 'decompile' / 'enumerate_udc_web_http_methods.py'

_CLASSES = 54
_VALUED = 660
_BARE = 14
_TOTAL = 674
_DISTINCT_OPS = 673
_EXPOSED = 666
_STALE_SUBSET_VALUED, _STALE_SUBSET_BARE = 653, 13
_MISSING_IN_STALE = ('ParameterController', 'UdcFileController')

pytestmark = pytest.mark.skipif(
    not (JAVAP_GBK.is_dir() and JAVAP_UTF8.is_dir() and API.exists() and TOOL.exists()),
    reason='udc-web javap / 契约件 / 独立枚举器缺失')


def _tool():
    spec = importlib.util.spec_from_file_location('enumerate_udc_web_http_methods', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope='module')
def enum():
    mod = _tool()

    def run(directory, encoding):
        out = {}
        for f in sorted(Path(directory).glob('*.javap.txt')):
            txt = f.read_bytes().decode(encoding, errors='replace').replace(chr(13), '')
            out[f.name.replace('.javap.txt', '')] = mod.parse_class(txt)
        return out
    return {'gbk': run(JAVAP_GBK, 'gbk'),
            'utf8': run(JAVAP_UTF8, 'utf-8'), 'mod': mod}


@pytest.fixture(scope='module')
def contract():
    return json.loads(API.read_text(encoding='utf-8'))


# ------------------------------------------------- 独立重算的四个总量
def test_independent_parser_is_not_the_derived_contracts_parser():
    """独立解析器必须真的独立：不得**导入/调用**被复核的那台提取器。

    注意判据必须是 AST 里的真实依赖，不是文本出现 —— 该文件的注释里本就提到
    `extract_udc_web_methods`（说明它与文本搜索轴不同），文本匹配会把说明当违规。
    """
    import ast

    src = TOOL.read_text(encoding='utf-8')
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or '')
    assert not any('extract_udc_web_methods' in m for m in imported), imported
    # 也不得读被复核机器的产物（那样就是把它的输出当输入）
    assert '_api_full.json' not in src, '独立解析器不得读契约产物'
    # 独立的轴：按缩进层级解析注解块
    assert 'def _indent' in src
    assert '_block_end' in src


@pytest.mark.parametrize('enc', ['gbk', 'utf8'])
def test_independent_totals_recompute_674(enum, enc):
    """54 类 / 660 带值 / 14 裸 / 合计 674 —— 与契约口径逐项相等。"""
    o = enum[enc]
    assert len(o) == _CLASSES, len(o)
    valued = sum(len(v['endpoints']) for v in o.values())
    bare = sum(len(v['bare_mapping']) for v in o.values())
    assert (valued, bare) == (_VALUED, _BARE), (valued, bare)
    assert valued + bare == _TOTAL


@pytest.mark.parametrize('enc', ['gbk', 'utf8'])
def test_independent_class_set_equals_contract(enum, contract, enc):
    """类集合必须与契约完全相同（不漏不多）—— 残缺快照陷阱的正面对冲。"""
    assert set(enum[enc]) == set(contract), sorted(set(enum[enc]) ^ set(contract))
    assert len(contract) == _CLASSES


@pytest.mark.parametrize('enc', ['gbk', 'utf8'])
def test_every_valued_endpoint_matches_contract_exactly(enum, contract, enc):
    """逐条 (类,方法,动词,full_path) 集合相等 —— 0 双向差，非抽样。"""
    contrav = {(c, m['method'], m['http'], m['full_path'])
               for c, v in contract.items() for m in v['methods']
               if m.get('path', '') != ''}
    indep = {(c, e['method'], e['http'], e['full_path'])
             for c, v in enum[enc].items() for e in v['endpoints']}
    assert not (indep - contrav), sorted(indep - contrav)[:5]
    assert not (contrav - indep), sorted(contrav - indep)[:5]
    assert len(indep) == _VALUED


@pytest.mark.parametrize('enc', ['gbk', 'utf8'])
def test_bare_mapping_population_identical_and_takes_class_root(enum, contract, enc):
    """14 条裸 mapping：两侧 (类,方法) 集合相同；full_path 必须 = 类级根。

    **语义要点**：裸 mapping 的 full_path 必须取 `join_path(class_mapping, None)`。
    若误用 `join_path(None, None)` 会得到 `'/'`（**非空**！）而被当成真路径，
    `derive_ops` 里「空路径跳过」的守卫就失效了。此处把该语义钉死。
    """
    mod = enum['mod']
    indep = {(c, b['method']) for c, v in enum[enc].items() for b in v['bare_mapping']}
    contrav = {(c, m['method']) for c, v in contract.items() for m in v['methods']
               if m.get('path', '') == ''}
    assert indep == contrav, sorted(indep ^ contrav)
    assert len(indep) == _BARE
    for c, v in enum[enc].items():
        for b in v['bare_mapping']:
            want = mod.join_path(v['class_mapping'], None)
            got = [m['full_path'] for m in contract[c]['methods']
                   if m['method'] == b['method'] and m.get('path', '') == '']
            assert got == [want], (c, b['method'], got, want)


@pytest.mark.parametrize('enc', ['gbk', 'utf8'])
def test_stale_52_class_subset_yields_666_by_coincidence(enum, enc):
    """**陷阱钉桩**：去掉缺失的 2 类后得 666 —— 恰好等于暴露面数。

    少扫 2 个类的残缺扫描会「看起来验证了暴露面 666」。本测试固定该巧合：
    任何人若把 666 的来源说成「独立扫描得 666」，必须解释这 2 个类去哪了。
    """
    sub = {k: v for k, v in enum[enc].items() if k not in _MISSING_IN_STALE}
    valued = sum(len(v['endpoints']) for v in sub.values())
    bare = sum(len(v['bare_mapping']) for v in sub.values())
    assert len(sub) == _CLASSES - 2
    assert (valued, bare) == (_STALE_SUBSET_VALUED, _STALE_SUBSET_BARE)
    assert valued + bare == _EXPOSED, (
        '巧合破灭 -> 暴露面 666 的独立证据必须重写：' + str(valued + bare))


def test_both_in_repo_javap_copies_agree(enum):
    """两个仓内 javap 副本（GBK / UTF-8）独立解析结果一致 —— 排除编码副作用。"""
    def sig(o):
        return ({c: {(e['method'], e['http'], e['full_path']) for e in v['endpoints']}
                 for c, v in o.items()},
                {c: {(b['method'], b['verb']) for b in v['bare_mapping']}
                 for c, v in o.items()})
    assert sig(enum['gbk']) == sig(enum['utf8'])


def test_parameter_controller_is_only_class_without_restapi(enum):
    """ParameterController 是唯一无类级 @RestApi 的类 —— 6 条端点因此不进 op 面。"""
    pc = enum['gbk']['ParameterController']
    assert pc['class_mapping'] is None
    assert pc['bare_mapping'] == [
        {'method': 'create', 'verb': 'POST', 'annotation': 'PostMapping'}]


def test_udcfile_controller_has_mapping_but_no_restapioperation(enum):
    """UdcFileController 2 条有 mapping、无方法级 @RestApiOperation -> 同样不进 op 面。"""
    assert [e['full_path'] for e in enum['gbk']['UdcFileController']['endpoints']] == [
        '/udc/runtime/file/download', '/udc/runtime/file/metadata/{appId}']


def test_exposure_gate_recomputed_independently():
    """666 = 674 - 6(ParameterController 全类无 @RestApi) - 2(File 无 @RestApiOperation)。

    双注解门：类级 `@RestApi` ∧ 方法级 `@RestApiOperation`，缺一不可
    （见 REST-EXPOSURE-MECHANISM.md / MetadataScanner 分支一）。
    """
    missing_class, lacking_op, mapping_methods = [], [], []
    for f in sorted(JAVAP_GBK.glob('*.javap.txt')):
        cls = f.name.replace('.javap.txt', '')
        lines = (f.read_bytes().decode('gbk', errors='replace')
                 .replace(chr(13), '').split(chr(10)))
        end = max(i for i, l in enumerate(lines) if l.strip() == '}')
        tail = chr(10).join(lines[end + 1:])
        if 'com.seeyon.boot.annotation.RestApi' not in tail:
            missing_class.append(cls)
        starts = [i for i in range(len(lines) - 1)
                  if lines[i].startswith('  ') and not lines[i].startswith('    ')
                  and '(' in lines[i] and 'descriptor:' not in lines[i]
                  and lines[i + 1].strip().startswith('descriptor:')]
        for k, i in enumerate(starts):
            stop = starts[k + 1] if k + 1 < len(starts) else len(lines)
            blk = (chr(10).join(lines[i:stop])
                   .split('RuntimeVisibleParameterAnnotations')[0])
            mapped = any('annotation.' + a in blk for a in (
                'PostMapping', 'GetMapping', 'PutMapping', 'DeleteMapping', 'PatchMapping'))
            if not mapped:
                continue
            mapping_methods.append((cls, lines[i].strip().split('(')[0].split()[-1]))
            if 'annotation.RestApiOperation' not in blk:
                lacking_op.append(
                    (cls, lines[i].strip().split('(')[0].split()[-1]))
    assert missing_class == ['ParameterController'], missing_class
    assert lacking_op == [('UdcFileController', 'download'),
                          ('UdcFileController', 'metadataDownload')], lacking_op
    assert len(mapping_methods) == _TOTAL, len(mapping_methods)
    assert _TOTAL - 6 - len(lacking_op) == _EXPOSED


def test_independent_op_face_equals_derive_ops(enum, contract):
    """独立枚举 -> op 面 == derive_ops(契约)；两侧 distinct op 均 673。"""
    mod = enum['mod']
    ops = set()
    for v in enum['gbk'].values():
        for e in v['endpoints']:
            ops.add(path_to_op(e['full_path'], e['http']))
        for b in v['bare_mapping']:
            p = mod.join_path(v['class_mapping'], None)
            if p.strip('/'):
                ops.add(path_to_op(p, b['verb']))
    ref = set(derive_ops(contract))
    assert len(ops) == _DISTINCT_OPS and len(ref) == _DISTINCT_OPS
    assert ops == ref, sorted(ops ^ ref)[:5]
