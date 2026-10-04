import type { Metadata } from 'next'

import { ChatSection } from '@/components/marketing/chat-widget'
import { SiteFooter, SiteHeader } from '@/components/marketing/site-chrome'
import {
  ArchitectureSection,
  CtaSection,
  FaqSection,
  Hero,
  PagesSection,
  PlatformSection,
  PricingSection,
  ProcessingSection,
} from '@/components/marketing/sections'

export const metadata: Metadata = {
  title: 'DataAir | Enterprise Data Operating Platform',
  description:
    'DataAir is an enterprise data operating and intelligence platform covering the complete lifecycle from ingestion to AI agents: sources, knowledge bases, search, RAG, lineage, governance and evaluation.',
  keywords: [
    'data platform',
    'data engineering',
    'data governance',
    'knowledge base',
    'RAG',
    'data lineage',
    'AI agents',
  ],
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: '/',
    title: 'DataAir | Enterprise Data Operating Platform',
    description: 'The complete data lifecycle, from ingestion to AI agents.',
    siteName: 'DataAir',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'DataAir | Enterprise Data Operating Platform',
    description: 'The complete data lifecycle, from ingestion to AI agents.',
  },
}

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <Hero />
        <ChatSection />
        <PlatformSection />
        <PagesSection />
        <ProcessingSection />
        <ArchitectureSection />
        <PricingSection />
        <FaqSection />
        <CtaSection />
      </main>
      <SiteFooter />
    </div>
  )
}
