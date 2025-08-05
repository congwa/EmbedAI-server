import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'
import { toast } from '@/hooks/use-toast'
import { withRetry } from '@/utils/retry'
import {
  AdminLoginRequest,
  AdminRegisterRequest,
  ApiResponse,
  ApiErrorResponse,
  CreateDocumentRequest,
  CreateKnowledgeBaseRequest,
  CreateUserRequest,
  Document,
  GetDocumentsQuery,
  LoginResponse,
  UpdateKnowledgeBaseRequest,
  PaginationData,
  User,
  UpdatePasswordRequest,
  AdminChangeUserPasswordRequest,
  GetKnowledgeBasesQuery,
  KnowledgeBaseDetail,
  KnowledgeBasePermissionCreate,
  KnowledgeBasePermissionUpdate,
  KnowledgeBaseTrainResponse,
  KnowledgeBaseQueryRequest,
  KnowledgeBaseQueryResponse,
  Chat,
  ChatMessage,
  ChatMessageCreate,
  GetChatsQuery,
  ChatStats,
} from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 添加全局响应拦截器
axios.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse
    if (!data.success) {
      // eslint-disable-next-line no-console
      console.log('API Error Response:', data)
     
      toast({
        title: '请求失败',
        description: data.message || '操作失败',
        variant: 'destructive',
      })
    }
    return response
  },
  (error) => {
    let errorResponse: ApiErrorResponse | undefined
  

    if (error.response) {
      errorResponse = error.response.data as ApiErrorResponse
      // eslint-disable-next-line no-console
      console.log('Error Response:', errorResponse)

      switch (error.response.status) {
        case 401:
          useAuthStore.getState().reset()
          if (!window.location.pathname.includes('/sign-in')) {
            window.location.href = '/sign-in'
          }
          toast({
            title: '',
            description: errorResponse?.message || '您的会话已过期，请重新登录',
            variant: 'destructive',
          })
          break
        case 403:
          useAuthStore.getState().reset()
          if (!window.location.pathname.includes('/sign-in')) {
            window.location.href = '/sign-in'
          }
          toast({
            title: '访问被拒绝',
            description: errorResponse?.message || '您没有权限访问此资源',
            variant: 'destructive',
          })
          break
        case 422:
        case 400:
          toast({
            title: '请求失败',
            description: errorResponse?.message || '数据验证错误',
            variant: 'destructive',
          })
          break
        case 500:
          toast({
            title: '服务器错误',
            description: errorResponse?.message || '服务器发生错误，请稍后重试',
            variant: 'destructive',
          })
          break
        default:
          toast({
            title: '操作失败',
            description: errorResponse?.message || '请求失败，请重试',
            variant: 'destructive',
          })
      }
    } else if (error.request) {
      toast({
        title: '网络错误',
        description: '无法连接到服务器，请检查网络连接',
        variant: 'destructive',
      })
    } else {
      toast({
        title: '请求错误',
        description: error.message,
        variant: 'destructive',
      })
    }
    return Promise.reject(error)
  }
)

class AdminService {
  private static instance: AdminService
  private baseUrl: string

  private constructor() {
    this.baseUrl = BASE_URL
  }

  public static getInstance(): AdminService {
    if (!AdminService.instance) {
      AdminService.instance = new AdminService()
    }
    return AdminService.instance
  }

  private getHeaders() {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    const token = useAuthStore.getState().accessToken
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  }

  // 管理员注册
  async register(data: AdminRegisterRequest): Promise<ApiResponse> {
    const response = await axios.post<ApiResponse>(
      `${this.baseUrl}/api/v1/admin/register`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 管理员登录
  async login(data: AdminLoginRequest): Promise<ApiResponse<LoginResponse>> {
    const response = await axios.post<ApiResponse<LoginResponse>>(
      `${this.baseUrl}/api/v1/admin/login`,
      data,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    return response.data
  }

  // 创建普通用户
  async createUser(data: CreateUserRequest): Promise<ApiResponse<User>> {
    return withRetry(async () => {
      const response = await axios.post<ApiResponse<User>>(
        `${this.baseUrl}/api/v1/admin/users`,
        data,
        { headers: this.getHeaders() }
      )
      return response.data
    }, { maxRetries: 2 })
  }

  // 获取普通用户列表
  async getUsers(
    page: number = 1,
    page_size: number = 10
  ): Promise<ApiResponse<PaginationData<User>>> {
    const response = await axios.get<ApiResponse<PaginationData<User>>>(
      `${this.baseUrl}/api/v1/admin/users`,
      {
        params: { page, page_size },
        headers: this.getHeaders(),
      }
    )
    return response.data
  }

  // 修改用户状态
  async updateUserStatus(userId: number, is_active: boolean): Promise<ApiResponse<User>> {
    return withRetry(async () => {
      const response = await axios.put<ApiResponse<User>>(
        `${this.baseUrl}/api/v1/admin/users/${userId}/status`,
        { is_active },
        { headers: this.getHeaders() }
      )
      return response.data
    }, { maxRetries: 2 })
  }

  // 修改用户管理员权限
  async updateUserAdmin(userId: number, is_admin: boolean): Promise<ApiResponse<User>> {
    const response = await axios.put<ApiResponse<User>>(
      `${this.baseUrl}/api/v1/admin/users/${userId}/admin`,
      { is_admin },
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 重置用户密钥对
  async resetUserKeys(userId: number): Promise<ApiResponse<User>> {
    return withRetry(async () => {
      const response = await axios.post<ApiResponse<User>>(
        `${this.baseUrl}/api/v1/admin/users/${userId}/reset-keys`,
        {},
        { headers: this.getHeaders() }
      )
      return response.data
    }, { maxRetries: 2 })
  }

  // 知识库管理相关接口
  async getKnowledgeBases(params: GetKnowledgeBasesQuery): Promise<ApiResponse<PaginationData<KnowledgeBaseDetail>>> {
    const response = await axios.get<ApiResponse<PaginationData<KnowledgeBaseDetail>>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases`,
      {
        params,
        headers: this.getHeaders(),
      }
    )
    return response.data
  }

  async createKnowledgeBase(data: CreateKnowledgeBaseRequest): Promise<ApiResponse<KnowledgeBaseDetail>> {
    const response = await axios.post<ApiResponse<KnowledgeBaseDetail>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  async updateKnowledgeBase(
    id: number,
    data: UpdateKnowledgeBaseRequest
  ): Promise<ApiResponse<KnowledgeBaseDetail>> {
    const response = await axios.put<ApiResponse<KnowledgeBaseDetail>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases/${id}`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  async deleteKnowledgeBase(id: number): Promise<ApiResponse<null>> {
    const response = await axios.delete<ApiResponse<null>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases/${id}`,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  async addKnowledgeBaseUser(
    kb_id: number,
    data: KnowledgeBasePermissionCreate
  ): Promise<ApiResponse<null>> {
    const response = await axios.post<ApiResponse<null>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases/${kb_id}/members`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  async updateKnowledgeBaseUserPermission(
    kb_id: number,
    user_id: number,
    data: KnowledgeBasePermissionUpdate
  ): Promise<ApiResponse<null>> {
    const response = await axios.put<ApiResponse<null>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases/${kb_id}/members/${user_id}`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  async removeKnowledgeBaseUser(kb_id: number, user_id: number): Promise<ApiResponse<null>> {
    const response = await axios.delete<ApiResponse<null>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases/${kb_id}/members/${user_id}`,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  async trainKnowledgeBase(id: number): Promise<ApiResponse<KnowledgeBaseTrainResponse>> {
    return withRetry(async () => {
      const response = await axios.post<ApiResponse<KnowledgeBaseTrainResponse>>(
        `${this.baseUrl}/api/v1/admin/knowledge-bases/${id}/train`,
        {},
        { headers: this.getHeaders() }
      )
      return response.data
    }, { maxRetries: 3, retryDelay: 2000 }) // 训练操作使用更长的重试间隔
  }

  async queryKnowledgeBase(
    id: number,
    data: KnowledgeBaseQueryRequest
  ): Promise<ApiResponse<KnowledgeBaseQueryResponse>> {
    const response = await axios.post<ApiResponse<KnowledgeBaseQueryResponse>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases/${id}/query`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  async getKnowledgeBase(id: number): Promise<ApiResponse<KnowledgeBaseDetail>> {
    const response = await axios.get<ApiResponse<KnowledgeBaseDetail>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases/${id}`,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  async getMyKnowledgeBases(): Promise<ApiResponse<KnowledgeBaseDetail[]>> {
    const response = await axios.get<ApiResponse<KnowledgeBaseDetail[]>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases/my`,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 创建文本文档
  async createTextDocument(
    data: CreateDocumentRequest,
    knowledgeBaseId: number
  ): Promise<ApiResponse<Document>> {
    const response = await axios.post<ApiResponse<Document>>(
      `${this.baseUrl}/api/v1/admin/documents/knowledge-bases/${knowledgeBaseId}/documents/text`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 上传文件创建文档
  async uploadDocument(
    file: File,
    knowledgeBaseId: number,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<Document>> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post<ApiResponse<Document>>(
      `${this.baseUrl}/api/v1/admin/documents/knowledge-bases/${knowledgeBaseId}/documents/upload`,
      formData,
      {
        headers: {
          ...this.getHeaders(),
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        },
      }
    )
    return response.data
  }

  // 获取文档列表
  async getDocuments(
    query: GetDocumentsQuery
  ): Promise<ApiResponse<PaginationData<Document>>> {
    const response = await axios.get<ApiResponse<PaginationData<Document>>>(
      `${this.baseUrl}/api/v1/admin/knowledge-bases/${query.knowledge_base_id}/documents`,
      {
        params: {
          skip: query.skip,
          limit: query.limit,
          title: query.title,
          doc_type: query.doc_type,
          start_time: query.start_time,
          end_time: query.end_time,
        },
        headers: this.getHeaders(),
      }
    )
    return response.data
  }

  // 更新文档
  async updateDocument(
    docId: number,
    data: Partial<CreateDocumentRequest>
  ): Promise<ApiResponse<Document>> {
    const response = await axios.put<ApiResponse<Document>>(
      `${this.baseUrl}/api/v1/admin/documents/${docId}`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 删除文档
  async deleteDocument(docId: number): Promise<ApiResponse<Document>> {
    const response = await axios.delete<ApiResponse<Document>>(
      `${this.baseUrl}/api/v1/admin/documents/${docId}`,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 重新处理文档
  async reprocessDocument(docId: number): Promise<ApiResponse<Document>> {
    const response = await axios.post<ApiResponse<Document>>(
      `${this.baseUrl}/api/v1/admin/documents/${docId}/reprocess`,
      {},
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 修改密码
  async updatePassword(data: UpdatePasswordRequest): Promise<ApiResponse> {
    const response = await axios.put<ApiResponse>(
      `${this.baseUrl}/api/v1/admin/password`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 管理员修改用户密码
  async adminChangeUserPassword(
    userId: number,
    data: AdminChangeUserPasswordRequest
  ): Promise<ApiResponse> {
    const response = await axios.put<ApiResponse>(
      `${this.baseUrl}/api/v1/admin/users/${userId}/password`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 聊天管理相关接口

  // 聊天管理相关接口 (基于实际API文档)

  // 获取聊天列表
  async getChats(params: GetChatsQuery): Promise<ApiResponse<PaginationData<Chat>>> {
    const response = await axios.get<ApiResponse<PaginationData<Chat>>>(
      `${this.baseUrl}/api/v1/chat/admin`,
      {
        params: {
          skip: params.skip,
          limit: params.limit,
          include_inactive: params.include_inactive,
          all_chats: params.all_chats,
          user_id: params.user_id,
          knowledge_base_id: params.knowledge_base_id,
          status: params.status,
        },
        headers: this.getHeaders(),
      }
    )
    return response.data
  }

  // 获取聊天详情
  async getChatDetail(chatId: number): Promise<ApiResponse<Chat>> {
    const response = await axios.get<ApiResponse<Chat>>(
      `${this.baseUrl}/api/v1/chat/admin/${chatId}`,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 获取聊天消息列表
  async getChatMessages(chatId: number, skip?: number, limit?: number): Promise<ApiResponse<ChatMessage[]>> {
    const response = await axios.get<ApiResponse<ChatMessage[]>>(
      `${this.baseUrl}/api/v1/chat/admin/${chatId}/messages`,
      {
        params: { skip, limit },
        headers: this.getHeaders(),
      }
    )
    return response.data
  }

  // 发送聊天消息
  async sendChatMessage(chatId: number, data: ChatMessageCreate): Promise<ApiResponse<ChatMessage>> {
    const response = await axios.post<ApiResponse<ChatMessage>>(
      `${this.baseUrl}/api/v1/chat/admin/${chatId}/messages`,
      data,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 切换聊天模式
  async switchChatMode(chatId: number, mode: string): Promise<ApiResponse<null>> {
    const response = await axios.post<ApiResponse<null>>(
      `${this.baseUrl}/api/v1/chat/admin/${chatId}/switch-mode`,
      {},
      {
        params: { mode },
        headers: this.getHeaders(),
      }
    )
    return response.data
  }

  // 加入聊天
  async joinChat(chatId: number): Promise<ApiResponse<null>> {
    const response = await axios.post<ApiResponse<null>>(
      `${this.baseUrl}/api/v1/chat/admin/${chatId}/join`,
      {},
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 离开聊天
  async leaveChat(chatId: number): Promise<ApiResponse<null>> {
    const response = await axios.post<ApiResponse<null>>(
      `${this.baseUrl}/api/v1/chat/admin/${chatId}/leave`,
      {},
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 恢复聊天
  async restoreChat(chatId: number): Promise<ApiResponse<null>> {
    const response = await axios.post<ApiResponse<null>>(
      `${this.baseUrl}/api/v1/chat/admin/${chatId}/restore`,
      {},
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 获取已删除的聊天列表
  async getDeletedChats(skip?: number, limit?: number): Promise<ApiResponse<PaginationData<Chat>>> {
    const response = await axios.get<ApiResponse<PaginationData<Chat>>>(
      `${this.baseUrl}/api/v1/chat/admin/deleted`,
      {
        params: { skip, limit },
        headers: this.getHeaders(),
      }
    )
    return response.data
  }

  // 获取用户聊天统计
  async getUserChatStats(thirdPartyUserId: number): Promise<ApiResponse<ChatStats>> {
    const response = await axios.get<ApiResponse<ChatStats>>(
      `${this.baseUrl}/api/v1/chat/admin/users/${thirdPartyUserId}/stats`,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // 获取知识库聊天统计
  async getKnowledgeBaseChatStats(kbId: number): Promise<ApiResponse<ChatStats>> {
    const response = await axios.get<ApiResponse<ChatStats>>(
      `${this.baseUrl}/api/v1/chat/admin/knowledge-bases/${kbId}/stats`,
      { headers: this.getHeaders() }
    )
    return response.data
  }

  // WebSocket 连接管理 (基于实际API端点)
  createChatWebSocket(chatId: number, adminId: number, clientId: string): WebSocket {
    const wsUrl = this.baseUrl.replace('http', 'ws')
    const params = new URLSearchParams({
      client_id: clientId,
      admin_id: adminId.toString(),
    })
    
    // 实际的管理端WebSocket端点
    const ws = new WebSocket(`${wsUrl}/api/v1/ws/admin/${chatId}?${params}`)
    
    ws.onopen = () => {
      // eslint-disable-next-line no-console
      console.log(`Admin WebSocket connected to chat ${chatId}`)
    }
    
    ws.onerror = (error) => {
      // eslint-disable-next-line no-console
      console.error('WebSocket error:', error)
      toast({
        title: 'WebSocket连接错误',
        description: '实时聊天连接失败，请刷新页面重试',
        variant: 'destructive',
      })
    }
    
    ws.onclose = (event) => {
      // eslint-disable-next-line no-console
      console.log('WebSocket closed:', event.code, event.reason)
      if (event.code !== 1000) {
        // 非正常关闭，显示错误信息
        toast({
          title: 'WebSocket连接断开',
          description: '实时聊天连接已断开，正在尝试重连...',
          variant: 'destructive',
        })
      }
    }
    
    return ws
  }
}

export const adminService = AdminService.getInstance()
