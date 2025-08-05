import { createLazyFileRoute } from '@tanstack/react-router'
import { AnalyticsDashboard } from '@/features/analytics/dashboard'

export const Route = createLazyFileRoute('/_authenticated/analytics/')({
  component: AnalyticsDashboard,
})
