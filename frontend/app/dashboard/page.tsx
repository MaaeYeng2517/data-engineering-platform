import type { Metadata } from 'next'

import { DashboardOverview } from '@/components/dashboard/overview'

export const metadata: Metadata = {
  title: 'Dashboard | DataAir',
  description: 'Overview of your DataAir workspace.',
}

export default function DashboardPage() {
  return <DashboardOverview />
}