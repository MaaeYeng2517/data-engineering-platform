import type { Metadata } from 'next'

import { ToolsPage } from '@/components/dashboard/tools-page'

export const metadata: Metadata = {
  title: 'Tools | DataAir',
  description: 'Operator tools that run alongside the DataAir platform.',
}

export default function Page() {
  return <ToolsPage />
}