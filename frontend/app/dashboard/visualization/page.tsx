"use client"

import { ExternalLink, BarChart3, PieChart, LineChart, Activity } from "lucide-react"
import useSWR from "swr"

import { fetcher } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { PlatformLinks } from "@/types/platform"

export default function VisualizationPage() {
  const { data: links } = useSWR<PlatformLinks>("/platform/links", fetcher)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Data Visualization</h1>
        <p className="text-muted-foreground">
          Interactive dashboards and business intelligence tools
        </p>
      </div>

      <Card className="border-primary/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-6 w-6 text-primary" />
              <CardTitle>Apache Superset</CardTitle>
            </div>
            <Badge variant="default">Primary BI Tool</Badge>
          </div>
          <CardDescription>
            Modern, enterprise-ready business intelligence web application
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="flex flex-col items-center gap-2 p-4 border rounded-lg">
              <BarChart3 className="h-8 w-8 text-primary" />
              <p className="text-sm font-medium">Charts</p>
            </div>
            <div className="flex flex-col items-center gap-2 p-4 border rounded-lg">
              <PieChart className="h-8 w-8 text-primary" />
              <p className="text-sm font-medium">Dashboards</p>
            </div>
            <div className="flex flex-col items-center gap-2 p-4 border rounded-lg">
              <LineChart className="h-8 w-8 text-primary" />
              <p className="text-sm font-medium">Time Series</p>
            </div>
            <div className="flex flex-col items-center gap-2 p-4 border rounded-lg">
              <Activity className="h-8 w-8 text-primary" />
              <p className="text-sm font-medium">SQL Lab</p>
            </div>
          </div>
          <Button asChild disabled={!links?.superset} size="lg" className="w-full md:w-auto">
            <a href={links?.superset} target="_blank" rel="noreferrer">
              <ExternalLink className="mr-2 h-4 w-4" />
              Open Apache Superset
            </a>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
