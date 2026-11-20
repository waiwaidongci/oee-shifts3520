# 初始结构

SQLAlchemy启动创建以下业务表：shifts, downtimeevents, productioncounts, oeeruns, delivery_schedules, deliveries、users、audits。Source专属JSON字段由对应validation严格校验；Policy为不可覆盖的版本记录；Run保存source/policy冻结快照；Period仅用于已有期间选择器，不计入核心复杂度。已有数据库升级需先备份，后续字段演进应以独立迁移执行。

# 002 串线复盘

新增 line_plans（串线方案：工序顺序/缓冲容量/期初在制品JSON，名称唯一）与 line_runs（串线复盘：冻结快照、SHA256、两遍仿真结果、状态）。启动时create_all自动建表；存量库无数据迁移。LineRun快照保存共同班次、各站节拍与裁剪合并后的停机段及取消选择，排队后底稿更正不影响该任务。
