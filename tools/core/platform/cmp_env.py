# -*- coding: utf-8 -*-
"""对比 test2 / uat：状态(草稿/已生成) × 正文/附件/pdf 落库情况"""
import os, sys
for line in open(r'<HERMES_HOME>\skills\seeyon\01-platform\seeyon-low-code-environment\.env', encoding='utf-8'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1); os.environ[k] = v
sys.path.insert(0, r'<HERMES_HOME>\skills\seeyon\01-platform\seeyon-low-code-environment\scripts')
from env import load_env
import pymysql
cfg = load_env('test2'); m = cfg['mysql']
c = pymysql.connect(host=m['host'], port=int(m['port']), user=os.environ['SEEYON_DB_USERNAME'],
                    password=os.environ['SEEYON_DB_PASSWORD'], database='udc_test2', charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor)
def q(s, a=None):
    with c.cursor() as cur:
        cur.execute(s, a or ()); return cur.fetchall()

for DB in ('9000000000000000001_test2', '9000000000000000001_uat'):
    T = f"`{DB}`.htmbzxsc_m6352819929563555081"
    print("=" * 90)
    print(f"### {DB}")
    tot = q(f"SELECT COUNT(*) n FROM {T}")[0]['n']
    print(f"   总行数: {tot}")
    print("   --- 状态 × 正文/附件/pdf ---")
    for r in q(f"""SELECT status_type st, draft,
                    SUM(CASE WHEN zhengwenziduan='' THEN 1 ELSE 0 END) zw_kong,
                    SUM(CASE WHEN zhengwenziduan<>'' THEN 1 ELSE 0 END) zw_you,
                    SUM(CASE WHEN fujianziduan='' THEN 1 ELSE 0 END) fj_kong,
                    SUM(CASE WHEN fujianziduan<>'' THEN 1 ELSE 0 END) fj_you,
                    SUM(CASE WHEN zhhpdffj IS NULL OR zhhpdffj='' THEN 1 ELSE 0 END) pdf_kong,
                    SUM(CASE WHEN zhhpdffj IS NOT NULL AND zhhpdffj<>'' THEN 1 ELSE 0 END) pdf_you,
                    COUNT(*) n
                    FROM {T} GROUP BY status_type, draft ORDER BY n DESC"""):
        print(f"   状态={r['st']} draft={r['draft']} (共{r['n']}): 正文 空{r['zw_kong']}/有{r['zw_you']}  "
              f"附件 空{r['fj_kong']}/有{r['fj_you']}  pdf 空{r['pdf_kong']}/有{r['pdf_you']}")
    # 已生成却正文为空
    r = q(f"SELECT COUNT(*) n FROM {T} WHERE status_type=1 AND zhengwenziduan=''")[0]['n']
    print(f"   ★ 已生成(status=1) 但正文为空: {r}")
c.close()
