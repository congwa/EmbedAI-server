# EmbedAI 测试说明

## 测试环境准备

1. 确保已安装所需依赖：

```bash
pip install pytest pytest-asyncio
```

2. 确保配置文件正确：
   - 数据库配置
   - 环境变量配置
   - 确保 `ACCESS_TOKEN_EXPIRE_MINUTES` 设置足够长（建议测试时设置为 60）

## 运行测试

### 1. 完整测试运行

```bash
# 方式一：清理环境并运行
rm -f tests/states/knowledge_base_flow.json
pytest tests/test_knowledge_base_flow.py -v

# 方式二：使用重置参数运行
pytest tests/test_knowledge_base_flow.py -v --reset-state
```

### 2. 断点续测

```bash
# 直接运行，会从上次中断的地方继续
pytest tests/test_knowledge_base_flow.py -v
```

### 3. 测试状态管理

```bash
# 查看测试状态
python -c "import json; print(json.load(open('tests/states/knowledge_base_flow.json')))"

```

### 4. 调试说明

1. **认证问题排查**：
   - 检查 token 是否正确保存：`print(state.get_step_data("user_token"))`
   - 验证 token 格式：确保包含 "Bearer "
   - 检查 token 有效期：建议测试时设置较长的有效期

2. **API路径问题**：
   - 管理员接口：`/api/v1/admin/...`
   - 普通接口：`/api/v1/...`
   - 认证接口：`/api/v1/auth/...`
   - 客户端接口：`/api/v1/client/...`

3. **常见问题解决**：
   - 401错误：检查token是否正确、是否过期
   - 403错误：检查用户权限
   - 404错误：检查API路径是否正确

## 测试流程说明

### 1. 知识库管理测试流程

1. 用户认证流程：
   - 创建管理员账户
   - 管理员登录认证
   - 创建普通用户
   - 普通用户登录

2. 知识库操作：
   - 创建知识库
   - 配置知识库权限
   - 添加成员到知识库
   - 更新成员权限
   - 测试成员访问权限
   - 移除知识库成员

### 2. 文档管理测试流程

1. 文档基础操作：
   - 创建文档：上传文本内容
   - 更新文档：修改标题和内容
   - 获取文档：验证更新结果
   - 获取文档列表：分页查询
   - 软删除文档：保留数据但标记删除

### 3. WebSocket聊天测试流程

1. 聊天会话管理：
   - 创建聊天会话
   - 建立WebSocket连接
   - 发送心跳消息
   - 发送聊天消息
   - 接收消息广播
   - 接收AI回复

2. 管理员聊天功能：
   - 管理员WebSocket连接
   - 发送管理员消息
   - 接收消息广播

### 4. 第三方用户接口测试流程

1. 用户管理：
   - 创建第三方用户
   - 获取用户信息
   - 获取用户列表
   - 更新用户信息

2. 客户端API访问：
   - 获取知识库列表
   - 创建聊天会话
   - 验证访问权限

### 5. 状态管理机制

- **状态保存位置**：
  - 测试状态文件保存在 `tests/states/` 目录
  - 每个测试流程独立的状态文件
  - 文件格式：JSON

- **状态内容**：
  - 当前执行步骤
  - 测试数据（用户ID、知识库ID等）
  - 已完成的测试步骤

- **断点续测机制**：
  - 自动记录测试进度
  - 支持从断点处继续执行
  - 可以随时重置状态

