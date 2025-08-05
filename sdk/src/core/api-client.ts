/**
 * API客户端 - 处理HTTP请求
 */

import { 
  APIResponse, 
  Chat, 
  ChatCreateRequest, 
  Message, 
  QueryRequest, 
  QueryResponse,
  NetworkError,
  AuthError 
} from '@/types'

export class APIClient {
  private baseUrl: string
  private clientId: string
  private thirdPartyUserId: number

  constructor(serverUrl: string, clientId: string, thirdPartyUserId: number) {
    this.baseUrl = `${serverUrl}/api/v1`
    this.clientId = clientId
    this.thirdPartyUserId = thirdPartyUserId
  }

  /**
   * 发送HTTP请求
   */
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'X-Client-ID': this.clientId,
      'X-Third-Party-User-ID': this.thirdPartyUserId.toString()
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers
        }
      })

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new AuthError(`认证失败: ${response.statusText}`)
        }
        throw new NetworkError(`请求失败: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      if (error instanceof AuthError || error instanceof NetworkError) {
        throw error
      }
      throw new NetworkError(`网络请求失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  /**
   * 创建聊天会话
   */
  async createChat(request: ChatCreateRequest): Promise<Chat> {
    const response = await this.request<Chat>('/chat/client/create', {
      method: 'POST',
      body: JSON.stringify(request)
    })

    if (!response.success || !response.data) {
      throw new NetworkError('创建聊天会话失败')
    }

    return response.data
  }

  /**
   * 获取聊天列表
   */
  async getChatList(skip = 0, limit = 20): Promise<Chat[]> {
    const params = new URLSearchParams({
      third_party_user_id: this.thirdPartyUserId.toString(),
      skip: skip.toString(),
      limit: limit.toString()
    })

    const response = await this.request<Chat[]>(`/chat/client/list?${params}`)

    if (!response.success || !response.data) {
      throw new NetworkError('获取聊天列表失败')
    }

    return response.data
  }

  /**
   * 获取聊天详情
   */
  async getChatDetail(chatId: number): Promise<Chat> {
    const params = new URLSearchParams({
      third_party_user_id: this.thirdPartyUserId.toString()
    })

    const response = await this.request<Chat>(`/chat/client/${chatId}?${params}`)

    if (!response.success || !response.data) {
      throw new NetworkError('获取聊天详情失败')
    }

    return response.data
  }

  /**
   * 获取聊天消息列表
   */
  async getChatMessages(chatId: number, skip = 0, limit = 50): Promise<Message[]> {
    const params = new URLSearchParams({
      third_party_user_id: this.thirdPartyUserId.toString(),
      skip: skip.toString(),
      limit: limit.toString()
    })

    const response = await this.request<Message[]>(`/chat/client/${chatId}/messages?${params}`)

    if (!response.success || !response.data) {
      throw new NetworkError('获取聊天消息失败')
    }

    return response.data
  }

  /**
   * 删除聊天会话
   */
  async deleteChat(chatId: number): Promise<void> {
    const params = new URLSearchParams({
      third_party_user_id: this.thirdPartyUserId.toString()
    })

    const response = await this.request(`/chat/client/${chatId}?${params}`, {
      method: 'DELETE'
    })

    if (!response.success) {
      throw new NetworkError('删除聊天会话失败')
    }
  }

  /**
   * 查询知识库
   */
  async queryKnowledgeBase(knowledgeBaseId: number, request: QueryRequest): Promise<QueryResponse> {
    const params = new URLSearchParams({
      client_id: this.clientId,
      third_party_user_id: this.thirdPartyUserId.toString()
    })

    const response = await this.request<QueryResponse>(
      `/client/knowledge-base/${knowledgeBaseId}/query?${params}`,
      {
        method: 'POST',
        body: JSON.stringify(request)
      }
    )

    if (!response.success || !response.data) {
      throw new NetworkError('知识库查询失败')
    }

    return response.data
  }

  /**
   * 更新客户端ID
   */
  updateClientId(clientId: string): void {
    this.clientId = clientId
  }

  /**
   * 更新第三方用户ID
   */
  updateThirdPartyUserId(thirdPartyUserId: number): void {
    this.thirdPartyUserId = thirdPartyUserId
  }
}
