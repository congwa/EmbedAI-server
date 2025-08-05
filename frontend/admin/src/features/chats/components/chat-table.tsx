import { MoreHorizontal, MessageCircle, UserCheck, UserX, RotateCcw, Eye } from 'lucide-react'
import { Chat, ChatStatus } from '@/services/types'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

interface ChatTableProps {
  data: Chat[]
  onViewChat: (chat: Chat) => void
  onJoinChat: (chat: Chat) => void
  onLeaveChat: (chat: Chat) => void
  onRestoreChat: (chat: Chat) => void
  loading?: boolean
}

export function ChatTable({
  data,
  onViewChat,
  onJoinChat,
  onLeaveChat,
  onRestoreChat,
  loading = false,
}: ChatTableProps) {
  const getStatusColor = (status: ChatStatus): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" => {
    switch (status) {
      case ChatStatus.ACTIVE:
        return 'success'
      case ChatStatus.INACTIVE:
        return 'secondary'
      case ChatStatus.ARCHIVED:
        return 'outline'
      default:
        return 'default'
    }
  }

  const getStatusText = (status: ChatStatus): string => {
    switch (status) {
      case ChatStatus.ACTIVE:
        return '活跃'
      case ChatStatus.INACTIVE:
        return '非活跃'
      case ChatStatus.ARCHIVED:
        return '已归档'
      default:
        return '未知'
    }
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getTimeAgo = (dateString: string): string => {
    const now = new Date()
    const date = new Date(dateString)
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return '刚刚'
    if (diffInMinutes < 60) return `${diffInMinutes}分钟前`
    
    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `${diffInHours}小时前`
    
    const diffInDays = Math.floor(diffInHours / 24)
    if (diffInDays < 7) return `${diffInDays}天前`
    
    return formatDate(dateString)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>用户</TableHead>
          <TableHead>聊天ID</TableHead>
          <TableHead>知识库</TableHead>
          <TableHead>状态</TableHead>
          <TableHead>消息数</TableHead>
          <TableHead>最后活动</TableHead>
          <TableHead>创建时间</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={8} className="h-24 text-center">
              <div className="flex flex-col items-center justify-center text-sm text-muted-foreground">
                <MessageCircle className="h-8 w-8 mb-2 opacity-50" />
                <p>暂无聊天记录</p>
                <p>用户开始聊天后，记录将显示在这里</p>
              </div>
            </TableCell>
          </TableRow>
        ) : (
          data.map((chat) => (
            <TableRow key={chat.id} className="hover:bg-muted/50">
              <TableCell>
                <div className="flex items-center space-x-3">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="text-xs">
                      {chat.user_email ? chat.user_email.charAt(0).toUpperCase() : chat.third_party_user_id.toString().charAt(0)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium text-sm">
                      {chat.user_email || `用户 ${chat.third_party_user_id}`}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      ID: {chat.third_party_user_id}
                    </div>
                  </div>
                </div>
              </TableCell>
              <TableCell>
                <code className="text-xs bg-muted px-2 py-1 rounded">
                  {chat.id}
                </code>
              </TableCell>
              <TableCell>
                <div>
                  <div className="font-medium text-sm">
                    {chat.knowledge_base_name || `知识库 ${chat.kb_id}`}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    ID: {chat.kb_id}
                  </div>
                </div>
              </TableCell>
              <TableCell>
                <Badge variant={getStatusColor(chat.status)}>
                  {getStatusText(chat.status)}
                </Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center space-x-1">
                  <MessageCircle className="h-4 w-4 text-muted-foreground" />
                  <span>{chat.message_count || 0}</span>
                </div>
              </TableCell>
              <TableCell>
                <div className="text-sm">
                  {chat.last_message_at ? getTimeAgo(chat.last_message_at) : '无消息'}
                </div>
              </TableCell>
              <TableCell>
                <div className="text-sm text-muted-foreground">
                  {formatDate(chat.created_at)}
                </div>
              </TableCell>
              <TableCell className="text-right">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="h-8 w-8 p-0">
                      <span className="sr-only">打开菜单</span>
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onViewChat(chat)}>
                      <Eye className="mr-2 h-4 w-4" />
                      查看聊天
                    </DropdownMenuItem>
                    
                    {chat.status === ChatStatus.ACTIVE && (
                      <>
                        <DropdownMenuItem onClick={() => onJoinChat(chat)}>
                          <UserCheck className="mr-2 h-4 w-4" />
                          加入聊天
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => onLeaveChat(chat)}>
                          <UserX className="mr-2 h-4 w-4" />
                          离开聊天
                        </DropdownMenuItem>
                      </>
                    )}
                    
                    {chat.status === ChatStatus.ARCHIVED && (
                      <DropdownMenuItem onClick={() => onRestoreChat(chat)}>
                        <RotateCcw className="mr-2 h-4 w-4" />
                        恢复聊天
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  )
}