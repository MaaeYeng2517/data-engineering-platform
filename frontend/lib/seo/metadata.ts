import type { Metadata } from 'next'

export function buildMetadata({
  title,
  description,
  url,
}: {
  title: string
  description: string
  url: string
}): Metadata {
  const base = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'
  return {
    title,
    description,
    metadataBase: new URL(base),
    alternates: { canonical: url },
    openGraph: { title, description, url },
    twitter: { card: 'summary_large_image', title, description },
  }
}
