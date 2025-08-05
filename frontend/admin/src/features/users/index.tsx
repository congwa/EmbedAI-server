'use client'

import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { adminService } from '@/services/admin'
import { useAuth } from '@/stores/authStore'
import { useToast } from '@/hooks/use-toast'
import { CreateUserDialog } from './components/create-user-dialog'
import { UsersTable } from './components/users-table'
import { Pagination } from './components/pagination'
import { UserActivityMonitor } from './components/user-activity-monitor'
import { BulkUserOperations } from './components/bulk-user-operations'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function UsersPage() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const { user } = useAuth()
  const [page, setPage] = useState(1)
  const [selectedUsers, setSelectedUsers] = useState<number[]>([])
  const pageSize = 10

  // 检查是否是管理员
  useEffect(() => {
    if (!user?.is_admin) {
      navigate({ to: '/' })
    }
  }, [user, navigate])

  // 获取用户列表
  const { data: usersData, refetch } = useQuery({
    queryKey: ['users', page, pageSize],
    queryFn: () => adminService.getUsers(page, pageSize),
    enabled: !!user?.is_admin,
  })

  // 更新用户状态
  const handleUpdateStatus = async (userId: number, is_active: boolean) => {
    try {
      await adminService.updateUserStatus(userId, { is_active })
      toast({
        title: '更新成功',
        description: `用户已${is_active ? '启用' : '禁用'}`,
      })
      refetch()
    } catch (error) {
      toast({
        variant: 'destructive',
        title: '更新失败',
        description: error instanceof Error ? error.message : '操作失败，请稍后重试',
      })
    }
  }

  // 更新用户管理员权限
  const handleUpdateAdmin = async (userId: number, is_admin: boolean) => {
    try {
      await adminService.updateUserAdmin(userId, { is_admin })
      toast({
        title: '更新成功',
        description: `用户已${is_admin ? '设为管理员' : '取消管理员权限'}`,
      })
      refetch()
    } catch (error) {
      toast({
        variant: 'destructive',
        title: '更新失败',
        description: error instanceof Error ? error.message : '操作失败，请稍后重试',
      })
    }
  }

  // 重置用户密钥对
  const handleResetKeys = async (userId: number) => {
    try {
      const response = await adminService.resetUserKeys(userId)
      toast({
        title: '重置成功',
        description: '用户密钥对已重置，新密钥已生成',
      })
      refetch()
      
      // 如果需要，可以显示新密钥信息
      if (response.data) {
        console.log('New keys generated for user:', userId)
      }
    } catch (error) {
      toast({
        variant: 'destructive',
        title: '重置失败',
        description: error instanceof Error ? error.message : '密钥重置失败，请稍后重试',
      })
    }
  }

  if (!user?.is_admin) {
    return null
  }

  return (
    <div className="container mx-auto py-10">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold tracking-tight">用户管理</h2>
        <CreateUserDialog onSuccess={refetch} />
      </div>

      <Tabs defaultValue="users" className="space-y-6">
        <TabsList>
          <TabsTrigger value="users">用户列表</TabsTrigger>
          <TabsTrigger value="activity">活动监控</TabsTrigger>
        </TabsList>
        
        <TabsContent value="users" className="space-y-6">
          {usersData?.data.items && (
            <>
              <BulkUserOperations
                users={usersData.data.items}
                selectedUsers={selectedUsers}
                onSelectionChange={setSelectedUsers}
                onOperationComplete={refetch}
              />
              
              <UsersTable
                users={usersData.data.items}
                selectedUsers={selectedUsers}
                onSelectionChange={setSelectedUsers}
                onUpdateStatus={handleUpdateStatus}
                onUpdateAdmin={handleUpdateAdmin}
                onResetKeys={handleResetKeys}
              />
            </>
          )}

          {usersData?.data.pagination && (
            <Pagination
              page={page}
              pageSize={pageSize}
              total={usersData.data.pagination.total}
              onPageChange={setPage}
            />
          )}
        </TabsContent>
        
        <TabsContent value="activity">
          <UserActivityMonitor />
        </TabsContent>
      </Tabs>
    </div>
  )
}
