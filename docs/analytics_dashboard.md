# Analytics & Reporting Dashboard

## Overview

The Analytics & Reporting Dashboard provides comprehensive insights into system performance, user activity, knowledge base usage, and cost analysis. This module automatically collects metrics and provides both real-time and historical analytics.

## Features

### 1. System Overview Dashboard
- **Active Users**: Number of users active in the last 7 days
- **Total Users**: Total registered users in the system
- **Knowledge Bases**: Total number of knowledge bases
- **Total Documents**: Total number of documents across all knowledge bases
- **Total Queries**: Total number of queries processed
- **System Uptime**: Current system uptime in hours
- **Average Response Time**: Average API response time
- **Success Rate**: Percentage of successful API calls
- **Total Cost**: Total LLM usage costs

### 2. User Activity Analytics
- **Login Frequency**: Track user login patterns
- **Session Duration**: Average session length per user
- **Usage Patterns**: Identify most active users and usage trends
- **Activity Timeline**: Detailed activity logs with timestamps

### 3. Knowledge Base Statistics
- **Query Counts**: Number of queries per knowledge base
- **Success Rates**: Query success rates by knowledge base
- **Response Times**: Average response times per knowledge base
- **Cost Analysis**: LLM costs per knowledge base
- **User Engagement**: Unique users per knowledge base

### 4. Performance Metrics
- **API Response Times**: Real-time and historical response time tracking
- **Error Rates**: Track API error rates and patterns
- **Throughput**: Requests per second metrics
- **System Resources**: CPU, memory, and disk usage monitoring

### 5. Cost Analysis
- **Total Costs**: Overall LLM usage costs
- **Cost Breakdown**: Costs by model, user, and knowledge base
- **Daily Trends**: Daily cost analysis and trends
- **Budget Tracking**: Monitor spending against budgets

## API Endpoints

### Dashboard Data
```http
GET /api/v1/admin/analytics/dashboard
```

Returns comprehensive dashboard data including overview, recent activities, top knowledge bases, performance trends, and cost summary.

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "active_users": 25,
      "total_users": 100,
      "knowledge_bases": 15,
      "total_documents": 500,
      "total_queries": 10000,
      "system_uptime": 168.5,
      "avg_response_time": 0.85,
      "success_rate": 98.5,
      "total_cost": 125.50
    },
    "recent_activities": [...],
    "top_knowledge_bases": [...],
    "performance_trends": [...],
    "cost_summary": {...},
    "alerts": [...]
  }
}
```

### System Overview
```http
GET /api/v1/admin/analytics/overview
```

Returns system-wide statistics and metrics.

### User Activity Statistics
```http
GET /api/v1/admin/analytics/users/activity?limit=20&start_date=2024-01-01&end_date=2024-12-31
```

**Parameters:**
- `limit` (optional): Number of users to return (1-100, default: 20)
- `start_date` (optional): Start date for activity analysis
- `end_date` (optional): End date for activity analysis

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "user_id": 1,
      "email": "user@example.com",
      "login_count": 45,
      "last_login": "2024-08-04T10:30:00Z",
      "session_duration_avg": 25.5,
      "total_queries": 150,
      "active_days": 20
    }
  ]
}
```

### Knowledge Base Statistics
```http
GET /api/v1/admin/analytics/knowledge-bases/stats?limit=10&start_date=2024-01-01&end_date=2024-12-31
```

**Parameters:**
- `limit` (optional): Number of knowledge bases to return (1-50, default: 10)
- `start_date` (optional): Start date for statistics
- `end_date` (optional): End date for statistics

### Performance Metrics
```http
GET /api/v1/admin/analytics/performance/metrics?hours=24&granularity=hour
```

**Parameters:**
- `hours` (optional): Time range in hours (1-168, default: 24)
- `granularity` (optional): Time granularity - "hour" or "day" (default: "hour")

### Cost Analysis
```http
GET /api/v1/admin/analytics/costs/analysis?start_date=2024-01-01&end_date=2024-12-31&user_id=1&kb_id=5
```

**Parameters:**
- `start_date` (optional): Start date for cost analysis
- `end_date` (optional): End date for cost analysis
- `user_id` (optional): Filter by specific user
- `kb_id` (optional): Filter by specific knowledge base

### Export Analytics Data
```http
POST /api/v1/admin/analytics/export
```

**Request Body:**
```json
{
  "report_type": "overview",
  "format": "csv",
  "filters": {
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z",
    "user_id": null,
    "kb_id": null
  },
  "include_charts": false
}
```

**Supported Report Types:**
- `overview`: System overview statistics
- `users`: User activity statistics
- `knowledge_bases`: Knowledge base statistics
- `costs`: Cost analysis data

**Supported Formats:**
- `csv`: Comma-separated values
- `json`: JSON format
- `pdf`: PDF report (coming soon)

## Data Models

### SystemMetrics
Stores system-level performance and usage metrics.

**Fields:**
- `id`: Unique identifier
- `metric_type`: Type of metric (e.g., "system", "performance")
- `metric_name`: Name of the metric
- `metric_value`: Numeric value of the metric
- `metric_unit`: Unit of measurement
- `extra_metadata`: Additional metadata as JSON
- `timestamp`: When the metric was recorded

### UserActivityLog
Tracks detailed user activity records.

**Fields:**
- `id`: Unique identifier
- `user_id`: Associated user ID
- `session_id`: Session identifier
- `activity_type`: Type of activity (e.g., "login", "api_call")
- `activity_details`: Activity details as JSON
- `ip_address`: User's IP address
- `user_agent`: User's browser/client information
- `timestamp`: When the activity occurred
- `duration`: Duration of the activity in seconds

### KnowledgeBaseMetrics
Stores knowledge base usage statistics and performance metrics.

**Fields:**
- `id`: Unique identifier
- `knowledge_base_id`: Associated knowledge base ID
- `metric_date`: Date for the metrics
- `query_count`: Number of queries
- `success_count`: Number of successful queries
- `error_count`: Number of failed queries
- `avg_response_time`: Average response time in seconds
- `total_tokens_used`: Total tokens consumed
- `total_cost`: Total cost incurred
- `unique_users`: Number of unique users

### APIMetrics
Stores API call performance and usage statistics.

**Fields:**
- `id`: Unique identifier
- `endpoint`: API endpoint path
- `method`: HTTP method
- `status_code`: HTTP status code
- `response_time`: Response time in seconds
- `user_id`: Associated user ID (if authenticated)
- `ip_address`: Client IP address
- `timestamp`: When the API call was made

## Automatic Data Collection

The analytics system automatically collects data through middleware:

### AnalyticsMiddleware
- Captures all API calls and response times
- Records user activities for authenticated requests
- Collects system performance metrics periodically
- Stores data in both database and Redis for real-time access

### SystemMetricsCollector
- Background service that collects system metrics every 60 seconds
- Monitors CPU, memory, disk usage, and network statistics
- Tracks application-specific metrics

## Configuration

### Environment Variables
```bash
# Analytics configuration
ANALYTICS_ENABLED=true
ANALYTICS_RETENTION_DAYS=90
SYSTEM_METRICS_INTERVAL=60
```

### Redis Configuration
Analytics data is cached in Redis for real-time access:
- `api_metrics:realtime`: Recent API metrics (1 hour retention)
- `system_metrics:current`: Current system metrics (5 minutes retention)

## Usage Examples

### Frontend Integration
```javascript
// Fetch dashboard data
const response = await fetch('/api/v1/admin/analytics/dashboard', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const dashboardData = await response.json();

// Display metrics
console.log(`Active Users: ${dashboardData.data.overview.active_users}`);
console.log(`Success Rate: ${dashboardData.data.overview.success_rate}%`);
```

### Export Data
```bash
# Export user activity data as CSV
curl -X POST "http://localhost:8000/api/v1/admin/analytics/export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "users",
    "format": "csv",
    "filters": {
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-12-31T23:59:59Z"
    }
  }' \
  --output user_activity_report.csv
```

## Security Considerations

1. **Admin Access Only**: All analytics endpoints require admin authentication
2. **Data Privacy**: Personal user data is anonymized in exports
3. **Rate Limiting**: Analytics endpoints are rate-limited to prevent abuse
4. **Data Retention**: Automatic cleanup of old analytics data based on retention policy

## Performance Considerations

1. **Asynchronous Collection**: Metrics collection doesn't block request processing
2. **Batch Processing**: Metrics are processed in batches for efficiency
3. **Redis Caching**: Real-time data is cached for fast access
4. **Database Indexing**: Proper indexing on timestamp and foreign key fields

## Troubleshooting

### Common Issues

1. **Missing Data**: Check if AnalyticsMiddleware is properly configured
2. **Slow Queries**: Ensure database indexes are created
3. **High Memory Usage**: Adjust Redis retention policies
4. **Export Failures**: Check disk space and permissions

### Monitoring

Monitor the analytics system itself:
- Check Redis memory usage
- Monitor database query performance
- Track middleware processing times
- Verify data collection completeness
