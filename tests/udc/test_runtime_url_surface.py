# -*- coding: utf-8 -*-
"""运行期 URL 面（LIVE pods/log）护栏（2026-10-15 第九轮）。

本轮把第八轮的 pod 日志通道从**单 pod 扩到全 namespace 32 个 running pod**，
并对 udc pod 另取 250k 行单窗做**同线程 URL->biz 方法关联**，
首次把「平台操作面」的**实际被调用轴**与 674 端点契约逐模板对账。

两个发现
A. /udc 前缀下存在 **udc-web 之外**的 REST 提供者：
   同线程 request url:/udc/metadata/app-service-by-name ->
   MetadataQueryAppService#selectAppServiceMetadataByFullName；
   单窗计数 /udc/metadata/ = 20 vs /udc/design-metadata/ = 0（契约登记的那条没人调）；
   提供者字节码 = docs/audit/artifacts/metadata-5.3.358/MetadataController.class
   （父类 BaseComponentController、类路径字面 metadata、方法字面 app-service-by-name）。
   => 674 契约是单构件视图。
B. 两条「被调用但契约没有」的路由：
   select-by-appid（语义正确、字面不存在 => 同线程无 biz 行 = 无实现；
   契约里同方法字面是 select-by-type，平台源码复制粘贴瑕疵）与
   search-list（UNVERIFIED：部署版本可能 != 5.3.517 / 另一构件 / 死路径）。

本文件钉死（任何一条被改动都必须显式改这里 + 重跑）
1. 面切分与计数（271 控制面 / 150 运行期 / 421 distinct / 1407 URL 行）；
2. 模板级对账 14 EXACT_T + 4 MISS_T = 18，且 MISS_T 字面集合精确固定；
3. 与 674 契约的反向断言（哪些字面必须在契约、哪些必须在契约外）——防证据件腐化；
4. 提供者字节码断言（ctp metadata 类不是 udc-web 类）；
5. 清洗门：数据件非 source 子树不得出现 6 位以上数字串（客户 id / pod 名一律不落盘）；
6. 运行期家族骨架集合固定（23 个模板，两个路由根互不重叠）。
"""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SEM = REPO / 'docs/audit/udc-semantics'
ART = SEM / 'RUNTIME-URL-SURFACE.json'
CONTRACT = REPO / 'docs/audit/artifacts/udc-web-5.3.517-contracts/_api_full.json'
META_CLASS = REPO / 'docs/audit/artifacts/metadata-5.3.358/MetadataController.class'
DOC = SEM / 'RUNTIME-URL-SURFACE.md'

MISS_T_EXPECTED = {
    '/udc/graphql',
    '/udc/metadata/app-service-by-name',
    '/udc/micro-flow-group/search-list',
    '/udc/micro-flow-group/select-by-appid/{arg}',
}
MFG_CONTRACT_METHODS = ('create', 'update', 'batchMove', 'deleteById',
                        'deleteBatchGroupAndContent', 'selectById', 'selectByAppId')
RUNTIME_FAMILIES_CORE = {
    '/{appId}/udc-runtime/app-draft/create',
    '/{appId}/udc-runtime/app-draft/exist',
    '/{appId}/udc-runtime/app-draft/select',
    '/{appId}/udc-runtime/app-log/create-batch',
    '/{appId}/udc-runtime/meta-data/refer-and-metadata',
    '/{appId}/udc-runtime/meta-data/select-host-and-only-page-pages',
    '/{appId}/graphql',
    '/{appId}/file/details',
    '/{appId}/enum-item/search-by-enum-codes',
    '/{appId}/ctp-parameter/values',
    '/{appId}/{key}/microflow/{key}',
    '/{appId}/{key}/microflow/getProgressByPlan',
    '/{appId}/{key}/filter-plan/{key}/{key}/{id}',
    '/{appId}/{key}/refer/{key}/{key}/{id}',
    '/{appId}/{key}/refer/{key}/{key}/{id}/select-by-ids',
}


def _art():
    return json.loads(ART.read_text(encoding='utf-8'))


def _api():
    return json.loads(CONTRACT.read_text(encoding='utf-8'))


def _contract_paths():
    return [m.get('full_path') or '' for v in _api().values() for m in v['methods']]


def _full_path(cls, method):
    for m in _api()[cls]['methods']:
        if m.get('method') == method:
            return m.get('full_path')
    raise AssertionError('not in contract: %s#%s' % (cls, method))


# ---------- 1. 面切分与计数 ----------

def test_surface_counts_frozen():
    a = _art()
    assert a['source']['namespace_pods_running'] == 32
    assert a['source']['request_url_lines_total'] == 1407
    assert a['source']['distinct_raw_urls'] == 421
    assert a['control_plane']['distinct'] == 271
    assert a['app_runtime']['distinct'] == 150
    assert a['source']['pods_emitting_request_url'] == 6
    assert a['source']['pods_by_class'] == {'platform': 1, 'app_runtime': 5}


def test_two_route_roots_do_not_overlap():
    """设计态 /udc/** 与运行态 /{appId}/** 是两个互不重叠的路由根。"""
    a = _art()
    assert all(t.startswith('/udc/') for t in a['control_plane']['templates'])
    assert all(f.startswith('/{appId}/') for f in a['app_runtime']['families'])
    assert not any(f.startswith('/udc/') for f in a['app_runtime']['families'])


def test_raw_url_verdicts_sum_to_distinct():
    a = _art()
    v = a['control_plane']['verdicts_on_distinct_raw_urls']
    assert v == {'EXACT': 10, 'PARAM': 258, 'MISS': 3}
    assert sum(v.values()) == a['control_plane']['distinct']
    assert set(a['control_plane']['miss_routes']) == {
        '/udc/graphql',
        '/udc/metadata/app-service-by-name',
        '/udc/micro-flow-group/select-by-appid/{arg}',
    }


# ---------- 2. 模板级对账 ----------

def test_template_verdicts_partition_and_count():
    a = _art()
    tpls = set(a['control_plane']['templates'])
    ok = set(a['control_plane']['templates_matching_contract'])
    bad = set(a['control_plane']['templates_absent_from_contract'])
    assert len(tpls) == 18
    assert ok | bad == tpls and not (ok & bad)
    assert len(ok) == 14 and len(bad) == 4
    assert bad == MISS_T_EXPECTED
    expected = {t: ('EXACT_T' if t in ok else 'MISS_T') for t in tpls}
    assert a['control_plane']['template_verdicts'] == expected


def test_miss_templates_are_really_absent_from_contract():
    paths = set(_contract_paths())
    assert '/udc/graphql' not in paths          # 非 REST 入口，预期 MISS
    for t in ('/udc/metadata/app-service-by-name',
              '/udc/micro-flow-group/search-list',
              '/udc/micro-flow-group/select-by-appid/{appId}'):
        assert t not in paths, t


def test_matched_templates_really_exist_in_contract():
    paths = set(_contract_paths())
    for t in ('/udc/design-metadata/app-service-by-name',
              '/udc/microflow/findById/{id}',
              '/udc/micro-flow-group/select-by-type',
              '/udc/runtime/expect-deploy-time',
              '/udc/microflow/create'):
        assert t in paths, t


# ---------- 3. 发现 A：udc-web 之外的提供者 ----------

def test_finding_a_live_facts_frozen():
    a = _art()
    f = a['findings']['A_non_udc_web_provider_under_udc_prefix']
    assert f['live_route'] == '/udc/metadata/app-service-by-name'
    assert f['same_thread_biz'] == 'MetadataQueryAppService#selectAppServiceMetadataByFullName'
    assert f['live_calls_in_window'] == 16 and f['same_thread_biz_calls'] == 18
    assert f['provider_class'] == 'com.seeyon.ctp.metadata.controller.MetadataController'
    assert f['provider_restapi_path'] == 'metadata'
    usage = a['control_plane']['route_family_usage_in_window']
    assert usage['/udc/metadata/'] == 20
    assert usage['/udc/design-metadata/'] == 0


def test_finding_a_provider_bytecode_is_not_udc_web():
    b = META_CLASS.read_bytes()
    assert b'com/seeyon/boot/starter/web/BaseComponentController' in b
    assert b'app-service-by-name' in b
    assert b'RestApi' in b
    assert b'MetadataQueryAppService' in b
    # 契约里同名 op 属于 udc-web 的另一个 Controller（路径 /udc/design-metadata/**）
    owner = [c for c, v in _api().items()
             if any(m.get('full_path') == '/udc/design-metadata/app-service-by-name'
                    for m in v['methods'])]
    assert owner == ['UdcDesignMetadataController']


# ---------- 4. 发现 B：被调用但无实现 / 未验证 ----------

def test_finding_b_select_by_appid_is_a_source_quirk():
    """契约里 selectByAppId 的字面被写成 select-by-type（平台源码复制粘贴瑕疵）。"""
    assert _full_path('MicroFlowGroupController', 'selectByAppId') == '/udc/micro-flow-group/select-by-type'
    joined = ' '.join(_full_path('MicroFlowGroupController', m) for m in MFG_CONTRACT_METHODS)
    assert 'select-by-appid' not in joined
    assert 'search-list' not in joined


def test_finding_b_no_same_thread_biz_and_sibling_route():
    a = _art()
    b = a['findings']['B_called_but_unimplemented_route']
    assert 'NONE' in b['same_thread_followup_biz']
    assert b['live_calls_in_window'] == 1
    assert b['live_route_shape'] == '/udc/micro-flow-group/select-by-appid/{appId}'
    sib = b['sibling_contract_absent_route']
    assert sib['live_route'] == '/udc/micro-flow-group/search-list'
    assert sib['in_contract'] is False
    assert len(sib['same_prefix_contract_routes']) == 7
    assert 'UNVERIFIED' in sib['status']


# ---------- 5. 运行期家族骨架 ----------

def test_runtime_families_core_frozen_and_clean():
    a = _art()
    fams = set(a['app_runtime']['families'])
    assert len(fams) == 23
    assert RUNTIME_FAMILIES_CORE <= fams
    assert not [f for f in fams if re.search(r'\d', f)]
    covered = set()
    for v in a['app_runtime']['family_classes'].values():
        covered |= set(v)
    assert covered == fams
    assert len(a['app_runtime']['family_classes']['udc_runtime']) == 7


# ---------- 6. 清洗门（客户业务明细 / pod 名不入库） ----------

def _walk(o, path=''):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _walk(v, path + '/' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk(v, path + '/' + str(i))
    elif isinstance(o, str):
        yield path, o


def test_artifact_has_no_customer_ids_or_pod_names():
    a = _art()
    body = {k: v for k, v in a.items() if k != 'source'}   # source 只放聚合计数
    bad = [(p, s) for p, s in _walk(body) if re.search(r'\d{6,}', s)]
    assert not bad, bad[:3]
    txt = ART.read_text(encoding='utf-8')
    for banned in ('vb2tx', 'xiangmuguanli', 'yunyewu', 'znxmglpt', 'udc-7cbfc587f5'):
        assert banned not in txt, banned


def test_doc_exists_and_records_limitations():
    t = DOC.read_text(encoding='utf-8')
    assert '不含 HTTP 状态码' in t
    assert 'EXACT_T' in t and 'MISS_T' in t
    assert 'select-by-appid' in t and 'app-service-by-name' in t
    assert 'UNVERIFIED' in t
    assert 'BaseComponentController' in t
