# System Configuration Management

## Overview

The System Configuration Management module provides a comprehensive web-based interface for managing system configurations, environment variables, and configuration templates. It offers centralized control over all system settings with features like validation, backup/restore, audit trails, and template-based configuration deployment.

## Core Features

### 1. System Configuration Management
- **Centralized Configuration**: Manage all system settings from a single interface
- **Type-Safe Values**: Support for string, integer, float, boolean, JSON, password, email, URL, and file path types
- **Validation Rules**: Custom validation with regex patterns and value constraints
- **Sensitive Data Protection**: Automatic masking of sensitive configuration values
- **Read-Only Protection**: System-critical configurations are protected from modification

### 2. Environment Variable Management
- **Environment Integration**: Manage environment variables with database persistence
- **OS Synchronization**: Sync environment variables to the operating system
- **Category Organization**: Organize variables by functional categories
- **Validation Support**: Custom validation rules for environment variables

### 3. Configuration Templates
- **Template-Based Deployment**: Pre-defined configuration sets for different environments
- **Version Control**: Template versioning for configuration management
- **Bulk Application**: Apply multiple configurations simultaneously
- **Custom Templates**: Create custom templates for specific use cases

### 4. Backup & Restore
- **Automated Backups**: Create configuration backups with metadata
- **Selective Backup**: Backup specific configuration categories
- **Point-in-Time Restore**: Restore configurations from any backup point
- **Conflict Resolution**: Handle configuration conflicts during restore

### 5. Audit & Monitoring
- **Change Tracking**: Complete audit trail of all configuration changes
- **User Attribution**: Track who made changes and when
- **Change Reasons**: Optional reason tracking for configuration modifications
- **Dashboard Analytics**: Visual overview of configuration status and changes

## Configuration Categories

### System (`SYSTEM`)
- **system_name**: System display name
- **system_version**: Current system version (read-only)
- **max_upload_size**: Maximum file upload size in MB
- **session_timeout**: User session timeout in seconds

### Database (`DATABASE`)
- **db_pool_size**: Database connection pool size
- **db_max_overflow**: Maximum connection pool overflow
- Connection settings and performance tuning

### Redis (`REDIS`)
- **redis_max_connections**: Maximum Redis connections
- **redis_timeout**: Redis connection timeout
- Cache and session storage settings

### Email (`EMAIL`)
- **smtp_host**: SMTP server hostname
- **smtp_port**: SMTP server port
- **smtp_username**: SMTP authentication username
- **smtp_password**: SMTP authentication password (sensitive)
- **smtp_use_tls**: Enable TLS encryption

### AI Model (`AI_MODEL`)
- **openai_api_key**: OpenAI API key (sensitive)
- **openai_base_url**: OpenAI API base URL
- **default_model**: Default AI model selection
- **max_tokens**: Maximum token limit
- **temperature**: Model temperature parameter

### Security (`SECURITY`)
- **password_min_length**: Minimum password length
- **password_require_uppercase**: Require uppercase letters
- **password_require_lowercase**: Require lowercase letters
- **password_require_numbers**: Require numbers
- **password_require_symbols**: Require special characters
- **max_login_attempts**: Maximum failed login attempts
- **account_lockout_duration**: Account lockout duration in seconds

### Logging (`LOGGING`)
- **log_level**: System logging level
- **log_max_size**: Maximum log file size in MB
- **log_backup_count**: Number of log file backups

### Monitoring (`MONITORING`)
- **health_check_interval**: Health check frequency in seconds
- **metrics_retention_days**: Metrics data retention period

## API Endpoints

### Configuration Dashboard

#### Get Dashboard Data
```http
GET /api/v1/admin/config/dashboard
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_configs": 30,
    "configs_by_category": {
      "SYSTEM": 4,
      "DATABASE": 2,
      "REDIS": 2,
      "EMAIL": 5,
      "AI_MODEL": 5,
      "SECURITY": 7,
      "LOGGING": 3,
      "MONITORING": 2
    },
    "sensitive_configs": 3,
    "readonly_configs": 1,
    "recent_changes": [...],
    "backup_count": 5,
    "template_count": 3,
    "env_var_count": 5
  }
}
```

### System Configuration Management

#### Create Configuration
```http
POST /api/v1/admin/config/configs
```

**Request Body:**
```json
{
  "key": "custom_setting",
  "value": "default_value",
  "default_value": "default_value",
  "description": "Custom system setting",
  "category": "SYSTEM",
  "type": "STRING",
  "is_sensitive": false,
  "is_required": true,
  "validation_rule": "^[a-zA-Z0-9_]+$",
  "min_value": "1",
  "max_value": "100"
}
```

#### Get Configurations
```http
GET /api/v1/admin/config/configs?category=SYSTEM&search=password&include_sensitive=false
```

#### Update Configuration
```http
PUT /api/v1/admin/config/configs/{config_id}
```

**Request Body:**
```json
{
  "value": "new_value",
  "description": "Updated description"
}
```

#### Batch Update Configurations
```http
POST /api/v1/admin/config/configs/batch-update
```

**Request Body:**
```json
{
  "configs": [
    {
      "id": 1,
      "value": "new_value_1"
    },
    {
      "id": 2,
      "value": "new_value_2"
    }
  ],
  "reason": "Bulk configuration update for performance optimization"
}
```

### Configuration Templates

#### Create Template
```http
POST /api/v1/admin/config/templates
```

**Request Body:**
```json
{
  "name": "Production Environment",
  "description": "Production-ready configuration template",
  "category": "SYSTEM",
  "template_data": {
    "log_level": {
      "value": "WARNING",
      "description": "Production log level",
      "category": "LOGGING",
      "type": "STRING"
    },
    "session_timeout": {
      "value": "7200",
      "description": "Extended session timeout",
      "category": "SECURITY",
      "type": "INTEGER"
    }
  },
  "version": "1.0.0"
}
```

#### Apply Template
```http
POST /api/v1/admin/config/templates/{template_id}/apply?overwrite_existing=true
```

### Configuration Backup & Restore

#### Create Backup
```http
POST /api/v1/admin/config/backups
```

**Request Body:**
```json
{
  "name": "Pre-deployment Backup",
  "description": "Backup before major system update",
  "categories": ["SYSTEM", "SECURITY", "AI_MODEL"]
}
```

### Environment Variables

#### Create Environment Variable
```http
POST /api/v1/admin/config/env-vars
```

**Request Body:**
```json
{
  "name": "CUSTOM_API_ENDPOINT",
  "value": "https://api.example.com",
  "description": "Custom API endpoint URL",
  "category": "INTEGRATION",
  "is_sensitive": false,
  "is_required": true,
  "validation_rule": "^https://.*",
  "restart_required": true
}
```

#### Sync Environment Variables
```http
POST /api/v1/admin/config/env-vars/sync
```

### Configuration Validation

#### Validate Configurations
```http
POST /api/v1/admin/config/validate
```

**Request Body:**
```json
{
  "configs": [
    {
      "key": "test_config",
      "value": "test_value",
      "type": "string",
      "validation_rule": "^[a-z]+$"
    }
  ]
}
```

### Import/Export

#### Export Configurations
```http
POST /api/v1/admin/config/export
```

**Request Body:**
```json
{
  "categories": ["SYSTEM", "SECURITY"],
  "include_sensitive": false,
  "format": "json"
}
```

#### Import Configurations
```http
POST /api/v1/admin/config/import
```

**Request Body:**
```json
{
  "data": {
    "config_key_1": {
      "value": "config_value_1",
      "description": "Imported configuration",
      "category": "SYSTEM",
      "type": "STRING"
    }
  },
  "overwrite_existing": false,
  "validate_only": false
}
```

## Configuration Types & Validation

### Supported Types

1. **STRING**: Text values with optional regex validation
2. **INTEGER**: Numeric values with min/max constraints
3. **FLOAT**: Decimal values with range validation
4. **BOOLEAN**: True/false values (accepts: true/false, 1/0, yes/no)
5. **JSON**: Valid JSON objects and arrays
6. **PASSWORD**: Sensitive text values (automatically masked)
7. **EMAIL**: Email addresses with format validation
8. **URL**: HTTP/HTTPS URLs with format validation
9. **FILE_PATH**: File system paths

### Validation Features

- **Regex Patterns**: Custom regular expression validation
- **Range Constraints**: Min/max values for numeric types
- **Required Fields**: Mandatory configuration validation
- **Options Lists**: Enumerated value selection
- **Type Checking**: Automatic type validation

## Security Features

### Sensitive Data Protection
- Automatic masking of sensitive values in API responses
- Secure storage of passwords and API keys
- Access control for sensitive configuration viewing

### Audit Trail
- Complete change history with timestamps
- User attribution for all modifications
- IP address and user agent tracking
- Optional change reason documentation

### Access Control
- Admin-only access to configuration management
- Role-based permissions for different configuration categories
- Read-only protection for system-critical settings

## Best Practices

### Configuration Organization
1. **Use Categories**: Organize configurations by functional area
2. **Descriptive Names**: Use clear, descriptive configuration keys
3. **Default Values**: Always provide sensible default values
4. **Documentation**: Include comprehensive descriptions

### Security Guidelines
1. **Sensitive Data**: Mark sensitive configurations appropriately
2. **Validation Rules**: Implement proper validation for all inputs
3. **Regular Backups**: Create backups before major changes
4. **Change Documentation**: Document reasons for configuration changes

### Performance Considerations
1. **Caching**: Configuration values are cached for performance
2. **Restart Requirements**: Mark configurations that require restart
3. **Batch Operations**: Use batch updates for multiple changes
4. **Validation**: Validate configurations before applying

## Troubleshooting

### Common Issues

1. **Validation Errors**: Check regex patterns and value constraints
2. **Cache Issues**: Clear configuration cache if changes don't appear
3. **Permission Denied**: Verify admin access and role permissions
4. **Import Failures**: Validate JSON format and configuration structure

### Debugging Commands

```python
# Get configuration value
config = await config_service.get_config_by_key("system_name")

# Clear configuration cache
await config_service._clear_config_cache()

# Validate configuration
result = await config_service.validate_configs(validation_request)
```

## Integration Examples

### Reading Configuration in Code
```python
from app.services.config import ConfigService

# Get configuration value
async def get_system_setting():
    config_service = ConfigService(db)
    config = await config_service.get_config_by_key("max_upload_size")
    return int(config.value) if config else 100
```

### Environment Variable Sync
```python
# Sync environment variables to OS
async def sync_environment():
    config_service = ConfigService(db)
    result = await config_service.sync_env_vars_to_os()
    print(f"Synced {result['synced']} variables")
```

### Template Application
```python
# Apply configuration template
async def deploy_production_config():
    config_service = ConfigService(db)
    result = await config_service.apply_template(
        template_id=1, 
        overwrite_existing=True
    )
    print(f"Applied {result['created'] + result['updated']} configurations")
```
