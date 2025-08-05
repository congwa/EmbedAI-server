import { ReactNode } from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import { ChevronRight, ChevronDown } from 'lucide-react'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  useSidebar,
} from '@/components/ui/sidebar'
import { Badge } from '../ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu'
import {
  type NavGroup,
  type NavItem,
  type NavLink,
  type NavCollapsible,
} from './types'
import { useAuth } from '@/stores/authStore'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

export function NavGroup({ title, items }: NavGroup) {
  const { state } = useSidebar()
  const href = useLocation({ select: (location) => location.href })
  const { isAdmin } = useAuth()

  // 过滤需要管理员权限的菜单项
  const filteredItems = items.filter(item => {
    if (item.adminOnly) {
      return isAdmin
    }
    return true
  })

  return (
    <SidebarGroup>
      <SidebarGroupLabel>{title}</SidebarGroupLabel>
      <SidebarMenu>
        {filteredItems.map((item) => {
          const key = `${item.title}-${item.url}`

          if ('url' in item && !item.items)
            return <SidebarMenuLink key={key} item={item as NavLink} href={href} />

          if (state === 'collapsed')
            return (
              <SidebarMenuCollapsedDropdown key={key} item={item as NavCollapsible} href={href} />
            )

          return <SidebarMenuCollapsible key={key} item={item as NavCollapsible} href={href} />
        })}
      </SidebarMenu>
    </SidebarGroup>
  )
}

const NavBadge = ({ children }: { children: ReactNode }) => (
  <Badge className='rounded-full px-1 py-0 text-xs'>{children}</Badge>
)

const SidebarMenuLink = ({ item, href }: { item: NavLink; href: string }) => {
  const { setOpenMobile } = useSidebar()
  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        asChild
        isActive={checkIsActive(href, item)}
        tooltip={item.title}
      >
        <Link to={item.url} onClick={() => setOpenMobile(false)}>
          {item.icon && <item.icon />}
          <span>{item.title}</span>
          {item.badge && <NavBadge>{item.badge}</NavBadge>}
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}

const SidebarMenuCollapsible = ({
  item,
  href,
}: {
  item: NavCollapsible
  href: string
}) => {
  const { setOpenMobile } = useSidebar()
  const { isAdmin } = useAuth()

  // 过滤需要管理员权限的子菜单项
  const filteredItems = item.items.filter(subItem => {
    if (subItem.adminOnly) {
      return isAdmin
    }
    return true
  })

  return (
    <Collapsible
      asChild
      defaultOpen={checkIsActive(href, item, true)}
      className='group/collapsible'
    >
      <SidebarMenuItem>
        <CollapsibleTrigger asChild>
          <SidebarMenuButton tooltip={item.title}>
            {item.icon && <item.icon />}
            <span>{item.title}</span>
            {item.badge && <NavBadge>{item.badge}</NavBadge>}
            <ChevronRight className='ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90' />
          </SidebarMenuButton>
        </CollapsibleTrigger>
        <CollapsibleContent className='CollapsibleContent'>
          <SidebarMenuSub>
            {filteredItems.map((subItem) => (
              <SidebarMenuSubItem key={subItem.title}>
                <SidebarMenuSubButton
                  asChild
                  isActive={checkIsActive(href, subItem)}
                >
                  <Link to={subItem.url} onClick={() => setOpenMobile(false)}>
                    {subItem.icon && <subItem.icon />}
                    <span>{subItem.title}</span>
                    {subItem.badge && <NavBadge>{subItem.badge}</NavBadge>}
                  </Link>
                </SidebarMenuSubButton>
              </SidebarMenuSubItem>
            ))}
          </SidebarMenuSub>
        </CollapsibleContent>
      </SidebarMenuItem>
    </Collapsible>
  )
}

const SidebarMenuCollapsedDropdown = ({
  item,
  href,
}: {
  item: NavCollapsible
  href: string
}) => {

  return (
    <SidebarMenuItem>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <SidebarMenuButton
            tooltip={item.title}
            isActive={checkIsActive(href, item)}
          >
            {item.icon && <item.icon />}
            <span>{item.title}</span>
            {item.badge && <NavBadge>{item.badge}</NavBadge>}
            <ChevronRight className='ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90' />
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent side='right' align='start' sideOffset={4}>
          <DropdownMenuLabel>
            {item.title} {item.badge ? `(${item.badge})` : ''}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          {item.items.map((sub) => (
            <DropdownMenuItem key={`${sub.title}-${sub.url}`} asChild>
              <Link
                to={sub.url}
                className={`${checkIsActive(href, sub) ? 'bg-secondary' : ''}`}
              >
                {sub.icon && <sub.icon />}
                <span className='max-w-52 text-wrap'>{sub.title}</span>
                {sub.badge && (
                  <span className='ml-auto text-xs'>{sub.badge}</span>
                )}
              </Link>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  )
}

function checkIsActive(href: string, item: NavItem, mainNav = false) {
  if ('url' in item) {
    return (
      href === item.url || // /endpint?search=param
      href.split('?')[0] === item.url // endpoint
    )
  }

  if ('items' in item) {
    return (
      !!item.items.filter((i) => i.url === href).length || // if child nav is active
      (mainNav &&
        href.split('/')[1] !== '' &&
        item.items.some(i => href.split('/')[1] === i.url?.split('/')[1]))
    )
  }

  return false
}

function NavCollapsible({ title, icon: Icon, items = [] }: NavItem) {
  const { isAdmin } = useAuth()

  // 过滤需要管理员权限的子菜单项
  const filteredItems = items.filter(item => {
    if (item.adminOnly) {
      return isAdmin
    }
    return true
  })

  return (
    <Collapsible>
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          className={cn(
            'group relative flex w-full justify-between px-4 py-2 hover:bg-accent hover:text-accent-foreground'
          )}
        >
          <div className="flex items-center gap-x-3">
            {Icon && <Icon className="h-4 w-4" />}
            <span>{title}</span>
          </div>
          <ChevronDown className="h-4 w-4 shrink-0 transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="space-y-1">
        {filteredItems.map((item, index) => (
          <NavLink key={index} {...item} nested />
        ))}
      </CollapsibleContent>
    </Collapsible>
  )
}

function NavLink({
  title,
  url,
  icon: Icon,
  badge,
  nested,
}: NavItem & { nested?: boolean }) {
  return (
    <Button
      asChild
      variant="ghost"
      className={cn(
        'group relative flex w-full justify-between hover:bg-accent hover:text-accent-foreground',
        nested ? 'pl-11' : 'px-4',
        'py-2'
      )}
    >
      <Link to={url!}>
        <div className="flex items-center gap-x-3">
          {Icon && <Icon className="h-4 w-4" />}
          <span>{title}</span>
        </div>
        {badge && (
          <span className="absolute right-2 top-[50%] translate-y-[-50%] text-xs">
            {badge}
          </span>
        )}
      </Link>
    </Button>
  )
}
