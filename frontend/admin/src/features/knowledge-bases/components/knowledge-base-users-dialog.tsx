import { useState } from 'react'
import { AxiosError } from 'axios'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Trash, UserPlus } from 'lucide-react'
import { KnowledgeBaseDetail, PermissionType } from '@/services/types'
import { useToast } from '@/hooks/use-toast'

interface KnowledgeBaseUsersDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  knowledgeBase: KnowledgeBaseDetail
  onAddUser: (email: string, permission: PermissionType) => Promise<void>
  onUpdatePermission: (userId: number, permission: PermissionType) => Promise<void>
  onRemoveUser: (userId: number) => Promise<void>
}

export function KnowledgeBaseUsersDialog({
  open,
  onOpenChange,
  knowledgeBase,
  onAddUser,
  onUpdatePermission,
  onRemoveUser,
}: KnowledgeBaseUsersDialogProps) {
  const { toast } = useToast()
  const [newUserEmail, setNewUserEmail] = useState('')
  const [newUserPermission, setNewUserPermission] = useState<PermissionType>(PermissionType.VIEWER)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleAddUser = async () => {
    if (!newUserEmail) {
      toast({
        title: '请输入用户邮箱',
        variant: 'destructive',
      })
      return
    }
    
    setIsSubmitting(true)
    try {
      await onAddUser(newUserEmail, newUserPermission)
      setNewUserEmail('')
      setNewUserPermission(PermissionType.VIEWER)
      toast({
        title: '添加成功',
        description: '成员已添加到知识库',
      })
    } catch (_error: unknown) {
      if (_error instanceof AxiosError && _error.response?.data?.message) {
        toast({
          title: '添加失败',
          description: _error.response.data.message,
          variant: 'destructive',
        })
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdatePermission = async (userId: number, permission: PermissionType) => {
    try {
      await onUpdatePermission(userId, permission)
      toast({
        title: '更新成功',
        description: '成员权限已更新',
      })
    } catch (_error: unknown) {
      if (_error instanceof AxiosError && _error.response?.data?.message) {
        toast({
          title: '更新失败',
          description: _error.response.data.message,
          variant: 'destructive',
        })
      }
    }
  }

  const handleRemoveUser = async (userId: number) => {
    try {
      await onRemoveUser(userId)
      toast({
        title: '移除成功',
        description: '成员已从知识库中移除',
      })
    } catch (_error: unknown) {
      if (_error instanceof AxiosError && _error.response?.data?.message) {
        toast({
          title: '移除失败',
          description: _error.response.data.message,
          variant: 'destructive',
        })
      }
    }
  }

  const getPermissionColor = (permission: PermissionType): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" => {
    switch (permission) {
      case PermissionType.OWNER:
        return 'success'
      case PermissionType.ADMIN:
        return 'warning'
      case PermissionType.EDITOR:
        return 'default'
      case PermissionType.VIEWER:
        return 'secondary'
      default:
        return 'default'
    }
  }

  const getPermissionLabel = (permission: PermissionType): string => {
    switch (permission) {
      case PermissionType.OWNER:
        return '所有者'
      case PermissionType.ADMIN:
        return '管理员'
      case PermissionType.EDITOR:
        return '编辑者'
      case PermissionType.VIEWER:
        return '查看者'
      default:
        return '未知'
    }
  }

  // 如果 knowledgeBase 不存在，不渲染对话框
  if (!knowledgeBase) {
    return null
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>管理知识库成员 - {knowledgeBase.name}</DialogTitle>
          <DialogDescription>
            管理知识库的成员及其权限。所有者拥有最高权限，管理员可以管理成员，编辑者可以编辑内容，查看者只能查看。
          </DialogDescription>
        </DialogHeader>
        <div className="flex items-center space-x-4 mb-4">
          <Input
            placeholder="用户邮箱"
            value={newUserEmail}
            onChange={(e) => setNewUserEmail(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddUser()}
          />
          <Select
            value={newUserPermission}
            onValueChange={(value) => setNewUserPermission(value as PermissionType)}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="选择权限" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={PermissionType.ADMIN}>管理员</SelectItem>
              <SelectItem value={PermissionType.EDITOR}>编辑者</SelectItem>
              <SelectItem value={PermissionType.VIEWER}>查看者</SelectItem>
            </SelectContent>
          </Select>
          <Button 
            onClick={handleAddUser} 
            disabled={isSubmitting || !newUserEmail}
            className="flex items-center gap-2"
          >
            <UserPlus className="h-4 w-4" />
            添加成员
          </Button>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>邮箱</TableHead>
              <TableHead>权限</TableHead>
              <TableHead>加入时间</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {knowledgeBase.users?.map((user) => (
              <TableRow key={user.user_id}>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  <Select
                    value={user.permission}
                    onValueChange={(value) =>
                      handleUpdatePermission(user.user_id, value as PermissionType)
                    }
                    disabled={user.permission === PermissionType.OWNER}
                  >
                    <SelectTrigger className="w-[120px]">
                      <SelectValue>
                        <div className="flex items-center gap-2">
                          <Badge variant={getPermissionColor(user.permission)}>
                            {getPermissionLabel(user.permission)}
                          </Badge>
                        </div>
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={PermissionType.ADMIN}>管理员</SelectItem>
                      <SelectItem value={PermissionType.EDITOR}>编辑者</SelectItem>
                      <SelectItem value={PermissionType.VIEWER}>查看者</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>{new Date(user.created_at).toLocaleString()}</TableCell>
                <TableCell className="text-right">
                  {user.permission !== PermissionType.OWNER && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveUser(user.user_id)}
                    >
                      <Trash className="h-4 w-4" />
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </DialogContent>
    </Dialog>
  )
} 