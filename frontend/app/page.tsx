import { BlogHomePage } from '@/components/marketing/blog-home'
import { SiteFooter, SiteHeader } from '@/components/marketing/site-chrome'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <BlogHomePage />
      </main>
      <SiteFooter />
    </div>
  )
}
