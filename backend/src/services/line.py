import hashlib,json,time
from fastapi import HTTPException
from src.models.line import LinePlan,LineRun
from src.models.source import Source
from src.services.audit import log
from src.services.linesim import resolve,simulate,METHOD
from src.services.validation import validate_line_plan
from src.config.settings import REDIS_URL
import redis
def sources_by_id(db): return {x.id:x.data for x in db.query(Source).all()}
def save_plan(db,user,data,id=None):
 validate_line_plan(data)
 resolve(data,sources_by_id(db))
 clash=db.query(LinePlan).filter(LinePlan.name==data['name']).first()
 if clash and clash.id!=id: raise HTTPException(409,'方案名已存在，请另起名称保留历史')
 obj=db.get(LinePlan,id) if id else LinePlan(created=time.time())
 if not obj: raise HTTPException(404,'串线方案不存在')
 obj.name=data['name'];obj.data=data;db.add(obj)
 log(db,user.email,'line.plan.update' if id else 'line.plan.create',data['name']);db.commit();return obj
def remove_plan(db,user,id):
 obj=db.get(LinePlan,id)
 if not obj: raise HTTPException(404,'串线方案不存在')
 db.delete(obj);log(db,user.email,'line.plan.delete',id);db.commit();return {'deleted':id}
def resolve_plan(db,id):
 obj=db.get(LinePlan,id)
 if not obj: raise HTTPException(404,'串线方案不存在')
 return {'plan_id':obj.id,'plan_name':obj.name,**resolve(obj.data,sources_by_id(db))}
def submit_run(db,user,body):
 plan=db.get(LinePlan,body.plan_id)
 if not plan: raise HTTPException(404,'串线方案不存在')
 resolved=resolve(plan.data,sources_by_id(db))
 canceled=set()
 for pair in body.canceled:
  if not isinstance(pair,(list,tuple)) or len(pair)!=2: raise HTTPException(422,'取消停机项需为[工序序号,停机段序号]')
  i,j=pair
  if isinstance(i,bool) or isinstance(j,bool) or not isinstance(i,int) or not isinstance(j,int) or not 0<=i<len(resolved['stations']) or not 0<=j<len(resolved['stations'][i]['downtime']): raise HTTPException(422,'取消停机项超出方案范围')
  canceled.add((i,j))
 snapshot={'plan_id':plan.id,'plan_name':plan.name,**resolved,'canceled':[list(x) for x in sorted(canceled)]}
 checksum=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 obj=LineRun(name=body.name,status='queued',snapshot=snapshot,checksum=checksum,created=time.time())
 db.add(obj);log(db,user.email,'linerun.queue',body.name);db.commit()
 redis.Redis.from_url(REDIS_URL).rpush('line-jobs',obj.id)
 return obj
def process(db,job):
 """串线复盘按遍断点续跑：每算完一遍即落库；中断恢复后已完成的遍不重算（已交接的件不重复过站）；两遍都算完才给出末端差值。"""
 result=dict(job.result or {})
 if 'pass_a' not in result:
  result={'method':METHOD,'pass_a':simulate(job.snapshot,[])}
  job.result=result;db.commit()
 if 'pass_b' not in result:
  result['pass_b']=simulate(job.snapshot,job.snapshot['canceled'])
  result['diff']={'completed_a':result['pass_a']['completed'],'completed_b':result['pass_b']['completed'],'delta':result['pass_b']['completed']-result['pass_a']['completed']}
  job.result=result;db.commit()
 job.status='completed';db.commit()
