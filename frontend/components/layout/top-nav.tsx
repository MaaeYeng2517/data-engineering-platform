'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useMemo, useState } from 'react'
import { Bell, LogOut, Menu, Moon, Plus, Search, Sun, User } from 'lucide-react'
import { useTheme } from 'next-themes'

import { Button } from '@/components/ui/button'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Sidebar, SidebarContent, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarTrigger } from '@/components/ui/sidebar'
import { useAuth } from '@/providers/auth-provider'
import { getList } from '@/lib/api/data'
import { useApi } from '@/components/shared/async'
import { adminOnlyHrefs, navGroups, navItems } from './nav-items'

function titleFromPath(pathname: string): string {
  if (pathname === '/dashboard') return 'Overview'
  const segment = pathname.split('/').filter(Boolean).pop() || 'Overview'
  return segment
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function TopNav() {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const { resolvedTheme, setTheme } = useTheme()
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [alertsOpen, setAlertsOpen] = useState(false)

  // The audit log is admin-scoped; non-admins would get a 403, so don't count it.
  const isAdmin = user?.role === 'admin' || user?.is_superuser === true

  // Surface a badge only for real signals: failed API calls and account issues.
  const usage = useApi(
    () =>
      getList<{ id?: string; status_code?: number }>('/api-keys/usage').catch(() => ({
        items: [],
        total: 0,
      })),
    []
  )
  const failedCalls = usage.data?.items.filter((c) => (c.status_code ?? 0) >= 400).length ?? 0
  const attentionCount = failedCalls + (user?.is_active === false ? 1 : 0)

  const searchMatches = useMemo(() => {
    const q = searchTerm.trim().toLowerCase()
    const pool = isAdmin
      ? navItems
      : navItems.filter((item) => !adminOnlyHrefs.has(item.href))
    if (!q) return pool.slice(0, 8)
    return pool
      .filter((item) => item.title.toLowerCase().includes(q))
      .slice(0, 8)
  }, [searchTerm, isAdmin])

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-2 border-b bg-background px-4">
      <SidebarTrigger className="-ml-1" />

      <Separator orientation="vertical" className="mr-1 h-4" />

      <Breadcrumb className="hidden sm:block">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/dashboard">Dashboard</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <BreadcrumbPage>{titleFromPath(pathname)}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="ml-auto flex items-center gap-1">
        <Dialog open={searchOpen} onOpenChange={setSearchOpen}>
          <DialogTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Search">
              <Search className="h-5 w-5" />
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle className="sr-only">Search the platform</DialogTitle>
            </DialogHeader>
            <div className="space-y-2">
              <Input
                placeholder="Jump to a page…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                autoFocus
              />
              <ul className="max-h-80 space-y-1 overflow-y-auto">
                {searchMatches.map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={() => setSearchOpen(false)}
                      className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                    >
                      <item.icon className="h-4 w-4 text-muted-foreground" />
                      {item.title}
                    </Link>
                  </li>
                ))}
                {searchMatches.length === 0 && (
                  <li className="px-3 py-6 text-center text-sm text-muted-foreground">
                    No pages match &ldquo;{searchTerm}&rdquo;.
                  </li>
                )}
              </ul>
            </div>
          </DialogContent>
        </Dialog>

        <Button
          variant="ghost"
          size="icon"
          aria-label="Toggle theme"
          onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
        >
          {resolvedTheme === 'dark' ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </Button>

        <Dialog open={alertsOpen} onOpenChange={setAlertsOpen}>
          <DialogTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Notifications" className="relative">
              <Bell className="h-5 w-5" />
              {attentionCount > 0 && (
                <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-primary" />
              )}
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Notifications</DialogTitle>
              <DialogDescription>
                {attentionCount > 0
                  ? `${attentionCount} item${attentionCount === 1 ? '' : 's'} need your attention.`
                  : 'Nothing needs your attention right now.'}
              </DialogDescription>
            </DialogHeader>
            <ul className="space-y-2">
              <li className="rounded-md border p-3 text-sm">
                <p className="font-medium">Approval queue</p>
                <p className="text-muted-foreground">
                  Documents awaiting sign-off appear here.
                </p>
              </li>
              <li className="rounded-md border p-3 text-sm">
                <p className="font-medium">Pipeline health</p>
                <p className="text-muted-foreground">
                  Failed workflow runs are tracked on the Activity page.
                </p>
              </li>
            </ul>
            <DialogFooter>
              <Button asChild variant="outline" size="sm">
                <Link href="/dashboard/activity" onClick={() => setAlertsOpen(false)}>
                  View activity
                </Link>
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        <Button size="sm" className="ml-1 hidden sm:inline-flex" asChild>
          <Link href="/dashboard/sources">
            <Plus className="mr-1.5 h-4 w-4" />
            New source
          </Link>
        </Button>

        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open navigation">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 p-0">
            <SheetTitle className="sr-only">Navigation</SheetTitle>
            <Sidebar className="border-none">
              <SidebarContent className="overflow-y-auto">
                {navGroups.map((group) => (
                  <div key={group.label} className="mb-3">
                    <p className="px-2 py-1 text-xs font-medium text-muted-foreground">
                      {group.label}
                    </p>
                    <SidebarMenu>
                      {group.items.map((item) => (
                        <SidebarMenuItem key={item.href}>
                          <SidebarMenuButton asChild>
                            <Link href={item.href}>
                              <item.icon className="h-4 w-4" />
                              <span>{item.title}</span>
                            </Link>
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      ))}
                    </SidebarMenu>
                  </div>
                ))}
              </SidebarContent>
            </Sidebar>
          </SheetContent>
        </Sheet>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="ml-1 gap-2 px-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                {(user?.full_name || user?.email || '?').charAt(0).toUpperCase()}
              </span>
              <span className="hidden text-sm font-medium md:inline">
                {user?.full_name || user?.email}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <span className="block text-sm font-medium">{user?.full_name || 'User'}</span>
              <span className="block text-xs font-normal text-muted-foreground">
                {user?.email}
              </span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/dashboard/settings">
                <User className="mr-2 h-4 w-4" />
                Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout}>
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}