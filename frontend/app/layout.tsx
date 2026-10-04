import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from '@/providers/query-provider'
import { ThemeProvider } from '@/providers/theme-provider'
import { AuthProvider } from '@/providers/auth-provider'
import { Toaster } from 'sonner'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DataAir | Enterprise Data Operating Platform',
  description: 'DataAir is an Enterprise Data Operating & Intelligence Platform that manages the complete data lifecycle from ingestion to AI agents.',
  keywords: 'data platform, data engineering, data quality, metadata, lineage, AI, RAG',
  authors: [{ name: 'DataAir Team' }],
  creator: 'DataAir',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://dataair.io',
    title: 'DataAir',
    description: 'Enterprise Data Operating & Intelligence Platform',
    siteName: 'DataAir',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'DataAir',
    description: 'Enterprise Data Operating & Intelligence Platform',
  },
  icons: {
    icon: '/favicon.svg',
    shortcut: '/favicon.svg',
    apple: '/apple-touch-icon.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider>
          <QueryProvider>
            <AuthProvider>
              {children}
              <Toaster />
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}