import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DatePickerWithRange } from '@/components/ui/date-range-picker'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts'
import { 
  Users, 
  Database, 
  Activity, 
  TrendingUp, 
  Download,
  Calendar,
  Filter
} from 'lucide-react'
import { adminService } from '@/services/admin'
import { format, subDays } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { toast } from '@/hooks/use-toast'
import type { DateRange } from 'react-day-picker'

// 颜色配置
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

// 用户活动报告组件
function UserActivityReport() {
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: subDays(new Date(), 7),
    to: new Date(),
  })
  const [activityType, setActivityType] = useState<string>('all')

  const { data, isLoading, error } = useQuery({
    queryKey: ['user-activity-stats', dateRange, activityType],
    queryFn: () => adminService.getUserActivityStats({
      start_date: dateRange?.from ? format(dateRange.from, 'yyyy-MM-dd') : undefined,
      end_date: dateRange?.to ? format(dateRange.to, 'yyyy-MM-dd') : undefined,
      activity_type: activityType === 'all' ? undefined : activityType,
      limit: 100,
    }),
    enabled: !!dateRange?.from && !!dateRange?.to,
  })

  const handleExport = async () => {
    try {
      const blob = await adminService.exportAnalyticsData({
        data_type: 'user_activity',
        format: 'csv',
        start_date: dateRange?.from ? format(dateRange.from, 'yyyy-MM-dd') : undefined,
        end_date: dateRange?.to ? format(dateRange.to, 'yyyy-MM-dd') : undefined,
        filters: activityType === 'all' ? {} : { activity_type: activityType },
      })
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `user_activity_${format(new Date(), 'yyyy-MM-dd')}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
      
      toast({
        title: '导出成功',
        description: '用户活动数据已导出',
      })
    } catch (error) {
      toast({
        title: '导出失败',
        description: '数据导出时发生错误，请重试',
        variant: 'destructive',
      })
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-[200px] w-full" />
        <Skeleton className="h-[300px] w-full" />
      </div>
    )
  }

  if (error || !data?.data) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          加载用户活动数据失败，请重试。
        </AlertDescription>
      </Alert>
    )
  }

  const stats = data.data

  // 准备图表数据
  const dailyTrendsData = stats.daily_trends.map(trend => ({
    date: format(new Date(trend.date), 'MM/dd'),
    activities: trend.total_activities,
    users: trend.unique_users,
  }))

  const activityBreakdownData = Object.entries(stats.activity_breakdown).map(([type, count]) => ({
    name: type,
    value: count,
  }))

  return (
    <div className="space-y-6">
      {/* 控制面板 */}
      <div className="flex flex-col sm:flex-row gap-4">
        <DatePickerWithRange
          date={dateRange}
          onDateChange={setDateRange}
        />
        <Select value={activityType} onValueChange={setActivityType}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="选择活动类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有活动</SelectItem>
            <SelectItem value="login">登录</SelectItem>
            <SelectItem value="document_upload">文档上传</SelectItem>
            <SelectItem value="knowledge_base_create">创建知识库</SelectItem>
            <SelectItem value="query_submit">提交查询</SelectItem>
          </SelectContent>
        </Select>
        <Button onClick={handleExport} variant="outline">
          <Download className="h-4 w-4 mr-2" />
          导出数据
        </Button>
      </div>

      {/* 统计概览 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总活动数</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.summary.total_activities}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活跃用户</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.summary.unique_users}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">最活跃用户</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">{stats.summary.most_active_user.email}</div>
            <div className="text-xs text-muted-foreground">
              {stats.summary.most_active_user.activity_count} 次活动
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 图表 */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* 每日趋势 */}
        <Card>
          <CardHeader>
            <CardTitle>每日活动趋势</CardTitle>
            <CardDescription>活动数量和用户数量的每日变化</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyTrendsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="activities" 
                  stroke="#8884d8" 
                  name="活动数量"
                />
                <Line 
                  type="monotone" 
                  dataKey="users" 
                  stroke="#82ca9d" 
                  name="用户数量"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 活动类型分布 */}
        <Card>
          <CardHeader>
            <CardTitle>活动类型分布</CardTitle>
            <CardDescription>不同类型活动的数量分布</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={activityBreakdownData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {activityBreakdownData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 最近活动列表 */}
      <Card>
        <CardHeader>
          <CardTitle>最近活动</CardTitle>
          <CardDescription>用户最新操作记录</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {stats.recent_activities.slice(0, 10).map((activity) => (
              <div key={activity.id} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Badge variant="outline">{activity.activity_type}</Badge>
                  <div>
                    <p className="text-sm font-medium">{activity.user_email}</p>
                    <p className="text-xs text-muted-foreground">
                      {format(new Date(activity.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">
                    耗时: {activity.duration}ms
                  </p>
                  <p className="text-xs text-muted-foreground">
                    IP: {activity.ip_address}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 知识库统计报告组件
function KnowledgeBaseReport() {
  const [period, setPeriod] = useState('7d')
  const [sortBy, setSortBy] = useState('query_count')

  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge-base-stats', period, sortBy],
    queryFn: () => adminService.getKnowledgeBaseStats({
      period,
      sort_by: sortBy,
      limit: 20,
    }),
  })

  const handleExport = async () => {
    try {
      const blob = await adminService.exportAnalyticsData({
        data_type: 'knowledge_bases',
        format: 'csv',
        filters: { period, sort_by: sortBy },
      })
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `knowledge_bases_${format(new Date(), 'yyyy-MM-dd')}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
      
      toast({
        title: '导出成功',
        description: '知识库数据已导出',
      })
    } catch (error) {
      toast({
        title: '导出失败',
        description: '数据导出时发生错误，请重试',
        variant: 'destructive',
      })
    }
  }

  if (isLoading) {
    return <Skeleton className="h-[400px] w-full" />
  }

  if (error || !data?.data) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          加载知识库统计数据失败，请重试。
        </AlertDescription>
      </Alert>
    )
  }

  const stats = data.data

  // 准备图表数据
  const usageTrendsData = stats.usage_trends.dates.map((date, index) => ({
    date: format(new Date(date), 'MM/dd'),
    queries: stats.usage_trends.query_counts[index],
    accuracy: stats.usage_trends.accuracy_rates[index],
  }))

  return (
    <div className="space-y-6">
      {/* 控制面板 */}
      <div className="flex flex-col sm:flex-row gap-4">
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="选择时间周期" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">最近7天</SelectItem>
            <SelectItem value="30d">最近30天</SelectItem>
            <SelectItem value="90d">最近90天</SelectItem>
          </SelectContent>
        </Select>
        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="排序方式" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="query_count">按查询次数</SelectItem>
            <SelectItem value="accuracy_rate">按准确率</SelectItem>
            <SelectItem value="document_count">按文档数量</SelectItem>
          </SelectContent>
        </Select>
        <Button onClick={handleExport} variant="outline">
          <Download className="h-4 w-4 mr-2" />
          导出数据
        </Button>
      </div>

      {/* 统计概览 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">知识库总数</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.summary.total_knowledge_bases}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活跃知识库</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.summary.active_knowledge_bases}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总查询次数</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.summary.total_queries}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均准确率</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.summary.average_accuracy.toFixed(1)}%</div>
          </CardContent>
        </Card>
      </div>

      {/* 使用趋势图表 */}
      <Card>
        <CardHeader>
          <CardTitle>使用趋势</CardTitle>
          <CardDescription>查询次数和准确率的时间趋势</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={usageTrendsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="queries" fill="#8884d8" name="查询次数" />
              <Line 
                yAxisId="right" 
                type="monotone" 
                dataKey="accuracy" 
                stroke="#82ca9d" 
                name="准确率 (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 热门知识库列表 */}
      <Card>
        <CardHeader>
          <CardTitle>热门知识库</CardTitle>
          <CardDescription>按{sortBy === 'query_count' ? '查询次数' : sortBy === 'accuracy_rate' ? '准确率' : '文档数量'}排序</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {stats.top_knowledge_bases.map((kb, index) => (
              <div key={kb.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <Badge variant="outline" className="w-8 h-8 p-0 flex items-center justify-center">
                    {index + 1}
                  </Badge>
                  <div>
                    <p className="font-medium">{kb.name}</p>
                    <p className="text-sm text-muted-foreground">{kb.domain}</p>
                  </div>
                </div>
                <div className="text-right space-y-1">
                  <div className="flex items-center space-x-4">
                    <div className="text-center">
                      <p className="text-sm font-medium">{kb.query_count}</p>
                      <p className="text-xs text-muted-foreground">查询次数</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm font-medium">{kb.accuracy_rate.toFixed(1)}%</p>
                      <p className="text-xs text-muted-foreground">准确率</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm font-medium">{kb.document_count}</p>
                      <p className="text-xs text-muted-foreground">文档数</p>
                    </div>
                  </div>
                  <Progress value={kb.accuracy_rate} className="w-24 h-2" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 主报告组件
export function AnalyticsReports() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">分析报告</h1>
        <p className="text-muted-foreground">
          详细的数据分析和统计报告
        </p>
      </div>

      <Tabs defaultValue="user-activity" className="space-y-4">
        <TabsList>
          <TabsTrigger value="user-activity">用户活动</TabsTrigger>
          <TabsTrigger value="knowledge-bases">知识库统计</TabsTrigger>
          <TabsTrigger value="performance">性能指标</TabsTrigger>
          <TabsTrigger value="cost">成本分析</TabsTrigger>
        </TabsList>

        <TabsContent value="user-activity" className="space-y-4">
          <UserActivityReport />
        </TabsContent>

        <TabsContent value="knowledge-bases" className="space-y-4">
          <KnowledgeBaseReport />
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="text-center py-8">
            <p className="text-muted-foreground">性能指标报告开发中...</p>
          </div>
        </TabsContent>

        <TabsContent value="cost" className="space-y-4">
          <div className="text-center py-8">
            <p className="text-muted-foreground">成本分析报告开发中...</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
