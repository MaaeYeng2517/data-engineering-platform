'use client'

import { useEffect, useState } from 'react'
import { BarChart3, Users, Eye, UserPlus, Activity, Globe, Monitor, MousePointerClick } from 'lucide-react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316']

interface WebsiteStats {
  period_days: number
  total_visitors: number
  total_page_views: number
  total_subscribers: number
  total_users: number
  daily_visitors: Array<{ date: string; visitors: number }>
  daily_page_views: Array<{ date: string; page_views: number }>
  daily_subscribers: Array<{ date: string; subscribers: number }>
  top_pages: Array<{ path: string; views: number }>
  referrers: Array<{ referrer: string; count: number }>
  devices: Array<{ device: string; count: number }>
  browsers: Array<{ browser: string; count: number }>
  countries: Array<{ country: string; count: number }>
  events_by_type: Array<{ event_type: string; count: number }>
  section_usage: Array<{ section: string; count: number }>
}

export default function SiteAnalyticsPage() {
  const [stats, setStats] = useState<WebsiteStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true)
        const res = await fetch('http://localhost:8000/api/v1/analytics/website-stats?days=30')
        if (res.ok) {
          const data = await res.json()
          setStats(data)
        }
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="container mx-auto py-12">
          <div className="text-center">Loading website analytics...</div>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="container mx-auto py-12">
          <div className="text-center">No analytics data available yet</div>
        </div>
      </div>
    )
  }

  const chartData = stats.daily_visitors.map((v, i) => ({
    date: v.date,
    visitors: v.visitors,
    pageViews: stats.daily_page_views[i]?.page_views || 0,
    subscribers: stats.daily_subscribers[i]?.subscribers || 0,
  }))

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="container mx-auto py-8 space-y-8">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">Website Statistics</h1>
          <p className="text-muted-foreground">Comprehensive site traffic and user engagement analytics</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Visitors</CardTitle>
              <Users className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_visitors.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Last {stats.period_days} days</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-green-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Page Views</CardTitle>
              <Eye className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_page_views.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Total views</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-orange-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Subscribers</CardTitle>
              <UserPlus className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_subscribers.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Newsletter subscribers</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-purple-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Registered Users</CardTitle>
              <Activity className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_users.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Platform users</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Traffic Overview (Last 30 Days)
            </CardTitle>
            <CardDescription>Daily visitors, page views, and subscriber growth</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Area yAxisId="left" type="monotone" dataKey="visitors" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} name="Visitors" />
                  <Area yAxisId="left" type="monotone" dataKey="pageViews" stroke="#10b981" fill="#10b981" fillOpacity={0.2} name="Page Views" />
                  <Line yAxisId="right" type="monotone" dataKey="subscribers" stroke="#f59e0b" name="Subscribers" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="pages" className="space-y-4">
          <TabsList>
            <TabsTrigger value="pages">Top Pages</TabsTrigger>
            <TabsTrigger value="devices">Devices</TabsTrigger>
            <TabsTrigger value="browsers">Browsers</TabsTrigger>
            <TabsTrigger value="sections">Section Usage</TabsTrigger>
          </TabsList>

          <TabsContent value="pages" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MousePointerClick className="h-4 w-4" />
                  Most Visited Pages
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {stats.top_pages.map((page, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-sm font-medium">
                          {idx + 1}
                        </div>
                        <div className="truncate max-w-[500px] text-sm">{page.path}</div>
                      </div>
                      <div className="text-sm font-medium">{page.views.toLocaleString()} views</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="devices" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Monitor className="h-4 w-4" />
                    Device Distribution
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={stats.devices}
                          dataKey="count"
                          nameKey="device"
                          cx="50%"
                          cy="50%"
                          outerRadius={100}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        >
                          {stats.devices.map((entry, idx) => (
                            <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {stats.devices.map((device, idx) => (
                      <div key={idx} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="h-3 w-3 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                          <span className="text-sm">{device.device || 'Unknown'}</span>
                        </div>
                        <span className="text-sm font-medium">{device.count.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="browsers" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Browser Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stats.browsers} layout="horizontal">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="browser" type="category" width={80} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sections" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Section Engagement</CardTitle>
                <CardDescription>Usage across different sections of the platform</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stats.section_usage}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="section" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#10b981" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
