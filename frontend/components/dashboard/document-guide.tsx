'use client'

import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import {
  documentGuide,
  documentStatuses,
  guideFlow,
  guideFlowIcon,
} from '@/lib/documentation'

export function DocumentGuide() {
  const [active, setActive] = useState(documentGuide[0]?.id ?? '')

  return (
    <Card>
      <CardContent className="space-y-6 pt-6">
        <div>
          <h2 className="text-lg font-semibold">How this system works</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            What happens to a file after you upload it, and the concepts each
            dashboard area relies on.
          </p>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium">Processing pipeline</p>
          <div className="flex flex-wrap items-center gap-2">
            {guideFlow.map((stage, index) => {
              const Icon = guideFlowIcon
              return (
                <div key={stage} className="flex items-center gap-2">
                  <Badge variant={index === guideFlow.length - 1 ? 'default' : 'secondary'}>
                    <Icon className="mr-1 h-3 w-3" />
                    {stage}
                  </Badge>
                  {index < guideFlow.length - 1 && (
                    <span className="text-muted-foreground" aria-hidden>
                      →
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        <Tabs value={active} onValueChange={setActive}>
          <TabsList className="flex-wrap">
            {documentGuide.map((topic) => {
              const Icon = topic.icon
              return (
                <TabsTrigger key={topic.id} value={topic.id}>
                  <Icon className="mr-1.5 h-3.5 w-3.5" />
                  {topic.label}
                </TabsTrigger>
              )
            })}
          </TabsList>

          {documentGuide.map((topic) => (
            <TabsContent key={topic.id} value={topic.id} className="space-y-4 pt-4">
              <p className="text-sm text-muted-foreground">{topic.summary}</p>

              <ol className="space-y-3">
                {topic.steps.map((step, index) => (
                  <li key={step.title} className="rounded-lg border p-4">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{index + 1}</Badge>
                      <p className="font-medium">{step.title}</p>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">{step.detail}</p>
                  </li>
                ))}
              </ol>

              {topic.notes && topic.notes.length > 0 && (
                <div className="rounded-lg bg-muted/40 p-4">
                  <p className="mb-2 text-sm font-medium">Good to know</p>
                  <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                    {topic.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>

        <div>
          <p className="mb-2 text-sm font-medium">Status values in the table above</p>
          <ul className="grid gap-2 md:grid-cols-2">
            {documentStatuses.map((info) => (
              <li key={info.status} className="rounded-lg border p-4">
                <div className="flex items-center gap-2">
                  <Badge variant={info.tone}>{info.label}</Badge>
                  <code className="text-xs text-muted-foreground">{info.status}</code>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{info.description}</p>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}