#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
标品域能力索引生成器
====================
从 docs/audit/reference/surface-index.tar.gz 的 domains/*.md 提取
「域 → 接口 → 方法签名」，生成结构化 JSON 索引。

用途：让 Agent 能按业务意图检索标品能力（组织/BPM/文件/枚举…）。

用法：
  python scripts/research/build_domain_index.py
  python scripts/research/build_domain_index.py --query "按部门查人员"
"""
import argparse
import json
import os
import re
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SURFACE = os.path.join(ROOT, "docs/audit/reference/surface-index.tar.gz")
OUT = os.path.join(ROOT, "core/research/platform-dev-system/domain-index.json")

# 域 → 业务标签（帮助检索）
DOMAIN_TAGS = {
    "organization": ["组织", "部门", "单位", "人员", "岗位", "职级", "角色", "兼职", "多维组织", "汇报线"],
    "bpm": ["流程", "审批", "单据", "发起", "提交", "退回", "终止", "模板", "节点", "表单权限", "会签"],
    "file": ["附件", "文件", "上传", "下载", "存储", "分片", "缩略图", "水印"],
    "formula": ["表达式", "公式", "函数", "计算"],
    "mybatis": ["DAO", "持久化", "分页", "查询", "批量", "动态SQL"],
    "affair": ["事项", "待办", "协同", "督办"],
    "connector": ["集成", "连接器", "第三方", "SSO", "数据同步"],
    "dubbo": ["泛化", "跨服务", "代理", "可靠调用"],
    "systemvariable": ["系统变量", "系统参数"],
    "formconvert": ["表单转换", "Word", "模板"],
    "datasource": ["数据源", "连接池"],
}


def parse_domain(raw):
    """解析 domains/*.md，返回 {scale, interfaces:[{name, methods:N, pkg, signatures:[...]}]}"""
    raw = raw.replace("\r", "")
    out = {"scale": None, "interfaces": []}

    m = re.search(r"规模：(\d+) 类 / (\d+) 接口 / (\d+) 个关键类 / (\d+) 方法", raw)
    if m:
        out["scale"] = {
            "classes": int(m.group(1)),
            "interfaces": int(m.group(2)),
            "key_classes": int(m.group(3)),
            "methods": int(m.group(4)),
        }

    # 按 "### `Name`（N 方法）" 分段
    blocks = re.split(r"### `(\w+)`（(\d+) 方法）", raw)
    # blocks[0] 是头部，之后三三元组: name, count, body
    for i in range(1, len(blocks) - 2, 3):
        name = blocks[i]
        count = int(blocks[i + 1])
        body = blocks[i + 2]

        pkg = ""
        pm = re.search(r"`(com\.seeyon[\w\.]+)`", body)
        if pm:
            pkg = pm.group(1)

        sigs = []
        cm = re.search(r"```java\n(.*?)```", body, re.S)
        if cm:
            for line in cm.group(1).split("\n"):
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                # 提取方法名
                mm = re.search(r"(\w+)\s*\(", line)
                if mm:
                    sigs.append({"method": mm.group(1), "sig": line[:400]})

        out["interfaces"].append({
            "name": name,
            "method_count": count,
            "package": pkg,
            "methods": sigs,
        })
    return out


def build():
    tf = tarfile.open(SURFACE, "r:gz")
    index = {}
    for n in tf.getnames():
        if not n.startswith("domains/") or not n.endswith(".md"):
            continue
        dom = n.replace("domains/", "").replace(".md", "")
        raw = tf.extractfile(n).read().decode("utf-8", "ignore")
        d = parse_domain(raw)
        d["tags"] = DOMAIN_TAGS.get(dom, [])
        index[dom] = d
    return index


def stats(index):
    print("=" * 72)
    print("标品域索引统计")
    print("=" * 72)
    tot_cls = tot_if = tot_m = tot_sig = 0
    print(f"{'域':20s} {'类':>6} {'接口':>6} {'方法':>8} {'已提取签名':>10}")
    print("-" * 72)
    for dom in sorted(index, key=lambda k: -(index[k]["scale"]["methods"] if index[k]["scale"] else 0)):
        d = index[dom]
        s = d["scale"] or {}
        sig = sum(len(i["methods"]) for i in d["interfaces"])
        tot_cls += s.get("classes", 0)
        tot_if += s.get("interfaces", 0)
        tot_m += s.get("methods", 0)
        tot_sig += sig
        print(f"{dom:20s} {s.get('classes',0):>6} {s.get('interfaces',0):>6} "
              f"{s.get('methods',0):>8} {sig:>10}")
    print("-" * 72)
    print(f"{'合计':20s} {tot_cls:>6} {tot_if:>6} {tot_m:>8} {tot_sig:>10}")


# 中文意图 → 英文方法名关键词
# ★ 分两类：动作词权重低（因为 select 满地都是），对象词权重高
ACTION_MAP = {
    "查": ["select", "get", "query", "find", "list"],
    "查询": ["select", "query", "list"],
    "取": ["get", "select"],
    "获取": ["get", "select"],
    "新增": ["create", "add", "insert"],
    "创建": ["create", "add"],
    "保存": ["save", "create", "update"],
    "修改": ["update", "modify", "edit"],
    "更新": ["update"],
    "删除": ["delete", "remove"],
    "上传": ["upload"],
    "下载": ["download"],
    "发起": ["start"],
    "提交": ["submit"],
    "退回": ["return", "reject"],
    "终止": ["stop", "terminate"],
    "暂停": ["pause", "suspend"],
    "撤回": ["takeBack", "repeal", "withdraw"],
    "审批": ["approve"],
    "同步": ["sync"],
    "分页": ["page"],
    "批量": ["batch"],
}

OBJECT_MAP = {
    "人员": ["member"],
    "用户": ["user"],
    "部门": ["unit", "department"],
    "单位": ["unit", "org"],
    "岗位": ["post"],
    "职级": ["level"],
    "角色": ["role"],
    "组织": ["org"],
    "流程": ["bpm", "process"],
    "单据": ["case", "bill"],
    "模板": ["template"],
    "节点": ["node", "activity"],
    "附件": ["file", "attach"],
    "文件": ["file"],
    "分片": ["part"],
    "缩略图": ["thumbnail"],
    "水印": ["watermark"],
    "表达式": ["expression", "formula"],
    "函数": ["function"],
    "权限": ["permission", "auth"],
    "意见": ["opinion"],
    "日志": ["log"],
    "部门信息": ["unit"],
    "多维组织": ["multidim"],
}

INTENT_MAP = {**ACTION_MAP, **OBJECT_MAP}


def expand_intent(q):
    """返回 (动作词集合, 对象词集合)"""
    acts, objs = set(), set()
    for cn in sorted(ACTION_MAP, key=len, reverse=True):
        if cn in q:
            acts.update(t.lower() for t in ACTION_MAP[cn])
    for cn in sorted(OBJECT_MAP, key=len, reverse=True):
        if cn in q:
            objs.update(t.lower() for t in OBJECT_MAP[cn])
    return acts, objs


def search(index, q):
    """中文意图检索：按最佳单方法命中打分，不按累加（避免方法多的接口刷分）"""
    def grams(s):
        s = s.lower()
        out = set()
        for w in re.findall(r"[a-z0-9_]+", s):
            if len(w) >= 2:
                out.add(w)
        for run in re.findall(r"[\u4e00-\u9fff]+", s):
            if len(run) == 1:
                out.add(run)
            else:
                for i in range(len(run) - 1):
                    out.add(run[i:i + 2])
        return out

    qg = grams(q)
    acts, objs = expand_intent(q)
    hits = []

    for dom, d in index.items():
        tag_score = 0
        for t in d["tags"]:
            tg = grams(t)
            if tg and len(tg & qg) / len(tg) >= 0.5:
                tag_score = max(tag_score, 2)
                break

        for iface in d["interfaces"]:
            nm = iface["name"].lower()
            pkg = (iface["package"] or "").lower()
            iface_has_obj = bool(objs) and (any(o in nm for o in objs) or any(o in pkg for o in objs))

            # ★ 取「单个方法的最佳得分」，而不是累加
            best = 0
            best_methods = []
            obj_best = 0
            for m in iface["methods"]:
                mn = m["method"].lower()
                a = sum(1 for e in acts if e in mn)
                o = sum(1 for e in objs if e in mn)

                if o >= 1 and a >= 1:
                    s = 100 + o * 8 + a * 4        # 动作+对象双命中
                elif o >= 1:
                    s = 40 + o * 8                 # 只命中对象
                elif a >= 1:
                    s = 30 + a * 4                 # 只命中动作（submit / start 这类）
                else:
                    s = 0

                # ★ 纯动作方法：若接口本身在对象域里，提权（BpmAppService.submit）
                if s == 30 + a * 4 and iface_has_obj:
                    s = 95

                if s > best:
                    best = s
                    obj_best = o
                    best_methods = [m["method"]]
                elif s == best and s > 0:
                    best_methods.append(m["method"])

            sc = best
            if sc == 0:
                if tag_score:
                    sc = tag_score
                else:
                    continue

            if iface_has_obj:
                sc += 15
            if acts and any(a in nm for a in acts):
                sc += 3

            hits.append({
                "score": sc, "domain": dom, "interface": iface["name"],
                "package": iface["package"], "method_count": iface["method_count"],
                "matched_methods": best_methods[:8],
                "obj_hits": obj_best,
            })

    hits.sort(key=lambda x: (-x["score"], -x["obj_hits"], x["method_count"]))
    return hits[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query")
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args()

    index = build()
    stats(index)

    if a.save:
        json.dump(index, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n已写入 {OUT}")

    if a.query:
        print()
        print("=" * 72)
        print(f"检索：{a.query}")
        print("=" * 72)
        for h in search(index, a.query):
            print(f"[{h['score']:>2}] {h['domain']:16s} {h['interface']:38s} {h['method_count']:>3}方法")
            if h["matched_methods"]:
                print(f"      命中：{', '.join(h['matched_methods'])}")


if __name__ == "__main__":
    main()
