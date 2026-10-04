import Link from 'next/link'
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  Bot,
  CircleDollarSign,
  Database,
  FileText,
  Filter,
  FlaskConical,
  GitBranch,
  KeyRound,
  Layers,
  Network,
  Scissors,
  Search,
  ShieldCheck,
  Sparkles,
  Workflow,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const capabilities = [
  {
    title: 'Unified ingestion',
    description:
      'Connect databases, warehouses and object stores through typed connectors, then trigger syncs on demand.',
    icon: Database,
  },
  {
    title: 'Knowledge bases',
    description:
      'Curate document collections with versioning and publish them for retrieval across your workspace.',
    icon: BookOpen,
  },
  {
    title: 'Hybrid search',
    description:
      'Query with semantic, vector or keyword retrieval, or combine them in a single hybrid search request.',
    icon: Search,
  },
  {
    title: 'Retrieval augmented generation',
    description:
      'Answer natural-language questions grounded in your published knowledge, with evaluation datasets to measure quality.',
    icon: Bot,
  },
  {
    title: 'Workflow orchestration',
    description:
      'Define repeatable data pipelines and execute them on schedule, tracking each run for audit.',
    icon: Workflow,
  },
  {
    title: 'Data lineage',
    description:
      'Follow each asset from source through transformation to the agents that consumed it.',
    icon: GitBranch,
  },
  {
    title: 'Governance & audit',
    description:
      'Policy-as-code with an approval queue and an immutable audit trail, scoped by role per workspace.',
    icon: ShieldCheck,
  },
  {
    title: 'Analytics',
    description:
      'Usage, quality and pipeline metrics surfaced in one place so regressions are visible before they compound.',
    icon: BarChart3,
  },
]

const architecture = [
  {
    step: '01',
    title: 'Connect',
    description:
      'Register data sources and credentials. Connectors validate reachability before any sync is scheduled.',
  },
  {
    step: '02',
    title: 'Ingest',
    description:
      'Run syncs to materialize datasets and documents, each tagged with the source that produced it.',
  },
  {
    step: '03',
    title: 'Curate',
    description:
      'Group assets into knowledge bases, validate schemas, and govern changes through approvals.',
  },
  {
    step: '04',
    title: 'Serve',
    description:
      'Expose data through search, RAG endpoints and API keys, with usage tracked against your plan.',
  },
]

const pages = [
  {
    title: 'Ingest data',
    description: 'Register sources, validate connectors and materialise datasets and documents.',
    items: [
      { title: 'Data sources', description: 'Connect databases and warehouses.', icon: Database, href: '/dashboard/sources' },
      { title: 'Connectors', description: 'Typed connectors for object stores and APIs.', icon: Network, href: '/dashboard/connectors' },
      { title: 'Datasets', description: 'Schema-validated tabular assets.', icon: FileText, href: '/dashboard/metadata' },
      { title: 'Documents', description: 'Uploaded files queued for indexing.', icon: FileText, href: '/dashboard/documents' },
    ],
  },
  {
    title: 'Curate knowledge',
    description: 'Extract, clean, chunk, embed and index documents, then retrieve over them.',
    items: [
      { title: 'Knowledge bases', description: 'Versioned, publishable collections.', icon: BookOpen, href: '/dashboard/knowledge' },
      { title: 'Search', description: 'Semantic, vector, keyword or hybrid.', icon: Search, href: '/dashboard/search' },
      { title: 'RAG query', description: 'Grounded answers with citations.', icon: Bot, href: '/dashboard/rag' },
    ],
  },
  {
    title: 'Automate & measure',
    description: 'Run pipelines on a schedule and check that answers stay correct.',
    items: [
      { title: 'Workflows', description: 'Scheduled pipelines with per-run audit.', icon: Workflow, href: '/dashboard/workflows' },
      { title: 'Lineage', description: 'Trace every asset to its consumers.', icon: GitBranch, href: '/dashboard/lineage' },
      { title: 'Evaluation', description: 'Score retrieval quality on your datasets.', icon: FlaskConical, href: '/dashboard/evaluation' },
      { title: 'Analytics', description: 'Usage, quality and pipeline metrics.', icon: BarChart3, href: '/dashboard/analytics' },
    ],
  },
  {
    title: 'Govern & administer',
    description: 'Policy-as-code, scoped keys and workspace administration.',
    items: [
      { title: 'Governance', description: 'Policies, roles and approvals.', icon: ShieldCheck, href: '/dashboard/governance' },
      { title: 'API keys', description: 'Read, write or admin scoped keys.', icon: KeyRound, href: '/dashboard/api-keys' },
      { title: 'Billing', description: 'Plan usage and invoices.', icon: CircleDollarSign, href: '/dashboard/billing' },
    ],
  },
]

const processing = [
  {
    step: '01',
    title: 'Extract',
    description:
      'Pull raw text out of PDFs, HTML and uploaded files, then normalise whitespace and encoding.',
    icon: FileText,
    href: '/dashboard/documents',
  },
  {
    step: '02',
    title: 'Clean',
    description:
      'Strip markup and boilerplate so downstream chunks carry signal rather than layout noise.',
    icon: Filter,
    href: '/dashboard/documents',
  },
  {
    step: '03',
    title: 'Chunk',
    description:
      'Split long text into overlapping token windows so a single answer never depends on one huge block.',
    icon: Scissors,
    href: '/dashboard/documents',
  },
  {
    step: '04',
    title: 'Embed',
    description:
      'Turn each chunk into a normalised vector, using your configured provider or the offline fallback.',
    icon: Sparkles,
    href: '/dashboard/knowledge',
  },
  {
    step: '05',
    title: 'Index',
    description:
      'Store chunks across the keyword, vector and graph indexes so hybrid retrieval can combine them.',
    icon: Layers,
    href: '/dashboard/search',
  },
]

const pricing = [
  {
    name: 'Free',
    price: '฿0',
    period: 'forever',
    description: 'Evaluate the platform with a single source.',
    features: ['1 data source', '1,000 API calls / month', 'Community support'],
    cta: 'Start free',
    highlight: false,
  },
  {
    name: 'Pro',
    price: '฿199',
    period: 'per month',
    description: 'For teams running production pipelines.',
    features: [
      'Unlimited data sources',
      '100,000 API calls / month',
      'Advanced governance',
      'Priority support',
    ],
    cta: 'Go Pro',
    highlight: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: 'annual',
    description: 'Custom terms for large organizations.',
    features: ['Custom retention', 'SSO & SCIM', 'Dedicated support', 'SLA'],
    cta: 'Contact sales',
    highlight: false,
  },
]

const faqs = [
  {
    q: 'How is authentication handled?',
    a: 'Sessions use HTTP-only cookies with CSRF protection. Access and refresh tokens never reach client-side JavaScript, and password hashes use bcrypt.',
  },
  {
    q: 'Can I run this locally?',
    a: 'Yes. The stack is defined in docker-compose.yml and brings up PostgreSQL, Redis, MinIO, Qdrant, Elasticsearch and the API together.',
  },
  {
    q: 'What separates DataAir from a plain warehouse?',
    a: 'DataAir covers the full lifecycle: ingestion, curation, governance, retrieval and evaluation, with lineage captured across all of it.',
  },
  {
    q: 'How are API keys scoped?',
    a: 'Keys carry read, write or admin scopes, are stored as HMAC digests, and can carry an expiry date. Usage is logged per request.',
  },
]

export function Hero() {
  return (
    <section className="border-b bg-gradient-to-b from-muted/50 to-background">
      <div className="container flex flex-col items-center gap-6 py-20 text-center sm:py-28">
        <Badge variant="secondary" className="gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-primary" />
          Enterprise data operating platform
        </Badge>
        <h1 className="max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
          The complete data lifecycle, from ingestion to AI agents
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          DataAir manages every stage of the data lifecycle — connect your sources, curate
          knowledge, govern changes, and serve results through search and AI agents.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button size="lg" asChild>
            <Link href="/register">
              Start building
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="#capabilities">Explore the platform</Link>
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          No credit card required &middot; Free plan available
        </p>
      </div>
    </section>
  )
}

export function PlatformSection() {
  return (
    <section id="platform" className="scroll-mt-16 border-b py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            One platform for the whole lifecycle
          </h2>
          <p className="mt-3 text-muted-foreground">
            Every capability below is backed by a working API — nothing here is a placeholder.
          </p>
        </div>
        <div id="capabilities" className="mt-12 grid scroll-mt-20 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {capabilities.map((item) => (
            <Card key={item.title} className="h-full">
              <CardHeader>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <item.icon className="h-5 w-5" />
                </div>
                <CardTitle className="pt-2 text-base">{item.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}

export function PagesSection() {
  return (
    <section id="pages" className="scroll-mt-16 border-b py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Explore the workspace
          </h2>
          <p className="mt-3 text-muted-foreground">
            Every page below maps to a screen you land in after signing in.
          </p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-2">
          {pages.map((group) => (
            <Card key={group.title} className="flex h-full flex-col">
              <CardHeader>
                <CardTitle>{group.title}</CardTitle>
                <CardDescription>{group.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <ul className="grid gap-2 sm:grid-cols-2">
                  {group.items.map((item) => (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className="group flex h-full items-start gap-3 rounded-lg border p-3 transition-colors hover:border-primary hover:bg-accent"
                      >
                        <item.icon className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                        <span className="min-w-0">
                          <span className="block text-sm font-medium">{item.title}</span>
                          <span className="block text-xs text-muted-foreground">
                            {item.description}
                          </span>
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}

export function ProcessingSection() {
  return (
    <section id="processing" className="scroll-mt-16 border-b bg-muted/30 py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            How data processing works
          </h2>
          <p className="mt-3 text-muted-foreground">
            Every document moves through the same five stages before it can be searched or cited.
          </p>
        </div>
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
          {processing.map((item) => (
            <Link
              key={item.step}
              href={item.href}
              className="group flex h-full flex-col rounded-lg border bg-background p-6 transition-colors hover:border-primary"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <item.icon className="h-4 w-4" />
                </div>
                <span className="text-sm font-semibold text-primary">{item.step}</span>
              </div>
              <h3 className="mt-3 font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{item.description}</p>
              <span className="mt-4 inline-flex items-center text-sm font-medium text-primary">
                Open
                <ArrowRight className="ml-1 h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
              </span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}

export function ArchitectureSection() {
  return (
    <section id="architecture" className="scroll-mt-16 border-b bg-muted/30 py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            How the platform fits together
          </h2>
          <p className="mt-3 text-muted-foreground">
            Four stages, each auditable, each independently usable.
          </p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {architecture.map((item) => (
            <div key={item.step} className="relative rounded-lg border bg-background p-6">
              <span className="text-sm font-semibold text-primary">{item.step}</span>
              <h3 className="mt-2 font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export function PricingSection() {
  return (
    <section id="pricing" className="scroll-mt-16 border-b py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Simple, predictable pricing
          </h2>
          <p className="mt-3 text-muted-foreground">
            Start free, upgrade when your pipelines need it.
          </p>
        </div>
        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          {pricing.map((tier) => (
            <Card
              key={tier.name}
              className={tier.highlight ? 'border-primary shadow-lg' : undefined}
            >
              <CardHeader>
                <CardTitle>{tier.name}</CardTitle>
                <CardDescription>{tier.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <span className="text-3xl font-bold">{tier.price}</span>
                  <span className="ml-1 text-sm text-muted-foreground">{tier.period}</span>
                </div>
                <ul className="space-y-2 text-sm">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Button
                  className="w-full"
                  variant={tier.highlight ? 'default' : 'outline'}
                  asChild
                >
                  <Link href="/register">{tier.cta}</Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}

export function FaqSection() {
  return (
    <section id="faq" className="scroll-mt-16 py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Frequently asked questions
          </h2>
        </div>
        <div className="mx-auto mt-12 max-w-3xl">
          <dl className="space-y-6">
            {faqs.map((faq) => (
              <div key={faq.q} className="rounded-lg border p-6">
                <dt className="font-semibold">{faq.q}</dt>
                <dd className="mt-2 text-sm text-muted-foreground">{faq.a}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  )
}

export function CtaSection() {
  return (
    <section className="border-t bg-primary text-primary-foreground">
      <div className="container flex flex-col items-center gap-4 py-16 text-center">
        <h2 className="text-3xl font-bold tracking-tight">
          Ready to run your data lifecycle end to end?
        </h2>
        <p className="max-w-xl text-primary-foreground/80">
          Create a workspace in minutes and connect your first source.
        </p>
        <Button size="lg" variant="secondary" asChild>
          <Link href="/register">
            Get started free
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </div>
    </section>
  )
}