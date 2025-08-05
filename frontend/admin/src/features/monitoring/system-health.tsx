import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Activity, 
  Server, 
  Database, 
  Wifi, 
  HardDrive,
  Cpu,
  MemoryStick,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react'
import { adminService } from '@/services/admin'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { cn } from '@/lib/utils'

// 状态指示器组件
interface StatusIndicatorProps {
  status: 'healthy' | 'warning' | 'critical' | 'unknown'
  size?: 'sm' | 'md' | 'lg'
}

function StatusIndicator({ status, size = 'md' }: StatusIndicatorProps) {
  const sizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-6 w-6'
  }

  const statusConfig = {
    healthy: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-100' },
    warning: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-100' },
    critical: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-100' },
    unknown: { icon: AlertTriangle, color: 'text-gray-500', bg: 'bg-gray-100' }
  }

  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <div className={cn('rounded-full p-1', config.bg)}>
      <Icon className={cn(sizeClasses[size], config.color)} />
    </div>
  )
}

// 服务状态卡片组件
interface ServiceCardProps {
  name: string
  status: 'healthy' | 'warning' | 'critical' | 'unknown'
  responseTime: number
  lastCheck: string
  errorMessage?: string
  icon: React.ReactNode
}

function ServiceCard({ name, status, responseTime, lastCheck, errorMessage, icon }: ServiceCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          {icon}
          {name}
        </CardTitle>
        <StatusIndicator status={status} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{responseTime}ms</div>
        <p className="text-xs text-muted-foreground">
          响应时间
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          最后检查: {formatDistanceToNow(new Date(lastCheck), { addSuffix: true, locale: zhCN })}
        </p>
        {errorMessage && (
          <p className="text-xs text-red-500 mt-1">{errorMessage}</p>
        )}
      </CardContent>
    </Card>
  )
}

// 系统资源使用率组件
interface ResourceUsageProps {
  title: string
  usage: number
  icon: React.ReactNode
  unit?: string
}

function ResourceUsage({ title, usage, icon, unit = '%' }: ResourceUsageProps) {
  const getUsageColor = (usage: number) => {
    if (usage >= 90) return 'text-red-500'
    if (usage >= 70) return 'text-yellow-500'
    return 'text-green-500'
  }

  const getProgressColor = (usage: number) => {
    if (usage >= 90) return 'bg-red-500'
    if (usage >= 70) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={cn("text-2xl font-bold", getUsageColor(usage))}>
          {usage.toFixed(1)}{unit}
        </div>
        <Progress 
          value={usage} 
          className="mt-2"
          // className={cn("mt-2", getProgressColor(usage))}
        />
        <p className="text-xs text-muted-foreground mt-1">
          {usage >= 90 ? '使用率过高' : usage >= 70 ? '使用率较高' : '使用率正常'}
        </p>
      </CardContent>
    </Card>
  )
}

// 最近错误列表组件
interface RecentErrorsProps {
  errors: Array<{
    timestamp: string
    level: string
    message: string
    source: string
  }>
}

function RecentErrors({ errors }: RecentErrorsProps) {
  const getLevelBadgeVariant = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
      case 'critical':
        return 'destructive'
      case 'warning':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  return (
    <div className="space-y-3">
      {errors.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4">
          暂无错误记录
        </p>
      ) : (
        errors.map((error, index) => (
          <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg">
            <Badge variant={getLevelBadgeVariant(error.level)}>
              {error.level}
            </Badge>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium">{error.message}</p>
              <p className="text-xs text-muted-foreground">
                来源: {error.source}
              </p>
              <p className="text-xs text-muted-foreground">
                {formatDistanceToNow(new Date(error.timestamp), { addSuffix: true, locale: zhCN })}
              </p>
            </div>
          </div>
        ))
      )}
    </div>
  )
}

// 主系统健康组件
export function SystemHealthMonitoring() {
  const { 
    data: healthData, 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => adminService.getSystemHealth(),
    refetchInterval: 30000, // 30秒自动刷新
  })

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          加载系统健康数据失败，请检查网络连接或稍后重试。
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
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
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

  const data = healthData?.data

  if (!data) {
    return (
      <Alert>
        <AlertDescription>
          暂无系统健康数据
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">系统健康监控</h1>
          <p className="text-muted-foreground">
            实时监控系统状态和服务健康
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge 
            variant={data.status === 'healthy' ? 'default' : data.status === 'warning' ? 'secondary' : 'destructive'}
            className="text-sm"
          >
            <StatusIndicator status={data.status} size="sm" />
            <span className="ml-2">
              {data.status === 'healthy' ? '系统正常' : 
               data.status === 'warning' ? '系统警告' : '系统异常'}
            </span>
          </Badge>
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

      {/* 系统概览 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              系统运行时间
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.floor(data.uptime / 3600)}h</div>
            <p className="text-xs text-muted-foreground">
              版本: {data.version}
            </p>
          </CardContent>
        </Card>

        <ResourceUsage
          title="CPU 使用率"
          usage={data.system_info.cpu_usage}
          icon={<Cpu className="h-4 w-4" />}
        />

        <ResourceUsage
          title="内存使用率"
          usage={data.system_info.memory_usage}
          icon={<MemoryStick className="h-4 w-4" />}
        />

        <ResourceUsage
          title="磁盘使用率"
          usage={data.system_info.disk_usage}
          icon={<HardDrive className="h-4 w-4" />}
        />
      </div>

      {/* 服务状态 */}
      <Card>
        <CardHeader>
          <CardTitle>服务状态</CardTitle>
          <CardDescription>各个服务的健康状态和响应时间</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <ServiceCard
              name="数据库"
              status={data.services.database.status}
              responseTime={data.services.database.response_time}
              lastCheck={data.services.database.last_check}
              errorMessage={data.services.database.error_message}
              icon={<Database className="h-4 w-4" />}
            />
            <ServiceCard
              name="Redis"
              status={data.services.redis.status}
              responseTime={data.services.redis.response_time}
              lastCheck={data.services.redis.last_check}
              errorMessage={data.services.redis.error_message}
              icon={<Server className="h-4 w-4" />}
            />
            <ServiceCard
              name="存储服务"
              status={data.services.storage.status}
              responseTime={data.services.storage.response_time}
              lastCheck={data.services.storage.last_check}
              errorMessage={data.services.storage.error_message}
              icon={<HardDrive className="h-4 w-4" />}
            />
            <ServiceCard
              name="LLM API"
              status={data.services.llm_api.status}
              responseTime={data.services.llm_api.response_time}
              lastCheck={data.services.llm_api.last_check}
              errorMessage={data.services.llm_api.error_message}
              icon={<Wifi className="h-4 w-4" />}
            />
          </div>
        </CardContent>
      </Card>

      {/* 网络I/O和最近错误 */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* 网络I/O */}
        <Card>
          <CardHeader>
            <CardTitle>网络I/O</CardTitle>
            <CardDescription>网络流量统计</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-sm font-medium">发送字节数</span>
                <span className="text-sm">{(data.system_info.network_io.bytes_sent / 1024 / 1024).toFixed(2)} MB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">接收字节数</span>
                <span className="text-sm">{(data.system_info.network_io.bytes_received / 1024 / 1024).toFixed(2)} MB</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 最近错误 */}
        <Card>
          <CardHeader>
            <CardTitle>最近错误</CardTitle>
            <CardDescription>系统最新的错误和警告</CardDescription>
          </CardHeader>
          <CardContent>
            <RecentErrors errors={data.recent_errors} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
