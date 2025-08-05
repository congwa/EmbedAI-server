import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Document, DocumentType, CreateDocumentRequest, UpdateDocumentRequest } from '@/services/types'

const formSchema = z.object({
  title: z.string().min(1, '请输入文档标题').max(255, '文档标题不能超过255个字符'),
  content: z.string().min(1, '请输入文档内容'),
  doc_type: z.nativeEnum(DocumentType, {
    required_error: '请选择文档类型',
  }),
  metadata: z.record(z.unknown()).optional(),
})

type FormValues = z.infer<typeof formSchema>

interface DocumentEditDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  document?: Document
  onSubmit: (values: CreateDocumentRequest | UpdateDocumentRequest) => Promise<void>
}

export function DocumentEditDialog({
  open,
  onOpenChange,
  document,
  onSubmit,
}: DocumentEditDialogProps) {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: '',
      content: '',
      doc_type: DocumentType.TEXT,
    },
  })

  useEffect(() => {
    if (open) {
      if (document) {
        form.reset({
          title: document.title,
          content: document.content,
          doc_type: document.doc_type,
          metadata: document.metadata,
        })
      } else {
        form.reset({
          title: '',
          content: '',
          doc_type: DocumentType.TEXT,
          metadata: undefined,
        })
      }
    }
  }, [open, document, form])

  const handleSubmit = async (values: FormValues) => {
    await onSubmit(values)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {document ? '编辑文档' : '创建文档'}
          </DialogTitle>
          <DialogDescription>
            {document ? '修改文档的基本信息' : '创建一个新的文档'}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>标题</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入文档标题" {...field} />
                  </FormControl>
                  <FormDescription>
                    文档标题不能超过255个字符
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="doc_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>类型</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="请选择文档类型" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value={DocumentType.TEXT}>文本</SelectItem>
                      <SelectItem value={DocumentType.WEBPAGE}>网页</SelectItem>
                      <SelectItem value={DocumentType.PDF}>PDF</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="content"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>内容</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="请输入文档内容"
                      className="min-h-[200px]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex justify-end">
              <Button type="submit">
                {document ? '保存' : '创建'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
} 