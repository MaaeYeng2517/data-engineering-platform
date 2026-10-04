import type { Metadata } from 'next'

import { DocumentsPage } from '@/components/dashboard/documents-page'

export const metadata: Metadata = {
  title: 'Documents | DataAir',
  description: 'Documents in the DataAir platform.',
}

export default function Page() {
  return <DocumentsPage />
}
