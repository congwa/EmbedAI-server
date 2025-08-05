import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { SystemHealthMonitoring } from './system-health'
import { PerformanceMonitoring } from './performance'
import { AlertsManagement } from './alerts'

export function MonitoringDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">系统监控</h1>
        <p className="text-muted-foreground">
          监控系统健康状态、性能指标和告警管理
        </p>
      </div>

      <Tabs defaultValue="health" className="space-y-4">
        <TabsList>
          <TabsTrigger value="health">系统健康</TabsTrigger>
          <TabsTrigger value="performance">性能监控</TabsTrigger>
          <TabsTrigger value="alerts">告警管理</TabsTrigger>
        </TabsList>

        <TabsContent value="health" className="space-y-4">
          <SystemHealthMonitoring />
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <PerformanceMonitoring />
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <AlertsManagement />
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default MonitoringDashboard
