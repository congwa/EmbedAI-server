import { createLazyFileRoute } from '@tanstack/react-router'
import { AnalyticsReports } from '@/features/analytics/reports'

export const Route = createLazyFileRoute('/_authenticated/analytics/reports')({
  component: AnalyticsReports,
})
