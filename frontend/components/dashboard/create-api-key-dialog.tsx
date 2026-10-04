'use client'

import { useState } from 'react'
import { Copy, Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'
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
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { extractErrorDetail, post } from '@/lib/api/data'
import { toast } from 'sonner'

interface CreatedKey {
  api_key?: { id?: string; name?: string; key_prefix?: string }
  plain_key?: string
}

const SCOPES = ['read', 'write', 'admin'] as const

export function CreateApiKeyDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [scope, setScope] = useState<string>('read')
  const [plainKey, setPlainKey] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function create() {
    if (!name.trim()) {
      setError('Give the key a name')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const result = await post<CreatedKey>('/api-keys', {
        name: name.trim(),
        scopes: [scope],
      })
      setPlainKey(result.plain_key ?? null)
      toast.success('API key created')
      onCreated()
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setName('')
    setScope('read')
    setPlainKey(null)
    setError(null)
  }

  async function copyKey() {
    if (!plainKey) return
    try {
      await navigator.clipboard.writeText(plainKey)
      toast.success('Copied to clipboard')
    } catch {
      toast.error('Could not copy — select the key manually')
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) reset()
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Create key
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create API key</DialogTitle>
          <DialogDescription>
            The key is shown once. Store it somewhere safe.
          </DialogDescription>
        </DialogHeader>

        {plainKey ? (
          <div className="space-y-3">
            <div className="rounded-lg border bg-muted p-3">
              <p className="mb-1 text-xs text-muted-foreground">Your new key</p>
              <code className="block break-all font-mono text-xs">{plainKey}</code>
            </div>
            <Button variant="outline" className="w-full" onClick={copyKey}>
              <Copy className="mr-2 h-4 w-4" />
              Copy key
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="key-name">Name</Label>
              <Input
                id="key-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="CI pipeline"
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="key-scope">Scope</Label>
              <Select value={scope} onValueChange={setScope}>
                <SelectTrigger id="key-scope">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SCOPES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        )}

        <DialogFooter>
          {plainKey ? (
            <Button onClick={() => setOpen(false)}>Done</Button>
          ) : (
            <>
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button onClick={create} disabled={loading}>
                {loading ? 'Creating…' : 'Create key'}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}