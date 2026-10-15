'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import {
  ArrowRight,
  Calendar,
  Clock,
  Code,
  Database,
  LayoutGrid,
  Sparkles,
  Tag,
  User,
} from 'lucide-react'

import { useBlogStore } from '@/lib/blog/store'
import { fetchBlogPosts } from '@/lib/api/blog'
import {
  useCategoryStore,
  getCategoryColorClass,
  type CategoryColor,
} from '@/lib/blog/categories'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CategoryManager } from '@/components/blog/category-manager'
import { cn } from '@/lib/utils'

type Post = {
  id: string
  title: string
  slug: string
  excerpt: string
  coverImage?: string | null
  tags: string[]
  author: string
  publishedAt: string | null
  createdAt: string
  readingTime?: number
}

const fallbackColors = [
  'blue',
  'violet',
  'amber',
  'emerald',
  'cyan',
  'rose',
  'indigo',
  'teal',
  'fuchsia',
  'orange',
]

function getTagColorClass(tag: string): string {
  const key = tag.toLowerCase()
  const categorySlugMap: Record<string, string> = {
    technology: 'blue',
    'data-engineering': 'violet',
    'ai-ml': 'amber',
    tutorial: 'emerald',
    architecture: 'cyan',
    governance: 'rose',
    dataops: 'indigo',
    analytics: 'teal',
    streaming: 'fuchsia',
    'open-source': 'orange',
  }
  const colorKey = categorySlugMap[key] || fallbackColors[Math.abs(Array.from(key).reduce((a, c) => (a * 31 + c.charCodeAt(0)) | 0, 0)) % fallbackColors.length]
  return getCategoryColorClass(colorKey as CategoryColor)
}

const tagIcons: Record<string, React.ElementType> = {
  technology: Code,
  'data-engineering': Database,
  'ai-ml': Sparkles,
  tutorial: LayoutGrid,
  architecture: Tag,
  governance: Tag,
  analytics: Database,
  streaming: Database,
  dataops: Database,
  'open-source': Code,
}

function TagIcon({ tag }: { tag: string }): React.ReactElement {
  const Icon = tagIcons[tag.toLowerCase()] || Code
  return <Icon className="h-4 w-4" />
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function HeroSection() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-accent/10" aria-hidden="true" />
      <div
        className="absolute inset-0 opacity-[0.03]"
        aria-hidden="true"
        style={{
          backgroundImage:
            'radial-gradient(circle at 1px 1px, currentColor, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />
      <div className="absolute top-20 right-0 -z-10 h-96 w-96 -translate-y-1/2 translate-x-1/3 rounded-full blur-3xl" />
      <div className="container relative flex flex-col items-center gap-8 py-20 text-center sm:py-32">
        <Badge
          variant="outline"
          className="gap-2 border-primary/30 bg-primary/5 text-xs font-mono font-medium text-primary"
        >
          <Code className="h-3 w-3" />
          Data & AI engineering knowledge hub
        </Badge>

        <div className="space-y-6">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
            <span className="bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-transparent">
              Data & AI Engineering
            </span>
            <br />
            <span className="text-primary">Knowledge Hub</span>
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
            Articles, tutorials and deep-dives on data platforms, vector search,
            RAG pipelines, orchestration and the tools that power modern data
            infrastructure.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Button size="lg" asChild>
            <Link href="#articles">
              Browse articles
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/chat">Ask the AI agent</Link>
          </Button>
        </div>
      </div>
    </section>
  )
}

function FeaturedArticle({ post }: { post: Post }) {
  const primaryTag = post.tags[0] || 'technology'
  const tagClass = getTagColorClass(primaryTag)
  const Icon = tagIcons[primaryTag.toLowerCase()] || Code

  return (
    <section className="border-b py-16" id="articles">
      <div className="container flex justify-center">
        <Card className="group relative w-full max-w-4xl overflow-hidden border-2 border-border/50 shadow-2xl transition-all duration-300 hover:border-primary/30 hover:shadow-primary/5">
          {post.coverImage ? (
            <div className="relative aspect-[21/9] w-full overflow-hidden">
              <img
                src={post.coverImage}
                alt={post.title}
                className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background/60 to-transparent" />
            </div>
          ) : (
            <div className="relative flex h-48 w-full items-center justify-center border-b border-border bg-muted/30 font-mono text-xs text-muted-foreground sm:h-60">
              <Code className="h-10 w-10 text-muted-foreground/40" />
              <span className="mt-2 block">cover image</span>
            </div>
          )}

          <Badge
            variant="secondary"
            className="absolute left-6 top-4 gap-1.5 border-yellow-500/30 bg-yellow-500/10 font-mono text-xs font-medium text-yellow-600"
          >
            <Sparkles className="h-3 w-3" />
            Featured article
          </Badge>

          <div className="absolute right-6 top-4">
            <div
              className={cn(
                'flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium',
                tagClass,
              )}
            >
              <TagIcon tag={primaryTag} />
              {primaryTag}
            </div>
          </div>

          <CardHeader className="pb-3">
            <CardTitle className="line-clamp-2 text-3xl font-bold sm:text-4xl">
              {post.title}
            </CardTitle>
            <CardDescription className="mt-2 line-clamp-3 text-base">
              {post.excerpt}
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1.5 font-mono">
                <User className="h-4 w-4" />
                <span>{post.author}</span>
              </div>
              <div className="flex items-center gap-1.5 font-mono">
                <Calendar className="h-4 w-4" />
                <span>
                  {formatDate(post.publishedAt) || formatDate(post.createdAt)}
                </span>
              </div>
              {post.readingTime && (
                <div className="flex items-center gap-1.5 font-mono">
                  <Clock className="h-4 w-4" />
                  <span>{post.readingTime} min read</span>
                </div>
              )}
            </div>
          </CardContent>

          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary/20 via-primary/40 to-primary/20 opacity-0 transition-opacity group-hover:opacity-100" />
        </Card>
      </div>
    </section>
  )
}

function CategoryNav({
  categories,
  selected,
  onSelect,
}: {
  categories: string[]
  selected: string | null
  onSelect: (cat: string | null) => void
}) {
  const pills = [
    { name: 'All', slug: null, color: 'border-primary/30 bg-primary/10 text-primary' },
    ...categories.map((c) => ({ name: c, slug: c, color: getTagColorClass(c) })),
  ]

  return (
    <section className="border-b py-12" id="categories">
      <div className="container text-center">
        <h2 className="mb-2 text-2xl font-bold">Browse by category</h2>
        <p className="mb-8 text-sm text-muted-foreground">
          Filter articles by topic — each category is a deep-dive stream
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          {pills.map((cat) => {
            const active = selected === cat.slug
            return (
              <button
                key={cat.slug ?? '__all__'}
                type="button"
                onClick={() => onSelect(cat.slug)}
                className={cn(
                  'rounded-full border px-5 py-2 text-sm font-medium font-mono transition-all duration-200',
                  cat.color,
                  active
                    ? 'ring-2 ring-primary ring-offset-2 ring-offset-background'
                    : 'hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/10',
                )}
              >
                {cat.name}
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}

function ArticleCard({ post }: { post: Post }) {
  const tagClass = post.tags[0] ? getTagColorClass(post.tags[0]) : ''

  return (
    <Card
      className={cn(
        'group h-full overflow-hidden border-border/50 transition-all duration-300',
        'hover:border-primary/30 hover:shadow-xl hover:shadow-primary/5',
      )}
    >
      <Link href={`/blog/${post.slug}`} className="block">
        <CardHeader className="space-y-3 pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              {post.tags.length > 0 && (
                <Badge
                  variant="outline"
                  className={cn('border-transparent font-mono text-xs', tagClass)}
                >
                  {post.tags[0]}
                </Badge>
              )}
            </div>
            <div className="flex items-center text-xs text-muted-foreground font-mono">
              <Clock className="mr-1 h-3 w-3" />
              {post.readingTime} min
            </div>
          </div>
          <CardTitle className="line-clamp-2 text-lg transition-colors group-hover:text-primary">
            {post.title}
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-4">
          <CardDescription className="line-clamp-3 text-sm">
            {post.excerpt}
          </CardDescription>
          <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted-foreground font-mono">
            <div className="flex items-center gap-1">
              <User className="h-3 w-3" />
              <span>{post.author}</span>
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>
                {formatDate(post.publishedAt) || formatDate(post.createdAt)}
              </span>
            </div>
          </div>
        </CardContent>
      </Link>
    </Card>
  )
}

function ArticleGrid({ posts, categoryName }: { posts: Post[]; categoryName?: string }) {
  if (posts.length === 0) {
    return (
      <p className="text-center text-muted-foreground">
        ไม่มีบทความในหมวดหมู่นี้
      </p>
    )
  }

  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {posts.map((post) => (
        <ArticleCard key={post.id} post={post} />
      ))}
    </div>
  )
}

function CategorySection({ category, posts }: { category: string; posts: Post[] }) {
  const tagClass = getTagColorClass(category)
  const Icon = tagIcons[category.toLowerCase()] || Code

  return (
    <section className="border-b border-border/30 py-14 last:border-0">
      <div className="container">
        <div className="mb-8 flex items-center gap-3">
          <div
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-lg',
              tagClass,
            )}
          >
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              Category
            </h3>
            <h4 className="text-2xl font-bold">{category}</h4>
          </div>
          <div className="ml-auto rounded-full border border-border px-2.5 py-0.5 text-xs font-mono text-muted-foreground">
            {posts.length} article{posts.length !== 1 ? 's' : ''}
          </div>
        </div>

        <ArticleGrid posts={posts} />
      </div>
    </section>
  )
}

const techStack = [
  { name: 'Apache Airflow', icon: Database },
  { name: 'dbt', icon: Database },
  { name: 'FastAPI', icon: Code },
  { name: 'PostgreSQL', icon: Database },
  { name: 'Redis', icon: Database },
  { name: 'Elasticsearch', icon: Database },
  { name: 'Qdrant', icon: Database },
  { name: 'MinIO', icon: Database },
  { name: 'OpenMetadata', icon: Database },
  { name: 'React', icon: Code },
  { name: 'Next.js', icon: Code },
  { name: 'Tailwind CSS', icon: Code },
]

function TechStack() {
  return (
    <section className="border-b bg-muted/30 py-12" id="tech-stack">
      <div className="container">
        <div className="mb-8 text-center">
          <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            Built with
          </h3>
          <h4 className="mt-2 text-2xl font-bold">Technology stack</h4>
          <p className="mt-2 text-sm text-muted-foreground">
            Modern open-source tools powering the DataAir platform
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-6">
          {techStack.map((tech) => {
            const Icon = tech.icon
            return (
              <div
                key={tech.name}
                className="flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2.5 text-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
              >
                <Icon className="h-4 w-4 text-primary" />
                <span className="font-medium">{tech.name}</span>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

function EmptyState() {
  return (
    <section className="border-b py-16">
      <div className="container text-center">
        <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-muted/30">
          <Code className="h-8 w-8 text-muted-foreground/50" />
        </div>
        <h3 className="mt-6 text-2xl font-bold">No articles yet</h3>
        <p className="mt-3 text-muted-foreground">
          Articles will appear here once they are published. Check back soon or
          sign in to start writing.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Button asChild>
            <Link href="/register">Create a workspace</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/documents">Read the docs</Link>
          </Button>
        </div>
      </div>
    </section>
  )
}

function HomeCta() {
  return (
    <section className="border-t bg-primary/5 py-16">
      <div className="container flex flex-col items-center gap-4 text-center">
        <h3 className="text-2xl font-bold">Ready to build with data & AI?</h3>
        <p className="max-w-xl text-sm text-muted-foreground">
          Start your free workspace, connect your first source, and deploy your
          first RAG pipeline in minutes.
        </p>
        <div className="flex gap-3">
          <Button size="lg" asChild>
            <Link href="/register">
              Get started free
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/blog">View all articles</Link>
          </Button>
        </div>
      </div>
    </section>
  )
}

export function BlogHomePage() {
  const { list, hydrated: localHydrated } = useBlogStore()
  const { list: listCategories, hydrated: catHydrated } = useCategoryStore()

  const [remotePosts, setRemotePosts] = useState<(Post & { _source: 'remote' | 'local' })[]>([])
  const [remoteTried, setRemoteTried] = useState(false)

  useEffect(() => {
    fetchBlogPosts()
      .then((posts) => {
        setRemotePosts(
          posts.map((p) => ({
            id: p.id,
            title: p.title,
            slug: p.slug,
            excerpt: p.excerpt,
            coverImage: p.coverImage,
            tags: p.tags,
            author: p.author,
            publishedAt: p.publishedAt,
            createdAt: p.createdAt,
            readingTime: p.readingTime,
            _source: 'remote' as const,
          })),
        )
      })
      .catch(() => setRemotePosts([]))
      .finally(() => setRemoteTried(true))
  }, [])

  const posts: Post[] = useMemo(() => {
    const localRaw = localHydrated ? list(true) : []
    const localPosts: (Post & { _source: 'local' })[] = localRaw.map((p) => ({
      id: p.id,
      title: p.title,
      slug: p.slug,
      excerpt: p.excerpt,
      coverImage: p.coverImage,
      tags: p.tags,
      author: p.author,
      publishedAt: p.publishedAt,
      createdAt: p.createdAt,
      readingTime: p.readingTime,
      _source: 'local',
    }))

    if (remotePosts.length > 0) {
      const remoteSlugs = new Set(remotePosts.map((p) => p.slug))
      const localOnly = localPosts.filter((p) => !remoteSlugs.has(p.slug))
      const merged = [...remotePosts, ...localOnly]
      const seen = new Set<string>()
      const deduped = merged.filter((p) => {
        if (seen.has(p.slug)) return false
        seen.add(p.slug)
        return true
      })
      return [...deduped].sort((a, b) => {
        const ta = a.publishedAt ? new Date(a.publishedAt).getTime() : new Date(a.createdAt).getTime()
        const tb = b.publishedAt ? new Date(b.publishedAt).getTime() : new Date(b.createdAt).getTime()
        return tb - ta
      }).map(({ _source: _, ...rest }) => rest)
    }

    return localPosts.map(({ _source: _, ...rest }) => rest)
  }, [remotePosts, list, localHydrated])

  const hydrated = localHydrated && remoteTried

  const [selectedTag, setSelectedTag] = useState<string | null>(null)

  const categories: string[] = useMemo(() => {
    const managed = catHydrated ? listCategories().map((c) => c.name) : []
    const tagSet = new Set<string>()
    posts.forEach((p) => p.tags.forEach((t) => tagSet.add(t)))
    const all = Array.from(new Set([...managed, ...tagSet])).sort()
    return all
  }, [posts, listCategories, catHydrated])

  const featuredPost = posts[0]
  const remainingPosts = posts.slice(1)

  const filteredPosts = useMemo(
    () =>
      selectedTag
        ? remainingPosts.filter((p) => p.tags.includes(selectedTag))
        : remainingPosts,
    [remainingPosts, selectedTag],
  )

  const groupedPosts = useMemo(() => {
    const map = new Map<string, Post[]>()
    filteredPosts.forEach((post) => {
      const primary = selectedTag || post.tags[0] || 'Uncategorized'
      if (!map.has(primary)) map.set(primary, [])
      map.get(primary)!.push(post)
    })
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b))
  }, [filteredPosts, selectedTag])

  return (
    <div className="min-h-screen">
      <HeroSection />

      {!hydrated ? (
        <div className="container py-16">
          <div className="mx-auto max-w-4xl space-y-4">
            <div className="h-10 w-3/4 animate-pulse rounded bg-muted" />
            <div className="h-6 w-1/2 animate-pulse rounded bg-muted" />
            <div className="h-6 w-5/6 animate-pulse rounded bg-muted" />
          </div>
        </div>
      ) : posts.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          <FeaturedArticle post={featuredPost} />

          <CategoryNav
            categories={categories}
            selected={selectedTag}
            onSelect={setSelectedTag}
          />

          {groupedPosts.length === 0 ? (
            <div className="border-b py-14">
              <div className="container">
                <p className="text-center text-muted-foreground">
                  ไม่มีบทความในหมวดหมู่นี้
                </p>
              </div>
            </div>
          ) : (
            groupedPosts.map(([cat, catPosts]) => (
              <CategorySection key={cat} category={cat} posts={catPosts} />
            ))
          )}

          <TechStack />
          <CategoryManager />
          <HomeCta />
        </>
      )}
    </div>
  )
}
