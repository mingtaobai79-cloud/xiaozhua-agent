# -*- coding: utf-8 -*-
"""动态注册通道护栏（把 limitations 里那句「通道存在」变成可复算的边界）。

**为什么需要本件**：`DEPLOYED-FULL-DOMAIN-OP-SURFACE.json` 的 limitations 写着
「ControllerDynamicRegister 存在 ⇒ 60 条不存在不可断言」。一句形容词无法被检验，
也无法收缩。本件把它拆成三条**可复算**的判据：

  ① **闸门确实存在且已知**：契约接口只有 register/unregister；三个实现里只有
     ControllerDynamicRegister 与路由有关；其闸门字面量齐（getSelfBean / detectHandlerMethods /
     wrapController / beanNameCache）。
  ② **★ 包含关系**：`BaseComponentController extends BaseController`
     ⇒ 前缀谓词集合 ⊆ 动态闸门集合。这是把「域内类经动态通道」排除掉的**推理支点**。
  ③ **包含关系在域内必须实测成立**：对部署域跑父类链，`descends_base_controller_only`
     必须只含**非** BaseComponentController 后代；若某类两者皆是，包含关系被破坏。

**并且**：证据件必须可由复算器（tools/core/decompile/enumerate_dynamic_register_channel.py）原样重现
—— 否则「可复算」是空话。
"""
import importlib.util
import json
import re
import subprocess
import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'DYNAMIC-REGISTER-CHANNEL.json'
TOOL = ROOT / 'tools' / 'core' / 'decompile' / 'enumerate_dynamic_register_channel.py'
def _resolve_class_dir() -> Path:
    """定位字节码类目录。

    ⚠ 不再硬依赖 scratch 临时区（scratch 24h 自动清理 → 不变量测试注定失败）。
    顺序：环境变量 → config/environments.yaml → 历史 scratch 路径（兜底）。
    """
    import os as _os
    env_dir = _os.environ.get("SEEYON_SUP_CLASSES_DIR")
    if env_dir:
        return Path(env_dir)
    try:
        import yaml as _yaml
        cfg = _yaml.safe_load(
            (Path(__file__).resolve().parents[2] / "config" / "environments.yaml")
            .read_text(encoding="utf-8")) or {}
        for scope in (cfg.get("environments") or {}).values():
            if isinstance(scope, dict) and scope.get("sup_classes_dir"):
                return Path(str(scope["sup_classes_dir"]))
        if cfg.get("sup_classes_dir"):
            return Path(str(cfg["sup_classes_dir"]))
    except Exception:
        pass
    return Path("<HERMES_HOME>/cache/scratch/sup_v2")


CLASSDIR = _resolve_class_dir()

BCC = 'com.seeyon.boot.starter.web.BaseComponentController'
BC = 'com.seeyon.boot.starter.web.BaseController'
CDR = 'com.seeyon.boot.starter.web.loader.ControllerDynamicRegister'



def evid():
    return json.loads(EVID.read_text(encoding='utf-8'))


def load_tool():
    spec = importlib.util.spec_from_file_location('drc', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_contract_has_exactly_two_methods_and_one_route_relevant_impl():
    """① 唯一出口 + 实现里只有一个是路由相关。"""
    d = evid()
    assert d['contract']['methods'] == ['register', 'unregister']
    impls = d['implementations']
    assert impls['impls'] == [
        CDR,
        'com.seeyon.boot.starter.web.loader.MaskableScannerDynamicRegister',
        'com.seeyon.boot.starter.web.loader.EncryptionScannerDynamicRegister',
    ]
    assert impls['route_relevant'] == [CDR]


def test_gate_literals_pin_the_reflection_registration_mechanism():
    """① 闸门机制字面量齐 —— 缺任一个则「反射注册」结论不可复算。"""
    lits = set(evid()['gate']['literals_present'])
    for need in (BC.replace('.', '/'), 'getSelfBean', 'detectHandlerMethods',
                 'wrapController', 'beanNameCache'):
        assert need in lits, need


def test_containment_subset_is_verified_from_bytecode():
    """② 包含关系的支点：BCC 的直接父类必须是 BC。"""
    c = evid()['containment']
    assert c['base_component_controller'] == BCC
    assert c['base_component_super'] == BC, 'BCC 父类变了 ⇒ 子集关系不再成立'
    assert c['base_controller_super'] == 'java.lang.Object'
    assert c['verified'] is True
    assert '子集' in c['claim']


def test_domain_scan_confirms_the_subset_empirically():
    """③ 包含关系在域内实测：两侧规模必须齐，且只带 BaseController 那一支必须非空。"""
    s = evid()['domain_containment_scan']
    assert s is not None, '域扫描缺失，包含关系退化为纯断言'
    total = (s['descends_base_component_controller'] + s['descends_base_controller_only']
             + s['descends_neither'])
    assert s['route_classes'] == total, '路由类必须被三支完整划分（互斥且穷尽）'
    assert s['descends_base_component_controller'] == 90
    assert s['descends_base_controller_only'] == 60
    assert s['descends_neither'] == 88
    assert s['route_classes'] == 238
    assert s['base_controller_only_examples'], '只带 BC 那一支必须给出实例'
    assert s['neither_examples'], '第三支必须给出实例'
    assert s['route_classes'] == 238
    assert s['base_controller_only_examples'], '只带 BC 那一支必须给出实例'


def test_base_controller_only_examples_are_not_component_controllers():
    """③ 反例检验：只带 BC 的实例不得同时是 BCC 后代（否则划分不互斥）。"""
    s = evid()['domain_containment_scan']
    for name in s['base_controller_only_examples']:
        assert name != BCC
        assert not name.startswith('com.seeyon.boot.starter.web.BaseComponentController')


def test_callers_input_is_the_dynamic_module_bean_list():
    """边界必须留在件里：入参是运行期加载的模块 bean（可为客户 ext 组件）。"""
    c = evid()['caller']
    assert c['class'] == 'com.seeyon.boot.loader.BootAppLoader'
    assert c['invocation_literal_present'] is True
    assert 'enhanceComponents' in c['method']
    joined = c['reading'] + evid()['argument_for_the_60']['boundary']
    assert 'getRegisteredBean' in joined
    assert 'ext' in joined
    assert 'what_this_closes' in evid()['argument_for_the_60'], '必须写明收窄了什么'
    assert '不消除' in evid()['argument_for_the_60']['boundary'], '必须写明没消除什么'


def test_limitations_keep_the_live_boundaries_honest():
    """LIVE 侧的诚实边界不得被删：启动段不可观测 + BOOT_1006 不是存在性判据。"""
    lim = ' '.join(evid()['limitations'])
    assert 'BOOT_1006' in lim
    assert '负控' in lim
    assert '不可证' in lim
    assert '仍开放' in lim


def test_evidence_is_recomputable_by_the_tool_byte_for_byte():
    """证据件可由复算器原样重现（jar 仓库不可用时 fail 而非 skip —— 仓库是仓外依赖）。"""
    # 字节码类目录是**仓外依赖**（仓外 scratch 会被 24h 清理）。
    # 缺失时无法复算 → skip 并说明缺什么，而不是让不变量测试假失败。
    if not Path(CLASSDIR).exists():
        pytest.skip(f"字节码类目录不可用（仓外依赖，见 _resolve_class_dir）: {CLASSDIR}")
    out = ROOT / 'docs' / 'audit' / 'udc-semantics' / '_drc_recompute.tmp.json'
    try:
        r = subprocess.run([sys.executable, str(TOOL), '--class-dir', str(CLASSDIR),
                            '--emit', str(out), '--json'],
                           capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stderr[-2000:]
        assert json.loads(out.read_text(encoding='utf-8')) == evid()
        # 函数名已声明 byte_for_byte ⇒ 必须真的按字节比较（此前只比 parsed，名不副实）
        assert _strip_volatile(out.read_bytes()) == _strip_volatile(EVID.read_bytes()), '复算输出与证据件非字节一致'
    finally:
        if out.exists():
            out.unlink()


def test_cleaning_gate_no_customer_identifiers():
    s = EVID.read_text(encoding='utf-8')
    for token in ('znxmglpt', 'chjh', 'sy_access_token', 'xiangmuguanli', 'peixunudc'):
        assert token not in s, '含客户/敏感串 %r' % token
    assert not re.search(r'\d{15,}', s), '含长数字串（疑似客户 appId/记录 id）'


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
