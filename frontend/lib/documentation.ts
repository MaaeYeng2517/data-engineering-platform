import type { ComponentType } from 'react'
import {
  ArrowRightCircle,
  Database,
  GitBranch,
  KeyRound,
  Layers,
  ListChecks,
  Search,
  ShieldCheck,
  Upload,
  Workflow,
} from 'lucide-react'

export interface GuideStep {
  title: string
  detail: string
}

export interface GuideTopic {
  id: string
  label: string
  icon: ComponentType<{ className?: string }>
  summary: string
  steps: GuideStep[]
  notes?: string[]
}

/** Usage guide rendered inside the Documents page. */
export const documentGuide: GuideTopic[] = [
  {
    id: 'lifecycle',
    label: 'Document lifecycle',
    icon: ListChecks,
    summary:
      'Every file moves through ingest, process, chunk, embed and index. Status in the table above reflects where a document currently sits.',
    steps: [
      {
        title: 'Upload or connect',
        detail:
          'Upload a file from this page, or point a connector at an external source so new files arrive automatically.',
      },
      {
        title: 'Extract and clean',
        detail:
          'Text is pulled out of the source format, stripped of boilerplate and normalised to lowercase.',
      },
      {
        title: 'Chunk',
        detail:
          'The text is split into overlapping token windows (300 tokens with 50 overlap) so a retrieval hit keeps its surrounding context.',
      },
      {
        title: 'Embed',
        detail:
          'Each chunk becomes a normalised vector. With an OpenAI key configured the embeddings API is used, otherwise a deterministic hashed projection keeps local runs reproducible.',
      },
      {
        title: 'Index and publish',
        detail:
          'Chunks land in the keyword index, the vector index and the metadata index. Publishing makes a document visible to Search and RAG queries.',
      },
    ],
    notes: [
      'Chunk ids are derived from the document id and chunk index, so re-indexing the same file keeps vector ids stable.',
      'Draft documents stay searchable by admins but are excluded for other members until published.',
    ],
  },
  {
    id: 'knowledge-bases',
    label: 'Knowledge bases',
    icon: Layers,
    summary:
      'A knowledge base is the container that groups documents, metadata schemas, workflows and evaluation runs. Everything is scoped to the workspace it belongs to.',
    steps: [
      {
        title: 'Create the knowledge base',
        detail: 'Name it and pick a slug; the slug appears in API paths and cannot be reused.',
      },
      {
        title: 'Attach documents',
        detail: 'Each document belongs to exactly one knowledge base and carries its own version string.',
      },
      {
        title: 'Declare metadata',
        detail:
          'Metadata schemas define which fields you can filter on during search and which taxonomy the graph builder uses.',
      },
      {
        title: 'Evaluate before publishing',
        detail:
          'Run an evaluation set against the knowledge base to check retrieval quality, then publish when scores look acceptable.',
      },
    ],
    notes: [
      'Use the filter above to scope this table to a single knowledge base.',
      'Deleting a knowledge base removes its documents and chunks; archive it instead if you need history.',
    ],
  },
  {
    id: 'sources',
    label: 'Sources & connectors',
    icon: Database,
    summary:
      'Sources describe where documents come from. Connectors know how to talk to that system and keep it in sync.',
    steps: [
      {
        title: 'Register the source',
        detail: 'Add a source with its type and connection config inside a knowledge base.',
      },
      {
        title: 'Choose a connector',
        detail:
          'Each connector type knows its authentication style and the schedule it supports.',
      },
      {
        title: 'Sync',
        detail:
          'A sync pulls new or changed files and creates or updates documents. The source records the sync status and last run.',
      },
    ],
    notes: [
      'Credentials belong in the connector config, never in a document.',
      'A failed sync leaves existing documents untouched; only new content is added.',
    ],
  },
  {
    id: 'search-rag',
    label: 'Search & RAG',
    icon: Search,
    summary:
      'Search blends a keyword score with a vector similarity score. RAG takes the top results and asks the language model to answer from them.',
    steps: [
      {
        title: 'Query',
        detail: 'Send a question plus the knowledge base ids you want searched.',
      },
      {
        title: 'Retrieve',
        detail:
          'Keyword hits contribute 40% and vector similarity 60% to the hybrid score, then results are filtered by metadata if provided.',
      },
      {
        title: 'Generate',
        detail:
          'The top chunks are handed to the model together with citations, and the answer returns with its sources and token usage.',
      },
    ],
    notes: [
      'Raise the score threshold when you need fewer but more precise sources.',
      'RAG answers only from retrieved chunks; anything outside them should be treated as unsupported.',
    ],
  },
  {
    id: 'workflows',
    label: 'Workflows & pipelines',
    icon: Workflow,
    summary:
      'Workflows describe the graph that runs over a knowledge base; pipelines are the scheduled executions of those graphs.',
    steps: [
      {
        title: 'Design the graph',
        detail: 'Add nodes for extraction, enrichment, chunking and publishing, then wire them with edges.',
      },
      {
        title: 'Version and activate',
        detail: 'Each save bumps the version so you can compare runs.',
      },
      {
        title: 'Schedule',
        detail:
          'Airflow owns the schedule; the Celery worker executes the steps and Flower shows live progress.',
      },
    ],
    notes: [
      'Long steps run in the worker, not in the API request, so a failing run can be retried safely.',
      'dbt models under /opt/airflow/dbt transform warehouse tables and are run by the same Airflow cluster.',
    ],
  },
  {
    id: 'governance',
    label: 'Governance',
    icon: ShieldCheck,
    summary:
      'Roles, approvals and an audit trail wrap everything above so changes stay reviewable.',
    steps: [
      {
        title: 'Assign roles',
        detail: 'Guests read, members create and publish, admins manage the workspace.',
      },
      {
        title: 'Review changes',
        detail: 'Publishing a document or changing metadata can be routed through the approval queue.',
      },
      {
        title: 'Audit',
        detail: 'Every privileged action is recorded with actor, target and timestamp.',
      },
    ],
    notes: [
      'API key and billing access require the admin role.',
      'Audit entries are append-only; they cannot be edited from the UI.',
    ],
  },
  {
    id: 'api-keys',
    label: 'API keys & billing',
    icon: KeyRound,
    summary:
      'Machine access uses API keys scoped per user, and usage counts against the plan attached to the workspace.',
    steps: [
      {
        title: 'Create a key',
        detail: 'Issue a key with the scopes you need; the full secret is shown once and only a prefix is stored.',
      },
      {
        title: 'Send it',
        detail: 'Pass the key in the x-api-key header; requests are authenticated without a session cookie.',
      },
      {
        title: 'Watch usage',
        detail: 'Each call is logged with endpoint, latency and status, and counted against the monthly allowance.',
      },
      {
        title: 'Revoke',
        detail: 'Revoking disables the key immediately; the usage history is kept.',
      },
    ],
    notes: [
      'Browser sessions use httpOnly cookies plus a CSRF token, so scripts must send the CSRF header explicitly.',
      'Plans cap monthly API calls; the entitlements endpoint reports the current limit and features.',
    ],
  },
  {
    id: 'lineage',
    label: 'Metadata & lineage',
    icon: GitBranch,
    summary:
      'Entities and relationships extracted from documents form a knowledge graph that backs the Lineage view.',
    steps: [
      {
        title: 'Extract entities',
        detail: 'Named entities are detected per chunk and stored against the document.',
      },
      {
        title: 'Link relations',
        detail: 'Relationships connect entities with a predicate and a weight.',
      },
      {
        title: 'Trace impact',
        detail: 'Lineage walks the graph to show which documents and fields depend on each other.',
      },
    ],
  },
]

export interface DocumentStatusInfo {
  status: string
  label: string
  description: string
  tone: 'default' | 'secondary' | 'outline' | 'destructive'
}

/** Explains the status values shown in the documents table. */
export const documentStatuses: DocumentStatusInfo[] = [
  {
    status: 'pending',
    label: 'Pending',
    description: 'Queued for extraction; nothing has been indexed yet.',
    tone: 'secondary',
  },
  {
    status: 'processing',
    label: 'Processing',
    description: 'Being chunked and embedded right now.',
    tone: 'secondary',
  },
  {
    status: 'indexed',
    label: 'Indexed',
    description: 'Chunks are searchable, but the document is still a draft.',
    tone: 'default',
  },
  {
    status: 'failed',
    label: 'Failed',
    description: 'Ingestion or indexing errored; check the worker logs and retry.',
    tone: 'destructive',
  },
  {
    status: 'published',
    label: 'Published',
    description: 'Visible to every member of the workspace in Search and RAG.',
    tone: 'default',
  },
]

export const guideFlow: string[] = [
  'Upload',
  'Extract',
  'Chunk',
  'Embed',
  'Index',
  'Publish',
]

export const guideFlowIcon = ArrowRightCircle