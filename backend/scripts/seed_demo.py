import json,random,time,hashlib
from src.config.database import Base,engine,Session
from src.config.settings import CONFIG
from src.models.identity import User
from src.models.source import Source,Policy,Period
from src.models.line import LinePlan,LineRun
from src.models import run
from src.utils.security import password_hash
from src.services.validation import validate_source
from src.services.linesim import resolve,simulate,METHOD

def demo_rows():
 rng=random.Random(42);rows=[]
 for i in range(240):
  total=rng.randint(600,1050);rows.append({'period':'2026-11-'+str(1+i%20).zfill(2),'department':['试制机A','试制机B','试制机C'][i%3],'start':480,'end':1020,'ideal_seconds':25,'total':total,'good':total-rng.randint(10,60),'downtime':[[540,570],[560,590],[950,970]]})
 return rows

def seed():
 Base.metadata.create_all(engine)
 with Session() as db:
  for role in ('admin','analyst','viewer'):
   if not db.query(User).filter_by(email=role+'@demo.local').first():db.add(User(email=role+'@demo.local',role=role,password=password_hash('Demo2026!')))
  rows=demo_rows()
  for name in sorted(set(r['period'] for r in rows)):
   if not db.query(Period).filter_by(name=name).first():db.add(Period(name=name,description='合成演示业务期间，seed=42'))
  for i,data in enumerate(rows):
   validate_source(data);key='demo-'+str(i+1)
   if not db.query(Source).filter_by(natural_key=key).first():db.add(Source(natural_key=key,data=data))
  if not db.query(Policy).filter_by(version=CONFIG['policy']['version']).first():db.add(Policy(version=CONFIG['policy']['version'],data=CONFIG['policy']))
  db.commit()
  by_key={x.natural_key:x for x in db.query(Source).all()}
  trio=[by_key.get('demo-'+str(i)) for i in (1,2,3)]
  plan=db.query(LinePlan).filter_by(name='演示串线·试制三联').first()
  if all(trio) and not plan:
   plan=LinePlan(name='演示串线·试制三联',data={'name':'演示串线·试制三联','stations':[x.id for x in trio],'buffers':[2,1],'initial_wip':[1,0]},created=time.time())
   db.add(plan);db.commit()
  if plan and not db.query(LineRun).filter_by(name='演示复盘·取消三站首段停机').first():
   canceled=[[0,0],[1,0],[2,0]]
   snapshot={'plan_id':plan.id,'plan_name':plan.name,**resolve(plan.data,{x.id:x.data for x in db.query(Source).all()}),'canceled':canceled}
   pass_a=simulate(snapshot,[]);pass_b=simulate(snapshot,canceled)
   result={'method':METHOD,'pass_a':pass_a,'pass_b':pass_b,'diff':{'completed_a':pass_a['completed'],'completed_b':pass_b['completed'],'delta':pass_b['completed']-pass_a['completed']}}
   checksum=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
   db.add(LineRun(name='演示复盘·取消三站首段停机',status='completed',snapshot=snapshot,checksum=checksum,result=result,created=time.time()))
   db.commit()
  db.commit();print(json.dumps({'users':db.query(User).count(),'sources':db.query(Source).count(),'policies':db.query(Policy).count(),'periods':db.query(Period).count(),'lines':db.query(LinePlan).count(),'lineruns':db.query(LineRun).count()},ensure_ascii=False))
if __name__=='__main__':seed()
