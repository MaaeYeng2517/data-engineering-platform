'use client'

import { useEffect, useState } from 'react'
import { Building2, LogOut, Moon, Sun, User } from 'lucide-react'
import { useTheme } from 'next-themes'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { getList, patch } from '@/lib/api/data'
import { PageHeader, useApi } from '@/components/shared/async'
import { useAuth } from '@/providers/auth-provider'

interface Workspace {
  id?: string
  name?: string
  slug?: string
  description?: string
  is_active?: boolean
  created_at?: string
}

export function WorkspacePage() {
  const workspaces = useApi(() => getList<Workspace>('/tenants/'), [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workspace"
        description="The tenant your account and all its data belong to."
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {workspaces.loading && (
          <p className="col-span-full py-10 text-center text-sm text-muted-foreground">
            Loading…
          </p>
        )}
        {workspaces.data?.items.map((workspace, index) => (
          <Card key={workspace.id ?? index}>
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                  {workspace.name ?? `Workspace ${index + 1}`}
                </CardTitle>
                <Badge variant={workspace.is_active === false ? 'secondary' : 'default'}>
                  {workspace.is_active === false ? 'Disabled' : 'Active'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-1.5 text-sm">
              <p className="text-muted-foreground">
                {workspace.description ?? 'No description.'}
              </p>
              <p className="text-xs text-muted-foreground">
                Slug: <span className="font-mono">{workspace.slug ?? '—'}</span>
              </p>
              {workspace.created_at && (
                <p className="text-xs text-muted-foreground">
                  Created {new Date(workspace.created_at).toLocaleDateString()}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {workspaces.error && (
        <p className="text-sm text-destructive">{workspaces.error}</p>
      )}
    </div>
  )
}

export function SettingsPage() {
  const { user, updateProfile, logout } = useAuth()
  const { theme, setTheme } = useTheme()
  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [status, setStatus] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setFullName(user?.full_name ?? '')
  }, [user])

  async function saveProfile() {
    setSaving(true)
    setStatus(null)
    try {
      await updateProfile({ full_name: fullName })
      setStatus('Profile updated')
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      setStatus(e.response?.data?.detail ?? 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="Manage your profile and preferences." />

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <User className="h-4 w-4 text-muted-foreground" />
            Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" value={user?.email ?? ''} disabled />
          </div>
          <div className="space-y-2">
            <Label htmlFor="fullname">Full name</Label>
            <Input
              id="fullname"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Your name"
            />
          </div>
          <div className="flex items-center gap-3">
            <Button onClick={saveProfile} disabled={saving}>
              {saving ? 'Saving…' : 'Save changes'}
            </Button>
            {status && <span className="text-sm text-muted-foreground">{status}</span>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Appearance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Label htmlFor="theme">Theme</Label>
          <Select value={theme ?? 'system'} onValueChange={setTheme}>
            <SelectTrigger id="theme" className="w-full sm:w-64">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="light">
                <span className="flex items-center gap-2">
                  <Sun className="h-4 w-4" /> Light
                </span>
              </SelectItem>
              <SelectItem value="dark">
                <span className="flex items-center gap-2">
                  <Moon className="h-4 w-4" /> Dark
                </span>
              </SelectItem>
              <SelectItem value="system">System</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Session</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Signing out clears your session cookies on this device.
          </p>
          <Separator />
          <Button variant="destructive" onClick={logout}>
            <LogOut className="mr-2 h-4 w-4" />
            Sign out
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}