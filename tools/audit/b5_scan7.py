# -*- coding: utf-8 -*-
"""B-5 三链量化（b5_scan7.py 修复版）
修复两处同根缺陷：
  L37 原 `'messageInfo' in o` 过滤 → 改为只读 data_schema.trigger，正确处理空壳
  L63 原 `n.endswith(generator)` TypeError → 改为 tuple 展开
输出 D22 要求的三行：total=254 / with_mi=244 / without=10，加 A/B/C 口径对照
"""
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
print("微流程总数: %d"%len(rows))

# ---------- 链A：只读 data_schema.trigger ----------
trig=[]
for r in rows:
    try: ds=json.loads(r['data_schema'] or '{}')
    except: continue
    t=ds.get('trigger')
    if isinstance(t,dict) and t.get('type')=='BUSINESS_EVENT':
        trig.append((r, t))
has=[x for x in trig if 'messageInfo' in x[1]]
shell=[x for x in trig if 'messageInfo' not in x[1]]

# D22 三行（只读 /trigger 位；每微流程最多 1 个 trigger → occurrence 与 unique 恒等，不存在二者之分）
occ_n   = len(trig)
uniq_n  = len({(r['id'], t.get('nodeId')) for r,t in trig})
has_mi  = len(has)
print("\n[分母三行 D22] total=%d / with_mi=%d / without=%d" % (occ_n, has_mi, len(shell)))
print("  空壳(无 messageInfo)=%d ; 分布 %s" % (len(shell), dict(Counter((r['app_id']) for r,t in shell))))
print("  空壳键集合: %s" % set(tuple(sorted(t.keys())) for r,t in shell))
print("  CUSTOM/SERVICE: %s" % dict(Counter((t.get('nodeId') or '').split('_')[0] for r,t in shell)))

ms=Counter(t['messageInfo'].get('messageSource') for r,t in has)
combo=Counter((t['messageInfo'].get('messageSource'), t['messageInfo'].get('topic') is not None) for r,t in has)
print("  messageSource(has_mi 域): %s" % dict(ms))
print("  (ms,有topic): %s" % dict(combo))
viol=[1 for r,t in has if ((t['messageInfo'].get('messageSource')=='MESSAGE') != (t['messageInfo'].get('topic') is not None))]
print("  互斥违反数: %d" % len(viol))

# 附：nodeInfo 引用（不是 trigger，用于解释 255 假象）
refs=[]
def walk_refs(o):
    if isinstance(o,dict):
        ni=o.get('nodeInfo')
        if isinstance(ni,dict) and ni.get('type')=='BUSINESS_EVENT': yield ni
        for v in o.values(): yield from walk_refs(v)
    elif isinstance(o,list):
        for v in o: yield from walk_refs(v)
for r in rows:
    try: ds=json.loads(r['data_schema'] or '{}')
    except: continue
    for ni in walk_refs(ds.get('nodes') or []): refs.append((r,ni))
print("\n[附] 口径 A/B/C 对照（D21 验收项）")
# B 口径：任意深度求 type==BUSINESS_EVENT
def walk_any(o):
    if isinstance(o,dict):
        if o.get('type')=='BUSINESS_EVENT': yield o
        for v in o.values(): yield from walk_any(v)
    elif isinstance(o,list):
        for v in o: yield from walk_any(v)
depth_all=0
for r in rows:
    try: ds=json.loads(r['data_schema'] or '{}')
    except: continue
    depth_all+=sum(1 for _ in walk_any(ds))
A=len(trig); B=depth_all
print("     A) 只数 /trigger 位                = %d   ← 唯一正确口径" % A)
print("     B) 任意深度 type==BUSINESS_EVENT   = %d   ← 含引用碎片, 禁用" % B)
print("     C) B - A                           = %d" % (B-A))
print("     差值完整路径 = /nodes[0]/value/selectParam/nodeInfo （引用碎片，非 trigger）")
print("\n[附] nodeInfo 引用明细 =%d" % len(refs))
for r,ni in refs:
    print("     mf=%s(%s) nodeId=%s keys=%s" % (r['name'],r['id'],ni.get('nodeId'),tuple(sorted(ni.keys()))))

# ---------- 链B：投递 ----------
def walk_pub(o):
    if isinstance(o,dict):
        if o.get('actionType')=='PUBLISH_BUSINESS_EVENT': yield o
        for v in o.values(): yield from walk_pub(v)
    elif isinstance(o,list):
        for v in o: yield from walk_pub(v)
pub=[]
for r in rows:
    try: ds=json.loads(r['data_schema'] or '{}')
    except: continue
    for o in walk_pub(ds): pub.append((r,o))
print("\n[链B] PUBLISH_BUSINESS_EVENT 节点=%d" % len(pub))
print("  eventType: %s" % dict(Counter(o.get('eventType') for r,o in pub)))
print("  selectEvent.source: %s" % dict(Counter((o.get('selectEvent') or {}).get('source') for r,o in pub)))
print("  eventType×selectEvent为空: %s" % dict(Counter((o.get('eventType'), (o.get('selectEvent') or {}).get('fullName') is None) for r,o in pub)))

# ---------- 对账（L63 修复：endswith 传 tuple 不是 generator）----------
ev=q("SELECT id,name,app_id,source,caption FROM udc_event")
byname={}
for e in ev: byname.setdefault((e['name'] or '').lower(),[]).append(e)
print("\n[对账] selectEvent.fullName 末段 -> udc_event.name")
hit=0; miss=[]
for r,o in pub:
    se=o.get('selectEvent') or {}
    fn=se.get('fullName')
    last=(fn or '').rsplit('.',1)[-1] if fn else ''
    if last and last.lower() in byname:
        hit+=1
        print("    命中: %-50s -> %s (app=%s)" % (fn[-50:], byname[last.lower()][0]['name'], byname[last.lower()][0]['app_id']))
    else:
        miss.append((se.get('caption'), se.get('source'), fn))
print("  命中 %d / 总 %d" % (hit, len(pub)))
print("  未命中 %d: source %s ; fullName=null %d" % (len(miss), dict(Counter(x[1] for x in miss)), sum(1 for x in miss if x[2] is None)))
