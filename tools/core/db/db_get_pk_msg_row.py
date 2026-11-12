# -*- coding: utf-8 -*-
"""只读：取出"违反主键约束"与"主键冲突"模板的完整 i18n 记录（key/bundle/source）。"""
import pathlib
import pymysql

ENV = pathlib.Path("<HERMES_HOME>/skills/devops/xiaozhua-low-code-environment/.env")


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
                        password=cfg["XIAOZHUA_DB_PASSWORD"], database="app_common_test2",
                        charset="utf8mb4", connect_timeout=10, read_timeout=600)
    cur = c.cursor()
    print("### cn_value='违反主键约束' 的记录")
    cur.execute("""SELECT id, bundle_name, resource_key, resource_type, parent_resource_key,
                          source_name, sub_bundle_name, cn_value, en_value
                   FROM i18n_default_resource WHERE cn_value='违反主键约束'""")
    for r in cur.fetchall():
        print("   ", str(r)[:600])

    print("\n### resource_key 含 PK/PRIMARY/DUPLICATE 的记录")
    cur.execute("""SELECT resource_key, cn_value, bundle_name, source_name FROM i18n_default_resource
                   WHERE resource_key LIKE '%PRIMARY%' OR resource_key LIKE '%DUPLICATE%'
                      OR resource_key LIKE '%PK%' OR cn_value LIKE '%主键冲突%' LIMIT 15""")
    for r in cur.fetchall():
        print("   %-52s | %-40s | %s | %s" % (r[0], str(r[1])[:40], r[2], r[3]))

    print("\n### i18n_resource(租户覆盖) 中同 key")
    cur.execute("""SELECT bundle_name, locale_name, resource_key, LEFT(resource_value,200), source_name
                   FROM i18n_resource WHERE resource_value LIKE '%违反主键%' OR resource_key LIKE '%PRIMARY%' LIMIT 15""")
    rows = cur.fetchall()
    print("   rows =", len(rows))
    for r in rows:
        print("   ", str(r)[:400])
    c.close()


if __name__ == "__main__":
    main()
