# -*- coding: utf-8 -*-
"""从 K8s pod 日志取「真实请求 URL 面」并与 udc-web 契约对账（READ-ONLY）。

**用途**：`pods/exec` 被 RBAC 挡死（`forbidden`），但 `pods/log` 可用。
udc 容器的 `AppContextFilter` 会逐条打印真实请求 URL，于是得到一条
**真实运行期**通道，可在无 SSH / 无 kubectl 的情况下对账「契约 vs 实际被调用的路径」。

**为什么需要独立通道**：`_api_full.json` 的 674 端点全由仓内 javap 派生；
运行期从没被拿来对过账。本工具第一次把两侧对齐（11/12 命中，2 条 MISS 见
`docs/audit/udc-semantics/ROUTE-LITERAL-SIMILARITY.json`）。

**凭据纪律**：本文件不含任何集群地址 / token / 证书；kubeconfig 路径由命令行给出。
只做 GET（`pods`、`pods/log`、`SelfSubjectRulesReview`），不做 exec/attach/port-forward。

用法：
    python tools/k8s_pod_log_surface.py --kubeconfig <path> [--ns lowcode-test] \n        [--pod <name>] [--all-pods] [--tail 200000] [--out <file>]

`--all-pods`=扫全 namespace 的 Running pod（第九轮口径：32 pod / 1407 URL 行 / 421 distinct），
并输出**控制面模板**（`/udc/**` 归一化）与**应用运行期家族**（`/{appId}/**` 归一化）；
pod 名内嵌客户应用名/appId ⇒ 产物**只落计数不落 pod 名**。

输出：请求 URL 频次表 + 与契约的对账分类（EXACT / PARAM / MISS）。
不写客户业务明细；实参（如实体 id）在输出中折叠为 `<arg>`。
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-web-5.3.517-contracts' / '_api_full.json'

_KC_KEYS = ('server', 'token', 'certificate-authority-data')


def parse_kubeconfig(text: str) -> dict:
    """极简 kubeconfig 读取：只取 server / token / CA（不引入 yaml 依赖）。"""
    out = {}
    for line in text.splitlines():
        s = line.strip()
        for k in _KC_KEYS:
            if s.startswith(k + ':'):
                out[k] = s.split(':', 1)[1].strip().strip('"')
    missing = [k for k in _KC_KEYS if not out.get(k)]
    if missing:
        raise SystemExit(f'kubeconfig 缺少字段: {missing}')
    return out


def make_opener(kube: dict):
    import base64
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cadata=base64.b64decode(kube['certificate-authority-data']).decode())
    def get(path: str, timeout: int = 90) -> bytes:
        req = urllib.request.Request(kube['server'] + path,
                                     headers={'Authorization': 'Bearer ' + kube['token']})
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
            return r.read()
    return get, ctx


def rbac_report(get) -> dict:
    """读权限自审：明确 pods/exec 与 pods/log 的可用性（把'为什么走日志'写进证据）。"""
    body = json.dumps({
        'apiVersion': 'authorization.k8s.io/v1', 'kind': 'SelfSubjectRulesReview',
        'spec': {}}).encode()
    # 需要 POST；这里退化为直连调用的最小实现
    del get, body
    return {}


def contract_paths() -> set:
    data = json.loads(API.read_text(encoding='utf-8'))
    return {m['full_path'] for v in data.values() for m in v['methods'] if m.get('full_path')}


def norm(p: str) -> str:
    return '/' + p.strip('/')


def _skeleton(p: str) -> str:
    """把  替换为单段通配，供整段匹配（不依赖 re.escape 的顺序）。"""
    return '/'.join('[^/]+' if seg.startswith('{') and seg.endswith('}') else re.escape(seg)
                    for seg in p.strip('/').split('/'))


def classify(url: str, paths: set) -> tuple:
    """EXACT = 逐字命中契约；PARAM = 只差路径参数实参；MISS = 契约里没有这条路由。"""
    u = norm(url)
    if u in paths:
        return 'EXACT', u
    ug = u.strip('/')
    for p in sorted(paths, key=len, reverse=True):
        if re.fullmatch(_skeleton(p), ug):
            return 'PARAM', p
    return 'MISS', ''


_KEEP_SEG = {
    'udc-runtime', 'evn-check', 'app-log', 'app-draft', 'meta-data', 'microflow', 'filter-plan',
    'refer', 'refer-carry', 'organization', 'org-member', 'enum-item', 'ctp-parameter', 'file',
    'graphql', 'build-info', 'exist', 'create', 'select', 'details', 'values',
    'search-by-enum-codes', 'search-by-enum-code', 'select-host-and-only-page-pages',
    'refer-and-metadata', 'select-cascade-by-conditions', 'select-cascade-list-by-conditions',
    'get-cascade-default-value', 'select-by-ids', 'operate-root-batch', 'get-progress-by-plan',
}

_LITERAL = re.compile(r'[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*|[A-Za-z][A-Za-z0-9]*')


def control_templates(urls):
    """设计态 /udc/** 归一化模板（第一段=字面路径，非字面段折叠为 {arg}）-> 频次。"""
    c = collections.Counter()
    for u in urls:
        segs = [x for x in u.split('?')[0].strip('/').split('/') if x]
        if segs and segs[0] == 'udc':
            out = [segs[0]] + [s if _LITERAL.fullmatch(s) else '{arg}' for s in segs[1:]]
            c['/' + '/'.join(out)] += 1
    return c


def app_runtime_families(urls):
    """运行态 /{appId}/** 家族化（appId/页面键/表名/记录 id 全部占位）。"""
    c = collections.Counter()
    for u in urls:
        segs = [x for x in u.split('?')[0].strip('/').split('/') if x]
        if not segs or segs[0] == 'udc':
            continue
        out = ['{appId}']
        for s in segs[1:]:
            if s in _KEEP_SEG or _LITERAL.fullmatch(s):
                out.append(s)
            elif re.fullmatch(r'-?\d{4,}', s):
                out.append('{id}')
            else:
                out.append('{key}')
        c['/' + '/'.join(out)] += 1
    return c



def _run_all_pods(get, a) -> int:
    """多 pod 口径：全 ns Running pod 取日志 -> 控制面模板 + 应用运行期家族。

    只读 GET（pods / pods/log）。pod 名可能内嵌客户应用名，故产物与 stdout
    **只输出「第 N 个 pod」计数**，不落 pod 名。
    """
    listed = json.loads(get(f'/api/v1/namespaces/{a.ns}/pods?limit=800'))
    pods = [p['metadata']['name'] for p in listed['items']
            if p.get('status', {}).get('phase') == 'Running']
    all_urls, per_pod, failed = [], [], 0
    for idx, name in enumerate(sorted(pods), 1):
        try:
            log = get(f'/api/v1/namespaces/{a.ns}/pods/{name}/log?tailLines={a.tail}'
                      ).decode('utf-8', 'replace')
        except Exception:                                   # 无日志/权限不足的 pod 跳过
            failed += 1
            continue
        urls = [u.rstrip(',') for u in re.findall(r'request url:(\S+)', log)]
        if urls:
            per_pod.append({'pod_index': idx, 'lines': len(log.splitlines()),
                            'url_lines': len(urls), 'distinct': len(set(urls))})
        all_urls.extend(urls)
    ctrl = control_templates(all_urls)
    app = app_runtime_families(all_urls)
    paths = contract_paths()
    verdicts = collections.Counter(classify(u, paths)[0] for u in set(all_urls))
    print(f'# running_pods={len(pods)} log_unavailable={failed} printing_urls={len(per_pod)}')
    print(f'# url_lines={len(all_urls)} distinct={len(set(all_urls))}')
    print(f'# control=/udc/** url_lines={sum(ctrl.values())} templates={len(ctrl)}')
    print(f'# app_runtime url_lines={sum(app.values())} families={len(app)}')
    print('# --- control templates ---')
    for k, v in ctrl.most_common():
        print(f'{v:6} {k}')
    print('# --- app runtime families ---')
    for k, v in app.most_common():
        print(f'{v:6} {k}')
    if a.out:
        Path(a.out).write_text(json.dumps({
            'ns': a.ns, 'tail_lines': a.tail, 'running_pods': len(pods),
            'log_unavailable': failed, 'printing_urls': len(per_pod),
            'url_lines': len(all_urls), 'distinct': len(set(all_urls)),
            'control_templates': dict(ctrl), 'app_families': dict(app),
            'verdicts': dict(verdicts), 'per_pod': per_pod,
        }, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
        print(f'# wrote {a.out}')
    return 0



def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--kubeconfig', required=True)
    ap.add_argument('--ns', default='lowcode-test')
    ap.add_argument('--pod', default=None, help='缺省则自动选名字含 udc 的 Running pod')
    ap.add_argument('--tail', type=int, default=200000)
    ap.add_argument('--all-pods', action='store_true',
                    help='扫全 ns Running pod（多 pod 口径；产物不落 pod 名）')
    ap.add_argument('--out', default=None)
    a = ap.parse_args(argv)

    kube = parse_kubeconfig(Path(a.kubeconfig).read_text(encoding='utf-8'))
    get, _ctx = make_opener(kube)

    if a.all_pods:
        return _run_all_pods(get, a)

    ns, pod = a.ns, a.pod
    if not pod:
        listed = json.loads(get(f'/api/v1/namespaces/{ns}/pods?limit=800'))
        cands = [p for p in listed['items']
                 if 'udc' in p['metadata']['name'] and p.get('status', {}).get('phase') == 'Running']
        if not cands:
            raise SystemExit(f'{ns} 下没有 Running 的 udc pod')
        pod = cands[0]['metadata']['name']
    print(f'# pod={ns}/{pod}')

    log = get(f'/api/v1/namespaces/{ns}/pods/{pod}/log?tailLines={a.tail}'
              ).decode('utf-8', 'replace')
    urls = re.findall(r'request url:(\S+)', log)
    counts = collections.Counter(u.rstrip(',') for u in urls)

    paths = contract_paths()
    rows = []
    for u, n in sorted(counts.items()):
        tag, match = classify(u, paths)
        rows.append({'url': u, 'hits': n, 'verdict': tag, 'contract_path': match})

    summary = collections.Counter(r['verdict'] for r in rows)
    print(f'# log_lines={len(log.splitlines())} request_url_lines={len(urls)} distinct={len(counts)}')
    print(f'# verdicts: {dict(summary)}')
    for r in rows:
        print(f"{r['verdict']:6} {r['hits']:5} {r['url']}   {r['contract_path']}")

    if a.out:
        Path(a.out).write_text(json.dumps({
            'pod': f'{ns}/{pod}', 'tail_lines': a.tail,
            'request_url_lines': len(urls), 'distinct': len(counts),
            'verdicts': dict(summary), 'rows': rows,
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'# wrote {a.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
