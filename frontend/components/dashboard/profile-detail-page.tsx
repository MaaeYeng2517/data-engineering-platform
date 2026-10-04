'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Activity, KeyRound, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { extractErrorDetail } from '@/lib/api/data'
import {
  AUTH_TYPE_LABELS,
  CLOUD_LABELS,
  ENVIRONMENT_LABELS,
  SERVICE_TYPE_LABELS,
  profilesApi,
} from '@/lib/api/profiles'
import { AsyncBoundary, PageHeader, ReloadButton, useApi } from '@/components/shared/async'
import { ProfileServiceDialog } from './profile-service-dialog'
import { ProfileConfigDialog } from './profile-config-dialog'

const HEALTH_VARIANTS: Record<string, 'default' | 'secondary' | 'destructive'> = {
  healthy: 'default',
  degraded: 'secondary',
  down: 'destructive',
  unknown: 'secondary',
}

export function ProfileDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const profileId = params?.id
  const [busyId, setBusyId] = useState<string | null>(null)

  const profile = useApi(
    () => (profileId ? profilesApi.get(profileId) : Promise.reject(new Error('Missing profile'))),
    [profileId]
  )

  async function checkService(serviceId: string, name: string) {
    setBusyId(serviceId)
    try {
      const updated = await profilesApi.checkService(profileId as string, serviceId)
      toast.success(`${name} is ${updated.health_status}`)
      profile.reload()
    } catch (err) {
      toast.error(extractErrorDetail(err))
    } finally {
      setBusyId(null)
    }
  }

  async function removeService(serviceId: string, name: string) {
    if (!window.confirm(`Remove "${name}" from this profile?`)) return
    setBusyId(serviceId)
    try {
      await profilesApi.removeService(profileId as string, serviceId)
      toast.success('Service removed')
      profile.reload()
    } catch (err) {
      toast.error(extractErrorDetail(err))
    } finally {
      setBusyId(null)
    }
  }

  async function removeConfig(itemId: string, key: string) {
    if (!window.confirm(`Delete the setting "${key}"?`)) return
    setBusyId(itemId)
    try {
      await profilesApi.removeConfig(profileId as string, itemId)
      toast.success('Setting deleted')
      profile.reload()
    } catch (err) {
      toast.error(extractErrorDetail(err))
    } finally {
      setBusyId(null)
    }
  }

  async function destroyProfile(name: string) {
    if (!window.confirm(`Delete "${name}" and every service and setting in it?`)) return
    try {
      await profilesApi.remove(profileId as string)
      toast.success('Profile deleted')
      router.push('/dashboard/profiles')
    } catch (err) {
      toast.error(extractErrorDetail(err))
    }
  }

  const data = profile.data

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="-ml-2">
        <Link href="/dashboard/profiles">
          <ArrowLeft className="mr-2 h-4 w-4" />
          All profiles
        </Link>
      </Button>

      <AsyncBoundary
        loading={profile.loading}
        error={profile.error}
        onRetry={profile.reload}
        isEmpty={!data}
        empty={<p className="text-sm text-muted-foreground">Profile not found.</p>}
      >
        {data && (
          <>
            <PageHeader
              title={data.name}
              description={data.description ?? 'No description'}
              actions={
                <>
                  <ReloadButton onClick={profile.reload} />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => destroyProfile(data.name)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete profile
                  </Button>
                </>
              }
            />

            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={data.environment === 'production' ? 'destructive' : 'secondary'}>
                {ENVIRONMENT_LABELS[data.environment] ?? data.environment}
              </Badge>
              <Badge variant="outline">
                {CLOUD_LABELS[data.cloud_provider] ?? data.cloud_provider}
              </Badge>
              {data.region && <Badge variant="outline">{data.region}</Badge>}
              {data.zone && <Badge variant="outline">{data.zone}</Badge>}
              <span className="font-mono text-xs text-muted-foreground">{data.slug}</span>
            </div>

            <Tabs defaultValue="services">
              <TabsList>
                <TabsTrigger value="services">Services ({data.services.length})</TabsTrigger>
                <TabsTrigger value="config">Configuration ({data.config_items.length})</TabsTrigger>
                <TabsTrigger value="variables">Variables</TabsTrigger>
              </TabsList>

              <TabsContent value="services" className="mt-4 space-y-4">
                <div className="flex justify-end">
                  <ProfileServiceDialog profileId={data.id} onSaved={profile.reload} />
                </div>

                {data.services.length === 0 ? (
                  <Card>
                    <CardContent className="py-12 text-center text-sm text-muted-foreground">
                      No services in this profile yet. Add one to record its endpoint,
                      auth type and token.
                    </CardContent>
                  </Card>
                ) : (
                  <Card>
                    <CardContent className="pt-6">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Service</TableHead>
                            <TableHead>Endpoint</TableHead>
                            <TableHead>Auth</TableHead>
                            <TableHead>Token</TableHead>
                            <TableHead>Health</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {data.services.map((service) => (
                            <TableRow key={service.id}>
                              <TableCell className="font-medium">
                                {service.name}
                                <p className="text-xs text-muted-foreground">
                                  {SERVICE_TYPE_LABELS[service.service_type] ??
                                    service.service_type}
                                  {service.provider ? ` · ${service.provider}` : ''}
                                </p>
                              </TableCell>
                              <TableCell className="font-mono text-xs">
                                {service.api_base_url ??
                                  [service.host, service.port].filter(Boolean).join(':') ??
                                  '—'}
                                {service.region && (
                                  <p className="text-muted-foreground">{service.region}</p>
                                )}
                              </TableCell>
                              <TableCell className="text-sm">
                                {AUTH_TYPE_LABELS[service.auth_type] ?? service.auth_type}
                              </TableCell>
                              <TableCell>
                                {service.has_token ? (
                                  <span className="inline-flex items-center gap-1 font-mono text-xs text-muted-foreground">
                                    <KeyRound className="h-3 w-3" />
                                    {service.token_masked ?? 'set'}
                                  </span>
                                ) : (
                                  <span className="text-muted-foreground">—</span>
                                )}
                              </TableCell>
                              <TableCell>
                                <Badge
                                  variant={HEALTH_VARIANTS[service.health_status] ?? 'secondary'}
                                >
                                  {service.health_status}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex items-center justify-end gap-1">
                                  {service.health_check_enabled && (
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      disabled={busyId === service.id}
                                      onClick={() => checkService(service.id, service.name)}
                                      aria-label={`Check ${service.name}`}
                                    >
                                      <Activity className="h-4 w-4" />
                                    </Button>
                                  )}
                                  <ProfileServiceDialog
                                    profileId={data.id}
                                    service={service}
                                    onSaved={profile.reload}
                                  />
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    disabled={busyId === service.id}
                                    onClick={() => removeService(service.id, service.name)}
                                    aria-label={`Remove ${service.name}`}
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
                )}
              </TabsContent>

              <TabsContent value="config" className="mt-4 space-y-4">
                <div className="flex justify-end">
                  <ProfileConfigDialog profileId={data.id} onSaved={profile.reload} />
                </div>

                {data.config_items.length === 0 ? (
                  <Card>
                    <CardContent className="py-12 text-center text-sm text-muted-foreground">
                      No configuration settings in this profile yet.
                    </CardContent>
                  </Card>
                ) : (
                  <Card>
                    <CardContent className="pt-6">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Key</TableHead>
                            <TableHead>Value</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {data.config_items.map((item) => (
                            <TableRow key={item.id}>
                              <TableCell className="font-mono text-xs font-medium">
                                {item.key}
                                {item.description && (
                                  <p className="font-sans text-xs font-normal text-muted-foreground">
                                    {item.description}
                                  </p>
                                )}
                              </TableCell>
                              <TableCell className="font-mono text-xs">
                                {item.is_secret ? (
                                  <span className="text-muted-foreground">
                                    {item.value_masked ?? 'set'}
                                  </span>
                                ) : (
                                  (item.value ?? '—')
                                )}
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline">{item.value_type}</Badge>
                                {item.is_secret && (
                                  <Badge variant="secondary" className="ml-1">
                                    secret
                                  </Badge>
                                )}
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex items-center justify-end gap-1">
                                  <ProfileConfigDialog
                                    profileId={data.id}
                                    item={item}
                                    onSaved={profile.reload}
                                  />
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    disabled={busyId === item.id}
                                    onClick={() => removeConfig(item.id, item.key)}
                                    aria-label={`Delete ${item.key}`}
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
                )}
              </TabsContent>

              <TabsContent value="variables" className="mt-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Profile variables</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {Object.keys(data.variables ?? {}).length === 0 ? (
                      <p className="py-6 text-center text-sm text-muted-foreground">
                        No profile variables. Edit the profile to add them.
                      </p>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Key</TableHead>
                            <TableHead>Value</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {Object.entries(data.variables).map(([key, value]) => (
                            <TableRow key={key}>
                              <TableCell className="font-mono text-xs font-medium">
                                {key}
                              </TableCell>
                              <TableCell className="font-mono text-xs">
                                {String(value ?? '')}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}
      </AsyncBoundary>
    </div>
  )
}
