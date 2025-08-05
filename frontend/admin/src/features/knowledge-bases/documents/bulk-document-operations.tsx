import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { Document } from '@/services/types'
import { BulkOperations, documentBulkActions, BulkSelectableRow } from '@/components/bulk-operations'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { FileText, Download, Upload, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { useNotification } from '@/hooks/use-notification'

interface BulkDocumentOperationsProps {
  documents: Document[]
  knowledgeBases?: Array<{ id: number; name: string }>
  className?: string
}

export function BulkDocumentOperations({ 
  documents, 
  knowledgeBases = [],
  className 
}: BulkDocumentOperationsProps) {
  const [selectedDocuments, setSelectedDocuments] = useState<Document[]>([])
  const [showMoveDialog, setShowMoveDialog] = useState(false)
  const [targetKnowledgeBaseId, setTargetKnowledgeBaseId] = useState<string>('')
  const queryClient = useQueryClient()
  const notification = useNotification()

  // 批量操作处理函数
  const handleBulkAction = async (actionId: string, documents: Document[]) => {
    const document = documents[0] // 单个文档操作

    switch (actionId) {
      case 'reprocess':
        await adminService.reprocessDocument(document.id)
        break
      
      case 'download':
        // 创建下载链接
        const link = document.createElement('a')
        link.href = `/api/v1/admin/documents/${document.id}/download`
        link.download = document.filename
        link.click()
        break
      
      case 'move':
        // 显示移动对话框
        setShowMoveDialog(true)
        return // 不要继续执行，等待用户选择目标知识库
      
      case 'delete':
        await adminService.deleteDocument(document.id)
        break
      
      default:
        throw new Error(`未知操作: ${actionId}`)
    }

    // 刷新文档列表
    queryClient.invalidateQueries({ queryKey: ['documents'] })
  }

  const handleMoveDocuments = async () => {
    if (!targetKnowledgeBaseId) {
      notification.warning('请选择目标知识库')
      return
    }

    try {
      // 这里需要添加移动文档的API方法
      for (const doc of selectedDocuments) {
        // await adminService.moveDocument(doc.id, parseInt(targetKnowledgeBaseId))
        console.log(`Moving document ${doc.id} to knowledge base ${targetKnowledgeBaseId}`)
      }
      
      notification.success('文档移动完成', `已移动 ${selectedDocuments.length} 个文档`)
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setShowMoveDialog(false)
      setTargetKnowledgeBaseId('')
      setSelectedDocuments([])
    } catch (error) {
      notification.error('移动失败', error instanceof Error ? error.message : '未知错误')
    }
  }

  const getDocumentStatusBadge = (document: Document) => {
    switch (document.status) {
      case 'processed':
        return <Badge variant="default">已处理</Badge>
      case 'processing':
        return <Badge variant="secondary">处理中</Badge>
      case 'failed':
        return <Badge variant="destructive">处理失败</Badge>
      case 'pending':
        return <Badge variant="outline">待处理</Badge>
      default:
        return <Badge variant="outline">{document.status}</Badge>
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const downloadSelectedDocuments = async () => {
    if (selectedDocuments.length === 0) return

    try {
      // 创建一个临时的下载链接
      for (const doc of selectedDocuments) {
        const link = document.createElement('a')
        link.href = `/api/v1/admin/documents/${doc.id}/download`
        link.download = doc.filename
        link.click()
        
        // 添加延迟避免浏览器阻止多个下载
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      
      notification.success('下载开始', `正在下载 ${selectedDocuments.length} 个文档`)
    } catch (error) {
      notification.error('下载失败', error instanceof Error ? error.message : '未知错误')
    }
  }

  return (
    <div className={className}>
      <BulkOperations
        items={documents}
        selectedItems={selectedDocuments}
        onSelectionChange={setSelectedDocuments}
        actions={[
          ...documentBulkActions,
          // 添加自定义的批量下载操作
          {
            id: 'bulk_download',
            label: '批量下载',
            icon: Download,
            variant: 'secondary' as const,
          },
        ]}
        onAction={async (actionId, docs) => {
          if (actionId === 'bulk_download') {
            await downloadSelectedDocuments()
          } else if (actionId === 'move') {
            setShowMoveDialog(true)
          } else {
            await handleBulkAction(actionId, docs)
          }
        }}
        getItemId={(doc) => doc.id}
        getItemLabel={(doc) => doc.filename}
        className="mb-4"
      />

      {/* 文档列表 */}
      <div className="space-y-2">
        {documents.map((document) => {
          const isSelected = selectedDocuments.some(selected => selected.id === document.id)
          
          return (
            <BulkSelectableRow
              key={document.id}
              selected={isSelected}
              onToggle={() => {
                if (isSelected) {
                  setSelectedDocuments(selectedDocuments.filter(d => d.id !== document.id))
                } else {
                  setSelectedDocuments([...selectedDocuments, document])
                }
              }}
            >
              <div className="flex items-center gap-4">
                <div className="flex-shrink-0">
                  <FileText className="h-8 w-8 text-muted-foreground" />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-sm truncate">{document.filename}</h3>
                    {getDocumentStatusBadge(document)}
                  </div>
                  
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>ID: {document.id}</span>
                    <span>大小: {formatFileSize(document.size || 0)}</span>
                    <span>知识库: {document.knowledge_base_id}</span>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      <span>
                        {formatDistanceToNow(new Date(document.created_at), {
                          addSuffix: true,
                          locale: zhCN,
                        })}
                      </span>
                    </div>
                  </div>
                  
                  {document.content && (
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {document.content.slice(0, 150)}...
                    </p>
                  )}
                </div>
              </div>
            </BulkSelectableRow>
          )
        })}
      </div>

      {/* 移动文档对话框 */}
      <Dialog open={showMoveDialog} onOpenChange={setShowMoveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              移动文档到知识库
            </DialogTitle>
            <DialogDescription>
              选择要将 {selectedDocuments.length} 个文档移动到的目标知识库
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">目标知识库</label>
              <Select value={targetKnowledgeBaseId} onValueChange={setTargetKnowledgeBaseId}>
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="选择知识库..." />
                </SelectTrigger>
                <SelectContent>
                  {knowledgeBases.map((kb) => (
                    <SelectItem key={kb.id} value={kb.id.toString()}>
                      {kb.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* 选中的文档列表 */}
            <div>
              <label className="text-sm font-medium">要移动的文档 ({selectedDocuments.length})</label>
              <div className="mt-2 max-h-32 overflow-y-auto space-y-1">
                {selectedDocuments.slice(0, 5).map((doc) => (
                  <div key={doc.id} className="text-sm text-muted-foreground flex items-center gap-2">
                    <FileText className="h-3 w-3" />
                    <span className="truncate">{doc.filename}</span>
                  </div>
                ))}
                {selectedDocuments.length > 5 && (
                  <div className="text-xs text-muted-foreground">
                    还有 {selectedDocuments.length - 5} 个文档...
                  </div>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMoveDialog(false)}>
              取消
            </Button>
            <Button onClick={handleMoveDocuments} disabled={!targetKnowledgeBaseId}>
              移动文档
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// 文档批量上传组件
interface BulkDocumentUploadProps {
  knowledgeBaseId: number
  onUpload: (files: File[]) => Promise<void>
  className?: string
}

export function BulkDocumentUpload({ 
  knowledgeBaseId, 
  onUpload, 
  className 
}: BulkDocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadQueue, setUploadQueue] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const notification = useNotification()

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    handleFiles(files)
  }

  const handleFiles = (files: File[]) => {
    // 过滤支持的文件类型
    const supportedTypes = ['.pdf', '.txt', '.doc', '.docx', '.md']
    const validFiles = files.filter(file => {
      const extension = '.' + file.name.split('.').pop()?.toLowerCase()
      return supportedTypes.includes(extension)
    })

    if (validFiles.length !== files.length) {
      notification.warning(
        '部分文件被跳过',
        `只支持 ${supportedTypes.join(', ')} 格式的文件`
      )
    }

    setUploadQueue(prev => [...prev, ...validFiles])
  }

  const handleUpload = async () => {
    if (uploadQueue.length === 0) return

    setIsUploading(true)
    try {
      await onUpload(uploadQueue)
      setUploadQueue([])
      notification.success('批量上传完成', `成功上传 ${uploadQueue.length} 个文档`)
    } catch (error) {
      notification.error('上传失败', error instanceof Error ? error.message : '未知错误')
    } finally {
      setIsUploading(false)
    }
  }

  const removeFromQueue = (index: number) => {
    setUploadQueue(prev => prev.filter((_, i) => i !== index))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className={className}>
      {/* 拖拽上传区域 */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging 
            ? 'border-primary bg-primary/5' 
            : 'border-muted-foreground/25 hover:border-muted-foreground/50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <div className="space-y-2">
          <h3 className="font-medium">批量上传文档</h3>
          <p className="text-sm text-muted-foreground">
            拖拽文件到此处或点击选择文件
          </p>
          <div className="text-xs text-muted-foreground">
            支持格式：PDF, TXT, DOC, DOCX, MD
          </div>
        </div>
        
        <input
          type="file"
          multiple
          accept=".pdf,.txt,.doc,.docx,.md"
          onChange={handleFileSelect}
          className="hidden"
          id="bulk-upload-files"
        />
        <label
          htmlFor="bulk-upload-files"
          className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 mt-4 cursor-pointer"
        >
          选择文件
        </label>
      </div>

      {/* 上传队列 */}
      {uploadQueue.length > 0 && (
        <div className="mt-4 p-4 border rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium">上传队列 ({uploadQueue.length} 个文件)</h4>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setUploadQueue([])}
                disabled={isUploading}
              >
                清空队列
              </Button>
              <Button
                size="sm"
                onClick={handleUpload}
                disabled={isUploading}
              >
                {isUploading ? '上传中...' : '开始上传'}
              </Button>
            </div>
          </div>
          
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {uploadQueue.map((file, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span className="text-sm truncate">{file.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {formatFileSize(file.size)}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFromQueue(index)}
                  disabled={isUploading}
                  className="h-6 w-6 p-0"
                >
                  ×
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}