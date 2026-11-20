import math
from src.config.settings import CONFIG
def number(value,name,minimum=0,integer=False):
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<minimum or (integer and int(value)!=value): raise ValueError(name+'数值不合法')
 return value
def validate_source(d):
 if not isinstance(d,dict) or set(d)!=set(CONFIG['fields']): raise ValueError('底稿字段必须与业务字段一致')
 for key in ('period','department'):
  if not isinstance(d[key],str) or not 1<=len(d[key])<=100: raise ValueError(key+'不能为空或过长')
 number(d['start'],'开始分钟',integer=True);number(d['end'],'结束分钟',integer=True)
 if not d['start']<d['end']<=2880: raise ValueError('班次必须为正时长且不超过两日')
 number(d['ideal_seconds'],'理想秒/件',minimum=0.001);number(d['total'],'产量',integer=True);number(d['good'],'合格数',integer=True)
 if d['good']>d['total']: raise ValueError('合格数不可大于总产量')
 if not isinstance(d['downtime'],list) or len(d['downtime'])>100: raise ValueError('停机区间需为数组且最多100段')
 for pair in d['downtime']:
  if not isinstance(pair,list) or len(pair)!=2: raise ValueError('停机区间必须是两个分钟数')
  number(pair[0],'停机起点');number(pair[1],'停机终点')
  if pair[1]<=pair[0]: raise ValueError('停机结束需晚于开始')
def validate_policy(d):
 if not isinstance(d,dict) or not isinstance(d.get('version'),str) or not 2<=len(d['version'])<=120: raise ValueError('口径版本名不合法')
 if not isinstance(d.get('definition'),str) or not d['definition']: raise ValueError('核算说明不能为空')
def validate_line_plan(d):
 if not isinstance(d,dict) or set(d)!={'name','stations','buffers','initial_wip'}: raise ValueError('方案字段必须为名称/工序顺序/缓冲容量/期初在制品')
 if not isinstance(d['name'],str) or not 2<=len(d['name'])<=120: raise ValueError('方案名称需2-120字')
 if not isinstance(d['stations'],list) or not 2<=len(d['stations'])<=12: raise ValueError('工序顺序需2-12站')
 for sid in d['stations']:
  if isinstance(sid,bool) or not isinstance(sid,int) or sid<1: raise ValueError('工序引用的底稿编号不合法')
 if len(set(d['stations']))!=len(d['stations']): raise ValueError('同一底稿不可在串线中重复使用')
 labels={'buffers':'缓冲容量','initial_wip':'期初在制品'}
 for key in labels:
  if not isinstance(d[key],list) or len(d[key])!=len(d['stations'])-1: raise ValueError(labels[key]+'数量需为工序数减一')
  for v in d[key]: number(v,labels[key],integer=True)
  if key=='buffers':
   for v in d[key]:
    if v>999: raise ValueError('单段缓冲容量不可超过999')
 for j,w in enumerate(d['initial_wip']):
  if w>d['buffers'][j]: raise ValueError('期初在制品不可超过对应缓冲容量')
