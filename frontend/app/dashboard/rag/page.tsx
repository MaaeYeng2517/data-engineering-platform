import type { Metadata } from 'next'

import { RagPage } from '@/components/dashboard/rag-page'

export const metadata: Metadata = {
  title: 'RAG | DataAir',
  description: 'RAG in the DataAir platform.',
}

export default function Page() {
  return <RagPage />
}
