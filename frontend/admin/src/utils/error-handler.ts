import { AxiosError } from 'axios'
import { globalNotify } from '@/hooks/use-notification'

export interface ErrorHandlingConfig {
  maxRetries: number
  retryDelay: number
  showToast: boolean
  logError: boolean
  retryCondition?: (error: AxiosError) => boolean
}

const DEFAULT_CONFIG: ErrorHandlingConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  showToast: true,
  logError: true,
  retryCondition: (error) => {
    // 默认重试条件：网络错误或5xx服务器错误
    return !error.response || (error.response.status >= 500 && error.response.status < 600)
  },
}

export class EnhancedErrorHandler {
  private static retryAttempts = new Map<string, number>()
  
  /**
   * 处理API错误
   */
  static async handleApiError(
    error: AxiosError,
    config: Partial<ErrorHandlingConfig> = {},
    requestKey?: string
  ): Promise<void> {
    const finalConfig = { ...DEFAULT_CONFIG, ...config }
    
    // 记录错误
    if (finalConfig.logError) {
      console.error('API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        message: error.message,
        data: error.response?.data,
      })
    }
    
    // 获取用户友好的错误消息
    const userMessage = this.getUserFriendlyMessage(error)
    
    // 显示错误通知
    if (finalConfig.showToast) {
      globalNotify.error('操作失败', userMessage)
    }
    
    // 处理重试逻辑
    if (requestKey && finalConfig.retryCondition?.(error)) {
      const attempts = this.retryAttempts.get(requestKey) || 0
      if (attempts < finalConfig.maxRetries) {
        this.retryAttempts.set(requestKey, attempts + 1)
        
        // 显示重试通知
        globalNotify.info(
          '正在重试',
          `第 ${attempts + 1} 次重试，共 ${finalConfig.maxRetries} 次`
        )
        
        // 延迟后重试
        await this.delay(finalConfig.retryDelay * Math.pow(2, attempts)) // 指数退避
        return
      } else {
        // 重试次数用完
        this.retryAttempts.delete(requestKey)
        globalNotify.error(
          '重试失败',
          `已重试 ${finalConfig.maxRetries} 次，请检查网络连接或稍后再试`
        )
      }
    }
  }
  
  /**
   * 获取用户友好的错误消息
   */
  private static getUserFriendlyMessage(error: AxiosError): string {
    // 网络错误
    if (!error.response) {
      return '网络连接失败，请检查网络设置'
    }
    
    const status = error.response.status
    const data = error.response.data as any
    
    // 服务器返回的错误消息
    if (data?.message) {
      return data.message
    }
    
    // 根据状态码返回友好消息
    switch (status) {
      case 400:
        return '请求参数错误，请检查输入内容'
      case 401:
        return '登录已过期，请重新登录'
      case 403:
        return '没有权限执行此操作'
      case 404:
        return '请求的资源不存在'
      case 409:
        return '操作冲突，请刷新页面后重试'
      case 422:
        return '数据验证失败，请检查输入内容'
      case 429:
        return '操作过于频繁，请稍后再试'
      case 500:
        return '服务器内部错误，请稍后重试'
      case 502:
        return '服务器网关错误，请稍后重试'
      case 503:
        return '服务暂时不可用，请稍后重试'
      case 504:
        return '服务器响应超时，请稍后重试'
      default:
        return `操作失败 (${status})，请稍后重试`
    }
  }
  
  /**
   * 延迟函数
   */
  private static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
  
  /**
   * 清除重试计数
   */
  static clearRetryAttempts(requestKey: string): void {
    this.retryAttempts.delete(requestKey)
  }
  
  /**
   * 获取重试次数
   */
  static getRetryAttempts(requestKey: string): number {
    return this.retryAttempts.get(requestKey) || 0
  }
}

/**
 * 创建带重试的请求函数
 */
export function createRetryableRequest<T>(
  requestFn: () => Promise<T>,
  requestKey: string,
  config: Partial<ErrorHandlingConfig> = {}
): () => Promise<T> {
  return async () => {
    const finalConfig = { ...DEFAULT_CONFIG, ...config }
    let lastError: any
    
    for (let attempt = 0; attempt <= finalConfig.maxRetries; attempt++) {
      try {
        const result = await requestFn()
        // 成功时清除重试计数
        EnhancedErrorHandler.clearRetryAttempts(requestKey)
        return result
      } catch (error) {
        lastError = error
        
        // 如果是最后一次尝试或不满足重试条件，直接抛出错误
        if (
          attempt === finalConfig.maxRetries ||
          (error instanceof Error && !finalConfig.retryCondition?.(error as AxiosError))
        ) {
          break
        }
        
        // 等待后重试
        await EnhancedErrorHandler['delay'](finalConfig.retryDelay * Math.pow(2, attempt))
      }
    }
    
    // 处理最终错误
    if (lastError instanceof Error) {
      await EnhancedErrorHandler.handleApiError(
        lastError as AxiosError,
        config,
        requestKey
      )
    }
    
    throw lastError
  }
}

/**
 * 离线检测
 */
export class OfflineDetector {
  private static isOnline = navigator.onLine
  private static listeners: Array<(online: boolean) => void> = []
  
  static {
    // 监听在线状态变化
    window.addEventListener('online', () => {
      this.isOnline = true
      this.notifyListeners(true)
      globalNotify.success('网络已连接', '您现在可以正常使用所有功能')
    })
    
    window.addEventListener('offline', () => {
      this.isOnline = false
      this.notifyListeners(false)
      globalNotify.warning(
        '网络连接断开',
        '部分功能可能无法使用，请检查网络连接',
        { duration: 0 } // 不自动消失
      )
    })
  }
  
  static getOnlineStatus(): boolean {
    return this.isOnline
  }
  
  static addListener(listener: (online: boolean) => void): () => void {
    this.listeners.push(listener)
    return () => {
      const index = this.listeners.indexOf(listener)
      if (index > -1) {
        this.listeners.splice(index, 1)
      }
    }
  }
  
  private static notifyListeners(online: boolean): void {
    this.listeners.forEach(listener => listener(online))
  }
}