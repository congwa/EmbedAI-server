import { createLazyFileRoute } from '@tanstack/react-router'
import { KnowledgeBaseDocumentsPage } from '@/features/knowledge-bases/documents'

export const Route = createLazyFileRoute('/_authenticated/knowledge-bases/$id/documents/')({
  component: KnowledgeBaseDocumentsPage,
}) 