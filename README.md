# EmbedAI-server

随处可用的智能知识助手系统，基于图数据库和大语言模型，提供高性能的知识检索和智能问答服务。

## 配套项目

- [EmbedAI-sdk h5端sdk](https://github.com/congwa/EmbedAI-sdk)
- [EmbedAI-admin 后台管理端](https://github.com/congwa/EmbedAI-admin)
- [EmbedAI-server 服务端](https://github.com/congwa/EmbedAI-server)

## 功能特性

- **轻松植入**：提供多语言SDK和完整API，支持快速接入任何系统
- **智能问答**：基于大语言模型和图数据库的知识检索，提供准确的问答服务
- **知识库隔离**：为每个接入系统提供独立的知识库空间，确保数据安全和隔离
- **高效文档管理**：支持多种文档类型的管理，包括创建、更新、查询和软删除
- **权限控制**：完善的访问权限管理，支持多租户和多角色

## 技术优势

- 极简接入方案
  - 提供Python、Java、Node.js等多语言SDK
  - 完整的RESTful API支持，支持任意系统快速集成
  - 支持Docker一键部署，简化运维成本
  - 提供详细的接入文档和示例代码

- 基于图数据库的知识存储
  - 相比传统关系型数据库，图数据库能更自然地表达实体间的复杂关系
  - 支持高效的图遍历算法，显著提升多跳关系查询性能
  - 灵活的图模型设计，便于动态扩展知识结构
  - 强大的关系分析能力，支持知识推理和关联发现

- 先进的AI问答处理流程
  - 智能实体识别：区分命名实体和通用实体，通过向量编码实现精准匹配
  - 多层次评分机制：
    - 实体评分：基于向量相似度，对命名实体和通用实体采用差异化评分策略
    - 图结构评分：利用图结构信息重新评估实体重要性，考虑实体间关系强度
    - 关系评分：基于实体分数评估关系重要性，使用实体到关系的映射矩阵
    - 文本块评分：通过关系找到相关文本块，确保上下文完整性
  - 层层递进的处理确保查询理解准确性和结果相关性

- 企业级特性支持
  - 完善的多租户隔离机制
  - 细粒度的访问控制策略
  - 支持文档的软删除机制，保护数据安全
  - 基于FastAPI构建，提供高性能的异步处理能力
  - 支持知识库训练队列管理，优化系统资源使用

## 数据库关系

[![](https://mermaid.ink/img/pako:eNqNVMuumzAQ_RXL6yQKuYQEltVVN3dTqeqmimQ5eEJcwKa2aS4l-fcOIQ9eleKN7TmH8fjMMTWNtQAaUTDvkieG5ztFcPywYMj5PJ_rul1HZEdjA9yB3dEh50w-lD5lIBL4wi1cyfqkJpg1eddxmYNyUxn7WSY_0Mpx2Wbu5K7bdTMkMqUg3z6eIeuMVAmBnMtsFD1yewTBCm7tSRvxxPdaZ8AVkZZxkUs1jcRO_oFRUitSlkI1jgPe2PWhpuBWB8H2FcPav3ZqFxh3MocHhbsWvNwF6Iv2khKK59DnYbfADM--sYVG4TrX_2W1IvDJ8yID9rsEI7GDA1Q56SrmqmIEZVnOsIsHmYwOQv1TnJmQ5omBKnPiDFbQQNZxV9oJeboM09VpmnXA6dr3Lu1WxoMExmgzkQXvXE514uHUl5qACmVj5zQGxxSD-wsdX8V8wRc9sCzECOy4V0AGCPerTe9-Yns01NAT_3frhc5oDga9IvB_cpVgR90R0Gq0ebqCm7R5tg2Pl05_r1RMI2dKmFGjy-RIowPPLO7aqm__ozul4Oqn1t0tjWr6SaO5768X3nLle6HvvS3Dt3BGKxr5m-1itQ62AQLbYO1t_MuM_r1m8BZeEIThcu35_irYbvzV5R_K2pLI?type=png)](https://mermaid.live/edit#pako:eNqNVMuumzAQ_RXL6yQKuYQEltVVN3dTqeqmimQ5eEJcwKa2aS4l-fcOIQ9eleKN7TmH8fjMMTWNtQAaUTDvkieG5ztFcPywYMj5PJ_rul1HZEdjA9yB3dEh50w-lD5lIBL4wi1cyfqkJpg1eddxmYNyUxn7WSY_0Mpx2Wbu5K7bdTMkMqUg3z6eIeuMVAmBnMtsFD1yewTBCm7tSRvxxPdaZ8AVkZZxkUs1jcRO_oFRUitSlkI1jgPe2PWhpuBWB8H2FcPav3ZqFxh3MocHhbsWvNwF6Iv2khKK59DnYbfADM--sYVG4TrX_2W1IvDJ8yID9rsEI7GDA1Q56SrmqmIEZVnOsIsHmYwOQv1TnJmQ5omBKnPiDFbQQNZxV9oJeboM09VpmnXA6dr3Lu1WxoMExmgzkQXvXE514uHUl5qACmVj5zQGxxSD-wsdX8V8wRc9sCzECOy4V0AGCPerTe9-Yns01NAT_3frhc5oDga9IvB_cpVgR90R0Gq0ebqCm7R5tg2Pl05_r1RMI2dKmFGjy-RIowPPLO7aqm__ozul4Oqn1t0tjWr6SaO5768X3nLle6HvvS3Dt3BGKxr5m-1itQ62AQLbYO1t_MuM_r1m8BZeEIThcu35_irYbvzV5R_K2pLI)

## API接口文档

### 文档管理接口

#### 创建文档

- **接口**：POST /api/v1/admin/documents
- **描述**：创建新的文档（仅管理员）
- **参数**：
  - knowledge_base_id：知识库ID
  - title：文档标题
  - content：文档内容
  - doc_type：文档类型

#### 获取文档列表

- **接口**：GET /api/v1/admin/documents
- **描述**：获取文档列表（仅管理员）
- **参数**：
  - knowledge_base_id：知识库ID
  - skip：分页偏移量
  - limit：每页数量
  - title：文档标题（模糊搜索）
  - doc_type：文档类型
  - start_time：创建时间范围开始
  - end_time：创建时间范围结束

#### 更新文档

- **接口**：PUT /api/v1/admin/documents/{doc_id}
- **描述**：更新指定文档（仅管理员）
- **参数**：
  - title：文档标题
  - content：文档内容
  - doc_type：文档类型

#### 删除文档

- **接口**：DELETE /api/v1/admin/documents/{doc_id}
- **描述**：软删除指定文档（仅管理员）

### 知识库管理接口

#### 创建知识库

- **接口**：POST /api/v1/admin/knowledge-bases
- **描述**：为指定用户创建知识库（仅管理员）
- **参数**：
  - name：知识库名称
  - domain：领域描述
  - example_queries：示例查询
  - entity_types：实体类型
  - llm_config：模型配置

#### 训练知识库

- **接口**：POST /api/v1/admin/knowledge-bases/{kb_id}/train
- **描述**：启动知识库训练（仅管理员）

#### 知识库查询

- **接口**：POST /api/v1/knowledge-bases/{kb_id}/query
- **描述**：执行知识库查询
- **参数**：
  - query：查询内容
  - additional_context：附加上下文
  - max_tokens：最大token数

### 用户管理接口

#### 创建用户

- **接口**：POST /api/v1/admin/users
- **描述**：创建新用户（仅管理员）
- **参数**：
  - email：用户邮箱
  - password：用户密码
  - is_admin：是否为管理员

#### 更新用户信息

- **接口**：PUT /api/v1/admin/users/{user_id}
- **描述**：更新用户信息（仅管理员）
- **参数**：
  - email：用户邮箱
  - password：用户密码

## TODOist

### sdk

- [ ] web SDK

### 后台管理

- [ ] 后台管理页面
  
### 服务器功能

- [x] 用户管理
  - [x] 用户注册与普通用户管理
  - [ ] 用户多知识库管理
    - [x] 用户创建多知识库
    - [ ] 知识库管理
    - [ ] toC用户管理

- [ ] 客服
  - [ ] 客服与用户聊天
  - [ ] 聊天记录管理
  
- [x] 文档库
  - [x] 文档的创建、更新、查询和软删除
  - [ ] 多种文档类型支持
    - [x] 文本
    - [ ] 图片
    - [ ] pdf
    - [ ] 网页
  - [x] 文档列表分页查询

- [x] 知识库管理
  - [x] 知识库创建与配置
  - [x] 知识库训练队列管理
  - [x] 基于图数据库的知识存储
  - [x] 智能实体识别和关系分析
  - [ ] 多ai模型配置配置
  - [ ] token计算
  - [ ] 分析
- [ ] 知识库查询
  - [x] 基于图数据库的多跳关系查询
  - [x] 基于大语言模型的智能问答
  - [x] 防止盗刷
  - [ ] 上下文信息的传递与更新
  - [ ] 提示词配置与组合
  - [ ] 访问控制

- [ ] 系统特性  - [x] 基于FastAPI的高性能异步处理
  - [ ] Docker一键部署支持

