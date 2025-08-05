import { useEffect, useRef, useState } from 'react'
import { ChatMessage } from '@/services/types'
import { MessageBubble } from './message-bubble'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { ChevronDown, Loader2 } from 'lucide-react'
import { format, isSameDay } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface MessageListProps {
  messages: ChatMessage[]
  loading?: boolean
  onLoadMore?: () => void
  hasMore?: boolean
  autoScroll?: boolean
}

export function MessageList({ 
  messages, 
  loading = false, 
  onLoadMore,
  hasMore = false,
  autoScroll = true 
}: MessageListProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)
  const [isUserScrolling, setIsUserScrolling] = useState(false)

  // 按日期分组消息
  const groupedMessages = messages.reduce((groups, message) => {
    const date = format(new Date(message.created_at), 'yyyy-MM-dd')
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(message)
    return groups
  }, {} as Record<string, ChatMessage[]>)

  // 检查是否为连续消息（同一发送者，时间间隔小于5分钟）
  const isConsecutiveMessage = (current: ChatMessage, previous: ChatMessage | undefined): boolean => {
    if (!previous) return false
    
    const timeDiff = new Date(current.created_at).getTime() - new Date(previous.created_at).getTime()
    const fiveMinutes = 5 * 60 * 1000
    
    return (
      current.sender_type === previous.sender_type &&
      current.sender_id === previous.sender_id &&
      timeDiff < fiveMinutes
    )
  }

  // 自动滚动到底部
  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }

  // 检查是否滚动到底部
  const checkScrollPosition = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        const { scrollTop, scrollHeight, clientHeight } = scrollContainer
        const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
        setShowScrollButton(!isAtBottom)
        setIsUserScrolling(!isAtBottom)
      }
    }
  }

  // 处理滚动事件
  const handleScroll = () => {
    checkScrollPosition()
  }

  // 新消息时自动滚动
  useEffect(() => {
    if (autoScroll && !isUserScrolling) {
      scrollToBottom()
    }
  }, [messages, autoScroll, isUserScrolling])

  // 初始化时滚动到底部
  useEffect(() => {
    scrollToBottom()
  }, [])

  const formatDateHeader = (dateString: string) => {
    const date = new Date(dateString)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (isSameDay(date, today)) {
      return '今天'
    } else if (isSameDay(date, yesterday)) {
      return '昨天'
    } else {
      return format(date, 'yyyy年MM月dd日', { locale: zhCN })
    }
  }

  if (messages.length === 0 && !loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="text-lg mb-2">暂无消息</div>
          <div className="text-sm">开始对话吧！</div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 relative">
      <ScrollArea 
        ref={scrollAreaRef} 
        className="h-full"
        onScrollCapture={handleScroll}
      >
        <div className="p-4 space-y-4">
          {/* 加载更多按钮 */}
          {hasMore && (
            <div className="flex justify-center">
              <Button
                variant="outline"
                size="sm"
                onClick={onLoadMore}
                disabled={loading}
                className="text-xs"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                    加载中...
                  </>
                ) : (
                  '加载更多消息'
                )}
              </Button>
            </div>
          )}

          {/* 消息列表 */}
          {Object.entries(groupedMessages).map(([date, dayMessages]) => (
            <div key={date}>
              {/* 日期分隔符 */}
              <div className="flex justify-center my-6">
                <div className="bg-muted text-muted-foreground px-3 py-1 rounded-full text-xs">
                  {formatDateHeader(date)}
                </div>
              </div>

              {/* 该日期的消息 */}
              {dayMessages.map((message, index) => {
                const previousMessage = index > 0 ? dayMessages[index - 1] : undefined
                const isConsecutive = isConsecutiveMessage(message, previousMessage)
                
                return (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    showSender={!isConsecutive}
                    isConsecutive={isConsecutive}
                  />
                )
              })}
            </div>
          ))}

          {/* 加载指示器 */}
          {loading && messages.length === 0 && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          )}
        </div>
      </ScrollArea>

      {/* 滚动到底部按钮 */}
      {showScrollButton && (
        <Button
          size="sm"
          className="absolute bottom-4 right-4 rounded-full shadow-lg"
          onClick={scrollToBottom}
        >
          <ChevronDown className="h-4 w-4" />
        </Button>
      )}
    </div>
  )
}