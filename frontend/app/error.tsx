'use client'

import { useEffect } from 'react'
import { AlertTriangle, Home, RotateCcw } from 'lucide-react'

import { Button } from '@/components/ui/button'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Page render error:', error)
  }, [error])

  return (
    <div className="flex min-h-[50vh] items-center justify-center p-6">
      <div className="w-full max-w-md space-y-4 rounded-lg border p-6 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h1 className="text-lg font-semibold">This page failed to render</h1>
        <p className="text-sm text-muted-foreground">
          The rest of the dashboard is still usable — retry, or head back to the overview.
        </p>
        {error.digest && (
          <p className="font-mono text-xs text-muted-foreground">Digest: {error.digest}</p>
        )}
        <div className="flex justify-center gap-2">
          <Button variant="outline" onClick={reset}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Try again
          </Button>
          <Button asChild>
            <a href="/dashboard">
              <Home className="mr-2 h-4 w-4" />
              Dashboard
            </a>
          </Button>
        </div>
      </div>
    </div>
  )
}