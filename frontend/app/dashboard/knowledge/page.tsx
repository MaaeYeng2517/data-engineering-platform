import type { Metadata } from 'next'

import { KnowledgeBasesPage } from '@/components/dashboard/knowledge-page'

export const metadata: Metadata = {
  title: 'Knowledge Bases | DataAir',
  description: 'Knowledge Bases in the DataAir platform.',
}

export default function Page() {
  return <KnowledgeBasesPage />
}
