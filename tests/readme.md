# EmbedAI 测试说明

## 运行测试

1. 首次运行完整测试：

```bash
# 清理环境（可选）
rm -f tests/states/knowledge_base_flow.json

# 运行测试
pytest tests/test_knowledge_base_flow.py -v
```

2. 从断点继续运行：

```bash
# 直接运行，会从上次中断的地方继续
pytest tests/test_knowledge_base_flow.py -v
```

3. 重置测试状态：

```bash
# 方式1：删除状态文件
rm -f tests/states/knowledge_base_flow.json

# 方式2：使用 Python API
python -c "from tests.utils.test_state import TestState; TestState('knowledge_base_flow').reset()"
```

4. 查看测试状态：

```bash
python -c "import json; print(json.load(open('tests/states/knowledge_base_flow.json')))"
```

## 测试流程说明

1. 基础流程：
   - 创建管理员账户
   - 管理员登录
   - 创建普通用户
   - 普通用户登录
   - 创建知识库
   - 添加用户到知识库
   - 创建文档
   - 训练知识库
   - 查询知识库

2. 状态保存：
   - 测试状态保存在 `tests/states/` 目录
   - 每个测试用例的状态独立保存
   - 支持断点续测

3. 注意事项：
   - 首次运行会重置数据库
   - 确保数据库配置正确
   - 确保环境变量配置正确

```py

# 首次运行完整测试
pytest tests/test_knowledge_base_flow.py -v

# 从断点继续运行
pytest tests/test_knowledge_base_flow.py -v



# 首次运行完整测试
pytest tests/test_knowledge_base_flow.py -v

# 从断点继续运行
pytest tests/test_knowledge_base_flow.py -v


# 清理环境
rm -f tests/states/knowledge_base_flow.json

# 运行测试
pytest tests/test_knowledge_base_flow.py -v


# 直接运行，会从上次中断的地方继续
pytest tests/test_knowledge_base_flow.py -v

# 删除状态文件
rm -f tests/states/knowledge_base_flow.json

# 或者使用 Python
from tests.utils.test_state import TestState
state = TestState("knowledge_base_flow")
state.reset()


import json
with open("tests/states/knowledge_base_flow.json") as f:
    print(json.load(f))

```
