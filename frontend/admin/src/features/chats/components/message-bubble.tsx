import { ChatMessage } from '@/services/types'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface MessageBubbleProps {
  message: ChatMessage
  showSender?: boolean
  isConsecutive?: boolean
}

export function MessageBubble({ 
  message, 
  showSender = true, 
  isConsecutive = false 
}: MessageBubbleProps) {
  const isAdmin = message.sender_type === 'official'
  const isSystem = message.message_type === 'SYSTEM'
  const isUser = message.sender_type === 'third_party'

  const getSenderColor = (senderType: 'official' | 'third_party') => {
    switch (senderType) {
      case 'official':
        return 'bg-blue-500'
      case 'third_party':
        return 'bg-green-500'
      default:
        return 'bg-gray-400'
    }
  }

  const getSenderLabel = (senderType: 'official' | 'third_party', messageType: string) => {
    if (messageType === 'SYSTEM') return '系统'
    switch (senderType) {
      case 'official':
        return '管理员'
      case 'third_party':
        return '用户'
      default:
        return '未知'
    }
  }

  const formatTime = (dateString: string) => {
    return format(new Date(dateString), 'HH:mm', { locale: zhCN })
  }

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'yyyy年MM月dd日', { locale: zhCN })
  }

  // 系统消息特殊处理
  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <div className="bg-muted text-muted-foreground px-3 py-1 rounded-full text-xs">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className={cn(
      'flex gap-3 mb-4',
      isAdmin && 'flex-row-reverse',
      isConsecutive && 'mb-1'
    )}>
      {/* 头像 */}
      {showSender && !isConsecutive && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className={cn('text-white text-xs', getSenderColor(message.sender_type))}>
            {isAdmin ? '管' : (message.sender_email ? message.sender_email.charAt(0).toUpperCase() : 'U')}
          </AvatarFallback>
        </Avatar>
      )}
      
      {/* 占位符，保持对齐 */}
      {(!showSender || isConsecutive) && (
        <div className="h-8 w-8 flex-shrink-0" />
      )}

      <div className={cn(
        'flex flex-col max-w-[70%]',
        isAdmin && 'items-end'
      )}>
        {/* 发送者信息 */}
        {showSender && !isConsecutive && (
          <div className={cn(
            'flex items-center gap-2 mb-1',
            isAdmin && 'flex-row-reverse'
          )}>
            <Badge variant="outline" className="text-xs">
              {getSenderLabel(message.sender_type, message.message_type)}
            </Badge>
            {message.sender_email && (
              <span className="text-xs text-muted-foreground">
                {message.sender_email}
              </span>
            )}
          </div>
        )}

        {/* 消息内容 */}
        <div className={cn(
          'px-4 py-2 rounded-lg break-words',
          isAdmin 
            ? 'bg-primary text-primary-foreground rounded-br-sm' 
            : 'bg-muted rounded-bl-sm',
          isConsecutive && (isAdmin ? 'rounded-br-lg' : 'rounded-bl-lg')
        )}>
          <div className="text-sm whitespace-pre-wrap">
            {message.content}
          </div>
          
          {/* 消息元数据 */}
          {message.metadata && Object.keys(message.metadata).length > 0 && (
            <div className="mt-2 pt-2 border-t border-current/20">
              <details className="text-xs opacity-70">
                <summary className="cursor-pointer">元数据</summary>
                <pre className="mt-1 text-xs">
                  {JSON.stringify(message.metadata, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>

        {/* 时间戳 */}
        <div className={cn(
          'text-xs text-muted-foreground mt-1 px-1',
          isAdmin && 'text-right'
        )}>
          {formatTime(message.created_at)}
        </div>
      </div>
    </div>
  )
}