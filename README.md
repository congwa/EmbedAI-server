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

## TODO LIST

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



## 查询过程

让我为您详细解释每个步骤的作用和原因：

1. 生成查询嵌入

- 作用：将文本转换为向量表示
- 原因：
  * 便于在向量空间中进行相似度计算
  * 区分处理命名实体和通用实体，通过添加[NONE]前缀来区分实体类型
  * 将查询文本也转换为向量，实现统一的相似度计算

2. 向量数据库评分

- 作用：基于向量相似度为实体打分
- 原因：
  * 命名实体使用严格匹配（top_k=1），因为命名实体需要精确匹配
  * 通用实体使用模糊匹配（top_k=20），允许更多相关实体的召回
  * 使用不同的阈值控制匹配质量

3. 实体评分合并

- 作用：整合不同来源的实体评分
- 原因：
  * 使用max操作选择最高分，确保最相关的匹配被保留
  * 统一评分标准，便于后续处理

4. 图结构评分

- 作用：利用图结构信息进行二次评分
- 原因：
  * 考虑实体间的关系网络
  * 利用图的结构特征提升评分的准确性
  * 补充纯向量相似度无法捕捉的结构信息

5. 实体检索

- 作用：根据最终评分提取相关实体
- 原因：
  * 使用排序后的评分确保获取最相关的实体
  * 异步获取实体信息提高效率
  * 过滤无效实体，确保结果质量

6. 关系检索

- 作用：基于已选实体提取相关关系
- 原因：
  * 利用实体评分传导到关系层面
  * 确保关系的两端实体都具有较高相关性
  * 构建实体间的语义连接

7. 文档块检索

- 作用：获取支持关系的原始文本证据
- 原因：
  * 提供关系的上下文支持
  * 通过文档块回溯到原始信息
  * 为最终答案生成提供证据支持

8. 上下文构建

- 作用：组织检索到的所有信息
- 原因：
  * 将实体、关系、文档块统一组织
  * 提供结构化的上下文信息
  * 便于后续的答案生成

这种层层递进的设计体现了：

1. 从表层到深层的信息提取过程
2. 多维度的相关性评估机制
3. 完整的知识图谱利用策略
4. 高效的异步处理机制
