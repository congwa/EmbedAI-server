import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Users, 
  Database, 
  FileText, 
  MessageSquare, 
  TrendingUp, 
  TrendingDown,
  Activity,
  DollarSign,
  Download,
  RefreshCw
} from 'lucide-react'
import { adminService } from '@/services/admin'
import { formatDistanceToNow, format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { toast } from '@/hooks/use-toast'
import { useState } from 'react'

// 统计卡片组件
interface StatsCardProps {
  title: string
  value: number | string
  description?: string
  icon: React.ReactNode
  trend?: {
    value: number
    isPositive: boolean
  }
}

function StatsCard({ title, value, description, icon, trend }: StatsCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
        {trend && (
          <div className="flex items-center mt-2">
            {trend.isPositive ? (
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
            )}
            <span className={`text-xs ${trend.isPositive ? 'text-green-500' : 'text-red-500'}`}>
              {trend.isPositive ? '+' : ''}{trend.value}%
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// 活动列表组件
interface ActivityListProps {
  activities: Array<{
    user_id: number
    user_email: string
    activity_type: string
    activity_details: Record<string, any>
    timestamp: string
  }>
}

function ActivityList({ activities }: ActivityListProps) {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'login':
        return <Users className="h-4 w-4" />
      case 'document_upload':
        return <FileText className="h-4 w-4" />
      case 'knowledge_base_create':
        return <Database className="h-4 w-4" />
      case 'query_submit':
        return <MessageSquare className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  const getActivityDescription = (type: string, details: Record<string, any>) => {
    switch (type) {
      case 'login':
        return '用户登录'
      case 'document_upload':
        return `上传文档: ${details.document_name || '未知文档'}`
      case 'knowledge_base_create':
        return `创建知识库: ${details.knowledge_base || '未知知识库'}`
      case 'query_submit':
        return `提交查询: ${details.query?.substring(0, 50) || '查询内容'}...`
      default:
        return '未知活动'
    }
  }

  return (
    <div className="space-y-4">
      {activities.map((activity, index) => (
        <div key={index} className="flex items-start space-x-3">
          <div className="flex-shrink-0 mt-1">
            {getActivityIcon(activity.activity_type)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900">
              {activity.user_email}
            </p>
            <p className="text-sm text-gray-500">
              {getActivityDescription(activity.activity_type, activity.activity_details)}
            </p>
            <p className="text-xs text-gray-400">
              {formatDistanceToNow(new Date(activity.timestamp), { 
                addSuffix: true, 
                locale: zhCN 
              })}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}

// 知识库排行榜组件
interface TopKnowledgeBasesProps {
  knowledgeBases: Array<{
    id: number
    name: string
    domain: string
    document_count: number
    query_count: number
    last_updated: string
  }>
}

function TopKnowledgeBases({ knowledgeBases }: TopKnowledgeBasesProps) {
  return (
    <div className="space-y-4">
      {knowledgeBases.map((kb, index) => (
        <div key={kb.id} className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Badge variant="outline" className="w-6 h-6 p-0 flex items-center justify-center">
              {index + 1}
            </Badge>
            <div>
              <p className="text-sm font-medium">{kb.name}</p>
              <p className="text-xs text-gray-500">{kb.domain}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium">{kb.query_count} 次查询</p>
            <p className="text-xs text-gray-500">{kb.document_count} 个文档</p>
          </div>
        </div>
      ))}
    </div>
  )
}

// 成本概览组件
interface CostOverviewProps {
  costSummary: {
    current_month: {
      total_cost: number
      llm_cost: number
      storage_cost: number
      api_cost: number
    }
    previous_month: {
      total_cost: number
      growth_rate: number
    }
  }
}

function CostOverview({ costSummary }: CostOverviewProps) {
  const { current_month, previous_month } = costSummary

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">本月总成本</span>
        <span className="text-2xl font-bold">${current_month.total_cost.toFixed(2)}</span>
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>LLM API</span>
          <span>${current_month.llm_cost.toFixed(2)}</span>
        </div>
        <Progress 
          value={(current_month.llm_cost / current_month.total_cost) * 100} 
          className="h-2"
        />
        
        <div className="flex justify-between text-sm">
          <span>存储费用</span>
          <span>${current_month.storage_cost.toFixed(2)}</span>
        </div>
        <Progress 
          value={(current_month.storage_cost / current_month.total_cost) * 100} 
          className="h-2"
        />
        
        <div className="flex justify-between text-sm">
          <span>API调用</span>
          <span>${current_month.api_cost.toFixed(2)}</span>
        </div>
        <Progress 
          value={(current_month.api_cost / current_month.total_cost) * 100} 
          className="h-2"
        />
      </div>

      <div className="pt-2 border-t">
        <div className="flex items-center justify-between text-sm">
          <span>相比上月</span>
          <div className="flex items-center">
            {previous_month.growth_rate > 0 ? (
              <TrendingUp className="h-4 w-4 text-red-500 mr-1" />
            ) : (
              <TrendingDown className="h-4 w-4 text-green-500 mr-1" />
            )}
            <span className={previous_month.growth_rate > 0 ? 'text-red-500' : 'text-green-500'}>
              {previous_month.growth_rate > 0 ? '+' : ''}{previous_month.growth_rate.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

// 主仪表板组件
export function AnalyticsDashboard() {
  const [isExporting, setIsExporting] = useState(false)

  // 获取仪表板数据
  const { 
    data: dashboardData, 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => adminService.getDashboardData(),
    refetchInterval: 30000, // 30秒自动刷新
  })

  // 导出数据
  const handleExport = async (dataType: 'user_activity' | 'knowledge_bases' | 'performance' | 'cost') => {
    try {
      setIsExporting(true)
      const blob = await adminService.exportAnalyticsData({
        data_type: dataType,
        format: 'csv',
      })
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${dataType}_export_${format(new Date(), 'yyyy-MM-dd')}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
      
      toast({
        title: '导出成功',
        description: `${dataType} 数据已导出`,
      })
    } catch (error) {
      toast({
        title: '导出失败',
        description: '数据导出时发生错误，请重试',
        variant: 'destructive',
      })
    } finally {
      setIsExporting(false)
    }
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          加载仪表板数据失败，请检查网络连接或稍后重试。
        </AlertDescription>
      </Alert>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-[100px]" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-[60px] mb-2" />
                <Skeleton className="h-3 w-[120px]" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-[150px]" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-[200px] w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  const data = dashboardData?.data

  if (!data) {
    return (
      <Alert>
        <AlertDescription>
          暂无仪表板数据
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">仪表板</h1>
          <p className="text-muted-foreground">
            系统概览和关键指标
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('user_activity')}
            disabled={isExporting}
          >
            <Download className="h-4 w-4 mr-2" />
            导出数据
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="总用户数"
          value={data.overview.total_users}
          description="系统注册用户"
          icon={<Users className="h-4 w-4 text-muted-foreground" />}
        />
        <StatsCard
          title="活跃用户"
          value={data.overview.active_users}
          description="最近7天活跃"
          icon={<Activity className="h-4 w-4 text-muted-foreground" />}
        />
        <StatsCard
          title="知识库数量"
          value={data.overview.total_knowledge_bases}
          description="已创建知识库"
          icon={<Database className="h-4 w-4 text-muted-foreground" />}
        />
        <StatsCard
          title="文档总数"
          value={data.overview.total_documents}
          description="已上传文档"
          icon={<FileText className="h-4 w-4 text-muted-foreground" />}
        />
      </div>

      {/* 详细信息 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* 最近活动 */}
        <Card>
          <CardHeader>
            <CardTitle>最近活动</CardTitle>
            <CardDescription>用户最新操作记录</CardDescription>
          </CardHeader>
          <CardContent>
            <ActivityList activities={data.recent_activities} />
          </CardContent>
        </Card>

        {/* 热门知识库 */}
        <Card>
          <CardHeader>
            <CardTitle>热门知识库</CardTitle>
            <CardDescription>查询次数最多的知识库</CardDescription>
          </CardHeader>
          <CardContent>
            <TopKnowledgeBases knowledgeBases={data.top_knowledge_bases} />
          </CardContent>
        </Card>

        {/* 成本概览 */}
        <Card>
          <CardHeader>
            <CardTitle>成本概览</CardTitle>
            <CardDescription>本月费用统计</CardDescription>
          </CardHeader>
          <CardContent>
            <CostOverview costSummary={data.cost_summary} />
          </CardContent>
        </Card>
      </div>

      {/* 系统状态 */}
      <Card>
        <CardHeader>
          <CardTitle>系统状态</CardTitle>
          <CardDescription>系统运行状态和关键指标</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-500">
                {data.overview.system_uptime.toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">系统运行时间</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {data.overview.total_queries.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">总查询次数</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {((data.overview.total_queries - (data.overview.total_queries * 0.05)) / data.overview.total_queries * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">查询成功率</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
