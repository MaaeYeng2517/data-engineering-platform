'use client'

import { useState } from 'react'
import { Plus, Trash2, UserPlus, Users } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import { extractErrorDetail, getList, post, remove } from '@/lib/api/data'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'
import { useAuth } from '@/providers/auth-provider'
import { toast } from 'sonner'

interface WorkGroup {
  id?: string
  name?: string
  slug?: string
  description?: string
  is_active?: boolean
  member_count?: number
}

interface Member {
  id?: string
  user_id?: string
  role?: 'owner' | 'member'
  joined_at?: string
  user_email?: string
  user_full_name?: string
}

interface Candidate {
  id?: string
  email?: string
  full_name?: string
}

function CreateWorkGroupDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function create() {
    if (!name.trim()) {
      setError('Give the group a name')
      return
    }
    setLoading(true)
    setError(null)
    try {
      await post<WorkGroup>('/work-groups', {
        name: name.trim(),
        ...(description.trim() ? { description: description.trim() } : {}),
      })
      toast.success('Work group created')
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
          New work group
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>New work group</DialogTitle>
          <DialogDescription>
            Group people in this workspace to collaborate on shared data.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="wg-name">Name</Label>
            <Input
              id="wg-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Analytics team"
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="wg-desc">Description (optional)</Label>
            <Textarea
              id="wg-desc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What does this group work on?"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={create} disabled={loading}>
            {loading ? 'Creating…' : 'Create group'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function MembersDialog({
  group,
  onChanged,
}: {
  group: WorkGroup
  onChanged: () => void
}) {
  const [open, setOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const members = useApi(() => getList<Member>(`/work-groups/${group.id}/members`), [group.id, open])
  const candidates = useApi(
    () =>
      open
        ? getList<Candidate>(`/work-groups/${group.id}/candidates`)
        : Promise.resolve({ items: [], total: 0 }),
    [group.id, open]
  )

  async function addMember() {
    if (!selectedUser) {
      setError('Select someone to add')
      return
    }
    setAdding(true)
    setError(null)
    try {
      await post(`/work-groups/${group.id}/members`, {
        user_id: selectedUser,
        role: 'member',
      })
      toast.success('Member added')
      setSelectedUser('')
      members.reload()
      candidates.reload()
      onChanged()
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setAdding(false)
    }
  }

  async function removeMember(memberId: string) {
    setError(null)
    try {
      await remove(`/work-groups/${group.id}/members/${memberId}`)
      toast.success('Member removed')
      members.reload()
      candidates.reload()
      onChanged()
    } catch (err) {
      setError(extractErrorDetail(err))
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Users className="mr-2 h-4 w-4" />
          Members
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{group.name} · members</DialogTitle>
          <DialogDescription>
            People in this workspace who belong to the group.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row">
            <div className="flex-1">
              <Select value={selectedUser} onValueChange={setSelectedUser}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a member to add" />
                </SelectTrigger>
                <SelectContent>
                  {candidates.data?.items.map((candidate, index) => (
                    <SelectItem key={candidate.id ?? index} value={candidate.id ?? ''}>
                      {candidate.full_name || candidate.email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={addMember} disabled={adding}>
              <UserPlus className="mr-2 h-4 w-4" />
              {adding ? 'Adding…' : 'Add'}
            </Button>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="max-h-64 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Member</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead className="text-right">Remove</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.data?.items.map((member, index) => (
                  <TableRow key={member.id ?? index}>
                    <TableCell>
                      <p className="font-medium">{member.user_full_name || '—'}</p>
                      <p className="text-xs text-muted-foreground">{member.user_email}</p>
                    </TableCell>
                    <TableCell>
                      <Badge variant={member.role === 'owner' ? 'default' : 'secondary'}>
                        {member.role ?? 'member'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {member.id && (
                        <Button
                          variant="ghost"
                          size="sm"
                          aria-label={`Remove ${member.user_email ?? 'member'}`}
                          onClick={() => removeMember(member.id as string)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function WorkGroupsPage() {
  const { user } = useAuth()
  const groups = useApi(() => getList<WorkGroup>('/work-groups'), [])
  const [deleting, setDeleting] = useState<string | null>(null)

  async function deleteGroup(id: string) {
    setDeleting(id)
    try {
      await remove(`/work-groups/${id}`)
      toast.success('Work group deleted')
      groups.reload()
    } catch (err) {
      toast.error(extractErrorDetail(err))
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Work Groups"
        description={`Teams within ${user?.email ? 'your' : 'this'} workspace, used to organise collaboration.`}
        actions={
          <>
            <ReloadButton onClick={groups.reload} />
            <CreateWorkGroupDialog onCreated={groups.reload} />
          </>
        }
      />

      <AsyncBoundary
        loading={groups.loading}
        error={groups.error}
        onRetry={groups.reload}
        isEmpty={!groups.data?.items.length}
        empty={
          <EmptyState
            title="No work groups"
            description="Create a group to organise the people working on your data."
            action={<CreateWorkGroupDialog onCreated={groups.reload} />}
          />
        }
      >
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {groups.data?.items.map((group, index) => (
            <Card key={group.id ?? index}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    {group.name}
                  </CardTitle>
                  <Badge variant={group.is_active === false ? 'secondary' : 'default'}>
                    {group.member_count ?? 0} member{(group.member_count ?? 0) === 1 ? '' : 's'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  {group.description ?? 'No description.'}
                </p>
                <p className="text-xs text-muted-foreground">
                  Slug: <span className="font-mono">{group.slug}</span>
                </p>
                <div className="flex items-center justify-between gap-2">
                  <MembersDialog group={group} onChanged={groups.reload} />
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={deleting === group.id}
                    onClick={() => group.id && deleteGroup(group.id)}
                    aria-label={`Delete ${group.name}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </AsyncBoundary>
    </div>
  )
}