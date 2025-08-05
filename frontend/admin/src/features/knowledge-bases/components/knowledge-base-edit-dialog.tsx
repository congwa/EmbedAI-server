/* eslint-disable react-hooks/exhaustive-deps */
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
import { KnowledgeBaseDetail } from '@/services/types'

const formSchema = z.object({
  name: z.string().min(1, '请输入知识库名称'),
  domain: z.string().min(1, '请输入知识库领域'),
  example_queries: z.array(z.string()).optional(),
  entity_types: z.array(z.string()).optional(),
  llm_config: z
    .object({
      llm: z.object({
        model: z.string(),
        base_url: z.string(),
        api_key: z.string(),
      }),
      embeddings: z.object({
        model: z.string(),
        base_url: z.string(),
        api_key: z.string(),
        embedding_dim: z.number(),
      }),
    })
    .optional(),
})

type FormValues = z.infer<typeof formSchema>

interface KnowledgeBaseEditDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  knowledgeBase?: KnowledgeBaseDetail
  onSubmit: (values: FormValues) => Promise<void>
}

export function KnowledgeBaseEditDialog({
  open,
  onOpenChange,
  knowledgeBase,
  onSubmit,
}: KnowledgeBaseEditDialogProps) {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: knowledgeBase?.name || '',
      domain: knowledgeBase?.domain || '',
      example_queries: knowledgeBase?.example_queries || [],
      entity_types: knowledgeBase?.entity_types || [],
      llm_config: knowledgeBase?.llm_config,
    }
  })

  // 处理多值输入的辅助函数
  const handleMultiValueInput = (value: string): string[] => {
    if (!value) return []
    // 支持逗号、顿号、分号、空格等分隔符
    return value
      .split(/[,，、；;\s]+/)
      .map(item => item.trim())
      .filter(Boolean)
  }

  // 将数组转换为显示文本
  const arrayToDisplayText = (arr: string[] | undefined): string => {
    return arr?.join('，') || ''
  }

  useEffect(() => {
    if (open) {
      form.reset({
        name: knowledgeBase?.name || '',
        domain: knowledgeBase?.domain || '',
        example_queries: knowledgeBase?.example_queries || [],
        entity_types: knowledgeBase?.entity_types || [],
        llm_config: knowledgeBase?.llm_config,
      })
    }
  }, [open, knowledgeBase])

  const handleSubmit = async (values: FormValues) => {
    await onSubmit(values)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {knowledgeBase ? '编辑知识库' : '创建知识库'}
          </DialogTitle>
          <DialogDescription>
            {knowledgeBase ? '修改知识库的基本信息' : '创建一个新的知识库'}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>名称</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入知识库名称" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="domain"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>领域</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入知识库领域" {...field} />
                  </FormControl>
                  <FormDescription>
                    知识库所属的领域，如"金融"、"医疗"等，默认为"通用知识领域"
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="example_queries"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>示例查询</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="请输入示例查询，使用逗号、顿号、分号等分隔（选填）"
                      className="resize-none"
                      value={arrayToDisplayText(field.value)}
                      onChange={(e) => {
                        field.onChange(handleMultiValueInput(e.target.value))
                      }}
                    />
                  </FormControl>
                  <FormDescription>
                    用户可能会问的问题示例，使用逗号、顿号、分号等分隔多个问题
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="entity_types"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>实体类型</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="请输入实体类型，使用逗号、顿号、分号等分隔（选填）"
                      className="resize-none"
                      value={arrayToDisplayText(field.value)}
                      onChange={(e) => {
                        field.onChange(handleMultiValueInput(e.target.value))
                      }}
                    />
                  </FormControl>
                  <FormDescription>
                    知识库中包含的实体类型，使用逗号、顿号、分号等分隔多个类型
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex justify-end">
              <Button type="submit">
                {knowledgeBase ? '保存' : '创建'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
} 