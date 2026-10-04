import type { Metadata } from 'next'

import { WorkflowsPage } from '@/components/dashboard/workflows-page'

export const metadata: Metadata = {
  title: 'Workflows | DataAir',
  description: 'Workflows in the DataAir platform.',
}

export default function Page() {
  return <WorkflowsPage />
}
