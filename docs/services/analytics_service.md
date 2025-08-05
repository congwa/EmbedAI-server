# AnalyticsService 分析服务类

## 概述

`AnalyticsService` 是系统分析和统计的核心服务类，提供用户活动跟踪、系统性能监控、知识库使用统计、成本分析等功能。

## 类定义

```python
from app.services.analytics import AnalyticsService
```

**文件路径**: `app/services/analytics.py`

## 类初始化

### 构造函数

```python
def __init__(self, db: AsyncSession)
```

**参数**:
- `db` (AsyncSession): 异步数据库会话对象

**示例**:
```python
from app.models.database import AsyncSessionLocal
from app.services.analytics import AnalyticsService

async with AsyncSessionLocal() as db:
    analytics_service = AnalyticsService(db)
```

## 核心方法

### 1. 获取系统概览

```python
async def get_system_overview(self) -> SystemOverviewResponse
```

**功能**: 获取系统整体概览数据，包括用户统计、知识库统计、查询统计等

**返回值**:
- `SystemOverviewResponse`: 系统概览数据模型
  - `total_users` (int): 总用户数
  - `active_users` (int): 活跃用户数（最近7天）
  - `total_knowledge_bases` (int): 知识库总数
  - `total_documents` (int): 文档总数
  - `total_queries` (int): 查询总数
  - `system_uptime` (float): 系统运行时间百分比

**使用示例**:
```python
overview = await analytics_service.get_system_overview()
print(f"总用户数: {overview.total_users}")
print(f"活跃用户数: {overview.active_users}")
print(f"知识库数量: {overview.total_knowledge_bases}")
print(f"系统运行时间: {overview.system_uptime}%")
```

### 2. 获取用户活动统计

```python
async def get_user_activity_stats(
    self,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[int] = None,
    activity_type: Optional[str] = None,
    limit: int = 100
) -> UserActivityStats
```

**功能**: 获取用户活动的详细统计信息

**参数**:
- `start_date` (datetime, 可选): 开始日期，默认为7天前
- `end_date` (datetime, 可选): 结束日期，默认为当前时间
- `user_id` (int, 可选): 特定用户ID过滤
- `activity_type` (str, 可选): 活动类型过滤
- `limit` (int): 返回记录数限制，默认100

**返回值**:
- `UserActivityStats`: 用户活动统计数据
  - `total_activities` (int): 总活动数
  - `unique_users` (int): 唯一用户数
  - `activity_breakdown` (Dict): 活动类型分布
  - `daily_trends` (List): 每日趋势数据
  - `most_active_users` (List): 最活跃用户列表

**使用示例**:
```python
from datetime import datetime, timedelta

# 获取最近7天的用户活动统计
start_date = datetime.now() - timedelta(days=7)
stats = await analytics_service.get_user_activity_stats(
    start_date=start_date,
    limit=50
)

print(f"总活动数: {stats.total_activities}")
print(f"唯一用户数: {stats.unique_users}")
print("活动类型分布:")
for activity_type, count in stats.activity_breakdown.items():
    print(f"  {activity_type}: {count}")

# 获取特定用户的活动
user_stats = await analytics_service.get_user_activity_stats(
    user_id=1,
    start_date=start_date
)
print(f"用户1的活动数: {user_stats.total_activities}")
```

### 3. 获取知识库统计

```python
async def get_knowledge_base_stats(
    self,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    knowledge_base_id: Optional[int] = None,
    limit: int = 20
) -> KnowledgeBaseStats
```

**功能**: 获取知识库使用统计和性能数据

**参数**:
- `start_date` (datetime, 可选): 开始日期
- `end_date` (datetime, 可选): 结束日期
- `knowledge_base_id` (int, 可选): 特定知识库ID
- `limit` (int): 返回数量限制

**返回值**:
- `KnowledgeBaseStats`: 知识库统计数据
  - `total_knowledge_bases` (int): 知识库总数
  - `active_knowledge_bases` (int): 活跃知识库数
  - `total_documents` (int): 文档总数
  - `total_queries` (int): 查询总数
  - `average_accuracy` (float): 平均准确率
  - `top_knowledge_bases` (List): 热门知识库列表

**使用示例**:
```python
# 获取所有知识库统计
kb_stats = await analytics_service.get_knowledge_base_stats(limit=10)
print(f"知识库总数: {kb_stats.total_knowledge_bases}")
print(f"平均准确率: {kb_stats.average_accuracy}%")

print("热门知识库:")
for kb in kb_stats.top_knowledge_bases:
    print(f"  {kb.name}: {kb.query_count} 次查询")

# 获取特定知识库统计
specific_kb_stats = await analytics_service.get_knowledge_base_stats(
    knowledge_base_id=1
)
```

### 4. 获取性能指标

```python
async def get_performance_metrics(
    self,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    metric_type: Optional[str] = None
) -> PerformanceMetrics
```

**功能**: 获取系统性能相关的指标数据

**参数**:
- `start_date` (datetime, 可选): 开始日期
- `end_date` (datetime, 可选): 结束日期
- `metric_type` (str, 可选): 指标类型过滤

**返回值**:
- `PerformanceMetrics`: 性能指标数据
  - `average_response_time` (float): 平均响应时间
  - `total_requests` (int): 总请求数
  - `error_rate` (float): 错误率
  - `uptime_percentage` (float): 运行时间百分比
  - `resource_usage` (Dict): 资源使用情况

**使用示例**:
```python
# 获取最近24小时的性能指标
start_date = datetime.now() - timedelta(hours=24)
metrics = await analytics_service.get_performance_metrics(
    start_date=start_date
)

print(f"平均响应时间: {metrics.average_response_time}ms")
print(f"总请求数: {metrics.total_requests}")
print(f"错误率: {metrics.error_rate}%")
print(f"系统运行时间: {metrics.uptime_percentage}%")

# 获取特定类型的指标
cpu_metrics = await analytics_service.get_performance_metrics(
    metric_type="cpu_usage"
)
```

### 5. 获取成本分析

```python
async def get_cost_analysis(
    self,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    breakdown_by: str = "service"
) -> CostAnalysis
```

**功能**: 获取系统运营成本的详细分析

**参数**:
- `start_date` (datetime, 可选): 开始日期
- `end_date` (datetime, 可选): 结束日期
- `breakdown_by` (str): 分解维度，可选值：service, user, knowledge_base

**返回值**:
- `CostAnalysis`: 成本分析数据
  - `total_cost` (float): 总成本
  - `cost_breakdown` (Dict): 成本分解
  - `daily_costs` (List): 每日成本
  - `projections` (Dict): 成本预测

**使用示例**:
```python
# 获取本月成本分析
from datetime import date
start_date = datetime(date.today().year, date.today().month, 1)
cost_analysis = await analytics_service.get_cost_analysis(
    start_date=start_date,
    breakdown_by="service"
)

print(f"总成本: ${cost_analysis.total_cost:.2f}")
print("成本分解:")
for service, cost in cost_analysis.cost_breakdown.items():
    print(f"  {service}: ${cost:.2f}")

# 按用户分解成本
user_cost_analysis = await analytics_service.get_cost_analysis(
    breakdown_by="user"
)
```

### 6. 获取时间序列数据

```python
async def get_time_series_data(
    self,
    metric_name: str,
    start_date: datetime,
    end_date: datetime,
    granularity: str = "hour"
) -> TimeSeriesData
```

**功能**: 获取指定指标的时间序列数据

**参数**:
- `metric_name` (str): 指标名称
- `start_date` (datetime): 开始日期
- `end_date` (datetime): 结束日期
- `granularity` (str): 数据粒度，可选值：minute, hour, day

**返回值**:
- `TimeSeriesData`: 时间序列数据
  - `metric_name` (str): 指标名称
  - `timestamps` (List[datetime]): 时间戳列表
  - `values` (List[float]): 数值列表
  - `granularity` (str): 数据粒度

**使用示例**:
```python
# 获取最近24小时的响应时间数据
start_date = datetime.now() - timedelta(hours=24)
end_date = datetime.now()

response_time_data = await analytics_service.get_time_series_data(
    metric_name="response_time",
    start_date=start_date,
    end_date=end_date,
    granularity="hour"
)

print(f"指标: {response_time_data.metric_name}")
print(f"数据点数: {len(response_time_data.values)}")
for timestamp, value in zip(response_time_data.timestamps, response_time_data.values):
    print(f"{timestamp}: {value}ms")
```

### 7. 记录用户活动

```python
async def log_user_activity(
    self,
    user_id: int,
    activity_type: str,
    activity_details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> UserActivityLog
```

**功能**: 记录用户活动日志

**参数**:
- `user_id` (int): 用户ID
- `activity_type` (str): 活动类型
- `activity_details` (Dict, 可选): 活动详情
- `ip_address` (str, 可选): IP地址
- `user_agent` (str, 可选): 用户代理

**返回值**:
- `UserActivityLog`: 创建的活动日志对象

**使用示例**:
```python
# 记录用户登录活动
login_log = await analytics_service.log_user_activity(
    user_id=1,
    activity_type="login",
    activity_details={"login_method": "email"},
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)

# 记录文档上传活动
upload_log = await analytics_service.log_user_activity(
    user_id=1,
    activity_type="document_upload",
    activity_details={
        "document_name": "API文档.pdf",
        "knowledge_base_id": 1,
        "file_size": "2.5MB"
    }
)
```

### 8. 记录系统指标

```python
async def record_system_metric(
    self,
    metric_type: str,
    metric_name: str,
    metric_value: float,
    metric_unit: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> SystemMetrics
```

**功能**: 记录系统性能指标

**参数**:
- `metric_type` (str): 指标类型
- `metric_name` (str): 指标名称
- `metric_value` (float): 指标值
- `metric_unit` (str, 可选): 指标单位
- `extra_metadata` (Dict, 可选): 额外元数据

**返回值**:
- `SystemMetrics`: 创建的系统指标对象

**使用示例**:
```python
# 记录CPU使用率
cpu_metric = await analytics_service.record_system_metric(
    metric_type="system",
    metric_name="cpu_usage",
    metric_value=75.5,
    metric_unit="percent"
)

# 记录API响应时间
response_time_metric = await analytics_service.record_system_metric(
    metric_type="api",
    metric_name="response_time",
    metric_value=125.0,
    metric_unit="ms",
    extra_metadata={"endpoint": "/api/v1/users"}
)
```

### 9. 生成分析报告

```python
async def generate_analytics_report(
    self,
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

**功能**: 生成综合分析报告

**参数**:
- `report_type` (str): 报告类型：daily, weekly, monthly
- `start_date` (datetime): 开始日期
- `end_date` (datetime): 结束日期
- `filters` (Dict, 可选): 过滤条件

**返回值**:
- `Dict[str, Any]`: 综合分析报告数据

**使用示例**:
```python
# 生成周报
start_date = datetime.now() - timedelta(days=7)
end_date = datetime.now()

weekly_report = await analytics_service.generate_analytics_report(
    report_type="weekly",
    start_date=start_date,
    end_date=end_date
)

print("周报摘要:")
print(f"总用户活动: {weekly_report['user_activities']['total']}")
print(f"新增用户: {weekly_report['user_growth']['new_users']}")
print(f"系统平均响应时间: {weekly_report['performance']['avg_response_time']}ms")

# 生成特定知识库的月报
monthly_report = await analytics_service.generate_analytics_report(
    report_type="monthly",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    filters={"knowledge_base_id": 1}
)
```

### 10. 获取实时统计

```python
async def get_real_time_stats(self) -> Dict[str, Any]
```

**功能**: 获取实时系统统计数据

**返回值**:
- `Dict[str, Any]`: 实时统计数据
  - `online_users` (int): 在线用户数
  - `current_requests` (int): 当前请求数
  - `system_load` (float): 系统负载
  - `memory_usage` (float): 内存使用率

**使用示例**:
```python
real_time_stats = await analytics_service.get_real_time_stats()
print(f"在线用户: {real_time_stats['online_users']}")
print(f"当前请求数: {real_time_stats['current_requests']}")
print(f"系统负载: {real_time_stats['system_load']}")
print(f"内存使用率: {real_time_stats['memory_usage']}%")
```

## 数据模型

### SystemOverviewResponse

```python
class SystemOverviewResponse(BaseModel):
    total_users: int
    active_users: int
    total_knowledge_bases: int
    total_documents: int
    total_queries: int
    system_uptime: float
```

### UserActivityStats

```python
class UserActivityStats(BaseModel):
    total_activities: int
    unique_users: int
    activity_breakdown: Dict[str, int]
    daily_trends: List[Dict[str, Any]]
    most_active_users: List[Dict[str, Any]]
```

### PerformanceMetrics

```python
class PerformanceMetrics(BaseModel):
    average_response_time: float
    total_requests: int
    error_rate: float
    uptime_percentage: float
    resource_usage: Dict[str, float]
```

## 最佳实践

### 1. 数据聚合优化

```python
# 使用数据库聚合函数提高性能
async def get_efficient_stats(self):
    # 一次查询获取多个统计数据
    result = await self.db.execute(
        select(
            func.count(User.id).label('total_users'),
            func.count(case((User.is_active == True, 1))).label('active_users'),
            func.count(KnowledgeBase.id).label('total_kbs')
        ).select_from(User).outerjoin(KnowledgeBase)
    )
    return result.first()
```

### 2. 缓存策略

```python
from app.core.redis_manager import redis_manager

async def get_cached_overview(self):
    # 尝试从缓存获取
    cached_data = await redis_manager.get("system_overview")
    if cached_data:
        return json.loads(cached_data)
    
    # 计算新数据
    overview = await self.get_system_overview()
    
    # 缓存5分钟
    await redis_manager.setex(
        "system_overview", 
        300, 
        json.dumps(overview.dict())
    )
    
    return overview
```

### 3. 异步批量处理

```python
async def batch_log_activities(self, activities: List[Dict]):
    # 批量插入活动日志
    activity_objects = [
        UserActivityLog(**activity) for activity in activities
    ]
    
    self.db.add_all(activity_objects)
    await self.db.commit()
```

## 性能考虑

1. **索引优化**: 确保时间戳字段有适当的索引
2. **数据分区**: 对大量历史数据进行分区
3. **聚合表**: 创建预聚合的统计表
4. **缓存策略**: 缓存频繁查询的统计数据
5. **异步处理**: 使用异步任务处理重型分析任务
