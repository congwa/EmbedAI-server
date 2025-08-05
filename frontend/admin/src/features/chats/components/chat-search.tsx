import { useState } from 'react'
import { Search, Filter, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
import { ChatStatus } from '@/services/types'

interface ChatSearchProps {
  onSearch: (params: {
    user_id?: number // 修正为数字类型
    knowledge_base_id?: number
    status?: ChatStatus
    include_inactive?: boolean
  }) => void
  onReset: () => void
}

export function ChatSearch({ onSearch, onReset }: ChatSearchProps) {
  const [userId, setUserId] = useState('')
  const [knowledgeBaseId, setKnowledgeBaseId] = useState('')
  const [status, setStatus] = useState<ChatStatus | ''>('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [isFilterOpen, setIsFilterOpen] = useState(false)

  const handleSearch = () => {
    onSearch({
      user_id: userId ? Number(userId) : undefined, // 转换为数字
      knowledge_base_id: knowledgeBaseId ? Number(knowledgeBaseId) : undefined,
      status: status || undefined,
      include_inactive: includeInactive,
    })
    setIsFilterOpen(false)
  }

  const handleReset = () => {
    setUserId('')
    setKnowledgeBaseId('')
    setStatus('')
    setIncludeInactive(false)
    onReset()
    setIsFilterOpen(false)
  }

  const hasActiveFilters = userId || knowledgeBaseId || status || includeInactive

  return (
    <div className="flex items-center space-x-4 mb-4">
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="搜索用户ID或邮箱"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="pl-10"
        />
      </div>
      
      <Popover open={isFilterOpen} onOpenChange={setIsFilterOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            高级筛选
            {hasActiveFilters && (
              <Badge variant="secondary" className="ml-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs">
                !
              </Badge>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="end">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-medium">筛选条件</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsFilterOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium mb-2 block">知识库ID</label>
                <Input
                  placeholder="输入知识库ID"
                  value={knowledgeBaseId}
                  onChange={(e) => setKnowledgeBaseId(e.target.value)}
                  type="number"
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">聊天状态</label>
                <Select value={status} onValueChange={(value) => setStatus(value as ChatStatus | '')}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择状态" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">全部状态</SelectItem>
                    <SelectItem value={ChatStatus.ACTIVE}>活跃</SelectItem>
                    <SelectItem value={ChatStatus.INACTIVE}>非活跃</SelectItem>
                    <SelectItem value={ChatStatus.ARCHIVED}>已归档</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="include-inactive"
                  checked={includeInactive}
                  onChange={(e) => setIncludeInactive(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="include-inactive" className="text-sm">
                  包含非活跃聊天
                </label>
              </div>
            </div>
            
            <div className="flex space-x-2 pt-2">
              <Button onClick={handleSearch} className="flex-1">
                应用筛选
              </Button>
              <Button variant="outline" onClick={handleReset}>
                重置
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
      
      <Button onClick={handleSearch} className="flex items-center gap-2">
        <Search className="h-4 w-4" />
        搜索
      </Button>
      
      {hasActiveFilters && (
        <Button variant="outline" onClick={handleReset}>
          重置
        </Button>
      )}
    </div>
  )
}