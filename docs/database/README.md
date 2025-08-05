# EmbedAI 数据库架构文档

## 概述

EmbedAI管理后台系统采用关系型数据库设计，使用SQLAlchemy ORM进行数据访问。数据库设计遵循第三范式，确保数据一致性和完整性。

## 数据库配置

### 支持的数据库

- **开发环境**: SQLite
- **生产环境**: PostgreSQL, MySQL
- **ORM框架**: SQLAlchemy (异步)

### 连接配置

```python
# 数据库连接字符串示例
DATABASE_URL = "sqlite+aiosqlite:///./embedai.db"  # SQLite
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/embedai"  # PostgreSQL
DATABASE_URL = "mysql+aiomysql://user:pass@localhost/embedai"  # MySQL
```

## 数据库架构概览

### 核心模块

1. **用户管理模块**
   - `users` - 用户基础信息
   - `user_identities` - 用户身份信息
   - `third_party_users` - 第三方用户

2. **知识库模块**
   - `knowledge_bases` - 知识库信息
   - `documents` - 文档信息
   - `document_chunks` - 文档分块
   - `document_embeddings` - 文档向量

3. **对话模块**
   - `chats` - 对话会话
   - `chat_messages` - 对话消息
   - `llm_usage_logs` - LLM使用日志

4. **分析模块**
   - `system_metrics` - 系统指标
   - `user_activity_logs` - 用户活动日志
   - `knowledge_base_metrics` - 知识库指标
   - `api_metrics` - API指标

5. **健康监控模块**
   - `service_health` - 服务健康状态
   - `system_alerts` - 系统告警
   - `performance_thresholds` - 性能阈值
   - `health_check_configs` - 健康检查配置
   - `uptime_records` - 运行时间记录

6. **权限管理模块**
   - `permissions` - 权限定义
   - `roles` - 角色定义
   - `user_groups` - 用户组
   - `user_sessions` - 用户会话
   - `user_login_logs` - 登录日志
   - `user_security_settings` - 安全设置

7. **系统配置模块**
   - `system_configs` - 系统配置
   - `config_change_logs` - 配置变更日志
   - `config_templates` - 配置模板
   - `config_backups` - 配置备份
   - `environment_variables` - 环境变量
   - `config_validation_rules` - 配置验证规则

8. **安全模块**
   - `two_factor_auth` - 双因子认证
   - `ip_whitelists` - IP白名单
   - `ip_blacklists` - IP黑名单
   - `security_events` - 安全事件
   - `password_history` - 密码历史
   - `device_fingerprints` - 设备指纹
   - `security_policies` - 安全策略

9. **内容管理模块**
   - `content_moderation_rules` - 内容审核规则
   - `content_moderation_logs` - 内容审核日志
   - `bulk_operations` - 批量操作
   - `content_tags` - 内容标签
   - `content_categories` - 内容分类
   - `search_indexes` - 搜索索引
   - `content_statistics` - 内容统计
   - `data_export_tasks` - 数据导出任务

10. **集成模块**
    - `api_keys` - API密钥
    - `webhooks` - Webhook配置
    - `webhook_deliveries` - Webhook投递记录
    - `integrations` - 集成配置
    - `api_endpoints` - API端点
    - `api_usage_logs` - API使用日志
    - `integration_templates` - 集成模板
    - `api_documentation` - API文档

## 表关系图

```mermaid
erDiagram
    users ||--o{ user_identities : has
    users ||--o{ third_party_users : has
    users ||--o{ knowledge_bases : owns
    users ||--o{ chats : creates
    users ||--o{ user_activity_logs : generates
    
    knowledge_bases ||--o{ documents : contains
    documents ||--o{ document_chunks : splits_into
    document_chunks ||--o{ document_embeddings : has
    
    chats ||--o{ chat_messages : contains
    chat_messages ||--o{ llm_usage_logs : triggers
    
    users ||--o{ user_sessions : has
    users ||--o{ user_login_logs : generates
    users ||--o{ password_history : has
    
    roles ||--o{ permissions : has
    users ||--o{ roles : assigned_to
    user_groups ||--o{ users : contains
```

## 数据类型约定

### 主键
- 所有表使用自增整数作为主键
- 字段名统一为 `id`

### 时间戳
- 创建时间: `created_at` (DateTime)
- 更新时间: `updated_at` (DateTime)
- 删除时间: `deleted_at` (DateTime, 软删除)

### 状态字段
- 布尔类型: `is_active`, `is_enabled`, `is_deleted`
- 枚举类型: 使用字符串枚举

### 外键约束
- 外键字段命名: `{table_name}_id`
- 删除策略: 根据业务需求设置 CASCADE 或 SET NULL

## 索引策略

### 主要索引

1. **用户表索引**
   - `email` (唯一索引)
   - `sdk_key` (唯一索引)
   - `is_active, created_at` (复合索引)

2. **知识库表索引**
   - `user_id, name` (复合索引)
   - `domain` (普通索引)
   - `created_at` (普通索引)

3. **文档表索引**
   - `knowledge_base_id` (普通索引)
   - `file_hash` (唯一索引)
   - `created_at` (普通索引)

4. **活动日志索引**
   - `user_id, timestamp` (复合索引)
   - `activity_type` (普通索引)
   - `timestamp` (普通索引)

5. **系统指标索引**
   - `metric_type, timestamp` (复合索引)
   - `metric_name` (普通索引)

## 数据完整性约束

### 外键约束

```sql
-- 用户知识库关系
ALTER TABLE knowledge_bases 
ADD CONSTRAINT fk_kb_user 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 文档知识库关系
ALTER TABLE documents 
ADD CONSTRAINT fk_doc_kb 
FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE;

-- 用户活动日志关系
ALTER TABLE user_activity_logs 
ADD CONSTRAINT fk_activity_user 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
```

### 检查约束

```sql
-- 邮箱格式检查
ALTER TABLE users 
ADD CONSTRAINT chk_email_format 
CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- 密码长度检查
ALTER TABLE users 
ADD CONSTRAINT chk_password_length 
CHECK (length(hashed_password) >= 60);

-- 性能指标值范围检查
ALTER TABLE system_metrics 
ADD CONSTRAINT chk_metric_value 
CHECK (metric_value >= 0);
```

## 数据迁移

### 迁移文件结构

```
migrations/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_user_tables.py
│   ├── 003_add_knowledge_base_tables.py
│   ├── 004_add_analytics_tables.py
│   ├── 005_add_health_monitoring.py
│   ├── 006_add_rbac_system.py
│   ├── 007_add_security_features.py
│   └── 008_add_integration_support.py
└── alembic.ini
```

### 迁移命令

```bash
# 生成新迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

## 性能优化

### 查询优化

1. **使用适当的索引**
   - 为频繁查询的字段创建索引
   - 避免过多的索引影响写入性能

2. **分页查询优化**
   ```python
   # 使用 LIMIT 和 OFFSET
   query = select(User).offset(skip).limit(limit)
   
   # 使用游标分页（更高效）
   query = select(User).where(User.id > last_id).limit(limit)
   ```

3. **预加载关联数据**
   ```python
   # 使用 selectinload 避免 N+1 查询
   query = select(User).options(selectinload(User.knowledge_bases))
   ```

### 数据库连接池

```python
# 连接池配置
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # 连接池大小
    max_overflow=30,       # 最大溢出连接
    pool_timeout=30,       # 连接超时
    pool_recycle=3600,     # 连接回收时间
    echo=False             # 生产环境关闭SQL日志
)
```

## 备份策略

### 自动备份

1. **每日全量备份**
   ```bash
   # PostgreSQL
   pg_dump -h localhost -U user -d embedai > backup_$(date +%Y%m%d).sql
   
   # MySQL
   mysqldump -u user -p embedai > backup_$(date +%Y%m%d).sql
   ```

2. **增量备份**
   - 使用WAL日志进行增量备份
   - 定期清理旧的备份文件

### 数据恢复

```bash
# PostgreSQL恢复
psql -h localhost -U user -d embedai < backup_20240805.sql

# MySQL恢复
mysql -u user -p embedai < backup_20240805.sql
```

## 监控指标

### 关键指标

1. **连接数监控**
   - 活跃连接数
   - 连接池使用率
   - 连接等待时间

2. **查询性能监控**
   - 慢查询日志
   - 查询执行时间
   - 锁等待时间

3. **存储监控**
   - 数据库大小
   - 表大小增长
   - 索引使用率

### 监控工具

- **PostgreSQL**: pg_stat_statements, pgAdmin
- **MySQL**: Performance Schema, MySQL Workbench
- **通用**: Prometheus + Grafana

## 安全考虑

### 数据加密

1. **传输加密**
   - 使用SSL/TLS连接
   - 配置证书验证

2. **存储加密**
   - 敏感字段加密存储
   - 数据库文件加密

### 访问控制

1. **数据库用户权限**
   ```sql
   -- 创建只读用户
   CREATE USER readonly_user WITH PASSWORD 'password';
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
   
   -- 创建应用用户
   CREATE USER app_user WITH PASSWORD 'password';
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
   ```

2. **行级安全**
   ```sql
   -- 启用行级安全
   ALTER TABLE user_data ENABLE ROW LEVEL SECURITY;
   
   -- 创建策略
   CREATE POLICY user_data_policy ON user_data
   FOR ALL TO app_user
   USING (user_id = current_setting('app.current_user_id')::int);
   ```

## 故障排除

### 常见问题

1. **连接池耗尽**
   - 检查连接泄漏
   - 调整连接池大小
   - 优化长时间运行的查询

2. **死锁问题**
   - 分析死锁日志
   - 优化事务顺序
   - 减少事务持有时间

3. **性能下降**
   - 检查索引使用情况
   - 分析慢查询日志
   - 更新表统计信息

### 诊断工具

```sql
-- PostgreSQL 查看活跃连接
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- 查看锁等待
SELECT * FROM pg_locks WHERE NOT granted;

-- 查看表大小
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```
