# -*- coding: utf-8 -*-
"""全部署域 op 面枚举 / 余量裁定器（离线只读，VERIFIED_STATIC_BYTECODE）。

问题：余 60 条未归位 `udc*` op，在**部署态全构件注解路由面**（而非 22 个 `udc-*.jar`
单域）内是否承接？

域（可证超集，非预筛）：任何带 @RequestMapping/@GetMapping/... 的类，其常量池必然引用
`org/springframework/web/bind/annotation/*`。故取「常量池含 bind/annotation 的 class」
为域 = 全部 HTTP 注解类的超集。教训：按「类级 mapping 字面量存在」预筛会丢
`ParameterController`（无类级 mapping、方法齐全），曾致 668/674 的假 FAIL。

前缀机制（CFR 权威锚定，取代此前散文表述）——boot-starter-web-5.3.358 的
`com.seeyon.boot.starter.web.WebAutoConfiguration.configurePathMatch` 实测字节码：

    configurer.addPathPrefix(Apps.getAppName(), predicate:
        BaseComponentController.class.isAssignableFrom(aClass));

要点：① 前缀段 = Apps.getAppName()（运行期取值，本部署 = udc），非硬编码字面量；
② 判据是**传递父类链** isAssignableFrom，不是字符串包含（本器读 super_class 做闭包）。
LIVE 锚点：/service//udc/file/download（FileController 自身 mapping=file、方法=download
⇒ 叠加段 = udc）。

同域对照：udc-web 674 契约须 674/674；跨构件归位 32 条须 32/32（这 32 条正是靠前缀机制
归位，故同时校验前缀规则）。另跑 none/substr 两变体做稳健性：余 60 的 0 命中不得依赖
某一种前缀写法。

用法：
    uv run --no-project python tools/enumerate_full_domain_op_surface.py \
        --class-dir <HERMES_HOME>/cache/scratch/sup --emit <out.json>
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UNLOCATED = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'frontend-udc-unlocated.json'
CONTRACT = (ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-web-5.3.517-contracts'
            / '_api_full.json')
BCC = 'com/seeyon/boot/starter/web/BaseComponentController'


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_super(data):
    """极简常量池读取：只取 super_class / this_class 名（不经 javap/CFR）。"""
    o = 8
    n = struct.unpack_from('>H', data, o)[0]
    o += 2
    pool = {}
    i = 1
    while i < n:
        tag = data[o]
        o += 1
        if tag == 1:
            ln = struct.unpack_from('>H', data, o)[0]
            o += 2
            pool[i] = data[o:o + ln].decode('utf-8', 'replace')
            o += ln
        elif tag == 7:
            pool[i] = ('cls', struct.unpack_from('>H', data, o)[0])
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
            raise ValueError('unknown constant pool tag %d' % tag)
        i += 1
    o += 2
    this_i = struct.unpack_from('>H', data, o)[0]
    o += 2
    sup_i = struct.unpack_from('>H', data, o)[0]

    def nm(idx):
        v = pool.get(idx)
        return pool.get(v[1]) if isinstance(v, tuple) else None

    return nm(sup_i), nm(this_i)


def build_domain(class_dir):
    """扫描 class 根，建 this_class -> super_class 映射 + 文件索引。

    注意：同一 FQCN 可能在多个 jar 里各有一份（部署 fat jar 内重复）。文件索引按
    FQCN 建 dict 会**合并**这些重复名 —— 故另返回 dup_groups（>1 份的 FQCN -> 路径表），
    供上层核验「不存在两份同名类各自都带路由」的情形，即不会因合并而丢端点。
    """
    parent, files, byname = {}, {}, {}
    for f in sorted(class_dir.rglob('*.class')):
        rel = '/'.join(f.relative_to(class_dir).parts)
        try:
            sup, this = read_super(f.read_bytes())
        except Exception:
            continue
        parent[this] = sup
        byname.setdefault(this, []).append(rel)
        # 同名的后续副本只登记文件清单，不覆盖首份（避免路径漂移）
        files.setdefault(this, (f, rel))
    dup_groups = {k: v for k, v in byname.items() if len(v) > 1}
    return parent, files, dup_groups


def make_is_bcc(parent):
    """传递闭包判据（不是字符串包含）。"""
    def is_bcc(t):
        seen = set()
        while t and t not in seen:
            seen.add(t)
            if t == BCC:
                return True
            t = parent.get(t)
        return False
    return is_bcc


def scan(class_dir, app_name, mode):
    """mode in none|prefix|substr（后两者供稳健性对照）。"""
    ecm = _load('ecm', ROOT / 'tools' / 'core' / 'enumerate_class_http_mappings.py')
    gql = _load('gql', ROOT / 'components' / 'udc' / 'graphql_op_naming.py')
    parent, files, dup_groups = build_domain(class_dir)
    is_bcc = make_is_bcc(parent)
    routed = methods = prefixed = 0
    no_ann, ops, per_jar = [], {}, {}
    classlist = ['/'.join(f.relative_to(class_dir).parts)
                 for f in sorted(class_dir.rglob('*.class'))]
    for t, (f, rel) in sorted(files.items()):
        raw = f.read_bytes()
        try:
            p = ecm.parse_class_file(f)
        except Exception:
            continue
        if not p['methods'] and not p['class_mapping']:
            continue
        routed += 1
        if b'bind/annotation' not in raw:
            no_ann.append(rel)
        base = (p['class_mapping'] or '').strip('/')
        if mode == 'prefix':
            add = is_bcc(t)
        elif mode == 'substr':
            add = b'BaseComponentController' in raw
        else:
            add = False
        if add:
            prefixed += 1
            base = (app_name + '/' + base).strip('/')
        d = per_jar.setdefault(rel.split('/')[0], [0, 0])
        got = set()
        for m in p['methods']:
            d[1] += 1
            methods += 1
            for http, frags, _ in m['routes']:
                frag = (frags[0] if frags else '').lstrip('/')
                full = '/' + '/'.join(x for x in (base, frag) if x)
                got.add(gql.path_to_op(full, http if http != 'ANY' else 'GET'))
        d[0] = len(got)
        for o in got:
            ops.setdefault(o, []).append(rel)
    return {'class_count': len(files), 'routed': routed, 'methods': methods,
            'ops': ops, 'per_jar': per_jar, 'prefixed': prefixed,
            'no_ann': no_ann, 'classlist': classlist,
            'class_files': len(classlist), 'dup_name_groups': dup_groups}


def dup_route_conflicts(class_dir, parent, files):
    """核验：不存在「同一 FQCN 的两份副本各自都带路由」⇒ 合并索引不丢端点。

    返回冲突清单（应为空）。这是「按 FQCN 建 dict」这一实现选择的**实测检验**，
    而不是口头保证。
    """
    ecm = _load('ecm', ROOT / 'tools' / 'core' / 'enumerate_class_http_mappings.py')
    byname = {}
    for f in sorted(class_dir.rglob('*.class')):
        rel = '/'.join(f.relative_to(class_dir).parts)
        try:
            _sup, this = read_super(f.read_bytes())
        except Exception:
            continue
        byname.setdefault(this, []).append((f, rel))
    bad = []
    for name, copies in byname.items():
        if len(copies) < 2:
            continue
        routed = []
        for f, rel in copies:
            try:
                pr = ecm.parse_class_file(f)
            except Exception:
                continue
            if pr['methods'] or pr['class_mapping']:
                routed.append(rel)
        if len(routed) > 1:
            bad.append({'class': name, 'routed_copies': routed})
    return bad


def contract_ops():
    gql = _load('gql', ROOT / 'components' / 'udc' / 'graphql_op_naming.py')
    data = json.loads(CONTRACT.read_text(encoding='utf-8'))
    return {gql.path_to_op(m['full_path'], m.get('http', 'POST'))
            for body in data.values() for m in body.get('methods', [])
            if m.get('full_path')}


def build_payload(class_dir, app_name, conflicts=None):
    """复算全部署域 op 面 + 双同域对照 + 稳健性变体。"""
    un = json.loads(UNLOCATED.read_text(encoding='utf-8'))
    cops, rem, rel = contract_ops(), un['remaining_ops'], un['relocated_ops']
    res = scan(class_dir, app_name, 'prefix')
    ops = set(res['ops'])
    variants = {}
    for mode in ('none', 'substr'):
        vo = set(scan(class_dir, app_name, mode)['ops'])
        variants[mode] = {
            'distinct_op': len(vo),
            'same_domain_control_hits': len(cops & vo),
            'relocated_32_hits': sum(1 for o in rel if o in vo),
            'remaining_60_hits': sum(1 for o in rem if o in vo),
            'reading': '余 60 命中须仍为 0，否则 0 命中依赖前缀写法、不可断言',
        }
    return {
        'schema': 'deployed-op-surface-full.v1',
        'evidence': 'LIVE-DEPLOYED (pod BOOT-INF/lib) + VERIFIED_STATIC_BYTECODE',
        'domain': ('部署态全构件注解路由面（常量池含 bind/annotation 的 class，'
                   '= 全部 HTTP 注解类的可证超集）'),
        'domain_superset_argument': (
            '任何带 @RequestMapping/@GetMapping/... 的类必然引用 '
            'org/springframework/web/bind/annotation/*，故该筛选是超集；'
            'routed_without_bind_annotation 为该论证的实测检验（须为空）。'),
        'prefix_mechanism': {
            'authority': ('boot-starter-web-5.3.358 :: com.seeyon.boot.starter.web.'
                          'WebAutoConfiguration.configurePathMatch'),
            'bytecode': ('configurer.addPathPrefix(Apps.getAppName(), predicate: '
                         'BaseComponentController.class.isAssignableFrom(aClass))'),
            'reading': [
                '前缀段 = Apps.getAppName()（运行期取值，本部署 = udc），不是硬编码字面量',
                '判据是传递父类链 isAssignableFrom，不是字符串包含',
                'LIVE 锚点 /service//udc/file/download：FileController 自身 mapping=file、'
                '方法=download ⇒ 叠加段 = udc',
                'addPathPrefix 全仓仅在 boot-starter-web-5.3.358 命中，故该机制是单点权威源',
            ],
            'app_name_used': app_name,
        },
        'class_files': res['class_files'],
        'class_count': res['class_count'],
        'duplicate_class_names': {
            'groups': len(res['dup_name_groups']),
            'route_conflicts': conflicts or [],
            'reading': ('同一 FQCN 在多个 jar 内重复（部署 fat jar 常态）。'
                        'route_conflicts 为空 = 不存在「两份同名类各自都带路由」⇒ '
                        '按 FQCN 建索引合并副本不会丢端点。'),
        },
        'classlist_sha256': hashlib.sha256(
            '\n'.join(res['classlist']).encode()).hexdigest(),
        'classes_with_routes': res['routed'],
        'methods': res['methods'],
        'distinct_op': len(ops),
        'jars_contributing_ops': len(res['per_jar']),
        'classes_prefixed': res['prefixed'],
        'routed_without_bind_annotation': res['no_ann'],
        'same_domain_control': {
            'what': 'udc-web 674 契约 op 面在同域 op 集内的命中数',
            'contract_ops': len(cops), 'hits': len(cops & ops),
            'verdict': 'PASS' if cops <= ops else 'FAIL',
        },
        'relocated_32_control': {
            'what': ('跨构件归位 32 条同域命中数 —— 同时校验前缀规则本身'
                     '（这 32 条正是靠 addPathPrefix 才归位）'),
            'hits': sum(1 for o in rel if o in ops), 'total': len(rel),
            'verdict': 'PASS' if all(o in rel and o in ops for o in rel) else 'FAIL',
        },
        'target_60': {
            'hits': sum(1 for o in rem if o in ops), 'total': len(rem),
            'verdict': ('0 命中 ⇒ 部署态全构件注解路由面内确不承接（强负面）；'
                        '仍不可断言「不存在」，见 limitations'),
        },
        'robustness_variants': variants,
        'per_jar': {k: {'methods': res['per_jar'][k][1], 'ops': res['per_jar'][k][0]}
                    for k in sorted(res['per_jar'])},
        'limitations': [
            "域 = 磁盘构件内可注解路由面；运行期动态注册通道（ControllerDynamicRegister）已由 tools/enumerate_dynamic_register_channel.py 与 DYNAMIC-REGISTER-CHANNEL.json 锚定：其暴露的 udc 前缀路由，控制器必为 BaseComponentController 后代（前缀谓词集合 是 闸门集合 的子集）；未消除的部分 = 运行期加载的域外 ext 组件（不在磁盘构件内，静态不可见）⇒ 「60 条不存在」仍不可断言。",
            "不含运行时才加载的客户 ext 组件。",
            "jar / class 本体不入 git；本件为复算产物。",
            "动态通道的「当前有无活对象」在本窗口不可证：pod 日志仅保留约 2 小时，且 /udc/** 未带会话一律返回 BOOT_1006（负控同响应）⇒ BOOT_1006 不是路由存在性/可用性判据。",
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='全部署域注解路由 op 面 / 余量裁定（离线只读）')
    ap.add_argument('--class-dir', required=True,
                    help='已解包 class 根（第一级目录名 = 构件名）')
    ap.add_argument('--app-name', default='udc',
                    help='Apps.getAppName() 取值（本部署实测 = udc）')
    ap.add_argument('--emit', default=None)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)

    cdir = Path(a.class_dir)
    if not cdir.is_dir():
        print(json.dumps({'error': 'class-dir 不存在', 'class_dir': str(cdir)},
                         ensure_ascii=False))
        return 2

    _p, _files, _ = build_domain(cdir)
    conflicts = dup_route_conflicts(cdir, _p, _files)
    payload = build_payload(cdir, a.app_name, conflicts)
    txt = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if a.emit:
        Path(a.emit).write_text(txt, encoding='utf-8', newline='\n')
        print('WROTE', a.emit)
    if a.json:
        print(txt)
    else:
        print('classes=%d routed=%d methods=%d distinct_op=%d jars=%d prefixed=%d' % (
            payload['class_count'], payload['classes_with_routes'],
            payload['methods'], payload['distinct_op'],
            payload['jars_contributing_ops'], payload['classes_prefixed']))
        c = payload['same_domain_control']
        print('同域对照 674  : %d/%d %s' % (c['hits'], c['contract_ops'], c['verdict']))
        r = payload['relocated_32_control']
        print('同域对照 rel32: %d/%d %s' % (r['hits'], r['total'], r['verdict']))
        print('余 60 命中    : %d/%d' % (payload['target_60']['hits'],
                                          payload['target_60']['total']))
        print('超集检验(routed 但无 bind/annotation): %d'
              % len(payload['routed_without_bind_annotation']))
        for k, v in payload['robustness_variants'].items():
            print('  稳健性[%s]: 674 %d  rel32 %d  余60 %d' % (
                k, v['same_domain_control_hits'], v['relocated_32_hits'],
                v['remaining_60_hits']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
