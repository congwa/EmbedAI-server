import { SearchTrigger } from './search-trigger'
import { cn } from '@/lib/utils'

interface Props {
  className?: string
  placeholder?: string
  variant?: 'default' | 'compact' | 'icon'
}

export function Search({ className = '', variant = 'default' }: Props) {
  return (
    <SearchTrigger 
      className={className}
      variant={variant}
    />
  )
}
