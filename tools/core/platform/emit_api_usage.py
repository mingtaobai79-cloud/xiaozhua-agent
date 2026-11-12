#!/usr/bin/env python3
"""生成「接口使用卡」：每个 AppService 接口一页，拿到就能调。

解决什么：现在有签名表（传什么类型）、DTO 字段表（字段有什么）、流转表（背后干什么），
但三份分开，写一段扩展代码要在三个文件间跳。使用卡把它们合成一页：

  接口全名 + 注解 + 实现类
  ↓ 每个方法
  签名 → 入参 DTO 逐字段（含嵌套标注）→ 返回 DTO 逐字段 → 流转第一步
  ↓ 接口级
  泛化调用模板（interfaceName/methodName/paramType/genericType/paramJson 五个值怎么填）

诚实边界：字段语义从字节码只能拿到「名字 + 类型」，**没有注释和业务含义**。
本工具只做结构化，不编造语义；能确定的（嵌套 DTO、集合元素类型、常量默认值）才标注。

用法：
  python tools/core/platform/emit_api_usage.py \
      --interfaces <interfaces.json> --impl-map <impl-map.json> \
      --flow-dir <service-flow 目录> --emit-dir <api-usage 目录>
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

REQ = re.compile(r"(?:SingleRequest|ListRequest|PageRequest)<\s*([\w.$]+)\s*>")
RESP = re.compile(r"(?:SingleResponse|ListResponse|PageResponse)<\s*([\w.$]+)\s*>")
RE_FLOW_CLASS = re.compile(r"^## `([\w$]+)`\s*$", re.M)
RE_FLOW_METHOD = re.compile(r"^### `([\w$]+)\(\)`\s*$", re.M)
RE_FLOW_LINE = re.compile(r"^- \*\*(\w+)\*\* `([\w$]+)` → (.+)$")

DOMAIN_OF = [
    ("bpm", "bpm"), ("organization", "organization"), ("org", "organization"),
    ("udc", "udc"), ("cip", "cip"), ("ctp", "ctp"), ("app", "app"),
    ("cdp", "cdp"), ("m5", "m5"), ("portal", "portal"), ("ai", "ai"),
    ("boot", "boot"), ("formula", "formula"), ("file", "file"),
]


def domain_of(fq: str) -> str:
    parts = fq.split(".")
    for p in parts[:4]:
        for key, dom in DOMAIN_OF:
            if p == key:
                return dom
    return "other"


def parse_flow(md: str) -> dict[tuple[str, str], list[str]]:
    out: dict[tuple[str, str], list[str]] = {}
    cur_cls = cur_meth = None
    for line in md.splitlines():
        m = RE_FLOW_CLASS.match(line)
        if m:
            cur_cls, cur_meth = m.group(1), None
            continue
        m = RE_FLOW_METHOD.match(line)
        if m and cur_cls:
            cur_meth = m.group(1)
            out[(cur_cls, cur_meth)] = []
            continue
        m = RE_FLOW_LINE.match(line)
        if m and cur_cls and cur_meth:
            out[(cur_cls, cur_meth)].append(
                f"{m.group(1)} `{m.group(2)}` → {m.group(3).split(',')[0].strip()}")
    return out


def field_rows(cls: dict | None, seen: set[str], depth: int = 0,
               validations: dict | None = None, fq: str = "",
               meta: dict | None = None) -> list[str]:
    """DTO 字段表。嵌套 DTO 标出来但不再展开（避免爆炸），指向其自身卡片。"""
    if not cls:
        return ["  （字段不可得：类不在索引里）"]
    vmap = (validations or {}).get(fq) or {}
    fields = [f for f in (cls.get("fields") or [])
              if not f["name"].startswith("serialVersionUID")
              and "static" not in (f.get("modifiers") or [])]
    if not fields:
        return ["  （无字段）"]
    rows = []
    for f in fields:
        t = f["type"]
        note = ""
        if "List<" in t or "Set<" in t:
            inner = re.search(r"[<\[]([\w.$]+)[>\]]", t)
            if inner:
                note = f"元素 `{inner.group(1).split('.')[-1]}`"
        elif t.endswith("Dto") or t.endswith("DTO"):
            note = "嵌套 DTO"
        mm = (meta or {}).get(fq, {})
        fm = (mm.get("fields") or {}).get(f["name"], {}) if mm else {}
        cn = fm.get("value") or ""
        ex = fm.get("example") or ""
        ds = fm.get("description") or ""
        rel = fm.get("relationDto") or ""
        ann = vmap.get(f["name"]) or []
        req = ""
        if any(x in ann for x in ("NotNull", "NotBlank", "NotEmpty")):
            req = " **[必填]**"
        elif ann:
            req = " [" + ",".join(ann) + "]"
        tail = []
        if cn:
            tail.append(cn)
        if ex:
            tail.append(f"例:{ex}")
        if ds:
            tail.append(ds)
        if rel:
            tail.append(f"关联 {rel.split('.')[-1]}")
        if note:
            tail.append(note)
        rows.append(f"  {f['name']:26s} {t.replace('java.lang.', '').replace('java.util.', ''):22s}"
                    f"{req}"
                    + ("   ← " + " · ".join(tail) if tail else ""))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--impl-map", default=None)
    ap.add_argument("--flow-dir", default=None)
    ap.add_argument("--validations", default=None,
                    help="scan_dto_validations.py 的产物，用来标 [必填]")
    ap.add_argument("--dto-meta", default=None,
                    help="scan_dto_meta.py 的产物：平台自己写的字段中文名/示例/说明")
    ap.add_argument("--emit-dir", required=True)
    ap.add_argument("--only-appservice", action="store_true", default=True)
    a = ap.parse_args()

    d = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = d["classes"]

    impl_of: dict[str, str] = {}
    for fq, c in cs.items():
        for i in (c.get("implements") or []):
            base = i.split("<")[0]
            impl_of[base] = fq.split(".")[-1]
    if a.impl_map:
        m = json.loads(Path(a.impl_map).read_text(encoding="utf-8"))["map"]
        for iface, impls in m.items():
            if impls:
                impl_of.setdefault(iface, impls[0]["impl"])

    flow: dict[tuple[str, str], list[str]] = {}
    if a.flow_dir:
        for f in Path(a.flow_dir).glob("*.md"):
            flow.update(parse_flow(f.read_text(encoding="utf-8", errors="replace")))

    validations: dict = {}
    if a.validations:
        vp = Path(a.validations)
        if vp.exists():
            validations = json.loads(vp.read_text(encoding="utf-8"))["map"]

    meta: dict = {}
    if a.dto_meta:
        mp = Path(a.dto_meta)
        if mp.exists():
            meta = json.loads(mp.read_text(encoding="utf-8"))["map"]

    svc = {f: c for f, c in cs.items()
           if c.get("kind") == "interface" and f.split(".")[-1].endswith("AppService")}

    by_dom: dict[str, list[str]] = defaultdict(list)
    n_meth = n_flow = 0
    for fq in sorted(svc):
        c = svc[fq]
        short = fq.split(".")[-1]
        impl = impl_of.get(fq, "")
        lines = [f"## `{short}`", "", f"`{fq}`", ""]
        meta_parts = [f"实现 `{impl}`" if impl else "**实现未找到**",
                      f"{len(c['methods'])} 个方法"]
        if c.get("annotations"):
            meta_parts.append("注解 " + ", ".join(f"`@{x}`" for x in c["annotations"][:3]))
        lines += [" · ".join(meta_parts), ""]
        for m in c["methods"]:
            sig = m.get("signature", "")
            n_meth += 1
            req = REQ.search(sig)
            resp = RESP.search(sig)
            dto = req.group(1) if req else ""
            ret = resp.group(1) if resp else ""
            ret_short = ret.split(".")[-1] if ret else ("void" if " void " in sig else "?")
            dto_short = dto.split(".")[-1] if dto else ""
            head = f"### `{m['name']}` → `{ret_short}`"
            lines += [head, ""]
            if dto_short:
                lines += [f"入参 `{dto_short}`"
                          + (f"（`{dto}`）" if dto else ""), ""]
                lines += field_rows(cs.get(dto), set(), validations=validations, fq=dto, meta=meta)
                lines.append("")
            elif " void " in sig or "(" in sig:
                bare = re.findall(r"\(([^)]*)\)", sig)
                if bare and bare[0].strip():
                    lines += [f"入参（裸参数）：`{bare[0]}`", ""]
            if ret_short not in ("?", "void"):
                rc = cs.get(ret)
                if rc and (rc.get("fields") or []):
                    lines += [f"返回 `{ret_short}` 字段", ""]
                    lines += field_rows(rc, set(), validations=validations, fq=ret, meta=meta)
                    lines.append("")
            chain = flow.get((impl, m["name"]), []) if impl else []
            if chain:
                n_flow += 1
                lines += ["流转（反编译方法体）：", ""]
                lines += [f"  {x}" for x in chain[:8]]
                if len(chain) > 8:
                    lines.append(f"  … 另 {len(chain)-8} 条")
                lines.append("")
        # 泛化调用模板
        sample = c["methods"][0] if c["methods"] else None
        if sample:
            sreq = REQ.search(sample.get("signature", ""))
            lines += ["泛化调用（`AppServiceProxy.invokeAppService`）：", "", "```",
                      f'interfaceName = "{fq}"',
                      f'methodName    = "{sample["name"]}"',
                      'paramType     = "com.seeyon.boot.transport.SingleRequest"',
                      f'genericType   = "{sreq.group(1) if sreq else ""}"',
                      'paramJson     = {"<字段>":"<值>"}   ← 对应上面入参 DTO 的字段',
                      "returnJson    = true              ← 要 JSON 字符串时开",
                      "```", ""]
        by_dom[domain_of(fq)].append("\n".join(lines))

    out_dir = Path(a.emit_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    for dom, pages in sorted(by_dom.items()):
        p = out_dir / f"{dom}.md"
        body = [f"# 接口使用卡 · {dom}（{len(pages)} 个接口）", "",
                "> 自动生成，勿手改。`tools/core/platform/emit_api_usage.py` 重跑。",
                "> 字段语义只有「名字 + 类型」，字节码没有注释——**别猜业务含义，先按名字理解再实测**。",
                "",
                "## 怎么调（两种方式，先看这个）",
                "",
                "### 方式一：Spring 注入（推荐）",
                "",
                "```java",
                "@Autowired",
                "private BpmAppService bpmAppService;            // 接口全名见每个卡片的第二行",
                "",
                "BpmSendDto dto = new BpmSendDto();",
                "dto.setTemplateCode(\"xxx\");                      // 字段清单见卡片「入参」段",
                "dto.setCurrentUserId(123L);",
                "",
                "SingleResponse<BpmSendResultDto> r = bpmAppService.send(SingleRequest.from(dto));",
                "BpmSendResultDto result = r.getData().getContent();   // 取值链固定：getData().getContent()",
                "```",
                "",
                "### 方式二：泛化调用（不知道类型 / 动态模块 / 只拿到接口名字符串时）",
                "",
                "```java",
                "AppServiceInvokeDto d = new AppServiceInvokeDto();",
                "d.setInterfaceName(\"com.seeyon.bpm.api.common.BpmAppService\");",
                "d.setMethodName(\"send\");",
                "d.setParamType(\"com.seeyon.boot.transport.SingleRequest\");",
                "d.setGenericType(\"com.seeyon.bpm.dto.operation.openapi.BpmSendDto\");",
                "d.setParamJson(\"{\\\"templateCode\\\":\\\"xxx\\\",\\\"currentUserId\\\":123}\");",
                "d.setReturnJson(Boolean.TRUE);          // 想直接拿 JSON 字符串就开",
                "SingleResponse<Object> r = appServiceProxy.invokeAppService(SingleRequest.from(d));",
                "```",
                "",
                "**泛化调用怎么找到 Bean**（`CtpCustomerProxyAppServiceImpl.processServiceInvoke` 实证）：",
                "",
                "```",
                "1. getBean(接口名末段首字母小写)   BpmAppService → bpmAppService",
                "2. getBean(接口全名)",
                "3. ModuleAppBeanCache.getBean(接口名)",
                "4. getBean(动态 Bean 名)",
                "5. getBean(dto.getBeanName())      显式指定",
                "6. getBeansOfType(loadClass(接口名))  按类型找，跳过含 mock 的",
                "全找不到 → 抛 BOOT_4014（日志会打全 5 个参数）",
                "```",
                "",
                "### 卡片怎么读",
                "",
                "```",
                "## `接口短名`",
                "`接口全名`                        ← interfaceName 用这个",
                "实现 `XxxImpl` · N 个方法          ← 没有实现 = 平台运行时装配，别硬调",
                "### `方法名` → `返回 DTO`",
                "入参 `XxxDto`（全名）              ← genericType 用这个",
                "  字段  类型   ← 嵌套 DTO / 元素类型",
                "返回 `YyyDto` 字段",
                "流转（反编译方法体）                ← 这个方法实际动了什么",
                "```",
                "",
                ]
        body += pages
        p.write_text("\n".join(body), encoding="utf-8")
        total_bytes += p.stat().st_size
        print(f"  {dom:14s} {len(pages):4d} 接口  {p.stat().st_size//1024:5d} KB")

    print(f"\n{len(svc)} 个 AppService / {n_meth} 个方法 / {n_flow} 个有流转 "
          f"→ {out_dir}（合计 {total_bytes//1024//1024} MB）")
    if len(svc) < 300:
        print("ERR: 接口过少")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
