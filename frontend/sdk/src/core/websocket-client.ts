/**
 * WebSocket客户端 - 处理实时通信
 */

import { 
  WSMessage, 
  Message, 
  ConnectionStatus,
  EventListener,
  NetworkError 
} from '@/types'

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private clientId: string
  private thirdPartyUserId: number
  private knowledgeBaseId: number
  private chatId: number | null = null
  private listeners: Map<string, EventListener[]> = new Map()
  private connectionStatus: ConnectionStatus = 'disconnected'
  private reconnectAttempts = 0
  private maxReconnectAttempts: number
  private reconnectInterval: number
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private isManualClose = false

  constructor(
    serverUrl: string,
    clientId: string,
    thirdPartyUserId: number,
    knowledgeBaseId: number,
    maxReconnectAttempts = 5,
    reconnectInterval = 3000
  ) {
    this.url = `${serverUrl.replace('http', 'ws')}/ws/client`
    this.clientId = clientId
    this.thirdPartyUserId = thirdPartyUserId
    this.knowledgeBaseId = knowledgeBaseId
    this.maxReconnectAttempts = maxReconnectAttempts
    this.reconnectInterval = reconnectInterval
  }

  /**
   * 连接WebSocket
   */
  connect(chatId?: number): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return
    }

    this.isManualClose = false
    this.chatId = chatId || null
    this.setConnectionStatus('connecting')

    const params = new URLSearchParams({
      client_id: this.clientId,
      third_party_user_id: this.thirdPartyUserId.toString(),
      kb_id: this.knowledgeBaseId.toString(),
      ...(this.chatId && { chat_id: this.chatId.toString() })
    })

    const wsUrl = `${this.url}?${params}`

    try {
      this.ws = new WebSocket(wsUrl)
      this.setupEventHandlers()
    } catch (error) {
      this.setConnectionStatus('error')
      this.emit('error', new NetworkError('WebSocket连接失败'))
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isManualClose = true
    this.clearTimers()
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    
    this.setConnectionStatus('disconnected')
  }

  /**
   * 发送消息
   */
  sendMessage(message: WSMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new NetworkError('WebSocket未连接')
    }

    try {
      this.ws.send(JSON.stringify(message))
    } catch (error) {
      throw new NetworkError('发送消息失败')
    }
  }

  /**
   * 发送聊天消息
   */
  sendChatMessage(content: string, chatId?: number): void {
    const message: WSMessage = {
      type: 'chat_message',
      payload: {
        content,
        chat_id: chatId || this.chatId
      },
      request_id: this.generateRequestId()
    }

    this.sendMessage(message)
  }

  /**
   * 查询知识库
   */
  queryKnowledgeBase(query: string, topK = 5): void {
    const message: WSMessage = {
      type: 'query',
      payload: {
        query,
        top_k: topK
      },
      request_id: this.generateRequestId()
    }

    this.sendMessage(message)
  }

  /**
   * 设置聊天ID
   */
  setChatId(chatId: number): void {
    this.chatId = chatId
  }

  /**
   * 获取连接状态
   */
  getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus
  }

  /**
   * 添加事件监听器
   */
  on(event: string, listener: EventListener): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event)!.push(listener)
  }

  /**
   * 移除事件监听器
   */
  off(event: string, listener?: EventListener): void {
    if (!this.listeners.has(event)) {
      return
    }

    if (!listener) {
      this.listeners.delete(event)
      return
    }

    const listeners = this.listeners.get(event)!
    const index = listeners.indexOf(listener)
    if (index > -1) {
      listeners.splice(index, 1)
    }
  }

  /**
   * 触发事件
   */
  private emit(event: string, ...args: any[]): void {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(...args)
        } catch (error) {
          console.error('Event listener error:', error)
        }
      })
    }
  }

  /**
   * 设置WebSocket事件处理器
   */
  private setupEventHandlers(): void {
    if (!this.ws) return

    this.ws.onopen = () => {
      this.setConnectionStatus('connected')
      this.reconnectAttempts = 0
      this.startHeartbeat()
      this.emit('connect')
    }

    this.ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onclose = (event) => {
      this.clearTimers()
      
      if (!this.isManualClose) {
        this.setConnectionStatus('disconnected')
        this.emit('disconnect', event)
        this.attemptReconnect()
      }
    }

    this.ws.onerror = (error) => {
      this.setConnectionStatus('error')
      this.emit('error', new NetworkError('WebSocket连接错误'))
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WSMessage): void {
    switch (message.type) {
      case 'chat_message':
        this.emit('message', message.payload as Message)
        break
      case 'query_response':
        this.emit('query_response', message.payload)
        break
      case 'typing':
        this.emit('typing', message.payload)
        break
      case 'error':
        this.emit('error', new NetworkError(message.payload.message))
        break
      case 'pong':
        // 心跳响应，不需要处理
        break
      default:
        console.warn('Unknown message type:', message.type)
    }
  }

  /**
   * 尝试重连
   */
  private attemptReconnect(): void {
    if (this.isManualClose || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return
    }

    this.reconnectAttempts++
    this.setConnectionStatus('reconnecting')
    
    this.reconnectTimer = window.setTimeout(() => {
      this.emit('reconnect', this.reconnectAttempts)
      this.connect(this.chatId || undefined)
    }, this.reconnectInterval)
  }

  /**
   * 开始心跳
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.sendMessage({ type: 'ping', payload: {} })
      }
    }, 30000) // 30秒心跳
  }

  /**
   * 清除定时器
   */
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 设置连接状态
   */
  private setConnectionStatus(status: ConnectionStatus): void {
    this.connectionStatus = status
    this.emit('status_change', status)
  }

  /**
   * 生成请求ID
   */
  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }
}
