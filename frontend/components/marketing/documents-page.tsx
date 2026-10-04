'use client'

import Link from 'next/link'
import { useState } from 'react'
import { ArrowRight, Terminal } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  documentGuide,
  documentStatuses,
  guideFlow,
  guideFlowIcon,
} from '@/lib/documentation'
import { platformTools } from '@/lib/platform-tools'

const quickStart: { title: string; detail: string }[] = [
  {
    title: 'Create a workspace',
    detail:
      'Registering an account creates a workspace, seeds the membership plans and puts you on the free plan.',
  },
  {
    title: 'Add a knowledge base',
    detail:
      'A knowledge base holds the documents, metadata schema, workflows and evaluation sets for one body of content.',
  },
  {
    title: 'Upload or connect',
    detail:
      'Upload files from the Documents page, or register a source and let a connector sync it on a schedule.',
  },
  {
    title: 'Publish and search',
    detail:
      'Publish the knowledge base, then query it from Search or RAG with citations back to the source chunks.',
  },
]

export function DocumentsPage() {
  const [active, setActive] = useState(documentGuide[0]?.id ?? '')

  return (
    <div className="container flex-1 space-y-16 py-16">
      <section className="max-w-3xl space-y-4">
        <Badge variant="outline">Documentation</Badge>
        <h1 className="text-4xl font-bold tracking-tight">
          How the DataAir platform works
        </h1>
        <p className="text-lg text-muted-foreground">
          What happens to a document after you upload it, what each dashboard
          area is responsible for, and which concepts everything else builds
          on.
        </p>
        <div className="flex flex-wrap gap-3 pt-2">
          <Button asChild>
            <Link href="/register">
              Get started
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Quick start</h2>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {quickStart.map((step, index) => (
            <Card key={step.title}>
              <CardContent className="pt-6">
                <Badge variant="outline">Step {index + 1}</Badge>
                <h3 className="mt-3 font-medium">{step.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{step.detail}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Processing pipeline</h2>
        <p className="max-w-3xl text-muted-foreground">
          Every document follows the same path. Each stage is idempotent, so a
          failed run can be retried without duplicating content.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          {guideFlow.map((stage, index) => {
            const Icon = guideFlowIcon
            return (
              <div key={stage} className="flex items-center gap-2">
                <Badge
                  variant={index === guideFlow.length - 1 ? 'default' : 'secondary'}
                  className="text-sm"
                >
                  <Icon className="mr-1 h-3.5 w-3.5" />
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
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Concepts</h2>
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
              <p className="max-w-3xl text-muted-foreground">{topic.summary}</p>

              <ol className="grid gap-4 md:grid-cols-2">
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
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Document status values</h2>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {documentStatuses.map((info) => (
            <Card key={info.status}>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Badge variant={info.tone}>{info.label}</Badge>
                  <code className="text-xs text-muted-foreground">{info.status}</code>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{info.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Operator tools</h2>
        <p className="max-w-3xl text-muted-foreground">
          Every service in the stack exposes its own interface. Signed-in users
          find the same list, with live status, in the dashboard.
        </p>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {platformTools.map((tool) => {
            const Icon = tool.icon
            return (
              <Card key={tool.id}>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    <h3 className="font-medium">{tool.name}</h3>
                    <Badge variant="outline" className="ml-auto">
                      {tool.category}
                    </Badge>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {tool.description}
                  </p>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Using the API directly</h2>
        <p className="max-w-3xl text-muted-foreground">
          Browser sessions authenticate with httpOnly cookies plus a CSRF
          header. Scripts and services should use an API key instead.
        </p>
        <Card>
          <CardContent className="space-y-3 pt-6">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-muted-foreground" />
              <p className="font-medium">Send a request with an API key</p>
            </div>
            <pre className="overflow-x-auto rounded-lg bg-muted p-4 text-sm">
{`curl http://localhost:8000/api/v1/search/ \\
  -H "x-api-key: dk_..." \\
  -H "Content-Type: application/json" \\
  -d '{"query": "how is billing calculated?", "kb_ids": ["<uuid>"]}'`}
            </pre>
            <p className="text-sm text-muted-foreground">
              Interactive schemas are served at{' '}
              <Link href="http://localhost:8000/docs" className="underline">
                /docs
              </Link>
              .
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}