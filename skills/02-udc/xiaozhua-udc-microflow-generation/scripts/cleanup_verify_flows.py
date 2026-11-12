#!/usr/bin/env python
"""验收流程收尾：删临时流程（含 DRAFT）+ 清测试数据 + 重建 + 轮询到终态。

为什么要有这个脚本：这一步每轮验证都要跑，手写四遍就有四遍差异；
而且它必须在「长跑之后」还能被执行 —— 放在 scratch/ 里的脚本会被清掉。

用法（在仓库根目录执行）：

    python <HERMES_HOME>/skills/udc/xiaozhua-udc-microflow-generation/scripts/\
cleanup_verify_flows.py --marks p5,p6 --tables-table migration_1962926556161096741 \
        --where "task_id LIKE 'P6%'" --where "source_table LIKE 'P6%'"

关键行为：
  1. 按名字前缀删流程时 **必须连 DRAFT 一起删** —— 发布失败会留下 DRAFT，
     而 sub_mf_candidates 只列 RELEASE，只用它会撞 UDC_MICROFLOW_0001 name already exists。
  2. 删流程 ≠ 停定时：必须再构建一次，否则调度器按缓存继续跑一两个周期。
  3. 清数据要在重建**之后**再复查一轮，确认行数不再增长。
"""
import argparse
import json
import os
import subprocess
import sys
import time

REPO = "<XIAOZHUA_AGENT_ROOT>"
CONN = "<HERMES_HOME>/skills/seeyon/01-platform/xiaozhua-low-code-environment"


def log(*a):
    print(*a)
    sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-id", default="8704025620829192834")
    ap.add_argument("--app-name", default="datamigration<应用ID>")
    ap.add_argument("--host", default="https://lowcode-test2.<客户组织>.com")
    ap.add_argument("--cookie-file", default="scratch/_ck.txt")
    ap.add_argument("--marks", default="p5,p6", help="流程名前缀，逗号分隔")
    ap.add_argument("--db", default="datamigration<应用ID>_test2")
    ap.add_argument("--entity-table", default="migration_1962926556161096741")
    ap.add_argument("--where", action="append", default=[], help="清数据的 WHERE 片段，可多个")
    ap.add_argument("--no-build", action="store_true", help="只删不改包（仅在无调度任务时用）")
    args = ap.parse_args()

    os.chdir(REPO)
    sys.path.insert(0, REPO)
    from components.udc.microflow.live_refs import LiveRefs
    from components.udc.microflow import deploy as DP
    from components.construction.p5_builder import PlatformBuilder
    from components.construction.p5_pipeline import _HttpAdapter

    ck = open(args.cookie_file).read().strip()
    lr = LiveRefs(args.host, ck)
    marks = tuple(m.strip().lower() for m in args.marks.split(",") if m.strip())

    q = ("mutation g($p: udcMicroflowSearchInputBody) { data0: udcMicroflowSearch(body: $p)"
         " { code data { content { id name state } } message } }")
    allmf = lr._content(lr._gql("udcMicroflowSearch",
        {"pageInfo": {"needTotal": True, "pageNumber": 1, "pageSize": 999,
                      "pages": 0, "total": 0},
         "params": {"appId": args.app_id}}, q)) or []
    hit = [it for it in allmf if (it.get("name") or "").lower().startswith(marks)]
    log("待删流程 %d 条（含 DRAFT）" % len(hit))
    for it in hit:
        log("  删", it.get("name"), it.get("state"), DP.delete(args.host, ck, it["id"]))

    for w in args.where:
        sql = ("DELETE FROM %s.%s WHERE %s" % (args.db, args.entity_table, w))
        r = subprocess.run(["python", "scripts/conn.py", "db", sql, "--write"],
                           cwd=CONN, capture_output=True, text=True)
        log("清数据 [%s] ->" % w, (r.stdout or r.stderr).strip().splitlines()[-1])

    if args.no_build:
        log("跳过重建（--no-build）：若流程带定时任务，调度器还会再跑一两个周期")
        return

    pb = PlatformBuilder(http=_HttpAdapter(host=args.host, cookie=ck), app_id=args.app_id,
                         poll_interval=10.0, timeout_s=900.0)
    dep = None
    for i in range(1, 13):
        try:
            dep = pb.trigger(deploy_type="RELEASE")
            break
        except Exception as e:  # 同应用不能并发构建
            if "UDC_DEPLOY_0002" not in str(e):
                raise
            log("  构建锁，等 30s（%d/12）" % i)
            time.sleep(30)
    log("deployId:", dep)
    t0, last = time.time(), None
    for _ in range(90):
        st = pb.deploy_status(dep) or {}
        s = st.get("state")
        if s != last:
            log("  [%4.0fs] state=%s" % (time.time() - t0, s))
            last = s
        if s in ("SUCCESS", "FAIL"):
            log("终态: %s | %.0fs" % (s, time.time() - t0))
            if s == "FAIL":
                log((st.get("msg") or "")[:600])
                sys.exit(2)
            break
        time.sleep(10)
    else:
        log("轮询超时（900s），不要当成功")
        sys.exit(3)

    log("★ 收尾未完成：再过满一个调度周期（约 5 分钟）复查行数仍为 0 才算干净")
    json.dump({"deploy_id": str(dep), "marks": list(marks)},
              open("_attic_pending/last_cleanup.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
