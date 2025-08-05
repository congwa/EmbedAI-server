import React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { MoreHorizontal } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'

interface MobileTableProps<T> {
  data: T[]
  renderItem: (item: T, index: number) => React.ReactNode
  className?: string
  emptyMessage?: string
  loading?: boolean
}

export function MobileTable<T>({
  data,
  renderItem,
  className,
  emptyMessage = '暂无数据',
  loading = false,
}: MobileTableProps<T>) {
  if (loading) {
    return (
      <div className={cn('space-y-3', className)}>
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="animate-pulse space-y-3">
                <div className="h-4 bg-muted rounded w-3/4"></div>
                <div className="h-3 bg-muted rounded w-1/2"></div>
                <div className="h-3 bg-muted rounded w-2/3"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-8 text-center">
          <p className="text-muted-foreground">{emptyMessage}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className={cn('space-y-3', className)}>
      {data.map((item, index) => (
        <Card key={index} className="overflow-hidden">
          <CardContent className="p-0">
            {renderItem(item, index)}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// 移动端表格项组件
interface MobileTableItemProps {
  children: React.ReactNode
  onClick?: () => void
  className?: string
}

export function MobileTableItem({
  children,
  onClick,
  className,
}: MobileTableItemProps) {
  return (
    <div
      className={cn(
        'p-4 cursor-pointer hover:bg-accent/50 transition-colors',
        onClick && 'active:bg-accent',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

// 移动端表格行组件
interface MobileTableRowProps {
  title: string
  subtitle?: string
  description?: string
  badge?: React.ReactNode
  status?: React.ReactNode
  actions?: Array<{
    label: string
    onClick: () => void
    icon?: React.ComponentType<{ className?: string }>
    variant?: 'default' | 'destructive'
  }>
  onClick?: () => void
  className?: string
}

export function MobileTableRow({
  title,
  subtitle,
  description,
  badge,
  status,
  actions,
  onClick,
  className,
}: MobileTableRowProps) {
  return (
    <MobileTableItem onClick={onClick} className={className}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-sm truncate">{title}</h3>
            {badge}
          </div>
          
          {subtitle && (
            <p className="text-xs text-muted-foreground truncate">{subtitle}</p>
          )}
          
          {description && (
            <p className="text-xs text-muted-foreground line-clamp-2">
              {description}
            </p>
          )}
          
          {status && (
            <div className="flex items-center gap-2 mt-2">
              {status}
            </div>
          )}
        </div>

        {actions && actions.length > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">打开菜单</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {actions.map((action, index) => {
                const Icon = action.icon
                return (
                  <DropdownMenuItem
                    key={index}
                    onClick={(e) => {
                      e.stopPropagation()
                      action.onClick()
                    }}
                    className={cn(
                      action.variant === 'destructive' && 'text-destructive focus:text-destructive'
                    )}
                  >
                    {Icon && <Icon className="mr-2 h-4 w-4" />}
                    {action.label}
                  </DropdownMenuItem>
                )
              })}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </MobileTableItem>
  )
}

// 移动端统计卡片组件
interface MobileStatsCardProps {
  title: string
  value: string | number
  description?: string
  trend?: {
    value: number
    label: string
    positive?: boolean
  }
  icon?: React.ComponentType<{ className?: string }>
  className?: string
}

export function MobileStatsCard({
  title,
  value,
  description,
  trend,
  icon: Icon,
  className,
}: MobileStatsCardProps) {
  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              {title}
            </p>
            <p className="text-2xl font-bold">{value}</p>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
          {Icon && (
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
              <Icon className="h-4 w-4 text-primary" />
            </div>
          )}
        </div>
        
        {trend && (
          <>
            <Separator className="my-3" />
            <div className="flex items-center gap-2">
              <Badge
                variant={trend.positive ? 'default' : 'secondary'}
                className="h-5 px-1.5 text-xs"
              >
                {trend.positive ? '+' : ''}{trend.value}%
              </Badge>
              <span className="text-xs text-muted-foreground">{trend.label}</span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}