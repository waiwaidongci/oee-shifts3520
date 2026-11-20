from sqlalchemy import Column,Integer,String,JSON,Text,Float
from src.config.database import Base
class LinePlan(Base):
 __tablename__='line_plans'
 id=Column(Integer,primary_key=True); name=Column(String(120),unique=True); data=Column(JSON,nullable=False); created=Column(Float)
class LineRun(Base):
 __tablename__='line_runs'
 id=Column(Integer,primary_key=True); name=Column(String(120)); status=Column(String(20)); snapshot=Column(JSON); checksum=Column(String(64)); result=Column(JSON); error=Column(Text); created=Column(Float)
