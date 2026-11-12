
# -*- coding: utf-8 -*-
"""SC2: udc_event 全库普查（纯只读）"""
import os,sys
from collections import Counter
for line in open(r'<HERMES_HOME>\skills\xiaozhua\01-platform\xiaozhua-low-code-environment\.env', encoding='utf-8'):
    line=line.strip()
    if '=' in line and not line.startswith('#'):
        k,v=line.split('=',1); os.environ[k]=v
sys.path.insert(0, r'<HERMES_HOME>\skills\xiaozhua\01-platform\xiaozhua-low-code-environment\scripts')
from env import load_env
import pymysql
cfg=load_env('test2'); m=cfg['mysql']
c=pymysql.connect(host=m['host'],port=int(m['port']),user=os.environ['XIAOZHUA_DB_USERNAME'],password=os.environ['XIAOZHUA_DB_PASSWORD'],database='udc_test2',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
def q(s,a=None):
    with c.cursor() as cur:
        cur.execute(s,a if a else None); return cur.fetchall()
import os as _os
AID=_os.environ.get("XIAOZHUA_APP_ID")
if not AID:
    raise SystemExit("缺 appId：请设 XIAOZHUA_APP_ID")
print("== udc_event 全库 %d 行 ==" % len(q("SELECT id FROM udc_event")))
print("  source:",dict(Counter(int(r['source']) for r in q("SELECT source FROM udc_event"))))
print("  enabled:",dict(Counter(int(r['enabled']) for r in q("SELECT enabled FROM udc_event"))))
print("  action_type:",dict(Counter(int(r['action_type']) for r in q("SELECT action_type FROM udc_event"))))
print("  event_data_type:",dict(Counter(int(r['event_data_type']) for r in q("SELECT event_data_type FROM udc_event"))))
print("  有exp_design_data的行数:", q("SELECT COUNT(*) n FROM udc_event WHERE exp_design_data IS NOT NULL AND exp_design_data<>''")[0]['n'])
print("  有message_topic的行数:", q("SELECT COUNT(*) n FROM udc_event WHERE message_topic IS NOT NULL AND message_topic<>''")[0]['n'])
print("\n== 本应用 udc_event 4 行 ==")
for r in q("SELECT id,name,caption,source,source_id,action_type,event_data,event_data_type,enabled FROM udc_event WHERE app_id=%s",(AID,)):
    print("  id=%s name=%-20s caption=%-16s src=%s act=%s dtype=%s enabled=%s srcId=%s data=%s"%(
        r['id'],r['name'],r['caption'],r['source'],r['action_type'],r['event_data_type'],r['enabled'],r['source_id'],r['event_data']))
