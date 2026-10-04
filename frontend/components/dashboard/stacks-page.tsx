'use client'

import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { PageHeader } from '@/components/shared/async'
import { platformStacks } from '@/lib/platform-tools'

export function StacksPage() {
  const [active, setActive] = useState(platformStacks[0]?.id ?? '')
  const selected = platformStacks.find((stack) => stack.id === active) ?? platformStacks[0]

  const languageCount =
    platformStacks.find((stack) => stack.id === 'languages')?.entries.length ?? 0
  const totalEntries = platformStacks.reduce((sum, stack) => sum + stack.entries.length, 0)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Stacks"
        description="Languages, runtimes and libraries this platform is built on, grouped by layer."
        actions={
          <Select value={active} onValueChange={setActive}>
            <SelectTrigger className="w-56">
              <SelectValue placeholder="Select a layer" />
            </SelectTrigger>
            <SelectContent>
              {platformStacks.map((stack) => (
                <SelectItem key={stack.id} value={stack.id}>
                  {stack.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Languages & runtimes</p>
            <p className="text-2xl font-bold">{languageCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Catalogued components</p>
            <p className="text-2xl font-bold">{totalEntries}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Layers covered</p>
            <p className="text-2xl font-bold">{platformStacks.length}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {platformStacks.map((stack) => {
          const Icon = stack.icon
          const isActive = stack.id === selected?.id
          return (
            <Card
              key={stack.id}
              className={isActive ? 'border-primary' : undefined}
              onClick={() => setActive(stack.id)}
            >
              <CardContent className="flex flex-col gap-3 pt-6">
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  <h2 className="font-semibold">{stack.label}</h2>
                  <Badge variant="secondary" className="ml-auto">
                    {stack.entries.length}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{stack.description}</p>
                <ul className="space-y-2">
                  {stack.entries.map((entry) => {
                    const EntryIcon = entry.icon
                    return (
                      <li
                        key={`${stack.id}-${entry.name}`}
                        className="rounded-lg border p-3"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="flex items-center gap-2 text-sm font-medium">
                            <EntryIcon className="h-3.5 w-3.5 text-muted-foreground" />
                            {entry.name}
                          </span>
                          <Badge variant="outline">{entry.version}</Badge>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">{entry.role}</p>
                      </li>
                    )
                  })}
                </ul>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}