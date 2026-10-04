import type { Metadata } from 'next'

import { MetadataPage } from '@/components/dashboard/metadata-page'

export const metadata: Metadata = {
  title: 'Datasets | DataAir',
  description: 'Datasets in the DataAir platform.',
}

export default function Page() {
  return <MetadataPage />
}
