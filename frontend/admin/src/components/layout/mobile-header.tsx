import React from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { MobileNav } from './mobile-nav'
import { NotificationCenter } from '@/components/notifications/notification-center'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { ThemeSwitch } from '@/components/theme-switch'
import { ArrowLeft, Search } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MobileHeaderProps {
  title?: string
  subtitle?: string
  showBack?: boolean
  onBack?: () => void
  actions?: React.ReactNode
  className?: string
}

export function MobileHeader({
  title,
  subtitle,
  showBack,
  onBack,
  actions,
  className,
}: MobileHeaderProps) {
  return (
    <header className={cn(
      'sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60',
      className
    )}>
      <div className="flex h-14 items-center px-4">
        {/* Left section */}
        <div className="flex items-center gap-2">
          {showBack ? (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={onBack}
            >
              <ArrowLeft className="h-4 w-4" />
              <span className="sr-only">返回</span>
            </Button>
          ) : (
            <MobileNav />
          )}
          
          {title && (
            <div className="flex-1 min-w-0 ml-2">
              <h1 className="text-sm font-semibold truncate">{title}</h1>
              {subtitle && (
                <p className="text-xs text-muted-foreground truncate">{subtitle}</p>
              )}
            </div>
          )}
        </div>

        {/* Right section */}
        <div className="flex items-center gap-1 ml-auto">
          {actions}
          
          {/* Search button for mobile */}
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 md:hidden"
          >
            <Search className="h-4 w-4" />
            <span className="sr-only">搜索</span>
          </Button>
          
          <NotificationCenter />
          <ThemeSwitch />
          <ProfileDropdown />
        </div>
      </div>
    </header>
  )
}

// 移动端页面标题组件
interface MobilePageHeaderProps {
  title: string
  description?: string
  badge?: string | number
  actions?: React.ReactNode
  className?: string
}

export function MobilePageHeader({
  title,
  description,
  badge,
  actions,
  className,
}: MobilePageHeaderProps) {
  return (
    <div className={cn('px-4 py-4 border-b bg-background', className)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold truncate">{title}</h1>
            {badge && (
              <Badge variant="secondary" className="h-5 px-2 text-xs">
                {badge}
              </Badge>
            )}
          </div>
          {description && (
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
              {description}
            </p>
          )}
        </div>
        
        {actions && (
          <div className="flex items-center gap-2 flex-shrink-0">
            {actions}
          </div>
        )}
      </div>
    </div>
  )
}