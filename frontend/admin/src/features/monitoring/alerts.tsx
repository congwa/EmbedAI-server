import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { 
  AlertTriangle, 
  Plus, 
  Edit, 
  Trash2, 
  RefreshCw,
  Settings,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react'
import { adminService } from '@/services/admin'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { toast } from '@/hooks/use-toast'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

// 表单验证模式
const alertFormSchema = z.object({
  name: z.string().min(1, '告警名称不能为空'),
  description: z.string().min(1, '告警描述不能为空'),
  service: z.string().min(1, '请选择服务'),
  metric: z.string().min(1, '请选择指标'),
  condition: z.enum(['greater_than', 'less_than', 'equals', 'not_equals']),
  threshold: z.number().min(0, '阈值必须大于等于0'),
  severity: z.enum(['low', 'medium', 'high', 'critical']),
  enabled: z.boolean(),
})

type AlertFormData = z.infer<typeof alertFormSchema>

// 告警状态徽章组件
function AlertStatusBadge({ status }: { status: string }) {
  const statusConfig = {
    active: { variant: 'destructive' as const, label: '活跃' },
    resolved: { variant: 'default' as const, label: '已解决' },
    acknowledged: { variant: 'secondary' as const, label: '已确认' },
  }

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.active

  return <Badge variant={config.variant}>{config.label}</Badge>
}

// 严重程度徽章组件
function SeverityBadge({ severity }: { severity: string }) {
  const severityConfig = {
    low: { variant: 'outline' as const, label: '低' },
    medium: { variant: 'secondary' as const, label: '中' },
    high: { variant: 'default' as const, label: '高' },
    critical: { variant: 'destructive' as const, label: '严重' },
  }

  const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.low

  return <Badge variant={config.variant}>{config.label}</Badge>
}

// 创建/编辑告警对话框组件
interface AlertDialogProps {
  alert?: any
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

function AlertDialog({ alert, open, onOpenChange, onSuccess }: AlertDialogProps) {
  const queryClient = useQueryClient()
  const isEdit = !!alert

  const form = useForm<AlertFormData>({
    resolver: zodResolver(alertFormSchema),
    defaultValues: {
      name: alert?.name || '',
      description: alert?.description || '',
      service: alert?.service || '',
      metric: alert?.metric || '',
      condition: alert?.condition || 'greater_than',
      threshold: alert?.threshold || 0,
      severity: alert?.severity || 'medium',
      enabled: alert?.enabled ?? true,
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: AlertFormData) => adminService.createAlert(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      toast({
        title: '创建成功',
        description: '告警规则已创建',
      })
      onSuccess()
      onOpenChange(false)
      form.reset()
    },
    onError: () => {
      toast({
        title: '创建失败',
        description: '创建告警规则时发生错误，请重试',
        variant: 'destructive',
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: AlertFormData) => adminService.updateAlert(alert.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      toast({
        title: '更新成功',
        description: '告警规则已更新',
      })
      onSuccess()
      onOpenChange(false)
    },
    onError: () => {
      toast({
        title: '更新失败',
        description: '更新告警规则时发生错误，请重试',
        variant: 'destructive',
      })
    },
  })

  const onSubmit = (data: AlertFormData) => {
    if (isEdit) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑告警规则' : '创建告警规则'}</DialogTitle>
          <DialogDescription>
            配置告警规则以监控系统指标和服务状态
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">告警名称</Label>
              <Input
                id="name"
                {...form.register('name')}
                placeholder="输入告警名称"
              />
              {form.formState.errors.name && (
                <p className="text-sm text-red-500">{form.formState.errors.name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="service">服务</Label>
              <Select value={form.watch('service')} onValueChange={(value) => form.setValue('service', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="选择服务" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="database">数据库</SelectItem>
                  <SelectItem value="redis">Redis</SelectItem>
                  <SelectItem value="storage">存储服务</SelectItem>
                  <SelectItem value="llm_api">LLM API</SelectItem>
                  <SelectItem value="system">系统</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">描述</Label>
            <Textarea
              id="description"
              {...form.register('description')}
              placeholder="输入告警描述"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="metric">监控指标</Label>
              <Select value={form.watch('metric')} onValueChange={(value) => form.setValue('metric', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="选择指标" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cpu_usage">CPU使用率</SelectItem>
                  <SelectItem value="memory_usage">内存使用率</SelectItem>
                  <SelectItem value="disk_usage">磁盘使用率</SelectItem>
                  <SelectItem value="response_time">响应时间</SelectItem>
                  <SelectItem value="error_rate">错误率</SelectItem>
                  <SelectItem value="uptime">运行时间</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="condition">条件</Label>
              <Select value={form.watch('condition')} onValueChange={(value) => form.setValue('condition', value as any)}>
                <SelectTrigger>
                  <SelectValue placeholder="选择条件" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="greater_than">大于</SelectItem>
                  <SelectItem value="less_than">小于</SelectItem>
                  <SelectItem value="equals">等于</SelectItem>
                  <SelectItem value="not_equals">不等于</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="threshold">阈值</Label>
              <Input
                id="threshold"
                type="number"
                step="0.1"
                {...form.register('threshold', { valueAsNumber: true })}
                placeholder="输入阈值"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="severity">严重程度</Label>
              <Select value={form.watch('severity')} onValueChange={(value) => form.setValue('severity', value as any)}>
                <SelectTrigger>
                  <SelectValue placeholder="选择严重程度" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">低</SelectItem>
                  <SelectItem value="medium">中</SelectItem>
                  <SelectItem value="high">高</SelectItem>
                  <SelectItem value="critical">严重</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="enabled">启用状态</Label>
              <div className="flex items-center space-x-2 pt-2">
                <Switch
                  id="enabled"
                  checked={form.watch('enabled')}
                  onCheckedChange={(checked) => form.setValue('enabled', checked)}
                />
                <Label htmlFor="enabled">启用告警</Label>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button 
              type="submit" 
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {isEdit ? '更新' : '创建'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// 主告警管理组件
export function AlertsManagement() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState<string>('all')
  const [severity, setSeverity] = useState<string>('all')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingAlert, setEditingAlert] = useState<any>(null)
  const pageSize = 10

  const queryClient = useQueryClient()

  // 获取告警列表
  const { data: alertsData, isLoading, error } = useQuery({
    queryKey: ['alerts', page, status, severity],
    queryFn: () => adminService.getAlerts({
      page,
      page_size: pageSize,
      status: status === 'all' ? undefined : status as any,
      severity: severity === 'all' ? undefined : severity as any,
    }),
  })

  // 删除告警
  const deleteMutation = useMutation({
    mutationFn: (id: number) => adminService.deleteAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      toast({
        title: '删除成功',
        description: '告警规则已删除',
      })
    },
    onError: () => {
      toast({
        title: '删除失败',
        description: '删除告警规则时发生错误，请重试',
        variant: 'destructive',
      })
    },
  })

  const handleEdit = (alert: any) => {
    setEditingAlert(alert)
    setDialogOpen(true)
  }

  const handleCreate = () => {
    setEditingAlert(null)
    setDialogOpen(true)
  }

  const handleDelete = (id: number) => {
    if (confirm('确定要删除这个告警规则吗？')) {
      deleteMutation.mutate(id)
    }
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          加载告警数据失败，请检查网络连接或稍后重试。
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">告警管理</h1>
          <p className="text-muted-foreground">
            管理系统告警规则和告警历史
          </p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          创建告警规则
        </Button>
      </div>

      {/* 过滤器 */}
      <div className="flex items-center space-x-4">
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="告警状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有状态</SelectItem>
            <SelectItem value="active">活跃</SelectItem>
            <SelectItem value="resolved">已解决</SelectItem>
            <SelectItem value="acknowledged">已确认</SelectItem>
          </SelectContent>
        </Select>
        <Select value={severity} onValueChange={setSeverity}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="严重程度" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有级别</SelectItem>
            <SelectItem value="low">低</SelectItem>
            <SelectItem value="medium">中</SelectItem>
            <SelectItem value="high">高</SelectItem>
            <SelectItem value="critical">严重</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* 告警列表 */}
      <Card>
        <CardHeader>
          <CardTitle>告警列表</CardTitle>
          <CardDescription>系统告警规则和状态</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名称</TableHead>
                  <TableHead>服务</TableHead>
                  <TableHead>指标</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>严重程度</TableHead>
                  <TableHead>触发时间</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alertsData?.data.items.map((alert) => (
                  <TableRow key={alert.id}>
                    <TableCell className="font-medium">{alert.name}</TableCell>
                    <TableCell>{alert.service}</TableCell>
                    <TableCell>{alert.metric}</TableCell>
                    <TableCell>
                      <AlertStatusBadge status={alert.status} />
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={alert.severity} />
                    </TableCell>
                    <TableCell>
                      {format(new Date(alert.triggered_at), 'yyyy-MM-dd HH:mm', { locale: zhCN })}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(alert)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(alert.id)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* 分页 */}
      {alertsData?.data.pagination && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            共 {alertsData.data.pagination.total} 条记录
          </p>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
            >
              上一页
            </Button>
            <span className="text-sm">
              第 {page} 页 / 共 {Math.ceil(alertsData.data.pagination.total / pageSize)} 页
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={page * pageSize >= alertsData.data.pagination.total}
            >
              下一页
            </Button>
          </div>
        </div>
      )}

      {/* 创建/编辑对话框 */}
      <AlertDialog
        alert={editingAlert}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={() => {
          setEditingAlert(null)
        }}
      />
    </div>
  )
}
