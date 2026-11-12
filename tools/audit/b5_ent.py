
import os,sys
import os as _os
AID=_os.environ.get("XIAOZHUA_APP_ID")
if not AID:
    raise SystemExit("缺 appId：请设 XIAOZHUA_APP_ID")
for line in open(r'<HERMES_HOME>\skills\xiaozhua\01-platform\xiaozhua-low-code-environment\.env', encoding='utf-8'):
    line=line.strip()
    if '=' in line and not line.startswith('#'):
        k,v=line.split('=',1); os.environ[k]=v
sys.path.insert(0, r'<HERMES_HOME>\skills\xiaozhua\01-platform\xiaozhua-low-code-environment\scripts')
from env import load_env
import pymysql
cfg=load_env('test2'); m=cfg['mysql']
c=pymysql.connect(host=m['host'],port=int(m['port']),user=os.environ['XIAOZHUA_DB_USERNAME'],password=os.environ['XIAOZHUA_DB_PASSWORD'],database='udc_test2',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
def q(s):
    with c.cursor() as cur:
        cur.execute(s); return cur.fetchall()
print("udc_entity 总行数:",q("SELECT COUNT(*) n FROM udc_entity")[0]['n'])
print("udc_application 总行数:",q("SELECT COUNT(*) n FROM udc_application")[0]['n'])
print("本应用实体数:",q("SELECT COUNT(*) n FROM udc_entity WHERE app_id=%s", (AID,))[0]['n'])
