'use client'

import { useState } from 'react'
import { Pencil, Plus } from 'lucide-react'
import { toast } from 'sonner'

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
import { Switch } from '@/components/ui/switch'
import { extractErrorDetail } from '@/lib/api/data'
import { ProfileConfigInput, ProfileConfigItem, profilesApi } from '@/lib/api/profiles'

const VALUE_TYPES = ['string', 'number', 'boolean', 'json']

export function ProfileConfigDialog({
  profileId,
  item,
  onSaved,
}: {
  profileId: string
  item?: ProfileConfigItem
  onSaved: () => void
}) {
  const [open, setOpen] = useState(false)
  const [key, setKey] = useState(item?.key ?? '')
  // A secret value is never returned, so the field starts blank and a blank
  // submit keeps whatever is stored.
  const [value, setValue] = useState('')
  const [description, setDescription] = useState(item?.description ?? '')
  const [valueType, setValueType] = useState(item?.value_type ?? 'string')
  const [isSecret, setIsSecret] = useState(item?.is_secret ?? false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function save() {
    if (!key.trim()) {
      setError('Give the setting a key')
      return
    }
    setLoading(true)
    setError(null)

    const body: ProfileConfigInput = {
      key: key.trim(),
      description: description.trim() || null,
      value_type: valueType,
      is_secret: isSecret,
    }
    if (value !== '') body.value = value

    try {
      if (item) {
        await profilesApi.updateConfig(profileId, item.id, body)
        toast.success('Setting updated')
      } else {
        await profilesApi.createConfig(profileId, body)
        toast.success('Setting added')
      }
      onSaved()
      setOpen(false)
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {item ? (
          <Button variant="ghost" size="sm" aria-label={`Edit ${item.key}`}>
            <Pencil className="h-4 w-4" />
          </Button>
        ) : (
          <Button variant="outline" size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Add setting
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{item ? 'Edit setting' : 'Add setting'}</DialogTitle>
          <DialogDescription>
            One configuration value for this environment.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="config-key">Key</Label>
            <Input
              id="config-key"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="RETRIES"
              autoFocus
              disabled={Boolean(item)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="config-value">Value</Label>
            <Input
              id="config-value"
              type={isSecret ? 'password' : 'text'}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={
                item ? 'Leave blank to keep the stored value' : isSecret ? 'Secret value' : '5'
              }
              autoComplete="off"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="config-type">Type</Label>
            <Select value={valueType} onValueChange={setValueType}>
              <SelectTrigger id="config-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {VALUE_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <Label htmlFor="config-secret">Secret</Label>
              <p className="text-xs text-muted-foreground">
                Encrypted at rest and never returned by the API.
              </p>
            </div>
            <Switch id="config-secret" checked={isSecret} onCheckedChange={setIsSecret} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="config-description">Description</Label>
            <Input
              id="config-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional"
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={save} disabled={loading}>
            {loading ? 'Saving…' : item ? 'Save changes' : 'Add setting'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
