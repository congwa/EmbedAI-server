import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
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
  CheckSquare,
  Square,
  Minus,
  Trash2,
  Edit,
  Download,
  Upload,
  RotateCcw,
  Play,
  Pause,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useNotification } from '@/hooks/use-notification'

export interface BulkAction {
  id: string
  label: string
  icon?: React.ComponentType<{ className?: string }>
  variant?: 'default' | 'destructive' | 'secondary'
  requiresConfirmation?: boolean
  confirmationTitle?: string
  confirmationDescription?: string
  disabled?: boolean
}

interface BulkOperationsProps<T> {
  items: T[]
  selectedItems: T[]
  onSelectionChange: (items: T[]) => void
  actions: BulkAction[]
  onAction: (actionId: string, items: T[]) => Promise<void>
  getItemId: (item: T) => string | number
  getItemLabel: (item: T) => string
  className?: string
}

export function BulkOperations<T>({
  items,
  selectedItems,
  onSelectionChange,
  actions,
  onAction,
  getItemId,
  getItemLabel,
  className,
}: BulkOperationsProps<T>) {
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionProgress, setExecutionProgress] = useState(0)
  const [executionResults, setExecutionResults] = useState<{
    success: number
    failed: number
    errors: Array<{ item: T; error: string }>
  } | null>(null)
  const [showConfirmation, setShowConfirmation] = useState<{
    action: BulkAction
    items: T[]
  } | null>(null)
  const [showResults, setShowResults] = useState(false)
  
  const notification = useNotification()

  const isAllSelected = items.length > 0 && selectedItems.length === items.length
  const isPartiallySelected = selectedItems.length > 0 && selectedItems.length < items.length

  const handleSelectAll = () => {
    if (isAllSelected) {
      onSelectionChange([])
    } else {
      onSelectionChange(items)
    }
  }

  const handleItemToggle = (item: T) => {
    const itemId = getItemId(item)
    const isSelected = selectedItems.some(selected => getItemId(selected) === itemId)
    
    if (isSelected) {
      onSelectionChange(selectedItems.filter(selected => getItemId(selected) !== itemId))
    } else {
      onSelectionChange([...selectedItems, item])
    }
  }

  const handleAction = async (action: BulkAction) => {
    if (selectedItems.length === 0) {
      notification.warning('请选择要操作的项目')
      return
    }

    if (action.requiresConfirmation) {
      setShowConfirmation({ action, items: selectedItems })
      return
    }

    await executeAction(action, selectedItems)
  }

  const executeAction = async (action: BulkAction, items: T[]) => {
    setIsExecuting(true)
    setExecutionProgress(0)
    setExecutionResults(null)

    const results = {
      success: 0,
      failed: 0,
      errors: [] as Array<{ item: T; error: string }>,
    }

    try {
      // 批量执行操作
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        try {
          await onAction(action.id, [item])
          results.success++
        } catch (error) {
          results.failed++
          results.errors.push({
            item,
            error: error instanceof Error ? error.message : '未知错误',
          })
        }
        
        setExecutionProgress(((i + 1) / items.length) * 100)
      }

      // 显示结果
      setExecutionResults(results)
      setShowResults(true)

      // 显示通知
      if (results.failed === 0) {
        notification.success(
          `批量操作完成`,
          `成功处理 ${results.success} 个项目`
        )
      } else {
        notification.warning(
          `批量操作完成`,
          `成功 ${results.success} 个，失败 ${results.failed} 个`
        )
      }

      // 清除选择
      onSelectionChange([])
    } catch (error) {
      notification.error(
        '批量操作失败',
        error instanceof Error ? error.message : '未知错误'
      )
    } finally {
      setIsExecuting(false)
    }
  }

  const getSelectionIcon = () => {
    if (isAllSelected) {
      return <CheckSquare className="h-4 w-4" />
    } else if (isPartiallySelected) {
      return <Minus className="h-4 w-4" />
    } else {
      return <Square className="h-4 w-4" />
    }
  }

  return (
    <>
      <div className={cn('flex items-center gap-4 p-4 border rounded-lg bg-muted/50', className)}>
        {/* 全选控制 */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={handleSelectAll}
          >
            {getSelectionIcon()}
          </Button>
          <span className="text-sm text-muted-foreground">
            {selectedItems.length > 0 ? (
              <>已选择 <Badge variant="secondary">{selectedItems.length}</Badge> 项</>
            ) : (
              '选择项目'
            )}
          </span>
        </div>

        {/* 批量操作按钮 */}
        {selectedItems.length > 0 && (
          <div className="flex items-center gap-2 ml-auto">
            {actions.map((action) => {
              const Icon = action.icon
              return (
                <Button
                  key={action.id}
                  variant={action.variant || 'outline'}
                  size="sm"
                  onClick={() => handleAction(action)}
                  disabled={action.disabled || isExecuting}
                  className="gap-2"
                >
                  {Icon && <Icon className="h-3 w-3" />}
                  {action.label}
                </Button>
              )
            })}
          </div>
        )}
      </div>

      {/* 执行进度 */}
      {isExecuting && (
        <div className="p-4 border rounded-lg bg-background">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">正在执行批量操作...</span>
            <span className="text-sm text-muted-foreground">
              {Math.round(executionProgress)}%
            </span>
          </div>
          <Progress value={executionProgress} className="h-2" />
        </div>
      )}

      {/* 确认对话框 */}
      <AlertDialog
        open={!!showConfirmation}
        onOpenChange={() => setShowConfirmation(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              {showConfirmation?.action.confirmationTitle || '确认操作'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {showConfirmation?.action.confirmationDescription || 
                `您确定要对选中的 ${selectedItems.length} 个项目执行"${showConfirmation?.action.label}"操作吗？`
              }
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (showConfirmation) {
                  executeAction(showConfirmation.action, showConfirmation.items)
                  setShowConfirmation(null)
                }
              }}
            >
              确认
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 结果对话框 */}
      <Dialog open={showResults} onOpenChange={setShowResults}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {executionResults?.failed === 0 ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500" />
              )}
              批量操作结果
            </DialogTitle>
            <DialogDescription>
              操作已完成，以下是详细结果
            </DialogDescription>
          </DialogHeader>

          {executionResults && (
            <div className="space-y-4">
              {/* 统计信息 */}
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 text-green-700">
                  <CheckCircle className="h-4 w-4" />
                  <span className="font-medium">成功: {executionResults.success}</span>
                </div>
                <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 text-red-700">
                  <XCircle className="h-4 w-4" />
                  <span className="font-medium">失败: {executionResults.failed}</span>
                </div>
              </div>

              {/* 错误详情 */}
              {executionResults.errors.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-sm">失败详情:</h4>
                  <div className="max-h-40 overflow-y-auto space-y-2">
                    {executionResults.errors.map((error, index) => (
                      <div key={index} className="p-2 rounded border bg-red-50 text-red-700 text-sm">
                        <div className="font-medium">{getItemLabel(error.item)}</div>
                        <div className="text-xs opacity-75">{error.error}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button onClick={() => setShowResults(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

// 批量选择表格行组件
interface BulkSelectableRowProps {
  selected: boolean
  onToggle: () => void
  children: React.ReactNode
  className?: string
}

export function BulkSelectableRow({
  selected,
  onToggle,
  children,
  className,
}: BulkSelectableRowProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg border transition-colors',
        selected ? 'bg-accent border-primary' : 'hover:bg-muted/50',
        className
      )}
    >
      <Checkbox
        checked={selected}
        onCheckedChange={onToggle}
        className="flex-shrink-0"
      />
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  )
}

// 预定义的批量操作
export const userBulkActions: BulkAction[] = [
  {
    id: 'activate',
    label: '启用用户',
    icon: CheckCircle,
    variant: 'default',
  },
  {
    id: 'deactivate',
    label: '禁用用户',
    icon: XCircle,
    variant: 'secondary',
    requiresConfirmation: true,
    confirmationTitle: '确认禁用用户',
    confirmationDescription: '禁用后用户将无法登录系统，确定要继续吗？',
  },
  {
    id: 'reset_keys',
    label: '重置密钥',
    icon: RotateCcw,
    variant: 'secondary',
    requiresConfirmation: true,
    confirmationTitle: '确认重置密钥',
    confirmationDescription: '重置后用户需要使用新的密钥，确定要继续吗？',
  },
  {
    id: 'delete',
    label: '删除用户',
    icon: Trash2,
    variant: 'destructive',
    requiresConfirmation: true,
    confirmationTitle: '确认删除用户',
    confirmationDescription: '删除后无法恢复，确定要继续吗？',
  },
]

export const documentBulkActions: BulkAction[] = [
  {
    id: 'reprocess',
    label: '重新处理',
    icon: RotateCcw,
    variant: 'default',
  },
  {
    id: 'download',
    label: '批量下载',
    icon: Download,
    variant: 'secondary',
  },
  {
    id: 'move',
    label: '移动到知识库',
    icon: Upload,
    variant: 'secondary',
  },
  {
    id: 'delete',
    label: '删除文档',
    icon: Trash2,
    variant: 'destructive',
    requiresConfirmation: true,
    confirmationTitle: '确认删除文档',
    confirmationDescription: '删除后无法恢复，确定要继续吗？',
  },
]

export const knowledgeBaseBulkActions: BulkAction[] = [
  {
    id: 'train',
    label: '开始训练',
    icon: Play,
    variant: 'default',
  },
  {
    id: 'pause_training',
    label: '暂停训练',
    icon: Pause,
    variant: 'secondary',
  },
  {
    id: 'export',
    label: '导出数据',
    icon: Download,
    variant: 'secondary',
  },
  {
    id: 'delete',
    label: '删除知识库',
    icon: Trash2,
    variant: 'destructive',
    requiresConfirmation: true,
    confirmationTitle: '确认删除知识库',
    confirmationDescription: '删除后所有相关数据都将丢失，确定要继续吗？',
  },
]