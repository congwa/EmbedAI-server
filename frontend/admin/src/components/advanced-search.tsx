import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Calendar,
  CalendarIcon,
  Filter,
  X,
  Search,
  RotateCcw,
} from 'lucide-react'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { cn } from '@/lib/utils'

interface SearchFilter {
  key: string
  label: string
  type: 'text' | 'select' | 'date' | 'dateRange' | 'number'
  options?: Array<{ value: string; label: string }>
  placeholder?: string
  value?: any
}

interface AdvancedSearchProps {
  filters: SearchFilter[]
  onSearch: (filters: Record<string, any>) => void
  onReset: () => void
  className?: string
  defaultExpanded?: boolean
}

export function AdvancedSearch({
  filters,
  onSearch,
  onReset,
  className,
  defaultExpanded = false,
}: AdvancedSearchProps) {
  const [expanded, setExpanded] = useState(defaultExpanded)
  const [filterValues, setFilterValues] = useState<Record<string, any>>({})
  const [quickSearch, setQuickSearch] = useState('')

  const handleFilterChange = (key: string, value: any) => {
    const newValues = { ...filterValues, [key]: value }
    if (value === '' || value === null || value === undefined) {
      delete newValues[key]
    }
    setFilterValues(newValues)
  }

  const handleSearch = () => {
    const searchParams = { ...filterValues }
    if (quickSearch.trim()) {
      searchParams.q = quickSearch.trim()
    }
    onSearch(searchParams)
  }

  const handleReset = () => {
    setFilterValues({})
    setQuickSearch('')
    onReset()
  }

  const getActiveFilterCount = () => {
    let count = Object.keys(filterValues).length
    if (quickSearch.trim()) count++
    return count
  }

  const renderFilter = (filter: SearchFilter) => {
    const value = filterValues[filter.key] || filter.value

    switch (filter.type) {
      case 'text':
        return (
          <Input
            placeholder={filter.placeholder}
            value={value || ''}
            onChange={(e) => handleFilterChange(filter.key, e.target.value)}
          />
        )

      case 'select':
        return (
          <Select
            value={value || ''}
            onValueChange={(val) => handleFilterChange(filter.key, val)}
          >
            <SelectTrigger>
              <SelectValue placeholder={filter.placeholder || '选择...'} />
            </SelectTrigger>
            <SelectContent>
              {filter.options?.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )

      case 'date':
        return (
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  'w-full justify-start text-left font-normal',
                  !value && 'text-muted-foreground'
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {value ? format(new Date(value), 'PPP', { locale: zhCN }) : filter.placeholder}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0">
              <Calendar
                mode="single"
                selected={value ? new Date(value) : undefined}
                onSelect={(date) => handleFilterChange(filter.key, date?.toISOString())}
                initialFocus
              />
            </PopoverContent>
          </Popover>
        )

      case 'number':
        return (
          <Input
            type="number"
            placeholder={filter.placeholder}
            value={value || ''}
            onChange={(e) => handleFilterChange(filter.key, e.target.value)}
          />
        )

      default:
        return null
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Search className="h-4 w-4" />
            高级搜索
            {getActiveFilterCount() > 0 && (
              <Badge variant="secondary" className="h-5 px-2 text-xs">
                {getActiveFilterCount()}
              </Badge>
            )}
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="h-8 px-2"
          >
            <Filter className={cn('h-4 w-4 transition-transform', expanded && 'rotate-180')} />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 快速搜索 */}
        <div className="flex gap-2">
          <div className="flex-1">
            <Input
              placeholder="快速搜索..."
              value={quickSearch}
              onChange={(e) => setQuickSearch(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <Button onClick={handleSearch} size="sm" className="px-3">
            <Search className="h-4 w-4" />
          </Button>
        </div>

        {/* 高级过滤器 */}
        {expanded && (
          <>
            <Separator />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filters.map((filter) => (
                <div key={filter.key} className="space-y-2">
                  <Label htmlFor={filter.key} className="text-sm font-medium">
                    {filter.label}
                  </Label>
                  {renderFilter(filter)}
                </div>
              ))}
            </div>

            {/* 操作按钮 */}
            <div className="flex items-center justify-between pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                className="gap-2"
              >
                <RotateCcw className="h-3 w-3" />
                重置
              </Button>
              
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setExpanded(false)}>
                  收起
                </Button>
                <Button size="sm" onClick={handleSearch}>
                  搜索
                </Button>
              </div>
            </div>
          </>
        )}

        {/* 活跃过滤器显示 */}
        {getActiveFilterCount() > 0 && !expanded && (
          <div className="flex flex-wrap gap-2">
            {quickSearch && (
              <Badge variant="secondary" className="gap-1">
                搜索: {quickSearch}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => setQuickSearch('')}
                />
              </Badge>
            )}
            {Object.entries(filterValues).map(([key, value]) => {
              const filter = filters.find(f => f.key === key)
              if (!filter || !value) return null
              
              let displayValue = value
              if (filter.type === 'select') {
                const option = filter.options?.find(o => o.value === value)
                displayValue = option?.label || value
              } else if (filter.type === 'date') {
                displayValue = format(new Date(value), 'MM/dd', { locale: zhCN })
              }

              return (
                <Badge key={key} variant="secondary" className="gap-1">
                  {filter.label}: {displayValue}
                  <X
                    className="h-3 w-3 cursor-pointer"
                    onClick={() => handleFilterChange(key, null)}
                  />
                </Badge>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// 预定义的搜索过滤器配置
export const chatSearchFilters: SearchFilter[] = [
  {
    key: 'user_id',
    label: '用户ID',
    type: 'text',
    placeholder: '输入用户ID',
  },
  {
    key: 'knowledge_base_id',
    label: '知识库',
    type: 'text',
    placeholder: '输入知识库ID',
  },
  {
    key: 'status',
    label: '状态',
    type: 'select',
    options: [
      { value: 'active', label: '活跃' },
      { value: 'deleted', label: '已删除' },
    ],
  },
  {
    key: 'created_after',
    label: '创建时间（从）',
    type: 'date',
    placeholder: '选择开始日期',
  },
  {
    key: 'created_before',
    label: '创建时间（到）',
    type: 'date',
    placeholder: '选择结束日期',
  },
  {
    key: 'min_messages',
    label: '最少消息数',
    type: 'number',
    placeholder: '输入数字',
  },
]

export const userSearchFilters: SearchFilter[] = [
  {
    key: 'email',
    label: '邮箱',
    type: 'text',
    placeholder: '输入邮箱地址',
  },
  {
    key: 'is_active',
    label: '状态',
    type: 'select',
    options: [
      { value: 'true', label: '活跃' },
      { value: 'false', label: '已禁用' },
    ],
  },
  {
    key: 'is_admin',
    label: '权限',
    type: 'select',
    options: [
      { value: 'true', label: '管理员' },
      { value: 'false', label: '普通用户' },
    ],
  },
  {
    key: 'created_after',
    label: '注册时间（从）',
    type: 'date',
    placeholder: '选择开始日期',
  },
  {
    key: 'created_before',
    label: '注册时间（到）',
    type: 'date',
    placeholder: '选择结束日期',
  },
]

export const knowledgeBaseSearchFilters: SearchFilter[] = [
  {
    key: 'name',
    label: '名称',
    type: 'text',
    placeholder: '输入知识库名称',
  },
  {
    key: 'status',
    label: '状态',
    type: 'select',
    options: [
      { value: 'ready', label: '就绪' },
      { value: 'training', label: '训练中' },
      { value: 'error', label: '错误' },
    ],
  },
  {
    key: 'created_after',
    label: '创建时间（从）',
    type: 'date',
    placeholder: '选择开始日期',
  },
  {
    key: 'created_before',
    label: '创建时间（到）',
    type: 'date',
    placeholder: '选择结束日期',
  },
  {
    key: 'min_documents',
    label: '最少文档数',
    type: 'number',
    placeholder: '输入数字',
  },
]