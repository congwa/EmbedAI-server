import React, { useState, useRef, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Send, Loader2, Paperclip, Smile } from 'lucide-react'
// 移除MessageType导入，使用字符串
import { cn } from '@/lib/utils'

interface MessageInputProps {
  onSendMessage: (content: string, messageType?: string) => void
  disabled?: boolean
  loading?: boolean
  placeholder?: string
  onTyping?: (isTyping: boolean) => void
}

export function MessageInput({
  onSendMessage,
  disabled = false,
  loading = false,
  placeholder = '输入消息...',
  onTyping,
}: MessageInputProps) {
  const [message, setMessage] = useState('')
  const [isComposing, setIsComposing] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout>()

  // 处理输入变化
  const handleInputChange = useCallback((value: string) => {
    setMessage(value)
    
    // 处理打字指示器
    if (onTyping) {
      onTyping(true)
      
      // 清除之前的定时器
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
      
      // 设置新的定时器，1秒后停止打字指示
      typingTimeoutRef.current = setTimeout(() => {
        onTyping(false)
      }, 1000)
    }
  }, [onTyping])

  // 发送消息
  const handleSendMessage = useCallback(() => {
    const trimmedMessage = message.trim()
    if (!trimmedMessage || disabled || loading) return

    onSendMessage(trimmedMessage, 'TEXT')
    setMessage('')
    
    // 停止打字指示器
    if (onTyping) {
      onTyping(false)
    }
    
    // 清除定时器
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current)
    }

    // 重新聚焦输入框
    setTimeout(() => {
      textareaRef.current?.focus()
    }, 0)
  }, [message, disabled, loading, onSendMessage, onTyping])

  // 处理键盘事件
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault()
      handleSendMessage()
    }
  }, [handleSendMessage, isComposing])

  // 处理输入法组合事件
  const handleCompositionStart = () => {
    setIsComposing(true)
  }

  const handleCompositionEnd = () => {
    setIsComposing(false)
  }

  // 自动调整文本框高度
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      const scrollHeight = textarea.scrollHeight
      const maxHeight = 120 // 最大高度约5行
      textarea.style.height = `${Math.min(scrollHeight, maxHeight)}px`
    }
  }, [])

  // 监听消息变化，调整高度
  React.useEffect(() => {
    adjustTextareaHeight()
  }, [message, adjustTextareaHeight])

  const canSend = message.trim().length > 0 && !disabled && !loading

  return (
    <div className="border-t bg-background p-4">
      <div className="flex items-end gap-2">
        {/* 附件按钮 */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={disabled}
          className="flex-shrink-0"
        >
          <Paperclip className="h-4 w-4" />
        </Button>

        {/* 表情按钮 */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={disabled}
          className="flex-shrink-0"
        >
          <Smile className="h-4 w-4" />
        </Button>

        {/* 消息输入框 */}
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onCompositionStart={handleCompositionStart}
            onCompositionEnd={handleCompositionEnd}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              'min-h-[40px] max-h-[120px] resize-none pr-12',
              'focus-visible:ring-1 focus-visible:ring-ring'
            )}
            style={{ height: '40px' }}
          />
          
          {/* 字符计数 */}
          {message.length > 0 && (
            <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
              {message.length}
            </div>
          )}
        </div>

        {/* 发送按钮 */}
        <Button
          onClick={handleSendMessage}
          disabled={!canSend}
          size="sm"
          className="flex-shrink-0"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* 提示文本 */}
      <div className="mt-2 text-xs text-muted-foreground">
        按 Enter 发送，Shift + Enter 换行
      </div>
    </div>
  )
}

// 清理定时器
React.useEffect(() => {
  return () => {
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current)
    }
  }
}, [])