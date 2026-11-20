"""串线复盘仿真：1秒粒度推进，同刻交接一起判定，满仓同步腾位，零容量直交，停机保进度。"""
METHOD='仿真按1秒节拍推进：每刻先统一判定全部交接再同时落子（同刻交接一起判定）；缓冲满时若下游同刻取件，上游可同刻补入（满仓同步腾位）；缓冲容量为0时，上站完工件可同刻直接交给空闲下站（零容量直交）；停机期间设备冻结，不加工也不交接，停机前做了一半的件保留进度、复工接着做；首站前原料无限，末站完工即计入期末完工件数；节拍按秒累计，不足1秒向上取整。两遍（原状/取消所选停机）共用排队时冻结的同一版班次、节拍与停机记录；任务中断后按遍续跑，已交接的件不重复过站；两遍都算完才给出末端差值。'
def merge_clip(intervals,start,end):
 """停机区间裁剪到班次并合并重叠，返回排序后的[[起,止]…]（分钟）。"""
 pieces=sorted((max(start,a),min(end,b)) for a,b in intervals if min(end,b)>max(start,a))
 merged=[]
 for a,b in pieces:
  if merged and a<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
  else:merged.append([a,b])
 return merged
def resolve(plan,sources_by_id):
 """把方案引用的底稿解析成仿真快照：共同班次、每站节拍与有效停机（裁剪合并后）。"""
 stations=[];shift=None
 for sid in plan['stations']:
  s=sources_by_id.get(sid)
  if s is None:raise ValueError('工序引用的底稿不存在，请更正方案')
  if shift is None:shift=(s['start'],s['end'])
  elif (s['start'],s['end'])!=shift:raise ValueError('各工序底稿的班次起止必须一致')
  stations.append({'source_id':sid,'name':s['department'],'takt_seconds':s['ideal_seconds'],'downtime':merge_clip(s['downtime'],s['start'],s['end'])})
 return {'shift':{'start':shift[0],'end':shift[1]},'stations':stations,'buffers':list(plan['buffers']),'initial_wip':list(plan['initial_wip'])}
def simulate(snapshot,canceled=(),observe=None):
 """跑一遍仿真。canceled为要移除的(工序序号,停机段序号)；返回该遍结果（完工/投料/在制/各站四类秒数与缺料堵料时段）。"""
 cancel={tuple(x) for x in canceled}
 start=snapshot['shift']['start'];end=snapshot['shift']['end']
 base=start*60;T=(end-start)*60
 stations=snapshot['stations'];n=len(stations)
 takts=[float(s['takt_seconds']) for s in stations]
 caps=[int(c) for c in snapshot['buffers']]
 buffers=[int(w) for w in snapshot['initial_wip']]
 downs=[]
 for i,s in enumerate(stations):
  flags=bytearray(T)
  for j,(a,b) in enumerate(s['downtime']):
   if (i,j) in cancel:continue
   lo=max(0,round(a*60-base));hi=min(T,round(b*60-base))
   if hi>lo:flags[lo:hi]=b'\x01'*(hi-lo)
  downs.append(flags)
 progress=[None]*n;completed=0;intake=0
 work=[0]*n;down=[0]*n;starve=[0]*n;block=[0]*n
 starve_ivs=[[]for _ in range(n)];block_ivs=[[]for _ in range(n)]
 kind=[None]*n;since=[0]*n
 def boundary(s):
  """交接判定：先按本刻开始时的状态统一判定，再同时落子。使用下一工作刻的停机标记。"""
  nonlocal completed,intake
  t=min(s,T-1)
  up=[not downs[i][t] for i in range(n)]
  fin=[up[i] and progress[i] is not None and progress[i]>=takts[i] for i in range(n)]
  unload=[False]*n;recv=[False]*n
  unload[n-1]=fin[n-1]
  recv[n-1]=up[n-1] and(progress[n-1] is None or unload[n-1])
  for i in range(n-2,-1,-1):
   if not fin[i]:unload[i]=False
   elif caps[i]==0:unload[i]=recv[i+1]
   else:unload[i]=buffers[i]<caps[i] or recv[i+1]
   recv[i]=up[i] and(progress[i] is None or unload[i])
  pull=[False]*n;direct=[False]*n
  for i in range(n):
   if not recv[i]:continue
   if i==0:pull[i]=True
   elif caps[i-1]>0:pull[i]=buffers[i-1]>0
   else:direct[i]=unload[i-1]
  for i in range(n):
   if unload[i]:
    if i==n-1:completed+=1
    elif caps[i]>0:buffers[i]+=1
    progress[i]=None
  for i in range(n):
   if pull[i]:
    if i==0:intake+=1
    else:buffers[i-1]-=1
    progress[i]=0.0
   elif direct[i]:progress[i]=0.0
 boundary(0)
 for t in range(T):
  for i in range(n):
   if downs[i][t]:down[i]+=1;state='down'
   elif progress[i] is None:starve[i]+=1;state='starve'
   elif progress[i]<takts[i]:work[i]+=1;progress[i]+=1.0;state='work'
   else:block[i]+=1;state='block'
   if state!=kind[i]:
    if kind[i]=='starve':starve_ivs[i].append([since[i]+base,t+base])
    elif kind[i]=='block':block_ivs[i].append([since[i]+base,t+base])
    kind[i]=state if state in('starve','block')else None
    since[i]=t
  boundary(t+1)
  if observe:observe(t,progress,buffers)
 for i in range(n):
  if kind[i]=='starve':starve_ivs[i].append([since[i]+base,T+base])
  elif kind[i]=='block':block_ivs[i].append([since[i]+base,T+base])
 wip_start=sum(int(w) for w in snapshot['initial_wip'])
 wip_end=sum(buffers)+sum(1 for p in progress if p is not None)
 assert intake+wip_start==completed+wip_end,'在制品守恒校验失败'
 return{'completed':completed,'intake':intake,'wip_start':wip_start,'wip_end':wip_end,'stations':[{'name':stations[i]['name'],'work':work[i],'down':down[i],'starved':starve[i],'blocked':block[i],'starve_intervals':starve_ivs[i],'block_intervals':block_ivs[i]}for i in range(n)]}
