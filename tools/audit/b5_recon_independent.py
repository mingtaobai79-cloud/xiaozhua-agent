
# -*- coding: utf-8 -*-
"""B-5 §5 对账 SELF-CHECK（可跑通版，替代 b5_scan7.py L63 崩溃段）

口径纪律（平台级）：trigger 节点只读 data_schema.trigger；禁任意深度求 type==BUSINESS_EVENT
（后者会把 nodes[*].value.selectParam.nodeInfo 的引用碎片计入，本实例 +1 → 错误值 255）。
PUBLISH_BUSINESS_EVENT 仍用全树遍历（它是节点 args，不是 trigger 位，语义不同且已核 72 稳定）。

输出: 分母三行 total=254 / with_mi=244 / without=10
      PUBLISH_BUSINESS_EVENT 节点数 / eventType / selectEvent.source
      selectEvent.fullName 末段 -> udc_event.name 对账命中率"""
import os,sys,json
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

rows=q("SELECT id,name,app_id,data_schema FROM udc_microflow_info")
# trigger 只读 /trigger 位（口径纪律：禁任意深度，否则会吃到 nodeInfo 引用碎片 → 255）
def get_trigger(ds):
    t=ds.get('trigger')
    if isinstance(t,dict) and t.get('type')=='BUSINESS_EVENT': return t
    return None
def walk_pub(o):
    if isinstance(o,dict):
        if o.get('actionType')=='PUBLISH_BUSINESS_EVENT': yield o
        for v in o.values(): yield from walk_pub(v)
    elif isinstance(o,list):
        for v in o: yield from walk_pub(v)

trig=[]; pub=[]
for r in rows:
    try: ds=json.loads(r['data_schema'] or '{}')
    except: continue
    t=get_trigger(ds)
    if t is not None: trig.append((r,t))
    for o in walk_pub(ds): pub.append((r,o))

# ① trigger 分档
has=[t for t in trig if 'messageInfo' in t[1]]
no =[t for t in trig if 'messageInfo' not in t[1]]
print("[1] 分母三行: total=%d / with_mi=%d / without=%d"%(len(trig),len(has),len(no)))
print("    有 trigger 的微流程数: %d → %s"%(len({r['id'] for r,t in trig}),
      "一一对应，无 occurrence/unique 之分" if len({r['id'] for r,t in trig})==len(trig) else "存在多 trigger 微流程"))
ms=Counter(t[1]['messageInfo'].get('messageSource') for t in has)
tp=Counter(t[1]['messageInfo'].get('topic') for t in has)
print("    messageSource: %s"%dict(ms))
print("    topic 非空数: %d ; topic=None 数: %d"%(sum(v for k,v in tp.items() if k),tp.get(None,0)))
combo=Counter((t[1]['messageInfo'].get('messageSource'), t[1]['messageInfo'].get('topic') is not None) for t in has)
print("    (messageSource,有topic): %s"%dict(combo))
shell_keys=Counter(tuple(sorted(t[1].keys())) for t in no)
print("    空壳形态(键集合->条数): ")
for k,v in shell_keys.items(): print("       %d × %s"%(v,k))

# ② 投递
se_list=[]
for r,o in pub:
    se=o.get('selectEvent') or {}
    se_list.append((r,o,se))
print("\n[2] PUBLISH_BUSINESS_EVENT 节点数: %d"%len(pub))
print("    eventType: %s"%dict(Counter(o.get('eventType') for _,o,_ in se_list)))
print("    selectEvent.source: %s"%dict(Counter(s.get('source') for _,_,s in se_list)))
print("    eventType×selectEvent为空: %s"%dict(Counter((o.get('eventType'), s.get('fullName') is None) for _,o,s in se_list)))

# ③ 对账（修好的版本：先建末段集合，再逐项判断）
ev=q("SELECT id,name,app_id,source,caption FROM udc_event")
byname={}
for e in ev: byname.setdefault((e['name'] or '').lower(),[]).append(e)
print("\n[3] selectEvent.fullName 末段 -> udc_event.name 对账")
hit=0; miss=[]
for r,o,se in se_list:
    fn=se.get('fullName')
    last=(fn or '').rsplit('.',1)[-1] if fn else ''
    recs=byname.get(last.lower()) if last else None
    if recs:
        hit+=1
        print("    命中: %-52s -> udc_event %s (app=%s)"%(fn[-52:], recs[0]['name'], recs[0]['app_id']))
    else:
        miss.append((se.get('caption'), se.get('source'), fn))
print("    命中 %d / 总 %d"%(hit,len(se_list)))
print("    未命中 %d 例: source 分布 %s"%(len(miss),dict(Counter(x[1] for x in miss))))
print("    未命中 fullName=null 数: %d"%sum(1 for x in miss if x[2] is None))
