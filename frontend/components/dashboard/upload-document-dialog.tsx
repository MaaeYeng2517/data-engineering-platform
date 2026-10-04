'use client'

import { useRef, useState } from 'react'
import { Upload } from 'lucide-react'

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
import { extractErrorDetail, getList, post } from '@/lib/api/data'
import { api } from '@/lib/api/client'
import { useApi } from '@/components/shared/async'
import { toast } from 'sonner'

interface KnowledgeBase {
  id?: string
  name?: string
}

const SOURCE_TYPES = ['file', 'url', 'text']

export function UploadDocumentDialog({ onUploaded }: { onUploaded: () => void }) {
  const [open, setOpen] = useState(false)
  const [kbId, setKbId] = useState('')
  const [title, setTitle] = useState('')
  const [sourceType, setSourceType] = useState('file')
  const [sourceUrl, setSourceUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)

  const knowledgeBases = useApi(() => getList<KnowledgeBase>('/knowledge-bases/'), [])

  async function submit() {
    if (!kbId) {
      setError('Select a knowledge base')
      return
    }
    if (sourceType === 'file' && !file) {
      setError('Choose a file to upload')
      return
    }
    if (sourceType === 'url' && !sourceUrl.trim()) {
      setError('Enter a source URL')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const resolvedTitle = title.trim() || file?.name || sourceUrl.trim()

      if (sourceType === 'file' && file) {
        const form = new FormData()
        form.append('file', file)
        form.append('kb_id', kbId)
        form.append('title', resolvedTitle)
        // Route through the shared client so the CSRF token rides along; a raw
        // fetch would be rejected by the backend's unsafe-method guard.
        await api.post<{ id?: string }>('/documents/upload', form)
      } else {
        await post<{ id?: string }>('/documents/', {
          kb_id: kbId,
          title: resolvedTitle,
          source_type: sourceType,
          ...(sourceUrl.trim() ? { source_url: sourceUrl.trim() } : {}),
        })
      }

      toast.success('Document submitted')
      setTitle('')
      setSourceUrl('')
      setFile(null)
      if (fileInput.current) fileInput.current.value = ''
      setOpen(false)
      onUploaded()
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
          <Upload className="mr-2 h-4 w-4" />
          Upload document
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Upload document</DialogTitle>
          <DialogDescription>
            Add a document to a knowledge base for retrieval.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="up-kb">Knowledge base</Label>
            <Select value={kbId} onValueChange={setKbId}>
              <SelectTrigger id="up-kb">
                <SelectValue placeholder="Select a knowledge base" />
              </SelectTrigger>
              <SelectContent>
                {knowledgeBases.data?.items.map((kb, index) => (
                  <SelectItem key={kb.id ?? index} value={kb.id ?? ''}>
                    {kb.name ?? `Knowledge base ${index + 1}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="up-type">Source type</Label>
            <Select value={sourceType} onValueChange={setSourceType}>
              <SelectTrigger id="up-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SOURCE_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {sourceType === 'file' ? (
            <div className="space-y-2">
              <Label htmlFor="up-file">File</Label>
              <Input
                id="up-file"
                type="file"
                ref={fileInput}
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </div>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="up-url">Source URL</Label>
              <Input
                id="up-url"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://example.com/doc"
              />
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="up-title">Title (optional)</Label>
            <Input
              id="up-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Defaults to the file name"
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={loading}>
            {loading ? 'Uploading…' : 'Upload'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}