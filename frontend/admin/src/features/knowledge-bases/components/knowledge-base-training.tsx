import React, { useState, useCallback, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { toast } from '@/hooks/use-toast'
import { KnowledgeBaseStatus, KnowledgeBaseTrainResponse } from '@/services/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
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
import {
  Play,
  Square,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
  FileText,
  Zap,
  Loader2,
} from 'lucide-react'

interface KnowledgeBaseTrainingProps {
  knowledgeBaseId: number
  knowledgeBaseName: string
  currentStatus: KnowledgeBaseStatus
  onStatusChange?: (status: KnowledgeBaseStatus) => void
}

export function KnowledgeBaseTraining({
  knowledgeBaseId,
  knowledgeBaseName,
  currentStatus,
  onStatusChange,
}: KnowledgeBaseTrainingProps) {
  const [showTrainDialog, setShowTrainDialog] = useState(false)
  const [trainingProgress, setTrainingProgress] = useState<KnowledgeBaseTrainResponse | null>(null)

  // 获取知识库详情（用于获取最新状态）
  const { data: knowledgeBase, refetch: refetchKnowledgeBase } = useQuery({
    queryKey: ['knowledge-base', knowledgeBaseId],
    queryFn: () => adminService.getKnowledgeBase(knowledgeBaseId),
    refetchInterval: currentStatus === KnowledgeBaseStatus.TRAINING ? 3000 : false, // 训练中时每3秒刷新
  })

  // 训练知识库
  const trainMutation = useMutation({
    mutationFn: () => adminService.trainKnowledgeBase(knowledgeBaseId),
    onSuccess: (response) => {
      if (response.success) {
        setTrainingProgress(response.data)
        onStatusChange?.(response.data.status)
        toast({
          title: '训练已开始',
          description: response.data.message,
        })
        setShowTrainDialog(false)
        refetchKnowledgeBase()
      }
    },
    onError: (error) => {
      toast({
        title: '训练启动失败',
        description: error instanceof Error ? error.message : '请稍后重试',
        variant: 'destructive',
      })
    },
  })

  // 开始训练
  const handleStartTraining = useCallback(() => {
    trainMutation.mutate()
  }, [trainMutation])

  // 监听知识库状态变化
  useEffect(() => {
    if (knowledgeBase?.data) {
      const newStatus = knowledgeBase.data.status
      if (newStatus !== currentStatus) {
        onStatusChange?.(newStatus)
      }
    }
  }, [knowledgeBase?.data, currentStatus, onStatusChange])

  // 获取状态颜色
  const getStatusColor = (status: KnowledgeBaseStatus) => {
    switch (status) {
      case KnowledgeBaseStatus.READY:
        return 'success'
      case KnowledgeBaseStatus.TRAINING:
        return 'default'
      case KnowledgeBaseStatus.ERROR:
        return 'destructive'
      case KnowledgeBaseStatus.INIT:
        return 'secondary'
      default:
        return 'outline'
    }
  }

  // 获取状态文本
  const getStatusText = (status: KnowledgeBaseStatus) => {
    switch (status) {
      case KnowledgeBaseStatus.READY:
        return '就绪'
      case KnowledgeBaseStatus.TRAINING:
        return '训练中'
      case KnowledgeBaseStatus.ERROR:
        return '错误'
      case KnowledgeBaseStatus.INIT:
        return '初始化'
      default:
        return '未知'
    }
  }

  // 获取状态图标
  const getStatusIcon = (status: KnowledgeBaseStatus) => {
    switch (status) {
      case KnowledgeBaseStatus.READY:
        return <CheckCircle className="h-4 w-4" />
      case KnowledgeBaseStatus.TRAINING:
        return <Loader2 className="h-4 w-4 animate-spin" />
      case KnowledgeBaseStatus.ERROR:
        return <AlertCircle className="h-4 w-4" />
      case KnowledgeBaseStatus.INIT:
        return <Clock className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  // 计算训练进度
  const getTrainingProgress = () => {
    if (!trainingProgress || !trainingProgress.total_documents) {
      return 0
    }
    const processed = trainingProgress.processed_documents || 0
    return Math.round((processed / trainingProgress.total_documents) * 100)
  }

  // 格式化剩余时间
  const formatRemainingTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`
    if (seconds < 3600) return `${Math.round(seconds / 60)}分钟`
    return `${Math.round(seconds / 3600)}小时`
  }

  const isTraining = currentStatus === KnowledgeBaseStatus.TRAINING
  const canTrain = currentStatus === KnowledgeBaseStatus.READY || currentStatus === KnowledgeBaseStatus.INIT || currentStatus === KnowledgeBaseStatus.ERROR
  const progress = getTrainingProgress()

  return (
    <div className="space-y-6">
      {/* 状态概览 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            训练状态
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                {getStatusIcon(currentStatus)}
                <span className="font-medium">{knowledgeBaseName}</span>
              </div>
              <Badge variant={getStatusColor(currentStatus)}>
                {getStatusText(currentStatus)}
              </Badge>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetchKnowledgeBase()}
                disabled={isTraining}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                刷新状态
              </Button>
              
              {canTrain && (
                <Button
                  onClick={() => setShowTrainDialog(true)}
                  disabled={trainMutation.isPending}
                >
                  {trainMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      启动中...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      开始训练
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>

          {/* 训练进度 */}
          {isTraining && trainingProgress && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span>训练进度</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {trainingProgress.total_documents && (
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span>总文档: {trainingProgress.total_documents}</span>
                  </div>
                )}
                
                {trainingProgress.processed_documents !== undefined && (
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>已处理: {trainingProgress.processed_documents}</span>
                  </div>
                )}
                
                {trainingProgress.error_documents !== undefined && trainingProgress.error_documents > 0 && (
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-red-500" />
                    <span>失败: {trainingProgress.error_documents}</span>
                  </div>
                )}
                
                {trainingProgress.estimated_time_remaining && (
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>剩余: {formatRemainingTime(trainingProgress.estimated_time_remaining)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 错误状态提示 */}
          {currentStatus === KnowledgeBaseStatus.ERROR && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                知识库训练过程中出现错误，请检查文档内容后重新训练。
              </AlertDescription>
            </Alert>
          )}

          {/* 初始化状态提示 */}
          {currentStatus === KnowledgeBaseStatus.INIT && (
            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                知识库已创建，请开始训练以使其可用于查询。
              </AlertDescription>
            </Alert>
          )}

          {/* 就绪状态提示 */}
          {currentStatus === KnowledgeBaseStatus.READY && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                知识库已就绪，可以进行查询。如果添加了新文档，建议重新训练以获得最佳效果。
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* 训练历史和统计 */}
      <Card>
        <CardHeader>
          <CardTitle>训练信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">最后训练时间</div>
              <div className="font-medium">
                {knowledgeBase?.data.updated_at 
                  ? new Date(knowledgeBase.data.updated_at).toLocaleString('zh-CN')
                  : '未知'
                }
              </div>
            </div>
            <div>
              <div className="text-muted-foreground">创建时间</div>
              <div className="font-medium">
                {knowledgeBase?.data.created_at 
                  ? new Date(knowledgeBase.data.created_at).toLocaleString('zh-CN')
                  : '未知'
                }
              </div>
            </div>
            <div>
              <div className="text-muted-foreground">知识库ID</div>
              <div className="font-medium">{knowledgeBaseId}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 训练确认对话框 */}
      <AlertDialog open={showTrainDialog} onOpenChange={setShowTrainDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>开始训练知识库</AlertDialogTitle>
            <AlertDialogDescription>
              训练过程将处理知识库中的所有文档，生成向量索引以支持智能查询。
              训练时间取决于文档数量和内容复杂度，期间知识库可能无法正常查询。
              <br /><br />
              确定要开始训练 "{knowledgeBaseName}" 吗？
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleStartTraining}>
              开始训练
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}