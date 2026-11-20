import {saveLinePlan,deleteLinePlan,resolveLine,submitLineRun} from '../api/business.js';
import {store,reload} from '../stores/business.js';
import {action} from './action.js';
import {paintStations} from '../pages/line.js';
export function bindLine(render){
 const box=document.querySelector('#line-stations');
 if(box){
  const d=store.data;
  const readState=()=>({stations:[...box.querySelectorAll('[name=station]')].map(x=>Number(x.value)),buffers:[...box.querySelectorAll('[name=buffer]')].map(x=>Number(x.value)),wip:[...box.querySelectorAll('[name=wip]')].map(x=>Number(x.value))});
  const paint=st=>{box.innerHTML=paintStations(d,st.stations,st.buffers,st.wip)};
  document.querySelector('#line-add-station').onclick=()=>{const st=readState();if(st.stations.length>=12||!d.sources.length)return;st.stations.push(d.sources[0].id);st.buffers.push(0);st.wip.push(0);paint(st)};
  box.onclick=e=>{
   const row=e.target.closest('.line-station');if(!row)return;
   const rows=[...box.querySelectorAll('.line-station')],i=rows.indexOf(row),st=readState();
   if(e.target.classList.contains('line-remove')){
    if(st.stations.length<=2)return;
    st.stations.splice(i,1);const g=i===0?0:i-1;st.buffers.splice(g,1);st.wip.splice(g,1);paint(st);
   }
   if(e.target.classList.contains('line-move')){
    const j=i+Number(e.target.dataset.dir);if(j<0||j>=st.stations.length)return;
    [st.stations[i],st.stations[j]]=[st.stations[j],st.stations[i]];paint(st);
   }
  };
 }
 const pf=document.querySelector('#line-plan-form');
 if(pf)pf.onsubmit=e=>{e.preventDefault();action(async()=>{
  const f=new FormData(pf);
  const data={name:f.get('name'),stations:[...pf.querySelectorAll('[name=station]')].map(x=>Number(x.value)),buffers:[...pf.querySelectorAll('[name=buffer]')].map(x=>Number(x.value)),initial_wip:[...pf.querySelectorAll('[name=wip]')].map(x=>Number(x.value))};
  await saveLinePlan(data,f.get('id')||null);store.line.edit=null;store.line.resolve=null;await reload();render();
 })};
 const ce=document.querySelector('#line-cancel-edit');
 if(ce)ce.onclick=()=>{store.line.edit=null;render()};
 document.querySelectorAll('.line-edit').forEach(b=>b.onclick=()=>{store.line.edit=store.data.lines.find(p=>p.id===Number(b.dataset.id));render()});
 document.querySelectorAll('.line-del').forEach(b=>b.onclick=()=>action(async()=>{const id=Number(b.dataset.id);await deleteLinePlan(id);if(store.line.edit&&store.line.edit.id===id)store.line.edit=null;store.line.resolve=null;await reload();render()}));
 const ps=document.querySelector('#line-plan-select');
 if(ps)ps.onchange=()=>{store.line.resolve=null;render()};
 const lr=document.querySelector('#line-load-resolve');
 if(lr)lr.onclick=()=>action(async()=>{store.line.resolve=await resolveLine(Number(document.querySelector('#line-plan-select').value));render()});
 const rf=document.querySelector('#line-run-form');
 if(rf)rf.onsubmit=e=>{e.preventDefault();action(async()=>{
  const f=new FormData(rf);
  const run=await submitLineRun({name:f.get('name'),plan_id:Number(f.get('plan_id')),canceled:f.getAll('cancel').map(v=>v.split(':').map(Number))});
  store.line.selected=run.id;store.line.query={pass:'pass_a',station:0,type:'starve'};await reload();render();
 })};
 document.querySelectorAll('.line-select-run').forEach(b=>b.onclick=()=>{store.line.selected=Number(b.dataset.id);store.line.query={pass:'pass_a',station:0,type:'starve'};render()});
 const qf=document.querySelector('#line-query');
 if(qf)qf.onchange=()=>{const f=new FormData(qf);store.line.query={pass:f.get('pass'),station:Number(f.get('station')),type:f.get('type')};render()};
}
