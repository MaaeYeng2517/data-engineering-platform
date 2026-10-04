import type { Metadata } from 'next'

import { SourcesPage } from '@/components/dashboard/sources-page'

export const metadata: Metadata = {
  title: 'Data Sources | DataAir',
  description: 'Data Sources in the DataAir platform.',
}

export default function Page() {
  return <SourcesPage />
}
