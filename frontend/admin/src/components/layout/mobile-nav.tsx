import React, { useState } from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Menu, 
  X, 
  MessageSquare, 
  Users, 
  BookOpen, 
  Settings,
  Home,
  FileText,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string | number
  description?: string
}

const navItems: NavItem[] = [
  {
    title: '首页',
    href: '/',
    icon: Home,
    description: '系统概览和统计',
  },
  {
    title: '聊天管理',
    href: '/chats',
    icon: MessageSquare,
    description: '管理用户聊天对话',
  },
  {
    title: '用户管理',
    href: '/users',
    icon: Users,
    description: '管理系统用户',
  },
  {
    title: '知识库',
    href: '/knowledge-bases',
    icon: BookOpen,
    description: '管理知识库和文档',
  },
  {
    title: '任务管理',
    href: '/tasks',
    icon: FileText,
    description: '查看系统任务',
  },
  {
    title: '设置',
    href: '/settings',
    icon: Settings,
    description: '系统设置和配置',
  },
]

export function MobileNav() {
  const [open, setOpen] = useState(false)
  const location = useLocation()

  const isActive = (href: string) => {
    if (href === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(href)
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="md:hidden h-9 w-9 p-0"
        >
          <Menu className="h-4 w-4" />
          <span className="sr-only">打开导航菜单</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-80 p-0">
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">AI</span>
              </div>
              <div>
                <h2 className="font-semibold text-sm">EmbedAI Admin</h2>
                <p className="text-xs text-muted-foreground">管理控制台</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={() => setOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 px-4">
            <div className="space-y-2 py-4">
              {navItems.map((item) => {
                const Icon = item.icon
                const active = isActive(item.href)
                
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors',
                      'hover:bg-accent hover:text-accent-foreground',
                      active 
                        ? 'bg-accent text-accent-foreground font-medium' 
                        : 'text-muted-foreground'
                    )}
                    onClick={() => setOpen(false)}
                  >
                    <Icon className="h-4 w-4 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="truncate">{item.title}</span>
                        {item.badge && (
                          <Badge variant="secondary" className="ml-2 h-5 px-1.5 text-xs">
                            {item.badge}
                          </Badge>
                        )}
                      </div>
                      {item.description && (
                        <p className="text-xs text-muted-foreground mt-0.5 truncate">
                          {item.description}
                        </p>
                      )}
                    </div>
                  </Link>
                )
              })}
            </div>
          </ScrollArea>

          {/* Footer */}
          <div className="border-t p-4">
            <div className="text-xs text-muted-foreground text-center">
              <p>版本 1.0.0</p>
              <p className="mt-1">© 2024 EmbedAI</p>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}