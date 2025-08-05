import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { adminService } from '@/services/admin'

interface CreateUserDialogProps {
  onSuccess: () => void
}

export function CreateUserDialog({ onSuccess }: CreateUserDialogProps) {
  const { toast } = useToast()
  const [isOpen, setIsOpen] = useState(false)
  const [form, setForm] = useState({
    email: '',
    password: '',
  })

  const handleSubmit = async () => {
    try {
      await adminService.createUser(form)
      toast({
        title: '创建成功',
        description: '用户创建成功',
      })
      setIsOpen(false)
      onSuccess()
      // 重置表单
      setForm({
        email: '',
        password: '',
      })
    } catch (_error) {
      toast({
        title: '创建失败',
        description: '用户创建失败，请重试',
        variant: 'destructive',
      })
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          创建用户
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>创建新用户</DialogTitle>
          <DialogDescription>
            创建一个新的用户账号，请填写以下信息。
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="email" className="text-right">
              邮箱
            </Label>
            <Input
              id="email"
              type="email"
              className="col-span-3"
              value={form.email}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  email: e.target.value,
                }))
              }
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="password" className="text-right">
              密码
            </Label>
            <Input
              id="password"
              type="password"
              className="col-span-3"
              value={form.password}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  password: e.target.value,
                }))
              }
            />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleSubmit}>确认创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 