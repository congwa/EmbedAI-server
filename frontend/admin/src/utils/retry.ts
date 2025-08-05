import { AxiosError } from 'axios'

export interface RetryConfig {
  maxRetries: number
  retryDelay: number
  retryCondition?: (error: AxiosError) => boolean
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  retryCondition: (error) => {
    // 默认重试条件：网络错误或5xx服务器错误
    return !error.response || (error.response.status >= 500 && error.response.status < 600)
  },
}

/**
 * 带重试的请求函数
 */
export async function withRetry<T>(
  requestFn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const finalConfig = { ...DEFAULT_RETRY_CONFIG, ...config }
  let lastError: any
  
  for (let attempt = 0; attempt <= finalConfig.maxRetries; attempt++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error
      
      // 如果是最后一次尝试或不满足重试条件，直接抛出错误
      if (
        attempt === finalConfig.maxRetries ||
        !finalConfig.retryCondition?.(error as AxiosError)
      ) {
        break
      }
      
      // 等待后重试（指数退避）
      await delay(finalConfig.retryDelay * Math.pow(2, attempt))
    }
  }
  
  throw lastError
}

/**
 * 延迟函数
 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 判断是否应该重试的辅助函数
 */
export function shouldRetry(error: AxiosError): boolean {
  // 网络错误
  if (!error.response) {
    return true
  }
  
  const status = error.response.status
  
  // 5xx 服务器错误
  if (status >= 500 && status < 600) {
    return true
  }
  
  // 429 请求过于频繁
  if (status === 429) {
    return true
  }
  
  // 408 请求超时
  if (status === 408) {
    return true
  }
  
  return false
}