import type { Metadata } from 'next'

import { DocumentsPage } from '@/components/marketing/documents-page'
import { SiteFooter, SiteHeader } from '@/components/marketing/site-chrome'

export const metadata: Metadata = {
  title: 'Documents | DataAir',
  description:
    'How the DataAir platform works: the document pipeline, knowledge bases, search and RAG, workflows, governance, API keys and the operator tools behind it.',
  alternates: { canonical: '/documents' },
  openGraph: {
    type: 'article',
    url: '/documents',
    title: 'Documents | DataAir',
    description:
      'The document pipeline and platform concepts, from ingestion to RAG.',
    siteName: 'DataAir',
  },
}

export default function Page() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <DocumentsPage />
      </main>
      <SiteFooter />
    </div>
  )
}