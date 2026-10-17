import {
  ArchitectureSection,
  CtaSection,
  FaqSection,
  Hero,
  PagesSection,
  PlatformSection,
  PricingSection,
  ProcessingSection,
  StatsSection,
} from '@/components/marketing/sections'
import { SiteFooter, SiteHeader } from '@/components/marketing/site-chrome'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <Hero />
        <StatsSection />
        <PlatformSection />
        <ProcessingSection />
        <ArchitectureSection />
        <PagesSection />
        <PricingSection />
        <FaqSection />
        <CtaSection />
      </main>
      <SiteFooter />
    </div>
  )
}
