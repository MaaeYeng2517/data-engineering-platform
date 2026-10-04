'use client'

import { ReactNode } from 'react'
import { redirect } from 'next/navigation'
import { Loader2 } from 'lucide-react'

import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { useAuth } from '@/providers/auth-provider'
import { AppSidebar } from './sidebar'
import { TopNav } from './top-nav'

export function DashboardLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!isAuthenticated) {
    redirect('/login')
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-w-0">
        <TopNav />
        <main className="flex-1 p-6">
          <div className="mx-auto w-full max-w-7xl">{children}</div>
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}