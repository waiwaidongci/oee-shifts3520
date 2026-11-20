export const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const fmt=v=>typeof v==='number'?v.toLocaleString('zh-CN',{maximumFractionDigits:4}):esc(typeof v==='object'?JSON.stringify(v):v);
export const time=v=>new Date(v*1000).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai'});
export const clock=v=>{v=Math.round(v);const h=String(Math.floor(v/3600)).padStart(2,'0'),m=String(Math.floor(v%3600/60)).padStart(2,'0'),s=String(v%60).padStart(2,'0');return `${h}:${m}:${s}`};
