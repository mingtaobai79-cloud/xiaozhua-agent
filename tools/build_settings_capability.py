"""合并三源机器证据 → 全节点配置项能力矩阵 node-settings-capability.json

源（全部已验证 LIVE）：
  fixtures/microflow/node_modals/*.json   逐节点抽屉字段契约（label/control/options/required）
  scratch/variant-evidence/VARIANTS.json  12 类节点 × 40 切换态字段增删实测
  scratch/node-full-evidence/SUMMARY.json 24 类节点真实画布抽屉 form_items（required 实测）
  语料 pmp_schemas.json                    落库形态统计（mappingType 等存储键真值）
  本轮构建实证                              compile_facts（backBuild.log 级）
"""
import os, json, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = os.path.join(ROOT, "core/facts/udc/microflow/node-settings-capability.json")

modals = {}
ALIAS = {"CREATE_MAPPING_GROUP": "CREATE_MAP", "MAPPING_OPERATION": "MAP_OPERATION",
         "MODIFY_LIST": "CHANGE_LIST", "CUSTOM_SERVICE": "CALL_APP_SERVICE",
         "DATA_CONVERSION": "DATA_MAPPING", "EVENT_DELIVERY": "PUBLISH_BUSINESS_EVENT",
         "TYPE_CONVERT": "CONVERT_DATA"}
for f in glob.glob(os.path.join(ROOT, "fixtures/microflow/node_modals/*.json")):
    m = json.load(open(f, encoding="utf-8"))
    at = ALIAS.get(m.get("actionType")) or m.get("actionType") or os.path.basename(f)[:-5]
    # 统一字段来源：modal_fields / common_fields / mode_fields / query_modes 都并入 modal_fields
    merged = list(m.get("modal_fields") or [])
    seen = {x.get("label") for x in merged}
    for k in ("common_fields", "mode_fields"):
        for x in m.get(k) or []:
            if isinstance(x, dict) and x.get("label") and x["label"] not in seen:
                seen.add(x["label"]); merged.append(x)
    for mode, qm in (m.get("query_modes") or {}).items():
        for lbl in (qm.get("fields") or []):
            if lbl not in seen:
                seen.add(lbl)
                merged.append({"label": lbl, "required": None,
                               "note": "仅「%s」模式" % mode, "source_mode": mode})
    m["modal_fields"] = merged
    modals.setdefault(at, m)

variants = json.load(open(os.path.join(ROOT, "scratch/variant-evidence/VARIANTS.json"), encoding="utf-8"))
summary = json.load(open(os.path.join(ROOT, "scratch/node-full-evidence/SUMMARY.json"), encoding="utf-8"))["nodes"]

# UI 标题 → actionType
title2at = {m.get("caption"): at for at, m in modals.items()}
title2at.update({"分支": "BRANCH", "列表循环": "FOR_EACH", "计数循环": "FOR", "自定义错误": "CUSTOM_ERROR",
                 "创建变量": "CREATE_VARIABLE", "修改变量": "CHANGE_VARIABLE", "创建映射组": "CREATE_MAP",
                 "映射操作": "MAP_OPERATION", "创建列表": "CREATE_LIST", "修改列表": "CHANGE_LIST",
                 "列表操作": "LIST_OPERATION", "查询单条数据": "RETRIEVE", "查询多条数据": "RETRIEVE_ARRAY",
                 "插入数据": "CREATE_ENTITY", "批量插入数据": "CREATE_BATCH_ENTITY", "更新数据": "CHANGE_ENTITY",
                 "批量更新数据": "CHANGE_BATCH_ENTITY", "删除数据": "DELETE_ENTITY", "自定义服务": "CALL_APP_SERVICE",
                 "事件投递": "PUBLISH_BUSINESS_EVENT", "子微流程": "SUB_MICROFLOW", "执行生单规则": "CALL_DATA_FLOW",
                 "类型转换": "CONVERT_DATA", "数据转换": "DATA_MAPPING"})

# 构建实证（backBuild.log / 前端指纹级，全部本轮或历史实测）
COMPILE_FACTS = {
    "CREATE_VARIABLE": [
        "BASIC 引用前序 BASIC 出参：selectParam.id/dtoType 必须空串（G17，PageInfo 模板残留）",
        "语料 1644 条：mappingType 仅实体型必带（attrs=字段映射/value=对象引用/mapping=自动映射）；BASIC 无此键，模式由 value 形态表达",
        "BASIC+SelectParam 引用 25/25 带 selectParam.path、23/25 带 customs 块（sourceType=ENTITY/SYSTEM）",
        "attrType 引用四键 refId/relationEntity/relationEntityId/filterRelationEntity 缺一即红字（G25）",
    ],
    "CHANGE_VARIABLE": [
        "mappingType=attrs 时 attrType 同四键（G27，原闸门只查 CREATE_VARIABLE 漏修改变量）",
        "赋值方式不选/缺失 → 前端不知道生成什么类型代码，依赖配置不出现（用户实测 2026-10-31）",
    ],
    "CREATE_ENTITY": [
        "G19：出参必须是影响行数（dataType=BIGINTEGER/INTEGER、dtoType 空），DTO 出参 → SingleResponse<Integer> 无法赋给 Dto 编译失败",
        "value 应为 null，赋值走 attrs（node-field-shape-contract §6）",
    ],
    "CHANGE_ENTITY": ["G19：出参=影响行数；赋值方式是级联字段，未选「选择更新的数据」前不渲染（node-variants §2.3）"],
    "CREATE_BATCH_ENTITY": ["G19：出参=影响行数；吃列表（创建列表/前序列表出参/RETRIEVE_ARRAY）"],
    "CHANGE_BATCH_ENTITY": ["G19：出参=影响行数；G24：selectParam 必带 key"],
    "DELETE_ENTITY": ["三种删除规则（指定/过滤条件/ID集合）字段集不同（VARIANTS 实测）"],
    "CALL_APP_SERVICE": [
        "G26：selectMethod 必带 md5/parameter/returnValue/fullName（缺 md5 原 G1-G25 全绿，设计器参数页签取不到出入参）",
        "parameter/returnValue 收最小形态 {caption,type,item:{enums,itemType,item}}，builder 模板 attrs 死引用必须清空 node.attrs=[]",
    ],
    "DATA_MAPPING": [
        "G29：上游必须列表（selectParam.type=ARRAY）；单对象主实体 → 生成器按 List 处理编译失败（backBuild.log 20261031185114）",
        "structure.key 恒两段 <源实体>_<目标实体>（同实体自映射也要拼）；上游列表时 output.type=ARRAY",
        "列表出参不能直接接 END basic（List<Dto> 无法转换为 Dto [161,140]），需 LIST_OPERATION 等承接",
    ],
    "MAP_OPERATION": [
        "basic 必须是选项对象 {label,value,key,dataType}，裸字符串 → 抽屉空占位 + structure 展开成字符下标垃圾（G9）",
        "GET 必填 selectMap/operationType/theKey/basic/arrayOrObject；entries 只对 PUT，GET 必须删；GET nullHandling 语料全 CONTINUE",
        "真实下拉选项：获取/赋值/删除/获取键列表（分组标题不是选项，node-variants §2.2）",
    ],
    "RETRIEVE": [
        "条件右值只有 CONTEXT_VARIABLE/CONSTANT/EXPRESSION 三形态，Simple → BOOT_1001 Parameter Error（condition_group 归一）",
    ],
    "RETRIEVE_ARRAY": [
        "pageSearch 是字符串 \"false\"（默认 \"true\" 会把 pageInfo 变必填阻塞保存，node-variants §2.4）",
    ],
    "END_NODE": [
        "END 必须在顶层 endNode、绝不能进 nodes；漏 type/actionType → 画布「节点开发中...」占位卡",
        "出参 basic 出参不能承接列表型前序值（List<Dto> 无法转换为 Dto）",
    ],
    "FOR_EACH": ["selectParam 才是保存校验认的字段，foreach.sourceItemes 是前端容器用；实体列表 selectParam 必带 dtoType"],
    "PUBLISH_BUSINESS_EVENT": ["IN_APP（应用内同步）用 selectEvent 非 selectMq；事件类型 radio 两态字段集不同"],
    "CALL_DATA_FLOW": [
        "dataFlowMappingId=规则列表行 id；dataFlow.id=dataFlowId（用列表行 id 报「生单规则已被删除」）；dataSourceType 只许 CONDITION/SELECT_PARAM；outputName 服务端必填位置未定（UNVERIFIED O1）",
    ],
    "CHANGE_LIST": ["action 必填；dataSource 不能留模板值（指向模板兄弟节点 → 「引用的参数已失效」红框）"],
    "LIST_OPERATION": ["真实操作选项：计数/过滤/去重/第一条/最后一条/第N条（分组标题非选项）"],
}

VALUE_CAPABILITY = ("值槽三态通用：常量=Simple{simple,desc} / 引用=SelectParam{outputName,key,customs,path} / "
                    "表达式=Expression{title,schema}（经 /expression/check + /expression/transform，executableExpr 不能手拼）；"
                    "条件右值仅 CONTEXT_VARIABLE(337)/CONSTANT(90)/EXPRESSION(65)")

out = {"_meta": {
    "desc": "全节点配置项能力矩阵：每个配置项的 UI 标签/控件/选项/子模式联动/必填时机/取值能力/编译实证。",
    "sources": ["fixtures/microflow/node_modals/*.json", "scratch/variant-evidence/VARIANTS.json",
                "scratch/node-full-evidence/SUMMARY.json", "pmp_schemas.json 语料", "backBuild.log 构建实证"],
    "value_capability_universal": VALUE_CAPABILITY,
    "generated": "2026-10-31",
}, "nodes": {}}

for title, node in summary.items():
    at = title2at.get(title)
    entry = {"caption": title, "actionType": at, "settings": [], "submodes": [], "compile_or_ui_facts": []}
    modal = modals.get(at or "", {})
    seen_labels = set()
    for fld in modal.get("modal_fields", []):
        seen_labels.add(fld.get("label"))
        entry["settings"].append({
            "key": None, "ui_label": fld.get("label"), "control": fld.get("control"),
            "options": fld.get("options"), "default": fld.get("default"),
            "required": fld.get("required"), "when": fld.get("note") or "",
            "source": "node_modals",
        })
    # 兜底：VARIANTS default / SUMMARY 实测抽屉字段（label+required），补 node_modals 缺的节点
    def _merge_items(items, source):
        for it in items or []:
            if not isinstance(it, dict) or not it.get("label"):
                continue
            if it["label"] in seen_labels:
                continue
            seen_labels.add(it["label"])
            entry["settings"].append({
                "key": it.get("id"), "ui_label": it["label"], "control": None,
                "options": None, "default": None,
                "required": bool(it.get("required")), "when": "",
                "source": source,
            })
    _merge_items((variants_of_default := None) or [], "")  # 占位防误用
    dv = None
    for vtitle, variants_of in variants.items():
        if title2at.get(vtitle) == at:
            dv = (variants_of.get("default") or {}).get("form_items")
            break
    _merge_items(dv, "VARIANTS.default")
    live = ((summary.get(title) or {}).get("step2_pick") or {}).get("drawer") or {}
    _merge_items(live.get("form_items"), "SUMMARY.drawer")
    # 子模式切换态（VARIANTS）
    for vtitle, variants_of in variants.items():
        if title2at.get(vtitle) != at:
            continue
        base_items = {i.get("label") for i in (variants_of.get("default") or {}).get("form_items", []) if isinstance(i, dict)}
        for key, var in (variants_of.items() if isinstance(variants_of, dict) else []):
            if key in ("node", "modal", "mode_field", "ts", "panel_ok", "default"):
                continue
            items = (var or {}).get("form_items") if isinstance(var, dict) else None
            if items is None:
                continue
            cur = {i.get("label") for i in items if isinstance(i, dict)}
            req = [i.get("label") for i in items if isinstance(i, dict) and i.get("required")]
            entry["submodes"].append({
                "mode_field": variants_of.get("mode_field"),
                "mode": key,
                "fields_added": sorted(cur - base_items),
                "fields_removed": sorted(base_items - cur),
                "required": req,
            })
    entry["compile_or_ui_facts"] = COMPILE_FACTS.get(at, [])
    entry["evidence_files"] = ["node_modals/%s.json" % (modal.get("actionType") or at or title),
                               "variant-evidence/VARIANTS.json", "node-full-evidence/SUMMARY.json"]
    out["nodes"][at or title] = entry

HAND = {
    "BRANCH": {"settings": [
        {"ui_label": "条件分支", "key": "conditions", "when": "恒有；name 只能 ifBranch/elseIfBranch/elseBranch（build-chain.md）",
         "required": True, "control": "branch-editor",
         "options": None, "default": None},
        {"ui_label": "条件表达式", "key": "conditions[].expression",
         "when": "ifBranch/elseIfBranch 必带；elseBranch 恒无（941/941）",
         "required": True, "control": "expression-editor", "value_capability": "表达式（tokens 顺序=[左值,算子,右值]）",
         "options": None, "default": None},
    ], "facts": ["BRANCH 无 actionType（type=BRANCH）；conditions[].nodes 装分支体",
                 "elseBranch isCompleted=None 是常态，红点判据要排除"]},
    "FOR": {"settings": [
        {"ui_label": "开始/结束/步长", "key": "forStart/forEnd/forStep", "when": "恒有（forStep=数字模板 1）", "required": True,
         "control": "value-slot", "value_capability": "常量/表达式（forEnd 可用 roundOffFloor 等函数表达式）", "options": None, "default": None},
        {"ui_label": "循环变量名", "key": "targetName", "when": "恒有（计数循环变量_1）", "required": True,
         "control": "input", "options": None, "default": None},
        {"ui_label": "比较符", "key": "operator", "when": "恒有（模板 <=）", "required": True, "control": "select", "options": ["<=", "<", ">=", ">", "=="], "default": "<="},
    ], "facts": ["FOR 的 foreach=null（FOR_EACH 才有 foreach 对象）；type=FOR + actionType=FOR",
                 "缺 forEnd → C-FOR 契约闸门拦"]},
    "FOR_EACH": {"settings": [
        {"ui_label": "选择列表", "key": "selectParam", "when": "恒有；filter: type=='ARRAY'；实体列表必带 dtoType",
         "required": True, "control": "param-picker", "value_capability": "前序引用（列表型出参）", "options": None, "default": None},
        {"ui_label": "循环对象名称", "key": "targetName", "when": "恒有", "required": True, "control": "input", "options": None, "default": None},
    ], "facts": ["type=FOR_EACH、无 actionType；foreach.sourceItemes 是前端容器用，保存校验只认 selectParam",
                 "画布卡片文本是「循环列表：」"]},
    "CREATE_LIST": {"settings": [
        {"ui_label": "数据类型", "key": "dataType", "when": "恒有", "required": True, "control": "select", "options": ["STRING", "INTEGER", "DTO"], "default": None},
        {"ui_label": "默认值", "key": "value", "when": "可选（母版无 value 也发布；BASIC 分支 valueComponent 三态）",
         "required": False, "control": "value-slot", "value_capability": "常量/引用/表达式", "options": None, "default": None},
        {"ui_label": "structure", "key": "structure", "when": "DTO 列表必带（C- 契约闸门）", "required": True, "control": None, "options": None, "default": None},
    ], "facts": ["value 缺键也会被 C- 闸门要求「可为空但不能没有」"]},
}
for at, spec in HAND.items():
    e = out["nodes"].get(at)
    if not e:
        continue
    if not e["settings"]:
        e["settings"] = spec["settings"]
    e["compile_or_ui_facts"] = (e["compile_or_ui_facts"] or []) + spec["facts"]
    e["evidence_files"] = sorted(set(e["evidence_files"] + ["node-field-shape-contract.md", "build-chain.md"]))


json.dump(out, open(FACTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
covered = [k for k, v in out["nodes"].items() if v["settings"] or v["submodes"]]
print("节点数:", len(out["nodes"]), "| 有配置项/子模式的:", len(covered))
print("子模式切换态总数:", sum(len(v["submodes"]) for v in out["nodes"].values()))
for k, v in out["nodes"].items():
    print("  %-24s settings=%d submodes=%d facts=%d" % (k, len(v["settings"]), len(v["submodes"]), len(v["compile_or_ui_facts"])))
