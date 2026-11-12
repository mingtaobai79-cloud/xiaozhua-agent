# -*- coding: utf-8 -*-
"""全部署域 op 面裁定护栏（余 60 条 在部署态**全构件**注解路由面内是否承接）。

**这轮补上的口径**：上一轮（第十八轮）只裁 **22 个 `udc-*.jar`** 单域；本件把域扩到
**全部署域注解路由面**（可证超集），故「余 60 条 0 命中」的强度再升一档。

**三层判据（缺一层不成立）**：
  ① **超集论证须被实测检验**：`routed_without_bind_annotation` 必须为空 ——
     任何带 @RequestMapping/... 的类在常量池必含 `bind/annotation`；若有路由类不含该串，
     则「域 ⊇ 全部注解路由类」不成立，0 命中不算强负面。
  ② **两条同域对照都必须 PASS**：udc-web 674 契约 **674/674**；跨构件归位 32 条 **32/32**
     （这 32 条正是靠 `addPathPrefix` 前缀机制才归位 ⇒ 该对照同时校验前缀规则本身）。
  ③ **稳健性**：另两种前缀写法（none / substr）下余 60 仍须 **0 命中** ——
     0 命中不得依赖某一种写法。

**前缀机制的权威锚（本轮升级）**：`boot-starter-web-5.3.358` 的
`com.seeyon.boot.starter.web.WebAutoConfiguration.configurePathMatch` 字节码实测为
`configurer.addPathPrefix(Apps.getAppName(), predicate: BaseComponentController.class
.isAssignableFrom(aClass))`。判别是**传递父类链**，不是字符串包含 ⇒ 本护栏要求证据件的
`classlist_sha256` 可由复算器原样重现，防止把子串启发式当机制。
"""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'DEPLOYED-FULL-DOMAIN-OP-SURFACE.json'
TOOL = ROOT / 'tools' / 'core' / 'decompile' / 'enumerate_full_domain_op_surface.py'
LEGACY = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'DEPLOYED-OP-SURFACE.json'
CLASSDIR = Path('<HERMES_HOME>/cache/scratch/sup_v2')

# 域规模下界（实测；只允许增长，缩水即扫描根/解析出问题）
# class_files = 磁盘 .class 文件数；class_count = 去重后 FQCN 数（fat jar 内有同名副本）
MIN_FILES, MIN_CLASS, MIN_ROUTED, MIN_METHODS, MIN_OPS, MIN_JARS = (1170, 1044, 238,
                                                                   2110, 2107, 53)


def _evid():
    return json.loads(EVID.read_text(encoding='utf-8'))


def _bytes_match(a: bytes, b: bytes) -> bool:
    """字节级复算判等（本件是复算产物：格式也是契约的一部分）。"""
    return a == b


def _load_tool():
    spec = importlib.util.spec_from_file_location('fdos', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_superset_argument_is_empirically_checked():
    """① 域 ⊇ 全部注解路由类：不得存在「有路由却不含 bind/annotation」的类。"""
    assert _evid()['routed_without_bind_annotation'] == []


def test_both_same_domain_controls_pass():
    """② 两条同域对照都须 PASS。"""
    d = _evid()
    c = d['same_domain_control']
    assert c['contract_ops'] == 674 and c['hits'] == 674 and c['verdict'] == 'PASS'
    r = d['relocated_32_control']
    assert r['total'] == 32 and r['hits'] == 32 and r['verdict'] == 'PASS'


def test_remaining_sixty_have_zero_hits_in_the_full_deployed_domain():
    t = _evid()['target_60']
    assert t['total'] == 60 and t['hits'] == 0


def test_zero_hit_does_not_depend_on_the_prefix_spelling():
    """③ 稳健性：三种前缀写法下余 60 都须 0 命中。"""
    v = _evid()['robustness_variants']
    assert set(v) == {'none', 'substr'}
    for mode, rec in v.items():
        assert rec['remaining_60_hits'] == 0, f'{mode} 变体下余 60 出现了命中'
    # 反向：'none' 变体必须**确实**丢了前缀（否则该变体没起作用、稳健性论证是空的）
    assert v['none']['relocated_32_hits'] < 32, 'none 变体未丢前缀，稳健性对照无效'


def test_domain_scale_does_not_shrink():
    d = _evid()
    assert d['class_files'] >= MIN_FILES
    assert d['class_count'] >= MIN_CLASS
    assert d['classes_with_routes'] >= MIN_ROUTED
    assert d['methods'] >= MIN_METHODS
    assert d['distinct_op'] >= MIN_OPS
    assert d['jars_contributing_ops'] >= MIN_JARS


def test_duplicate_class_names_do_not_hide_routes():
    """文件索引按 FQCN 建 dict 会合并同名副本 —— 必须实测「没有两副本都带路由」。"""
    d = _evid()['duplicate_class_names']
    assert d['groups'] > 0, 'fat jar 内竟无同名副本？与部署形态不符，须复核'
    assert d['route_conflicts'] == [], f'有同名类两份都带路由，会丢端点: {d["route_conflicts"]}'


def test_prefix_mechanism_is_recorded_with_its_bytecode_authority():
    """前缀机制必须带权威类名，不得只剩散文。"""
    pm = _evid()['prefix_mechanism']
    assert 'WebAutoConfiguration' in pm['authority']
    assert 'addPathPrefix' in pm['bytecode']
    assert 'isAssignableFrom' in pm['bytecode']
    assert pm['app_name_used'] == 'udc'
    joined = ' '.join(pm['reading'])
    assert '/udc/file/download' in joined, '缺 LIVE 锚点'


def test_full_domain_evidence_is_recomputable_by_the_tool(tmp_path):
    """证据件可由复算器原样重现（class 根随 scratch 清理会消失 ⇒ skip 并说明）。"""
    if not CLASSDIR.is_dir():
        import pytest
        pytest.skip(f'部署态 class 根不可用（scratch 已清理）: {CLASSDIR}')
    out = tmp_path / 'rerun.json'
    assert _load_tool().main(['--class-dir', str(CLASSDIR), '--emit', str(out)]) == 0
    assert json.loads(out.read_text(encoding='utf-8')) == _evid()
    # ★ 且须**字节级**一致：本件是复算产物，任何手改（哪怕只改 limitations 文案）
    #   都会让复算基线失效。indent=2 / sort_keys=True / 结尾无换行 都是契约的一部分
    #   （本轮教训：只改证据件不改生成处 ⇒ 该测试 FAILED）。
    assert out.read_bytes() == EVID.read_bytes(), (
        '证据件与复算器输出非字节一致 ⇒ 该件被手工改写过：请改 '
        'tools/core/decompile/enumerate_full_domain_op_surface.py 的生成处后重跑，勿直接编辑本件')


def test_legacy_udc_jar_domain_verdict_is_consistent_with_the_full_domain():
    """与第十八轮「22 个 udc-*.jar 单域」裁定一致性：两域都必须 674/674 且余 60 = 0。"""
    legacy = json.loads(LEGACY.read_text(encoding='utf-8'))
    assert legacy['same_domain_control']['verdict'] == 'PASS'
    assert legacy['target_60']['hits'] == 0
    d = _evid()
    assert d['same_domain_control']['verdict'] == 'PASS'
    assert d['target_60']['hits'] == 0
    # 全域必须是单域的**扩大**（单域 jar 数 <= 全域贡献 jar 数）
    assert d['jars_contributing_ops'] >= len(legacy['per_jar'])


def test_limitations_keep_the_dynamic_register_boundary():
    """边界必须留在件里：动态注册通道 ⇒ 「60 条不存在」不可断言。"""
    lim = ' '.join(_evid()['limitations'])
    assert 'ControllerDynamicRegister' in lim
    assert '不可断言' in lim


def test_byte_identity_check_bites_on_a_whitespace_only_edit():
    """内存内突变自证 ①：**只改缩进**（parsed JSON 完全相同）也必须被判为不一致。

    这正是本轮的教训：上轮手工改了本件 limitations 的换行/缩进，parsed 相等 ⇒
    只要护栏只比 parsed，改动就溜过去了。这里直接证伪「只比 parsed 就够」。
    """
    raw = EVID.read_bytes()
    # 只加一个空格到缩进（parsed JSON 完全等价）—— 无需任何转义，避免再次踩到转义坑
    mutated = raw.replace(b'"class_count"', b' "class_count"', 1)
    assert mutated != raw, '突变没生效，测试无效'
    # 语义未变：parsed 相等
    assert json.loads(mutated.decode('utf-8')) == json.loads(raw.decode('utf-8'))
    # 但字节不等 ⇒ 字节护栏必须拒绝（这正是只比 parsed 会漏掉的情形）
    assert not _bytes_match(mutated, raw)


def test_byte_identity_check_bites_on_a_reformatted_but_semantically_equal_file():
    """内存内突变自证 ②：整件按 indent=4 重新序列化（语义 100% 等价）也必须被判为不一致 ——
    证明本件是**复算产物**而非可自由重排的散文，格式（indent=2 / sort_keys / 无尾换行）是契约的一部分。
    """
    d = _evid()
    reformatted = json.dumps(d, ensure_ascii=False, indent=4).encode('utf-8')
    assert json.loads(reformatted.decode('utf-8')) == d
    assert not _bytes_match(reformatted, EVID.read_bytes())


def test_cleaning_gate_no_customer_identifiers():
    s = EVID.read_text(encoding='utf-8')
    for token in ('znxmglpt', 'chjh', 'sy_access_token', 'xiangmuguanli', 'peixunudc'):
        assert token not in s, f'含客户/敏感串 {token!r}'
    assert not re.search(r'\d{15,}', s), '含长数字串（疑似客户 appId/记录 id）'
