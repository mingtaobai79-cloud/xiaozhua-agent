"""模板残留引用检查：所有构造器产物里，不得有指向「不在本流程节点表」的引用。

动机：SUB_MICROFLOW.json 模板带 `_RETRIEVE_KNCEzh` 残留，构造器没清 → G2 拦发布。
19 个模板都含类似字面量，靠人眼查会漏。这个脚本机械扫。
"""
import json
import os
import re
import sys

os.chdir('<XIAOZHUA_AGENT_ROOT>')
sys.path.insert(0, '.')

from components.construction.node_builder import NodeBuilder
from components.construction import microflow_fields as F
from components.construction import microflow_nodes_v2 as V2
from components.construction import microflow_nodes_extra as X
from components.construction import microflow_nodes_svc as S

APP = "9000000000000000001"
APP_NAME = "datamigration9000000000000000001"

ENTITY = {
    "fullName": "com.seeyon.%s.dto.TestDto" % APP_NAME,
    "entity": "com.seeyon.%s.domain.entity.Test" % APP_NAME,
    "caption": "测试实体",
    "relationEntityId": "1234567890123456789",
    "refApp": APP_NAME,
    "attributes": {
        n: {"id": "com.seeyon.%s.dto.TestDto.%s" % (APP_NAME, n),
            "fullName": "com.seeyon.%s.dto.TestDto.%s" % (APP_NAME, n),
            "md5": "0123456789abcdef", "javaType": "java.lang.String",
            "dataType": "STRING", "caption": n}
        for n in ("mingcheng", "expText")
    },
}

b = NodeBuilder(app_id=APP, app_name=APP_NAME)
VAR = V2.create_variable(b, "vText", "STRING", F.simple("x"))
LIST = X.create_list(b, "vList")
RET = V2.retrieve(b, ENTITY, "mingcheng", F.constant("k"))
MAPN = X.create_map(b, "vMap")
MF = {"id": "-2470830010974137519", "appId": APP, "caption": "子流程",
      "name": "MFSERVICEtest", "path": "/microflow/MFSERVICEtest",
      "type": "SERVICE", "triggerType": "MANUAL", "method": "GET",
      "appCaption": None, "appName": None, "description": "",
      "hasInput": False, "hasOutput": False, "hostPath": None,
      "input": None, "output": None, "restType": "GET"}
DF = {"id": "5304545611384242198", "caption": "生单规则", "name": "df",
      "sourceEntityId": ENTITY["relationEntityId"]}

CASES = {}
def run(label, fn):
    try:
        n = fn()
        if isinstance(n, dict):
            CASES[label] = n
    except Exception as e:
        print("  !! %s 构造异常: %s" % (label, str(e)[:90]))

run("CREATE_VARIABLE", lambda: VAR)
run("CHANGE_VARIABLE", lambda: V2.change_variable(b, VAR, F.simple("y")))
run("CREATE_LIST", lambda: LIST)
run("CHANGE_LIST", lambda: X.change_list(b, LIST, VAR))
run("LIST_OPERATION", lambda: X.list_operation(b, LIST))
run("CREATE_MAP", lambda: MAPN)
run("MAP_OPERATION", lambda: X.map_operation(b, MAPN, F.simple("k")))
run("RETRIEVE", lambda: RET)
run("RETRIEVE_ARRAY", lambda: V2.retrieve_array(b, ENTITY, "mingcheng", F.constant("k")))
run("CREATE_ENTITY", lambda: V2.create_entity(b, ENTITY, [("mingcheng", F.simple("n"))]))
run("CHANGE_ENTITY", lambda: V2.change_entity(b, ENTITY, RET, [("mingcheng", F.simple("n"))]))
run("DELETE_ENTITY", lambda: V2.delete_entity(b, ENTITY, "mingcheng", F.constant("k")))
run("CREATE_BATCH_ENTITY", lambda: X.create_batch_entity(b, ENTITY, LIST, []))
run("CHANGE_BATCH_ENTITY", lambda: X.change_batch_entity(b, ENTITY, LIST, []))
run("CONVERT_DATA", lambda: X.convert_data(b, VAR, "Split", "结果"))
run("FOR", lambda: X.for_count(b, F.simple("0"), F.simple("10"), 1))
run("FOR_EACH", lambda: S.for_each(b, LIST))
run("CUSTOM_ERROR", lambda: X.custom_error(b, "错误"))
run("SUB_MICROFLOW", lambda: S.sub_microflow(b, MF))
run("CALL_APP_SERVICE", lambda: S.call_app_service(
    b, "FileAppService.copy", [],
    select_method={"fullName": "com.seeyon.boot.starter.file.appservice."
                             "FileAppService.copy", "md5": "x",
                   "caption": "复制", "dubbo": True,
                   "parameter": {"caption": "p", "type": "SingleRequest",
                                 "item": {"itemType": "java.lang.String"}},
                   "returnValue": {"caption": "r", "type": "SingleResponse",
                                   "item": {"itemType": "java.lang.String"}}}))
run("DATA_MAPPING", lambda: S.data_mapping(b, ENTITY, LIST))
run("CALL_DATA_FLOW", lambda: S.call_data_flow(b, ENTITY, {"id": DF["id"],
    "caption": DF["caption"], "name": DF["name"],
    "sourceEntityId": DF["sourceEntityId"]}))
run("BRANCH", lambda: X.branch(b, []))

# 本流程的合法节点集合
KNOWN = {n["nodeId"] for n in CASES.values()}
KNOWN |= {"MFStartNode", "MFEndNode"}

# 每个构造器单独看：它的节点里有没有指向别人/不存在节点的引用
print("=" * 84)
print("模板残留引用检查（引用指向的 nodeId 必须在本流程节点表内）")
print("=" * 84)

bad = 0
for label, node in sorted(CASES.items()):
    # 只查「该节点自身携带的引用」：nodeInfo.nodeId 指向的必须是自己或本流程已有的
    found = []

    def scan(o, path=""):
        if isinstance(o, dict):
            if o.get("type") == "SelectParam":
                sp = o.get("selectParam") or {}
                ni = (sp.get("nodeInfo") or {}).get("nodeId")
                on = sp.get("outputName")
                if ni and ni not in KNOWN:
                    found.append((path, ni))
                elif not ni and on and re.match(r"^_[A-Z][A-Z_]+_[A-Za-z0-9]{4,}$", str(on)) \
                        and on not in {v.get("output", {}).get("name") for v in CASES.values()}:
                    found.append((path, on))
            for k, v in o.items():
                scan(v, path + "." + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                scan(v, "%s[%d]" % (path, i))

    scan(node)
    # 排除「引用了本测试里其他构造器节点」的情况（跨节点合法引用）
    real_bad = [(p, nid) for p, nid in found if nid not in KNOWN]
    if real_bad:
        bad += 1
        print("\n✗ %s" % label)
        for p, nid in real_bad[:5]:
            print("     %s -> %s" % (p, nid))
    else:
        print("✓ %-22s 无残留引用" % label)

print("\n" + "=" * 84)
print("结果: %d / %d 个构造器干净，%d 个带残留引用"
      % (len(CASES) - bad, len(CASES), bad))
sys.exit(1 if bad else 0)
