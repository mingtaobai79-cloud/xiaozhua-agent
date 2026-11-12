# -*- coding: utf-8 -*-
"""只读：①udc_operation_log 最近记录 ②实体元数据表 → 表名映射（合同档案/变更 相关实体）"""
import pathlib
import pymysql

ENV = pathlib.Path("<HERMES_HOME>/skills/devops/seeyon-low-code-environment/.env")
PLAT = "udc_test2"


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
    c = pymysql.connect(host=cfg["SEEYON_DB_HOST"], port=int(cfg.get("SEEYON_DB_PORT", 3306)),
                        user=cfg["SEEYON_DB_USERNAME"], password=cfg["SEEYON_DB_PASSWORD"],
                        database=PLAT, charset="utf8mb4", connect_timeout=10, read_timeout=300)
    cur = c.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema=%s "
                "AND (table_name LIKE '%%entity%%' OR table_name LIKE '%%meta%%') ORDER BY table_name", (PLAT,))
    print("### 元数据相关表")
    for r in cur.fetchall():
        print("   ", r[0])

    print("\n### udc_operation_log 结构")
    cur.execute("SHOW CREATE TABLE udc_operation_log")
    print(cur.fetchone()[1][:1400])
    cur.execute("SELECT * FROM udc_operation_log ORDER BY id DESC LIMIT 3")
    print("cols:", [d[0] for d in cur.description])
    for r in cur.fetchall():
        print("   ", str(r)[:400])
    c.close()


if __name__ == "__main__":
    main()
