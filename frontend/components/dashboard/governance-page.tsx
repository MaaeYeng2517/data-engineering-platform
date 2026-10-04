'use client'

import { ShieldCheck } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { getList } from '@/lib/api/data'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'

interface RoleDefinition {
  name?: string
  permissions?: string[]
}

export function GovernancePage() {
  const roles = useApi(() => getList<RoleDefinition>('/governance/roles'), [])
  const permissions = useApi(() => getList<string>('/governance/permissions'), [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Governance"
        description="Roles, permissions and policy enforcement across your workspace."
        actions={
          <ReloadButton
            onClick={() => {
              roles.reload()
              permissions.reload()
            }}
          />
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardContent className="pt-6">
            <h2 className="mb-3 flex items-center gap-2 font-semibold">
              <ShieldCheck className="h-4 w-4 text-muted-foreground" />
              Roles
            </h2>
            <AsyncBoundary
              loading={roles.loading}
              error={roles.error}
              onRetry={roles.reload}
              isEmpty={!roles.data?.items.length}
              empty={
                <EmptyState
                  title="No roles"
                  description="No roles are defined in this deployment."
                />
              }
            >
              <ul className="space-y-3">
                {roles.data?.items.map((role, index) => (
                  <li key={role.name ?? index} className="rounded-lg border p-4">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium">{role.name ?? 'Role'}</p>
                      <Badge variant="outline">
                        {role.permissions?.length ?? 0} permissions
                      </Badge>
                    </div>
                    {role.permissions && role.permissions.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {role.permissions.map((permission) => (
                          <Badge key={permission} variant="secondary">
                            {permission}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </AsyncBoundary>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <h2 className="mb-3 font-semibold">Permissions</h2>
            <AsyncBoundary
              loading={permissions.loading}
              error={permissions.error}
              onRetry={permissions.reload}
              isEmpty={!permissions.data?.items.length}
              empty={
                <EmptyState
                  title="No permissions"
                  description="No permission matrix is published by the API."
                />
              }
            >
              <div className="flex flex-wrap gap-2">
                {permissions.data?.items.map((permission, index) => (
                  <Badge key={permission || index} variant="outline">
                    {permission}
                  </Badge>
                ))}
              </div>
            </AsyncBoundary>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}