#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
开发能力索引（研究用最小实现）
==============================
目的：验证「0% 基线是因为索引层错配」这个诊断。
做法：把 research 文档里已证实的「业务能力 → 类#方法」手写成索引，
      用同一份评估集重跑，看命中率是否显著上升。

⚠️ 这是研究原型，不是正式 MCP 工具。
⚠️ 所有映射均来自 core/research/platform-dev-system/ 的已证结论。

用法：
  python scripts/research/dev_capability_index.py --search "下载附件"
  python scripts/research/dev_capability_index.py --eval
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------- 索引定义
# 每条：capability -> {keywords, entries:[(class, method, note, evidence)]}
INDEX = {
    "attachment_download": {
        "keywords": ["下载附件", "取附件链接", "获取文件下载地址", "拿文件URL", "附件怎么取下来", "下载"],
        "entries": [
            ("FileAppService", "getDownloadUrl", "取下载 URL", "06-components.md §3.4"),
            ("FileAppService", "getBackendDownloadUrl", "后端下载 URL", "06-components.md §3.4"),
        ],
    },
    "attachment_upload": {
        "keywords": ["上传附件", "传个文件", "把文件存起来", "登记文件", "上传"],
        "entries": [
            ("FileAppService", "saveFileInfo", "登记文件信息", "06-components.md §3.4"),
            ("FileAppService", "saveFileInfos", "批量登记", "06-components.md §3.4"),
        ],
    },
    "attachment_multipart_upload": {
        "keywords": ["大文件分片上传", "分片上传", "断点续传", "大文件"],
        "entries": [
            ("StorageService", "partUploadInit", "分片初始化", "06-components.md §3.2"),
            ("StorageService", "partUpload", "上传分片", "06-components.md §3.2"),
            ("StorageService", "partUploadEnd", "分片合并", "06-components.md §3.2"),
        ],
    },
    "attachment_thumbnail": {
        "keywords": ["缩略图", "取附件缩略图", "图片预览"],
        "entries": [
            ("FileAppService", "getThumbnailUrl", "缩略图 URL", "06-components.md §3.4"),
            ("FileAppService", "getThumbnailUrls", "批量缩略图", "06-components.md §3.4"),
        ],
    },
    "org_member_query": {
        "keywords": ["查人员", "按ID查人员", "找人", "查询员工信息", "获取成员", "人员信息"],
        "entries": [
            ("OrgCommonAppService", "selectMemberInfoById", "按 ID 查人员", "06-components.md §4.1"),
            ("OrgCommonAppService", "selectMemberDepartmentInfoById", "查部门信息", "06-components.md §4.1"),
        ],
    },
    "org_member_multidim": {
        "keywords": ["多维组织", "一个人多个岗位", "兼职", "主岗副岗", "跨部门任职"],
        "entries": [
            ("OrgCommonAppService", "selectMemberMultiDimOrgInfo", "多维组织信息", "06-components.md §4.1"),
        ],
    },
    "aggregate_create": {
        "keywords": ["主子表保存", "主子表一起保存", "主表和明细一起存", "订单带明细保存", "聚合保存", "连子表一起新增"],
        "entries": [
            ("BaseEntityCurdService", "recursiveCreate", "递归创建（主+子）", "03-persistence.md §8.0.1"),
        ],
    },
    "aggregate_query": {
        "keywords": ["查询主子表", "级联查询", "主子表完整数据", "连子表一起查"],
        "entries": [
            ("BaseEntityCurdService", "selectCascadeById", "级联查询单条", "03-persistence.md §8.0.2"),
            ("BaseEntityCurdService", "selectCascadeByIds", "级联查询批量", "03-persistence.md §8.0.2"),
        ],
    },
    "aggregate_delete": {
        "keywords": ["删除主子表", "级联删除", "主子表整条删除"],
        "entries": [
            ("BaseEntityCurdService", "recursiveDelete", "递归删除", "03-persistence.md §8.0.1"),
        ],
    },
    "tree_children_query": {
        "keywords": ["查子节点", "按父节点查", "查下级", "树形展开", "取子节点", "子表"],
        "entries": [
            ("BaseCurdService", "selectByParentId", "按父 ID 查子", "03-persistence.md §8.0.6"),
            ("BaseCurdService", "selectByParentIds", "批量按父查", "03-persistence.md §8.0.6"),
        ],
    },
    "bill_create_bpm": {
        "keywords": ["创建单据", "发起单据", "起流程", "提申请单", "建单走审批", "开一张单据", "审批流程"],
        "entries": [
            ("BaseEntityCurdService", "create4Bpm", "为 BPM 创建单据", "03-persistence.md §8.0.4"),
        ],
    },
    "bill_save_draft": {
        "keywords": ["保存草稿", "存草稿", "暂存单据", "草稿"],
        "entries": [
            ("BpmAppService", "saveDraft", "保存草稿", "06-components.md §7.5.1"),
        ],
    },
    "bill_submit": {
        "keywords": ["提交草稿", "提交审批", "送审", "提交单据", "发起审批", "提交"],
        "entries": [
            ("BpmAppService", "submit", "提交", "06-components.md §7.5.1"),
        ],
    },
    "bill_takeback": {
        "keywords": ["撤回单据", "取回", "撤回已提交"],
        "entries": [
            ("BpmAppService", "takeBack", "取回", "06-components.md §7.5.2"),
            ("BpmAppService", "repeal", "撤销", "06-components.md §7.5.2"),
        ],
    },
    "bill_nullify": {
        "keywords": ["作废单据", "作废", "nullify"],
        "entries": [
            ("BpmAppService", "stop", "终止流程（作废相关）", "06-components.md §7.5.2"),
        ],
    },
    "expression_evaluate": {
        "keywords": ["执行表达式", "主动执行", "代码里执行", "执行一个表达式", "算一下公式", "表达式求值", "跑一遍表达式"],
        "entries": [
            ("ExpressionEvaluator", "eval", "运行时执行表达式", "04-expression.md §5.1"),
        ],
    },
    "expression_transform": {
        "keywords": ["编译表达式", "转成可执行形式", "表达式转代码", "生成executableExpr", "把表达式编译"],
        "entries": [
            ("ExpressionAppService", "transform", "设计态→可执行", "04-expression.md §3.3"),
            ("ExpressionCodeGenerator", "generateCode", "生成 Java 代码", "04-expression.md §4.2"),
        ],
    },
    "expression_check": {
        "keywords": ["校验表达式", "表达式是否合法", "检查表达式"],
        "entries": [
            ("ExpressionAppService", "check", "校验表达式", "04-expression.md §3.3"),
        ],
    },
    "system_variable_value": {
        "keywords": ["系统变量", "取系统变量值", "系统变量当前值"],
        "entries": [
            ("ExpressionAppService", "getSystemVariableResult", "取变量值", "04-expression.md §3.3"),
            ("ExpressionAppService", "getSystemVariableResultBySystemFunctionName", "按函数名取", "04-expression.md §3.3"),
        ],
    },
    "entity_page_query": {
        "keywords": ["分页查询", "分页拿数据", "翻页", "取第N页", "限制条数", "分页"],
        "entries": [
            ("AllInOneBaseDao", "selectPageByConditions", "分页查询", "03-persistence.md §3.5"),
            ("AllInOneBaseDao", "selectPageByComplexConditions", "复杂条件分页", "03-persistence.md §3.5"),
        ],
    },
    "entity_page_no_count": {
        "keywords": ["不需要总条数", "不要总条数", "不要总数", "不用查总数", "不用总数", "总条数", "跳过总数", "别count"],
        "entries": [
            ("PageInfo", "setNeedTotal", "关闭总数统计", "03-persistence.md §3.5"),
            ("PageInfo", "setNeedMore", "只判断是否还有更多", "03-persistence.md §3.5"),
        ],
    },
    "entity_batch_create": {
        "keywords": ["批量插入", "批量新增", "一次性插多条", "批量入库", "bulk insert"],
        "entries": [
            ("AllInOneBaseDao", "createBatch", "批量新增", "03-persistence.md §3.1"),
            ("BaseEntityCurdService", "createBatch", "批量新增", "03-persistence.md §8.0"),
        ],
    },
    "entity_update_columns": {
        "keywords": ["只更新某几个字段", "局部更新", "只改一个字段", "改某几列"],
        "entries": [
            ("AllInOneBaseDao", "updateColumns", "指定列更新", "03-persistence.md §3.1"),
        ],
    },
    "entity_update_ignore_version": {
        "keywords": ["跳过乐观锁", "忽略版本校验", "不校验版本"],
        "entries": [
            ("AllInOneBaseDao", "updateColumnsIgnoreVersion", "指定列+忽略版本", "03-persistence.md §3.1"),
            ("AllInOneBaseDao", "versionNoUpdateIgnoreVersion", "不递增版本+忽略", "03-persistence.md §3.1"),
        ],
    },
    "entity_column_projection": {
        "keywords": ["只查部分列", "别 select *", "列裁剪", "只取需要的列"],
        "entries": [
            ("AllInOneBaseDao", "selectListPropertiesByConditions", "只查指定列", "03-persistence.md §3.4"),
            ("AllInOneBaseDao", "selectListExcludeByConditions", "排除指定列", "03-persistence.md §3.4"),
        ],
    },
    "entity_aggregate_func": {
        "keywords": ["聚合统计", "求和", "count一下", "算平均值", "统计总数"],
        "entries": [
            ("AllInOneBaseDao", "selectListFuncByComplexConditions", "聚合函数查询", "03-persistence.md §3.6"),
        ],
    },
    "entity_join_query": {
        "keywords": ["关联查询", "连表查", "两张表一起查", "join", "连表"],
        "entries": [
            ("BaseEntityCurdService", "dynamicJoinSelect", "动态 JOIN", "03-persistence.md §8.0.3"),
            ("BaseEntityCurdService", "dynamicCountJoinSelect", "JOIN 计数", "03-persistence.md §8.0.3"),
        ],
    },
    "distributed_lock": {
        "keywords": ["分布式锁", "加锁", "并发控制", "互斥执行", "防止并发冲突"],
        "entries": [
            ("DistributedLockFactory", "newLock", "新建锁", "06-components.md §6.1"),
            ("DistributedLockFactory", "newLockIgnoreTenant", "跨租户锁", "06-components.md §6.1"),
        ],
    },
    "http_call": {
        "keywords": ["调外部接口", "HTTP请求", "调第三方", "请求外部系统", "调别人的API"],
        "entries": [
            ("HttpClientUtil", "get", "GET 请求", "06-components.md §5.1"),
            ("HttpClientUtil", "post", "POST 请求", "06-components.md §5.1"),
        ],
    },
    "generic_invoke": {
        "keywords": ["泛化调用", "没有接口Class", "没有接口", "接口Class", "动态调服务", "按名字调方法", "不知道Class怎么调"],
        "entries": [
            ("AppServiceProxy", "invokeAppService", "泛化单条", "05-interface-integration.md §4.2"),
            ("AppServiceProxy", "invokeAppServiceForList", "泛化列表", "05-interface-integration.md §4.2"),
        ],
    },
    "reliable_invoke": {
        "keywords": ["可靠投递", "可靠调用", "失败补偿", "跨应用可靠"],
        "entries": [
            ("AppServiceProxy", "reliableInvokeAppService", "可靠调用", "05-interface-integration.md §4.2.2"),
            ("AppServiceReliableInvoker", "compensateReliableInvoke", "补偿", "05-interface-integration.md §4.2.2"),
        ],
    },
    "dubbo_proxy": {
        "keywords": ["Dubbo代理", "取Dubbo服务", "Dubbo跨服务", "getProxy"],
        "entries": [
            ("DubboFactory", "getProxy", "取 Dubbo 代理", "05-interface-integration.md §4.1"),
        ],
    },
    "entity_excel_import": {
        "keywords": ["Excel导入", "导Excel", "从表格导入", "批量导入数据", "Excel灌数据"],
        "entries": [
            ("BaseEntityCurdService", "importEntityInitData", "实体 Excel 导入", "03-persistence.md §8.0.5"),
        ],
    },
    "unique_check": {
        "keywords": ["唯一性校验", "字段唯一", "查重", "校验唯一"],
        "entries": [
            ("BaseEntityCurdService", "uniqueFieldCheck", "唯一性校验", "03-persistence.md §8.0.5"),
        ],
    },
    "anti_recommit": {
        "keywords": ["防重复提交", "防止重复点击", "表单提交两次", "重复提交"],
        "entries": [
            ("AntiReCommit", "annotation", "防重复提交注解", "03-persistence.md §10A.1"),
        ],
    },
    "idempotent": {
        "keywords": ["幂等", "幂等保护", "重复执行结果一致"],
        "entries": [
            ("Idempotent", "annotation", "幂等注解", "03-persistence.md §10A.1"),
        ],
    },
    "long_to_string_json": {
        "keywords": ["雪花ID", "传前端", "传给前端", "Long转String", "丢精度", "不丢精度", "精度丢失", "大整数精度", "ID精度"],
        "entries": [
            ("JsonUtils", "toJsonLongToString", "Long 转 String 序列化", "06-components.md §7.1.2"),
        ],
    },
    "default_value_expression": {
        "keywords": ["默认值表达式", "自动算默认值", "创建前算默认值"],
        "entries": [
            ("BaseEntityCurdService", "recursiveDefaultValue", "递归默认值", "03-persistence.md §8.0.1"),
        ],
    },
    "custom_expression_function": {
        "keywords": ["自定义表达式函数", "自定义函数", "扩展表达式函数", "自定义一个表达式", "扩展函数", "注册函数", "加一个函数"],
        "entries": [
            ("FunctionClass", "annotation", "函数类注解", "04-expression.md §4.0"),
            ("Function", "annotation", "函数方法注解", "04-expression.md §4.0"),
        ],
    },
    "custom_code_task": {
        "keywords": ["自定义生成任务", "扩展代码生成", "注册CodeTask", "加生成任务"],
        "entries": [
            ("PluginDefinition", "getCodeTasks", "插件注册 CodeTask", "02-codegen.md §2.3"),
        ],
    },
}


def _grams(s):
    """中文按字符 bigram 切分；ASCII 词按原样保留。"""
    s = s.lower()
    out = set()
    # ASCII 词
    for w in re.findall(r"[a-z0-9_#\.]+", s):
        if len(w) >= 2:
            out.add(w)
    # 中文字符 bigram
    han = re.findall(r"[\u4e00-\u9fff]+", s)
    for run in han:
        if len(run) == 1:
            out.add(run)
        else:
            for i in range(len(run) - 1):
                out.add(run[i:i + 2])
        # 单字兜底（长度 >=2 的串也加入，便于短词命中）
        if len(run) <= 4:
            out.add(run)
    return out


def _sim(kw, q):
    """关键词与 query 的相似度，返回 0~1。

    1) 精确子串 → 1.0
    2) 否则按 bigram 覆盖率
    """
    k = kw.lower()
    if k in q or q in k:
        return 1.0
    kg, qg = _grams(k), _grams(q)
    if not kg:
        return 0.0
    inter = kg & qg
    if not inter:
        return 0.0
    return len(inter) / len(kg)


def search(query, top_k=5, forbidden=None, min_sim=0.5):
    """中文友好的检索：bigram 覆盖率打分 + forbidden 后置过滤。

    forbidden: 通配模式列表（如 "*delete*"），命中则丢弃该结果。
    min_sim: 关键词相似度阈值，低于则不计分。
    """
    q = query.lower()
    scored = []
    for cap, spec in INDEX.items():
        score = 0.0
        hits = []
        for kw in spec["keywords"]:
            s = _sim(kw, q)
            if s >= min_sim:
                # 长关键词更有区分度，权重随长度增长
                score += s * (10 + min(len(kw), 8))
                hits.append(kw)
        # 类名/方法名直接命中
        for cls, meth, note, ev in spec["entries"]:
            if cls.lower() in q or meth.lower() in q:
                score += 20
        if score > 0:
            scored.append((score, cap, spec, hits))
    scored.sort(key=lambda x: -x[0])

    # ★ forbidden 后置过滤（语义匹配，避免 "JsonUtils#toJson" 误杀 "toJsonLongToString"）
    forb = list(forbidden or [])
    out = []
    for score, cap, spec, hits in scored:
        for cls, meth, note, ev in spec["entries"]:
            item = {
                "capability": cap,
                "iface": cls,
                "method": meth,
                "note": note,
                "evidence": ev,
                "score": round(score, 2),
            }
            if _is_forbidden(item, forb):
                continue
            out.append(item)
    return out[:top_k]


def _is_forbidden(item, forbidden):
    """与 eval_baseline.forbidden_hit 同一语义：精确比方法名/类名，含 # 时精确比 Class#method。"""
    if not forbidden:
        return False
    meth = (item.get("method") or "").lstrip("@").lower()
    cls = (item.get("iface") or "").lstrip("@").lower()
    label = f"{cls}#{meth}"
    for pat in forbidden:
        p = pat.lower()
        star = "*" in p
        p2 = p.replace("*", "")
        if not p2:
            continue
        if "#" in p2:
            if label == p2 or (star and p2 in label):
                return True
        else:
            if p2 == meth or p2 == cls:
                return True
            if star and p2 in cls:
                return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search")
    ap.add_argument("--eval", action="store_true")
    a = ap.parse_args()

    if a.search:
        print(json.dumps(search(a.search), ensure_ascii=False, indent=1))
        return

    if a.eval:
        sys.path.insert(0, os.path.join(ROOT, "scripts/research"))
        from eval_baseline import norm, hit_any, hit_any_cap, forbidden_hit, classify_error

        ev = json.load(open(os.path.join(ROOT,
            "core/research/platform-dev-system/evaluation/intent-capability-set-v1.json"), encoding="utf-8"))
        pos = ev["positive"]
        n = len(pos); t1 = t5 = 0; rr = 0.0; errs = {}; fvs = []
        for e in pos:
            hits = search(e["intent"], top_k=5, forbidden=e.get("forbidden"))
            a1 = bool(hits) and hit_any_cap(hits[:1], e)
            a5 = bool(hits) and hit_any_cap(hits, e)
            r = 0.0
            for rank, h in enumerate(hits, 1):
                if hit_any_cap([h], e):
                    r = 1.0 / rank; break
            t1 += a1; t5 += a5; rr += r
            if forbidden_hit(hits, e.get("forbidden")):
                fvs.append(e["id"])
            err = classify_error(e, hits, a1, a5)
            if err: errs[err] = errs.get(err, 0) + 1

        print("=" * 70)
        print("开发能力索引 —— 基线复测")
        print("=" * 70)
        print(f"样本数     : {n}")
        print(f"Top-1 命中 : {t1}/{n} = {t1/n:.1%}")
        print(f"Top-5 命中 : {t5}/{n} = {t5/n:.1%}")
        print(f"MRR        : {rr/n:.3f}")
        print(f"forbidden  : {len(fvs)} {fvs if fvs else ''}")
        print()
        print("错误类型：")
        for k, v in sorted(errs.items(), key=lambda x: -x[1]):
            print(f"  {k:20s} {v}")
        print()
        print("未命中明细：")
        for e in pos:
            hits = search(e["intent"], top_k=5)
            if not hit_any_cap(hits, e):
                got = f"{hits[0]['iface']}#{hits[0]['method']}" if hits else "(无结果)"
                print(f"  ❌ {e['id']:8s} {e['intent'][:26]:28s} 期望={e['expected_top1'][0][:36]:38s} 实际={got[:36]}")


if __name__ == "__main__":
    main()
