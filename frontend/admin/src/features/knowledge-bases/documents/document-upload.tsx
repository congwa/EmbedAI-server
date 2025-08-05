import React, { useState, useCallback, useRef, DragEvent } from 'react'
import { adminService } from '@/services/admin'
import { toast } from '@/hooks/use-toast'
import { DocumentUploadProgress } from '@/services/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Upload,
  FileText,
  File,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface DocumentUploadProps {
  knowledgeBaseId: number
  open: boolean
  onOpenChange: (open: boolean) => void
  onUploadComplete?: () => void
}

interface UploadFile extends File {
  id: string
  progress: DocumentUploadProgress
}

const SUPPORTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'text/plain': ['.txt'],
  'text/markdown': ['.md'],
  'text/csv': ['.csv'],
}

const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB

export function DocumentUpload({
  knowledgeBaseId,
  open,
  onOpenChange,
  onUploadComplete,
}: DocumentUploadProps) {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [isDragActive, setIsDragActive] = useState(false)
  const abortControllersRef = useRef<Map<string, AbortController>>(new Map())
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 验证文件类型
  const isValidFileType = (file: File): boolean => {
    const validTypes = Object.keys(SUPPORTED_FILE_TYPES)
    return validTypes.includes(file.type) || 
           file.name.toLowerCase().endsWith('.txt') ||
           file.name.toLowerCase().endsWith('.md') ||
           file.name.toLowerCase().endsWith('.csv')
  }

  // 处理文件选择
  const handleFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files)
    const validFiles: File[] = []
    
    fileArray.forEach((file) => {
      if (file.size > MAX_FILE_SIZE) {
        toast({
          title: '文件过大',
          description: `${file.name} 超过了 50MB 的大小限制`,
          variant: 'destructive',
        })
      } else if (!isValidFileType(file)) {
        toast({
          title: '文件类型不支持',
          description: `${file.name} 的文件类型不受支持`,
          variant: 'destructive',
        })
      } else {
        validFiles.push(file)
      }
    })

    // 处理有效文件
    const newFiles: UploadFile[] = validFiles.map((file) => ({
      ...file,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      progress: {
        filename: file.name,
        progress: 0,
        status: 'uploading',
      },
    }))

    setUploadFiles((prev) => [...prev, ...newFiles])
  }, [])

  // 拖拽事件处理
  const handleDragEnter = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
  }, [])

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFiles(files)
    }
  }, [handleFiles])

  // 点击选择文件
  const handleClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  // 文件输入变化
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFiles(files)
    }
    // 清空input值，允许重复选择同一文件
    e.target.value = ''
  }, [handleFiles])

  // 上传单个文件
  const uploadFile = useCallback(async (file: UploadFile) => {
    const abortController = new AbortController()
    abortControllersRef.current.set(file.id, abortController)

    try {
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === file.id
            ? {
                ...f,
                progress: { ...f.progress, status: 'uploading', progress: 0 },
              }
            : f
        )
      )

      await adminService.uploadDocument(
        file,
        knowledgeBaseId,
        (progress) => {
          setUploadFiles((prev) =>
            prev.map((f) =>
              f.id === file.id
                ? {
                    ...f,
                    progress: { ...f.progress, progress },
                  }
                : f
            )
          )
        }
      )

      // 上传成功
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === file.id
            ? {
                ...f,
                progress: {
                  ...f.progress,
                  status: 'completed',
                  progress: 100,
                },
              }
            : f
        )
      )

      toast({
        title: '上传成功',
        description: `${file.name} 已成功上传并开始处理`,
      })
    } catch (error) {
      if (abortController.signal.aborted) {
        setUploadFiles((prev) => prev.filter((f) => f.id !== file.id))
        return
      }

      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === file.id
            ? {
                ...f,
                progress: {
                  ...f.progress,
                  status: 'error',
                  error: error instanceof Error ? error.message : '上传失败',
                },
              }
            : f
        )
      )

      toast({
        title: '上传失败',
        description: `${file.name} 上传失败: ${error instanceof Error ? error.message : '未知错误'}`,
        variant: 'destructive',
      })
    } finally {
      abortControllersRef.current.delete(file.id)
    }
  }, [knowledgeBaseId])

  // 开始上传所有文件
  const startUpload = useCallback(async () => {
    if (uploadFiles.length === 0) return

    setIsUploading(true)
    
    try {
      // 并发上传所有文件
      await Promise.allSettled(
        uploadFiles
          .filter((file) => file.progress.status === 'uploading' && file.progress.progress === 0)
          .map(uploadFile)
      )

      // 检查是否所有文件都上传成功
      const allCompleted = uploadFiles.every(
        (file) => file.progress.status === 'completed' || file.progress.status === 'error'
      )

      if (allCompleted) {
        onUploadComplete?.()
      }
    } finally {
      setIsUploading(false)
    }
  }, [uploadFiles, uploadFile, onUploadComplete])

  // 移除文件
  const removeFile = useCallback((fileId: string) => {
    const abortController = abortControllersRef.current.get(fileId)
    if (abortController) {
      abortController.abort()
    }
    setUploadFiles((prev) => prev.filter((f) => f.id !== fileId))
  }, [])

  // 重试上传
  const retryUpload = useCallback((file: UploadFile) => {
    uploadFile(file)
  }, [uploadFile])

  // 清空所有文件
  const clearAll = useCallback(() => {
    // 取消所有正在进行的上传
    abortControllersRef.current.forEach((controller) => {
      controller.abort()
    })
    abortControllersRef.current.clear()
    setUploadFiles([])
  }, [])

  // 获取文件图标
  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf') {
      return <FileText className="h-8 w-8 text-red-500" />
    }
    return <File className="h-8 w-8 text-blue-500" />
  }

  // 获取状态图标
  const getStatusIcon = (status: DocumentUploadProgress['status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return null
    }
  }

  // 获取状态文本
  const getStatusText = (progress: DocumentUploadProgress) => {
    switch (progress.status) {
      case 'uploading':
        return `上传中 ${progress.progress}%`
      case 'processing':
        return '处理中...'
      case 'completed':
        return '完成'
      case 'error':
        return progress.error || '失败'
      default:
        return '等待中'
    }
  }

  const completedCount = uploadFiles.filter((f) => f.progress.status === 'completed').length
  const errorCount = uploadFiles.filter((f) => f.progress.status === 'error').length
  const hasFiles = uploadFiles.length > 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>上传文档</DialogTitle>
          <DialogDescription>
            支持 PDF、Word、文本等格式，单个文件最大 50MB
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto space-y-4">
          {/* 拖拽上传区域 */}
          <Card>
            <CardContent className="p-6">
              <div
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={handleClick}
                className={cn(
                  'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                  isDragActive
                    ? 'border-primary bg-primary/5'
                    : 'border-muted-foreground/25 hover:border-primary/50'
                )}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.txt,.md,.csv"
                  onChange={handleFileInputChange}
                  className="hidden"
                />
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                {isDragActive ? (
                  <p className="text-lg">释放文件以开始上传...</p>
                ) : (
                  <div>
                    <p className="text-lg mb-2">拖拽文件到此处，或点击选择文件</p>
                    <p className="text-sm text-muted-foreground">
                      支持 PDF、Word、TXT、Markdown 等格式
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 文件列表 */}
          {hasFiles && (
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium">
                    文件列表 ({uploadFiles.length})
                  </h3>
                  <div className="flex items-center gap-2">
                    {completedCount > 0 && (
                      <Badge variant="secondary" className="text-green-600">
                        {completedCount} 成功
                      </Badge>
                    )}
                    {errorCount > 0 && (
                      <Badge variant="destructive">
                        {errorCount} 失败
                      </Badge>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearAll}
                      disabled={isUploading}
                    >
                      清空
                    </Button>
                  </div>
                </div>

                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {uploadFiles.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center gap-3 p-3 border rounded-lg"
                    >
                      {getFileIcon(file)}
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-medium truncate">{file.name}</p>
                          {getStatusIcon(file.progress.status)}
                        </div>
                        
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                          <span>•</span>
                          <span>{getStatusText(file.progress)}</span>
                        </div>
                        
                        {file.progress.status === 'uploading' && file.progress.progress > 0 && (
                          <Progress
                            value={file.progress.progress}
                            className="mt-2 h-1"
                          />
                        )}
                      </div>

                      <div className="flex items-center gap-1">
                        {file.progress.status === 'error' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => retryUpload(file)}
                            disabled={isUploading}
                          >
                            重试
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(file.id)}
                          disabled={isUploading && file.progress.status === 'uploading'}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex justify-between pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <div className="flex gap-2">
            {hasFiles && (
              <Button
                onClick={startUpload}
                disabled={isUploading || uploadFiles.every(f => f.progress.status !== 'uploading' || f.progress.progress > 0)}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    上传中...
                  </>
                ) : (
                  '开始上传'
                )}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}