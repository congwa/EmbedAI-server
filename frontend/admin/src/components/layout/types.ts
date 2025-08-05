import { type LucideIcon } from 'lucide-react'
import { type Icon } from '@tabler/icons-react'
import { type LinkProps } from '@tanstack/react-router'

export interface User {
  name: string
  email: string
  avatar: string
}

export interface Team {
  name: string
  logo: LucideIcon
  plan: string
}

export interface BaseNavItem {
  title: string
  badge?: string
  icon?: Icon | LucideIcon
  adminOnly?: boolean
}

export interface NavLink extends BaseNavItem {
  url: LinkProps['to']
  items?: never
}

export interface NavCollapsible extends BaseNavItem {
  items: NavLink[]
  url?: never
}

export type NavItem = NavLink | NavCollapsible

export interface NavGroup {
  title: string
  items: NavItem[]
}

export interface SidebarData {
  // user: User
  // teams: Team[]
  navGroups: NavGroup[]
}
