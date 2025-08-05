import React, { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { toast } from '@/hooks/use-toast'
import { KnowledgeBaseQueryRequest, KnowledgeBaseQueryResponse } from '@/services/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Search,
  Send,
  Loader2,
  ChevronDown,
  ChevronRight,
  FileText,
  Clock,
  Zap,
  History,
  BookOpen,
} from 'lucide-react'

interface KnowledgeBaseQueryProps {
  knowledgeBaseId: number
  knowledgeBaseName: string
}

interface QueryHistory {
  id: string
  query: string
  timestamp: string
  response?: KnowledgeBaseQueryResponse
}

export function KnowledgeBaseQuery({
  knowledgeBaseId,
  knowledgeBaseName,
}: KnowledgeBaseQueryProps) {
  const [query, setQuery] = useState('')
  const [queryParams, setQueryParams] = useState({
    temperature: 0.7,
    top_k: 5,
    similarity_threshold: 0.7,
  })
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([])
  const [selectedHistory, setSelectedHistory] = useState<QueryHistory | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)

  // 查询知识库
  const queryMutation = useMutation({
    mutationFn: async (queryData: KnowledgeBaseQueryRequest) => {
      return adminService.queryKnowledgeBase(knowledgeBaseId, queryData)
    },
    onSuccess: (response, variables) => {
      if (response.success) {
        const historyItem: QueryHistory = {
          id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          query: variables.query,
          timestamp: new Date().toISOString(),
          response: response.data,
        }
        setQueryHistory(prev => [historyItem, ...prev.slice(0, 19)]) // 保留最近20条
        setSelectedHistory(historyItem)
        toast({
          title: '查询成功',
          description: '知识库查询已完成',
        })
      }
    },
    onError: (error) => {
      toast({
        title: '查询失败',
        description: error instanceof Error ? error.message : '请稍后重试',
        variant: 'destructive',
      })
    },
  })

  // 执行查询
  const handleQuery = useCallback(() => {
    if (!query.trim()) {
      toast({
        title: '请输入查询内容',
        variant: 'destructive',
      })
      return
    }

    const queryData: KnowledgeBaseQueryRequest = {
      query: query.trim(),
      temperature: queryParams.temperature,
      top_k: queryParams.top_k,
      similarity_threshold: queryParams.similarity_threshold,
    }

    queryMutation.mutate(queryData)
  }, [query, queryParams, queryMutation])

  // 使用历史查询
  const handleUseHistory = useCallback((historyItem: QueryHistory) => {
    setQuery(historyItem.query)
    setSelectedHistory(historyItem)
  }, [])

  // 格式化时间
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // 获取相似度颜色
  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 0.8) return 'bg-green-500'
    if (similarity >= 0.6) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* 查询输入区域 */}
      <div className="lg:col-span-2 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              查询 {knowledgeBaseName}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 查询输入 */}
            <div>
              <Label htmlFor="query">查询内容</Label>
              <Textarea
                id="query"
                placeholder="请输入您的问题..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="min-h-[100px] mt-2"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault()
                    handleQuery()
                  }
                }}
              />
              <p className="text-xs text-muted-foreground mt-1">
                按 Ctrl+Enter 快速查询
              </p>
            </div>

            {/* 高级参数 */}
            <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" className="p-0 h-auto">
                  {showAdvanced ? (
                    <ChevronDown className="h-4 w-4 mr-2" />
                  ) : (
                    <ChevronRight className="h-4 w-4 mr-2" />
                  )}
                  高级参数
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-4 mt-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="temperature">温度 (Temperature)</Label>
                    <Input
                      id="temperature"
                      type="number"
                      min="0"
                      max="2"
                      step="0.1"
                      value={queryParams.temperature}
                      onChange={(e) =>
                        setQueryParams(prev => ({
                          ...prev,
                          temperature: parseFloat(e.target.value) || 0.7,
                        }))
                      }
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="top_k">返回文档数 (Top K)</Label>
                    <Input
                      id="top_k"
                      type="number"
                      min="1"
                      max="20"
                      value={queryParams.top_k}
                      onChange={(e) =>
                        setQueryParams(prev => ({
                          ...prev,
                          top_k: parseInt(e.target.value) || 5,
                        }))
                      }
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="similarity">相似度阈值</Label>
                    <Input
                      id="similarity"
                      type="number"
                      min="0"
                      max="1"
                      step="0.1"
                      value={queryParams.similarity_threshold}
                      onChange={(e) =>
                        setQueryParams(prev => ({
                          ...prev,
                          similarity_threshold: parseFloat(e.target.value) || 0.7,
                        }))
                      }
                      className="mt-1"
                    />
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>

            {/* 查询按钮 */}
            <Button
              onClick={handleQuery}
              disabled={queryMutation.isPending || !query.trim()}
              className="w-full"
            >
              {queryMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  查询中...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  查询知识库
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* 查询结果 */}
        {selectedHistory?.response && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                查询结果
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 回答内容 */}
              <div>
                <Label>AI 回答</Label>
                <div className="mt-2 p-4 bg-muted rounded-lg">
                  <p className="whitespace-pre-wrap">{selectedHistory.response.answer}</p>
                </div>
              </div>

              {/* Token 使用统计 */}
              {selectedHistory.response.tokens_used && (
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Zap className="h-4 w-4" />
                    <span>提示词: {selectedHistory.response.tokens_used.prompt_tokens}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Zap className="h-4 w-4" />
                    <span>完成词: {selectedHistory.response.tokens_used.completion_tokens}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Zap className="h-4 w-4" />
                    <span>总计: {selectedHistory.response.tokens_used.total_tokens}</span>
                  </div>
                </div>
              )}

              <Separator />

              {/* 引用来源 */}
              <div>
                <Label>引用来源 ({selectedHistory.response.sources.length})</Label>
                <div className="mt-2 space-y-3">
                  {selectedHistory.response.sources.map((source, index) => (
                    <Card key={index} className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4" />
                          <span className="font-medium">{source.document_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div
                            className={`w-2 h-2 rounded-full ${getSimilarityColor(source.similarity)}`}
                          />
                          <span className="text-sm text-muted-foreground">
                            {(source.similarity * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-3">
                        {source.content}
                      </p>
                    </Card>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 查询历史 */}
      <div>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              查询历史
            </CardTitle>
          </CardHeader>
          <CardContent>
            {queryHistory.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                暂无查询历史
              </p>
            ) : (
              <div className="space-y-2">
                {queryHistory.map((item) => (
                  <Card
                    key={item.id}
                    className={`p-3 cursor-pointer transition-colors ${
                      selectedHistory?.id === item.id
                        ? 'bg-primary/5 border-primary'
                        : 'hover:bg-muted/50'
                    }`}
                    onClick={() => handleUseHistory(item)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <p className="text-sm font-medium line-clamp-2">
                        {item.query}
                      </p>
                      <Badge variant="outline" className="ml-2 flex-shrink-0">
                        <Clock className="h-3 w-3 mr-1" />
                        {formatTime(item.timestamp)}
                      </Badge>
                    </div>
                    {item.response && (
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {item.response.answer}
                      </p>
                    )}
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}