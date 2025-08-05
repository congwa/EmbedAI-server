import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { GlobalSearch } from './global-search'
import { Search, Command } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SearchTriggerProps {
  className?: string
  variant?: 'default' | 'compact' | 'icon'
}

export function SearchTrigger({ className, variant = 'default' }: SearchTriggerProps) {
  const [open, setOpen] = useState(false)
  const [isMac, setIsMac] = useState(false)

  // 检测操作系统
  useEffect(() => {
    setIsMac(navigator.platform.toUpperCase().indexOf('MAC') >= 0)
  }, [])

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen(true)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const getShortcutText = () => {
    return isMac ? '⌘K' : 'Ctrl+K'
  }

  if (variant === 'icon') {
    return (
      <>
        <Button
          variant="ghost"
          size="sm"
          className={cn('h-8 w-8 p-0', className)}
          onClick={() => setOpen(true)}
        >
          <Search className="h-4 w-4" />
          <span className="sr-only">搜索</span>
        </Button>
        <GlobalSearch open={open} onOpenChange={setOpen} />
      </>
    )
  }

  if (variant === 'compact') {
    return (
      <>
        <Button
          variant="outline"
          size="sm"
          className={cn('h-8 px-3 gap-2', className)}
          onClick={() => setOpen(true)}
        >
          <Search className="h-3 w-3" />
          <span className="text-xs">搜索</span>
          <Badge variant="secondary" className="h-4 px-1 text-xs font-mono">
            {getShortcutText()}
          </Badge>
        </Button>
        <GlobalSearch open={open} onOpenChange={setOpen} />
      </>
    )
  }

  return (
    <>
      <Button
        variant="outline"
        className={cn(
          'relative h-9 w-full justify-start text-sm text-muted-foreground sm:pr-12 md:w-40 lg:w-64',
          className
        )}
        onClick={() => setOpen(true)}
      >
        <Search className="mr-2 h-4 w-4" />
        <span className="hidden lg:inline-flex">搜索聊天、用户、知识库...</span>
        <span className="inline-flex lg:hidden">搜索...</span>
        <div className="pointer-events-none absolute right-1.5 top-1.5 hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
          <span className="text-xs">{getShortcutText()}</span>
        </div>
      </Button>
      <GlobalSearch open={open} onOpenChange={setOpen} />
    </>
  )
}

// 搜索结果高亮组件
interface SearchHighlightProps {
  text: string
  query: string
  className?: string
}

export function SearchHighlight({ text, query, className }: SearchHighlightProps) {
  if (!query.trim()) {
    return <span className={className}>{text}</span>
  }

  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  const parts = text.split(regex)

  return (
    <span className={className}>
      {parts.map((part, index) =>
        regex.test(part) ? (
          <mark key={index} className="bg-yellow-200 text-yellow-900 rounded px-0.5">
            {part}
          </mark>
        ) : (
          part
        )
      )}
    </span>
  )
}

// 搜索统计组件
interface SearchStatsProps {
  total: number
  query: string
  duration?: number
  className?: string
}

export function SearchStats({ total, query, duration, className }: SearchStatsProps) {
  return (
    <div className={cn('text-xs text-muted-foreground', className)}>
      找到 <span className="font-medium">{total}</span> 个结果
      {query && (
        <>
          ，关键词 "<span className="font-medium">{query}</span>"
        </>
      )}
      {duration && (
        <>
          （用时 <span className="font-medium">{duration}ms</span>）
        </>
      )}
    </div>
  )
}

// 搜索过滤器组件
interface SearchFiltersProps {
  filters: Array<{
    key: string
    label: string
    count?: number
    active?: boolean
  }>
  onFilterChange: (key: string, active: boolean) => void
  className?: string
}

export function SearchFilters({ filters, onFilterChange, className }: SearchFiltersProps) {
  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {filters.map((filter) => (
        <Button
          key={filter.key}
          variant={filter.active ? 'default' : 'outline'}
          size="sm"
          className="h-7 px-2 text-xs"
          onClick={() => onFilterChange(filter.key, !filter.active)}
        >
          {filter.label}
          {filter.count !== undefined && (
            <Badge
              variant={filter.active ? 'secondary' : 'outline'}
              className="ml-1 h-4 px-1 text-xs"
            >
              {filter.count}
            </Badge>
          )}
        </Button>
      ))}
    </div>
  )
}