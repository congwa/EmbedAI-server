import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { Chat } from '@/services/types'
import { MobileTable, MobileTableRow } from '@/components/ui/mobile-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  MessageSquare, 
  Users, 
  Clock, 
  Search,
  Filter,
  RotateCcw,
  Trash2,
  Eye,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { cn } from '@/lib/utils'

interface MobileChatListProps {
  onChatSelect: (chat: Chat) => void
  showDeleted?: boolean
  className?: string
}

export function MobileChatList({ 
  onChatSelect, 
  showDeleted = false,
  className 
}: MobileChatListProps) {
  const [searchTerm, setSearchTerm] = React.useState('')
  const [page, setPage] = React.useState(1)
  const pageSize = 20

  // 获取聊天列表
  const { data, isLoading, refetch } = useQuery({
    queryKey: showDeleted 
      ? ['deleted-chats', page, pageSize] 
      : ['chats', page, pageSize, searchTerm],
    queryFn: () => showDeleted 
      ? adminService.getDeletedChats((page - 1) * pageSize, pageSize)
      : adminService.getChats({
          skip: (page - 1) * pageSize,
          limit: pageSize,
          search: searchTerm || undefined,
        }),
  })

  const chats = data?.data?.items || []
  const total = data?.data?.total || 0

  const handleRestore = async (chatId: number) => {
    try {
      await adminService.restoreChat(chatId)
      refetch()
    } catch (error) {
      console.error('恢复聊天失败:', error)
    }
  }

  const formatChatStatus = (chat: Chat) => {
    if (chat.is_deleted) {
      return <Badge variant="destructive" className="text-xs">已删除</Badge>
    }
    
    if (chat.messages && chat.messages.length > 0) {
      const lastMessage = chat.messages[chat.messages.length - 1]
      const timeAgo = formatDistanceToNow(new Date(lastMessage.created_at), {
        addSuffix: true,
        locale: zhCN,
      })
      return <Badge variant="secondary" className="text-xs">{timeAgo}</Badge>
    }
    
    return <Badge variant="outline" className="text-xs">无消息</Badge>
  }

  const getChatActions = (chat: Chat) => {
    const actions = [
      {
        label: '查看详情',
        onClick: () => onChatSelect(chat),
        icon: Eye,
      },
    ]

    if (showDeleted) {
      actions.push({
        label: '恢复聊天',
        onClick: () => handleRestore(chat.id),
        icon: RotateCcw,
      })
    }

    return actions
  }

  const getChatDescription = (chat: Chat) => {
    if (chat.messages && chat.messages.length > 0) {
      const lastMessage = chat.messages[chat.messages.length - 1]
      return lastMessage.content.slice(0, 100) + (lastMessage.content.length > 100 ? '...' : '')
    }
    return '暂无消息'
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* 搜索和筛选 */}
      {!showDeleted && (
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索聊天..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button variant="outline" size="sm" className="px-3">
            <Filter className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* 统计信息 */}
      <div className="flex items-center justify-between text-sm text-muted-foreground px-1">
        <span>共 {total} 个聊天</span>
        {!showDeleted && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            className="h-auto p-1"
          >
            <RotateCcw className="h-3 w-3" />
          </Button>
        )}
      </div>

      {/* 聊天列表 */}
      <MobileTable
        data={chats}
        loading={isLoading}
        emptyMessage={showDeleted ? '暂无已删除的聊天' : '暂无聊天记录'}
        renderItem={(chat) => (
          <MobileTableRow
            title={`聊天 #${chat.id}`}
            subtitle={`用户: ${chat.third_party_user_id} | 知识库: ${chat.knowledge_base_id || '无'}`}
            description={getChatDescription(chat)}
            badge={formatChatStatus(chat)}
            status={
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <MessageSquare className="h-3 w-3" />
                  <span>{chat.messages?.length || 0} 条消息</span>
                </div>
                <div className="flex items-center gap-1">
                  <Users className="h-3 w-3" />
                  <span>{chat.participants?.length || 0} 参与者</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  <span>
                    {formatDistanceToNow(new Date(chat.created_at), {
                      addSuffix: true,
                      locale: zhCN,
                    })}
                  </span>
                </div>
              </div>
            }
            actions={getChatActions(chat)}
            onClick={() => onChatSelect(chat)}
          />
        )}
      />

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex items-center justify-between px-1">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            上一页
          </Button>
          
          <span className="text-sm text-muted-foreground">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          
          <Button
            variant="outline"
            size="sm"
            disabled={page >= Math.ceil(total / pageSize)}
            onClick={() => setPage(page + 1)}
          >
            下一页
          </Button>
        </div>
      )}
    </div>
  )
}