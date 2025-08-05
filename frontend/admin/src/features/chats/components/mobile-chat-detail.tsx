import React, { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { Chat, ChatMessage } from '@/services/types'
import { useChatWebSocket } from '@/hooks/use-chat-websocket'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { 
  ArrowLeft, 
  Send, 
  Users, 
  Settings, 
  MessageSquare,
  Clock,
  User,
  Bot,
  MoreVertical,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { cn } from '@/lib/utils'
import { useNotification } from '@/hooks/use-notification'

interface MobileChatDetailProps {
  chat: Chat
  onBack: () => void
  className?: string
}

export function MobileChatDetail({ chat, onBack, className }: MobileChatDetailProps) {
  const [message, setMessage] = useState('')
  const [isJoined, setIsJoined] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  const notification = useNotification()

  // WebSocket连接
  const { 
    isConnected, 
    messages: wsMessages, 
    sendMessage: wsSendMessage 
  } = useChatWebSocket(chat.id, isJoined)

  // 获取聊天消息
  const { data: messagesData, isLoading } = useQuery({
    queryKey: ['chat-messages', chat.id],
    queryFn: () => adminService.getChatMessages(chat.id),
  })

  const messages = messagesData?.data || []
  const allMessages = [...messages, ...wsMessages]

  // 发送消息
  const sendMessageMutation = useMutation({
    mutationFn: (content: string) => 
      adminService.sendChatMessage(chat.id, { content, message_type: 'text' }),
    onSuccess: () => {
      setMessage('')
      queryClient.invalidateQueries({ queryKey: ['chat-messages', chat.id] })
    },
    onError: () => {
      notification.error('发送消息失败', '请稍后重试')
    },
  })

  // 加入聊天
  const joinChatMutation = useMutation({
    mutationFn: () => adminService.joinChat(chat.id),
    onSuccess: () => {
      setIsJoined(true)
      notification.success('已加入聊天', '您现在可以参与对话')
    },
    onError: () => {
      notification.error('加入聊天失败', '请稍后重试')
    },
  })

  // 离开聊天
  const leaveChatMutation = useMutation({
    mutationFn: () => adminService.leaveChat(chat.id),
    onSuccess: () => {
      setIsJoined(false)
      notification.success('已离开聊天')
    },
    onError: () => {
      notification.error('离开聊天失败', '请稍后重试')
    },
  })

  // 切换聊天模式
  const switchModeMutation = useMutation({
    mutationFn: (mode: string) => adminService.switchChatMode(chat.id, mode),
    onSuccess: () => {
      notification.success('聊天模式已切换')
      queryClient.invalidateQueries({ queryKey: ['chat-detail', chat.id] })
    },
    onError: () => {
      notification.error('切换模式失败', '请稍后重试')
    },
  })

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [allMessages])

  const handleSendMessage = () => {
    if (!message.trim()) return
    
    if (isJoined && isConnected) {
      wsSendMessage(message.trim())
    } else {
      sendMessageMutation.mutate(message.trim())
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatMessageTime = (timestamp: string) => {
    return formatDistanceToNow(new Date(timestamp), {
      addSuffix: true,
      locale: zhCN,
    })
  }

  const getMessageIcon = (messageType: string, isFromUser: boolean) => {
    if (isFromUser) {
      return <User className="h-4 w-4" />
    }
    return <Bot className="h-4 w-4" />
  }

  return (
    <div className={cn('flex flex-col h-full bg-background', className)}>
      {/* 头部 */}
      <div className="sticky top-0 z-10 bg-background border-b">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={onBack}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            
            <div className="min-w-0">
              <h1 className="font-semibold text-sm truncate">
                聊天 #{chat.id}
              </h1>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>用户 {chat.third_party_user_id}</span>
                {isConnected && (
                  <Badge variant="outline" className="h-4 px-1 text-xs">
                    在线
                  </Badge>
                )}
              </div>
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {isJoined ? (
                <DropdownMenuItem onClick={() => leaveChatMutation.mutate()}>
                  离开聊天
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem onClick={() => joinChatMutation.mutate()}>
                  加入聊天
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={() => switchModeMutation.mutate('assistant')}>
                切换到助手模式
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => switchModeMutation.mutate('knowledge_base')}>
                切换到知识库模式
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* 聊天信息 */}
        <div className="px-4 pb-3">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              <span>{allMessages.length} 条消息</span>
            </div>
            <div className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              <span>{chat.participants?.length || 0} 参与者</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{formatMessageTime(chat.created_at)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 消息列表 */}
      <ScrollArea className="flex-1 px-4">
        <div className="space-y-4 py-4">
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="flex gap-3">
                    <div className="h-8 w-8 bg-muted rounded-full"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-muted rounded w-1/4"></div>
                      <div className="h-16 bg-muted rounded"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : allMessages.length === 0 ? (
            <div className="text-center py-8">
              <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">暂无消息</p>
            </div>
          ) : (
            allMessages.map((msg, index) => {
              const isFromUser = msg.message_type === 'user' || msg.sender_type === 'user'
              return (
                <div key={index} className="flex gap-3">
                  <div className={cn(
                    'h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0',
                    isFromUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
                  )}>
                    {getMessageIcon(msg.message_type, isFromUser)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">
                        {isFromUser ? '用户' : '助手'}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatMessageTime(msg.created_at)}
                      </span>
                    </div>
                    
                    <Card>
                      <CardContent className="p-3">
                        <p className="text-sm whitespace-pre-wrap break-words">
                          {msg.content}
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )
            })
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* 消息输入 */}
      <div className="border-t bg-background p-4">
        <div className="flex gap-2">
          <Input
            placeholder="输入消息..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-1"
            disabled={!isJoined && !isConnected}
          />
          <Button
            size="sm"
            onClick={handleSendMessage}
            disabled={!message.trim() || sendMessageMutation.isPending}
            className="px-3"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        
        {!isJoined && (
          <p className="text-xs text-muted-foreground mt-2 text-center">
            需要加入聊天才能发送消息
          </p>
        )}
      </div>
    </div>
  )
}