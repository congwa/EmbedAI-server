import { useState } from 'react'
import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface KnowledgeBaseSearchProps {
  onSearch: (params: { name?: string }) => void
}

export function KnowledgeBaseSearch({ onSearch }: KnowledgeBaseSearchProps) {
  const [name, setName] = useState('')

  const handleSearch = () => {
    onSearch({
      name: name || undefined,
    })
  }

  const handleReset = () => {
    setName('')
    onSearch({})
  }

  return (
    <div className="flex items-center space-x-4 mb-4">
      <div className="flex-1">
        <Input
          placeholder="搜索知识库名称"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
      </div>
      <Button onClick={handleSearch} className="flex items-center gap-2">
        <Search className="h-4 w-4" />
        搜索
      </Button>
      <Button variant="outline" onClick={handleReset}>
        重置
      </Button>
    </div>
  )
} 