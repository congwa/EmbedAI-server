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

# 重置测试状态（三种方式）
# 方式1：删除状态文件
rm -f tests/states/knowledge_base_flow.json

# 方式2：使用 Python API
python -c "from tests.utils.test_state import TestState; TestState('knowledge_base_flow').reset()"

# 方式3：使用命令行参数
pytest tests/test_knowledge_base_flow.py -v --reset-state

# 运行单个测试用例
pytest tests/test_knowledge_base_flow.py::test_create_admin -v
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

3. **常见问题解决**：
   - 401错误：检查token是否正确、是否过期
   - 403错误：检查用户权限
   - 404错误：检查API路径是否正确

## 测试流程说明

### 1. 基础测试流程

测试用例按以下顺序执行：

1. 管理员相关：
   - 创建管理员账户
   - 管理员登录认证
   - 获取管理员信息

2. 用户管理：
   - 创建普通用户
   - 普通用户登录
   - 用户信息验证

3. 知识库操作：
   - 创建知识库
   - 配置知识库权限
   - 添加用户到知识库
   - 上传和管理文档
   - 知识库训练
   - 知识库查询测试

### 2. 状态管理机制

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

