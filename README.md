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
  - 完整的RESTful API支持，支持任意系统快速集成
  - 支持Docker一键部署，简化运维成本

- 基于图数据库的知识存储
  - 相比传统关系型数据库，图数据库能更自然地表达实体间的复杂关系
  - 支持高效的图遍历算法，显著提升多跳关系查询性能
  - 灵活的图模型设计，便于动态扩展知识结构
  - 强大的关系分析能力，支持知识推理和关联发现

- AI问答处理流程
  - 智能实体识别：区分命名实体和通用实体，通过向量编码实现精准匹配
  - 多层次评分机制：
    - 实体评分：基于向量相似度，对命名实体和通用实体采用差异化评分策略
    - 图结构评分：利用图结构信息重新评估实体重要性，考虑实体间关系强度
    - 关系评分：基于实体分数评估关系重要性，使用实体到关系的映射矩阵
    - 文本块评分：通过关系找到相关文本块，确保上下文完整性
  - 确保查询理解准确性和结果相关性

- 企业级特性
  - 多租户隔离机制
  - 访问控制策略
  - 文档的软删除机制
  - 知识库训练队列管理

## 用户和知识库的关系

```sh
User (用户)
├── owned_knowledge_bases (拥有的知识库，一对多)
│   └── KnowledgeBase.owner_id 引用 User.id
│
└── knowledge_bases (参与的知识库，多对多)
    └── knowledge_base_users (关联表)
        ├── user_id 引用 User.id
        ├── knowledge_base_id 引用 KnowledgeBase.id
        ├── permission (权限)
        └── created_at (加入时间)

KnowledgeBase (知识库)
├── owner (所有者，多对一)
│   └── owner_id 引用 User.id
│
└── users (成员，多对多)
    └── knowledge_base_users (关联表)
        ├── knowledge_base_id 引用 KnowledgeBase.id
        ├── user_id 引用 User.id
        ├── permission (权限)
        └── created_at (加入时间)
```

## 数据库关系

[![关系图](https://mermaid.ink/img/pako:eNqNVMuumzAQ_RXL6yQKuYQEltVVN3dTqeqmimQ5eEJcwKa2aS4l-fcOIQ9eleKN7TmH8fjMMTWNtQAaUTDvkieG5ztFcPywYMj5PJ_rul1HZEdjA9yB3dEh50w-lD5lIBL4wi1cyfqkJpg1eddxmYNyUxn7WSY_0Mpx2Wbu5K7bdTMkMqUg3z6eIeuMVAmBnMtsFD1yewTBCm7tSRvxxPdaZ8AVkZZxkUs1jcRO_oFRUitSlkI1jgPe2PWhpuBWB8H2FcPav3ZqFxh3MocHhbsWvNwF6Iv2khKK59DnYbfADM--sYVG4TrX_2W1IvDJ8yID9rsEI7GDA1Q56SrmqmIEZVnOsIsHmYwOQv1TnJmQ5omBKnPiDFbQQNZxV9oJeboM09VpmnXA6dr3Lu1WxoMExmgzkQXvXE514uHUl5qACmVj5zQGxxSD-wsdX8V8wRc9sCzECOy4V0AGCPerTe9-Yns01NAT_3frhc5oDga9IvB_cpVgR90R0Gq0ebqCm7R5tg2Pl05_r1RMI2dKmFGjy-RIowPPLO7aqm__ozul4Oqn1t0tjWr6SaO5768X3nLle6HvvS3Dt3BGKxr5m-1itQ62AQLbYO1t_MuM_r1m8BZeEIThcu35_irYbvzV5R_K2pLI?type=png)](https://mermaid.live/edit#pako:eNqNVMuumzAQ_RXL6yQKuYQEltVVN3dTqeqmimQ5eEJcwKa2aS4l-fcOIQ9eleKN7TmH8fjMMTWNtQAaUTDvkieG5ztFcPywYMj5PJ_rul1HZEdjA9yB3dEh50w-lD5lIBL4wi1cyfqkJpg1eddxmYNyUxn7WSY_0Mpx2Wbu5K7bdTMkMqUg3z6eIeuMVAmBnMtsFD1yewTBCm7tSRvxxPdaZ8AVkZZxkUs1jcRO_oFRUitSlkI1jgPe2PWhpuBWB8H2FcPav3ZqFxh3MocHhbsWvNwF6Iv2khKK59DnYbfADM--sYVG4TrX_2W1IvDJ8yID9rsEI7GDA1Q56SrmqmIEZVnOsIsHmYwOQv1TnJmQ5omBKnPiDFbQQNZxV9oJeboM09VpmnXA6dr3Lu1WxoMExmgzkQXvXE514uHUl5qACmVj5zQGxxSD-wsdX8V8wRc9sCzECOy4V0AGCPerTe9-Yns01NAT_3frhc5oDga9IvB_cpVgR90R0Gq0ebqCm7R5tg2Pl05_r1RMI2dKmFGjy-RIowPPLO7aqm__ozul4Oqn1t0tjWr6SaO5768X3nLle6HvvS3Dt3BGKxr5m-1itQ62AQLbYO1t_MuM_r1m8BZeEIThcu35_irYbvzV5R_K2pLI)

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
    - [x] 知识库管理
    - [x] 普通用户权限管理

- [ ] 客服
  - [ ] 客服与用户聊天 (进行中)
  - [ ] 聊天记录管理（进行中）

- [x] 文档库
  - [x] 文档的创建、更新、查询和软删除
  - [ ] 多种文档类型支持
    - [x] 文本
    - [ ] 图片
    - [ ] pdf
    - [ ] 网页
  - [x] 文档列表分页查询

- [ ] langchain现有工具使用
  
- [x] 知识库管理
  - [x] 知识库创建与配置
  - [x] 知识库训练队列管理
  - [x] 基于图数据库的知识存储
  - [x] 智能实体识别和关系分析
  - [ ] 多ai模型配置配置
  - [ ] token计算
  - [ ] 分析
- 
- [ ] 知识库查询
  - [x] 基于图数据库的多跳关系查询
  - [x] 基于大语言模型的智能问答
  - [x] 防止盗刷
  - [ ] 上下文信息的传递与更新
  - [ ] 提示词配置与组合
  - [ ] 访问控制

- [ ] 系统特性  - [x] 基于FastAPI的高性能异步处理
  - [ ] Docker一键部署支持

