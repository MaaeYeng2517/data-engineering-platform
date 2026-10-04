import type { ComponentType } from 'react'
import {
  Activity,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  Building2,
  CircleDollarSign,
  Cog,
  Database,
  FileText,
  FlaskConical,
  GitBranch,
  KeyRound,
  Layers,
  LayoutDashboard,
  MessageSquare,
  Network,
  Search,
  Settings,
  Shield,
  ShieldCheck,
  Users,
  Workflow,
  GitFork,
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

import { toolsNavGroups } from '@/lib/platform-tools'

export const navGroups: NavGroup[] = [
  {
    label: 'Overview',
    items: [
      { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { title: 'Activity', href: '/dashboard/activity', icon: Activity },
    ],
  },
  {
    label: 'Data',
    items: [
      { title: 'Data Sources', href: '/dashboard/sources', icon: Database },
      { title: 'Connectors', href: '/dashboard/connectors', icon: Network },
      { title: 'Datasets', href: '/dashboard/metadata', icon: FileText },
      { title: 'Documents', href: '/dashboard/documents', icon: FileText },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { title: 'Knowledge Bases', href: '/dashboard/knowledge', icon: BookOpen },
      { title: 'Search', href: '/dashboard/search', icon: Search },
      { title: 'RAG Query', href: '/dashboard/rag', icon: Bot },
      { title: 'Lineage', href: '/dashboard/lineage', icon: GitBranch },
    ],
  },
  {
    label: 'Orchestration',
    items: [
      { title: 'Workflows', href: '/dashboard/workflows', icon: Workflow },
      { title: 'Pipelines', href: '/dashboard/pipelines', icon: GitFork },
      { title: 'Evaluation', href: '/dashboard/evaluation', icon: FlaskConical },
      { title: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
    ],
  },
  {
    label: 'Governance',
    items: [
      { title: 'Governance', href: '/dashboard/governance', icon: ShieldCheck },
      { title: 'Approval Queue', href: '/dashboard/approvals', icon: Bell },
      { title: 'Audit Log', href: '/dashboard/audit', icon: Shield },
    ],
  },
  {
    label: 'Organization',
    items: [
      { title: 'Workspace', href: '/dashboard/tenants', icon: Building2 },
      { title: 'Work Groups', href: '/dashboard/work-groups', icon: Users },
      { title: 'Team Members', href: '/dashboard/team', icon: Users },
      { title: 'Billing', href: '/dashboard/billing', icon: CircleDollarSign },
      { title: 'API Keys', href: '/dashboard/api-keys', icon: KeyRound },
      { title: 'Service Profiles', href: '/dashboard/profiles', icon: Layers },
      { title: 'Support', href: '/dashboard/support', icon: MessageSquare },
      { title: 'Settings', href: '/dashboard/settings', icon: Settings },
      { title: 'Configuration', href: '/dashboard/configuration', icon: Cog },
    ],
  },
...toolsNavGroups,
]

export const navItems: NavItem[] = navGroups.flatMap((group) => group.items)

/** Pages reachable only by an admin. */
export const adminOnlyHrefs = new Set(['/dashboard/team', '/dashboard/audit'])