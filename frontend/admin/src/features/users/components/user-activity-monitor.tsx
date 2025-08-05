import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Activity,
  Users,
  MessageSquare,
  Clock,
  TrendingUp,
  RefreshCw,
  AlertCircle,
  CheckCircle,
} from 'lucide-react'

interface UserActivityData {
  online_users: number
  total_users: number
  active_chats: number
  messages_last_hour: number
  api_calls_last_hour: number
  error_rate: number
  avg_response_time: number
  recent_activities: Array<{
    user_id: number
    user_email: string
    activity_type: 'login' | 'chat' | 'api_call' | 'logout'
    timestamp: string
    details?: string
  }>
}

export function UserActivityMonitor() {
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30000) // 30秒

  // 获取用户活动数据
  const { data: activityData, isLoading, refetch } = useQuery({
    queryKey: ['user-activity-monitor'],
    queryFn: async (): Promise<{ data: UserActivityData }> => {
      // 模拟API调用，实际项目中应该调用真实的API
      await new Promise(resolve => setTimeout(resolve, 500))
      
      return {
        data: {
          online_users: Math.floor(Math.random() * 50) + 10,
          total_users: Math.floor(Math.random() * 200) + 100,
          active_chats: Math.floor(Math.random() * 30) + 5,
          messages_last_hour: Math.floor(Math.random() * 500) + 100,
          api_calls_last_hour: Math.floor(Math.random() * 1000) + 200,
          error_rate: Math.random() * 5,
          avg_response_time: Math.floor(Math.random() * 300) + 100,
          recent_activities: Array.from({ length: 10 }, (_, i) => ({
            user_id: Math.floor(Math.random() * 100) + 1,
            user_email: `user${Math.floor(Math.random() * 100)}@example.com`,
            activity_type: ['login', 'chat', 'api_call', 'logout'][Math.floor(Math.random() * 4)] as any,
            timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
            details: Math.random() > 0.5 ? '成功' : undefined,
          })),
        }
      }
    },
    refetchInterval: autoRefresh ? refreshInterval : false,
  })

  const formatTime = (timestamp: string) => {
    const now = new Date()
    const time = new Date(timestamp)
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return '刚刚'
    if (diffInMinutes < 60) return `${diffInMinutes}分钟前`
    
    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `${diffInHours}小时前`
    
    return time.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'login':
        return <CheckCircle className=\"h-3 w-3 text-green-500\" />
      case 'logout':
        return <AlertCircle className=\"h-3 w-3 text-gray-500\" />
      case 'chat':
        return <MessageSquare className=\"h-3 w-3 text-blue-500\" />
      case 'api_call':
        return <Activity className=\"h-3 w-3 text-purple-500\" />
      default:
        return <Activity className=\"h-3 w-3\" />
    }
  }

  const getActivityLabel = (type: string) => {
    switch (type) {
      case 'login':
        return '登录'
      case 'logout':
        return '登出'
      case 'chat':
        return '聊天'
      case 'api_call':
        return 'API调用'
      default:
        return '未知'
    }
  }

  const stats = activityData?.data

  return (
    <div className=\"space-y-6\">
      {/* 控制面板 */}
      <div className=\"flex items-center justify-between\">
        <h3 className=\"text-lg font-semibold flex items-center gap-2\">
          <Activity className=\"h-5 w-5\" />
          用户活动监控
        </h3>
        <div className=\"flex items-center gap-2\">
          <Button
            variant=\"outline\"
            size=\"sm\"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            size=\"sm\"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '停止自动刷新' : '开启自动刷新'}
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className=\"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4\">
        <Card>
          <CardHeader className=\"flex flex-row items-center justify-between space-y-0 pb-2\">
            <CardTitle className=\"text-sm font-medium\">在线用户</CardTitle>
            <Users className=\"h-4 w-4 text-muted-foreground\" />
          </CardHeader>
          <CardContent>
            <div className=\"text-2xl font-bold text-green-600\">
              {stats?.online_users || 0}
            </div>
            <p className=\"text-xs text-muted-foreground\">
              总用户数: {stats?.total_users || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className=\"flex flex-row items-center justify-between space-y-0 pb-2\">
            <CardTitle className=\"text-sm font-medium\">活跃聊天</CardTitle>
            <MessageSquare className=\"h-4 w-4 text-muted-foreground\" />
          </CardHeader>
          <CardContent>
            <div className=\"text-2xl font-bold text-blue-600\">
              {stats?.active_chats || 0}
            </div>
            <p className=\"text-xs text-muted-foreground\">
              当前进行中的聊天会话
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className=\"flex flex-row items-center justify-between space-y-0 pb-2\">
            <CardTitle className=\"text-sm font-medium\">每小时消息</CardTitle>
            <TrendingUp className=\"h-4 w-4 text-muted-foreground\" />
          </CardHeader>
          <CardContent>
            <div className=\"text-2xl font-bold text-purple-600\">
              {stats?.messages_last_hour || 0}
            </div>
            <p className=\"text-xs text-muted-foreground\">
              过去一小时的消息数
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className=\"flex flex-row items-center justify-between space-y-0 pb-2\">
            <CardTitle className=\"text-sm font-medium\">平均响应时间</CardTitle>
            <Clock className=\"h-4 w-4 text-muted-foreground\" />
          </CardHeader>
          <CardContent>
            <div className=\"text-2xl font-bold text-orange-600\">
              {stats?.avg_response_time || 0}ms
            </div>
            <p className=\"text-xs text-muted-foreground\">
              错误率: {stats?.error_rate?.toFixed(2) || 0}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 最近活动 */}
      <Card>
        <CardHeader>
          <CardTitle className=\"flex items-center gap-2\">
            <Clock className=\"h-5 w-5\" />
            最近活动
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className=\"flex items-center justify-center py-8\">
              <div className=\"animate-spin rounded-full h-8 w-8 border-b-2 border-primary\"></div>
            </div>
          ) : stats?.recent_activities && stats.recent_activities.length > 0 ? (
            <div className=\"space-y-3\">
              {stats.recent_activities.map((activity, index) => (
                <div key={index} className=\"flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50\">
                  <div className=\"flex-shrink-0\">
                    {getActivityIcon(activity.activity_type)}
                  </div>
                  <div className=\"flex-1 min-w-0\">
                    <div className=\"flex items-center gap-2\">
                      <span className=\"text-sm font-medium truncate\">
                        {activity.user_email}
                      </span>
                      <Badge variant=\"outline\" className=\"text-xs\">
                        {getActivityLabel(activity.activity_type)}
                      </Badge>
                    </div>
                    <div className=\"flex items-center gap-2 mt-1\">
                      <span className=\"text-xs text-muted-foreground\">
                        用户ID: {activity.user_id}
                      </span>
                      <span className=\"text-xs text-muted-foreground\">
                        {formatTime(activity.timestamp)}
                      </span>
                      {activity.details && (
                        <Badge variant=\"secondary\" className=\"text-xs\">
                          {activity.details}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className=\"text-center py-8 text-muted-foreground\">
              <Activity className=\"h-8 w-8 mx-auto mb-2 opacity-50\" />
              <p className=\"text-sm\">暂无最近活动</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 系统状态指示器 */}
      <Card>
        <CardHeader>
          <CardTitle>系统状态</CardTitle>
        </CardHeader>
        <CardContent>
          <div className=\"grid grid-cols-1 md:grid-cols-3 gap-4\">
            <div className=\"flex items-center gap-3\">
              <div className={`w-3 h-3 rounded-full ${
                (stats?.error_rate || 0) < 1 ? 'bg-green-500' : 
                (stats?.error_rate || 0) < 5 ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <div>
                <div className=\"text-sm font-medium\">API状态</div>
                <div className=\"text-xs text-muted-foreground\">
                  {(stats?.error_rate || 0) < 1 ? '正常' : 
                   (stats?.error_rate || 0) < 5 ? '警告' : '异常'}
                </div>
              </div>
            </div>
            
            <div className=\"flex items-center gap-3\">
              <div className={`w-3 h-3 rounded-full ${
                (stats?.avg_response_time || 0) < 200 ? 'bg-green-500' : 
                (stats?.avg_response_time || 0) < 500 ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <div>
                <div className=\"text-sm font-medium\">响应速度</div>
                <div className=\"text-xs text-muted-foreground\">
                  {(stats?.avg_response_time || 0) < 200 ? '快速' : 
                   (stats?.avg_response_time || 0) < 500 ? '正常' : '缓慢'}
                </div>
              </div>
            </div>
            
            <div className=\"flex items-center gap-3\">
              <div className={`w-3 h-3 rounded-full ${
                (stats?.online_users || 0) > 0 ? 'bg-green-500' : 'bg-gray-500'
              }`} />
              <div>
                <div className=\"text-sm font-medium\">用户活跃度</div>
                <div className=\"text-xs text-muted-foreground\">
                  {(stats?.online_users || 0) > 0 ? '活跃' : '无活动'}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}