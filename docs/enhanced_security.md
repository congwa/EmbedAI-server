# Enhanced Security Features

## Overview

The Enhanced Security Features module provides comprehensive security capabilities including Two-Factor Authentication (2FA), advanced session management, IP access control, security event monitoring, and audit logging. This enterprise-grade security system ensures robust protection against various security threats and compliance with security best practices.

## Core Security Features

### 1. Two-Factor Authentication (2FA)
- **TOTP Support**: Time-based One-Time Password using authenticator apps
- **SMS/Email Verification**: Alternative verification methods
- **Backup Codes**: Emergency access codes for account recovery
- **QR Code Generation**: Easy setup with authenticator apps
- **Device Trust**: Remember trusted devices for convenience

### 2. Enhanced Session Management
- **Session Tracking**: Comprehensive session monitoring and control
- **Device Fingerprinting**: Unique device identification
- **Concurrent Session Limits**: Control multiple active sessions
- **Session Termination**: Remote session management
- **Suspicious Activity Detection**: Automatic anomaly detection

### 3. IP Access Control
- **IP Whitelist/Blacklist**: Granular IP-based access control
- **Automatic Blocking**: Dynamic IP blocking based on behavior
- **Geographic Restrictions**: Country-based access control
- **Rate Limiting**: Per-IP request rate limiting
- **CIDR Range Support**: Network range management

### 4. Security Event Monitoring
- **Real-time Monitoring**: Live security event tracking
- **Event Classification**: Categorized security events with severity levels
- **Risk Scoring**: Automated risk assessment for events
- **Alert System**: Configurable security alerts
- **Event Resolution**: Security incident management

### 5. Password Security
- **Password History**: Prevent password reuse
- **Complexity Requirements**: Configurable password policies
- **Secure Storage**: Bcrypt hashing with salt
- **Password Expiration**: Configurable password aging
- **Breach Detection**: Integration with known breach databases

### 6. Device Management
- **Device Fingerprinting**: Browser and device identification
- **Trusted Devices**: Device trust management
- **Device History**: Track user devices over time
- **Suspicious Device Detection**: Identify unusual devices

### 7. Security Policies
- **Policy Engine**: Flexible security policy framework
- **Rule-based Configuration**: JSON-based policy rules
- **Priority System**: Policy precedence management
- **Dynamic Updates**: Runtime policy modifications

### 8. Audit & Compliance
- **Comprehensive Logging**: All security events logged
- **Audit Trails**: Complete user action history
- **Compliance Reports**: Automated compliance reporting
- **Data Retention**: Configurable log retention policies

## Security Policies

### Default Security Policies (8 policies)

#### 1. Password Complexity Policy
```json
{
  "min_length": 8,
  "max_length": 128,
  "require_uppercase": true,
  "require_lowercase": true,
  "require_numbers": true,
  "require_symbols": false,
  "forbidden_patterns": ["123456", "password", "admin"],
  "history_check": 5
}
```

#### 2. Login Security Policy
```json
{
  "max_failed_attempts": 5,
  "lockout_duration": 1800,
  "session_timeout": 3600,
  "require_2fa_for_admin": true,
  "allow_concurrent_sessions": 3,
  "ip_whitelist_enabled": false,
  "suspicious_activity_threshold": 10
}
```

#### 3. IP Access Control Policy
```json
{
  "whitelist_mode": false,
  "auto_block_enabled": true,
  "auto_block_threshold": 10,
  "auto_block_duration": 3600,
  "trusted_ip_ranges": [],
  "blocked_countries": [],
  "rate_limit_per_ip": 100
}
```

#### 4. Session Management Policy
```json
{
  "max_session_duration": 86400,
  "idle_timeout": 3600,
  "require_reauth_for_sensitive": true,
  "device_fingerprinting": true,
  "trusted_device_duration": 2592000,
  "force_logout_on_password_change": true
}
```

#### 5. Two-Factor Authentication Policy
```json
{
  "mandatory_for_admin": true,
  "mandatory_for_sensitive_operations": false,
  "allowed_methods": ["totp", "sms", "email"],
  "backup_codes_count": 10,
  "grace_period": 7,
  "remember_device_duration": 2592000
}
```

#### 6. Data Protection Policy
```json
{
  "encrypt_sensitive_data": true,
  "mask_sensitive_logs": true,
  "data_retention_days": 365,
  "audit_log_retention_days": 2555,
  "backup_encryption": true,
  "secure_delete": true
}
```

#### 7. API Security Policy
```json
{
  "rate_limit_per_user": 1000,
  "rate_limit_per_ip": 100,
  "require_https": true,
  "api_key_rotation_days": 90,
  "request_size_limit": 10485760,
  "response_headers_security": true
}
```

#### 8. Audit Policy
```json
{
  "log_all_admin_actions": true,
  "log_failed_authentications": true,
  "log_privilege_escalations": true,
  "log_data_access": true,
  "log_configuration_changes": true,
  "real_time_alerting": true,
  "alert_thresholds": {
    "failed_logins": 5,
    "privilege_escalations": 1,
    "suspicious_activities": 3
  }
}
```

## API Endpoints

### Security Dashboard

#### Get Security Dashboard
```http
GET /api/v1/admin/security/dashboard
```

**Response:**
```json
{
  "success": true,
  "data": {
    "active_sessions": 15,
    "failed_logins_24h": 3,
    "blocked_ips": 2,
    "security_events_24h": 25,
    "two_factor_enabled_users": 8,
    "suspicious_activities": 1,
    "recent_events": [...],
    "top_risk_ips": [...]
  }
}
```

### Two-Factor Authentication

#### Setup 2FA
```http
POST /api/v1/admin/security/2fa/setup
```

**Request Body:**
```json
{
  "method": "totp",
  "phone_number": "+1234567890",
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "secret_key": "JBSWY3DPEHPK3PXP",
    "qr_code_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "backup_codes": ["A1B2C3D4", "E5F6G7H8", ...],
    "method": "totp"
  }
}
```

#### Verify 2FA
```http
POST /api/v1/admin/security/2fa/verify
```

**Request Body:**
```json
{
  "code": "123456",
  "backup_code": "A1B2C3D4"
}
```

#### Get 2FA Status
```http
GET /api/v1/admin/security/2fa/status
```

#### Disable 2FA
```http
DELETE /api/v1/admin/security/2fa
```

### Session Management

#### Get User Sessions
```http
GET /api/v1/admin/security/sessions
```

**Response:**
```json
{
  "success": true,
  "data": {
    "current_session_id": 123,
    "sessions": [
      {
        "id": 123,
        "session_token": "abc123...",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "device_fingerprint": "fp_abc123",
        "location": {"country": "US", "city": "New York"},
        "status": "active",
        "is_mobile": false,
        "is_trusted": true,
        "last_activity": "2024-08-04T12:00:00Z",
        "expires_at": "2024-08-05T12:00:00Z",
        "created_at": "2024-08-04T08:00:00Z"
      }
    ],
    "total_count": 3
  }
}
```

#### Terminate Sessions
```http
POST /api/v1/admin/security/sessions/terminate
```

**Request Body:**
```json
{
  "session_ids": [124, 125],
  "terminate_all": false
}
```

### IP Access Control

#### Add IP to Whitelist
```http
POST /api/v1/admin/security/ip/whitelist
```

**Request Body:**
```json
{
  "ip_address": "192.168.1.100",
  "ip_range": "192.168.1.0/24",
  "description": "Office network",
  "user_id": 123,
  "expires_at": "2024-12-31T23:59:59Z"
}
```

#### Add IP to Blacklist
```http
POST /api/v1/admin/security/ip/blacklist
```

**Request Body:**
```json
{
  "ip_address": "10.0.0.100",
  "reason": "Suspicious activity detected",
  "block_type": "automatic",
  "expires_at": "2024-08-05T12:00:00Z"
}
```

#### Check IP Access
```http
POST /api/v1/admin/security/ip/check?ip_address=192.168.1.100
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ip_address": "192.168.1.100",
    "is_allowed": true,
    "reason": null
  }
}
```

#### Bulk IP Operations
```http
POST /api/v1/admin/security/ip/bulk-operation
```

**Request Body:**
```json
{
  "ip_addresses": ["10.0.0.1", "10.0.0.2", "10.0.0.3"],
  "operation": "blacklist",
  "reason": "Coordinated attack detected",
  "expires_at": "2024-08-05T12:00:00Z"
}
```

### Security Audit

#### Generate Security Audit Report
```http
POST /api/v1/admin/security/audit
```

**Request Body:**
```json
{
  "start_date": "2024-08-01T00:00:00Z",
  "end_date": "2024-08-04T23:59:59Z",
  "event_types": ["login_failed", "suspicious_activity"],
  "user_ids": [1, 2, 3],
  "ip_addresses": ["192.168.1.100"],
  "severity_levels": ["warning", "error"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_events": 150,
    "events_by_type": {
      "login_failed": 45,
      "login_success": 80,
      "suspicious_activity": 25
    },
    "events_by_severity": {
      "info": 80,
      "warning": 45,
      "error": 25
    },
    "top_users": [...],
    "top_ips": [...],
    "timeline_data": [...],
    "risk_analysis": {
      "high_risk_events": 10,
      "risk_percentage": 6.67,
      "most_common_event": "login_success"
    }
  }
}
```

#### Get Security Events
```http
GET /api/v1/admin/security/events?event_type=login_failed&severity=warning&is_resolved=false
```

### Password Security

#### Change Password
```http
POST /api/v1/admin/security/password/change
```

**Request Body:**
```json
{
  "current_password": "current_password",
  "new_password": "new_secure_password",
  "confirm_password": "new_secure_password"
}
```

## Security Event Types

### Authentication Events
- `LOGIN_SUCCESS` - Successful user login
- `LOGIN_FAILED` - Failed login attempt
- `LOGOUT` - User logout
- `TWO_FACTOR_ENABLED` - 2FA enabled for user
- `TWO_FACTOR_DISABLED` - 2FA disabled for user

### Account Security Events
- `PASSWORD_CHANGED` - Password changed
- `ACCOUNT_LOCKED` - Account locked due to failed attempts
- `ACCOUNT_UNLOCKED` - Account unlocked
- `SUSPICIOUS_ACTIVITY` - Suspicious behavior detected

### Access Control Events
- `IP_BLOCKED` - IP address blocked
- `PERMISSION_DENIED` - Access denied to resource

## Security Best Practices

### Implementation Guidelines

1. **Enable 2FA for All Admin Users**
   - Mandatory 2FA for administrative accounts
   - Regular backup code rotation
   - Device trust management

2. **Implement Strong Password Policies**
   - Minimum 8 characters with complexity requirements
   - Password history checking (last 5 passwords)
   - Regular password expiration

3. **Monitor Security Events**
   - Real-time security event monitoring
   - Automated alerting for high-risk events
   - Regular security audit reviews

4. **IP Access Control**
   - Implement IP whitelisting for sensitive operations
   - Automatic blocking of suspicious IPs
   - Geographic access restrictions

5. **Session Security**
   - Short session timeouts for sensitive operations
   - Device fingerprinting for anomaly detection
   - Concurrent session limits

### Compliance Considerations

1. **Data Protection**
   - Encrypt sensitive data at rest and in transit
   - Implement secure data deletion
   - Regular security assessments

2. **Audit Requirements**
   - Comprehensive audit logging
   - Long-term log retention (7 years for audit logs)
   - Tamper-evident logging

3. **Access Controls**
   - Principle of least privilege
   - Regular access reviews
   - Segregation of duties

## Integration Examples

### Custom Security Event Logging
```python
from app.services.security import SecurityService
from app.schemas.security import SecurityEventType

async def log_custom_security_event():
    security_service = SecurityService(db)
    await security_service.log_security_event(
        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        severity="warning",
        user_id=user_id,
        ip_address=request.client.host,
        details={"action": "unusual_data_access", "resource": "sensitive_data"}
    )
```

### IP Access Validation
```python
async def validate_ip_access(ip_address: str):
    security_service = SecurityService(db)
    is_allowed, reason = await security_service.check_ip_access(ip_address)
    if not is_allowed:
        raise HTTPException(status_code=403, detail=reason)
```

### Session Management
```python
async def create_secure_session(user_id: int, request: Request):
    security_service = SecurityService(db)
    session = await security_service.create_session(
        user_id=user_id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        device_fingerprint=generate_device_fingerprint(request)
    )
    return session
```

## Troubleshooting

### Common Issues

1. **2FA Setup Issues**
   - Verify time synchronization between server and client
   - Check QR code generation and scanning
   - Validate backup codes

2. **Session Problems**
   - Clear expired sessions regularly
   - Check Redis connectivity for session storage
   - Verify session token generation

3. **IP Blocking Issues**
   - Review IP whitelist/blacklist configurations
   - Check automatic blocking thresholds
   - Validate IP address formats

4. **Security Event Logging**
   - Verify database connectivity
   - Check event serialization
   - Monitor log storage capacity

### Debugging Commands

```python
# Check user 2FA status
status = await security_service.get_two_factor_status(user_id)

# Validate IP access
is_allowed, reason = await security_service.check_ip_access("192.168.1.100")

# Get user sessions
sessions = await security_service.get_user_sessions(user_id)

# Generate security audit
audit = await security_service.generate_security_audit(audit_request)
```
