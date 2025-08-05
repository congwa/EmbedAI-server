import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { User } from '@/services/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  BarChart3,
  MessageSquare,
  FileText,
  Clock,
  TrendingUp,
  User as UserIcon,
  Calendar,
  Activity,
} from 'lucide-react'

interface UserStatsDialogProps {
  user: User
  children?: React.ReactNode
}

export function UserStatsDialog({ user, children }: UserStatsDialogProps) {
  const [isOpen, setIsOpen] = useState(false)

  // 获取用户聊天统计
  const { data: chatStats, isLoading: loadingChatStats } = useQuery({
    queryKey: ['user-chat-stats', user.id],
    queryFn: () => adminService.getUserChatStats(user.id),
    enabled: isOpen,
  })

  // 模拟用户活动数据（实际项目中应该从API获取）
  const mockActivityData = {
    lastLoginTime: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
    totalApiCalls: Math.floor(Math.random() * 10000) + 100,
    thisMonthApiCalls: Math.floor(Math.random() * 1000) + 50,
    averageResponseTime: Math.floor(Math.random() * 500) + 100,
    errorRate: (Math.random() * 5).toFixed(2),
    favoriteFeatures: ['知识库查询', '文档上传', '聊天对话'],
    deviceInfo: {
      platform: 'Web',
      browser: 'Chrome',
      lastIp: '192.168.1.100',
    },
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getTimeAgo = (dateString: string) => {
    const now = new Date()
    const date = new Date(dateString)
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return '刚刚'
    if (diffInMinutes < 60) return `${diffInMinutes}分钟前`
    
    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `${diffInHours}小时前`
    
    const diffInDays = Math.floor(diffInHours / 24)
    if (diffInDays < 7) return `${diffInDays}天前`
    
    return formatDate(dateString)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button variant="outline" size="sm">
            <BarChart3 className="mr-2 h-4 w-4" />
            查看统计
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserIcon className="h-5 w-5" />
            用户统计 - {user.email}
          </DialogTitle>
          <DialogDescription>
            查看用户的活动统计和使用模式
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* 基本信息 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">基本信息</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">用户ID</div>
                  <div className="font-medium">{user.id}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">邮箱</div>
                  <div className="font-medium truncate">{user.email}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">角色</div>
                  <Badge variant={user.is_admin ? 'default' : 'secondary'}>
                    {user.is_admin ? '管理员' : '普通用户'}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">状态</div>
                  <Badge variant={user.is_active ? 'success' : 'destructive'}>
                    {user.is_active ? '已启用' : '已禁用'}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">创建时间</div>
                  <div className="font-medium">{formatDate(user.created_at)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">最后登录</div>
                  <div className="font-medium">{getTimeAgo(mockActivityData.lastLoginTime)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">创建者</div>
                  <div className="font-medium">管理员 #{user.created_by_id}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 聊天统计 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                聊天统计
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingChatStats ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : chatStats?.data ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">{chatStats.data.total_chats}</div>
                    <div className="text-sm text-muted-foreground">总聊天数</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{chatStats.data.active_chats}</div>
                    <div className="text-sm text-muted-foreground">活跃聊天</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{chatStats.data.total_messages}</div>
                    <div className="text-sm text-muted-foreground">总消息数</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {chatStats.data.avg_messages_per_chat.toFixed(1)}
                    </div>
                    <div className="text-sm text-muted-foreground">平均消息/聊天</div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  暂无聊天统计数据
                </div>
              )}
            </CardContent>
          </Card>

          {/* API 使用统计 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                API 使用统计
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">{mockActivityData.totalApiCalls.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">总调用次数</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{mockActivityData.thisMonthApiCalls.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">本月调用</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{mockActivityData.averageResponseTime}ms</div>
                  <div className="text-sm text-muted-foreground">平均响应时间</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{mockActivityData.errorRate}%</div>
                  <div className="text-sm text-muted-foreground">错误率</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 使用模式 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 常用功能 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  常用功能
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {mockActivityData.favoriteFeatures.map((feature, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm">{feature}</span>
                      <Badge variant="outline">{Math.floor(Math.random() * 100) + 10}次</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* 设备信息 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  设备信息
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">平台</span>
                    <span className="text-sm font-medium">{mockActivityData.deviceInfo.platform}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">浏览器</span>
                    <span className="text-sm font-medium">{mockActivityData.deviceInfo.browser}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">最后IP</span>
                    <span className="text-sm font-medium font-mono">{mockActivityData.deviceInfo.lastIp}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 密钥信息 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                API 密钥信息
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-muted-foreground mb-2">SDK 密钥</div>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 p-2 bg-muted rounded text-sm font-mono break-all">
                      {user.sdk_key}
                    </code>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigator.clipboard.writeText(user.sdk_key)}
                    >
                      复制
                    </Button>
                  </div>
                </div>
                
                <Separator />
                
                <div>
                  <div className="text-sm text-muted-foreground mb-2">Secret 密钥</div>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 p-2 bg-muted rounded text-sm font-mono break-all">
                      {user.secret_key}
                    </code>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigator.clipboard.writeText(user.secret_key)}
                    >
                      复制
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  )
}