# Integration & API Management

## Overview

The Integration & API Management module provides comprehensive tools for managing API access, webhook integrations, third-party service connections, and API documentation. It offers enterprise-grade features including API key management, webhook event delivery, integration templates, and detailed usage analytics.

## Core Features

### 1. API Key Management
- **Secure Key Generation**: Cryptographically secure API key generation with prefixes
- **Scope-based Permissions**: Granular permission control (read, write, admin, webhook)
- **Rate Limiting**: Configurable rate limits per API key
- **Usage Tracking**: Detailed usage statistics and monitoring
- **Expiration Management**: Automatic key expiration and renewal

### 2. Webhook Management
- **Event-driven Architecture**: Real-time event notifications via webhooks
- **Reliable Delivery**: Automatic retry mechanisms with exponential backoff
- **Signature Verification**: HMAC-SHA256 signature verification for security
- **Delivery Tracking**: Complete delivery history and status monitoring
- **Custom Headers**: Support for custom HTTP headers

### 3. Third-party Integrations
- **Integration Templates**: 8 pre-built templates for popular services
- **OAuth Support**: OAuth 2.0 flow support for secure authentication
- **Configuration Management**: Secure credential storage and management
- **Verification System**: Automatic integration health checks
- **Custom Integrations**: Support for custom integration types

### 4. API Documentation
- **Interactive Documentation**: Markdown-based API documentation
- **Version Management**: Multi-version API documentation support
- **Category Organization**: Hierarchical documentation structure
- **Search and Discovery**: Full-text search across documentation
- **Usage Analytics**: Documentation view tracking and analytics

### 5. Usage Analytics
- **Real-time Monitoring**: Live API usage monitoring and metrics
- **Performance Analytics**: Response time and error rate tracking
- **Usage Patterns**: Detailed usage pattern analysis
- **Custom Reports**: Flexible reporting and data export
- **Alerting**: Configurable usage and performance alerts

## API Key Management

### Key Generation and Security

API keys are generated using cryptographically secure methods:

```python
# Key format: eak_[32-character-base64-string]
# Example: eak_dGhpcyBpcyBhIHNhbXBsZSBrZXkgZm9yIGRlbW8
```

### Permission Scopes

#### Available Scopes
- **`read`**: Read-only access to resources
- **`write`**: Create and update resources
- **`admin`**: Full administrative access
- **`webhook`**: Webhook-specific permissions

#### Scope Combinations
```json
{
  "scopes": ["read", "write"],
  "rate_limit": 1000,
  "expires_at": "2024-12-31T23:59:59Z"
}
```

### Rate Limiting

Rate limits are enforced per API key:

- **Default Limit**: 1000 requests per hour
- **Custom Limits**: Configurable per key
- **Sliding Window**: 1-hour sliding window implementation
- **Headers**: Rate limit information in response headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1691164800
```

## Webhook System

### Supported Events

#### User Events
- `user.created` - New user registration
- `user.updated` - User profile updates
- `user.deleted` - User account deletion

#### Knowledge Base Events
- `knowledge_base.created` - New knowledge base creation
- `knowledge_base.updated` - Knowledge base modifications
- `knowledge_base.deleted` - Knowledge base deletion

#### Document Events
- `document.uploaded` - Document upload completion
- `document.processed` - Document processing completion
- `document.failed` - Document processing failure

#### Chat Events
- `chat.started` - New chat session initiation
- `chat.ended` - Chat session termination

#### System Events
- `system.alert` - System alerts and notifications

### Event Payload Structure

```json
{
  "event_type": "knowledge_base.created",
  "timestamp": "2024-08-04T12:00:00Z",
  "data": {
    "id": 123,
    "name": "New Knowledge Base",
    "owner_id": 1,
    "created_at": "2024-08-04T12:00:00Z"
  },
  "metadata": {
    "source": "api",
    "version": "v1",
    "request_id": "req_abc123"
  }
}
```

### Webhook Security

#### Signature Verification
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature"""
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

#### Headers
```http
Content-Type: application/json
User-Agent: EmbedAI-Webhook/1.0
X-EmbedAI-Signature: sha256=abc123...
X-EmbedAI-Event: knowledge_base.created
X-EmbedAI-Delivery: uuid-delivery-id
```

### Delivery Guarantees

- **At-least-once delivery**: Events are delivered at least once
- **Retry Logic**: Exponential backoff with jitter
- **Timeout Handling**: Configurable timeout (default: 30 seconds)
- **Failure Tracking**: Detailed failure logs and metrics

## Integration Templates

### Pre-built Templates (8 templates)

#### 1. Slack Integration
```json
{
  "name": "Slack集成",
  "provider": "Slack",
  "type": "webhook",
  "config": {
    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "channel": "#general",
    "username": "EmbedAI Bot",
    "icon_emoji": ":robot_face:"
  },
  "required_fields": ["webhook_url"],
  "rating": 4.8
}
```

#### 2. Discord Integration
```json
{
  "name": "Discord集成",
  "provider": "Discord",
  "type": "webhook",
  "config": {
    "webhook_url": "https://discord.com/api/webhooks/YOUR/WEBHOOK/URL",
    "username": "EmbedAI",
    "avatar_url": ""
  },
  "rating": 4.6
}
```

#### 3. Microsoft Teams Integration
```json
{
  "name": "Microsoft Teams集成",
  "provider": "Microsoft",
  "type": "webhook",
  "config": {
    "webhook_url": "https://outlook.office.com/webhook/YOUR/TEAMS/WEBHOOK",
    "card_type": "MessageCard",
    "theme_color": "0076D7"
  },
  "rating": 4.4
}
```

#### 4. GitHub Integration
```json
{
  "name": "GitHub集成",
  "provider": "GitHub",
  "type": "api_client",
  "config": {
    "api_url": "https://api.github.com",
    "repository": "owner/repo",
    "auth_type": "token"
  },
  "required_fields": ["repository", "access_token"],
  "rating": 4.9
}
```

#### 5. Jira Integration
```json
{
  "name": "Jira集成",
  "provider": "Atlassian",
  "type": "api_client",
  "config": {
    "api_url": "https://your-domain.atlassian.net/rest/api/3",
    "project_key": "PROJ",
    "issue_type": "Task"
  },
  "rating": 4.3
}
```

#### 6. Google Sheets Integration
```json
{
  "name": "Google Sheets集成",
  "provider": "Google",
  "type": "oauth",
  "config": {
    "api_url": "https://sheets.googleapis.com/v4/spreadsheets",
    "scope": "https://www.googleapis.com/auth/spreadsheets"
  },
  "rating": 4.5
}
```

#### 7. Salesforce Integration
```json
{
  "name": "Salesforce集成",
  "provider": "Salesforce",
  "type": "oauth",
  "config": {
    "api_url": "https://your-instance.salesforce.com/services/data/v58.0",
    "auth_url": "https://login.salesforce.com/services/oauth2/authorize"
  },
  "rating": 4.2
}
```

#### 8. Zapier Integration
```json
{
  "name": "Zapier集成",
  "provider": "Zapier",
  "type": "webhook",
  "config": {
    "webhook_url": "https://hooks.zapier.com/hooks/catch/YOUR/ZAPIER/HOOK",
    "trigger_event": "knowledge_base_created"
  },
  "rating": 4.7
}
```

## API Documentation System

### Documentation Structure

#### Categories
- **概述** - API overview and getting started
- **认证** - Authentication and authorization
- **API参考** - Detailed API reference
- **Webhook** - Webhook events and integration

#### Default Documentation (5 documents)

1. **API概述** - Complete API overview with quick start guide
2. **认证和授权** - Authentication methods and security best practices
3. **知识库管理** - Knowledge base CRUD operations
4. **文档管理** - Document upload and management
5. **Webhook事件** - Webhook events and payload formats

### Documentation Features

- **Markdown Support**: Rich markdown formatting
- **Code Highlighting**: Syntax highlighting for code blocks
- **Interactive Examples**: Live API examples
- **Version Control**: Multi-version documentation support
- **Search Integration**: Full-text search capabilities

## API Endpoints

### Integration Dashboard

#### Get Integration Dashboard
```http
GET /api/v1/admin/integration/dashboard
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_integrations": 15,
    "active_integrations": 12,
    "total_webhooks": 8,
    "active_webhooks": 6,
    "total_api_keys": 25,
    "active_api_keys": 20,
    "api_requests_24h": 15420,
    "webhook_deliveries_24h": 342,
    "webhook_success_rate": 98.5,
    "integration_by_type": {
      "webhook": 8,
      "api_client": 4,
      "oauth": 3
    }
  }
}
```

### API Key Management

#### Create API Key
```http
POST /api/v1/admin/integration/api-keys
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "name": "Production API Key",
  "description": "API key for production environment",
  "scopes": ["read", "write"],
  "rate_limit": 5000,
  "expires_at": "2024-12-31T23:59:59Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "Production API Key",
    "api_key": "eak_dGhpcyBpcyBhIHNhbXBsZSBrZXkgZm9yIGRlbW8",
    "key_prefix": "eak_dGhp",
    "scopes": ["read", "write"],
    "expires_at": "2024-12-31T23:59:59Z"
  }
}
```

#### Get API Keys
```http
GET /api/v1/admin/integration/api-keys?is_active=true&limit=50
Authorization: Bearer YOUR_API_KEY
```

#### Revoke API Key
```http
DELETE /api/v1/admin/integration/api-keys/{key_id}
Authorization: Bearer YOUR_API_KEY
```

### Webhook Management

#### Create Webhook
```http
POST /api/v1/admin/integration/webhooks
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "name": "Production Webhook",
  "description": "Webhook for production notifications",
  "url": "https://your-app.com/webhook",
  "events": ["knowledge_base.created", "document.processed"],
  "secret": "your-webhook-secret",
  "headers": {
    "X-Custom-Header": "custom-value"
  },
  "timeout": 30,
  "retry_count": 3
}
```

#### Update Webhook
```http
PUT /api/v1/admin/integration/webhooks/{webhook_id}
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "name": "Updated Webhook Name",
  "is_active": false
}
```

#### Test Webhook
```http
POST /api/v1/admin/integration/webhooks/{webhook_id}/test
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "event_type": "knowledge_base.created",
  "test_payload": {
    "test": true,
    "message": "This is a test webhook delivery"
  }
}
```

### Integration Management

#### Create Integration
```http
POST /api/v1/admin/integration/integrations
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "name": "Slack Notifications",
  "description": "Send notifications to Slack",
  "integration_type": "webhook",
  "provider": "Slack",
  "config": {
    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "channel": "#notifications"
  },
  "credentials": {
    "api_token": "encrypted_token_value"
  }
}
```

#### Get Integration Templates
```http
GET /api/v1/admin/integration/integration-templates?provider=Slack
Authorization: Bearer YOUR_API_KEY
```

### API Documentation

#### Create Documentation
```http
POST /api/v1/admin/integration/documentation
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "title": "Custom API Guide",
  "content": "# Custom API Guide\n\nThis is a custom API guide...",
  "content_type": "markdown",
  "category": "Guides",
  "tags": ["custom", "guide"],
  "version": "v1",
  "is_published": true
}
```

#### Get Documentation
```http
GET /api/v1/admin/integration/documentation?category=Guides&is_published=true
Authorization: Bearer YOUR_API_KEY
```

### Usage Analytics

#### Get API Usage Statistics
```http
GET /api/v1/admin/integration/api-keys/usage-stats?start_date=2024-08-01&end_date=2024-08-04
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_requests": 45230,
    "successful_requests": 44156,
    "failed_requests": 1074,
    "average_response_time": 245.6,
    "requests_by_endpoint": {
      "/v1/knowledge-bases": 15420,
      "/v1/documents": 12340,
      "/v1/chat": 8970
    },
    "requests_by_status": {
      "200": 35420,
      "201": 8736,
      "400": 542,
      "401": 312,
      "500": 220
    },
    "requests_by_hour": [
      {"hour": "2024-08-04T00:00:00Z", "count": 1250},
      {"hour": "2024-08-04T01:00:00Z", "count": 980}
    ],
    "top_api_keys": [
      {"name": "Production Key", "usage_count": 25420},
      {"name": "Development Key", "usage_count": 12340}
    ]
  }
}
```

## Database Schema

### Integration Management Tables (8 tables)

1. **api_keys** - API key management and authentication
2. **webhooks** - Webhook configuration and management
3. **webhook_deliveries** - Webhook delivery history and tracking
4. **integrations** - Third-party integration configurations
5. **api_endpoints** - API endpoint definitions and metadata
6. **api_usage_logs** - API usage tracking and analytics
7. **integration_templates** - Pre-built integration templates
8. **api_documentation** - API documentation content management

## Usage Examples

### API Key Management
```python
from app.services.integration import IntegrationService

# Create API key
key_data = APIKeyCreate(
    name="Production API Key",
    scopes=[APIKeyScope.READ, APIKeyScope.WRITE],
    rate_limit=5000
)
api_key = await integration_service.create_api_key(key_data, admin_id)

# Get usage statistics
stats = await integration_service.get_api_usage_stats()
```

### Webhook Management
```python
# Create webhook
webhook_data = WebhookCreate(
    name="Production Webhook",
    url="https://your-app.com/webhook",
    events=[WebhookEvent.KB_CREATED, WebhookEvent.DOC_PROCESSED],
    secret="your-webhook-secret"
)
webhook = await integration_service.create_webhook(webhook_data, admin_id)

# Trigger webhook event
await integration_service.trigger_webhook(
    WebhookEvent.KB_CREATED,
    {"id": 123, "name": "New KB"},
    {"source": "api"}
)
```

### Integration Management
```python
# Create integration
integration_data = IntegrationCreate(
    name="Slack Integration",
    integration_type=IntegrationType.WEBHOOK,
    provider="Slack",
    config={"webhook_url": "https://hooks.slack.com/..."}
)
integration = await integration_service.create_integration(integration_data, admin_id)
```

## Best Practices

### API Key Security
1. **Secure Storage**: Store API keys securely using encryption
2. **Regular Rotation**: Implement regular key rotation policies
3. **Principle of Least Privilege**: Grant minimal required permissions
4. **Monitoring**: Monitor API key usage for anomalies
5. **Expiration**: Set appropriate expiration dates

### Webhook Reliability
1. **Idempotency**: Design webhook handlers to be idempotent
2. **Signature Verification**: Always verify webhook signatures
3. **Error Handling**: Implement proper error handling and logging
4. **Timeout Management**: Set appropriate timeout values
5. **Retry Logic**: Implement exponential backoff for retries

### Integration Management
1. **Configuration Validation**: Validate integration configurations
2. **Health Monitoring**: Regularly check integration health
3. **Credential Security**: Encrypt and secure integration credentials
4. **Documentation**: Maintain up-to-date integration documentation
5. **Testing**: Implement comprehensive integration testing

## Troubleshooting

### Common Issues

1. **Webhook Delivery Failures**
   - Check endpoint availability and response codes
   - Verify webhook signature validation
   - Review timeout and retry configurations

2. **API Key Authentication Errors**
   - Verify API key format and validity
   - Check permission scopes and rate limits
   - Ensure proper Authorization header format

3. **Integration Connection Issues**
   - Validate integration configuration
   - Check network connectivity and firewall rules
   - Verify third-party service credentials

### Debugging Commands

```python
# Check webhook delivery status
deliveries = await integration_service.get_webhook_deliveries(webhook_id)

# Monitor API usage
usage_logs = await integration_service.get_api_usage_logs(api_key_id)

# Verify integration health
integration_status = await integration_service.verify_integration(integration_id)
```

## Integration Points

### With Security Module
- API key authentication and authorization
- Webhook signature verification
- Integration credential encryption

### With Analytics Module
- API usage metrics and reporting
- Webhook delivery analytics
- Integration performance monitoring

### With Content Management
- Webhook events for content changes
- API documentation integration
- Content-based integration triggers

This comprehensive integration management system provides enterprise-grade API management, webhook delivery, and third-party integration capabilities, enabling seamless connectivity with external systems and services.
