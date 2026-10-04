import type { Metadata } from 'next'

import { AnalyticsPage } from '@/components/dashboard/analytics-page'

export const metadata: Metadata = {
  title: 'Analytics | DataAir',
  description: 'Usage, quality and pipeline metrics for your workspace.',
}

export default function Page() {
  return <AnalyticsPage />
}