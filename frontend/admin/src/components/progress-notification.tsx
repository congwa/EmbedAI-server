import React, { useEffect, useState } from 'react'
import { useNotificationStore } from '@/stores/notificationStore'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  CheckCircle,
  AlertCircle,
  Loader2,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export interface ProgressNotificationOptions {
  id?: string
  title: string
  description?: string
  progress?: number
  status?: 'loading' | 'success' | 'error'
  persistent?: boolean
  onCancel?: () => void
  onRetry?: () => void
}

interface ProgressNotificationState {
  notifications: Map<string, ProgressNotificationOptions>
  addProgressNotification: (options: ProgressNotificationOptions) => string
  updateProgressNotification: (id: string, updates: Partial<ProgressNotificationOptions>) => void
  removeProgressNotification: (id: string) => void
}

// 创建一个专门的进度通知store
const progressNotifications = new Map<string, ProgressNotificationOptions>()
const listeners = new Set<() => void>()

const notifyListeners = () => {
  listeners.forEach(listener => listener())
}

export const progressNotificationManager = {
  add: (options: ProgressNotificationOptions): string => {
    const id = options.id || `progress-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    progressNotifications.set(id, { ...options, id })
    notifyListeners()
    return id
  },
  
  update: (id: string, updates: Partial<ProgressNotificationOptions>) => {
    const existing = progressNotifications.get(id)
    if (existing) {
      progressNotifications.set(id, { ...existing, ...updates })
      notifyListeners()
    }
  },
  
  remove: (id: string) => {
    progressNotifications.delete(id)
    notifyListeners()
  },
  
  complete: (id: string, options?: { title?: string; description?: string }) => {
    const existing = progressNotifications.get(id)
    if (existing) {
      progressNotifications.set(id, {
        ...existing,
        status: 'success',
        progress: 100,
        title: options?.title || existing.title,
        description: options?.description || existing.description,
      })
      notifyListeners()
      
      // 自动移除成功通知
      setTimeout(() => {
        progressNotifications.delete(id)
        notifyListeners()
      }, 3000)
    }
  },
  
  error: (id: string, options?: { title?: string; description?: string }) => {
    const existing = progressNotifications.get(id)
    if (existing) {
      progressNotifications.set(id, {
        ...existing,
        status: 'error',
        title: options?.title || existing.title,
        description: options?.description || existing.description,
      })
      notifyListeners()
    }
  },
}

export function ProgressNotifications() {
  const [notifications, setNotifications] = useState<ProgressNotificationOptions[]>([])
  
  useEffect(() => {
    const updateNotifications = () => {
      setNotifications(Array.from(progressNotifications.values()))
    }
    
    listeners.add(updateNotifications)
    updateNotifications()
    
    return () => {
      listeners.delete(updateNotifications)
    }
  }, [])
  
  if (notifications.length === 0) return null
  
  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <Card key={notification.id} className="shadow-lg">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">
                {notification.status === 'loading' && (
                  <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                )}
                {notification.status === 'success' && (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
                {notification.status === 'error' && (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium">{notification.title}</p>
                    {notification.description && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {notification.description}
                      </p>
                    )}
                  </div>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 ml-2"
                    onClick={() => progressNotificationManager.remove(notification.id!)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
                
                {notification.progress !== undefined && notification.status === 'loading' && (
                  <div className="mt-2">
                    <Progress value={notification.progress} className="h-1" />
                    <p className="text-xs text-muted-foreground mt-1">
                      {notification.progress}%
                    </p>
                  </div>
                )}
                
                {notification.status === 'error' && (
                  <div className="flex gap-2 mt-2">
                    {notification.onRetry && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs"
                        onClick={notification.onRetry}
                      >
                        重试
                      </Button>
                    )}
                  </div>
                )}
                
                {notification.status === 'loading' && notification.onCancel && (
                  <div className="mt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs"
                      onClick={notification.onCancel}
                    >
                      取消
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}