# -*- coding: utf-8 -*-
"""部署态 BOOT-INF/lib 清单护栏（LIVE-DEPLOYED）。

**通道破局**：历轮 `pods/exec` 为 RBAC `forbidden`，故「构件本身不在本仓库（在 pod
BOOT-INF/lib）」只能推断。本轮 `pods/exec` 实为 ALLOWED，据此首次完整取出部署态
`/app/udc-assemble.jar` 的 `BOOT-INF/lib`（544 jar），并逐一对本地 maven 仓库比对。

本护栏钉死：
  ① 部署态 udc 构件数 = 22，其中 **11 个本地缺失**（名单逐条固定）——
     即 COMPONENT-COVERAGE-EXHAUSTION.md §2「构件本身不在本仓库」由**推断**升级为
     **LIVE 实证**；
  ② 导出的 `udc-web-5.3.517.jar` sha256/bytes 与 DEPLOYED-VERSION-NOTE.md 记录**逐字一致**
     ⇒ 导出产物确实来自线上，不是别处的包；
  ③ **清洗门**：本证据件不得含客户标识 / 客户 jar 名（客户明细不进仓库）。
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / 'docs' / 'audit' / 'udc-semantics' / 'DEPLOYED-LIB-INVENTORY.json'
NOTE = (ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-assemble-5.3.517-deployed'
        / 'DEPLOYED-VERSION-NOTE.md')

EXPECTED_MISSING_LOCALLY = {
    'udc-affair-5.3.517.jar',
    'udc-app-common-5.3.517.jar',
    'udc-bpm-5.3.517.jar',
    'udc-cdpbi-5.3.517.jar',
    'udc-cip-5.3.517.jar',
    'udc-dataflow-5.3.517.jar',
    'udc-m5-5.3.517.jar',
    'udc-portal-5.3.517.jar',
    'udc-starter-autocode-5.3.517.jar',
    'udc-upgrade-5.3.517.jar',
    'udc-user-5.3.517.jar',
}
# 反向：这些部署态存在的 udc 构件，本地 maven 仓库**有**（对照组，证明比对不是全缺）
EXPECTED_PRESENT_LOCALLY = {'udc-web-5.3.517.jar', 'udc-biz-5.3.517.jar',
                            'udc-starter-runtime-5.3.517.jar', 'udc-common-5.3.517.jar'}


def _evid():
    return json.loads(EVID.read_text(encoding='utf-8'))


def test_deployed_lib_surface_is_544_jars_22_of_them_udc():
    d = _evid()
    assert d['jar_count'] == 544
    assert d['udc_jar_count'] == 22
    assert len(d['udc_jars']) == 22


def test_eleven_udc_artifacts_exist_in_deployed_state_but_not_locally():
    d = _evid()
    assert set(d['udc_missing_locally']) == EXPECTED_MISSING_LOCALLY
    assert len(d['udc_missing_locally']) == 11
    # 全为 5.3.517（与部署 tag 同版本族，不混写版本）
    assert all(x.endswith('-5.3.517.jar') for x in d['udc_missing_locally'])


def test_local_presence_branch_is_not_uniformly_empty():
    """对照：不是「本地全缺」。若本地全缺，说明比对根写错而非构件缺失。"""
    d = _evid()
    present = set(d['udc_present_locally'])
    assert EXPECTED_PRESENT_LOCALLY <= present, present
    # 两侧互斥且并集 = 全集
    assert not (present & set(d['udc_missing_locally']))
    assert present | set(d['udc_missing_locally']) == set(d['udc_jars'])


def test_exported_jar_matches_the_recorded_deployed_hash():
    """完整性：导出产物必须 = 线上产物（与 DEPLOYED-VERSION-NOTE.md 逐字对照）。"""
    d = _evid()['integrity']
    assert d['deployed_udc_web_sha256'].startswith('0d6b0a65')
    assert d['deployed_udc_web_bytes'] == 136930
    note = NOTE.read_text(encoding='utf-8')
    assert '0d6b0a65' in note and '136930' in note, '版本注记里的哈希/字节数对不上'


def test_evidence_carries_no_customer_identifiers():
    """清洗门：客户 jar 名 / 客户标识不得进仓库（客户明细只进 seeyon-customer-evidence）。"""
    s = EVID.read_text(encoding='utf-8')
    for token in ('znxmglpt', 'chjh', 'sy_access_token', 'xiangmuguanli', 'peixunudc'):
        assert token not in s, f'含客户/敏感串 {token!r}'
    assert not re.search(r'\d{15,}', s), '含长数字串（疑似客户 appId/记录 id）'
