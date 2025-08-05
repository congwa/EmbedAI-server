import React, { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { notify } from '@/stores/notificationStore'
import { adminService } from '@/services/admin'

interface SystemStatus {
  api_status: 'healthy' | 'degraded' | 'down'
  database_status: 'healthy' | 'degraded' | 'down'
  websocket_status: 'healthy' | 'degraded' | 'down'
  last_check: string
  active_users: number
  error_rate: number
  avg_response_time: number
}

export function SystemStatusNotifications() {
  // 定期检查系统状态
  const { data: systemStatus, isError } = useQuery({
    queryKey: ['system-status'],
    queryFn: async (): Promise<{ data: SystemStatus }> => {
      // 模拟系统状态检查，实际项目中应该调用真实的API
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const mockStatus: SystemStatus = {
        api_status: Math.random() > 0.1 ? 'healthy' : 'degraded',
        database_status: Math.random() > 0.05 ? 'healthy' : 'degraded',
        websocket_status: Math.random() > 0.15 ? 'healthy' : 'degraded',
        last_check: new Date().toISOString(),
        active_users: Math.floor(Math.random() * 100) + 10,
        error_rate: Math.random() * 5,
        avg_response_time: Math.floor(Math.random() * 300) + 100,
      }
      
      return { data: mockStatus }
    },
    refetchInterval: 60000, // 每分钟检查一次
    retry: 3,
  })

  // 监控系统状态变化并发送通知
  useEffect(() => {
    if (!systemStatus?.data) return

    const status = systemStatus.data
    
    // API状态检查
    if (status.api_status === 'down') {
      notify.error(
        'API服务异常',
        'API服务当前不可用，请稍后重试',
        {
          persistent: true,
          action: {
            label: '查看详情',
            onClick: () => {
              console.log('Navigate to system status page')
            },
          },
        }
      )
    } else if (status.api_status === 'degraded') {
      notify.warning(
        'API服务性能下降',
        'API响应时间较慢，可能影响用户体验',
        {
          duration: 10000,
        }
      )
    }

    // 数据库状态检查
    if (status.database_status === 'down') {
      notify.error(
        '数据库连接异常',
        '数据库服务当前不可用，部分功能可能受影响',
        {
          persistent: true,
        }
      )
    } else if (status.database_status === 'degraded') {
      notify.warning(
        '数据库性能下降',
        '数据库响应较慢，可能影响数据操作',
        {
          duration: 8000,
        }
      )
    }

    // WebSocket状态检查
    if (status.websocket_status === 'down') {
      notify.warning(
        'WebSocket连接异常',
        '实时功能可能不可用，请刷新页面重试',
        {
          persistent: true,
          action: {
            label: '刷新页面',
            onClick: () => {
              window.location.reload()
            },
          },
        }
      )
    }

    // 错误率检查
    if (status.error_rate > 10) {
      notify.error(
        '系统错误率过高',
        `当前错误率为 ${status.error_rate.toFixed(2)}%，请检查系统状态`,
        {
          persistent: true,
        }
      )
    } else if (status.error_rate > 5) {
      notify.warning(
        '系统错误率偏高',
        `当前错误率为 ${status.error_rate.toFixed(2)}%，建议关注系统状态`,
        {
          duration: 8000,
        }
      )
    }

    // 响应时间检查
    if (status.avg_response_time > 1000) {
      notify.warning(
        '系统响应缓慢',
        `平均响应时间为 ${status.avg_response_time}ms，可能影响用户体验`,
        {
          duration: 8000,
        }
      )
    }

    // 用户活跃度通知
    if (status.active_users > 80) {
      notify.info(
        '用户活跃度高',
        `当前有 ${status.active_users} 个活跃用户在线`,
        {
          duration: 5000,
        }
      )
    }
  }, [systemStatus])

  // 系统状态检查失败通知
  useEffect(() => {
    if (isError) {
      notify.error(
        '系统状态检查失败',
        '无法获取系统状态信息，请检查网络连接',
        {
          persistent: true,
          action: {
            label: '重试',
            onClick: () => {
              window.location.reload()
            },
          },
        }
      )
    }
  }, [isError])

  // 定期发送系统健康通知（每小时一次）
  useEffect(() => {
    const interval = setInterval(() => {
      if (systemStatus?.data) {
        const status = systemStatus.data
        const isHealthy = 
          status.api_status === 'healthy' &&
          status.database_status === 'healthy' &&
          status.websocket_status === 'healthy' &&
          status.error_rate < 1 &&
          status.avg_response_time < 500

        if (isHealthy) {
          notify.success(
            '系统运行正常',
            '所有服务运行良好，系统性能稳定',
            {
              duration: 3000,
            }
          )
        }
      }
    }, 3600000) // 每小时

    return () => clearInterval(interval)
  }, [systemStatus])

  // 这个组件不渲染任何UI，只负责监控和发送通知
  return null
}

// 系统维护通知组件
export function MaintenanceNotifications() {
  useEffect(() => {
    // 模拟系统维护通知
    const checkMaintenanceSchedule = () => {
      const now = new Date()
      const maintenanceTime = new Date()
      maintenanceTime.setHours(2, 0, 0, 0) // 凌晨2点维护
      
      const timeDiff = maintenanceTime.getTime() - now.getTime()
      const hoursUntilMaintenance = Math.floor(timeDiff / (1000 * 60 * 60))
      
      // 提前2小时通知维护
      if (hoursUntilMaintenance === 2) {
        notify.warning(
          '系统维护通知',
          '系统将在2小时后进行例行维护，维护期间部分功能可能不可用',
          {
            persistent: true,
            action: {
              label: '了解详情',
              onClick: () => {
                console.log('Navigate to maintenance info page')
              },
            },
          }
        )
      }
      
      // 提前30分钟通知维护
      if (hoursUntilMaintenance === 0 && Math.floor(timeDiff / (1000 * 60)) === 30) {
        notify.error(
          '系统维护即将开始',
          '系统将在30分钟后开始维护，请及时保存您的工作',
          {
            persistent: true,
            action: {
              label: '保存工作',
              onClick: () => {
                // 触发自动保存逻辑
                console.log('Auto-save triggered')
              },
            },
          }
        )
      }
    }
    
    // 每小时检查一次维护计划
    const interval = setInterval(checkMaintenanceSchedule, 3600000)
    checkMaintenanceSchedule() // 立即检查一次
    
    return () => clearInterval(interval)
  }, [])

  return null
}

// 新功能发布通知组件
export function FeatureAnnouncementNotifications() {
  useEffect(() => {
    // 模拟新功能发布通知
    const announceNewFeatures = () => {
      const lastAnnouncementDate = localStorage.getItem('lastFeatureAnnouncement')
      const today = new Date().toDateString()
      
      if (lastAnnouncementDate !== today) {
        // 模拟有新功能发布
        if (Math.random() > 0.8) { // 20%的概率有新功能
          notify.info(
            '新功能发布',
            '我们发布了新的用户管理功能，包括批量操作和活动监控',
            {
              persistent: true,
              action: {
                label: '查看详情',
                onClick: () => {
                  console.log('Navigate to feature announcement page')
                },
              },
            }
          )
          
          localStorage.setItem('lastFeatureAnnouncement', today)
        }
      }
    }
    
    // 页面加载时检查
    setTimeout(announceNewFeatures, 5000) // 延迟5秒显示
  }, [])

  return null
}