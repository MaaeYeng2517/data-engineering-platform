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
import { Textarea } from '@/components/ui/textarea'
import { extractErrorDetail } from '@/lib/api/data'
import {
  AUTH_TYPE_LABELS,
  ProfileService,
  ProfileServiceInput,
  SERVICE_TYPE_LABELS,
  profilesApi,
} from '@/lib/api/profiles'

const SERVICE_TYPES = [
  'llm',
  'embedding',
  'vector_db',
  'search',
  'object_storage',
  'database',
  'cache',
  'queue',
  'monitoring',
  'cdn',
  'other',
]

const AUTH_TYPES = ['none', 'api_key', 'bearer', 'basic', 'oauth2', 'mtls', 'custom']

/** Parses `KEY=value` lines, one per line, into an object. */
function parsePairs(raw: string): Record<string, string> {
  const parsed: Record<string, string> = {}
  for (const line of raw.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed) continue
    const separator = trimmed.indexOf('=')
    if (separator < 1) continue
    parsed[trimmed.slice(0, separator).trim()] = trimmed.slice(separator + 1).trim()
  }
  return parsed
}

function stringifyPairs(pairs?: Record<string, unknown>): string {
  if (!pairs) return ''
  return Object.entries(pairs)
    .map(([key, value]) => `${key}=${String(value ?? '')}`)
    .join('\n')
}

export function ProfileServiceDialog({
  profileId,
  service,
  onSaved,
}: {
  profileId: string
  service?: ProfileService
  onSaved: () => void
}) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState(service?.name ?? '')
  const [serviceType, setServiceType] = useState(service?.service_type ?? 'other')
  const [provider, setProvider] = useState(service?.provider ?? '')
  const [apiBaseUrl, setApiBaseUrl] = useState(service?.api_base_url ?? '')
  const [host, setHost] = useState(service?.host ?? '')
  const [port, setPort] = useState(service?.port?.toString() ?? '')
  const [region, setRegion] = useState(service?.region ?? '')
  const [zone, setZone] = useState(service?.zone ?? '')
  const [authType, setAuthType] = useState(service?.auth_type ?? 'api_key')
  // Always blank on open: the API never returns a stored token, and leaving the
  // mask in the field would invite an accidental no-op "rotation" back to it.
  const [token, setToken] = useState('')
  const [username, setUsername] = useState(service?.username ?? '')
  const [envVars, setEnvVars] = useState(stringifyPairs(service?.env_vars))
  const [headers, setHeaders] = useState(stringifyPairs(service?.headers))
  const [timeout, setTimeout] = useState((service?.timeout_seconds ?? 30).toString())
  const [maxRetries, setMaxRetries] = useState((service?.max_retries ?? 3).toString())
  const [healthCheckUrl, setHealthCheckUrl] = useState(service?.health_check_url ?? '')
  const [healthCheckEnabled, setHealthCheckEnabled] = useState(
    service?.health_check_enabled ?? false
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function save() {
    if (!name.trim()) {
      setError('Give the service a name')
      return
    }
    if (!apiBaseUrl.trim() && !host.trim()) {
      setError('Set an API base URL or a host')
      return
    }
    setLoading(true)
    setError(null)

    const body: ProfileServiceInput = {
      name: name.trim(),
      service_type: serviceType,
      provider: provider.trim() || null,
      api_base_url: apiBaseUrl.trim() || null,
      host: host.trim() || null,
      port: port.trim() ? Number(port) : null,
      region: region.trim() || null,
      zone: zone.trim() || null,
      auth_type: authType,
      username: username.trim() || null,
      env_vars: parsePairs(envVars),
      headers: parsePairs(headers),
      timeout_seconds: Number(timeout) || 30,
      max_retries: Number(maxRetries) || 0,
      health_check_url: healthCheckUrl.trim() || null,
      health_check_enabled: healthCheckEnabled,
    }
    // Only send the token when a new one was typed, so editing an unrelated
    // field cannot wipe or overwrite the stored secret.
    if (token.trim()) body.token = token.trim()

    try {
      if (service) {
        await profilesApi.updateService(profileId, service.id, body)
        toast.success('Service updated')
      } else {
        await profilesApi.createService(profileId, body)
        toast.success('Service added')
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
        {service ? (
          <Button variant="ghost" size="sm" aria-label={`Edit ${service.name}`}>
            <Pencil className="h-4 w-4" />
          </Button>
        ) : (
          <Button variant="outline" size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Add service
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{service ? 'Edit service' : 'Add service'}</DialogTitle>
          <DialogDescription>
            Where the service lives and how to authenticate against it.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="service-name">Name</Label>
              <Input
                id="service-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="OpenAI"
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="service-type">Type</Label>
              <Select value={serviceType} onValueChange={setServiceType}>
                <SelectTrigger id="service-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SERVICE_TYPES.map((item) => (
                    <SelectItem key={item} value={item}>
                      {SERVICE_TYPE_LABELS[item] ?? item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="service-provider">Provider</Label>
              <Input
                id="service-provider"
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                placeholder="openai"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="service-auth">Auth type</Label>
              <Select value={authType} onValueChange={setAuthType}>
                <SelectTrigger id="service-auth">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AUTH_TYPES.map((item) => (
                    <SelectItem key={item} value={item}>
                      {AUTH_TYPE_LABELS[item] ?? item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="service-url">API base URL</Label>
            <Input
              id="service-url"
              value={apiBaseUrl}
              onChange={(e) => setApiBaseUrl(e.target.value)}
              placeholder="https://api.openai.com/v1"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="service-host">Host</Label>
              <Input
                id="service-host"
                value={host}
                onChange={(e) => setHost(e.target.value)}
                placeholder="minio"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="service-port">Port</Label>
              <Input
                id="service-port"
                value={port}
                onChange={(e) => setPort(e.target.value.replace(/\D/g, ''))}
                placeholder="9000"
                inputMode="numeric"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="service-region">Region</Label>
              <Input
                id="service-region"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                placeholder="eu-central-1"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="service-token">Token</Label>
            <Input
              id="service-token"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder={
                service?.has_token
                  ? 'Leave blank to keep the stored token'
                  : 'sk-…'
              }
              autoComplete="off"
            />
            <p className="text-xs text-muted-foreground">
              {service?.has_token
                ? `Stored token ${service.token_masked ?? ''} — type a new value to rotate it. Tokens are encrypted at rest and never shown again.`
                : 'Encrypted at rest and never returned by the API after saving.'}
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="service-username">Username</Label>
              <Input
                id="service-username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Optional"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="service-timeout">Timeout (seconds)</Label>
              <Input
                id="service-timeout"
                value={timeout}
                onChange={(e) => setTimeout(e.target.value.replace(/\D/g, ''))}
                inputMode="numeric"
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="service-env">Environment variables</Label>
              <Textarea
                id="service-env"
                value={envVars}
                onChange={(e) => setEnvVars(e.target.value)}
                placeholder="ORG=org-123"
                rows={3}
                className="font-mono text-xs"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="service-headers">Headers</Label>
              <Textarea
                id="service-headers"
                value={headers}
                onChange={(e) => setHeaders(e.target.value)}
                placeholder="X-Tenant=dataair"
                rows={3}
                className="font-mono text-xs"
              />
            </div>
          </div>

          <div className="space-y-2 rounded-lg border p-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="service-health-toggle">Health check</Label>
              <Switch
                id="service-health-toggle"
                checked={healthCheckEnabled}
                onCheckedChange={setHealthCheckEnabled}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Lets an administrator probe the endpoint and record healthy, degraded
              or down on this service.
            </p>
            {healthCheckEnabled && (
              <Input
                value={healthCheckUrl}
                onChange={(e) => setHealthCheckUrl(e.target.value)}
                placeholder={apiBaseUrl || 'https://api.example.com/health'}
                className="mt-2"
              />
            )}
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={save} disabled={loading}>
            {loading ? 'Saving…' : service ? 'Save changes' : 'Add service'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
