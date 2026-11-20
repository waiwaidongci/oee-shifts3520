// API实体字段约定：来源{id,natural_key,data}、口径{id,version,data}、报告{id,status,snapshot,checksum,result,approved}、计划{next_at,enabled}、串线方案{id,name,data{stations,buffers,initial_wip}}、串线复盘{id,status,snapshot,result}。
export const ENTITY_KEYS=['sources','policies','runs','schedules','deliveries','lines','lineruns'];
