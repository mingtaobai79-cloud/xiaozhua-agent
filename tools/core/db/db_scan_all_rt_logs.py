# -*- coding: utf-8 -*-
"""只读：横扫所有应用库的 udc_rt_app_log，搜"主键/违反/约束/Duplicate/1062"类错误。
这是跨环境定位"违反主键约束"真实发生的最后一张网。"""
import datetime
import pathlib
import pymysql

ENV = pathlib.Path("<HERMES_HOME>/skills/devops/seeyon-low-code-environment/.env")
PATTERNS = ["%主键%", "%违反%", "%约束%", "%Duplicate%", "%duplicate%"]


def load_env():
    cfg = {}
    for ln in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or "=" not in ln:
            continue
        k, v = ln.split("=", 1)
        cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def ts(ms):
    try:
        return datetime.datetime.fromtimestamp(int(ms) / 1000).strftime("%m-%d %H:%M")
    except Exception:
        return str(ms)


def main():
    cfg = load_env()
    c = pymysql.connect(host=cfg["SEEYON_DB_HOST"], port=3306, user=cfg["SEEYON_DB_USERNAME"],
                        password=cfg["SEEYON_DB_PASSWORD"], charset="utf8mb4",
                        connect_timeout=10, read_timeout=900)
    cur = c.cursor()
    cur.execute("""SELECT table_schema FROM information_schema.tables
                   WHERE table_name='udc_rt_app_log' ORDER BY table_schema""")
    dbs = [r[0] for r in cur.fetchall()]
    print("含 udc_rt_app_log 的库数 =", len(dbs))

    total_hits = 0
    for db in dbs:
        try:
            cur.execute("SELECT COUNT(*) FROM `%s`.udc_rt_app_log" % db)
            n = cur.fetchone()[0]
        except Exception as e:
            print("   skip %s (%s)" % (db, str(e)[:60]))
            continue
        if not n:
            continue
        where = " OR ".join(["error_msg LIKE %s"] * len(PATTERNS))
        try:
            cur.execute("SELECT COUNT(*) FROM `%s`.udc_rt_app_log WHERE %s" % (db, where), PATTERNS)
            h = cur.fetchone()[0]
        except Exception as e:
            print("   query fail %s (%s)" % (db, str(e)[:60]))
            continue
        if h:
            total_hits += h
            print("### [%s] rows=%s 命中=%s" % (db, n, h))
            cur.execute("""SELECT log_start_time, source_caption, micro_flow_code, activity_caption,
                                  LEFT(COALESCE(error_msg,''),220), data_id
                           FROM `%s`.udc_rt_app_log WHERE %s
                           ORDER BY log_start_time DESC LIMIT 6""" % (db, where), PATTERNS)
            for r in cur.fetchall():
                print("    %s | %s | %s | %s | %s | %s" % (ts(r[0]), r[1], r[2], r[3], r[4], r[5]))
        else:
            print("    [%s] rows=%s 无命中" % (db, n))
    print("\n命中总数 =", total_hits)
    c.close()


if __name__ == "__main__":
    main()
