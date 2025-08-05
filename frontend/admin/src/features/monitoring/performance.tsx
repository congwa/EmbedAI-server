import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Legend
} from 'recharts'
import { 
  Activity, 
  TrendingUp, 
  TrendingDown,
  Zap,
  AlertTriangle,
  RefreshCw,
  Clock,
  Gauge
} from 'lucide-react'
import { adminService } from '@/services/admin'
import { format, subHours, subDays } from 'date-fns'
import { zhCN } from 'date-fns/locale'

// 性能指标卡片组件
interface MetricCardProps {
  title: string
  current: number
  average: number
  unit: string
  icon: React.ReactNode
  trend?: {
    value: number
    isPositive: boolean
  }
}

function MetricCard({ title, current, average, unit, icon, trend }: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{current.toFixed(1)}{unit}</div>
        <p className="text-xs text-muted-foreground">
          平均值: {average.toFixed(1)}{unit}
        </p>
        {trend && (
          <div className="flex items-center mt-2">
            {trend.isPositive ? (
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
            )}
            <span className={`text-xs ${trend.isPositive ? 'text-green-500' : 'text-red-500'}`}>
              {trend.isPositive ? '+' : ''}{trend.value.toFixed(1)}%
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// 服务性能卡片组件
interface ServicePerformanceCardProps {
  service: {
    name: string
    status: 'healthy' | 'warning' | 'critical'
    metrics: {
      response_time: {
        current: number
        average: number
        p95: number
        p99: number
      }
      throughput: {
        requests_per_second: number
        peak_rps: number
      }
      error_rate: {
        current: number
        average: number
      }
      resource_usage: {
        cpu: number
        memory: number
        disk: number
      }
    }
    alerts: Array<{
      type: string
      severity: 'low' | 'medium' | 'high' | 'critical'
      message: string
      timestamp: string
    }>
  }
}

function ServicePerformanceCard({ service }: ServicePerformanceCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800'
      case 'critical':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'destructive'
      case 'high':
        return 'destructive'
      case 'medium':
        return 'secondary'
      case 'low':
        return 'outline'
      default:
        return 'outline'
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{service.name}</CardTitle>
          <Badge className={getStatusColor(service.status)}>
            {service.status === 'healthy' ? '正常' : 
             service.status === 'warning' ? '警告' : '异常'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 响应时间指标 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm font-medium">响应时间</p>
            <p className="text-2xl font-bold">{service.metrics.response_time.current.toFixed(1)}ms</p>
            <p className="text-xs text-muted-foreground">
              P95: {service.metrics.response_time.p95.toFixed(1)}ms | 
              P99: {service.metrics.response_time.p99.toFixed(1)}ms
            </p>
          </div>
          <div>
            <p className="text-sm font-medium">吞吐量</p>
            <p className="text-2xl font-bold">{service.metrics.throughput.requests_per_second.toFixed(1)}</p>
            <p className="text-xs text-muted-foreground">
              峰值: {service.metrics.throughput.peak_rps.toFixed(1)} RPS
            </p>
          </div>
        </div>

        {/* 错误率和资源使用 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm font-medium">错误率</p>
            <p className="text-2xl font-bold text-red-500">{service.metrics.error_rate.current.toFixed(2)}%</p>
            <p className="text-xs text-muted-foreground">
              平均: {service.metrics.error_rate.average.toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-sm font-medium">资源使用</p>
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span>CPU</span>
                <span>{service.metrics.resource_usage.cpu.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-xs">
                <span>内存</span>
                <span>{service.metrics.resource_usage.memory.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-xs">
                <span>磁盘</span>
                <span>{service.metrics.resource_usage.disk.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* 告警信息 */}
        {service.alerts.length > 0 && (
          <div>
            <p className="text-sm font-medium mb-2">活跃告警</p>
            <div className="space-y-2">
              {service.alerts.slice(0, 3).map((alert, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Badge variant={getSeverityColor(alert.severity)} className="text-xs">
                      {alert.severity}
                    </Badge>
                    <span className="text-sm">{alert.message}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {format(new Date(alert.timestamp), 'HH:mm')}
                  </span>
                </div>
              ))}
              {service.alerts.length > 3 && (
                <p className="text-xs text-muted-foreground">
                  还有 {service.alerts.length - 3} 个告警...
                </p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// 主性能监控组件
export function PerformanceMonitoring() {
  const [timeRange, setTimeRange] = useState('1h')
  const [selectedService, setSelectedService] = useState('all')

  // 计算时间范围
  const getTimeRange = () => {
    const now = new Date()
    switch (timeRange) {
      case '1h':
        return { start: subHours(now, 1), end: now }
      case '6h':
        return { start: subHours(now, 6), end: now }
      case '24h':
        return { start: subHours(now, 24), end: now }
      case '7d':
        return { start: subDays(now, 7), end: now }
      default:
        return { start: subHours(now, 1), end: now }
    }
  }

  const { start, end } = getTimeRange()

  const { 
    data: performanceData, 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['performance-monitoring', timeRange, selectedService],
    queryFn: () => adminService.getPerformanceMonitoring({
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      service: selectedService === 'all' ? undefined : selectedService,
    }),
    refetchInterval: 30000, // 30秒自动刷新
  })

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          加载性能监控数据失败，请检查网络连接或稍后重试。
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
        <Skeleton className="h-[400px] w-full" />
      </div>
    )
  }

  const data = performanceData?.data

  if (!data) {
    return (
      <Alert>
        <AlertDescription>
          暂无性能监控数据
        </AlertDescription>
      </Alert>
    )
  }

  // 准备图表数据
  const chartData = data.trends.timestamps.map((timestamp, index) => ({
    time: format(new Date(timestamp), 'HH:mm'),
    responseTime: data.trends.response_times[index],
    throughput: data.trends.throughput[index],
    errorRate: data.trends.error_rates[index],
    cpuUsage: data.trends.cpu_usage[index],
    memoryUsage: data.trends.memory_usage[index],
  }))

  // 计算总体指标
  const totalServices = data.services.length
  const healthyServices = data.services.filter(s => s.status === 'healthy').length
  const warningServices = data.services.filter(s => s.status === 'warning').length
  const criticalServices = data.services.filter(s => s.status === 'critical').length

  return (
    <div className="space-y-6">
      {/* 页面标题和控制 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">性能监控</h1>
          <p className="text-muted-foreground">
            实时监控系统性能指标和服务状态
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">最近1小时</SelectItem>
              <SelectItem value="6h">最近6小时</SelectItem>
              <SelectItem value="24h">最近24小时</SelectItem>
              <SelectItem value="7d">最近7天</SelectItem>
            </SelectContent>
          </Select>
          <Select value={selectedService} onValueChange={setSelectedService}>
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有服务</SelectItem>
              {data.services.map(service => (
                <SelectItem key={service.name} value={service.name}>
                  {service.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      {/* 服务状态概览 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总服务数</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalServices}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">正常服务</CardTitle>
            <div className="h-2 w-2 bg-green-500 rounded-full"></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{healthyServices}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">警告服务</CardTitle>
            <div className="h-2 w-2 bg-yellow-500 rounded-full"></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">{warningServices}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">异常服务</CardTitle>
            <div className="h-2 w-2 bg-red-500 rounded-full"></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{criticalServices}</div>
          </CardContent>
        </Card>
      </div>

      {/* 性能趋势图表 */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* 响应时间和吞吐量 */}
        <Card>
          <CardHeader>
            <CardTitle>响应时间 & 吞吐量</CardTitle>
            <CardDescription>系统响应时间和请求吞吐量趋势</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="responseTime" 
                  stroke="#8884d8" 
                  name="响应时间 (ms)"
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="throughput" 
                  stroke="#82ca9d" 
                  name="吞吐量 (RPS)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 错误率和资源使用 */}
        <Card>
          <CardHeader>
            <CardTitle>错误率 & 资源使用</CardTitle>
            <CardDescription>系统错误率和资源使用率趋势</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="errorRate" 
                  stackId="1"
                  stroke="#ff7300" 
                  fill="#ff7300"
                  name="错误率 (%)"
                />
                <Area 
                  type="monotone" 
                  dataKey="cpuUsage" 
                  stackId="2"
                  stroke="#387908" 
                  fill="#387908"
                  name="CPU使用率 (%)"
                />
                <Area 
                  type="monotone" 
                  dataKey="memoryUsage" 
                  stackId="3"
                  stroke="#1890ff" 
                  fill="#1890ff"
                  name="内存使用率 (%)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 服务详细性能 */}
      <div>
        <h2 className="text-xl font-semibold mb-4">服务性能详情</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.services.map((service) => (
            <ServicePerformanceCard key={service.name} service={service} />
          ))}
        </div>
      </div>
    </div>
  )
}
