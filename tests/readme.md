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
