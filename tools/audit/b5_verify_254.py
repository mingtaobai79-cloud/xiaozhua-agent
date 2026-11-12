# -*- coding: utf-8 -*-
"""B-5 分母独立复核（只读 /trigger 位 = data_schema.trigger 且 type==BUSINESS_EVENT）

口径纪律（平台级，进 B-3 模板）:
  统计 BUSINESS_EVENT trigger 节点【必须以 /trigger 位为准】。
  禁用「对全 JSON 任意深度求 type==BUSINESS_EVENT」——该口径会把
  nodes[*].value.selectParam.nodeInfo 里的 trigger 引用碎片计入（本实例 +1，得错误值 255）。

期望输出: total=254 / with_mi=244 / without=10
"""
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

rows=q("SELECT id,name,app_id,data_schema FROM udc_microflow_info")

# ---- 唯一正确口径：只读 data_schema.trigger ----
trig=[]
for r in rows:
    try: ds=json.loads(r['data_schema'] or '{}')
    except: continue
    t=ds.get('trigger')
    if isinstance(t,dict) and t.get('type')=='BUSINESS_EVENT':
        trig.append((r,t))

total   = len(trig)
with_mi = sum(1 for r,t in trig if 'messageInfo' in t)
without = total - with_mi
mf_with_trigger = len({r['id'] for r,t in trig})

print("BUSINESS_EVENT trigger（只读 /trigger 位）")
print("  total   = %d" % total)
print("  with_mi = %d" % with_mi)
print("  without = %d" % without)
print("  有 trigger 的微流程数 = %d  → %s" % (mf_with_trigger, "一一对应，无 occurrence/unique 之分" if mf_with_trigger==total else "存在多 trigger 微流程"))

# 空壳形态
shell=[(r,t) for r,t in trig if 'messageInfo' not in t]
print("\n空壳(无 messageInfo) = %d" % len(shell))
print("  键集合: %s" % set(tuple(sorted(t.keys())) for r,t in shell))
print("  nodeId 前缀: %s" % dict(Counter((t.get('nodeId') or '').split('_')[0] for r,t in shell)))
print("  按应用: %s  （涉及 %d 个应用）" % (dict(Counter(r['app_id'] for r,t in shell)), len({r['app_id'] for r,t in shell})))

# messageSource 域（仅在 with_mi 内，None 不出现）
ms=Counter(t['messageInfo'].get('messageSource') for r,t in trig if 'messageInfo' in t)
print("\n具 messageInfo 域内 messageSource: %s" % dict(ms))
print("  注: 空壳不是 messageSource=None，而是没有 messageInfo —— 该字段不存在")

# 互斥校验
viol=sum(1 for r,t in trig if 'messageInfo' in t and (((t['messageInfo'].get('messageSource')=='MESSAGE') != (t['messageInfo'].get('topic') is not None))))
print("  互斥违反数 = %d" % viol)

# ---- 对照：错误口径（任意深度），仅用于说明差异，不参与断言 ----
def walk_any(o):
    if isinstance(o,dict):
        if o.get('type')=='BUSINESS_EVENT': yield o
        for v in o.values(): yield from walk_any(v)
    elif isinstance(o,list):
        for v in o: yield from walk_any(v)
depth=0
for r in rows:
    try: ds=json.loads(r['data_schema'] or '{}')
    except: continue
    depth+=sum(1 for _ in walk_any(ds))
print("\n[对照，禁用] 任意深度口径 = %d（= total + %d 个引用碎片）" % (depth, depth-total))
