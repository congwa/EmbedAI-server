# RAG API使用示例

## Python客户端示例

### 基础使用

```python
import requests
import json

class RAGClient:
    def __init__(self, base_url, access_token):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def create_knowledge_base(self, name, description="", llm_config=None):
        """创建知识库"""
        data = {'name': name, 'description': description}
        if llm_config:
            data['llm_config'] = llm_config
        
        response = requests.post(
            f'{self.base_url}/admin/knowledge-bases',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def upload_document(self, kb_id, file_path, title=None):
        """上传文档"""
        files = {'file': open(file_path, 'rb')}
        data = {}
        if title:
            data['title'] = title
        
        headers = {'Authorization': self.headers['Authorization']}
        response = requests.post(
            f'{self.base_url}/admin/knowledge-bases/{kb_id}/documents',
            headers=headers,
            files=files,
            data=data
        )
        files['file'].close()
        return response.json()
    
    def train_knowledge_base(self, kb_id):
        """训练知识库"""
        response = requests.post(
            f'{self.base_url}/admin/knowledge-bases/{kb_id}/train',
            headers=self.headers
        )
        return response.json()
    
    def query_knowledge_base(self, kb_id, query, method='hybrid_search', top_k=5):
        """查询知识库"""
        data = {
            'query': query,
            'method': method,
            'top_k': top_k,
            'use_rerank': True
        }
        response = requests.post(
            f'{self.base_url}/admin/knowledge-bases/{kb_id}/query',
            headers=self.headers,
            json=data
        )
        return response.json()

# 使用示例
client = RAGClient('https://api.example.com/api/v1', 'your-access-token')

# 1. 创建知识库
kb_result = client.create_knowledge_base(
    name='技术文档知识库',
    description='用于技术文档检索',
    llm_config={
        'embeddings': {
            'provider': 'openai',
            'model': 'text-embedding-ada-002',
            'api_key': 'your-openai-key'
        }
    }
)
kb_id = kb_result['data']['id']

# 2. 上传文档
doc_result = client.upload_document(
    kb_id=kb_id,
    file_path='./tech_doc.pdf',
    title='技术文档'
)

# 3. 训练知识库
train_result = client.train_knowledge_base(kb_id)

# 4. 查询知识库
query_result = client.query_knowledge_base(
    kb_id=kb_id,
    query='如何配置系统？',
    method='hybrid_search',
    top_k=5
)

print("查询结果:")
for result in query_result['data']['results']:
    print(f"- 相关度: {result['score']:.4f}")
    print(f"  内容: {result['content'][:100]}...")
    print(f"  来源: {result['document']['title']}")
```

## JavaScript客户端示例

```javascript
class RAGClient {
    constructor(baseUrl, accessToken) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.headers = {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        };
    }

    async createKnowledgeBase(name, description = '', llmConfig = null) {
        const data = { name, description };
        if (llmConfig) data.llm_config = llmConfig;

        const response = await fetch(`${this.baseUrl}/admin/knowledge-bases`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        return await response.json();
    }

    async uploadDocument(kbId, file, title = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (title) formData.append('title', title);

        const response = await fetch(`${this.baseUrl}/admin/knowledge-bases/${kbId}/documents`, {
            method: 'POST',
            headers: {
                'Authorization': this.headers.Authorization
            },
            body: formData
        });
        return await response.json();
    }

    async trainKnowledgeBase(kbId) {
        const response = await fetch(`${this.baseUrl}/admin/knowledge-bases/${kbId}/train`, {
            method: 'POST',
            headers: this.headers
        });
        return await response.json();
    }

    async queryKnowledgeBase(kbId, query, options = {}) {
        const data = {
            query,
            method: options.method || 'hybrid_search',
            top_k: options.topK || 5,
            use_rerank: options.useRerank !== false
        };

        const response = await fetch(`${this.baseUrl}/admin/knowledge-bases/${kbId}/query`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        return await response.json();
    }
}

// 使用示例
const client = new RAGClient('https://api.example.com/api/v1', 'your-access-token');

async function example() {
    try {
        // 创建知识库
        const kbResult = await client.createKnowledgeBase(
            '技术文档知识库',
            '用于技术文档检索'
        );
        const kbId = kbResult.data.id;

        // 上传文档（假设有文件输入）
        const fileInput = document.getElementById('fileInput');
        if (fileInput.files.length > 0) {
            const docResult = await client.uploadDocument(
                kbId,
                fileInput.files[0],
                '技术文档'
            );
            console.log('文档上传成功:', docResult);
        }

        // 训练知识库
        const trainResult = await client.trainKnowledgeBase(kbId);
        console.log('训练启动:', trainResult);

        // 查询知识库
        const queryResult = await client.queryKnowledgeBase(
            kbId,
            '如何配置系统？',
            { method: 'hybrid_search', topK: 5 }
        );

        console.log('查询结果:');
        queryResult.data.results.forEach(result => {
            console.log(`- 相关度: ${result.score.toFixed(4)}`);
            console.log(`  内容: ${result.content.substring(0, 100)}...`);
            console.log(`  来源: ${result.document.title}`);
        });

    } catch (error) {
        console.error('操作失败:', error);
    }
}

example();
```

## 常见使用场景

### 1. 智能客服系统

```python
class IntelligentCustomerService:
    def __init__(self, api_url, token, kb_id):
        self.client = RAGClient(api_url, token)
        self.kb_id = kb_id
    
    def answer_question(self, question):
        """回答用户问题"""
        try:
            # 查询知识库
            results = self.client.query_knowledge_base(
                kb_id=self.kb_id,
                query=question,
                method='hybrid_search',
                top_k=3
            )
            
            # 提取最相关的答案
            if results['data']['results']:
                best_result = results['data']['results'][0]
                if best_result['score'] > 0.7:
                    return {
                        'answer': best_result['content'],
                        'confidence': best_result['score'],
                        'source': best_result['document']['title'],
                        'need_human': False
                    }
            
            return {
                'answer': '抱歉，我没有找到相关信息。请联系人工客服。',
                'confidence': 0.0,
                'source': None,
                'need_human': True
            }
            
        except Exception as e:
            return {
                'answer': '系统暂时无法处理您的问题，请稍后重试。',
                'confidence': 0.0,
                'source': None,
                'need_human': True,
                'error': str(e)
            }

# 使用示例
customer_service = IntelligentCustomerService(
    api_url='https://api.example.com/api/v1',
    token='your-token',
    kb_id=1
)

questions = [
    "如何重置密码？",
    "产品保修期是多长时间？",
    "如何申请退款？"
]

for question in questions:
    response = customer_service.answer_question(question)
    print(f"问题: {question}")
    print(f"回答: {response['answer']}")
    print(f"置信度: {response['confidence']:.2f}")
    print(f"需要人工: {'是' if response['need_human'] else '否'}")
    print("-" * 50)
```

### 2. 文档搜索引擎

```python
class DocumentSearchEngine:
    def __init__(self, api_url, token):
        self.client = RAGClient(api_url, token)
    
    def search_documents(self, kb_id, query, search_type='hybrid'):
        """搜索文档"""
        methods = {
            'semantic': 'semantic_search',
            'keyword': 'keyword_search',
            'hybrid': 'hybrid_search'
        }
        
        method = methods.get(search_type, 'hybrid_search')
        
        results = self.client.query_knowledge_base(
            kb_id=kb_id,
            query=query,
            method=method,
            top_k=10
        )
        
        # 格式化搜索结果
        formatted_results = []
        for result in results['data']['results']:
            formatted_results.append({
                'title': result['document']['title'],
                'content_preview': result['content'][:200] + '...',
                'relevance_score': result['score'],
                'document_id': result['document']['id'],
                'chunk_id': result['chunk']['id']
            })
        
        return {
            'query': query,
            'search_type': search_type,
            'total_results': len(formatted_results),
            'results': formatted_results
        }
    
    def get_document_summary(self, kb_id, doc_id):
        """获取文档摘要"""
        # 使用文档的第一个分块作为摘要
        chunks = self.client.get_document_chunks(kb_id, doc_id, page_size=1)
        
        if chunks['data']['items']:
            first_chunk = chunks['data']['items'][0]
            return first_chunk['content'][:500] + '...'
        
        return "无法获取文档摘要"

# 使用示例
search_engine = DocumentSearchEngine('https://api.example.com/api/v1', 'your-token')

# 搜索文档
search_results = search_engine.search_documents(
    kb_id=1,
    query='API接口使用方法',
    search_type='hybrid'
)

print(f"搜索查询: {search_results['query']}")
print(f"搜索类型: {search_results['search_type']}")
print(f"结果数量: {search_results['total_results']}")
print("\n搜索结果:")

for i, result in enumerate(search_results['results'], 1):
    print(f"{i}. {result['title']}")
    print(f"   相关度: {result['relevance_score']:.4f}")
    print(f"   预览: {result['content_preview']}")
    print()
```

### 3. 批量文档处理

```python
import os
import time

def batch_document_processing(kb_id, document_folder):
    """批量文档处理"""
    client = RAGClient('https://api.example.com/api/v1', 'your-token')
    
    # 支持的文件格式
    supported_formats = ['.pdf', '.docx', '.xlsx', '.md', '.html', '.txt']
    
    # 收集所有文档
    documents_to_upload = []
    for root, dirs, files in os.walk(document_folder):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            if file_ext in supported_formats:
                documents_to_upload.append({
                    'path': file_path,
                    'title': file,
                    'category': os.path.basename(root)
                })
    
    print(f"找到 {len(documents_to_upload)} 个文档待处理")
    
    # 批量上传
    uploaded_docs = []
    failed_uploads = []
    
    for doc_info in documents_to_upload:
        try:
            result = client.upload_document(
                kb_id=kb_id,
                file_path=doc_info['path'],
                title=doc_info['title']
            )
            uploaded_docs.append(result['data'])
            print(f"✓ 上传成功: {doc_info['title']}")
        except Exception as e:
            failed_uploads.append({'doc': doc_info, 'error': str(e)})
            print(f"✗ 上传失败: {doc_info['title']} - {e}")
    
    print(f"\n上传完成: 成功 {len(uploaded_docs)}, 失败 {len(failed_uploads)}")
    
    # 开始训练
    if uploaded_docs:
        print("开始训练知识库...")
        train_result = client.train_knowledge_base(kb_id)
        print(f"训练任务已启动: {train_result['data']['task_id']}")
        
        # 监控训练进度
        while True:
            status = client.get_training_status(kb_id)
            training_status = status['data']['status']
            progress = status['data'].get('progress', 0)
            
            print(f"训练进度: {progress}% - {training_status}")
            
            if training_status in ['completed', 'failed']:
                break
            
            time.sleep(10)
        
        if training_status == 'completed':
            print("✓ 训练完成！")
        else:
            print("✗ 训练失败")
    
    return {
        'uploaded': len(uploaded_docs),
        'failed': len(failed_uploads),
        'failed_details': failed_uploads
    }

# 使用示例
result = batch_document_processing(
    kb_id=1,
    document_folder='./documents'
)

print(f"批量处理结果: {result}")
```

## 错误处理示例

```python
class RAGClientWithErrorHandling(RAGClient):
    """带错误处理的RAG客户端"""
    
    def safe_query(self, kb_id, query, **kwargs):
        """安全查询方法"""
        try:
            return self.query_knowledge_base(kb_id, query, **kwargs)
        except requests.exceptions.Timeout:
            return {
                'error': 'TIMEOUT',
                'message': '请求超时，请稍后重试'
            }
        except requests.exceptions.ConnectionError:
            return {
                'error': 'CONNECTION_ERROR',
                'message': '网络连接失败，请检查网络'
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {
                    'error': 'NOT_FOUND',
                    'message': '知识库不存在'
                }
            elif e.response.status_code == 403:
                return {
                    'error': 'PERMISSION_DENIED',
                    'message': '权限不足'
                }
            else:
                return {
                    'error': 'HTTP_ERROR',
                    'message': f'HTTP错误: {e.response.status_code}'
                }
        except Exception as e:
            return {
                'error': 'UNKNOWN_ERROR',
                'message': f'未知错误: {str(e)}'
            }
    
    def retry_operation(self, operation, max_retries=3, delay=1):
        """重试操作"""
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"操作失败，{delay}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                time.sleep(delay)

# 使用示例
client = RAGClientWithErrorHandling('https://api.example.com/api/v1', 'your-token')

# 安全查询
result = client.safe_query(
    kb_id=1,
    query='测试查询',
    method='hybrid_search'
)

if 'error' in result:
    print(f"查询失败: {result['message']}")
else:
    print("查询成功:", result['data']['results'])

# 重试操作
def upload_operation():
    return client.upload_document(
        kb_id=1,
        file_path='./test.pdf',
        title='测试文档'
    )

try:
    upload_result = client.retry_operation(upload_operation, max_retries=3)
    print("上传成功:", upload_result)
except Exception as e:
    print(f"上传最终失败: {e}")
```

这些示例展示了如何在实际项目中使用RAG API，包括基础操作、常见场景和错误处理。开发者可以根据自己的需求进行调整和扩展。