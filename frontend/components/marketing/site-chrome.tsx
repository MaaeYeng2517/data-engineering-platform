'use client'

import Link from 'next/link'
import { useState } from 'react'
import { ArrowRight, Database, Menu, X } from 'lucide-react'

import { Button } from '@/components/ui/button'

const navLinks = [
  { title: 'Documents', href: '/documents' },
  { title: 'Ask AI', href: '/#chat' },
  { title: 'Platform', href: '/#platform' },
  { title: 'Capabilities', href: '/#capabilities' },
  { title: 'Workspace', href: '/#pages' },
  { title: 'Processing', href: '/#processing' },
  { title: 'Architecture', href: '/#architecture' },
  { title: 'Pricing', href: '/#pricing' },
  { title: 'FAQ', href: '/#faq' },
]

export function SiteHeader() {
  const [open, setOpen] = useState(false)

  const links = navLinks.map((link) => (
    <Link
      key={link.href}
      href={link.href}
      onClick={() => setOpen(false)}
      className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
    >
      {link.title}
    </Link>
  ))

  const actions = (
    <>
      <Button variant="ghost" size="sm" asChild>
        <Link href="/login">Sign in</Link>
      </Button>
      <Button size="sm" asChild>
        <Link href="/register">
          Get started
          <ArrowRight className="ml-2 h-4 w-4" />
        </Link>
      </Button>
    </>
  )

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Database className="h-4 w-4" />
          </div>
          <span className="text-lg">DataAir</span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex">{links}</nav>

        <div className="hidden items-center gap-2 md:flex">{actions}</div>

        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle navigation"
          aria-expanded={open}
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      {open && (
        <div className="border-t md:hidden">
          <nav className="container flex flex-col gap-3 py-4">{links}</nav>
          <div className="container flex flex-col gap-2 pb-4">{actions}</div>
        </div>
      )}
    </header>
  )
}

export function SiteFooter() {
  return (
    <footer className="border-t bg-muted/30">
      <div className="container flex flex-col gap-4 py-10 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Database className="h-3.5 w-3.5" />
          </div>
          <span className="font-medium">DataAir</span>
        </div>
        <p className="text-sm text-muted-foreground">
          Enterprise data operating and intelligence platform.
        </p>
        <div className="flex gap-4 text-sm text-muted-foreground">
          <Link href="#pricing" className="hover:text-foreground">
            Pricing
          </Link>
          <Link href="#pages" className="hover:text-foreground">
            Workspace
          </Link>
          <Link href="/register" className="hover:text-foreground">
            Create account
          </Link>
          <Link href="/login" className="hover:text-foreground">
            Sign in
          </Link>
        </div>
      </div>
      <div className="border-t py-6">
        <p className="container text-xs text-muted-foreground">
          &copy; {new Date().getFullYear()} DataAir. All rights reserved.
        </p>
      </div>
    </footer>
  )
}