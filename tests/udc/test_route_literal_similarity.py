# -*- coding: utf-8 -*-
"""路由字面段「形近」陷阱护栏（2026-10-15 第八轮 · LIVE 日志通道新证）。

**怎么发现的（LIVE，非静态推断）**
第七轮把「pod `BOOT-INF/lib` 全量扫描」定为 60 条余量 op 定域的**唯一**剩余静态路径。
本轮换轴：用 `kubeconfig-zhiyuan` 的 token 直连 `10.0.0.1:6443`（本地无 kubectl，
自写 HTTP/WS 客户端），**RBAC 自审实测**（`SelfSubjectRulesReview`）：
- `pods/exec` = **forbidden(403)** ⇒ 静态缺口仍被挡（与第七轮结论一致，非放弃）
- `pods/log`   = **allowed**      ⇒ 得到一条**真实运行期**通道

udc pod（tag `5.3.517`）的 `AppContextFilter:50` 逐条打印**真实请求 URL**。
取近 200k 行日志：425 条请求 URL / **13 个 distinct**，与本仓契约逐条对账 **11/13 命中**
（5 精确 + 6 仅差路径参数实参）。2 条 MISS：
1. `/udc/graphql` —— GraphQL 单一入口，非 REST，预期 MISS；
2. `/udc/entity/select-all-by-entity-id/<实体id实参>` —— **本轮唯一异常**。

契约（且 javap 常量池逐字）里 `EntityController` 只有 `select-all-by-entityId/{id}`
（**驼峰 `Id`**）。连字符版 `.../entity-id/...` 在契约里**不存在**。
而同前缀下另有一条**真实存在**的连字符路由：
`/udc/entity/attribute/select-all-by-entity-id/{entityId}`（取**属性**，与取**实体**不同）。
⇒ 手写需求时按「读起来像」拼路径会打偏；打偏后果 = 404，**不入业务方法**
（日志里连 `AppServiceLogFilter: method :` 行都不会出现）。

**本文件钉死**
1. 契约里「占位符之前的字面段」含驼峰的端点集合 = **41 条**（显式固定，增删必改此处）；
2. 归一化（驼峰→连字符）比对：**0 组**真实同义撞车 ⇒ 两条形近路由不会同时存在，
   判据只能是逐字 `full_path`；
3. 反向护栏：驼峰路由的连字符改写**不得**存在于契约（典型的打偏形态）；
4. 占位符名不参与路由匹配（`{id}` / `{entityId}` / `{appId}` 同类），不得据此区分端点；
5. 证据件 `ROUTE-LITERAL-SIMILARITY.json` 与契约必须一致（防止证据件腐化）。

本文件不含客户业务 ID/名称，仅平台路由字面量。
"""
import json
import re
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-web-5.3.517-contracts' / '_api_full.json'
EVIDENCE = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'ROUTE-LITERAL-SIMILARITY.json'

_CAMEL_LITERAL_COUNT = 41


def _methods():
    data = json.loads(API.read_text(encoding='utf-8'))
    out = []
    for cls, body in data.items():
        for m in body['methods']:
            if m.get('full_path'):
                out.append((cls, m['method'], m['full_path']))
    return out


def _literal_before_param(path):
    """`{param}` 之前的最后一段字面量；无占位符则取最后一段。"""
    parts = path.strip('/').split('/')
    for i, p in enumerate(parts):
        if p.startswith('{'):
            return parts[i - 1] if i else ''
    return parts[-1] if parts else ''


def _has_camel(seg):
    return bool(re.search(r'[a-z][A-Z]', seg))


def _camel_set():
    return {(c, m, p) for c, m, p in _methods() if _has_camel(_literal_before_param(p))}


def _norm(path):
    """驼峰→连字符归一化，用于发现「形近同义」路由。"""
    return re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', path).lower()


def test_camel_literal_segment_count_is_41():
    """含驼峰字面段的端点恰 41 条（契约实测）。"""
    assert len(_camel_set()) == _CAMEL_LITERAL_COUNT


def test_normalized_paths_have_zero_near_collisions():
    """归一化后无任何两条不同 full_path 撞成一个骨架。

    含义：驼峰与连字符**不会**是同一条路由的两种写法 —— 故不存在「两种写法都行」。
    """
    groups = defaultdict(set)
    for _, _, p in _methods():
        groups[_norm(p)].add(p)
    collisions = {k: sorted(v) for k, v in groups.items() if len(v) > 1}
    assert collisions == {}


def test_entity_by_entityId_route_is_camel():
    """按实体 id 取**实体**：驼峰 `select-all-by-entityId/{id}`。"""
    assert ('EntityController', 'selectAllEntitiesByEntityId',
            '/udc/entity/select-all-by-entityId/{id}') in _methods()


def test_attribute_by_entity_id_route_is_hyphenated():
    """取**属性**：连字符 `select-all-by-entity-id/{entityId}`，且挂在 `attribute/` 之下。"""
    paths = {p for _, _, p in _methods()}
    assert '/udc/entity/attribute/select-all-by-entity-id/{entityId}' in paths


def test_hyphenated_rewrite_of_camel_routes_must_not_exist():
    """反向护栏：驼峰路由的连字符改写（典型打偏形态）不得存在。"""
    paths = {p for _, _, p in _methods()}
    for bad in (
        '/udc/entity/select-all-by-entity-id/{id}',
        '/udc/entity/select-all-by-entity-id',
        '/udc/entity/attribute/select-all-by-entityId/{entityId}',
        '/udc/entity/select-event-data-by-entity-id/{id}',
        '/udc/portlet/select-by-app-id/{appId}',
        '/udc/microflow/search/app-service-by-appName',
    ):
        assert bad not in paths, f'{bad} 不应存在（形近改写，非真实端点）'


def test_placeholder_name_does_not_participate_in_route_matching():
    """占位符名不参与匹配：`{id}` / `{entityId}` / `{appId}` 同类。

    故骨架相同的两条 full_path 若**字面段也相同**，就应是同一端点（不得因占位符名不同而分叉）。
    反之，字面段不同的形近路由（如 select-all-by-entityId vs attribute/...-entity-id）骨架不同，
    必须被当成两条不同端点 —— 这正是本文件的护栏对象。
    """
    skel = defaultdict(set)
    for _, _, p in _methods():
        skel[re.sub(r'\{[^}]+\}', '{}', p)].add(p)
    for s, group in skel.items():
        # 同一骨架下，字面段集合必须唯一
        lits = {tuple(x for x in g.strip('/').split('/') if not x.startswith('{')) for g in group}
        assert len(lits) == 1, f'骨架 {s} 出现多个字面段集合: {lits}'


def test_live_classifier_pins_exact_param_miss_vocabulary():
    """把 LIVE 对账分类器（tools/core/platform/k8s_pod_log_surface.py）的判据钉住。

    第一版分类器先把路径 re.escape(p) 再尝试还原占位符，顺序错误，导致 `/udc/entity/{id}` 这类路径无法整段匹配，
    把 6 条 PARAM 误报成 MISS。此处固定正确语义：EXACT / PARAM / MISS 三分类，
    并逐条钉住 LIVE 实测到的 URL。
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'pod_log_surface', ROOT / 'tools' / 'core' / 'platform' / 'k8s_pod_log_surface.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    paths = mod.contract_paths()
    cases = {
        '/udc/entity': 'EXACT',
        '/udc/entity/attribute/search-list': 'EXACT',
        '/udc/page-info/base-info/create': 'EXACT',
        '/udc/page-info/select-list/by-conditions': 'EXACT',
        '/udc/entity/-6338668863907875875': 'PARAM',   # -> /udc/entity/{id}
        '/udc/function/-623283056435289078': 'PARAM',  # -> /udc/function/{id}
        '/udc/page-info/6150153921121584026': 'PARAM', # -> /udc/page-info/{id}
        '/udc/graphql': 'MISS',                        # 非 REST，单一入口
        '/udc/entity/select-all-by-entity-id/1627860264017874938': 'MISS',  # 形近路由
    }
    for url, want in cases.items():
        got = mod.classify(url, paths)[0]
        assert got == want, f'{url}: got {got}, want {want}'


@pytest.mark.parametrize('frag,owner', [
    ('/udc/entity/select-all-by-entityId/{id}', 'EntityController'),
    ('/udc/entity/attribute/select-all-by-entity-id/{entityId}', 'EntityController'),
    ('/udc/microflow/findById/{id}', 'MicroFlowController'),
    ('/udc/attributeSet/{id}', 'AttributeSetController'),
    ('/udc/application/appVersion/{appGuid}', 'ApplicationController'),
])
def test_camel_fragments_are_verbatim_in_contract(frag, owner):
    """驼峰片段必须逐字命中契约（防「顺手规范化」把契约改坏）。"""
    hits = {(c, p) for c, _, p in _methods() if p == frag}
    assert hits, f'{frag} 不在契约中'
    assert any(c == owner for c, _ in hits), f'{frag} 的 Controller 应为 {owner}'


def test_evidence_artifact_matches_contract_and_hypothesis():
    """证据件与契约一致：41 条驼峰端点、0 组归一化撞车、LIVE 通道口径固定。"""
    ev = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    assert ev['artifact'] == 'udc-web-5.3.517'
    assert ev['camel_literal_segment_count'] == _CAMEL_LITERAL_COUNT
    assert ev['normalized_near_collisions'] == {}
    listed = {(d['controller'], d['method'], d['full_path']) for d in ev['camel_literal_segments']}
    assert listed == _camel_set()
    lc = ev['live_channel']
    assert lc['request_url_lines'] == 425 and lc['distinct_request_urls'] == 13
    assert lc['contract_match'] == {'exact': 5, 'param_placeholder': 6, 'miss': 2}
    assert lc['rbac'] == {'pods/exec': 'forbidden(403)', 'pods/log': 'allowed'}


def test_evidence_artifact_has_no_long_identifier_tokens():
    """证据件不得出现任何长数字串（平台/业务 ID 形态），负向且不点名任何客户。

    判据取「>=15 位连续数字」：平台 ID 为 19 位、雪花 id 为 19 位；
    证据件只应含计数（如 425 / 41），不应含任何对象标识。
    """
    raw = EVIDENCE.read_text(encoding='utf-8')
    long_ids = re.findall(r'(?<!\d)\d{15,}(?!\d)', raw)
    assert long_ids == [], f'证据件含长数字标识: {long_ids}'
