import { useState, useEffect } from 'react'

/**
 * 媒体查询hook
 * @param query CSS媒体查询字符串
 * @returns 是否匹配媒体查询
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    const media = window.matchMedia(query)
    
    // 设置初始值
    setMatches(media.matches)
    
    // 监听变化
    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches)
    }
    
    // 添加监听器
    if (media.addEventListener) {
      media.addEventListener('change', listener)
    } else {
      // 兼容旧版本浏览器
      media.addListener(listener)
    }
    
    // 清理函数
    return () => {
      if (media.removeEventListener) {
        media.removeEventListener('change', listener)
      } else {
        media.removeListener(listener)
      }
    }
  }, [query])

  return matches
}

// 常用的媒体查询hooks
export const useIsMobile = () => useMediaQuery('(max-width: 768px)')
export const useIsTablet = () => useMediaQuery('(min-width: 769px) and (max-width: 1024px)')
export const useIsDesktop = () => useMediaQuery('(min-width: 1025px)')
export const useIsSmallScreen = () => useMediaQuery('(max-width: 640px)')
export const useIsMediumScreen = () => useMediaQuery('(min-width: 641px) and (max-width: 1024px)')
export const useIsLargeScreen = () => useMediaQuery('(min-width: 1025px)')

// 响应式断点
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const