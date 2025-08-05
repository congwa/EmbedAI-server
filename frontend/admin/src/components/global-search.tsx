import React, { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Search,
  MessageSquare,
  Users,
  BookOpen,
  FileText,
  Clock,
  TrendingUp,
  X,
  Loader2,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { cn } from '@/lib/utils'
import { useNavigate } from '@tanstack/react-router'

interface SearchResult {
  id: string
  type: 'chat' | 'user' | 'knowledge_base' | 'document'
  title: string
  subtitle?: string
  description?: string
  url: string
  relevance: number
  timestamp?: string
  metadata?: Record<string, any>
}

interface GlobalSearchProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function GlobalSearch({ open, onOpenChange }: GlobalSearchProps) {
  const [query, setQuery] = useState('')
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)

  // 搜索结果
  const { data: searchResults, isLoading } = useQuery({
    queryKey: ['global-search', query],
    queryFn: async () => {
      if (!query.trim()) return []
      
      // 并行搜索所有类型的数据
      const [chats, users, knowledgeBases, documents] = await Promise.allSettled([
        adminService.getChats({ search: query, limit: 5 }),
        adminService.getUsers(1, 5), // 这里需要添加搜索参数
        adminService.getKnowledgeBases({ search: query, limit: 5 }),
        adminService.getDocuments({ search: query, limit: 5 }),
      ])

      const results: SearchResult[] = []

      // 处理聊天结果
      if (chats.status === 'fulfilled' && chats.value.data?.items) {
        chats.value.data.items.forEach((chat: any) => {
          results.push({
            id: `chat-${chat.id}`,
            type: 'chat',
            title: `聊天 #${chat.id}`,
            subtitle: `用户 ${chat.third_party_user_id}`,
            description: chat.messages?.[0]?.content?.slice(0, 100) || '暂无消息',
            url: `/chats?id=${chat.id}`,
            relevance: 0.9,
            timestamp: chat.created_at,
            metadata: { messageCount: chat.messages?.length || 0 },
          })
        })
      }

      // 处理用户结果
      if (users.status === 'fulfilled' && users.value.data?.items) {
        users.value.data.items
          .filter((user: any) => 
            user.email.toLowerCase().includes(query.toLowerCase()) ||
            user.id.toString().includes(query)
          )
          .forEach((user: any) => {
            results.push({
              id: `user-${user.id}`,
              type: 'user',
              title: user.email,
              subtitle: `用户 ID: ${user.id}`,
              description: `${user.is_active ? '活跃' : '已禁用'} | ${user.is_admin ? '管理员' : '普通用户'}`,
              url: `/users?id=${user.id}`,
              relevance: 0.8,
              timestamp: user.created_at,
              metadata: { isActive: user.is_active, isAdmin: user.is_admin },
            })
          })
      }

      // 处理知识库结果
      if (knowledgeBases.status === 'fulfilled' && knowledgeBases.value.data?.items) {
        knowledgeBases.value.data.items.forEach((kb: any) => {
          results.push({
            id: `kb-${kb.id}`,
            type: 'knowledge_base',
            title: kb.name,
            subtitle: kb.description || '无描述',
            description: `${kb.document_count || 0} 个文档`,
            url: `/knowledge-bases?id=${kb.id}`,
            relevance: 0.85,
            timestamp: kb.updated_at,
            metadata: { documentCount: kb.document_count, status: kb.status },
          })
        })
      }

      // 处理文档结果
      if (documents.status === 'fulfilled' && documents.value.data?.items) {
        documents.value.data.items.forEach((doc: any) => {
          results.push({
            id: `doc-${doc.id}`,
            type: 'document',
            title: doc.filename,
            subtitle: `知识库: ${doc.knowledge_base_id}`,
            description: doc.content?.slice(0, 100) || '无内容预览',
            url: `/knowledge-bases/documents?id=${doc.id}`,
            relevance: 0.7,
            timestamp: doc.created_at,
            metadata: { size: doc.size, status: doc.status },
          })
        })
      }

      // 按相关性排序
      return results.sort((a, b) => b.relevance - a.relevance)
    },
    enabled: query.length > 0,
    staleTime: 30000, // 30秒缓存
  })

  // 键盘导航
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!open) return

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex(prev => 
            Math.min(prev + 1, (searchResults?.length || 0) - 1)
          )
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex(prev => Math.max(prev - 1, 0))
          break
        case 'Enter':
          e.preventDefault()
          if (searchResults?.[selectedIndex]) {
            handleResultClick(searchResults[selectedIndex])
          }
          break
        case 'Escape':
          onOpenChange(false)
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, searchResults, selectedIndex, onOpenChange])

  // 重置选中索引
  useEffect(() => {
    setSelectedIndex(0)
  }, [searchResults])

  // 聚焦输入框
  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus()
    }
  }, [open])

  const handleResultClick = (result: SearchResult) => {
    // 添加到搜索历史
    if (query.trim()) {
      const newHistory = [query, ...searchHistory.filter(h => h !== query)].slice(0, 10)
      setSearchHistory(newHistory)
      localStorage.setItem('search-history', JSON.stringify(newHistory))
    }

    // 导航到结果页面
    navigate({ to: result.url })
    onOpenChange(false)
    setQuery('')
  }

  const getResultIcon = (type: SearchResult['type']) => {
    switch (type) {
      case 'chat':
        return <MessageSquare className="h-4 w-4" />
      case 'user':
        return <Users className="h-4 w-4" />
      case 'knowledge_base':
        return <BookOpen className="h-4 w-4" />
      case 'document':
        return <FileText className="h-4 w-4" />
      default:
        return <Search className="h-4 w-4" />
    }
  }

  const getResultTypeName = (type: SearchResult['type']) => {
    switch (type) {
      case 'chat':
        return '聊天'
      case 'user':
        return '用户'
      case 'knowledge_base':
        return '知识库'
      case 'document':
        return '文档'
      default:
        return '未知'
    }
  }

  // 加载搜索历史
  useEffect(() => {
    const saved = localStorage.getItem('search-history')
    if (saved) {
      try {
        setSearchHistory(JSON.parse(saved))
      } catch (error) {
        console.error('Failed to load search history:', error)
      }
    }
  }, [])

  const clearHistory = () => {
    setSearchHistory([])
    localStorage.removeItem('search-history')
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            全局搜索
          </DialogTitle>
        </DialogHeader>

        <div className="p-6">
          {/* 搜索输入 */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              ref={inputRef}
              placeholder="搜索聊天、用户、知识库、文档..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-10 pr-10"
            />
            {query && (
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                onClick={() => setQuery('')}
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>

          {/* 搜索结果 */}
          <ScrollArea className="max-h-96">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span className="ml-2 text-sm text-muted-foreground">搜索中...</span>
              </div>
            ) : query && searchResults ? (
              searchResults.length > 0 ? (
                <div className="space-y-2">
                  {searchResults.map((result, index) => (
                    <Card
                      key={result.id}
                      className={cn(
                        'cursor-pointer transition-colors hover:bg-accent',
                        index === selectedIndex && 'bg-accent'
                      )}
                      onClick={() => handleResultClick(result)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 mt-1">
                            {getResultIcon(result.type)}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-medium text-sm truncate">
                                {result.title}
                              </h3>
                              <Badge variant="outline" className="text-xs">
                                {getResultTypeName(result.type)}
                              </Badge>
                            </div>
                            
                            {result.subtitle && (
                              <p className="text-xs text-muted-foreground mb-1">
                                {result.subtitle}
                              </p>
                            )}
                            
                            {result.description && (
                              <p className="text-xs text-muted-foreground line-clamp-2">
                                {result.description}
                              </p>
                            )}
                            
                            {result.timestamp && (
                              <div className="flex items-center gap-1 mt-2">
                                <Clock className="h-3 w-3 text-muted-foreground" />
                                <span className="text-xs text-muted-foreground">
                                  {formatDistanceToNow(new Date(result.timestamp), {
                                    addSuffix: true,
                                    locale: zhCN,
                                  })}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">未找到相关结果</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    尝试使用不同的关键词
                  </p>
                </div>
              )
            ) : (
              // 搜索历史和建议
              <div className="space-y-4">
                {searchHistory.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium">最近搜索</h4>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearHistory}
                        className="h-auto p-1 text-xs"
                      >
                        清除
                      </Button>
                    </div>
                    <div className="space-y-1">
                      {searchHistory.slice(0, 5).map((term, index) => (
                        <div
                          key={index}
                          className="flex items-center gap-2 p-2 rounded-md hover:bg-accent cursor-pointer"
                          onClick={() => setQuery(term)}
                        >
                          <Clock className="h-3 w-3 text-muted-foreground" />
                          <span className="text-sm">{term}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <h4 className="text-sm font-medium mb-2">搜索建议</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { label: '最近聊天', query: 'recent:chats' },
                      { label: '活跃用户', query: 'active:users' },
                      { label: '训练中的知识库', query: 'status:training' },
                      { label: '今日文档', query: 'today:documents' },
                    ].map((suggestion) => (
                      <Button
                        key={suggestion.query}
                        variant="outline"
                        size="sm"
                        className="justify-start h-auto p-2"
                        onClick={() => setQuery(suggestion.query)}
                      >
                        <TrendingUp className="h-3 w-3 mr-2" />
                        <span className="text-xs">{suggestion.label}</span>
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </ScrollArea>

          {/* 快捷键提示 */}
          <Separator className="my-4" />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-4">
              <span>↑↓ 导航</span>
              <span>Enter 选择</span>
              <span>Esc 关闭</span>
            </div>
            <div>
              {searchResults && searchResults.length > 0 && (
                <span>{searchResults.length} 个结果</span>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}