import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { User } from '@/services/types'
import { BulkOperations, userBulkActions, BulkSelectableRow } from '@/components/bulk-operations'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { useNotification } from '@/hooks/use-notification'

interface BulkUserOperationsProps {
  users: User[]
  className?: string
}

export function BulkUserOperations({ users, className }: BulkUserOperationsProps) {
  const [selectedUsers, setSelectedUsers] = useState<User[]>([])
  const queryClient = useQueryClient()
  const notification = useNotification()

  // 批量操作处理函数
  const handleBulkAction = async (actionId: string, users: User[]) => {
    const user = users[0] // 单个用户操作

    switch (actionId) {
      case 'activate':
        await adminService.updateUserStatus(user.id, true)
        break
      
      case 'deactivate':
        await adminService.updateUserStatus(user.id, false)
        break
      
      case 'reset_keys':
        await adminService.resetUserKeys(user.id)
        break
      
      case 'delete':
        // 这里需要添加删除用户的API方法
        throw new Error('删除用户功能暂未实现')
      
      default:
        throw new Error(`未知操作: ${actionId}`)
    }

    // 刷新用户列表
    queryClient.invalidateQueries({ queryKey: ['users'] })
  }

  const getUserInitials = (email: string) => {
    return email.slice(0, 2).toUpperCase()
  }

  const getUserStatusBadge = (user: User) => {
    if (!user.is_active) {
      return <Badge variant="destructive">已禁用</Badge>
    }
    if (user.is_admin) {
      return <Badge variant="default">管理员</Badge>
    }
    return <Badge variant="secondary">普通用户</Badge>
  }

  return (
    <div className={className}>
      <BulkOperations
        items={users}
        selectedItems={selectedUsers}
        onSelectionChange={setSelectedUsers}
        actions={userBulkActions}
        onAction={handleBulkAction}
        getItemId={(user) => user.id}
        getItemLabel={(user) => user.email}
        className="mb-4"
      />

      {/* 用户列表 */}
      <div className="space-y-2">
        {users.map((user) => {
          const isSelected = selectedUsers.some(selected => selected.id === user.id)
          
          return (
            <BulkSelectableRow
              key={user.id}
              selected={isSelected}
              onToggle={() => {
                if (isSelected) {
                  setSelectedUsers(selectedUsers.filter(u => u.id !== user.id))
                } else {
                  setSelectedUsers([...selectedUsers, user])
                }
              }}
            >
              <div className="flex items-center gap-4">
                <Avatar className="h-10 w-10">
                  <AvatarFallback className="text-sm">
                    {getUserInitials(user.email)}
                  </AvatarFallback>
                </Avatar>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-sm truncate">{user.email}</h3>
                    {getUserStatusBadge(user)}
                  </div>
                  
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>ID: {user.id}</span>
                    <span>
                      创建于 {formatDistanceToNow(new Date(user.created_at), {
                        addSuffix: true,
                        locale: zhCN,
                      })}
                    </span>
                    {user.last_login && (
                      <span>
                        最后登录 {formatDistanceToNow(new Date(user.last_login), {
                          addSuffix: true,
                          locale: zhCN,
                        })}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </BulkSelectableRow>
          )
        })}
      </div>
    </div>
  )
}

// 用户批量导入组件
interface BulkUserImportProps {
  onImport: (users: Partial<User>[]) => Promise<void>
  className?: string
}

export function BulkUserImport({ onImport, className }: BulkUserImportProps) {
  const [isImporting, setIsImporting] = useState(false)
  const [importResults, setImportResults] = useState<{
    success: number
    failed: number
    errors: string[]
  } | null>(null)
  const notification = useNotification()

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.csv')) {
      notification.error('文件格式错误', '请上传CSV格式的文件')
      return
    }

    setIsImporting(true)
    setImportResults(null)

    try {
      const text = await file.text()
      const lines = text.split('\n').filter(line => line.trim())
      const headers = lines[0].split(',').map(h => h.trim())
      
      if (!headers.includes('email')) {
        throw new Error('CSV文件必须包含email列')
      }

      const users: Partial<User>[] = []
      const errors: string[] = []

      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim())
        const user: Partial<User> = {}

        headers.forEach((header, index) => {
          const value = values[index]
          switch (header) {
            case 'email':
              if (!value || !value.includes('@')) {
                errors.push(`第${i + 1}行: 邮箱格式无效`)
                return
              }
              user.email = value
              break
            case 'is_admin':
              user.is_admin = value.toLowerCase() === 'true'
              break
            case 'is_active':
              user.is_active = value.toLowerCase() !== 'false'
              break
          }
        })

        if (user.email) {
          users.push(user)
        }
      }

      if (errors.length > 0) {
        setImportResults({
          success: 0,
          failed: errors.length,
          errors,
        })
        return
      }

      // 执行导入
      let successCount = 0
      const importErrors: string[] = []

      for (const user of users) {
        try {
          await onImport([user])
          successCount++
        } catch (error) {
          importErrors.push(`${user.email}: ${error instanceof Error ? error.message : '导入失败'}`)
        }
      }

      setImportResults({
        success: successCount,
        failed: importErrors.length,
        errors: importErrors,
      })

      if (importErrors.length === 0) {
        notification.success('批量导入完成', `成功导入 ${successCount} 个用户`)
      } else {
        notification.warning('批量导入完成', `成功 ${successCount} 个，失败 ${importErrors.length} 个`)
      }
    } catch (error) {
      notification.error('导入失败', error instanceof Error ? error.message : '未知错误')
    } finally {
      setIsImporting(false)
      // 清除文件输入
      event.target.value = ''
    }
  }

  return (
    <div className={className}>
      <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-6 text-center">
        <div className="space-y-4">
          <div>
            <h3 className="font-medium">批量导入用户</h3>
            <p className="text-sm text-muted-foreground mt-1">
              上传CSV文件批量创建用户账户
            </p>
          </div>
          
          <div>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              disabled={isImporting}
              className="hidden"
              id="bulk-import-file"
            />
            <label
              htmlFor="bulk-import-file"
              className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 cursor-pointer"
            >
              {isImporting ? '导入中...' : '选择CSV文件'}
            </label>
          </div>
          
          <div className="text-xs text-muted-foreground">
            <p>CSV格式要求：</p>
            <p>必需列：email</p>
            <p>可选列：is_admin (true/false), is_active (true/false)</p>
          </div>
        </div>
      </div>

      {/* 导入结果 */}
      {importResults && (
        <div className="mt-4 p-4 border rounded-lg">
          <h4 className="font-medium mb-2">导入结果</h4>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="text-center p-2 bg-green-50 text-green-700 rounded">
              <div className="font-medium">成功</div>
              <div className="text-lg">{importResults.success}</div>
            </div>
            <div className="text-center p-2 bg-red-50 text-red-700 rounded">
              <div className="font-medium">失败</div>
              <div className="text-lg">{importResults.failed}</div>
            </div>
          </div>
          
          {importResults.errors.length > 0 && (
            <div>
              <h5 className="font-medium text-sm mb-2">错误详情：</h5>
              <div className="max-h-32 overflow-y-auto space-y-1">
                {importResults.errors.map((error, index) => (
                  <div key={index} className="text-xs text-red-600 bg-red-50 p-2 rounded">
                    {error}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}