import { useCallback, useEffect, useState } from 'react'
import { AxiosError } from 'axios'
import { EnhancedErrorHandler, ErrorHandlingConfig, OfflineDetector } from '@/utils/error-handler'
import { useNotification } from './use-notification'

/**
 * 错误处理hook
 */
export function useErrorHandler() {
  const notification = useNotification()
  
  const handleError = useCallback(async (
    error: AxiosError,
    config?: Partial<ErrorHandlingConfig>,
    requestKey?: string
  ) => {
    await EnhancedErrorHandler.handleApiError(error, config, requestKey)
  }, [])
  
  const handleWebSocketError = useCallback((
    error: Event,
    reconnect: () => void,
    maxReconnectAttempts?: number
  ) => {
    EnhancedErrorHandler.handleWebSocketError(error, reconnect, maxReconnectAttempts)
  }, [])
  
  const handleUploadError = useCallback((error: Error, filename: string) => {
    EnhancedErrorHandler.handleUploadError(error, filename)
  }, [])
  
  return {
    handleError,
    handleWebSocketError,
    handleUploadError,
    clearRetryAttempts: EnhancedErrorHandler.clearRetryAttempts,
    getRetryAttempts: EnhancedErrorHandler.getRetryAttempts,
  }
}

/**
 * 离线状态hook
 */
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(OfflineDetector.getOnlineStatus())
  
  useEffect(() => {
    const unsubscribe = OfflineDetector.addListener(setIsOnline)
    return unsubscribe
  }, [])
  
  return isOnline
}

/**
 * 带重试的请求hook
 */
export function useRetryableRequest<T>(
  requestFn: () => Promise<T>,
  requestKey: string,
  config?: Partial<ErrorHandlingConfig>
) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [data, setData] = useState<T | null>(null)
  
  const execute = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const result = await requestFn()
      setData(result)
      EnhancedErrorHandler.clearRetryAttempts(requestKey)
      return result
    } catch (err) {
      const error = err as AxiosError
      setError(error)
      
      // 处理错误和重试
      await EnhancedErrorHandler.handleApiError(error, config, requestKey)
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [requestFn, requestKey, config])
  
  const retry = useCallback(() => {
    return execute()
  }, [execute])
  
  const reset = useCallback(() => {
    setError(null)
    setData(null)
    EnhancedErrorHandler.clearRetryAttempts(requestKey)
  }, [requestKey])
  
  return {
    execute,
    retry,
    reset,
    isLoading,
    error,
    data,
    retryAttempts: EnhancedErrorHandler.getRetryAttempts(requestKey),
  }
}

/**
 * 批量操作错误处理hook
 */
export function useBatchErrorHandler() {
  const [errors, setErrors] = useState<Array<{ id: string; error: Error }>>([])
  const notification = useNotification()
  
  const addError = useCallback((id: string, error: Error) => {
    setErrors(prev => [...prev, { id, error }])
  }, [])
  
  const removeError = useCallback((id: string) => {
    setErrors(prev => prev.filter(e => e.id !== id))
  }, [])
  
  const clearErrors = useCallback(() => {
    setErrors([])
  }, [])
  
  const handleBatchErrors = useCallback((batchErrors: Array<{ id: string; error: Error }>) => {
    setErrors(batchErrors)
    
    if (batchErrors.length > 0) {
      notification.error(
        `批量操作失败`,
        `${batchErrors.length} 个操作失败，请查看详情`,
        {
          action: {
            label: '查看详情',
            onClick: () => {
              // 可以打开一个详情对话框
              console.log('Batch errors:', batchErrors)
            }
          }
        }
      )
    }
  }, [notification])
  
  return {
    errors,
    addError,
    removeError,
    clearErrors,
    handleBatchErrors,
    hasErrors: errors.length > 0,
  }
}