import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useToast } from '@/hooks/use-toast'
import { useAuth } from '@/stores/authStore'
import { adminService } from '@/services/admin'
import { KnowledgeBaseDetail, PermissionType } from '@/services/types'
import { KnowledgeBaseSearch } from './components/knowledge-base-search'
import { KnowledgeBaseTable } from './components/knowledge-base-table'
import { KnowledgeBaseEditDialog } from './components/knowledge-base-edit-dialog'
import { KnowledgeBaseUsersDialog } from './components/knowledge-base-users-dialog'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import React from 'react'

export function KnowledgeBasesPage() {
  const { toast } = useToast()
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useState<{ name?: string }>({})
  const [page, setPage] = useState(1)
  const pageSize = 10
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [usersDialogOpen, setUsersDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<KnowledgeBaseDetail>()

  // 获取知识库列表
  const { data: knowledgeBasesData, refetch } = useQuery({
    queryKey: ['knowledge-bases', searchParams],
    queryFn: () => adminService.getMyKnowledgeBases(),
    enabled: !!user,
  })

  // 将 handleSearch 移到 useMemo 外部并使用 useCallback
  const handleSearch = React.useCallback((params: { name?: string }) => {
    setSearchParams(params)
    const filteredData = knowledgeBasesData?.data.filter(kb => 
      !params.name || kb.name.toLowerCase().includes(params.name.toLowerCase())
    )
    return filteredData || []
  }, [knowledgeBasesData?.data])

  // 获取当前显示的知识库列表
  const currentKnowledgeBases = React.useMemo(() => {
    const filteredData = handleSearch(searchParams)
    const start = (page - 1) * pageSize
    const end = start + pageSize
    return filteredData.slice(start, end)
  }, [handleSearch, searchParams, page, pageSize])

  // 获取总数
  const total = React.useMemo(() => {
    return handleSearch(searchParams).length
  }, [handleSearch, searchParams])

  const handleCreateOrUpdate = async (values: {
    name: string
    domain: string
    example_queries?: string[]
    entity_types?: string[]
    llm_config?: {
      llm: {
        model: string
        base_url: string
        api_key: string
      }
      embeddings: {
        model: string
        base_url: string
        api_key: string
        embedding_dim: number
      }
    }
  }) => {
    try {
      if (selectedKnowledgeBase) {
        await adminService.updateKnowledgeBase(selectedKnowledgeBase.id, values)
        toast({
          title: '更新知识库成功',
        })
      } else {
        await adminService.createKnowledgeBase(values)
        toast({
          title: '创建知识库成功',
        })
      }
      setEditDialogOpen(false)
      refetch()
    } catch (_error) {
      toast({
        variant: 'destructive',
        title: selectedKnowledgeBase ? '更新知识库失败' : '创建知识库失败',
        description: '请稍后重试',
      })
    }
  }

  const handleDelete = async () => {
    if (!selectedKnowledgeBase) return
    try {
      await adminService.deleteKnowledgeBase(selectedKnowledgeBase.id)
      toast({
        title: '删除知识库成功',
      })
      setDeleteDialogOpen(false)
      refetch()
    } catch (_error) {
      toast({
        variant: 'destructive',
        title: '删除知识库失败',
        description: '请稍后重试',
      })
    }
  }

  const handleAddUser = async (_email: string, permission: PermissionType) => {
    if (!selectedKnowledgeBase) return
    try {
      await adminService.addKnowledgeBaseUser(selectedKnowledgeBase.id, {
        user_id: 0, // 后端会根据email查找用户
        permission,
      })
      toast({
        title: '添加成员成功',
      })
      refetch()
    } catch (_error) {
      toast({
        variant: 'destructive',
        title: '添加成员失败',
        description: '请确认用户邮箱是否正确',
      })
    }
  }

  const handleUpdatePermission = async (userId: number, permission: PermissionType) => {
    if (!selectedKnowledgeBase) return
    try {
      await adminService.updateKnowledgeBaseUserPermission(
        selectedKnowledgeBase.id,
        userId,
        { permission }
      )
      toast({
        title: '更新权限成功',
      })
      refetch()
    } catch (_error) {
      toast({
        variant: 'destructive',
        title: '更新权限失败',
        description: '请稍后重试',
      })
    }
  }

  const handleRemoveUser = async (userId: number) => {
    if (!selectedKnowledgeBase) return
    try {
      await adminService.removeKnowledgeBaseUser(selectedKnowledgeBase.id, userId)
      toast({
        title: '移除成员成功',
      })
      refetch()
    } catch (_error) {
      toast({
        variant: 'destructive',
        title: '移除成员失败',
        description: '请稍后重试',
      })
    }
  }

  if (!user) {
    return null
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">知识库管理</h1>
        <Button
          onClick={() => {
            setSelectedKnowledgeBase(undefined)
            setEditDialogOpen(true)
          }}
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          创建知识库
        </Button>
      </div>
      <KnowledgeBaseSearch onSearch={handleSearch} />
      {currentKnowledgeBases && (
        <KnowledgeBaseTable
          data={currentKnowledgeBases}
          onEdit={(kb: KnowledgeBaseDetail) => {
            setSelectedKnowledgeBase(kb)
            setEditDialogOpen(true)
          }}
          onDelete={(kb: KnowledgeBaseDetail) => {
            setSelectedKnowledgeBase(kb)
            setDeleteDialogOpen(true)
          }}
          onManageUsers={(kb: KnowledgeBaseDetail) => {
            setSelectedKnowledgeBase(kb)
            setUsersDialogOpen(true)
          }}
        />
      )}
      {total > pageSize && (
        <div className="flex justify-end mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
          >
            上一页
          </Button>
          <div className="mx-4">
            第 {page} 页 / 共 {Math.ceil(total / pageSize)} 页
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(page + 1)}
            disabled={page * pageSize >= total}
          >
            下一页
          </Button>
        </div>
      )}
      <KnowledgeBaseEditDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        knowledgeBase={selectedKnowledgeBase}
        onSubmit={handleCreateOrUpdate}
      />
      {selectedKnowledgeBase && (
        <KnowledgeBaseUsersDialog
          open={usersDialogOpen}
          onOpenChange={setUsersDialogOpen}
          knowledgeBase={selectedKnowledgeBase}
          onAddUser={handleAddUser}
          onUpdatePermission={handleUpdatePermission}
          onRemoveUser={handleRemoveUser}
        />
      )}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除知识库？</AlertDialogTitle>
            <AlertDialogDescription>
              此操作将永久删除该知识库及其所有内容，无法恢复。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>确认删除</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
} 