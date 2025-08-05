import { createLazyFileRoute } from '@tanstack/react-router'
import MonitoringDashboard from '@/features/monitoring'

export const Route = createLazyFileRoute('/_authenticated/monitoring/')({
  component: MonitoringDashboard,
})
