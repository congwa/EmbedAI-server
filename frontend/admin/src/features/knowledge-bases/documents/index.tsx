import { useState } from 'react'
import { Link, useParams } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { useToast } from '@/hooks/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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
import { ArrowLeft, Plus, Search } from 'lucide-react'
import { Document, DocumentType, CreateDocumentRequest, UpdateDocumentRequest } from '@/services/types'
import { DocumentEditDialog } from './document-edit-dialog'
import { DocumentPagination } from './document-pagination'
import { DocumentUpload } from './document-upload'
import { KnowledgeBaseQuery } from '../components/knowledge-base-query'
import { KnowledgeBaseTraining } from '../components/knowledge-base-training'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function KnowledgeBaseDocumentsPage() {
  const { id } = useParams({ from: '/_authenticated/knowledge-bases/$id/documents/' })
  const { toast } = useToast()
  const [searchParams, setSearchParams] = useState({
    title: '',
    doc_type: undefined as DocumentType | undefined,
    start_time: '',
    end_time: '',
  })
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document>()

  // 获取知识库信息
  const { data: knowledgeBase } = useQuery({
    queryKey: ['knowledge-base', id],
    queryFn: () => adminService.getKnowledgeBase(Number(id)),
    enabled: !!id,
  })

  // 获取文档列表
  const { data: documentsData, refetch } = useQuery({
    queryKey: ['documents', id, searchParams, page, pageSize],
    queryFn: () =>
      adminService.getDocuments({
        knowledge_base_id: Number(id),
        skip: (page - 1) * pageSize,
        limit: pageSize,
        title: searchParams.title || undefined,
        doc_type: searchParams.doc_type,
        start_time: searchParams.start_time || undefined,
        end_time: searchParams.end_time || undefined,
      }),
    enabled: !!id,
  })

  const handleSearch = () => {
    setPage(1)
    refetch()
  }

  const handleReset = () => {
    setSearchParams({
      title: '',
      doc_type: undefined,
      start_time: '',
      end_time: '',
    })
    setPage(1)
    refetch()
  }

  const handleCreateOrUpdate = async (values: CreateDocumentRequest | UpdateDocumentRequest) => {
    try {
      if (selectedDocument) {
        await adminService.updateDocument(selectedDocument.id, values as UpdateDocumentRequest)
        toast({
          title: '更新文档成功',
        })
      } else {
        await adminService.createTextDocument(values as CreateDocumentRequest, Number(id))
        toast({
          title: '创建文档成功',
        })
      }
      setEditDialogOpen(false)
      refetch()
    } catch (_error) {
      toast({
        variant: 'destructive',
        title: selectedDocument ? '更新文档失败' : '创建文档失败',
        description: '请稍后重试',
      })
    }
  }

  const handleDelete = async () => {
    if (!selectedDocument) return
    try {
      await adminService.deleteDocument(selectedDocument.id)
      toast({
        title: '删除文档成功',
      })
      setDeleteDialogOpen(false)
      refetch()
    } catch (_error) {
      toast({
        variant: 'destructive',
        title: '删除文档失败',
        description: '请稍后重试',
      })
    }
  }

  const handleReprocess = async (document: Document) => {
    try {
      await adminService.reprocessDocument(document.id)
      toast({
        title: '重新处理成功',
        description: `${document.title} 已开始重新处理`,
      })
      refetch()
    } catch (_error) {
      toast({
        variant: 'destructive',
        title: '重新处理失败',
        description: '请稍后重试',
      })
    }
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
  }

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize)
    setPage(1) // 重置到第一页
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center gap-4 mb-6">
        <Link to="/knowledge-bases">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <h1 className="text-2xl font-bold">
          {knowledgeBase?.data.name}
        </h1>
      </div>

      <Tabs defaultValue="documents" className="space-y-6">
        <TabsList>
          <TabsTrigger value="documents">文档管理</TabsTrigger>
          <TabsTrigger value="training">训练管理</TabsTrigger>
          <TabsTrigger value="query">查询测试</TabsTrigger>
        </TabsList>
        
        <TabsContent value="documents" className="space-y-6">

      <div className="space-y-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <Input
              placeholder="搜索文档标题"
              value={searchParams.title}
              onChange={(e) =>
                setSearchParams((prev) => ({ ...prev, title: e.target.value }))
              }
            />
          </div>
          <Select
            value={searchParams.doc_type}
            onValueChange={(value) =>
              setSearchParams((prev) => ({
                ...prev,
                doc_type: value as DocumentType | undefined,
              }))
            }
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="文档类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">全部</SelectItem>
              <SelectItem value={DocumentType.TEXT}>文本</SelectItem>
              <SelectItem value={DocumentType.WEBPAGE}>网页</SelectItem>
              <SelectItem value={DocumentType.PDF}>PDF</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleSearch} className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            搜索
          </Button>
          <Button variant="outline" onClick={handleReset}>
            重置
          </Button>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">创建时间:</label>
            <Input
              type="date"
              value={searchParams.start_time}
              onChange={(e) =>
                setSearchParams((prev) => ({ ...prev, start_time: e.target.value }))
              }
              className="w-[150px]"
            />
            <span className="text-sm text-muted-foreground">至</span>
            <Input
              type="date"
              value={searchParams.end_time}
              onChange={(e) =>
                setSearchParams((prev) => ({ ...prev, end_time: e.target.value }))
              }
              className="w-[150px]"
            />
          </div>
          
          <div className="ml-auto flex gap-2">
            <Button
              onClick={() => setUploadDialogOpen(true)}
              className="flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              上传文档
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setSelectedDocument(undefined)
                setEditDialogOpen(true)
              }}
              className="flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              创建文本
            </Button>
          </div>
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>标题</TableHead>
            <TableHead>类型</TableHead>
            <TableHead>字数</TableHead>
            <TableHead>分块数</TableHead>
            <TableHead>创建时间</TableHead>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {!documentsData?.data.items.length ? (
            <TableRow>
              <TableCell colSpan={7} className="h-24 text-center">
                <div className="flex flex-col items-center justify-center text-sm text-muted-foreground">
                  <p>暂无文档数据</p>
                  <p>点击右上角"创建文档"按钮开始创建</p>
                </div>
              </TableCell>
            </TableRow>
          ) : (
            documentsData?.data.items.map((doc) => (
              <TableRow key={doc.id}>
                <TableCell>{doc.id}</TableCell>
                <TableCell>{doc.title}</TableCell>
                <TableCell>{doc.doc_type}</TableCell>
                <TableCell>{doc.word_count}</TableCell>
                <TableCell>{doc.chunk_count}</TableCell>
                <TableCell>
                  {new Date(doc.created_at).toLocaleString()}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedDocument(doc)
                        setEditDialogOpen(true)
                      }}
                    >
                      编辑
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleReprocess(doc)}
                    >
                      重新处理
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-500"
                      onClick={() => {
                        setSelectedDocument(doc)
                        setDeleteDialogOpen(true)
                      }}
                    >
                      删除
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      {documentsData?.data.pagination && documentsData.data.pagination.total > pageSize && (
        <DocumentPagination
          page={page}
          pageSize={pageSize}
          total={documentsData.data.pagination.total}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />
      )}

      <DocumentUpload
        knowledgeBaseId={Number(id)}
        open={uploadDialogOpen}
        onOpenChange={setUploadDialogOpen}
        onUploadComplete={() => {
          refetch()
          setUploadDialogOpen(false)
        }}
      />

      <DocumentEditDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        document={selectedDocument}
        onSubmit={handleCreateOrUpdate}
      />

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除文档？</AlertDialogTitle>
            <AlertDialogDescription>
              此操作将永久删除该文档，无法恢复。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>确认删除</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
        </TabsContent>
        
        <TabsContent value="training">
          {knowledgeBase?.data && (
            <KnowledgeBaseTraining
              knowledgeBaseId={Number(id)}
              knowledgeBaseName={knowledgeBase.data.name}
              currentStatus={knowledgeBase.data.status}
              onStatusChange={(status) => {
                // 可以在这里处理状态变化，比如刷新数据
                
              }}
            />
          )}
        </TabsContent>
        
        <TabsContent value="query">
          {knowledgeBase?.data && (
            <KnowledgeBaseQuery
              knowledgeBaseId={Number(id)}
              knowledgeBaseName={knowledgeBase.data.name}
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
} 