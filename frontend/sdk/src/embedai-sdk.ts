/**
 * EmbedAI SDK 主类
 */

import { 
  EmbedAIConfig, 
  Chat, 
  Message, 
  EventListener,
  ConfigError,
  NetworkError,
  ConnectionStatus 
} from '@/types'
import { APIClient } from '@/core/api-client'
import { WebSocketClient } from '@/core/websocket-client'
import { ChatWidget } from '@/ui/widget'

export class EmbedAI {
  private config: EmbedAIConfig
  private apiClient: APIClient
  private wsClient: WebSocketClient
  private widget: ChatWidget
  private currentChat: Chat | null = null
  private isInitialized = false

  constructor(config: EmbedAIConfig) {
    this.validateConfig(config)
    this.config = this.mergeDefaultConfig(config)
    
    // 初始化客户端
    this.apiClient = new APIClient(
      this.config.serverUrl,
      this.config.clientId,
      this.config.thirdPartyUserId
    )
    
    this.wsClient = new WebSocketClient(
      this.config.serverUrl,
      this.config.clientId,
      this.config.thirdPartyUserId,
      this.config.knowledgeBaseId,
      this.config.maxReconnectAttempts,
      this.config.reconnectInterval
    )
    
    // 初始化UI组件
    this.widget = new ChatWidget(this.config)
    
    this.setupEventHandlers()
  }

  /**
   * 验证配置
   */
  private validateConfig(config: EmbedAIConfig): void {
    if (!config.serverUrl) {
      throw new ConfigError('serverUrl is required')
    }
    
    if (!config.knowledgeBaseId) {
      throw new ConfigError('knowledgeBaseId is required')
    }
    
    if (!config.clientId) {
      throw new ConfigError('clientId is required')
    }
    
    if (!config.thirdPartyUserId) {
      throw new ConfigError('thirdPartyUserId is required')
    }

    // 验证URL格式
    try {
      new URL(config.serverUrl)
    } catch {
      throw new ConfigError('Invalid serverUrl format')
    }
  }

  /**
   * 合并默认配置
   */
  private mergeDefaultConfig(config: EmbedAIConfig): EmbedAIConfig {
    return {
      language: 'zh-CN',
      autoOpen: false,
      welcomeMessage: '您好！我是您的智能助手，有什么可以帮助您的吗？',
      placeholder: '输入您的问题...',
      showAvatar: true,
      maxReconnectAttempts: 5,
      reconnectInterval: 3000,
      position: {
        horizontal: 'right',
        vertical: 'bottom',
        offset: { x: 20, y: 20 }
      },
      theme: {
        primaryColor: '#007bff',
        secondaryColor: '#6c757d',
        backgroundColor: '#ffffff',
        textColor: '#333333',
        borderColor: '#e0e0e0',
        borderRadius: '8px',
        fontSize: '14px',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)'
      },
      ...config
    }
  }

  /**
   * 设置事件处理器
   */
  private setupEventHandlers(): void {
    // Widget事件
    this.widget.on('open', () => {
      this.handleWidgetOpen()
    })

    this.widget.on('close', () => {
      this.handleWidgetClose()
    })

    this.widget.on('send_message', (content: string) => {
      this.sendMessage(content)
    })

    // WebSocket事件
    this.wsClient.on('connect', () => {
      this.widget.setConnectionStatus('connected')
    })

    this.wsClient.on('disconnect', () => {
      this.widget.setConnectionStatus('disconnected')
    })

    this.wsClient.on('status_change', (status: ConnectionStatus) => {
      this.widget.setConnectionStatus(status)
    })

    this.wsClient.on('message', (message: Message) => {
      this.handleNewMessage(message)
    })

    this.wsClient.on('typing', (data: any) => {
      this.widget.setTyping(data.isTyping)
    })

    this.wsClient.on('error', (error: Error) => {
      console.error('WebSocket error:', error)
    })

    this.wsClient.on('reconnect', (attempt: number) => {
      console.log(`WebSocket reconnecting... attempt ${attempt}`)
    })
  }

  /**
   * 初始化SDK
   */
  async init(): Promise<void> {
    if (this.isInitialized) {
      return
    }

    try {
      // 获取或创建聊天会话
      await this.initializeChat()
      
      // 连接WebSocket
      this.wsClient.connect(this.currentChat?.id)
      
      this.isInitialized = true
      
      console.log('EmbedAI SDK initialized successfully')
    } catch (error) {
      console.error('Failed to initialize EmbedAI SDK:', error)
      throw error
    }
  }

  /**
   * 初始化聊天会话
   */
  private async initializeChat(): Promise<void> {
    try {
      // 尝试获取现有聊天列表
      const chats = await this.apiClient.getChatList(0, 1)
      
      if (chats.length > 0) {
        // 使用最新的聊天会话
        this.currentChat = chats[0]
        
        // 加载历史消息
        const messages = await this.apiClient.getChatMessages(this.currentChat.id)
        messages.forEach(message => {
          this.widget.addMessage(message)
        })
      } else {
        // 创建新的聊天会话
        this.currentChat = await this.apiClient.createChat({
          third_party_user_id: this.config.thirdPartyUserId,
          kb_id: this.config.knowledgeBaseId,
          title: '新对话'
        })
      }
    } catch (error) {
      console.error('Failed to initialize chat:', error)
      throw new NetworkError('Failed to initialize chat session')
    }
  }

  /**
   * 处理Widget打开
   */
  private handleWidgetOpen(): void {
    if (!this.isInitialized) {
      this.init().catch(error => {
        console.error('Failed to initialize on widget open:', error)
      })
    }
  }

  /**
   * 处理Widget关闭
   */
  private handleWidgetClose(): void {
    // 可以在这里添加关闭时的逻辑
  }

  /**
   * 发送消息
   */
  async sendMessage(content: string): Promise<void> {
    if (!this.currentChat) {
      throw new NetworkError('No active chat session')
    }

    try {
      // 创建用户消息对象
      const userMessage: Message = {
        id: Date.now(), // 临时ID
        chat_id: this.currentChat.id,
        content,
        message_type: 'USER',
        sender_id: this.config.thirdPartyUserId,
        sender_type: 'third_party',
        created_at: new Date().toISOString(),
        read_by: []
      }

      // 立即显示用户消息
      this.widget.addMessage(userMessage)

      // 通过WebSocket发送消息
      this.wsClient.sendChatMessage(content, this.currentChat.id)
      
    } catch (error) {
      console.error('Failed to send message:', error)
      throw error
    }
  }

  /**
   * 处理新消息
   */
  private handleNewMessage(message: Message): void {
    this.widget.addMessage(message)
  }

  /**
   * 查询知识库
   */
  async queryKnowledgeBase(query: string, topK = 5): Promise<void> {
    try {
      this.wsClient.queryKnowledgeBase(query, topK)
    } catch (error) {
      console.error('Failed to query knowledge base:', error)
      throw error
    }
  }

  /**
   * 打开聊天窗口
   */
  open(): void {
    this.widget.open()
  }

  /**
   * 关闭聊天窗口
   */
  close(): void {
    this.widget.close()
  }

  /**
   * 最小化聊天窗口
   */
  minimize(): void {
    this.widget.minimize()
  }

  /**
   * 清空聊天记录
   */
  async clearChat(): Promise<void> {
    if (this.currentChat) {
      try {
        await this.apiClient.deleteChat(this.currentChat.id)
        this.widget.clearMessages()
        
        // 创建新的聊天会话
        this.currentChat = await this.apiClient.createChat({
          third_party_user_id: this.config.thirdPartyUserId,
          kb_id: this.config.knowledgeBaseId,
          title: '新对话'
        })
        
        // 重新连接WebSocket
        this.wsClient.setChatId(this.currentChat.id)
        
      } catch (error) {
        console.error('Failed to clear chat:', error)
        throw error
      }
    }
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig: Partial<EmbedAIConfig>): void {
    this.config = { ...this.config, ...newConfig }
    
    // 更新API客户端配置
    if (newConfig.clientId) {
      this.apiClient.updateClientId(newConfig.clientId)
    }
    
    if (newConfig.thirdPartyUserId) {
      this.apiClient.updateThirdPartyUserId(newConfig.thirdPartyUserId)
    }
    
    // 更新Widget配置
    this.widget.updateConfig(this.config)
  }

  /**
   * 获取连接状态
   */
  getConnectionStatus(): ConnectionStatus {
    return this.wsClient.getConnectionStatus()
  }

  /**
   * 获取当前聊天
   */
  getCurrentChat(): Chat | null {
    return this.currentChat
  }

  /**
   * 添加事件监听器
   */
  on(event: string, listener: EventListener): void {
    this.widget.on(event, listener)
  }

  /**
   * 移除事件监听器
   */
  off(event: string, listener?: EventListener): void {
    this.widget.off(event, listener)
  }

  /**
   * 销毁SDK实例
   */
  destroy(): void {
    this.wsClient.disconnect()
    this.widget.destroy()
    this.isInitialized = false
  }

  /**
   * 获取SDK版本
   */
  static getVersion(): string {
    return '1.0.0'
  }
}
