import type { Metadata } from 'next'

import { SystemStatusPage } from '@/components/system/system-status-page'

export const metadata: Metadata = {
  title: 'System Status | DataAir',
  description: 'Live health of every service in the DataAir platform.',
}

export default function Page() {
  return <SystemStatusPage />
}