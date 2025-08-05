import { useCallback, useEffect, useRef, useState } from 'react'
import { adminService } from '@/services/admin'
import { useAuth } from '@/stores/authStore'
import { toast } from '@/hooks/use-toast'
import {
  ChatMessage,
  WebSocketMessage,
  MessageNewEvent,
  TypingUpdateEvent,
  SystemNotificationEvent,
  ErrorResponse,
  HistoryResponse,
} from '@/services/types'

interface UseChatWebSocketProps {
  chatId: number // 修正为数字类型
  onMessage?: (message: ChatMessage) => void
  onTyping?: (data: { user_id: number; client_id: string; user_type: 'official' | 'third_party'; is_typing: boolean }) => void
  onSystemNotification?: (data: { level: 'info' | 'warning' | 'error'; content: string }) => void
  onError?: (error: Error) => void
  autoReconnect?: boolean
  maxReconnectAttempts?: number
}

interface WebSocketState {
  connected: boolean
  connecting: boolean
  reconnecting: boolean
  error: Error | null
  reconnectAttempts: number
}

export function useChatWebSocket({
  chatId,
  onMessage,
  onTyping,
  onSystemNotification,
  onError,
  autoReconnect = true,
  maxReconnectAttempts = 5,
}: UseChatWebSocketProps) {
  const { user } = useAuth()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const clientIdRef = useRef<string>(`admin-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`)

  const [state, setState] = useState<WebSocketState>({
    connected: false,
    connecting: false,
    reconnecting: false,
    error: null,
    reconnectAttempts: 0,
  })

  // 计算重连延迟（指数退避）
  const getReconnectDelay = useCallback((attempt: number): number => {
    return Math.min(1000 * Math.pow(2, attempt), 30000) // 最大30秒
  }, [])

  // 解析WebSocket消息
  const parseMessage = useCallback((data: string): WebSocketMessage | null => {
    try {
      return JSON.parse(data) as WebSocketMessage
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Failed to parse WebSocket message:', error)
      return null
    }
  }, [])

  // 处理WebSocket消息 (基于实际协议 V2)
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      const message = parseMessage(event.data)
      if (!message) return

      switch (message.type) {
        case 'message.new': {
          const messageEvent = message as MessageNewEvent
          // 转换为ChatMessage格式
          const chatMessage: ChatMessage = {
            id: messageEvent.payload.message.id,
            chat_id: messageEvent.payload.message.chat_id,
            sender_type: messageEvent.payload.message.sender_type,
            sender_id: messageEvent.payload.message.sender_id,
            content: messageEvent.payload.message.content,
            message_type: messageEvent.payload.message.message_type,
            created_at: messageEvent.payload.message.created_at,
            metadata: messageEvent.payload.message.metadata,
          }
          onMessage?.(chatMessage)
          break
        }
        case 'typing.update': {
          const typingEvent = message as TypingUpdateEvent
          onTyping?.({
            user_id: typingEvent.payload.sender.user_id,
            client_id: typingEvent.payload.sender.client_id,
            user_type: typingEvent.payload.sender.user_type,
            is_typing: typingEvent.payload.is_typing,
          })
          break
        }
        case 'notification.system': {
          const notificationEvent = message as SystemNotificationEvent
          onSystemNotification?.(notificationEvent.payload)
          break
        }
        case 'response.error': {
          const errorEvent = message as ErrorResponse
          const error = new Error(`${errorEvent.payload.code}: ${errorEvent.payload.message}`)
          setState(prev => ({ ...prev, error }))
          onError?.(error)
          break
        }
        case 'history.response': {
          // 处理历史消息响应
          const historyEvent = message as HistoryResponse
          const messages = historyEvent.payload.messages.map(msg => ({
            id: msg.id,
            chat_id: msg.chat_id,
            sender_type: msg.sender_type,
            sender_id: msg.sender_id,
            content: msg.content,
            message_type: msg.message_type,
            created_at: msg.created_at,
            metadata: msg.metadata,
          }))
          // 可以通过回调或事件发送历史消息
          messages.forEach(msg => onMessage?.(msg))
          break
        }
        default:
          // eslint-disable-next-line no-console
          console.warn('Unknown WebSocket message type:', message.type)
      }
    },
    [onMessage, onTyping, onSystemNotification, onError, parseMessage]
  )

  // 连接WebSocket
  const connect = useCallback(() => {
    if (!user?.id || !chatId) return

    setState(prev => ({ ...prev, connecting: true, error: null }))

    try {
      const ws = adminService.createChatWebSocket(
        chatId,
        user.id,
        clientIdRef.current
      )

      ws.onopen = () => {
        setState(prev => ({
          ...prev,
          connected: true,
          connecting: false,
          reconnecting: false,
          reconnectAttempts: 0,
          error: null,
        }))

        toast({
          title: '聊天连接成功',
          description: '实时聊天功能已启用',
        })
      }

      ws.onmessage = handleMessage

      ws.onerror = (error) => {
        const wsError = new Error('WebSocket connection error')
        setState(prev => ({ ...prev, error: wsError, connecting: false }))
        onError?.(wsError)
      }

      ws.onclose = (event) => {
        setState(prev => ({ ...prev, connected: false, connecting: false }))

        if (event.code !== 1000 && autoReconnect && state.reconnectAttempts < maxReconnectAttempts) {
          // 非正常关闭且允许重连
          const delay = getReconnectDelay(state.reconnectAttempts)
          setState(prev => ({
            ...prev,
            reconnecting: true,
            reconnectAttempts: prev.reconnectAttempts + 1,
          }))

          toast({
            title: '连接断开',
            description: `正在尝试重连... (${state.reconnectAttempts + 1}/${maxReconnectAttempts})`,
            variant: 'destructive',
          })

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else if (state.reconnectAttempts >= maxReconnectAttempts) {
          setState(prev => ({ ...prev, reconnecting: false }))
          toast({
            title: '连接失败',
            description: '无法连接到聊天服务器，请刷新页面重试',
            variant: 'destructive',
          })
        }
      }

      wsRef.current = ws
    } catch (error) {
      const connectError = error instanceof Error ? error : new Error('Failed to create WebSocket connection')
      setState(prev => ({ ...prev, error: connectError, connecting: false }))
      onError?.(connectError)
    }
  }, [user?.id, chatId, handleMessage, onError, autoReconnect, maxReconnectAttempts, getReconnectDelay, state.reconnectAttempts])

  // 断开连接
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }

    setState({
      connected: false,
      connecting: false,
      reconnecting: false,
      error: null,
      reconnectAttempts: 0,
    })
  }, [])

  // 发送消息
  const sendMessage = useCallback((message: object) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected')
    }

    try {
      wsRef.current.send(JSON.stringify(message))
    } catch (error) {
      const sendError = error instanceof Error ? error : new Error('Failed to send message')
      onError?.(sendError)
      throw sendError
    }
  }, [onError])

  // 发送打字指示器 (基于协议 V2)
  const sendTypingIndicator = useCallback((isTyping: boolean) => {
    try {
      const messageType = isTyping ? 'typing.start' : 'typing.stop'
      sendMessage({
        type: messageType,
        payload: { is_typing: isTyping },
        request_id: `typing-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      })
    } catch (error) {
      // 打字指示器发送失败不需要显示错误
      // eslint-disable-next-line no-console
      console.warn('Failed to send typing indicator:', error)
    }
  }, [sendMessage])

  // 发送聊天消息 (基于协议 V2)
  const sendChatMessage = useCallback((content: string, messageType = 'TEXT', metadata?: Record<string, unknown>) => {
    try {
      sendMessage({
        type: 'message.create',
        payload: {
          content,
          message_type: messageType,
          metadata,
        },
        request_id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      })
    } catch (error) {
      const sendError = error instanceof Error ? error : new Error('Failed to send message')
      onError?.(sendError)
      throw sendError
    }
  }, [sendMessage, onError])

  // 请求历史消息 (基于协议 V2)
  const requestHistory = useCallback((beforeMessageId?: number, limit = 20) => {
    try {
      sendMessage({
        type: 'history.request',
        payload: {
          before_message_id: beforeMessageId,
          limit,
        },
        request_id: `hist-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      })
    } catch (error) {
      const historyError = error instanceof Error ? error : new Error('Failed to request history')
      onError?.(historyError)
      throw historyError
    }
  }, [sendMessage, onError])

  // 手动重连
  const reconnect = useCallback(() => {
    disconnect()
    setState(prev => ({ ...prev, reconnectAttempts: 0 }))
    connect()
  }, [disconnect, connect])

  // 组件挂载时连接
  useEffect(() => {
    if (user?.id && chatId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [user?.id, chatId]) // 只在用户ID或聊天ID变化时重连

  // 清理定时器
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  return {
    // 状态
    connected: state.connected,
    connecting: state.connecting,
    reconnecting: state.reconnecting,
    error: state.error,
    reconnectAttempts: state.reconnectAttempts,
    
    // 方法
    connect,
    disconnect,
    reconnect,
    sendMessage,
    sendTypingIndicator,
    sendChatMessage,
    requestHistory,
    
    // WebSocket实例（用于高级用法）
    websocket: wsRef.current,
  }
}