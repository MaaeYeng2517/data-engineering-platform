'use client'

import { useState } from 'react'
import { ShieldCheck, Plus, Edit, Trash2, FileText, AlertTriangle } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/table'
import { getList, post, put, remove, extractErrorDetail } from '@/lib/api/data'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'
import { toast } from 'sonner'

interface RoleDefinition {
  name?: string
  permissions?: string[]
}

interface Policy {
  id?: string
  name?: string
  description?: string
  rules?: Record<string, unknown>
  created_by?: string
  created_at?: string
  updated_at?: string
}

interface Approval {
  id?: string
  kb_id?: string
  document_id?: string
  creator_id?: string
  reviewers?: string[]
  status?: string
  decision?: string
  comments?: string
  decided_by?: string
  decided_at?: string
  created_at?: string
  updated_at?: string
}

interface AuditLog {
  id?: string
  user_id?: string
  action?: string
  resource?: string
  details?: Record<string, unknown>
  created_at?: string
}

export function GovernancePage() {
  const [newPolicyName, setNewPolicyName] = useState('')
  const [newPolicyDescription, setNewPolicyDescription] = useState('')
  const [newPolicyRules, setNewPolicyRules] = useState('{}')
  const [creatingPolicy, setCreatingPolicy] = useState(false)
  const [editingPolicyId, setEditingPolicyId] = useState<string | null>(null)
  const [editPolicyName, setEditPolicyName] = useState('')
  const [editPolicyDescription, setEditPolicyDescription] = useState('')
  const [editPolicyRules, setEditPolicyRules] = useState('{}')
  const [updatingPolicy, setUpdatingPolicy] = useState(false)

  const [newApprovalKbId, setNewApprovalKbId] = useState('')
  const [newApprovalDocId, setNewApprovalDocId] = useState('')
  const [newApprovalCreatorId, setNewApprovalCreatorId] = useState('')
  const [newApprovalReviewers, setNewApprovalReviewers] = useState('')
  const [creatingApproval, setCreatingApproval] = useState(false)

  const [policyError, setPolicyError] = useState<string | null>(null)
  const [approvalError, setApprovalError] = useState<string | null>(null)

  const roles = useApi(() => getList<RoleDefinition>('/governance/roles'), [])
  const permissions = useApi(() => getList<string>('/governance/permissions'), [])
  const policies = useApi(() => getList<Policy>('/governance/policies'), [])
  const approvals = useApi(() => getList<Approval>('/governance/approvals'), [])
  const auditLogs = useApi(() => getList<AuditLog>('/governance/audit?limit=100'), [])

  async function createPolicy() {
    if (!newPolicyName.trim()) {
      setPolicyError('Policy name is required')
      return
    }
    setCreatingPolicy(true)
    setPolicyError(null)
    try {
      let rules: Record<string, unknown> = {}
      try {
        rules = JSON.parse(newPolicyRules)
      } catch {
        setPolicyError('Invalid JSON in rules')
        return
      }
      await post<Policy>('/governance/policies', {
        name: newPolicyName.trim(),
        description: newPolicyDescription.trim(),
        rules,
      })
      toast.success(`Created policy "${newPolicyName}"`)
      setNewPolicyName('')
      setNewPolicyDescription('')
      setNewPolicyRules('{}')
      policies.reload()
    } catch (err) {
      setPolicyError(extractErrorDetail(err))
    } finally {
      setCreatingPolicy(false)
    }
  }

  function startEditPolicy(policy: Policy) {
    setEditingPolicyId(policy.id ?? '')
    setEditPolicyName(policy.name ?? '')
    setEditPolicyDescription(policy.description ?? '')
    setEditPolicyRules(JSON.stringify(policy.rules ?? {}, null, 2))
  }

  async function updatePolicy() {
    if (!editingPolicyId || !editPolicyName.trim()) return
    setUpdatingPolicy(true)
    setPolicyError(null)
    try {
      let rules: Record<string, unknown> = {}
      try {
        rules = JSON.parse(editPolicyRules)
      } catch {
        setPolicyError('Invalid JSON in rules')
        return
      }
      await put<Policy>(`/governance/policies/${editingPolicyId}`, {
        name: editPolicyName.trim(),
        description: editPolicyDescription.trim(),
        rules,
      })
      toast.success('Policy updated')
      setEditingPolicyId(null)
      setEditPolicyName('')
      setEditPolicyDescription('')
      setEditPolicyRules('{}')
      policies.reload()
    } catch (err) {
      setPolicyError(extractErrorDetail(err))
    } finally {
      setUpdatingPolicy(false)
    }
  }

  async function deletePolicy(id: string) {
    if (!confirm('Delete this governance policy?')) return
    try {
      await remove(`/governance/policies/${id}`)
      toast.success('Policy deleted')
      policies.reload()
    } catch (err) {
      setPolicyError(extractErrorDetail(err))
    }
  }

  async function createApproval() {
    if (!newApprovalKbId.trim() || !newApprovalDocId.trim() || !newApprovalCreatorId.trim() || !newApprovalReviewers.trim()) {
      setApprovalError('All fields are required')
      return
    }
    setCreatingApproval(true)
    setApprovalError(null)
    try {
      const reviewers = newApprovalReviewers.split(',').map(r => r.trim()).filter(Boolean)
      await post<Approval>('/governance/approvals', {
        kb_id: newApprovalKbId.trim(),
        document_id: newApprovalDocId.trim(),
        creator_id: newApprovalCreatorId.trim(),
        reviewers,
      })
      toast.success('Approval workflow submitted')
      setNewApprovalKbId('')
      setNewApprovalDocId('')
      setNewApprovalCreatorId('')
      setNewApprovalReviewers('')
      approvals.reload()
    } catch (err) {
      setApprovalError(extractErrorDetail(err))
    } finally {
      setCreatingApproval(false)
    }
  }

  async function approveDocument(approvalId: string, reviewerId: string) {
    try {
      await post<Approval>(`/governance/approvals/${approvalId}/approve`, {
        reviewer_id: reviewerId,
        comments: 'Approved via UI',
      })
      toast.success('Document approved')
      approvals.reload()
    } catch (err) {
      setPolicyError(extractErrorDetail(err))
    }
  }

  async function rejectDocument(approvalId: string, reviewerId: string) {
    try {
      await post<Approval>(`/governance/approvals/${approvalId}/reject`, {
        reviewer_id: reviewerId,
        comments: 'Rejected via UI',
      })
      toast.success('Document rejected')
      approvals.reload()
    } catch (err) {
      setPolicyError(extractErrorDetail(err))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Governance"
        description="Roles, permissions, policies and approval workflows across your workspace."
        actions={
          <ReloadButton
            onClick={() => {
              roles.reload()
              permissions.reload()
              policies.reload()
              approvals.reload()
              auditLogs.reload()
            }}
          />
        }
      />

      {/* Create Policy Dialog */}
      <Dialog open={creatingPolicy} onOpenChange={setCreatingPolicy}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create Governance Policy</DialogTitle>
            <DialogDescription>
              Define a policy with rules that can be evaluated against your data.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new-pol-name">Policy name</Label>
              <Input
                id="new-pol-name"
                value={newPolicyName}
                onChange={(e) => setNewPolicyName(e.target.value)}
                placeholder="PII protection policy"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-pol-desc">Description (optional)</Label>
              <Textarea
                id="new-pol-desc"
                rows={2}
                value={newPolicyDescription}
                onChange={(e) => setNewPolicyDescription(e.target.value)}
                placeholder="Policy purpose and scope"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-pol-rules">Rules (JSON)</Label>
              <Textarea
                id="new-pol-rules"
                rows={6}
                value={newPolicyRules}
                onChange={(e) => setNewPolicyRules(e.target.value)}
                placeholder='{"field": "email", "rule": "mask", "condition": "contains_pii"}'
                className="font-mono text-sm"
              />
            </div>
            {policyError && <p className="text-sm text-destructive">{policyError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreatingPolicy(false)}>
              Cancel
            </Button>
            <Button onClick={createPolicy} disabled={creatingPolicy}>
              {creatingPolicy ? 'Creating…' : 'Create policy'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Policy Dialog */}
      {editingPolicyId && (
        <Dialog open onOpenChange={(open) => !open && setEditingPolicyId(null)}>
          <DialogContent className="sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle>Edit Policy</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="edit-pol-name">Policy name</Label>
                <Input
                  id="edit-pol-name"
                  value={editPolicyName}
                  onChange={(e) => setEditPolicyName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-pol-desc">Description (optional)</Label>
                <Textarea
                  id="edit-pol-desc"
                  rows={2}
                  value={editPolicyDescription}
                  onChange={(e) => setEditPolicyDescription(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-pol-rules">Rules (JSON)</Label>
                <Textarea
                  id="edit-pol-rules"
                  rows={6}
                  value={editPolicyRules}
                  onChange={(e) => setEditPolicyRules(e.target.value)}
                  className="font-mono text-sm"
                />
              </div>
              {policyError && <p className="text-sm text-destructive">{policyError}</p>}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditingPolicyId(null)}>
                Cancel
              </Button>
              <Button onClick={updatePolicy} disabled={updatingPolicy}>
                {updatingPolicy ? 'Saving…' : 'Save changes'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Create Approval Dialog */}
      <Dialog open={creatingApproval} onOpenChange={setCreatingApproval}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Submit for Approval</DialogTitle>
            <DialogDescription>
              Create an approval workflow for a document.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="appr-kb">Knowledge base ID</Label>
              <Input
                id="appr-kb"
                value={newApprovalKbId}
                onChange={(e) => setNewApprovalKbId(e.target.value)}
                placeholder="kb-uuid"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="appr-doc">Document ID</Label>
              <Input
                id="appr-doc"
                value={newApprovalDocId}
                onChange={(e) => setNewApprovalDocId(e.target.value)}
                placeholder="doc-uuid"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="appr-creator">Creator ID (your user ID)</Label>
              <Input
                id="appr-creator"
                value={newApprovalCreatorId}
                onChange={(e) => setNewApprovalCreatorId(e.target.value)}
                placeholder="user-uuid"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="appr-reviewers">Reviewers (comma-separated user IDs)</Label>
              <Input
                id="appr-reviewers"
                value={newApprovalReviewers}
                onChange={(e) => setNewApprovalReviewers(e.target.value)}
                placeholder="user-uuid-1, user-uuid-2"
              />
            </div>
            {approvalError && <p className="text-sm text-destructive">{approvalError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreatingApproval(false)}>
              Cancel
            </Button>
            <Button onClick={createApproval} disabled={creatingApproval}>
              {creatingApproval ? 'Submitting…' : 'Submit for approval'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Roles */}
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

        {/* Permissions */}
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

      {/* Policies with CRUD */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            Policies
          </CardTitle>
          <Dialog>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                New policy
              </Button>
            </DialogTrigger>
          </Dialog>
        </CardHeader>
        <CardContent className="pt-0">
          <AsyncBoundary
            loading={policies.loading}
            error={policies.error}
            onRetry={policies.reload}
            isEmpty={!policies.data?.items.length}
            empty={
              <EmptyState
                title="No policies"
                description="Create a governance policy to enforce rules on your data."
                action={
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button>
                        <Plus className="mr-2 h-4 w-4" />
                        Create policy
                      </Button>
                    </DialogTrigger>
                  </Dialog>
                }
              />
            }
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead className="hidden md:table-cell">Description</TableHead>
                  <TableHead className="hidden lg:table-cell">Rules preview</TableHead>
                  <TableHead className="hidden md:table-cell">Created by</TableHead>
                  <TableHead className="hidden md:table-cell">Created</TableHead>
                  <TableHead className="text-right w-[120px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {policies.data?.items.map((pol, index) => (
                  <TableRow key={pol.id ?? index}>
                    <TableCell className="font-medium">{pol.name ?? `Policy ${index + 1}`}</TableCell>
                    <TableCell className="hidden max-w-[200px] truncate text-muted-foreground md:table-cell">
                      {pol.description ?? '—'}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell font-mono text-xs text-muted-foreground max-w-[200px] truncate">
                      {pol.rules ? JSON.stringify(pol.rules).slice(0, 60) + '…' : '—'}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">
                      {pol.created_by?.slice(0, 8) ?? '—'}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">
                      {pol.created_at ? new Date(pol.created_at).toLocaleDateString() : '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => startEditPolicy(pol)}
                          title="Edit policy"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deletePolicy(pol.id ?? '')}
                          className="text-destructive hover:text-destructive"
                          title="Delete policy"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </AsyncBoundary>
        </CardContent>
      </Card>

      {/* Approvals with CRUD */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            Approval Workflows
          </CardTitle>
          <Dialog>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                New approval
              </Button>
            </DialogTrigger>
          </Dialog>
        </CardHeader>
        <CardContent className="pt-0">
          <AsyncBoundary
            loading={approvals.loading}
            error={approvals.error}
            onRetry={approvals.reload}
            isEmpty={!approvals.data?.items.length}
            empty={
              <EmptyState
                title="No approval workflows"
                description="Submit documents for review and approval."
                action={
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button>
                        <Plus className="mr-2 h-4 w-4" />
                        Submit for approval
                      </Button>
                    </DialogTrigger>
                  </Dialog>
                }
              />
            }
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Document</TableHead>
                  <TableHead>Creator</TableHead>
                  <TableHead>Reviewers</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Decision</TableHead>
                  <TableHead className="hidden md:table-cell">Created</TableHead>
                  <TableHead className="text-right w-[120px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {approvals.data?.items.map((appr, index) => (
                  <TableRow key={appr.id ?? index}>
                    <TableCell className="font-mono text-xs">{appr.id?.slice(0, 12) ?? `appr-${index}`}</TableCell>
                    <TableCell className="text-muted-foreground">{appr.document_id?.slice(0, 12) ?? '—'}</TableCell>
                    <TableCell className="text-muted-foreground">{appr.creator_id?.slice(0, 8) ?? '—'}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {appr.reviewers?.length ?? 0} reviewer(s)
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          appr.status === 'approved' ? 'default' :
                          appr.status === 'rejected' ? 'destructive' :
                          'secondary'
                        }
                      >
                        {appr.status ?? 'pending'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {appr.decision ?? '—'}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">
                      {appr.created_at ? new Date(appr.created_at).toLocaleDateString() : '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        {appr.status === 'pending' && (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => approveDocument(appr.id ?? '', appr.reviewers?.[0] ?? '')}
                              className="text-green-600 hover:text-green-600"
                              title="Approve"
                            >
                              <ShieldCheck className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => rejectDocument(appr.id ?? '', appr.reviewers?.[0] ?? '')}
                              className="text-destructive hover:text-destructive"
                              title="Reject"
                            >
                              <AlertTriangle className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </AsyncBoundary>
        </CardContent>
      </Card>

      {/* Audit Logs */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-sm font-medium">Audit Logs</CardTitle>
          <ReloadButton onClick={auditLogs.reload} />
        </CardHeader>
        <CardContent className="pt-0">
          <AsyncBoundary
            loading={auditLogs.loading}
            error={auditLogs.error}
            onRetry={auditLogs.reload}
            isEmpty={!auditLogs.data?.items.length}
            empty={<EmptyState title="No audit logs" description="Audit logs will appear here as actions are performed." />}
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead className="hidden lg:table-cell">Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {auditLogs.data?.items.map((log, index) => (
                  <TableRow key={log.id ?? index}>
                    <TableCell className="text-muted-foreground font-mono text-xs">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : '—'}
                    </TableCell>
                    <TableCell className="text-muted-foreground font-mono text-xs">
                      {log.user_id?.slice(0, 8) ?? 'system'}
                    </TableCell>
                    <TableCell className="font-medium">{log.action ?? '—'}</TableCell>
                    <TableCell className="text-muted-foreground">{log.resource ?? '—'}</TableCell>
                    <TableCell className="hidden lg:table-cell font-mono text-xs text-muted-foreground max-w-[300px] truncate">
                      {log.details ? JSON.stringify(log.details) : '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </AsyncBoundary>
        </CardContent>
      </Card>
    </div>
  )
}