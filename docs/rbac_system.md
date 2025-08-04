# Advanced User & Role Management (RBAC)

## Overview

The Role-Based Access Control (RBAC) system provides comprehensive user and permission management capabilities. It implements a flexible, hierarchical permission system that allows fine-grained control over user access to system resources and operations.

## Core Concepts

### 1. Permissions
Permissions define specific actions that can be performed on system resources. Each permission consists of:
- **Resource**: The type of resource (user, role, knowledge_base, document, etc.)
- **Action**: The operation to be performed (read, create, update, delete, etc.)
- **Code**: Unique identifier in format `resource:action` (e.g., `user:read`, `kb:create`)

### 2. Roles
Roles are collections of permissions that define what a user can do in the system. Features:
- **Hierarchical**: Roles can have different priority levels
- **Flexible**: Custom roles can be created with specific permission combinations
- **System Roles**: Pre-defined roles that cannot be modified
- **User Assignment**: Users can have multiple roles

### 3. User Groups
User groups provide organizational structure for managing users collectively:
- **Hierarchical**: Groups can have parent-child relationships
- **Role Inheritance**: Groups can be assigned roles that apply to all members
- **Bulk Management**: Perform operations on all group members simultaneously

### 4. Users
Enhanced user management with RBAC integration:
- **Multiple Roles**: Users can be assigned multiple roles
- **Group Membership**: Users can belong to multiple groups
- **Permission Aggregation**: Final permissions are aggregated from direct roles and group roles

## Default System Setup

### Pre-defined Permissions (35 total)

#### User Management
- `user:read` - View user information
- `user:create` - Create new users
- `user:update` - Update user information
- `user:delete` - Delete users
- `user:manage_roles` - Manage user role assignments

#### Role Management
- `role:read` - View role information
- `role:create` - Create new roles
- `role:update` - Update role information
- `role:delete` - Delete roles

#### Permission Management
- `permission:read` - View permission information
- `permission:create` - Create new permissions
- `permission:update` - Update permission information
- `permission:delete` - Delete permissions

#### User Group Management
- `group:read` - View user group information
- `group:create` - Create new user groups
- `group:update` - Update user group information
- `group:delete` - Delete user groups

#### Knowledge Base Management
- `kb:read` - View knowledge base information
- `kb:create` - Create new knowledge bases
- `kb:update` - Update knowledge base information
- `kb:delete` - Delete knowledge bases
- `kb:train` - Train knowledge bases

#### Document Management
- `document:read` - View document information
- `document:create` - Upload new documents
- `document:update` - Update document information
- `document:delete` - Delete documents

#### Analytics & Reporting
- `analytics:read` - View analysis reports
- `analytics:export` - Export analysis data

#### Health Monitoring
- `health:read` - View system health status
- `health:manage` - Manage health check configurations
- `health:alert` - Handle system alerts

#### System Configuration
- `config:read` - View system configuration
- `config:update` - Update system configuration

#### Chat Management
- `chat:read` - View chat records
- `chat:manage` - Manage chat sessions

### Pre-defined Roles

#### 1. Super Administrator (`super_admin`)
- **Priority**: 100
- **Permissions**: All 35 permissions
- **Description**: Complete system access for system owners

#### 2. System Administrator (`system_admin`)
- **Priority**: 90
- **Permissions**: 20 permissions including user management, analytics, health monitoring, and system configuration
- **Description**: System administration and user management

#### 3. Knowledge Base Administrator (`kb_admin`)
- **Priority**: 80
- **Permissions**: 12 permissions for knowledge base and document management
- **Description**: Knowledge base and content management

#### 4. Analyst (`analyst`)
- **Priority**: 70
- **Permissions**: 7 permissions for viewing analytics and basic read access
- **Description**: Data analysis and reporting

#### 5. Regular User (`user`)
- **Priority**: 10
- **Permissions**: 3 basic permissions for knowledge base and document viewing
- **Description**: Basic system usage

### Pre-defined User Groups

1. **Admin Group** (`admin_group`) - For system administrators
2. **KB Manager Group** (`kb_manager_group`) - For knowledge base managers
3. **User Group** (`user_group`) - For regular users

## API Endpoints

### Permission Management

#### Create Permission
```http
POST /api/v1/admin/rbac/permissions
```

**Request Body:**
```json
{
  "name": "查看报告",
  "code": "report:read",
  "description": "查看系统报告",
  "resource": "report",
  "action": "read",
  "is_system": false,
  "is_active": true
}
```

#### Get Permissions
```http
GET /api/v1/admin/rbac/permissions?skip=0&limit=100&is_active=true&resource=user
```

#### Update Permission
```http
PUT /api/v1/admin/rbac/permissions/{permission_id}
```

### Role Management

#### Create Role
```http
POST /api/v1/admin/rbac/roles
```

**Request Body:**
```json
{
  "name": "内容编辑",
  "code": "content_editor",
  "description": "内容编辑角色",
  "priority": 50,
  "permission_ids": [18, 19, 20, 23, 24, 25],
  "is_system": false,
  "is_active": true
}
```

#### Get Roles
```http
GET /api/v1/admin/rbac/roles?skip=0&limit=100&is_active=true
```

#### Update Role
```http
PUT /api/v1/admin/rbac/roles/{role_id}
```

### User Group Management

#### Create User Group
```http
POST /api/v1/admin/rbac/groups
```

**Request Body:**
```json
{
  "name": "编辑部",
  "code": "editorial_dept",
  "description": "编辑部门用户组",
  "parent_id": null,
  "role_ids": [3],
  "member_ids": [10, 11, 12],
  "is_active": true
}
```

#### Get User Groups
```http
GET /api/v1/admin/rbac/groups?skip=0&limit=100&is_active=true&parent_id=1
```

### User Role Assignment

#### Assign User Roles
```http
POST /api/v1/admin/rbac/users/assign-roles
```

**Request Body:**
```json
{
  "user_id": 5,
  "role_ids": [2, 3]
}
```

#### Get User Permissions
```http
GET /api/v1/admin/rbac/users/{user_id}/permissions
```

**Response:**
```json
{
  "success": true,
  "data": [
    "user:read",
    "user:create",
    "kb:read",
    "kb:create",
    "document:read"
  ]
}
```

#### Check User Permission
```http
GET /api/v1/admin/rbac/users/{user_id}/check-permission/{permission_code}
```

### Bulk Operations

#### Bulk User Operations
```http
POST /api/v1/admin/rbac/users/bulk-operation
```

**Request Body:**
```json
{
  "user_ids": [1, 2, 3, 4, 5],
  "operation": "assign_role",
  "data": {
    "role_ids": [2]
  }
}
```

**Supported Operations:**
- `activate` - Activate users
- `deactivate` - Deactivate users
- `delete` - Delete users
- `assign_role` - Assign roles to users
- `remove_role` - Remove roles from users
- `add_to_group` - Add users to groups
- `remove_from_group` - Remove users from groups

#### Import Users
```http
POST /api/v1/admin/rbac/users/import
```

**Request Body:**
```json
{
  "users": [
    {
      "email": "editor1@example.com",
      "password": "temp123",
      "is_admin": false,
      "role_codes": ["kb_admin"],
      "group_codes": ["kb_manager_group"]
    },
    {
      "email": "user1@example.com",
      "is_admin": false,
      "role_codes": ["user"],
      "group_codes": ["user_group"]
    }
  ],
  "send_welcome_email": false,
  "force_password_reset": true
}
```

#### Export Users
```http
GET /api/v1/admin/rbac/users/export
```

Returns CSV file with user data including roles and groups.

## Permission System Architecture

### Permission Aggregation
User permissions are calculated by combining:
1. **Direct Role Permissions**: Permissions from roles directly assigned to the user
2. **Group Role Permissions**: Permissions from roles assigned to user's groups
3. **Inheritance**: Child groups inherit permissions from parent groups

### Permission Caching
- User permissions are cached in Redis for 1 hour
- Cache is automatically cleared when user roles or group memberships change
- Cache key format: `user_permissions:{user_id}`

### Permission Checking
```python
# Check if user has specific permission
has_permission = await rbac_service.check_user_permission(user_id, "kb:create")

# Get all user permissions
permissions = await rbac_service.get_user_permissions(user_id)
```

## Security Features

### System Protection
- **System Roles**: Cannot be modified or deleted
- **System Permissions**: Cannot be modified or deleted
- **Admin Protection**: Super admin role cannot be removed from users

### Audit Trail
- All role assignments are logged with timestamps and assignor information
- User group memberships track join dates and who added them
- Permission changes are tracked through role modifications

### Access Control
- All RBAC endpoints require admin authentication
- Permission checks are performed at the API level
- Middleware integration for automatic permission validation

## Usage Examples

### Creating a Custom Role
```python
# Create a content manager role
role_data = RoleCreate(
    name="内容管理员",
    code="content_manager",
    description="负责内容审核和管理",
    priority=60,
    permission_ids=[18, 19, 20, 21, 23, 24, 25, 26],  # KB and document permissions
    is_system=False,
    is_active=True
)

role = await rbac_service.create_role(role_data, created_by=admin_user_id)
```

### Organizing Users with Groups
```python
# Create department group
group_data = UserGroupCreate(
    name="产品部",
    code="product_dept",
    description="产品部门",
    role_ids=[3],  # KB admin role
    member_ids=[10, 11, 12, 13],
    is_active=True
)

group = await rbac_service.create_user_group(group_data, created_by=admin_user_id)
```

### Bulk User Management
```python
# Assign role to multiple users
operation = BulkUserOperation(
    user_ids=[1, 2, 3, 4, 5],
    operation="assign_role",
    data={"role_ids": [2]}
)

result = await rbac_service.bulk_user_operation(operation)
print(f"Success: {result['success']}, Failed: {result['failed']}")
```

## Best Practices

### Role Design
1. **Principle of Least Privilege**: Grant minimum permissions necessary
2. **Role Hierarchy**: Use priority levels to establish clear role hierarchy
3. **Functional Roles**: Create roles based on job functions, not individuals
4. **Regular Review**: Periodically review and update role permissions

### Group Management
1. **Organizational Structure**: Mirror your organization's structure
2. **Inheritance**: Use parent-child relationships for permission inheritance
3. **Temporary Access**: Use groups for temporary project access

### Permission Management
1. **Granular Permissions**: Create specific permissions for fine-grained control
2. **Resource-Action Pattern**: Follow consistent naming convention
3. **Documentation**: Document custom permissions clearly

### Security
1. **Regular Audits**: Review user permissions and role assignments regularly
2. **Separation of Duties**: Ensure critical operations require multiple roles
3. **Access Reviews**: Conduct periodic access reviews for compliance

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check user roles and group memberships
2. **Cache Issues**: Clear user permission cache if permissions seem outdated
3. **Role Assignment Failures**: Verify role exists and is active
4. **Import Failures**: Check email uniqueness and role/group codes

### Debugging Commands

```python
# Check user's effective permissions
permissions = await rbac_service.get_user_permissions(user_id)

# Clear permission cache
await rbac_service._clear_user_permissions_cache(user_id)

# Verify role permissions
role = await rbac_service.get_role_by_id(role_id)
print([p.code for p in role.permissions])
```
