#!/usr/bin/env python3
"""从 UDC 构建产物 zip 出「实体可写性矩阵」，供写节点选实体前查。

解决两个会让写验证白跑的问题：
  ① 实体没有 create()  → 构建 40 秒 FAIL「找不到符号: 方法 create(SingleRequest<…Dto>)」
  ② 字段配了默认值表达式且 require_null=false → 传入值被无条件覆盖，永远看不到效果

用法：
    python entity_write_capability.py meta.zip
    python entity_write_capability.py meta.zip --out core/facts/udc/microflow/entity-write-capability.json
    python entity_write_capability.py <已解压目录>          # 也可以直接给解压后的根目录

zip 从哪来：构建日志 backBuild.log 第一屏的「构建元数据」地址
    <HOST>/service/udc/file/download?storageKey=metadata/udc/<appId>/<buildVersion>.zip

输出：
    {"entities": {短名: {has_create, expression_field_count, fields}},
     "entities_without_create": [...],
     "recommended": [...]}   # 有 create 且没有覆盖字段，优先拿来做写验证
"""
import argparse
import glob
import json
import os
import re
import sys
import tempfile
import zipfile

# executeExpressionXxx(list, <requireNull>, XxxDto::getField, this::expNNN, ...)
CALL = re.compile(
    r"executeExpression\w*\s*\(\s*[^,]+,\s*(true|false)\s*,"
    r"\s*\w+Dto::(get[A-Za-z0-9_]+)\s*,\s*this::(exp\d+)"
)
CREATE = re.compile(r"SingleResponse<Long>\s+create\s*\(\s*SingleRequest")


def _prepare(path):
    """返回可遍历的源码根目录；zip 解到临时目录。"""
    if os.path.isdir(path):
        return path, None
    if not zipfile.is_zipfile(path):
        sys.exit("既不是 zip 也不是目录: %s" % path)
    tmp = tempfile.mkdtemp(prefix="udcmeta_")
    with zipfile.ZipFile(path) as z:
        z.extractall(tmp)
    return tmp, tmp


def scan(root):
    root = os.path.abspath(root)

    # ① 有 create() 的实体。
    #    ★ 不要用 glob('**\\facade\\**\\*AppService.java')——Windows 下多段 ** 匹配不到，
    #      会得出「0 个实体有 create」的假结论。先粗匹配，再按路径子串过滤。
    has_create = set()
    for p in glob.glob(os.path.join(root, "**", "*AppService.java"), recursive=True):
        if "-facade" not in p:
            continue
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if CREATE.search(text):
            has_create.add(os.path.basename(p)[:-len("AppService.java")])

    # ② 每个实体 domain service 的默认值表达式（带 require_null）
    entities = {}
    for p in glob.glob(os.path.join(root, "**", "*Service.java"), recursive=True):
        norm = p.replace(os.sep, "/")
        if "/domain/service/" not in norm:
            continue
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if "preCreateBatch" not in text:
            continue
        name = os.path.basename(p)[:-len("Service.java")]
        fields = {}
        for req, getter, exp in CALL.findall(text):
            # getF03int -> f03int ; getUpdater -> updater
            field = getter[3].lower() + getter[4:]
            fields[field] = {"expr": exp, "require_null": req == "true"}
        entities[name] = {
            "has_create": name in has_create,
            "expression_field_count": len(fields),
            "fields": fields,
        }

    # 只在 domain service 里出现过、但 facade 没 create 的，补进表里便于核对
    for name in has_create - set(entities):
        entities[name] = {"has_create": True, "expression_field_count": 0, "fields": {}}

    good = []
    for name, info in sorted(entities.items()):
        if not info["has_create"]:
            continue
        risky = [f for f, d in info["fields"].items() if d["require_null"] is False]
        if not risky:
            good.append(name)

    return {
        "source": "UDC 构建产物 metadata zip（facade/api + domain/service）",
        "note": (
            "CREATE_ENTITY 编译成 XxxAppService.create(SingleRequest) —— 无 create 的实体不可用；"
            "字段配了默认值表达式且 require_null=false 时，preCreateBatch 会无条件覆盖传入值"
        ),
        "entities_without_create": sorted(n for n, i in entities.items() if not i["has_create"]),
        "recommended": good,
        "entities": dict(sorted(entities.items())),
    }


def self_check(result, *, min_entities=1):
    """三档阳性对照。返回问题列表，空=通过。

    扫错的形态**不是报错**，而是「所有实体 has_create=false」或「表达式数恒 0」——
    看起来完全合理，后果是 G34 拦掉全部流程（或一条不拦），没人会怀疑闸门。
    所以脚本必须自己发现这件事并以非零退出码报出来。
    """
    problems = []
    ents = result.get("entities") or {}

    # ① 有 create 的实体数 > 0。为 0 一定是口径错，不是真的一个都没有。
    n_create = sum(1 for i in ents.values() if i.get("has_create"))
    if n_create == 0:
        problems.append(
            "① 有 create 的实体数为 0 —— 一定是 glob 口径错（Windows 多段 ** 匹配不到，"
            "或按 'facade' 过滤但目录名是 '<app>-facade'），不是真没有")
    elif n_create < min_entities:
        problems.append("① 有 create 的实体数 %d < 期望下限 %d" % (n_create, min_entities))

    # ② 已知有 create 的实体必须在集合里（阳性样本）
    if ents and not any(i.get("has_create") for i in ents.values()):
        problems.append("② 找不到任何阳性样本实体")

    # ③ 必须至少扫出一个被覆盖字段，否则 G35 永远不报
    n_risky = sum(1 for i in ents.values()
                  for d in (i.get("fields") or {}).values()
                  if d.get("require_null") is False)
    if ents and n_risky == 0:
        problems.append(
            "③ 被 require_null=false 覆盖的字段数为 0 —— G35 永远不会触发，"
            "检查 executeExpression 正则是否匹配到")

    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="UDC 实体可写性矩阵")
    ap.add_argument("path", help="metadata zip 或已解压目录")
    ap.add_argument("--out", default="", help="输出 JSON 路径（默认只打印）")
    args = ap.parse_args(argv)

    root, tmp = _prepare(args.path)
    try:
        result = scan(root)
    finally:
        if tmp is None:
            pass
        # 临时目录不主动删，失败时方便人工核对；系统会清

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)

    ents = result["entities"]
    print("实体 %d 个 | 有 create %d | 无 create %d"
          % (len(ents), len([1 for i in ents.values() if i["has_create"]]),
             len(result["entities_without_create"])))
    if result["entities_without_create"]:
        print("无 create（不可挂写节点）:", ", ".join(result["entities_without_create"]))
    print()
    print("%-28s %-8s %-6s %s" % ("实体", "create", "表达式", "会被覆盖的字段"))
    for name, info in ents.items():
        risky = [f for f, d in info["fields"].items() if d["require_null"] is False]
        print("%-28s %-8s %-6d %s"
              % (name, "Y" if info["has_create"] else "-",
                 info["expression_field_count"], ",".join(sorted(risky)[:8]) or "-"))
    print()
    print("可直接用于写验证的实体（有 create 且无覆盖字段）:",
          ", ".join(result["recommended"]) or "（无）")

    # 三档自检不通过 → 非零退出码（脚本无 exit = 无闸门）
    checks = self_check(result)
    if checks:
        print()
        print("★ 自检未通过，这张表不可用：")
        for c in checks:
            print("   ", c)
        return 2

    if args.out:
        print("已写:", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
