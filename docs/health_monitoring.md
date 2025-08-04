# System Health Monitoring

## Overview

The System Health Monitoring module provides comprehensive real-time monitoring of system components, services, and infrastructure. It includes automated health checks, alerting, performance tracking, and uptime monitoring to ensure system reliability and early detection of issues.

## Features

### 1. Service Health Monitoring
- **Automated Health Checks**: Configurable health checks for various services
- **Real-time Status Tracking**: Monitor service status in real-time
- **Response Time Monitoring**: Track service response times and performance
- **Multi-check Support**: HTTP endpoints, command execution, and custom checks
- **Retry Logic**: Configurable retry attempts for failed checks

### 2. System Resource Monitoring
- **CPU Usage**: Real-time CPU utilization tracking
- **Memory Usage**: Memory consumption monitoring
- **Disk Usage**: Disk space utilization tracking
- **Network Statistics**: Network I/O monitoring
- **System Load**: System load average tracking

### 3. Alert Management
- **Automated Alerts**: Automatic alert generation based on thresholds
- **Alert Levels**: Info, Warning, Error, and Critical alert levels
- **Alert Resolution**: Track alert resolution and responsible parties
- **Notification System**: Extensible notification system for various channels
- **Alert History**: Complete audit trail of all alerts

### 4. Performance Thresholds
- **Configurable Thresholds**: Set warning and critical thresholds for metrics
- **Dynamic Monitoring**: Real-time threshold monitoring
- **Threshold Management**: Web-based threshold configuration
- **Multiple Operators**: Support for various comparison operators

### 5. Uptime Tracking
- **Service Uptime**: Track uptime percentage for each service
- **Historical Data**: Maintain historical uptime records
- **SLA Monitoring**: Monitor against service level agreements
- **Downtime Analysis**: Track and analyze downtime incidents

## API Endpoints

### Health Dashboard
```http
GET /api/v1/admin/health/dashboard
```

Returns comprehensive health monitoring dashboard data including system overview, service status, recent alerts, and resource metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "overall_status": "healthy",
      "healthy_services": 8,
      "warning_services": 1,
      "critical_services": 0,
      "total_services": 9,
      "system_uptime": 168.5,
      "last_check": "2024-08-04T14:30:00Z"
    },
    "services": [...],
    "recent_alerts": [...],
    "system_resources": {...},
    "uptime_trends": [...]
  }
}
```

### System Health Overview
```http
GET /api/v1/admin/health/overview
```

Returns high-level system health overview with service counts and overall status.

### Service Health Status
```http
GET /api/v1/admin/health/services?service_name=database&limit=50
```

**Parameters:**
- `service_name` (optional): Filter by specific service name
- `limit` (optional): Number of records to return (1-200, default: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "service_name": "database",
      "service_type": "database",
      "status": "healthy",
      "response_time": 15.5,
      "error_message": null,
      "details": {
        "record_count": 1250
      },
      "timestamp": "2024-08-04T14:30:00Z",
      "uptime_percentage": 99.8
    }
  ]
}
```

### Manual Health Check
```http
POST /api/v1/admin/health/services/{service_name}/check
```

Triggers a manual health check for the specified service.

### System Resource Metrics
```http
GET /api/v1/admin/health/resources
```

Returns current system resource utilization metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "cpu_usage": 25.5,
    "memory_usage": 68.2,
    "memory_total": 8589934592,
    "memory_used": 5858934592,
    "disk_usage": 45.8,
    "disk_total": 1000000000000,
    "disk_used": 458000000000,
    "network_bytes_sent": 1024000000,
    "network_bytes_recv": 2048000000,
    "load_average": 1.25,
    "timestamp": "2024-08-04T14:30:00Z"
  }
}
```

### System Alerts
```http
GET /api/v1/admin/health/alerts?level=critical&is_resolved=false&limit=50
```

**Parameters:**
- `level` (optional): Filter by alert level (info, warning, error, critical)
- `alert_type` (optional): Filter by alert type
- `is_resolved` (optional): Filter by resolution status
- `start_date` (optional): Filter by creation date range
- `end_date` (optional): Filter by creation date range
- `limit` (optional): Number of alerts to return (1-200, default: 50)

### Create Alert
```http
POST /api/v1/admin/health/alerts
```

**Request Body:**
```json
{
  "alert_type": "service_health",
  "level": "critical",
  "title": "Database Connection Failed",
  "message": "Unable to connect to primary database",
  "source": "database",
  "metadata": {
    "error_code": "CONNECTION_TIMEOUT",
    "retry_count": 3
  }
}
```

### Resolve Alert
```http
PUT /api/v1/admin/health/alerts/{alert_id}/resolve
```

**Request Body:**
```json
{
  "resolved_by": "admin@example.com",
  "resolution_note": "Database connection restored after server restart"
}
```

## Data Models

### ServiceHealth
Stores health check results for individual services.

**Fields:**
- `id`: Unique identifier
- `service_name`: Name of the service being monitored
- `service_type`: Type of service (database, redis, api, etc.)
- `status`: Health status (healthy, warning, critical, unknown)
- `response_time`: Response time in milliseconds
- `error_message`: Error message if check failed
- `details`: Additional check details as JSON
- `timestamp`: When the check was performed

### SystemAlert
Stores system alerts and notifications.

**Fields:**
- `id`: Unique identifier
- `alert_type`: Type of alert (service_health, performance, etc.)
- `level`: Alert severity level
- `title`: Alert title
- `message`: Detailed alert message
- `source`: Source of the alert
- `alert_metadata`: Additional alert data as JSON
- `is_resolved`: Whether the alert has been resolved
- `resolved_at`: When the alert was resolved
- `resolved_by`: Who resolved the alert
- `created_at`: When the alert was created

### PerformanceThreshold
Defines performance thresholds for monitoring.

**Fields:**
- `id`: Unique identifier
- `metric_name`: Name of the metric
- `metric_type`: Type of metric
- `warning_threshold`: Warning threshold value
- `critical_threshold`: Critical threshold value
- `comparison_operator`: Comparison operator (gt, lt, eq, etc.)
- `unit`: Unit of measurement
- `description`: Threshold description
- `is_enabled`: Whether threshold monitoring is enabled

### HealthCheckConfig
Configuration for automated health checks.

**Fields:**
- `id`: Unique identifier
- `service_name`: Service name
- `service_type`: Service type
- `check_interval`: Check interval in seconds
- `timeout`: Check timeout in seconds
- `retry_count`: Number of retries on failure
- `is_enabled`: Whether the check is enabled
- `check_url`: URL for HTTP checks
- `check_command`: Command for command-line checks
- `expected_response`: Expected response for validation
- `config_data`: Additional configuration as JSON

### UptimeRecord
Stores daily uptime statistics for services.

**Fields:**
- `id`: Unique identifier
- `service_name`: Service name
- `date`: Date of the record
- `total_checks`: Total number of checks performed
- `successful_checks`: Number of successful checks
- `failed_checks`: Number of failed checks
- `uptime_percentage`: Uptime percentage for the day
- `avg_response_time`: Average response time
- `max_response_time`: Maximum response time
- `min_response_time`: Minimum response time
- `downtime_duration`: Total downtime in seconds

## Health Check Types

### HTTP Health Checks
Monitor web services and APIs by making HTTP requests.

**Configuration:**
```json
{
  "service_name": "api_server",
  "service_type": "api",
  "check_url": "http://localhost:8000/health",
  "expected_response": "OK",
  "timeout": 30,
  "check_interval": 60
}
```

### Command Health Checks
Execute system commands to check service status.

**Configuration:**
```json
{
  "service_name": "nginx",
  "service_type": "web_server",
  "check_command": "systemctl is-active nginx",
  "expected_response": "active",
  "timeout": 10,
  "check_interval": 120
}
```

### Database Health Checks
Check database connectivity and performance.

**Configuration:**
```json
{
  "service_name": "postgres",
  "service_type": "database",
  "config_data": {
    "connection_string": "postgresql://user:pass@localhost/db"
  },
  "timeout": 15,
  "check_interval": 60
}
```

### Redis Health Checks
Monitor Redis server connectivity and performance.

**Configuration:**
```json
{
  "service_name": "redis",
  "service_type": "cache",
  "config_data": {
    "host": "localhost",
    "port": 6379
  },
  "timeout": 10,
  "check_interval": 60
}
```

## Automated Health Check Scheduler

The system includes an automated scheduler that runs health checks based on configured intervals.

### Starting the Scheduler
```python
from app.services.health_monitor import health_scheduler

# Start the health check scheduler
await health_scheduler.start()
```

### Stopping the Scheduler
```python
# Stop the health check scheduler
await health_scheduler.stop()
```

### Configuration
Health checks are automatically scheduled based on the `HealthCheckConfig` table. Each enabled configuration creates a background task that runs at the specified interval.

## Alert Notification System

The system supports extensible alert notifications through various channels.

### Supported Channels
- **Logging**: All alerts are logged to the system log
- **Redis**: Real-time alerts are stored in Redis for immediate access
- **Email**: Email notifications (configurable)
- **Slack**: Slack webhook notifications (configurable)
- **Custom**: Extensible for additional notification channels

### Notification Configuration
```python
# Example notification configuration
NOTIFICATION_CHANNELS = {
    "email": {
        "enabled": True,
        "smtp_server": "smtp.example.com",
        "recipients": ["admin@example.com"]
    },
    "slack": {
        "enabled": True,
        "webhook_url": "https://hooks.slack.com/services/..."
    }
}
```

## Performance Thresholds

Define custom thresholds for automatic alert generation.

### Default Thresholds
```json
[
  {
    "metric_name": "cpu_usage",
    "warning_threshold": 80.0,
    "critical_threshold": 95.0,
    "comparison_operator": "gt",
    "unit": "%"
  },
  {
    "metric_name": "memory_usage",
    "warning_threshold": 85.0,
    "critical_threshold": 95.0,
    "comparison_operator": "gt",
    "unit": "%"
  },
  {
    "metric_name": "disk_usage",
    "warning_threshold": 80.0,
    "critical_threshold": 90.0,
    "comparison_operator": "gt",
    "unit": "%"
  },
  {
    "metric_name": "response_time",
    "warning_threshold": 2000.0,
    "critical_threshold": 5000.0,
    "comparison_operator": "gt",
    "unit": "ms"
  }
]
```
