import Script from 'next/script'

export function JsonLd({ data }: { data: Record<string, any> }) {
  return (
    <Script
      id={`jsonld-${Date.now()}`}
      type='application/ld+json'
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
      strategy='afterInteractive'
    />
  )
}

export function websiteJsonLd() {
  const base = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'DataAir Blog',
    url: base,
  }
}
