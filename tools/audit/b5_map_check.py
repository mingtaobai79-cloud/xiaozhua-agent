
# -*- coding: utf-8 -*-
"""B-5: DB->DTO 枚举映射全量校验 + 事件对象普查"""
import os,sys,json
from collections import Counter
for line in open(r'<HERMES_HOME>\skills\seeyon\01-platform\seeyon-low-code-environment\.env', encoding='utf-8'):
    line=line.strip()
    if '=' in line and not line.startswith('#'):
        k,v=line.split('=',1); os.environ[k]=v
sys.path.insert(0, r'<HERMES_HOME>\skills\seeyon\01-platform\seeyon-low-code-environment\scripts')
from env import load_env
import pymysql
cfg=load_env('test2'); m=cfg['mysql']
c=pymysql.connect(host=m['host'],port=int(m['port']),user=os.environ['SEEYON_DB_USERNAME'],password=os.environ['SEEYON_DB_PASSWORD'],database='udc_test2',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
def q(s,a=None):
    with c.cursor() as cur:
        cur.execute(s,a if a else None); return cur.fetchall()
rows={str(r['id']):r for r in q("SELECT * FROM udc_event")}
smp=json.load(open(r"<SEEYON_AGENT_ROOT>\docs\audit\artifacts\udc-node-evidence\udcEventListPost_all.json",encoding="utf-8"))
SRC={0:"ENTITY",1:"MICRO_FLOW",2:"MICRO_FLOW_EVENT"}
OBJ={0:"OBJECT",1:"LIST"}
ACT={0:"CREATE",1:"UPDATE",2:"DELETE",3:"SELECT"}
MT={0:"DEFAULT",1:"DELAY"}
ok=bad=0; errs=[]
for e in smp:
    r=rows.get(str(e['id']))
    if not r: continue
    checks=[("source",SRC.get(int(r['source'])),e.get("source")),
            ("eventDataType",OBJ.get(int(r['event_data_type'])),e.get("eventDataType")),
            ("actionType",ACT.get(int(r['action_type'])),e.get("actionType")),
            ("messageType",MT.get(int(r['message_type'])),e.get("messageType")),
            ("enabled",bool(int(r['enabled'])),e.get("enabled")),
            ("name",r['name'],e.get("name")),
            ("caption",r['caption'],e.get("caption")),
            ("eventData",str(r['event_data']),str(e.get("eventData"))),
            ("numberFiredOnce",r['number_fired_once'],e.get("numberFiredOnce")),
            ("sourceId",str(r['source_id']),str(e.get("sourceId")))]
    for f,dbv,apiv in checks:
        if dbv==apiv: ok+=1
        else:
            bad+=1; errs.append((e.get('name'),f,dbv,apiv))
print("字段映射校验: ok=%d bad=%d"%(ok,bad))
for x in errs[:15]: print("  MISMATCH",x)
print("\n== 未出现的枚举值（全库 52 行）==")
print("  source values:",dict(Counter(int(r['source']) for r in rows.values())))
print("  action_type:",dict(Counter(int(r['action_type']) for r in rows.values())))
print("  event_data_type:",dict(Counter(int(r['event_data_type']) for r in rows.values())))
print("  message_type:",dict(Counter(int(r['message_type']) for r in rows.values())))
