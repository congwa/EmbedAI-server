import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { 
  Shield, 
  ShieldCheck, 
  ShieldX, 
  Plus, 
  Edit, 
  Trash2, 
  Search,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { adminService } from '@/services/admin'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { toast } from '@/hooks/use-toast'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

// 表单验证模式
const whitelistFormSchema = z.object({
  ip_address: z.string().min(1, 'IP地址不能为空').regex(/^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$/, 'IP地址格式不正确'),
  description: z.string().min(1, '描述不能为空'),
  status: z.enum(['active', 'inactive']),
})

const blacklistFormSchema = z.object({
  ip_address: z.string().min(1, 'IP地址不能为空').regex(/^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$/, 'IP地址格式不正确'),
  reason: z.string().min(1, '原因不能为空'),
  status: z.enum(['active', 'inactive']),
})

type WhitelistFormData = z.infer<typeof whitelistFormSchema>
type BlacklistFormData = z.infer<typeof blacklistFormSchema>

// 状态徽章组件
function StatusBadge({ status }: { status: 'active' | 'inactive' }) {
  return (
    <Badge variant={status === 'active' ? 'default' : 'secondary'}>
      {status === 'active' ? '启用' : '禁用'}
    </Badge>
  )
}

// IP白名单对话框组件
interface WhitelistDialogProps {
  entry?: any
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

function WhitelistDialog({ entry, open, onOpenChange, onSuccess }: WhitelistDialogProps) {
  const queryClient = useQueryClient()
  const isEdit = !!entry

  const form = useForm<WhitelistFormData>({
    resolver: zodResolver(whitelistFormSchema),
    defaultValues: {
      ip_address: entry?.ip_address || '',
      description: entry?.description || '',
      status: entry?.status || 'active',
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: WhitelistFormData) => adminService.addIpToWhitelist(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ip-whitelist'] })
      toast({
        title: '添加成功',
        description: 'IP地址已添加到白名单',
      })
      onSuccess()
      onOpenChange(false)
      form.reset()
    },
    onError: () => {
      toast({
        title: '添加失败',
        description: '添加IP白名单时发生错误，请重试',
        variant: 'destructive',
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: WhitelistFormData) => adminService.updateIpWhitelist(entry.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ip-whitelist'] })
      toast({
        title: '更新成功',
        description: 'IP白名单已更新',
      })
      onSuccess()
      onOpenChange(false)
    },
    onError: () => {
      toast({
        title: '更新失败',
        description: '更新IP白名单时发生错误，请重试',
        variant: 'destructive',
      })
    },
  })

  const onSubmit = (data: WhitelistFormData) => {
    if (isEdit) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑IP白名单' : '添加IP白名单'}</DialogTitle>
          <DialogDescription>
            管理允许访问系统的IP地址
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ip_address">IP地址</Label>
            <Input
              id="ip_address"
              {...form.register('ip_address')}
              placeholder="例如: 192.168.1.1 或 192.168.1.0/24"
            />
            {form.formState.errors.ip_address && (
              <p className="text-sm text-red-500">{form.formState.errors.ip_address.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">描述</Label>
            <Textarea
              id="description"
              {...form.register('description')}
              placeholder="输入描述信息"
              rows={3}
            />
            {form.formState.errors.description && (
              <p className="text-sm text-red-500">{form.formState.errors.description.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="status">状态</Label>
            <Select value={form.watch('status')} onValueChange={(value) => form.setValue('status', value as any)}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">启用</SelectItem>
                <SelectItem value="inactive">禁用</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button 
              type="submit" 
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {isEdit ? '更新' : '添加'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// IP黑名单对话框组件
interface BlacklistDialogProps {
  entry?: any
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

function BlacklistDialog({ entry, open, onOpenChange, onSuccess }: BlacklistDialogProps) {
  const queryClient = useQueryClient()
  const isEdit = !!entry

  const form = useForm<BlacklistFormData>({
    resolver: zodResolver(blacklistFormSchema),
    defaultValues: {
      ip_address: entry?.ip_address || '',
      reason: entry?.reason || '',
      status: entry?.status || 'active',
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: BlacklistFormData) => adminService.addIpToBlacklist(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ip-blacklist'] })
      toast({
        title: '添加成功',
        description: 'IP地址已添加到黑名单',
      })
      onSuccess()
      onOpenChange(false)
      form.reset()
    },
    onError: () => {
      toast({
        title: '添加失败',
        description: '添加IP黑名单时发生错误，请重试',
        variant: 'destructive',
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: BlacklistFormData) => adminService.updateIpBlacklist(entry.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ip-blacklist'] })
      toast({
        title: '更新成功',
        description: 'IP黑名单已更新',
      })
      onSuccess()
      onOpenChange(false)
    },
    onError: () => {
      toast({
        title: '更新失败',
        description: '更新IP黑名单时发生错误，请重试',
        variant: 'destructive',
      })
    },
  })

  const onSubmit = (data: BlacklistFormData) => {
    if (isEdit) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑IP黑名单' : '添加IP黑名单'}</DialogTitle>
          <DialogDescription>
            管理禁止访问系统的IP地址
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ip_address">IP地址</Label>
            <Input
              id="ip_address"
              {...form.register('ip_address')}
              placeholder="例如: 192.168.1.1 或 192.168.1.0/24"
            />
            {form.formState.errors.ip_address && (
              <p className="text-sm text-red-500">{form.formState.errors.ip_address.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="reason">封禁原因</Label>
            <Textarea
              id="reason"
              {...form.register('reason')}
              placeholder="输入封禁原因"
              rows={3}
            />
            {form.formState.errors.reason && (
              <p className="text-sm text-red-500">{form.formState.errors.reason.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="status">状态</Label>
            <Select value={form.watch('status')} onValueChange={(value) => form.setValue('status', value as any)}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">启用</SelectItem>
                <SelectItem value="inactive">禁用</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button 
              type="submit" 
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {isEdit ? '更新' : '添加'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// IP白名单管理组件
function WhitelistManagement() {
  const [page, setPage] = useState(1)
  const [searchIp, setSearchIp] = useState('')
  const [status, setStatus] = useState<string>('all')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingEntry, setEditingEntry] = useState<any>(null)
  const pageSize = 10

  const queryClient = useQueryClient()

  // 获取IP白名单
  const { data: whitelistData, isLoading, error } = useQuery({
    queryKey: ['ip-whitelist', page, searchIp, status],
    queryFn: () => adminService.getIpWhitelist({
      page,
      page_size: pageSize,
      ip_address: searchIp || undefined,
      status: status === 'all' ? undefined : status as any,
    }),
  })

  // 删除IP白名单
  const deleteMutation = useMutation({
    mutationFn: (id: number) => adminService.removeIpFromWhitelist(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ip-whitelist'] })
      toast({
        title: '删除成功',
        description: 'IP白名单条目已删除',
      })
    },
    onError: () => {
      toast({
        title: '删除失败',
        description: '删除IP白名单时发生错误，请重试',
        variant: 'destructive',
      })
    },
  })

  const handleEdit = (entry: any) => {
    setEditingEntry(entry)
    setDialogOpen(true)
  }

  const handleCreate = () => {
    setEditingEntry(null)
    setDialogOpen(true)
  }

  const handleDelete = (id: number) => {
    if (confirm('确定要删除这个IP白名单条目吗？')) {
      deleteMutation.mutate(id)
    }
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          加载IP白名单数据失败，请检查网络连接或稍后重试。
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-4">
      {/* 控制面板 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索IP地址"
              value={searchIp}
              onChange={(e) => setSearchIp(e.target.value)}
              className="pl-8 w-[250px]"
            />
          </div>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有状态</SelectItem>
              <SelectItem value="active">启用</SelectItem>
              <SelectItem value="inactive">禁用</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          添加IP白名单
        </Button>
      </div>

      {/* IP白名单列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5" />
            IP白名单
          </CardTitle>
          <CardDescription>管理允许访问系统的IP地址</CardDescription>
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
                  <TableHead>IP地址</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>访问次数</TableHead>
                  <TableHead>创建者</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {whitelistData?.data.items.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="font-mono">{entry.ip_address}</TableCell>
                    <TableCell>{entry.description}</TableCell>
                    <TableCell>
                      <StatusBadge status={entry.status} />
                    </TableCell>
                    <TableCell>{entry.access_count}</TableCell>
                    <TableCell>{entry.created_by_email}</TableCell>
                    <TableCell>
                      {format(new Date(entry.created_at), 'yyyy-MM-dd HH:mm', { locale: zhCN })}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(entry)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(entry.id)}
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
      {whitelistData?.data.pagination && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            共 {whitelistData.data.pagination.total} 条记录
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
              第 {page} 页 / 共 {Math.ceil(whitelistData.data.pagination.total / pageSize)} 页
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={page * pageSize >= whitelistData.data.pagination.total}
            >
              下一页
            </Button>
          </div>
        </div>
      )}

      {/* 创建/编辑对话框 */}
      <WhitelistDialog
        entry={editingEntry}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={() => {
          setEditingEntry(null)
        }}
      />
    </div>
  )
}

// IP黑名单管理组件（类似结构，这里简化）
function BlacklistManagement() {
  // 类似的实现逻辑...
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldX className="h-5 w-5" />
            IP黑名单
          </CardTitle>
          <CardDescription>管理禁止访问系统的IP地址</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">IP黑名单管理功能开发中...</p>
        </CardContent>
      </Card>
    </div>
  )
}

// 主IP管理组件
export function IpManagement() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">IP管理</h1>
        <p className="text-muted-foreground">
          管理系统访问控制的IP白名单和黑名单
        </p>
      </div>

      <Tabs defaultValue="whitelist" className="space-y-4">
        <TabsList>
          <TabsTrigger value="whitelist">IP白名单</TabsTrigger>
          <TabsTrigger value="blacklist">IP黑名单</TabsTrigger>
        </TabsList>

        <TabsContent value="whitelist" className="space-y-4">
          <WhitelistManagement />
        </TabsContent>

        <TabsContent value="blacklist" className="space-y-4">
          <BlacklistManagement />
        </TabsContent>
      </Tabs>
    </div>
  )
}
