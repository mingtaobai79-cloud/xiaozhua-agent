"""udc-web 持久化契约的方法级缺陷护栏（字节码直读，不依赖提取器）。



背景与证据：docs/audit/udc-semantics/COMPONENT-RELOCATION.md 第 2 节。

GROUND TRUTH = docs/audit/artifacts/udc-web-5.3.517-javap/*.javap.txt（javap -v 原文，GBK），

不是 tools/core/decompile/extract_udc_web_methods.py 的产物 —— 故提取器改坏时本测试仍能独立报警。



2026-10-15 第二轮：四类缺陷**已全部修复**，本文件由「已知缺陷钉桩」（修好即失败）

翻转为「修复态钉桩」（再坏即失败）：

  A 提取器以方法名为 key -> 同名重载被静默丢弃（14 组 / 15 实例）；

  B 注解块取值越界 -> 裸 mapping 之后的中文描述被当路径（污染 2 条）；

  C 无 mapping 方法被兜底为方法名路径 -> 幻影 1 条（ApplicationController.saveAsTemplate）；

  D 声明门只认 public/protected -> 漏掉 package-private 处理器 3 条（3 个 Controller 各 1）。



净效应：657 -> **674** 端点（+15 恢复重载 +3 包级 -1 幻影 ... 见 test_total_endpoints_is_674）。

口径（2026-10-15 第三轮收口）：**674 = 方法级 mapping 端点**（含 ParameterController 的 6 条）；

**derive_ops 产出的 distinct op = 673** —— ParameterController.create 的 full_path 为 "/"

（裸 mapping 且类级无前缀），strip("/") 后为空被 derive_ops 跳过。差 1 条，已有测试钉桩。



实现上刻意不用正则（避免转义），全部用字符串切分。

"""

import json

from pathlib import Path



import pytest



from components.udc.graphql_op_naming import derive_ops



ROOT = Path(__file__).resolve().parents[2]

_JAVAP = ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-web-5.3.517-javap'

_API = (ROOT / 'docs' / 'audit' / 'artifacts' / 'udc-web-5.3.517-contracts'

        / '_api_full.json')



pytestmark = pytest.mark.skipif(

    not (_JAVAP.is_dir() and _API.exists()),

    reason='udc-web javap/契约件缺失')



Q = chr(34)

_NL = chr(10)

_SIG = _NL + '  public '

_HTTP_ANN = ('PostMapping', 'GetMapping', 'PutMapping', 'DeleteMapping', 'PatchMapping')







def _javap_src(name):

    """javap -v 原文（GBK 解码），剥 CR。"""

    raw = (_JAVAP / (name + '.javap.txt')).read_bytes()

    return raw.decode('gbk', errors='replace').replace(chr(13), '')





def _api():

    return json.loads(_API.read_text(encoding='utf-8'))





def _block_mapping(blk):

    """从一个方法的注解区取 (http, [mapping value...])；无 mapping 返回 (None, [])。



    关键：裸注解 `annotation.PostMapping` 后**不跟** `(` -> 路径为空字符串。

    这正是缺陷 B 的判定点（旧提取器会把其后 RestApiOperation 的中文当路径）。

    """

    for a in _HTTP_ANN:

        i = blk.find('annotation.' + a)

        if i < 0:

            continue

        http = a[:-7].upper()

        j = i + len('annotation.') + len(a)

        if blk[j:j + 1] != '(':

            return http, ['']

        k = blk.find('value=', j)

        if k < 0:

            return http, ['']

        k += len('value=')

        if blk[k:k + 1] == '[':

            end = blk.find(']', k)

            inner = blk[k + 1:end]

            return http, [x for x in inner.split(Q) if x and x != ',']

        if blk[k:k + 1] == Q:

            end = blk.find(Q, k + 1)

            return http, [blk[k + 1:end]]

        return http, ['']

    return None, []





def _method_blocks(text):

    """按方法属性区切块 -> [(方法名, http, [mapping value...]), ...]。



    覆盖**任意访问级**（缺陷 D：package-private 处理器同样被 Spring 映射）。

    """

    out = []

    digs = [i for i, ln in enumerate(text.split(_NL))

            if ln.startswith('  ') and not ln.startswith('   ')

            and ln.strip().endswith(';') and '(' in ln]

    lines = text.split(_NL)

    starts = []

    for i in range(len(lines) - 1):

        ln = lines[i]

        if not ln.startswith('  ') or ln.startswith('   '):

            continue

        s = ln.strip()

        if not s.endswith(';') or '(' not in s:

            continue

        if not lines[i + 1].strip().startswith('descriptor:'):

            continue

        starts.append(i)

    for k, i in enumerate(starts):

        s = lines[i].strip()

        head = s.split('(')[0]

        name = head.split()[-1]

        end = starts[k + 1] if k + 1 < len(starts) else len(lines)

        blk = _NL.join(lines[i:end])

        blk = blk.split('RuntimeVisibleParameterAnnotations')[0]

        http, vals = _block_mapping(blk)

        out.append((name, http, vals))

    return out





def _declared_methods(text):

    """方法声明名（含重载，按出现顺序）。"""

    return [b[0] for b in _method_blocks(text)]





def _mapping_stats(text):

    """mapping 注解出现次数：裸（无括号） / 带 value。"""

    bare = valued = 0

    for a in _HTTP_ANN:

        bare += text.count('annotation.' + a + _NL)

        valued += text.count('annotation.' + a + '(' + _NL)

    return {'bare': bare, 'valued': valued}





_TOTAL_ENDPOINTS = 674

_BARE_MAPPINGS = 14



# (Controller, 方法名, 重载数, javap 中该重载组的 mapping value 全集)

_OVERLOADS = [

    ('ApplicationController', 'create', 3,

     {'', 'create-page-app', 'create-layout-app'}),

    ('ApplicationController', 'downloadFormAppPackage', 2,

     {'schema/form/download/batch/{fileNum}/{timeStamp}',

      'schema/form/download/by-app-ids'}),

    ('ApplicationController', 'importAppSchema', 2, {'/import', '/import/new'}),

    ('AttachmentTemplateController', 'delete', 2,

     {'/delete/{guid}', '/delete-by-guids'}),

    ('BackendComponentController', 'selectAppPageByConditions', 2,

     {'/search', '/search/app'}),

    ('EntityController', 'selectEntityAttributeGroupList', 2,

     {'attribute-group/search', 'attribute-group/bath-update'}),

    ('MetaDataController', 'mergeReferMetaData', 2,

     {'merge-refer', 'merge-refer-by-map'}),

    ('MetaDataController', 'selectEntityMetaDataByAppId', 2,

     {'select-app-by-id', 'select-entity-by-app-id/{appId}'}),

    ('MetaDataController', 'selectAggEntityIncludeAssociation', 2,

     {'select-aggregation-entity', 'select-aggregation-entity/{entityId}'}),

    ('MetaDataController', 'selectCtpEnumMetaDataListData1', 2,

     {'select-ctp-enum-by-app1', 'select-ctp-enum/{appId}'}),

    ('MicroFlowController', 'selectPageByCondition', 2, {'search', 'search-no-page'}),

    ('MicroFlowUpgradeController', 'thirdEntity', 2,

     {'thirdEntity/{appId}', 'thirdEntity/{appId}/{serviceName}'}),

    ('PageTemplateController', 'deleteById', 2, {'delete-by-id', 'delete-by-ids'}),

    ('PageTemplatePublishedController', 'deleteById', 2,

     {'delete-by-id', 'delete-by-ids'}),

]



# 缺陷 D：package-private 方法（无访问修饰符）但带 mapping —— 旧声明门漏掉的 3 条。

_PACKAGE_PRIVATE = [

    ('DataTransferObjectController', 'searchSelectableDtoList', 'search-selectable-list', 'POST'),

    ('EventController', 'selectWithEventData', 'select-with-data/{id}', 'GET'),

    ('MicroFlowUpgradeController', 'upgradeEntityEventFullName', 'upgrade/entity-event-full-name/{appId}', 'GET'),

]



# 无 mapping 的**非端点**方法（不得进契约；旧版曾被兜底成幻影端点）

_NON_ENDPOINTS = [

    ('ApplicationController', 'saveAsTemplate'),

    ('UdcManagerController', 'getTaskRateLimiter'),

]





# ---------------------------------------------------------------- 契约总量与缺陷面基线

def test_total_endpoints_is_674_and_matches_bytecode():

    """契约总量 674 = javap 内 mapping 注解实例数（逐方法块独立计数）。"""

    n = 0

    for pth in sorted(_JAVAP.glob('*.javap.txt')):

        txt = pth.read_bytes().decode('gbk', errors='replace').replace(chr(13), '')

        blocks = _method_blocks(txt)

        cls = pth.name.replace('.javap.txt', '')

        n += sum(1 for nm, http, vs in blocks if http)

    assert n == _TOTAL_ENDPOINTS, n

    d = _api()

    assert sum(v['api_count'] for v in d.values()) == _TOTAL_ENDPOINTS





def test_no_controller_is_over_or_under_counted():

    """逐 Controller：契约 api_count == javap 内带 mapping 的方法块数（无 net 抵消）。"""

    d = _api()

    for pth in sorted(_JAVAP.glob('*.javap.txt')):

        cls = pth.name.replace('.javap.txt', '')

        txt = pth.read_bytes().decode('gbk', errors='replace').replace(chr(13), '')

        n = sum(1 for nm, http, vs in _method_blocks(txt) if http)

        assert d[cls]['api_count'] == n, (cls, d[cls]['api_count'], n)





def test_bare_mapping_population_pinned():

    """裸 mapping（无 value）存在但占少数 —— 缺陷 B 的攻击面。"""

    bare = valued = 0

    for pth in sorted(_JAVAP.glob('*.javap.txt')):

        s = _mapping_stats(pth.read_bytes().decode('gbk', errors='replace')

                           .replace(chr(13), ''))

        bare += s['bare']

        valued += s['valued']

    assert bare == _BARE_MAPPINGS, '裸 mapping 面变化 -> 缺陷 B 需重评' + str(bare)

    assert valued >= 600, valued





def test_no_cjk_description_leaks_into_paths():

    """缺陷 B 已修：契约里不得有任何中文路径（描述不得被当路径）。"""

    bad = sorted((c, m['method'], m.get('path'))

                 for c, info in _api().items() for m in info['methods']

                 if any(chr(0x4e00) <= ch <= chr(0x9fff)

                        for ch in str(m.get('path') or '')))

    assert bad == [], bad





def test_no_phantom_endpoint_without_http_verb():

    """缺陷 C 已修：契约里不得有无 HTTP 动词的条目。"""

    bad = sorted((c, m['method']) for c, info in _api().items()

                 for m in info['methods'] if not m.get('http'))

    assert bad == [], bad





def test_non_endpoint_methods_are_absent_from_contract():

    """无 mapping 的方法不得出现在契约里（缺陷 C 的负面护栏）。"""

    d = _api()

    for ctrl, name in _NON_ENDPOINTS:

        assert not any(m['method'] == name for m in d[ctrl]['methods']), (ctrl, name)





# --------------------------------------- 缺陷 A：重载曾被静默丢弃（14 组 / 15 实例）

@pytest.mark.parametrize('ctrl,method,times,vals', _OVERLOADS)

def test_overload_group_exists_in_bytecode(ctrl, method, times, vals):

    """javap 原文证实：同名方法声明 times 次，且各自带不同的 mapping value。"""

    group = [b for b in _method_blocks(_javap_src(ctrl)) if b[0] == method]

    assert len(group) == times, (ctrl, method, len(group))

    got = {v for _n, _h, vs in group for v in vs}

    assert got == vals, (ctrl, method, got)





@pytest.mark.parametrize('ctrl,method,times,vals', _OVERLOADS)

def test_overload_group_preserved_in_persisted_contract(ctrl, method, times, vals):

    """缺陷 A 已修：重载组在契约里保留全部成员（按声明实例登记，不按方法名）。"""

    kept = [m['path'] for m in _api()[ctrl]['methods'] if m['method'] == method]

    assert len(kept) == times, (ctrl, method, kept)

    assert set(kept) == vals, (ctrl, method, set(kept))





def test_application_create_keeps_all_three_endpoints():

    """最尖锐实例：ApplicationController.create 的 3 个端点必须全在。"""

    assert _declared_methods(_javap_src('ApplicationController')).count('create') == 3

    kept = [m['full_path'] for m in _api()['ApplicationController']['methods']

            if m['method'] == 'create']

    assert sorted(kept) == ['/udc/application', '/udc/application/create-layout-app',

                              '/udc/application/create-page-app'], kept





# -------------------------------- 缺陷 D：package-private 处理器曾被丢弃

@pytest.mark.parametrize('ctrl,method,frag,http', _PACKAGE_PRIVATE)

def test_package_private_handler_exists_in_bytecode(ctrl, method, frag, http):

    """javap 证实：该方法声明**无访问修饰符**（包级），但带 mapping 注解。"""

    lines = _javap_src(ctrl).split(_NL)

    hits = []

    for i in range(len(lines) - 1):

        ln = lines[i]

        if not ln.startswith('  ') or ln.startswith('   '):

            continue

        s = ln.strip()

        if not s.endswith(';') or '(' not in s:

            continue

        if not lines[i + 1].strip().startswith('descriptor:'):

            continue

        if s.split('(')[0].split()[-1] != method:

            continue

        head = s.split('(')[0]

        assert not head.startswith(('public ', 'private ', 'protected ')), head

        hits.append(i)

    assert len(hits) == 1, (ctrl, method, hits)

    assert 'value=[' + Q + frag + Q + ']' in _javap_src(ctrl), (ctrl, frag)





@pytest.mark.parametrize('ctrl,method,frag,http', _PACKAGE_PRIVATE)

def test_package_private_handler_present_in_contract(ctrl, method, frag, http):

    """缺陷 D 已修：包级处理器同样进契约（且 HTTP 动词正确）。"""

    got = [(m['http'], m['path']) for m in _api()[ctrl]['methods']]

    assert (http, frag) in got, (ctrl, method, got)





# -------------------------------- 净效应：曾缺失的真实端点现已可在契约中推导

# (op, Controller, javap 中该 mapping 的字面量——含前导斜杠与否照录)

_RECOVERED = [

    ('udcApplicationPost', 'ApplicationController', ''),

    ('udcApplicationCreatePageAppPost', 'ApplicationController', 'create-page-app'),

    ('udcApplicationImportPost', 'ApplicationController', '/import'),

    ('udcAttachmentTemplateDeleteGuidPost', 'AttachmentTemplateController', '/delete/{guid}'),

    ('udcBackendComponentSearch', 'BackendComponentController', '/search'),

    ('udcDataTransferObjectSearchListPost', 'DataTransferObjectController', 'search-list'),

    ('udcEventListEventsPost', 'EventController', 'list/events'),

    ('udcMetaDataSelectCtpEnumByApp1Post', 'MetaDataController', 'select-ctp-enum-by-app1'),

    ('udcMicroFlowUpgradeUpgradeCallExtendAppServiceAppGet', 'MicroFlowUpgradeController',

     'upgrade/call-extend-app-service/{appId}'),

    ('udcApplicationSchemaFormDownloadBatchFileNumTimeStampGet', 'ApplicationController',

     'schema/form/download/batch/{fileNum}/{timeStamp}'),

    ('udcEntityAttributeGroupSearch', 'EntityController', 'attribute-group/search'),

    ('udcMetaDataMergeReferPost', 'MetaDataController', 'merge-refer'),

    ('udcMetaDataSelectAggregationEntityPost', 'MetaDataController', 'select-aggregation-entity'),

    ('udcMetaDataSelectAppByIdPost', 'MetaDataController', 'select-app-by-id'),

    ('udcMicroflowSearch', 'MicroFlowController', 'search'),

    ('udcMicroFlowUpgradeThirdEntityAppGet', 'MicroFlowUpgradeController', 'thirdEntity/{appId}'),

    ('udcPageTemplateDeleteByIdPost', 'PageTemplateController', 'delete-by-id'),

    ('udcPageTemplatePublishedDeleteByIdPost', 'PageTemplatePublishedController', 'delete-by-id'),

]





@pytest.mark.parametrize('op,ctrl,frag', _RECOVERED)

def test_recovered_path_attested_in_bytecode(op, ctrl, frag):

    """这些端点的路径在 javap 常量池里确实存在（是曾漏登记，非臆造）。"""

    src = _javap_src(ctrl)

    if frag == '':

        assert 'annotation.PostMapping' + _NL in src

        return

    assert 'value=[' + Q + frag + Q + ']' in src, (op, ctrl, frag)





@pytest.mark.parametrize('op,ctrl,frag', _RECOVERED)

def test_recovered_path_present_in_persisted_contract(op, ctrl, frag):

    """修复态：上述片段现已**在**契约 path 集合内（旧版此断言取反）。"""

    paths = {m['path'] for m in _api()[ctrl]['methods']}

    assert frag in paths, (op, ctrl, frag)





def test_empty_mapping_path_present_for_application_root():

    """udcApplicationPost：@PostMapping 裸注解（类级根 /udc/application）必须在契约中。"""

    blocks = _method_blocks(_javap_src('ApplicationController'))

    roots = [b for b in blocks if b[0] == 'create' and b[2] == ['']]

    assert len(roots) == 1, roots

    got = [(m['http'], m['full_path'])

           for m in _api()['ApplicationController']['methods'] if m['path'] == '']

    assert got == [('POST', '/udc/application')], got





def test_all_bare_mapping_endpoints_have_class_root_path():

    """14 处裸 mapping 全部落成「类级根」路径（不得留空、不得中文）。"""

    d = _api()

    blanks = [(c, m['method'], m['full_path'])

              for c, v in d.items() for m in v['methods'] if m['path'] == '']

    assert len(blanks) == _BARE_MAPPINGS, len(blanks)

    for c, meth, fp in blanks:

        base = d[c]['class_mapping']

        # 类级 mapping 缺失（ParameterController）-> 方法级 value 即全路径；裸 mapping 则退化为根 /。

        want = ('/' + base) if base else '/'

        assert fp == want, (c, meth, fp, want)

# ---------------------------------------------------------------- 暴露门（@RestApi 双注解）量化
# 2026-10-15 新增：REST-EXPOSURE-MECHANISM.md §1.1。
# MetadataScanner#collectRestMetadata 的守卫 `if (restApi == null || op == null) continue;`
# 要求**类级 @RestApi 与方法级 @RestApiOperation 缺一不可** —— 此前仅文字引用，未量化。
# 独立 class 文件解析器（直读常量池 + 方法表，不经 javap 文本）复核 54/54 类 0 差异。
_EXPOSED_ENDPOINTS = 666
_NO_CLASS_RESTAPI = 6
_NO_METHOD_RESTAPI_OP = 2


def _class_level_restapi(text):
    """类级注解位于 SourceFile 之后的 class attributes 区。"""
    i = text.rfind('SourceFile:')
    tail = text[i:] if i >= 0 else ''
    return 'com.seeyon.boot.annotation.RestApi(' in tail


def _exposure_split(text):
    """-> (mapping 端点数, 真进 op 面数, 类级无 @RestApi 数, 方法级无 @RestApiOperation 数)。"""
    cls_rest = _class_level_restapi(text)
    tot = exposed = no_cls = no_op = 0
    lines = text.split(_NL)
    starts = []
    for i in range(len(lines) - 1):
        ln = lines[i]
        if not ln.startswith('  ') or ln.startswith('   '):
            continue
        t = ln.strip()
        if not t.endswith(';') or '(' not in t:
            continue
        if not lines[i + 1].strip().startswith('descriptor:'):
            continue
        starts.append(i)
    for k, i in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        blk = _NL.join(lines[i:end]).split('RuntimeVisibleParameterAnnotations')[0]
        if not any('annotation.' + a in blk for a in _HTTP_ANN):
            continue
        tot += 1
        if not cls_rest:
            no_cls += 1
        elif 'com.seeyon.boot.annotation.RestApiOperation(' not in blk:
            no_op += 1
        else:
            exposed += 1
    return tot, exposed, no_cls, no_op


def test_exposure_gate_quantified():
    """674 个 mapping 端点中 666 真正进 op 面（类级 @RestApi ∧ 方法级 @RestApiOperation）。"""
    tot = exposed = no_cls = no_op = 0
    for pth in sorted(_JAVAP.glob('*.javap.txt')):
        t = pth.read_bytes().decode('gbk', errors='replace').replace(chr(13), '')
        a, b, c, d = _exposure_split(t)
        tot += a; exposed += b; no_cls += c; no_op += d
    assert tot == _TOTAL_ENDPOINTS, tot
    assert exposed == _EXPOSED_ENDPOINTS, exposed
    assert no_cls == _NO_CLASS_RESTAPI, no_cls
    assert no_op == _NO_METHOD_RESTAPI_OP, no_op
    # 674 = 666 + 6 + 2（口径自洽）
    assert tot == exposed + no_cls + no_op


def test_parameter_controller_is_the_only_class_without_restapi():
    """ParameterController 是唯一无类级 @RestApi 的 Controller（其 6 条 handler 不进 op 面）。"""
    missing = []
    for pth in sorted(_JAVAP.glob('*.javap.txt')):
        t = pth.read_bytes().decode('gbk', errors='replace').replace(chr(13), '')
        cls, exposed, no_cls, no_op = pth.name.replace('.javap.txt', ''), *_exposure_split(t)[1:]
        if no_cls:
            missing.append(cls)
    assert missing == ['ParameterController'], missing


def test_udc_file_download_has_no_restapi_operation():
    """UdcFileController.download / .metadataDownload 有 mapping 但无 @RestApiOperation。"""
    t = _javap_src('UdcFileController')
    for name in ('download', 'metadataDownload'):
        assert 'annotation.RestApiOperation' not in t.split(name)[1][:400], name
    d = _api()['UdcFileController']
    assert {m['method'] for m in d['methods']} == {'download', 'metadataDownload'}






# ---------------------------------------------------------------- 674 端点 / 673 op 口径收口（2026-10-15 第三轮）

_DISTINCT_OPS = 673





def test_derived_ops_count_is_673_vs_674_endpoints():

    """方法级 mapping 端点 674 条，但 derive_ops 的 distinct op 只有 673。



    差额 1 = ParameterController.create：类级无 @RestApi/mapping（class_mapping=None），

    方法级为裸 @PostMapping -> 其 full_path 落成 "/"；derive_ops 里 strip("/") 为空即跳过。

    这是**已知且有据**的口径差，不是丢数据：该端点本就因 exposure gate（无类级 @RestApi）

    不进 op 面。钉死 674 与 673 两个数，防止二者被混用或静默回退。

    """

    assert sum(v["api_count"] for v in _api().values()) == _TOTAL_ENDPOINTS

    derived = derive_ops(_api())

    assert len(derived) == _DISTINCT_OPS, len(derived)





def test_parameter_controller_create_has_class_root_full_path():

    """差额来源可定位：ParameterController.create 的 full_path 为 "/"（类级无前缀 + 裸 mapping）。



    带 mapping 的 674 个端点里「有可推导 full_path」的只有 673 —— 差值即此条；

    derive_ops 不为其产出 op，故 op 面口径（666）与 exposure 口径均不受影响。

    """

    pc = _api()["ParameterController"]

    assert pc["class_mapping"] is None

    m = [x for x in pc["methods"] if x["method"] == "create"]

    assert len(m) == 1 and m[0]["full_path"] == "/"

    derived = derive_ops(_api())

    assert not any(e["path"] == "" for b in derived.values() for e in b)



