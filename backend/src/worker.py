import time,json,traceback
from pathlib import Path
import redis
from src.config.database import Base,engine,Session
from src.config.settings import REDIS_URL
from src.models import identity,source,run,line
from src.models.run import Run
from src.models.line import LineRun
from src.services.calculation import calculate
from src.services.line import process as process_line_job
from src.services.delivery import tick
Base.metadata.create_all(engine)
r=redis.Redis.from_url(REDIS_URL)
with Session() as db:
 for stuck in db.query(LineRun).filter(LineRun.status=='running').all(): r.rpush('line-jobs',stuck.id)
while True:
 Path('/tmp/worker-heartbeat').write_text(str(time.time()))
 try:
  item=r.lpop('report-jobs')
  if item:
   with Session() as db:
    job=db.get(Run,int(item))
    if job and job.status=='queued':
     job.status='running';db.commit()
     try: job.result=calculate(job.snapshot['sources'],job.snapshot['policy']);job.status='completed'
     except Exception as exc: job.status='failed';job.error=str(exc);traceback.print_exc()
     db.commit()
  item=r.lpop('line-jobs')
  if item:
   with Session() as db:
    job=db.get(LineRun,int(item))
    if job and job.status in ('queued','running'):
     job.status='running';db.commit()
     try: process_line_job(db,job)
     except Exception as exc: job.status='failed';job.error=str(exc);traceback.print_exc();db.commit()
  with Session() as db: tick(db)
 except Exception: traceback.print_exc()
 time.sleep(1)
