# -*- coding: utf-8 -*-
"""只读：在平台 i18n 资源表里搜"主键/违反/唯一"文案。"""
import pathlib
import pymysql

ENV = pathlib.Path("<HERMES_HOME>/skills/devops/xiaozhua-low-code-environment/.env")
CANDIDATES = [
    ("app_common_test2", ["i18n_resource", "i18n_default_resource"]),
    ("udc_test2", ["udc_resource", "ctp_manager_resource"]),
    ("ctp_user_test2", ["ctp_resource"]),
]


def load_env():
    cfg = {}
    for ln in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or "=" not in ln:
            continue
        k, v = ln.split("=", 1)
        cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def main():
    cfg = load_env()
    c = pymysql.connect(host=cfg["XIAOZHUA_DB_HOST"], port=3306, user=cfg["XIAOZHUA_DB_USERNAME"],
                        password=cfg["XIAOZHUA_DB_PASSWORD"], charset="utf8mb4",
                        connect_timeout=10, read_timeout=600)
    cur = c.cursor()
    for db, tables in CANDIDATES:
        for t in tables:
            try:
                cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name=%s", (db, t))
                if not cur.fetchone()[0]:
                    continue
                cur.execute("SHOW COLUMNS FROM `%s`.`%s`" % (db, t))
                cols = [r[0] for r in cur.fetchall()]
                txt = [x for x in cols if any(k in x.lower() for k in ("value", "text", "content", "msg", "name", "code"))]
                print("### %s.%s cols=%s" % (db, t, cols[:14]))
                for col in txt:
                    try:
                        cur.execute("SELECT COUNT(*) FROM `%s`.`%s` WHERE `%s` LIKE %%s" % (db, t, col), ("%主键%",))
                        n = cur.fetchone()[0]
                    except Exception:
                        continue
                    if n:
                        print("   >> %s.%s 命中 主键: %d" % (t, col, n))
                        cur.execute("SELECT `%s` FROM `%s`.`%s` WHERE `%s` LIKE %%s LIMIT 5" % (col, db, t, col), ("%主键%",))
                        for r in cur.fetchall():
                            print("      ", str(r[0])[:220])
                    try:
                        cur.execute("SELECT COUNT(*) FROM `%s`.`%s` WHERE `%s` LIKE %%s" % (db, t, col), ("%违反%",))
                        n2 = cur.fetchone()[0]
                    except Exception:
                        continue
                    if n2:
                        print("   >> %s.%s 命中 违反: %d" % (t, col, n2))
                        cur.execute("SELECT `%s` FROM `%s`.`%s` WHERE `%s` LIKE %%s LIMIT 5" % (col, db, t, col), ("%违反%",))
                        for r in cur.fetchall():
                            print("      ", str(r[0])[:220])
            except Exception as e:
                print("   skip %s.%s : %s" % (db, t, e))
    c.close()


if __name__ == "__main__":
    main()
