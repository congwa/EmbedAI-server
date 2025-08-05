import { createLazyFileRoute } from '@tanstack/react-router'
import { KnowledgeBasesPage } from '@/features/knowledge-bases'

export const Route = createLazyFileRoute('/_authenticated/knowledge-bases/')({
  component: KnowledgeBasesPage,
}) 