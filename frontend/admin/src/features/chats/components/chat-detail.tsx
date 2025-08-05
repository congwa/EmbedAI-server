import { useState, useCallback } from 'react'
import { Chat } from '@/services/types'
import {
  ArrowLeft,
  MoreVertical,
  UserCheck,
  UserX,
  Settings,
  Wifi,
  WifiOff,
  Users,
  MessageSquare,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useChat } from '@/hooks/use-chat'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MessageInput } from './message-input'
import { MessageList } from './message-list'

interface ChatDetailProps {
  chat: Chat
  onBack?: () => void
  className?: string
}

export function ChatDetail({ chat, onBack, className }: ChatDetailProps) {
  const [showJoinDialog, setShowJoinDialog] = useState(false)
  const [showLeaveDialog, setShowLeaveDialog] = useState(false)

  // 使用聊天hook
  const {
    messages,
    connected,
    connecting,
    connectionError,
    sendMessage,
    sendTypingIndicator,
    joinChat,
    leaveChat,
    switchMode,
    sendingMessage,
    joiningChat,
    leavingChat,
    // switchingMode, // 暂时未使用
    loadingMessages,
  } = useChat({
    chatId: chat.id,
    autoConnect: true,
  })

  // 发送消息
  const handleSendMessage = useCallback(
    (content: string, messageType?: string) => {
      sendMessage(content, messageType)
    },
    [sendMessage]
  )

  // 处理打字指示器
  const handleTyping = useCallback(
    (isTyping: boolean) => {
      sendTypingIndicator(isTyping)
    },
    [sendTypingIndicator]
  )

  // 加入聊天
  const handleJoinChat = useCallback(() => {
    joinChat()
    setShowJoinDialog(false)
  }, [joinChat])

  // 离开聊天
  const handleLeaveChat = useCallback(() => {
    leaveChat()
    setShowLeaveDialog(false)
  }, [leaveChat])

  // 切换模式
  const handleSwitchMode = useCallback(
    (mode: string) => {
      switchMode(mode)
    },
    [switchMode]
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success'
      case 'inactive':
        return 'secondary'
      case 'archived':
        return 'outline'
      default:
        return 'default'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '活跃'
      case 'inactive':
        return '非活跃'
      case 'archived':
        return '已归档'
      default:
        return '未知'
    }
  }

  return (
    <Card className={cn('flex h-full flex-col', className)}>
      {/* 聊天头部 */}
      <CardHeader className='flex-shrink-0 pb-3'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center gap-3'>
            {/* 返回按钮 */}
            {onBack && (
              <Button
                variant='ghost'
                size='sm'
                onClick={onBack}
                className='p-2'
              >
                <ArrowLeft className='h-4 w-4' />
              </Button>
            )}

            {/* 用户信息 */}
            <div className='flex items-center gap-3'>
              <Avatar className='h-10 w-10'>
                <AvatarFallback className='bg-green-500 text-white'>
                  {chat.user_email
                    ? chat.user_email.charAt(0).toUpperCase()
                    : chat.third_party_user_id.toString().charAt(0)}
                </AvatarFallback>
              </Avatar>

              <div>
                <div className='flex items-center gap-2'>
                  <h3 className='font-semibold'>
                    {chat.user_email || `用户 ${chat.third_party_user_id}`}
                  </h3>
                  <Badge variant={getStatusColor(chat.status)}>
                    {getStatusText(chat.status)}
                  </Badge>
                </div>
                <div className='text-sm text-muted-foreground'>
                  {chat.knowledge_base_name || `知识库 ${chat.kb_id}`}
                </div>
              </div>
            </div>
          </div>

          {/* 连接状态和操作 */}
          <div className='flex items-center gap-2'>
            {/* 连接状态指示器 */}
            <div className='flex items-center gap-1'>
              {connected ? (
                <Wifi className='h-4 w-4 text-green-500' />
              ) : connecting ? (
                <WifiOff className='h-4 w-4 animate-pulse text-yellow-500' />
              ) : (
                <WifiOff className='h-4 w-4 text-red-500' />
              )}
              <span className='text-xs text-muted-foreground'>
                {connected ? '已连接' : connecting ? '连接中' : '未连接'}
              </span>
            </div>

            {/* 操作菜单 */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant='ghost' size='sm' className='p-2'>
                  <MoreVertical className='h-4 w-4' />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align='end'>
                <DropdownMenuItem onClick={() => setShowJoinDialog(true)}>
                  <UserCheck className='mr-2 h-4 w-4' />
                  加入聊天
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowLeaveDialog(true)}>
                  <UserX className='mr-2 h-4 w-4' />
                  离开聊天
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleSwitchMode('auto')}>
                  <Settings className='mr-2 h-4 w-4' />
                  切换到自动模式
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleSwitchMode('manual')}>
                  <Settings className='mr-2 h-4 w-4' />
                  切换到手动模式
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* 聊天统计信息 */}
        <div className='flex items-center gap-4 text-sm text-muted-foreground'>
          <div className='flex items-center gap-1'>
            <MessageSquare className='h-4 w-4' />
            <span>{chat.message_count || 0} 条消息</span>
          </div>
          <div className='flex items-center gap-1'>
            <Users className='h-4 w-4' />
            <span>聊天ID: {chat.id}</span>
          </div>
        </div>

        {/* 连接错误提示 */}
        {connectionError && (
          <div className='rounded bg-destructive/10 p-2 text-sm text-destructive'>
            连接错误: {connectionError.message}
          </div>
        )}
      </CardHeader>

      {/* 消息列表 */}
      <CardContent className='flex flex-1 flex-col overflow-hidden p-0'>
        <MessageList
          messages={messages}
          loading={loadingMessages}
          autoScroll={true}
        />

        {/* 消息输入 */}
        <MessageInput
          onSendMessage={handleSendMessage}
          onTyping={handleTyping}
          disabled={!connected}
          loading={sendingMessage}
          placeholder={connected ? '输入消息...' : '连接中，请稍候...'}
        />
      </CardContent>

      {/* 加入聊天确认对话框 */}
      <AlertDialog open={showJoinDialog} onOpenChange={setShowJoinDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>加入聊天</AlertDialogTitle>
            <AlertDialogDescription>
              您确定要加入这个聊天对话吗？加入后您将能够参与实时对话。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleJoinChat} disabled={joiningChat}>
              {joiningChat ? '加入中...' : '确认加入'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 离开聊天确认对话框 */}
      <AlertDialog open={showLeaveDialog} onOpenChange={setShowLeaveDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>离开聊天</AlertDialogTitle>
            <AlertDialogDescription>
              您确定要离开这个聊天对话吗？离开后您将无法接收新消息。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleLeaveChat} disabled={leavingChat}>
              {leavingChat ? '离开中...' : '确认离开'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  )
}
