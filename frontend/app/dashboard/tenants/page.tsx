import type { Metadata } from 'next'

import { WorkspacePage } from '@/components/dashboard/workspace-pages'

export const metadata: Metadata = {
  title: 'Workspace | DataAir',
  description: 'Workspace in the DataAir platform.',
}

export default function Page() {
  return <WorkspacePage />
}
