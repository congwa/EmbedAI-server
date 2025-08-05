import { useCallback, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { useChatWebSocket } from './use-chat-websocket'
import { toast } from '@/hooks/use-toast'
import { ChatMessage, ChatMessageCreate } from '@/services/types'

interface UseChatOptions {
  chatId: number // 修正为数字类型
  autoConnect?: boolean
  onNewMessage?: (message: ChatMessage) => void
  onTyping?: (data: { user_id: number; client_id: string; user_type: 'official' | 'third_party'; is_typing: boolean }) => void
  onError?: (error: Error) => void
}

/**
 * 聊天功能的综合hook
 * 集成了WebSocket连接、消息发送、消息历史等功能
 */
export function useChat({
  chatId,
  autoConnect = true,
  onNewMessage,
  onTyping,
  onError,
}: UseChatOptions) {
  const queryClient = useQueryClient()
  const [messages, setMessages] = useState<ChatMessage[]>([])

  // 处理新消息
  const handleNewMessage = useCallback((message: ChatMessage) => {
    setMessages(prev => [...prev, message])
    onNewMessage?.(message)
    
    // 更新React Query缓存
    queryClient.setQueryData(['chat-messages', chatId], (oldData: ChatMessage[] | undefined) => {
      return oldData ? [...oldData, message] : [message]
    })
  }, [chatId, onNewMessage, queryClient])

  // WebSocket连接
  const websocket = useChatWebSocket({
    chatId,
    onMessage: handleNewMessage,
    onTyping,
    onSystemNotification: (data) => {
      // 处理系统通知
      toast({
        title: data.level === 'error' ? '错误' : data.level === 'warning' ? '警告' : '信息',
        description: data.content,
        variant: data.level === 'error' ? 'destructive' : 'default',
      })
    },
    onError,
    autoReconnect: autoConnect,
  })

  // 获取聊天详情
  const { data: chatDetail, isLoading: loadingChatDetail } = useQuery({
    queryKey: ['chat-detail', chatId],
    queryFn: () => adminService.getChatDetail(chatId),
    enabled: !!chatId,
  })

  // 获取消息历史
  const { data: messageHistory, isLoading: loadingMessages } = useQuery({
    queryKey: ['chat-messages', chatId],
    queryFn: () => adminService.getChatMessages(chatId),
    enabled: !!chatId,
    onSuccess: (response) => {
      if (response.success) {
        setMessages(response.data)
      }
    },
  })

  // 发送消息
  const sendMessageMutation = useMutation({
    mutationFn: async (data: { content: string; messageType?: string }) => {
      const messageData: ChatMessageCreate = {
        content: data.content,
        message_type: data.messageType || 'TEXT',
      }
      return adminService.sendChatMessage(chatId, messageData)
    },
    onSuccess: (response) => {
      if (response.success) {
        // 消息已通过WebSocket接收，不需要手动添加
        toast({
          title: '消息发送成功',
        })
      }
    },
    onError: (error) => {
      toast({
        title: '消息发送失败',
        description: error instanceof Error ? error.message : '请稍后重试',
        variant: 'destructive',
      })
    },
  })

  // 加入聊天
  const joinChatMutation = useMutation({
    mutationFn: () => adminService.joinChat(chatId),
    onSuccess: () => {
      toast({
        title: '已加入聊天',
      })
      queryClient.invalidateQueries(['chat-detail', chatId])
    },
    onError: (error) => {
      toast({
        title: '加入聊天失败',
        description: error instanceof Error ? error.message : '请稍后重试',
        variant: 'destructive',
      })
    },
  })

  // 离开聊天
  const leaveChatMutation = useMutation({
    mutationFn: () => adminService.leaveChat(chatId),
    onSuccess: () => {
      toast({
        title: '已离开聊天',
      })
      queryClient.invalidateQueries(['chat-detail', chatId])
    },
    onError: (error) => {
      toast({
        title: '离开聊天失败',
        description: error instanceof Error ? error.message : '请稍后重试',
        variant: 'destructive',
      })
    },
  })

  // 切换聊天模式
  const switchModeMutation = useMutation({
    mutationFn: (mode: string) => adminService.switchChatMode(chatId, mode),
    onSuccess: () => {
      toast({
        title: '模式切换成功',
      })
      queryClient.invalidateQueries(['chat-detail', chatId])
    },
    onError: (error) => {
      toast({
        title: '模式切换失败',
        description: error instanceof Error ? error.message : '请稍后重试',
        variant: 'destructive',
      })
    },
  })

  // 发送消息的便捷方法
  const sendMessage = useCallback((content: string, messageType?: string) => {
    sendMessageMutation.mutate({ content, messageType })
  }, [sendMessageMutation])

  // 发送打字指示器
  const sendTypingIndicator = useCallback((isTyping: boolean) => {
    websocket.sendTypingIndicator(isTyping)
  }, [websocket])

  return {
    // 聊天数据
    chat: chatDetail?.data,
    messages,
    
    // 加载状态
    loadingChatDetail,
    loadingMessages,
    
    // WebSocket状态
    connected: websocket.connected,
    connecting: websocket.connecting,
    reconnecting: websocket.reconnecting,
    connectionError: websocket.error,
    
    // 操作方法
    sendMessage,
    sendTypingIndicator,
    joinChat: joinChatMutation.mutate,
    leaveChat: leaveChatMutation.mutate,
    switchMode: switchModeMutation.mutate,
    
    // WebSocket控制
    connect: websocket.connect,
    disconnect: websocket.disconnect,
    reconnect: websocket.reconnect,
    
    // 操作状态
    sendingMessage: sendMessageMutation.isPending,
    joiningChat: joinChatMutation.isPending,
    leavingChat: leaveChatMutation.isPending,
    switchingMode: switchModeMutation.isPending,
  }
}