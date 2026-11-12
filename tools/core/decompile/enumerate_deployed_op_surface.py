# -*- coding: utf-8 -*-
"""部署态 udc-*.jar 域 —— op 面枚举 / 余量裁定器（离线只读）。

**要回答的问题**（PROGRESS 遗留）：余 60 条 `udc*` 未归位 op，在**部署态**（pod
`BOOT-INF/lib`，含 11 个本地 Artifactory 缺失的 udc 构件）是否承接？

**方法**：对指定目录下的 `udc-*.jar` 逐 class **直读 .class 常量池**
（复用 `tools/enumerate_class_http_mappings.py`，不经 javap/CFR，故免疫文本视图截断），
按 `components/udc/graphql_op_naming.path_to_op` 复算 op 名。

**为何必须带「同域对照」**：单看「余 60 条 0 命中」无法区分「真不承接」与「扫描器空转」。
故本器强制给出对照 —— **udc-web 674 契约 op 面必须全落本域**（674/674）。
注意对照**必须同域**：跨域拿 sandbox 族（属 `boot-starter-sandbox`，不在 22 个 udc jar 内）
当阳性对照会得到 5/32 的**假阴性**，是上一轮的口径错用。

用法（jar 需先从 pod 取出，见 docs/audit/udc-semantics/DEPLOYED-LIB-INVENTORY.json）：
    uv run --no-project python tools/enumerate_deployed_op_surface.py \
        --lib-dir <HERMES_HOME>/cache/scratch/djars --emit <out.json>
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UNLOCATED = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'frontend-udc-unlocated.json'
CONTRACT = (ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-web-5.3.517-contracts'
            / '_api_full.json')


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def enumerate_domain(lib_dir: Path) -> tuple[dict, dict, set]:
    ecm = _load('ecm', ROOT / 'tools' / 'core' / 'enumerate_class_http_mappings.py')
    gql = _load('gql', ROOT / 'components' / 'udc' / 'graphql_op_naming.py')
    ops_by_jar: dict[str, set] = {}
    stats: dict[str, list] = {}
    allops: set = set()
    tmp = lib_dir / '_scratch_class.bin'
    for j in sorted(lib_dir.glob('udc-*.jar')):
        got, cls, meth = set(), 0, 0
        with zipfile.ZipFile(j) as z:
            for n in z.namelist():
                if not n.endswith('.class'):
                    continue
                tmp.write_bytes(z.read(n))
                try:
                    p = ecm.parse_class_file(tmp)
                except Exception:
                    continue
                if not p['methods'] and not p['class_mapping']:
                    continue
                cls += 1
                base = (p['class_mapping'] or '').strip('/')
                for m in p['methods']:
                    meth += 1
                    for http, frags, _ in m['routes']:
                        frag = (frags[0] if frags else '').lstrip('/')
                        full = '/' + '/'.join(x for x in (base, frag) if x)
                        got.add(gql.path_to_op(full, http if http != 'ANY' else 'GET'))
        if got:
            ops_by_jar[j.name] = got
            allops |= got
            stats[j.name] = [cls, meth]
    if tmp.exists():
        tmp.unlink()
    return stats, ops_by_jar, allops


def contract_ops() -> set:
    gql = _load('gql', ROOT / 'components' / 'udc' / 'graphql_op_naming.py')
    data = json.loads(CONTRACT.read_text(encoding='utf-8'))
    out = set()
    for body in data.values():
        for m in body.get('methods', []):
            if m.get('full_path'):
                out.add(gql.path_to_op(m['full_path'], m.get('http', 'POST')))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='部署态 udc-*.jar 域 op 面 / 余量裁定（离线只读）')
    ap.add_argument('--lib-dir', required=True, help='已从 pod 取出的 udc-*.jar 目录')
    ap.add_argument('--emit', default=None)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)

    lib = Path(a.lib_dir)
    if not lib.is_dir():
        print(json.dumps({'error': 'lib-dir 不存在', 'lib_dir': str(lib)}, ensure_ascii=False))
        return 2

    stats, ops_by_jar, allops = enumerate_domain(lib)
    cops = contract_ops()
    un = json.loads(UNLOCATED.read_text(encoding='utf-8'))
    rem = un['remaining_ops']
    payload = {
        'schema': 'deployed-op-surface.v1',
        'evidence': 'LIVE-DEPLOYED jar (pod BOOT-INF/lib) + VERIFIED_STATIC_BYTECODE',
        'domain': f'部署态 {len(stats)} 个 udc-*.jar',
        'domain_scope_note': '本件只裁 udc-*.jar 域；boot-starter-* 等其余 jar 未纳入',
        'classes': sum(v[0] for v in stats.values()),
        'methods': sum(v[1] for v in stats.values()),
        'distinct_op': len(allops),
        'per_jar': {k: {'classes': v[0], 'methods': v[1], 'ops': len(ops_by_jar[k])}
                    for k, v in stats.items()},
        'same_domain_control': {
            'what': 'udc-web 674 契约 op 面在同域 op 集内的命中数',
            'contract_ops': len(cops), 'hits': len(cops & allops),
            'verdict': 'PASS' if cops <= allops else 'FAIL',
            'why': '同域对照才成立：契约 op 必须全落本域，否则 0 命中不可信',
        },
        'target_60': {'hits': sum(1 for o in rem if o in allops), 'total': len(rem),
                      'verdict': '0 命中 ⇒ 本域内确不承接（强负面）'},
        'relocated_32_in_this_domain': {
            'hits': sorted(o for o in un['relocated_ops'] if o in allops),
            'hit_count': sum(1 for o in un['relocated_ops'] if o in allops),
            'explanation': '其余归位到 boot-starter-sandbox(22) 及本域外构件，故不在本域；'
                           '跨域当阳性对照会得假阴性（上一轮口径错用，已更正）',
        },
        'limitations': ['本域仅 udc-*.jar；跨域结论需另立域复算',
                        'jar 本体不入 git'],
    }
    txt = json.dumps(payload, ensure_ascii=False, indent=1) + '\n'
    if a.emit:
        # 换行显式固定为 CRLF：此前靠 Windows 文本模式隐式转换，
        # 复算字节随宿主平台变化（Linux 出 LF）⇒ 不是可移植契约。
        Path(a.emit).write_text(txt, encoding='utf-8', newline='\r\n')
        print('WROTE', a.emit)
    if a.json:
        print(txt)
    else:
        print(f"域内 jar={len(stats)} class={payload['classes']} "
              f"method={payload['methods']} distinct_op={payload['distinct_op']}")
        c = payload['same_domain_control']
        print(f"同域对照: {c['hits']}/{c['contract_ops']} {c['verdict']}")
        print(f"余 60 命中: {payload['target_60']['hits']}/{len(rem)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
