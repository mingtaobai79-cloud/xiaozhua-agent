# -*- coding: utf-8 -*-
"""由 facade json 生成应用文档的「接口面」部分。

用法：
  python gen_app_doc.py organization --out DIR
  python gen_app_doc.py bpm --out DIR
"""
import json, io, os, sys, re, collections

REPO = "C:/Users/白明涛/xiaozhua-agent"
FACADE = f"{REPO}/docs/audit/artifacts/facade"

VERB_WORDS = {
    "select": "查询", "get": "获取", "query": "查询", "find": "查找",
    "search": "搜索", "load": "加载", "fetch": "拉取", "list": "列出",
    "create": "新建", "add": "新增", "save": "保存", "insert": "插入",
    "update": "修改", "modify": "修改", "edit": "编辑", "upsert": "新建或修改",
    "delete": "删除", "remove": "移除", "disable": "停用", "enable": "启用",
    "push": "推送", "sync": "同步", "import": "导入", "export": "导出",
    "check": "校验", "validate": "校验", "verify": "校验",
    "is": "判断", "has": "判断有", "can": "判断能否", "exists": "判断存在",
    "count": "统计", "register": "注册", "bind": "绑定", "unbind": "解绑",
    "fix": "修正", "fill": "填充", "convert": "转换", "contains": "判断包含",
    "copy": "复制", "move": "移动", "sort": "排序", "merge": "合并",
}

MOD_WORDS = {
    "Page": "分页", "List": "列表", "Cascade": "级联", "CascadeList": "",
    "Batch": "批量", "Dynamic": "动态", "Join": "", "Info": "",
    "Core": "", "Base": "", "Properties": "指定字段", "All": "全部",
    "Ignore": "", "Tenant": "", "Id": "", "Self": "本人",
    "Increment": "增量", "Node": "", "Tree": "树", "Extension": "扩展",
}

SEM_WORDS = {
    "Access": "可见", "View": "", "Sensitive": "敏感", "Secret": "涉密",
    "Manage": "管理", "Manager": "负责人", "Leader": "领导",
    "Supervise": "监管", "Supervisor": "上级", "Auth": "权限",
    "Permission": "权限", "Role": "角色", "Legal": "法人",
    "Watermark": "水印", "Offline": "离线", "Storage": "存储",
    "Metadata": "扩展属性", "Extend": "扩展", "Ext": "扩展",
    "Child": "下级", "Children": "下级", "Parent": "上级", "Parents": "上级",
    "Root": "根", "First": "第一级", "Same": "同", "Type": "类型",
    "Scope": "范围", "Domain": "域", "Main": "主", "Current": "当前",
    "Login": "登录", "Switch": "切换", "Institution": "机构",
    "SelectPeople": "选人数据", "Split": "拆分", "Path": "路径",
    "Tradition": "传统", "Simple": "简单", "Name": "名称", "Names": "名称",
    "Code": "编码", "Codes": "编码", "Third": "第三方", "Thirds": "第三方",
    "Condition": "条件", "Conditions": "条件", "Key": "键", "Sort": "排序",
    "Table": "表", "Data": "数据", "Number": "编号", "Field": "字段",
    "Fields": "字段", "Member": "人员", "Members": "人员",
    "Unit": "单位", "Units": "单位", "Department": "部门", "Dept": "部门",
    "Org": "组织", "Post": "岗位", "Posts": "岗位", "Job": "职务",
    "Level": "职务级别", "Levels": "职务级别", "Team": "团队",
    "Role": "角色", "Roles": "角色", "Account": "账户", "Password": "密码",
    "AddressBook": "通讯录", "External": "外部人员", "Business": "业务",
    "Parameter": "参数", "Resource": "资源", "File": "文件",
    "Message": "消息", "Notice": "通知", "Log": "日志",
}


def split_camel(name):
    parts = re.sub(r"(?<!^)(?=[A-Z])", " ", name).split()
    # 合并连续大写缩写（如 DSL）
    out, buf = [], ""
    for p in parts:
        if len(p) == 1 and p.isupper():
            buf += p
        else:
            if buf:
                out.append(buf); buf = ""
            out.append(p)
    if buf:
        out.append(buf)
    return out


def zh(words, table):
    got = []
    for w in words:
        if w in table:
            v = table[w]
            if v and v not in got:
                got.append(v)
    return got


def describe(name, args, ret=""):
    """返回 (中文描述, 是否确定)"""
    words = split_camel(name)
    if not words:
        return "执行", False

    verb = ""
    rest = list(words)
    # 动词可能在开头，也可能在 Dynamic/Batch 之后
    for i in range(min(3, len(rest))):
        if rest[i].lower() in VERB_WORDS:
            verb = VERB_WORDS[rest[i].lower()]
            rest = rest[i + 1:]
            break
    certain = bool(verb)

    # By 之后的键
    keys = []
    if "By" in rest:
        i = rest.index("By")
        keys = rest[i + 1:]
        rest = rest[:i]

    # 修饰词
    mods = []
    for w in list(rest):
        if w in MOD_WORDS:
            if MOD_WORDS[w] and MOD_WORDS[w] not in mods:
                mods.append(MOD_WORDS[w])
            rest.remove(w)

    # 语义 + 实体
    nouns = zh(rest, SEM_WORDS)
    # 剩余未识别的词，作为限定（保留原词）
    unknown = [w for w in rest if w not in SEM_WORDS]

    head = "".join(mods) + verb if verb else ""
    if not head:
        head = "执行"

    obj = "".join(nouns)
    if unknown:
        obj += "".join(unknown)

    by = ""
    if keys:
        if keys == ["Id"]:
            by = "按 id"
        elif keys == ["Ids"]:
            by = "按 ids"
        else:
            kz = zh(keys, SEM_WORDS)
            by = "按" + ("".join(kz) if kz else "".join(keys))

    if obj:
        text = head + obj + by
    else:
        # 实体从入参 DTO 或返回 DTO 反推
        ent = entity_of(args, "Request") or (entity_of_ret(ret) if ret else "")
        if ent:
            text = head + ent + by
            certain = True
        elif args:
            text = head + by + f"（{args[0].split(' ')[0].split('<')[0]}）"
            certain = bool(verb)
        else:
            text = head + by
    return text, certain


PRIM = {"Long", "Integer", "String", "Boolean", "Map", "List", "Object",
        "Set", "Double", "BigDecimal", "Date", "LocalDate"}

ENT_SUFFIX = ("Create", "Update", "Base", "Request", "Data", "Dto", "DTO",
              "Batch", "DtoList", "Result", "Info", "Param", "Form")


def _ent(inner):
    inner = inner.split("<")[0].split(",")[0].split(".")[-1]
    if inner in PRIM:
        return ""
    inner = re.sub(r"^(Org|Udc|Ctp|Bpm|Cip|Cdp|Ai)", "", inner)
    words = split_camel(inner)
    words = [w for w in words if w not in ENT_SUFFIX]
    got = zh(words, SEM_WORDS)
    if got:
        return "".join(got)
    return "".join(words) if words else ""


def entity_of(args, _k):
    """从 SingleRequest<OrgCreateMemberBaseDto> 反推中文实体名"""
    if not args:
        return ""
    t = args[0].split(" ")[0]
    m = re.match(r"^(?:Single|List|Page|PageDto)(?:Dto)?Request<(.+)>$", t)
    return _ent(m.group(1)) if m else ""


def entity_of_ret(t):
    if not t:
        return ""
    m = re.match(r"^(?:Single|List|Page)(?:Dto)?Response<(.+)>$", t)
    return _ent(m.group(1)) if m else ""


def compress(t):
    """SingleRequest<X> 只显示 X"""
    if not t:
        return "—"
    m = re.match(r"^(?:Single|List|Page|PageDto)(?:Dto)?Request<(.+)>$", t)
    if m:
        return m.group(1)
    if t in ("SingleRequest", "ListRequest", "PageRequest", "PageDtoRequest"):
        return "无参"
    return t


def esc(s):
    return (s or "").replace("|", "\\|")


NOTES = f"{REPO}/tools/core/platform/notes"


def load_notes(dom):
    p = os.path.join(NOTES, f"{dom}.json")
    if not os.path.exists(p):
        return {}
    d = json.load(io.open(p, encoding="utf-8"))
    return {k: v for k, v in d.items() if not k.startswith("_")}


def render(dom, note_map=None, title_prefix="facade 层"):
    o = json.load(io.open(f"{FACADE}/{dom}.json", encoding="utf-8"))
    merged = load_notes(dom)
    if note_map:
        merged.update(note_map)
    note_map = merged
    byp = collections.defaultdict(list)
    for f in o["facades"]:
        byp[f["package"]].append(f)

    L = [f"## {title_prefix}：{o['n_facades']} 个接口 / {o['n_methods']} 个方法", "",
         "> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。",
         "> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。", ""]

    L.extend(["### 接口清单", "", "| 包 | 接口数 | 方法数 |", "|---|---:|---:|"])
    tot_i = tot_m = 0
    for p in sorted(byp):
        ni, nm = len(byp[p]), sum(len(f["methods"]) for f in byp[p])
        tot_i += ni; tot_m += nm
        L.append(f"| `{p}` | {ni} | {nm} |")
    L.append(f"| **合计** | **{tot_i}** | **{tot_m}** |")
    L.append("")

    uncertain = 0
    for p in sorted(byp):
        L.append(f"### `{p}`")
        L.append("")
        for f in sorted(byp[p], key=lambda x: x["name"]):
            L.append(f"#### {f['name']}")
            L.append("")
            line = f"`{f['fqcn']}`"
            if f["pkg_artifact"]:
                line += f" · 构件 `{f['pkg_artifact']}`"
            if f.get("extends"):
                line += f" · extends `{', '.join(f['extends'])}`"
            L.append(line)
            L.append("")
            if not f["methods"]:
                L.append("（无方法）")
                L.append("")
                continue
            L.append("| 方法 | 入参 | 返回 | 干什么 |")
            L.append("|---|---|---|---|")
            for m in f["methods"]:
                arg = compress(m["args"][0]) if m["args"] else "—"
                desc, ok = describe(m["name"], m["args"], m["returns"])
                k = f"{f['name']}#{m['name']}"
                if note_map and k in note_map:
                    desc, ok = note_map[k], True
                if not ok:
                    uncertain += 1
                L.append(f"| `{esc(m['name'])}` | `{esc(arg)}` | `{esc(compress(m['returns']))}` "
                         f"| {esc(desc)}{'' if ok else ' ⚠️'} |")
            L.append("")

    L.append(f"> ⚠️ 共 {uncertain} 个方法仅凭名称无法确定语义，需实测或读实现类。")
    L.append("")
    return "\n".join(L), o, uncertain


def main():
    if len(sys.argv) < 2:
        print("用法: gen_app_doc.py <domain> [--out DIR]")
        return 2
    dom = sys.argv[1]
    body, o, unc = render(dom)
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, "_facade.generated.md")
        io.open(p, "w", encoding="utf-8").write(body)
        print(f"{o['n_facades']} 接口 / {o['n_methods']} 方法，其中 {unc} 个语义待定 -> {p}")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())