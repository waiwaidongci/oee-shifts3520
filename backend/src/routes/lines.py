from fastapi import APIRouter,Depends,HTTPException
from src.config.database import database
from src.controllers.auth import current,editor
from src.models.line import LinePlan,LineRun
from src.schemas.requests import DataInput,LineRunInput
from src.services.line import save_plan,remove_plan,resolve_plan,submit_run
from src.utils.serialize import row
router=APIRouter()
@router.get('/lines')
def plans(db=Depends(database),u=Depends(current)): return [row(x) for x in db.query(LinePlan).order_by(LinePlan.id).all()]
@router.post('/lines')
def create(b:DataInput,db=Depends(database),u=Depends(editor)): return row(save_plan(db,u,b.data))
@router.put('/lines/{id}')
def update(id:int,b:DataInput,db=Depends(database),u=Depends(editor)): return row(save_plan(db,u,b.data,id))
@router.delete('/lines/{id}')
def delete(id:int,db=Depends(database),u=Depends(editor)): return remove_plan(db,u,id)
@router.get('/lines/{id}/resolve')
def resolve_view(id:int,db=Depends(database),u=Depends(current)): return resolve_plan(db,id)
@router.get('/lineruns')
def runs(db=Depends(database),u=Depends(current)): return [row(x) for x in db.query(LineRun).order_by(LineRun.id.desc()).all()]
@router.post('/lineruns')
def queue(b:LineRunInput,db=Depends(database),u=Depends(editor)): return row(submit_run(db,u,b))
@router.get('/lineruns/{id}')
def detail(id:int,db=Depends(database),u=Depends(current)):
 obj=db.get(LineRun,id)
 if not obj: raise HTTPException(404,'复盘任务不存在')
 return row(obj)
