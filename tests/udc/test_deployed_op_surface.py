# -*- coding: utf-8 -*-
"""部署态 op 面裁定护栏：余 60 条 `udc*` 未归位 op 在**部署态**是否承接。

**为什么这轮才有资格裁**：历轮「构件本身不在本仓库」只是**推断**（`pods/exec` RBAC
forbidden）。本轮 `pods/exec` 实为 ALLOWED，首次取出部署态 `BOOT-INF/lib`（544 jar，
含 11 个本地缺失的 udc 构件）⇒ 该域内可做**真裁定**。

**判据（三层，缺一层就不成立）**：
  ① **同域对照必须 PASS**：udc-web 674 契约 op 面须全落本域（674/674）。
     —— 对照**必须同域**；跨域拿 sandbox 族当阳性对照会得 5/32 的**假阴性**
     （sandbox 归位到 `boot-starter-sandbox`，不在 22 个 udc jar 内），
     第十七轮的「32/32 阳性对照」正是该口径错用，本护栏把它钉在解释位而非判据位。
  ② **余 60 条 0 命中**；③ 域规模下界（jar/class/method/op 不得缩水）。
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'DEPLOYED-OP-SURFACE.json'
LIB = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'DEPLOYED-LIB-INVENTORY.json'
TOOL = ROOT / 'tools' / 'core' / 'decompile' / 'enumerate_deployed_op_surface.py'

# 域规模下界（部署态实测；只允许增长，缩短即扫描根/解析出问题）
MIN_CLASSES, MIN_METHODS, MIN_OPS = 100, 958, 958


def _evid():
    return json.loads(EVID.read_text(encoding='utf-8'))


def _load_tool():
    spec = importlib.util.spec_from_file_location('dos', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_same_domain_control_passes_so_zero_hit_is_not_a_dead_scanner():
    c = _evid()['same_domain_control']
    assert c['contract_ops'] == 674 and c['hits'] == 674
    assert c['verdict'] == 'PASS'


def test_remaining_sixty_have_zero_hits_in_the_deployed_domain():
    t = _evid()['target_60']
    assert t['total'] == 60 and t['hits'] == 0


def test_domain_scale_does_not_shrink():
    d = _evid()
    assert d['classes'] >= MIN_CLASSES
    assert d['methods'] >= MIN_METHODS
    assert d['distinct_op'] >= MIN_OPS
    assert len(d['per_jar']) >= 10
    # 该域必须包含本地缺失构件（否则不叫部署态域）
    assert 'udc-upgrade-5.3.517.jar' in d['per_jar']


def test_cross_domain_positive_control_is_recorded_as_explanation_not_criterion():
    """口径护栏：跨域对照不得回到判据位。"""
    r = _evid()['relocated_32_in_this_domain']
    assert r['hit_count'] < 32, '跨域命中必须 < 32，否则口径又错了'
    assert '口径错用' in r['explanation']


def test_evidence_recomputable_by_the_tool(tmp_path):
    """证据件可由复算器复现 —— 结论面逐字判等（域规模键同样参与）。"""
    d = _evid()
    # 复算器只吃 jar 目录；目录随 scratch 清理会消失 ⇒ 不可用时 skip 并说明
    lib = Path(d.get('lib_dir') or '<HERMES_HOME>/cache/scratch/djars')
    if not lib.is_dir():
        import pytest
        pytest.skip(f'部署态 jar 目录不可用（scratch 已清理）: {lib}')
    out = tmp_path / 'rerun.json'
    assert _load_tool().main(['--lib-dir', str(lib), '--emit', str(out)]) == 0
    assert json.loads(out.read_text(encoding='utf-8')) == d
    # ★ 本件是复算产物 ⇒ 字节即契约：parsed 相等会漏掉格式/换行漂移
    assert out.read_bytes() == EVID.read_bytes(), '复算输出与证据件非字节一致'


def test_guardrail_bites_on_a_lf_reserialization():
    """会咬自证：LF 版本 parsed 等价却必须被判字节不等。

    本件此前只靠 Windows 文本模式隐式转 CRLF 才能被“原样重现”，
    Linux 上同一工具会出 LF ⇒ 该不变量本来是宿主依赖的。现已显式钉死。
    """
    raw = EVID.read_bytes()
    assert raw.count(bytes([13, 10])) > 0, '证据件应为 CRLF'
    lf = raw.replace(bytes([13, 10]), bytes([10]))
    assert json.loads(lf.decode('utf-8')) == _evid()   # 语义 100% 等价
    assert lf != raw                                   # 但换行是契约的一部分


def test_cleaning_gate_no_customer_identifiers():
    s = EVID.read_text(encoding='utf-8')
    for token in ('znxmglpt', 'chjh', 'sy_access_token', 'xiangmuguanli'):
        assert token not in s
    import re
    assert not re.search(r'\d{15,}', s)


def test_deployed_lib_evidence_agrees_on_the_domain():
    """与部署态 lib 清单交叉：域内 jar 名必须是 udc 构件且版本 5.3.517。"""
    lib = json.loads(LIB.read_text(encoding='utf-8'))
    assert set(lib['udc_jars']) >= set(_evid()['per_jar'])
    assert all(n.endswith('-5.3.517.jar') for n in _evid()['per_jar'])
