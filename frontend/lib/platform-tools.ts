import type { ComponentType } from 'react'
import {
  Airplay,
  BookOpen,
  Boxes,
  Braces,
  Cloud,
  Code2,
  Database,
  FileCode2,
  GitBranch,
  Gauge,
  LayoutTemplate,
  MonitorPlay,
  Network,
  NotebookPen,
  Search,
  Server,
  ShieldCheck,
  Terminal,
  Workflow,
} from 'lucide-react'

export interface NavItem {
  title: string
  href: string
  icon: ComponentType<{ className?: string }>
  badge?: string
}

export interface NavGroup {
  label: string
  items: NavItem[]
}

export type ToolCategory =
  | 'Orchestration'
  | 'Data'
  | 'Search & Vector'
  | 'Object Storage'
  | 'Observability'
  | 'Catalog'
  | 'Developer'

export interface PlatformTool {
  id: string
  name: string
  description: string
  url: string
  category: ToolCategory
  icon: ComponentType<{ className?: string }>
  /** Health probe used by the tools page to report live status. */
  healthUrl?: string
  /** Ports the tool is published on, relative to the compose host. */
  ports: string[]
  notes?: string
}

export const platformTools: PlatformTool[] = [
  {
    id: 'airflow',
    name: 'Apache Airflow',
    description: 'Author, schedule and monitor data pipelines and dbt jobs.',
    url: 'http://localhost:8080',
    category: 'Orchestration',
    icon: Workflow,
    healthUrl: 'http://localhost:8080/health',
    ports: ['8080'],
    notes: 'Executors run locally; webserver, scheduler and triggerer are separate services.',
  },
  {
    id: 'flower',
    name: 'Flower',
    description: 'Live Celery task inspector with worker and queue statistics.',
    url: 'http://localhost:5555',
    category: 'Orchestration',
    icon: Airplay,
    ports: ['5555'],
    notes: 'Shares the worker image so it can introspect backend.app.workers.celery_app.',
  },
  {
    id: 'jupyter',
    name: 'JupyterLab',
    description: 'Notebook workspace for dbt, data quality checks and ad-hoc SQL.',
    url: 'http://localhost:8888',
    category: 'Developer',
    icon: NotebookPen,
    ports: ['8888'],
    notes: 'Toolbox image ships Python 3.11 with dbt, great-expectations and dbt-duckdb.',
  },
  {
    id: 'postgres',
    name: 'PostgreSQL',
    description: 'Primary warehouse and platform metadata store with pgvector.',
    url: 'http://localhost:5432',
    category: 'Data',
    icon: Database,
    healthUrl: 'http://localhost:8000/health',
    ports: ['5432'],
    notes: 'Databases: dataair, airflow, airflow_om, openmetadata_db.',
  },
  {
    id: 'redis',
    name: 'Redis',
    description: 'Cache, Celery broker and Airflow task result backend.',
    url: 'http://localhost:6379',
    category: 'Data',
    icon: Server,
    ports: ['6379'],
  },
  {
    id: 'elasticsearch',
    name: 'Elasticsearch',
    description: 'Full-text and hybrid keyword search over document chunks.',
    url: 'http://localhost:9200',
    category: 'Search & Vector',
    icon: Search,
    healthUrl: 'http://localhost:9200/_cluster/health',
    ports: ['9200'],
  },
  {
    id: 'qdrant',
    name: 'Qdrant',
    description: 'Vector store for chunk embeddings used by retrieval and RAG.',
    url: 'http://localhost:6333',
    category: 'Search & Vector',
    icon: Network,
    healthUrl: 'http://localhost:6333/healthz',
    ports: ['6333', '6334'],
  },
  {
    id: 'minio',
    name: 'MinIO',
    description: 'S3-compatible object storage for uploads and connector artifacts.',
    url: 'http://localhost:9001',
    category: 'Object Storage',
    icon: Boxes,
    healthUrl: 'http://localhost:9000/minio/health/live',
    ports: ['9000', '9001'],
    notes: 'Console on 9001, S3 API on 9000.',
  },
  {
    id: 'grafana',
    name: 'Grafana',
    description: 'Dashboards for platform and infrastructure metrics.',
    url: 'http://localhost:3001',
    category: 'Observability',
    icon: Gauge,
    healthUrl: 'http://localhost:3001/api/health',
    ports: ['3001'],
  },
  {
    id: 'prometheus',
    name: 'Prometheus',
    description: 'Metrics scraping, alerting rules and time-series queries.',
    url: 'http://localhost:9090',
    category: 'Observability',
    icon: MonitorPlay,
    healthUrl: 'http://localhost:9090/-/healthy',
    ports: ['9090'],
    notes: 'Scrapes the postgres and redis exporters alongside service endpoints.',
  },
  {
    id: 'openmetadata',
    name: 'OpenMetadata',
    description: 'Data catalog with lineage, glossary and ingestion workflows.',
    url: 'http://localhost:8585',
    category: 'Catalog',
    icon: GitBranch,
    healthUrl: 'http://localhost:8585/api/v1/system/version',
    ports: ['8585'],
    notes: 'Runs its own migrations plus an ingestion scheduler on the airflow_om database.',
  },
  {
    id: 'api',
    name: 'Platform API',
    description: 'FastAPI backend with OpenAPI docs at /docs.',
    url: 'http://localhost:8000/docs',
    category: 'Developer',
    icon: Terminal,
    healthUrl: 'http://localhost:8000/health',
    ports: ['8000'],
  },
]

export const toolCategories: ToolCategory[] = [
  'Orchestration',
  'Data',
  'Search & Vector',
  'Object Storage',
  'Observability',
  'Catalog',
  'Developer',
]

export interface StackEntry {
  name: string
  version: string
  role: string
  icon: ComponentType<{ className?: string }>
}

export interface LanguageEntry {
  name: string
  version: string
  use: string[]
  icon: ComponentType<{ className?: string }>
}

export interface PlatformStack {
  id: string
  label: string
  description: string
  icon: ComponentType<{ className?: string }>
  entries: StackEntry[]
}

export const platformStacks: PlatformStack[] = [
  {
    id: 'languages',
    label: 'Languages & Runtimes',
    description: 'Every language that ships in the toolbox or runs as a service.',
    icon: Code2,
    entries: [
      { name: 'Python', version: '3.11', role: 'Backend, Airflow DAGs, dbt, notebooks', icon: FileCode2 },
      { name: 'TypeScript', version: '5.6', role: 'Frontend (Next.js 14, React 18)', icon: Braces },
      { name: 'JavaScript', version: 'ES2022', role: 'Node 20 alpine runtime for the web tier', icon: Braces },
      { name: 'SQL', version: 'PostgreSQL 16', role: 'dbt models, warehouse migrations, seeds', icon: Database },
      { name: 'Java', version: '17', role: 'Elasticsearch, OpenMetadata, Qdrant runtimes', icon: Boxes },
      { name: 'Go', version: '1.21', role: 'Qdrant and Prometheus binaries', icon: Terminal },
      { name: 'Rust', version: '1.75', role: 'ripgrep utilities in the toolbox image', icon: Terminal },
      { name: 'Bash', version: '5.2', role: 'Entrypoints, init SQL drivers, CI scripts', icon: Terminal },
    ],
  },
  {
    id: 'backend',
    label: 'Backend',
    description: 'API framework, data access and background processing.',
    icon: Server,
    entries: [
      { name: 'FastAPI', version: '0.115', role: 'ASGI app, routers, OpenAPI', icon: Terminal },
      { name: 'Uvicorn', version: '0.32', role: 'ASGI server', icon: Server },
      { name: 'SQLAlchemy', version: '2.0', role: 'Async ORM and session management', icon: Database },
      { name: 'Pydantic', version: '2.10', role: 'Request and response schemas', icon: Braces },
      { name: 'Celery', version: '5.4', role: 'Task queue, beat scheduler, Flower UI', icon: Workflow },
      { name: 'PyJWT', version: '2.10', role: 'Access and refresh tokens', icon: ShieldCheck },
      { name: 'Passlib', version: '1.7', role: 'bcrypt password hashing', icon: ShieldCheck },
      { name: 'httpx', version: '0.28', role: 'Outbound HTTP clients', icon: Network },
    ],
  },
  {
    id: 'data',
    label: 'Data Engineering',
    description: 'Transformation, quality and pipeline tooling.',
    icon: Database,
    entries: [
      { name: 'Apache Airflow', version: '2.10.3', role: 'DAG orchestration', icon: Workflow },
      { name: 'dbt Core', version: '1.9.1', role: 'SQL transformation in an isolated venv', icon: GitBranch },
      { name: 'dbt Postgres', version: '1.9.1', role: 'Warehouse adapter', icon: Database },
      { name: 'dbt DuckDB', version: '1.9.1', role: 'Local analytics adapter', icon: Database },
      { name: 'Great Expectations', version: '0.18.15', role: 'Data quality suites', icon: FileCode2 },
      { name: 'pandas', version: '2.2', role: 'Dataframes in pipelines and checks', icon: FileCode2 },
      { name: 'NumPy', version: '1.26', role: 'Vector maths for similarity search', icon: FileCode2 },
    ],
  },
  {
    id: 'ai',
    label: 'AI & Retrieval',
    description: 'Models and libraries backing embeddings, search and RAG.',
    icon: BookOpen,
    entries: [
      { name: 'sentence-transformers', version: '3.3', role: 'Local embedding fallback', icon: Network },
      { name: 'OpenAI SDK', version: '1.59', role: 'Embeddings when an API key is set', icon: Cloud },
      { name: 'rank_bm25', version: '0.2.2', role: 'Keyword scoring', icon: Search },
      { name: 'pgvector', version: 'pg16', role: 'Vector similarity in Postgres', icon: Database },
      { name: 'Qdrant Client', version: '1.12', role: 'Vector collection access', icon: Network },
    ],
  },
  {
    id: 'frontend',
    label: 'Frontend',
    description: 'Design system and UI stack for the dashboard.',
    icon: LayoutTemplate,
    entries: [
      { name: 'Next.js', version: '14.2', role: 'App router, server components', icon: LayoutTemplate },
      { name: 'React', version: '18.3', role: 'Component runtime', icon: Braces },
      { name: 'Tailwind CSS', version: '3.4', role: 'Utility styling and design tokens', icon: LayoutTemplate },
      { name: 'shadcn/ui', version: 'New York', role: 'Component primitives on Radix', icon: LayoutTemplate },
      { name: 'Radix UI', version: '1.x', role: 'Accessible headless primitives', icon: LayoutTemplate },
      { name: 'React Query', version: '5.x', role: 'Server state and caching', icon: Cloud },
      { name: 'Jest', version: '29', role: 'Unit and component tests', icon: FileCode2 },
    ],
  },
  {
    id: 'platform',
    label: 'Platform',
    description: 'Storage, messaging and infrastructure services.',
    icon: Cloud,
    entries: [
      { name: 'PostgreSQL', version: '16 (pgvector)', role: 'Warehouse and metadata store', icon: Database },
      { name: 'Redis', version: '7.2', role: 'Cache and broker', icon: Server },
      { name: 'MinIO', version: '2025.7', role: 'S3-compatible object storage', icon: Boxes },
      { name: 'Elasticsearch', version: '8.17', role: 'Keyword and hybrid search', icon: Search },
      { name: 'Qdrant', version: '1.12', role: 'Vector database', icon: Network },
      { name: 'Prometheus', version: 'latest', role: 'Metrics and alerting', icon: MonitorPlay },
      { name: 'Grafana', version: 'latest', role: 'Dashboards', icon: Gauge },
      { name: 'OpenMetadata', version: '1.5.11', role: 'Catalog, lineage, ingestion', icon: GitBranch },
    ],
  },
]

/** Sidebar entries for the developer-facing tools only. */
export const toolsNavGroups: NavGroup[] = [
  {
    label: 'Tools',
    items: [
      { title: 'Tool Catalog', href: '/dashboard/tools', icon: LayoutTemplate },
      { title: 'Stacks', href: '/dashboard/stacks', icon: Code2 },
      { title: 'JupyterLab', href: 'http://localhost:8888', icon: NotebookPen, badge: 'external' },
      { title: 'Airflow', href: 'http://localhost:8080', icon: Workflow, badge: 'external' },
      { title: 'Flower', href: 'http://localhost:5555', icon: Airplay, badge: 'external' },
      { title: 'Grafana', href: 'http://localhost:3001', icon: Gauge, badge: 'external' },
      { title: 'Prometheus', href: 'http://localhost:9090', icon: MonitorPlay, badge: 'external' },
      { title: 'MinIO Console', href: 'http://localhost:9001', icon: Boxes, badge: 'external' },
      { title: 'OpenMetadata', href: 'http://localhost:8585', icon: GitBranch, badge: 'external' },
      { title: 'Qdrant', href: 'http://localhost:6333', icon: Network, badge: 'external' },
    ],
  },
]