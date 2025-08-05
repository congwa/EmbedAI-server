import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { useAuth } from '@/stores/authStore'
import { toast } from '@/hooks/use-toast'
import { Chat, ChatStatus, GetChatsQuery } from '@/services/types'
import { ChatSearch } from './chat-search'
import { ChatTable } from './chat-table'
import { ChatPagination } from './chat-pagination'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RefreshCw, MessageSquare } from 'lucide-react'

interface ChatListProps {
  onChatSelect?: (chat: Chat) => void
  showDeleted?: boolean
}

export function ChatList({ onChatSelect, showDeleted = false }: ChatListProps) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  
  // 分页和筛选状态
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchParams, setSearchParams] = useState<GetChatsQuery>({})

  // 构建查询参数
  const queryParams: GetChatsQuery = {
    skip: (currentPage - 1) * pageSize,
    limit: pageSize,
    ...searchParams,
  }

  // 获取聊天列表
  const { data: chatsData, isLoading, error, refetch } = useQuery({
    queryKey: ['chats', queryParams, showDeleted],
    queryFn: () => showDeleted 
      ? adminService.getDeletedChats(queryParams.skip, queryParams.limit)
      : adminService.getChats(queryParams),
    enabled: !!user,
    keepPreviousData: true,
  })

  // 加入聊天
  const joinChatMutation = useMutation({
    mutationFn: (chatId: number) => adminService.joinChat(chatId),
    onSuccess: () => {
      toast({
        title: '成功加入聊天',
        description: '您现在可以参与这个聊天对话',
      })
      refetch()
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
    mutationFn: (chatId: number) => adminService.leaveChat(chatId),
    onSuccess: () => {
      toast({
        title: '已离开聊天',
        description: '您已退出该聊天对话',
      })
      refetch()
    },
    onError: (error) => {
      toast({
        title: '离开聊天失败',
        description: error instanceof Error ? error.message : '请稍后重试',
        variant: 'destructive',
      })
    },
  })

  // 恢复聊天
  const restoreChatMutation = useMutation({
    mutationFn: (chatId: number) => adminService.restoreChat(chatId),
    onSuccess: () => {
      toast({
        title: '聊天已恢复',
        description: '该聊天对话已成功恢复',
      })
      refetch()
    },
    onError: (error) => {
      toast({
        title: '恢复聊天失败',
        description: error instanceof Error ? error.message : '请稍后重试',
        variant: 'destructive',
      })
    },
  })

  // 处理搜索
  const handleSearch = useCallback((params: GetChatsQuery) => {
    setSearchParams(params)
    setCurrentPage(1) // 重置到第一页
  }, [])

  // 重置搜索
  const handleReset = useCallback(() => {
    setSearchParams({})
    setCurrentPage(1)
  }, [])

  // 处理分页
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page)
  }, [])

  const handlePageSizeChange = useCallback((newPageSize: number) => {
    setPageSize(newPageSize)
    setCurrentPage(1) // 重置到第一页
  }, [])

  // 处理聊天操作
  const handleViewChat = useCallback((chat: Chat) => {
    onChatSelect?.(chat)
  }, [onChatSelect])

  const handleJoinChat = useCallback((chat: Chat) => {
    joinChatMutation.mutate(chat.id)
  }, [joinChatMutation])

  const handleLeaveChat = useCallback((chat: Chat) => {
    leaveChatMutation.mutate(chat.id)
  }, [leaveChatMutation])

  const handleRestoreChat = useCallback((chat: Chat) => {
    restoreChatMutation.mutate(chat.id)
  }, [restoreChatMutation])

  // 手动刷新
  const handleRefresh = useCallback(() => {
    refetch()
  }, [refetch])

  // 计算分页信息
  const chats = chatsData?.data?.items || []
  const totalItems = chatsData?.data?.pagination?.total || 0
  const totalPages = Math.ceil(totalItems / pageSize)

  if (error) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center h-64">
          <MessageSquare className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium mb-2">加载聊天列表失败</p>
          <p className="text-sm text-muted-foreground mb-4">
            {error instanceof Error ? error.message : '请检查网络连接后重试'}
          </p>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            重试
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              {showDeleted ? '已删除的聊天' : '聊天管理'}
            </CardTitle>
            <Button
              onClick={handleRefresh}
              variant="outline"
              size="sm"
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {!showDeleted && (
            <ChatSearch onSearch={handleSearch} onReset={handleReset} />
          )}
          
          <ChatTable
            data={chats}
            onViewChat={handleViewChat}
            onJoinChat={handleJoinChat}
            onLeaveChat={handleLeaveChat}
            onRestoreChat={handleRestoreChat}
            loading={isLoading}
          />
          
          {totalItems > 0 && (
            <ChatPagination
              currentPage={currentPage}
              totalPages={totalPages}
              pageSize={pageSize}
              totalItems={totalItems}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
              loading={isLoading}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}