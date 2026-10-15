'use client'

import { useEffect, useState } from 'react'
import { BarChart3, Users, Eye, UserPlus, Activity } from 'lucide-react'
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
} from 'recharts'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PageHeader } from '@/components/shared/async'

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

export default function AnalyticsPage() {
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
      <div className="container mx-auto py-8">
        <p>Loading analytics...</p>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="container mx-auto py-8">
        <p>No data available</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <PageHeader
        title="Website Analytics"
        description={`Traffic statistics for the last ${stats.period_days} days`}
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Visitors</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_visitors.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Page Views</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_page_views.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Subscribers</CardTitle>
            <UserPlus className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_subscribers.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Registered Users</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_users.toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Daily Visitors
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.daily_visitors}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="visitors" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top Pages</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.top_pages.slice(0, 8).map((page, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="truncate max-w-[70%] text-sm">{page.path}</div>
                  <div className="text-sm font-medium">{page.views.toLocaleString()}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Devices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.devices}
                    dataKey="count"
                    nameKey="device"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
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
      </div>
    </div>
  )
}
