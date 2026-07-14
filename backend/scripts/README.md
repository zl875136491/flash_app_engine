# 运维 / 初始化脚本目录
# 后续可放置：种子用户导入、Mongo 索引初始化等

本任务点已通过 Beanie `Settings.name` 与字段 `Indexed` 声明集合与唯一索引；
应用启动时 `connect_db()` 会自动注册 `User` / `Image` / `Task`。
