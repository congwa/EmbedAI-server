import { create } from 'zustand'
import { toast } from '@/hooks/use-toast'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  description?: string
  duration?: number
  persistent?: boolean
  timestamp: number
  read?: boolean
  action?: {
    label: string
    onClick: () => void
  }
}

interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  
  // Actions
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void
  removeNotification: (id: string) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  clearAll: () => void
  
  // Convenience methods
  success: (title: string, description?: string, options?: Partial<Notification>) => void
  error: (title: string, description?: string, options?: Partial<Notification>) => void
  warning: (title: string, description?: string, options?: Partial<Notification>) => void
  info: (title: string, description?: string, options?: Partial<Notification>) => void
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  
  addNotification: (notification) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: Date.now(),
      read: false,
    }
    
    set((state) => ({
      notifications: [newNotification, ...state.notifications],
      unreadCount: state.unreadCount + 1,
    }))
    
    // 显示toast通知
    toast({
      title: newNotification.title,
      description: newNotification.description,
      variant: newNotification.type === 'error' ? 'destructive' : 'default',
    })
    
    // 自动移除非持久化通知
    if (!newNotification.persistent) {
      const duration = newNotification.duration || 5000
      setTimeout(() => {
        get().removeNotification(id)
      }, duration)
    }
  },
  
  removeNotification: (id) => {
    set((state) => {
      const notification = state.notifications.find(n => n.id === id)
      const wasUnread = notification && !notification.read
      
      return {
        notifications: state.notifications.filter(n => n.id !== id),
        unreadCount: wasUnread ? state.unreadCount - 1 : state.unreadCount,
      }
    })
  },
  
  markAsRead: (id) => {
    set((state) => {
      const notification = state.notifications.find(n => n.id === id)
      if (!notification || notification.read) return state
      
      return {
        notifications: state.notifications.map(n => 
          n.id === id ? { ...n, read: true } : n
        ),
        unreadCount: state.unreadCount - 1,
      }
    })
  },
  
  markAllAsRead: () => {
    set((state) => ({
      notifications: state.notifications.map(n => ({ ...n, read: true })),
      unreadCount: 0,
    }))
  },
  
  clearAll: () => {
    set({ notifications: [], unreadCount: 0 })
  },
  
  // Convenience methods
  success: (title, description, options = {}) => {
    get().addNotification({ ...options, type: 'success', title, description })
  },
  
  error: (title, description, options = {}) => {
    get().addNotification({ ...options, type: 'error', title, description, persistent: true })
  },
  
  warning: (title, description, options = {}) => {
    get().addNotification({ ...options, type: 'warning', title, description })
  },
  
  info: (title, description, options = {}) => {
    get().addNotification({ ...options, type: 'info', title, description })
  },
}))

// 全局通知方法
export const notify = {
  success: (title: string, description?: string, options?: Partial<Notification>) => {
    useNotificationStore.getState().success(title, description, options)
  },
  error: (title: string, description?: string, options?: Partial<Notification>) => {
    useNotificationStore.getState().error(title, description, options)
  },
  warning: (title: string, description?: string, options?: Partial<Notification>) => {
    useNotificationStore.getState().warning(title, description, options)
  },
  info: (title: string, description?: string, options?: Partial<Notification>) => {
    useNotificationStore.getState().info(title, description, options)
  },
}