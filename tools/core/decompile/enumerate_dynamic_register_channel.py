# -*- coding: utf-8 -*-
"""动态注册通道（ControllerDynamicRegister）—— 从散文升级为字节码锚定 + 复算器。

要回答的问题（PROGRESS 遗留 / DEPLOYED-FULL-DOMAIN-OP-SURFACE.json 的 limitations）：
ControllerDynamicRegister 存在 ⇒ 「余 60 条不存在」不可断言。本轮把「存在通道」压到
通道的必要条件 + 域边界，让边界可复算，而不是一句形容词。

本件确立的静态事实（全部直读 .class 常量池，来源 = maven 仓库，可复算）：

1. 契约：com.seeyon.boot.loader.ComponentDynamicRegister 只有 register / unregister
   —— 动态通道的唯一出口。该接口只在 boot-core 内。
2. 实现（boot-starter-web 的 META-INF/spring.factories）：三个实现，只有
   ControllerDynamicRegister 与路由有关。
3. 通道闸门（ControllerDynamicRegister.register）：
   beanName -> getSelfBean(beanName)，非 BaseController 直接 continue；
   放行者经 wrapController 后反射调用 RequestMappingHandlerMapping.detectHandlerMethods 注册。
4. 包含关系（本件关键推理）：WebAutoConfiguration.configurePathMatch 的前缀谓词是
   BaseComponentController.class.isAssignableFrom(aClass)，而
   BaseComponentController extends BaseController
   ⇒ 前缀谓词集合 是 动态注册闸门集合 的子集。
   即：凡能拿到 /udc 前缀的控制器，必然也能被动态闸门放行（反之不然）。

为什么这条包含关系重要：余 60 条 op 的 op 名带 udc 前缀，其路由必带 /udc 前缀段
⇒ 若由动态通道暴露，被注册控制器必为 BaseComponentController 后代
⇒ 其路由字面量本就在本任务静态扫描域内。故「域内类经动态通道注册」不产生新的静态不可见端点。

边界（不消除的部分）：动态注册的输入是 ModuleClassLoader.getRegisteredBean()，
= 运行期动态加载的模块 jar（可为客户 ext 组件），这类类不在磁盘构件内，静态扫描不可见。

用法：
    uv run --no-project python tools/enumerate_dynamic_register_channel.py --json
    uv run --no-project python tools/enumerate_dynamic_register_channel.py --class-dir DIR --emit OUT.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENV = ROOT / 'config' / 'environments.yaml'
EVID = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'DYNAMIC-REGISTER-CHANNEL.json'

INTERFACE = 'com/seeyon/boot/loader/ComponentDynamicRegister.class'
REGISTER = 'com/seeyon/boot/starter/web/loader/ControllerDynamicRegister.class'
BASECOMP = 'com/seeyon/boot/starter/web/BaseComponentController.class'
BASECTRL = 'com/seeyon/boot/starter/web/BaseController.class'
AUTOCONF = 'com/seeyon/boot/starter/web/WebAutoConfiguration.class'
BOOTAPP = 'com/seeyon/boot/loader/BootAppLoader.class'
FACTORIES_KEY = 'com.seeyon.boot.loader.ComponentDynamicRegister'

BASECOMP_FQCN = 'com.seeyon.boot.starter.web.BaseComponentController'
BASECTRL_FQCN = 'com.seeyon.boot.starter.web.BaseController'
CONT = chr(92)


def to_dots(name):
    """常量池里类名是斜杠形式（com/x/Y），本件统一转点形式。"""
    return (name or '').replace('/', '.')


def default_repo_root():
    """从 config/environments.yaml 的 local-maven.maven_root 读 jar 仓库根（不写死路径）。"""
    if not ENV.exists():
        return None
    for line in ENV.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if s.startswith('maven_root:'):
            return Path(s.split(':', 1)[1].split('#')[0].strip())
    return None


def pick(repo: Path, artifact: str, member: str):
    """取该 artifact 最高版本 jar 内某成员的字节（版本不写死）。"""
    cands = []
    for j in (repo / artifact).glob('*/' + artifact + '-*.jar'):
        m = re.search(r'-([0-9]+(?:[.][0-9]+)*)[.]jar$', j.name)
        if m:
            cands.append((tuple(int(x) for x in m.group(1).split('.')), j))
    if not cands:
        raise FileNotFoundError('no jar for ' + artifact + ' under ' + str(repo))
    cands.sort()
    jar = cands[-1][1]
    with zipfile.ZipFile(jar) as z:
        return jar, z.read(member)


def scan_class(b):
    """极简 class 头扫描，返回 (this_class, super_class, 常量池 Utf8 集合) 或 None。"""
    if struct.unpack_from('>I', b, 0)[0] != 0xCAFEBABE:
        return None
    cnt = struct.unpack_from('>H', b, 8)[0]
    o = 10
    utf8, cls, lits = {}, {}, set()
    i = 1
    while i < cnt:
        tag = b[o]
        o += 1
        if tag == 1:
            n = struct.unpack_from('>H', b, o)[0]
            o += 2
            s = b[o:o + n].decode('utf-8', 'replace')
            o += n
            utf8[i] = s
            lits.add(s)
        elif tag == 7:
            cls[i] = struct.unpack_from('>H', b, o)[0]
            o += 2
        elif tag in (8, 16, 19, 20):
            o += 2
        elif tag == 15:
            o += 3
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            o += 4
        elif tag in (5, 6):
            o += 8
            i += 1
        else:
            return None
        i += 1
    o += 2
    this_i = struct.unpack_from('>H', b, o)[0]
    o += 2
    super_i = struct.unpack_from('>H', b, o)[0]

    def name(idx):
        t = cls.get(idx)
        return utf8.get(t, '') if t else ''

    return name(this_i), name(super_i), lits


def _toks(text):
    """按逗号切分并剥掉 spring.factories 续行符。"""
    return [x.strip().rstrip(CONT).strip() for x in text.split(',') if x.strip().rstrip(CONT).strip()]


def spring_factories_impls(jar, key):
    """解析 spring.factories（含续行语法），取该 key 的实现列表。"""
    with zipfile.ZipFile(jar) as z:
        txt = z.read('META-INF/spring.factories').decode('utf-8', 'replace')
    out, hit = [], False
    for raw in txt.splitlines():
        line = raw.rstrip()
        if line.strip().startswith(key):
            hit = True
            rest = (line.split('=', 1)[1] if '=' in line else '').lstrip(CONT)
            out += _toks(rest)
            if not line.endswith(CONT):
                hit = False
            continue
        if hit:
            out += _toks(line)
            if not line.endswith(CONT):
                hit = False
    return out


def _has_route(path):
    """路由判据与全域裁定器同源：用注解解析器，不用字面量启发式。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'ecm_drc', ROOT / 'tools' / 'core' / 'enumerate_class_http_mappings.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        p = mod.parse_class_file(path)
    except Exception:
        return False
    return bool(p['methods'] or p['class_mapping'])


def scan_domain(class_dir):
    """域内包含关系实测：按父类链把路由类分成 BaseComponentController 后代 / 仅 BaseController。"""
    parent = {}
    files = sorted(class_dir.rglob('*.class'))
    for f in files:
        try:
            got = scan_class(f.read_bytes())
        except OSError:
            continue
        if got and got[0]:
            parent[to_dots(got[0])] = to_dots(got[1])

    def reaches(cls, target):
        seen, cur = set(), cls
        while cur and cur not in seen:
            if cur == target:
                return True
            seen.add(cur)
            cur = parent.get(cur, '')
        return False

    with_routes, comp, base_only, neither = [], [], [], []
    for f in files:
        try:
            got = scan_class(f.read_bytes())
        except OSError:
            continue
        if not got:
            continue
        this, _sup, _lits = got
        if not _has_route(f):
            continue
        this = to_dots(this)
        with_routes.append(this)
        if reaches(this, BASECOMP_FQCN):
            comp.append(this)
        elif reaches(this, BASECTRL_FQCN):
            base_only.append(this)
        else:
            neither.append(this)
    return {
        'class_files': len(files),
        'route_classes': len(with_routes),
        'descends_base_component_controller': len(comp),
        'descends_base_controller_only': len(base_only),
        'descends_neither': len(neither),
        'base_controller_only_examples': sorted(base_only)[:10],
        'neither_examples': sorted(neither)[:10],
        'reading': ('prefix predicate set (BaseComponentController 后代) 是 '
                    'gate set (BaseController 后代) 的子集；本扫描给出两侧实测规模。'
                    '第三支 descends_neither = 既不继承 BaseController 也带路由的类，'
                    '它们既拿不到 /udc 前缀、也不能被动态闸门放行。'),
    }


def build(repo, class_dir=None):
    core_jar, iface_b = pick(repo, 'boot-core', INTERFACE)
    web_jar, reg_b = pick(repo, 'boot-starter-web', REGISTER)
    _w, comp_b = pick(repo, 'boot-starter-web', BASECOMP)
    _w, ctrl_b = pick(repo, 'boot-starter-web', BASECTRL)
    _w, autoc_b = pick(repo, 'boot-starter-web', AUTOCONF)
    boot_jar, boot_b = pick(repo, 'boot-core', BOOTAPP)

    comp = scan_class(comp_b)
    ctrl = scan_class(ctrl_b)
    iface_lits = scan_class(iface_b)[2]
    reg_lits = scan_class(reg_b)[2]
    autoc_lits = scan_class(autoc_b)[2]
    boot_lits = scan_class(boot_b)[2]

    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    domain = scan_domain(Path(class_dir)) if (class_dir and Path(class_dir).is_dir()) else None
    return {
        'schema': 'dynamic-register-channel.v1',
        'evidence': 'VERIFIED_STATIC_BYTECODE (直读 .class 常量池)',
        'sources': {
            'boot_core_jar': core_jar.name,
            'boot_core_sha256_16': sha(core_jar)[:16],
            'boot_starter_web_jar': web_jar.name,
            'boot_starter_web_sha256_16': sha(web_jar)[:16],
        },
        'contract': {
            'fqcn': 'com.seeyon.boot.loader.ComponentDynamicRegister',
            'methods': sorted(x for x in iface_lits if x in ('register', 'unregister')),
            'reading': '动态通道的唯一出口：register(module, beans) / unregister(module)。',
        },
        'implementations': {
            'source': 'boot-starter-web :: META-INF/spring.factories',
            'key': FACTORIES_KEY,
            'impls': spring_factories_impls(web_jar, FACTORIES_KEY),
            'route_relevant': ['com.seeyon.boot.starter.web.loader.ControllerDynamicRegister'],
        },
        'gate': {
            'class': 'com.seeyon.boot.starter.web.loader.ControllerDynamicRegister',
            'condition': 'controllerBean instanceof BaseController',
            'literals_present': sorted(x for x in reg_lits if x in (
                BASECTRL_FQCN.replace('.', '/'), 'BaseController', 'detectHandlerMethods',
                'getSelfBean', 'beanNameCache', 'wrapController', 'unregister')),
            'reading': ('beanName -> SeeyonBeanFactory.getSelfBean；非 BaseController 直接 continue；'
                        '放行者经 wrapController 后反射调用 '
                        'RequestMappingHandlerMapping.detectHandlerMethods 注册。'),
        },
        'prefix_predicate': {
            'class': 'com.seeyon.boot.starter.web.WebAutoConfiguration.configurePathMatch',
            'literals_present': sorted(x for x in autoc_lits if x in (
                'addPathPrefix', 'isAssignableFrom')),
            'reading': '前缀谓词 = BaseComponentController.class.isAssignableFrom(aClass)。',
        },
        'containment': {
            'claim': ('前缀谓词集合 是 动态注册闸门集合 的子集，凡能取到 /udc 前缀的控制器'
                      '必然也被动态闸门放行（反之不然）。'),
            'base_component_controller': to_dots(comp[0]) if comp else '',
            'base_component_super': to_dots(comp[1]) if comp else '',
            'base_controller_super': to_dots(ctrl[1]) if ctrl else '',
            'verified': bool(comp) and to_dots(comp[1]) == BASECTRL_FQCN,
        },
        'caller': {
            'class': 'com.seeyon.boot.loader.BootAppLoader',
            'method': 'enhanceComponents(moduleName, beanNameList)',
            'invocation_literal_present': 'enhanceComponents' in boot_lits,
            'reading': ('BootAppLoader 以 ModuleClassLoader.getRegisteredBean() 为入参调用 '
                        'enhanceComponents，逐个 ComponentDynamicRegister.register(module, beans)。'
                        'getRegisteredBean() = 运行期动态加载的模块 bean（可为客户 ext 组件）。'),
        },
        'argument_for_the_60': {
            'claim': ('余 60 条 op 的 op 名均以 udc 开头。op 名由路径导出（graphql_op_naming），'
                      '故其路由必带 /udc 前缀段；而 /udc 前缀只由 WebAutoConfiguration 的谓词'
                      '（BaseComponentController 后代）施加。若某路由由动态通道暴露且 op 名仍以 udc'
                      '开头，则该控制器必为 BaseComponentController 后代。'
                      '又因为 前缀谓词集合 是 闸门集合(BaseController 后代) 的子集 —— 闸门比前缀更宽，'
                      '故动态通道不会把「本该带 /udc 前缀」的类漏出前缀规则之外。'),
            'what_this_closes': ('把限制从「动态通道存在，边界无界」收窄为：动态通道暴露的'
                                 'udc 前缀路由，其控制器必属 BaseComponentController 后代这一已知类别。'),
            'boundary': ('不消除的部分：BCC 是平台公开类，运行期加载的域外模块（客户 ext 组件）'
                         '同样可以继承它，而这类类不在磁盘构件内、静态扫描不可见。'
                         '故「60 条不存在」仍不可断言。'),
        },
        'domain_containment_scan': domain,
        'limitations': [
            'LIVE 启动段不可观测：pod 日志仅保留约 2 小时，容器 startTime 在前一日，'
            'register() 是否在启动/加载期被调用于本窗口不可证。',
            'LIVE HTTP 探针不可用：/udc/** 未带会话一律返回 BOOT_1006，且负控'
            '（明显不存在的路由）返回完全相同响应，故 BOOT_1006 不是路由存在性/可用性判据。',
            '本件只把 域内类经动态通道暴露 一支排除；运行期加载的域外 ext 组件 支仍开放。',
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description='动态注册通道字节码锚定器（离线只读）')
    ap.add_argument('--repo-root', default=None, help='jar 仓库根（默认取 environments.yaml）')
    ap.add_argument('--class-dir', default=None, help='域 class 根（可选，做包含关系实测）')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--emit', default=None, help='证据件输出路径')
    a = ap.parse_args(argv)
    repo = Path(a.repo_root) if a.repo_root else default_repo_root()
    if not repo or not repo.exists():
        print(json.dumps({'error': 'repo_root 未找到', 'repo_root': str(repo)}, ensure_ascii=False))
        return 2
    payload = build(repo, a.class_dir)
    txt = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if a.emit:
        Path(a.emit).write_text(txt, encoding='utf-8', newline='\n')
    if a.json or not a.emit:
        print(txt)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
