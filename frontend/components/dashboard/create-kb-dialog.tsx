'use client'

import { useState } from 'react'
import { Plus } from 'lucide-react'

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
import { Textarea } from '@/components/ui/textarea'
import { extractErrorDetail, post } from '@/lib/api/data'
import { toast } from 'sonner'

interface CreatedKnowledgeBase {
  id?: string
  name?: string
  slug?: string
}

export function CreateKnowledgeBaseDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function create() {
    if (!name.trim()) {
      setError('Give the knowledge base a name')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const result = await post<CreatedKnowledgeBase>('/knowledge-bases/', {
        name: name.trim(),
        ...(description.trim() ? { description: description.trim() } : {}),
      })
      toast.success(`Created ${result.name ?? 'knowledge base'}`)
      setName('')
      setDescription('')
      setOpen(false)
      onCreated()
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New knowledge base
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>New knowledge base</DialogTitle>
          <DialogDescription>
            Group documents and schemas for retrieval in one collection.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="kb-name">Name</Label>
            <Input
              id="kb-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Product documentation"
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="kb-desc">Description (optional)</Label>
            <Textarea
              id="kb-desc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What belongs in this collection?"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={create} disabled={loading}>
            {loading ? 'Creating…' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}