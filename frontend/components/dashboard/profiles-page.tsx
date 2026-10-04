'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { Copy, Globe2, Pencil, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
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
import { Textarea } from '@/components/ui/textarea'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { extractErrorDetail } from '@/lib/api/data'
import {
  CLOUD_LABELS,
  ENVIRONMENT_LABELS,
  ProfileInput,
  ServiceProfile,
  profilesApi,
} from '@/lib/api/profiles'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'

const ENVIRONMENTS = ['development', 'staging', 'production', 'testing']
const CLOUD_PROVIDERS = ['aws', 'gcp', 'azure', 'on_premise', 'hybrid', 'other']

/** Parses `KEY=value` lines, one per line, into a variables object. */
function parseVariables(raw: string): Record<string, string> {
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

function stringifyVariables(variables?: Record<string, unknown>): string {
  if (!variables) return ''
  return Object.entries(variables)
    .map(([key, value]) => `${key}=${String(value ?? '')}`)
    .join('\n')
}

function ProfileDialog({
  profile,
  onSaved,
}: {
  profile?: ServiceProfile
  onSaved: () => void
}) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState(profile?.name ?? '')
  const [description, setDescription] = useState(profile?.description ?? '')
  const [environment, setEnvironment] = useState(profile?.environment ?? 'development')
  const [cloudProvider, setCloudProvider] = useState(profile?.cloud_provider ?? 'other')
  const [region, setRegion] = useState(profile?.region ?? '')
  const [zone, setZone] = useState(profile?.zone ?? '')
  const [variables, setVariables] = useState(stringifyVariables(profile?.variables))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function save() {
    if (!name.trim()) {
      setError('Give the profile a name')
      return
    }
    setLoading(true)
    setError(null)
    const body: ProfileInput = {
      name: name.trim(),
      description: description.trim() || null,
      environment,
      cloud_provider: cloudProvider,
      region: region.trim() || null,
      zone: zone.trim() || null,
      variables: parseVariables(variables),
    }
    try {
      if (profile) {
        await profilesApi.update(profile.id, body)
        toast.success('Profile updated')
      } else {
        await profilesApi.create(body)
        toast.success('Profile created')
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
        {profile ? (
          <Button variant="ghost" size="sm" aria-label={`Edit ${profile.name}`}>
            <Pencil className="h-4 w-4" />
          </Button>
        ) : (
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New profile
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{profile ? 'Edit profile' : 'New profile'}</DialogTitle>
          <DialogDescription>
            A profile groups the configuration and services of one environment.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="profile-name">Name</Label>
            <Input
              id="profile-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Production EU"
              autoFocus
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="profile-environment">Environment</Label>
              <Select value={environment} onValueChange={setEnvironment}>
                <SelectTrigger id="profile-environment">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ENVIRONMENTS.map((item) => (
                    <SelectItem key={item} value={item}>
                      {ENVIRONMENT_LABELS[item] ?? item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="profile-cloud">Cloud provider</Label>
              <Select value={cloudProvider} onValueChange={setCloudProvider}>
                <SelectTrigger id="profile-cloud">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CLOUD_PROVIDERS.map((item) => (
                    <SelectItem key={item} value={item}>
                      {CLOUD_LABELS[item] ?? item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="profile-region">Region</Label>
              <Input
                id="profile-region"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                placeholder="eu-central-1"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="profile-zone">Zone</Label>
              <Input
                id="profile-zone"
                value={zone}
                onChange={(e) => setZone(e.target.value)}
                placeholder="eu-central-1a"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="profile-variables">Environment variables</Label>
            <Textarea
              id="profile-variables"
              value={variables}
              onChange={(e) => setVariables(e.target.value)}
              placeholder={'LOG_LEVEL=info\nWORKERS=8'}
              rows={4}
              className="font-mono text-xs"
            />
            <p className="text-xs text-muted-foreground">
              One <code>KEY=value</code> per line. Secrets belong in a service token
              or a secret config key, not here.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="profile-description">Description</Label>
            <Textarea
              id="profile-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What runs in this environment"
              rows={3}
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={save} disabled={loading}>
            {loading ? 'Saving…' : profile ? 'Save changes' : 'Create profile'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function ProfilesPage() {
  const [environment, setEnvironment] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [busyId, setBusyId] = useState<string | null>(null)

  const profiles = useApi(
    () =>
      profilesApi.list({
        environment: environment === 'all' ? undefined : environment,
        search: search.trim() || undefined,
      }),
    [environment, search]
  )

  const summary = useMemo(() => {
    const items = profiles.data?.items ?? []
    return {
      total: items.length,
      services: items.reduce((sum, profile) => sum + (profile.service_count ?? 0), 0),
      production: items.filter((profile) => profile.environment === 'production').length,
    }
  }, [profiles.data])

  async function duplicate(profile: ServiceProfile) {
    setBusyId(profile.id)
    try {
      await profilesApi.duplicate(profile.id)
      toast.success(`Duplicated ${profile.name}`)
      profiles.reload()
    } catch (err) {
      toast.error(extractErrorDetail(err))
    } finally {
      setBusyId(null)
    }
  }

  async function destroy(profile: ServiceProfile) {
    if (!window.confirm(`Delete "${profile.name}" and every service in it?`)) return
    setBusyId(profile.id)
    try {
      await profilesApi.remove(profile.id)
      toast.success('Profile deleted')
      profiles.reload()
    } catch (err) {
      toast.error(extractErrorDetail(err))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Service Profiles"
        description="Store system configuration and the services of each environment, with tokens, endpoints, hosting and cloud details."
        actions={
          <>
            <ReloadButton onClick={profiles.reload} />
            <ProfileDialog onSaved={profiles.reload} />
          </>
        }
      />

      <Card>
        <CardContent className="flex flex-col gap-3 pt-6 sm:flex-row sm:items-center">
          <div className="flex-1">
            <Label htmlFor="profile-search" className="sr-only">
              Search profiles
            </Label>
            <Input
              id="profile-search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name or slug"
            />
          </div>
          <div className="sm:w-56">
            <Select value={environment} onValueChange={setEnvironment}>
              <SelectTrigger id="profile-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All environments</SelectItem>
                {ENVIRONMENTS.map((item) => (
                  <SelectItem key={item} value={item}>
                    {ENVIRONMENT_LABELS[item] ?? item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <AsyncBoundary
        loading={profiles.loading}
        error={profiles.error}
        onRetry={profiles.reload}
        isEmpty={!profiles.data?.items.length}
        empty={
          <EmptyState
            title="No profiles yet"
            description="Create a profile to hold the configuration and services of an environment."
            action={<ProfileDialog onSaved={profiles.reload} />}
          />
        }
      >
        <>
          <p className="text-sm text-muted-foreground">
            {summary.total} profiles · {summary.services} services ·{' '}
            {summary.production} production
          </p>

          <Card>
            <CardContent className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Environment</TableHead>
                    <TableHead>Hosting</TableHead>
                    <TableHead className="text-right">Services</TableHead>
                    <TableHead className="text-right">Config</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {profiles.data?.items.map((profile) => (
                    <TableRow key={profile.id}>
                      <TableCell className="font-medium">
                        <Link
                          href={`/dashboard/profiles/${profile.id}`}
                          className="hover:underline"
                        >
                          {profile.name}
                        </Link>
                        <p className="font-mono text-xs text-muted-foreground">
                          {profile.slug}
                        </p>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={profile.environment === 'production' ? 'destructive' : 'secondary'}
                        >
                          {ENVIRONMENT_LABELS[profile.environment] ?? profile.environment}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-sm">
                          <Globe2 className="h-3.5 w-3.5 text-muted-foreground" />
                          {CLOUD_LABELS[profile.cloud_provider] ?? profile.cloud_provider}
                        </div>
                        {profile.region && (
                          <p className="text-xs text-muted-foreground">
                            {profile.region}
                            {profile.zone ? ` · ${profile.zone}` : ''}
                          </p>
                        )}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {profile.service_count}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {profile.config_count}
                      </TableCell>
                      <TableCell>
                        <Badge variant={profile.is_active ? 'default' : 'secondary'}>
                          {profile.is_active ? 'Active' : 'Disabled'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={busyId === profile.id}
                            onClick={() => duplicate(profile)}
                            aria-label={`Duplicate ${profile.name}`}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                          <ProfileDialog profile={profile} onSaved={profiles.reload} />
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={busyId === profile.id}
                            onClick={() => destroy(profile)}
                            aria-label={`Delete ${profile.name}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      </AsyncBoundary>
    </div>
  )
}
