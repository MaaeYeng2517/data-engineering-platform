"use client"

import { ExternalLink, Shield, FileText, Users, Lock } from "lucide-react"
import useSWR from "swr"

import { fetcher } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { PlatformLinks } from "@/types/platform"

export default function GovernancePage() {
  const { data: links } = useSWR<PlatformLinks>("/platform/links", fetcher)

  const tools = [
    {
      name: "Apache Ranger",
      description: "Centralized security administration, fine-grained access control, and data governance",
      icon: Shield,
      url: links?.ranger,
      features: ["Row/Column Level Security", "Data Masking", "Audit Logging", "Policy Management"],
      status: "Available",
    },
    {
      name: "OpenMetadata",
      description: "Data discovery, cataloging, lineage, and governance",
      icon: FileText,
      url: links?.openmetadata,
      features: ["Data Catalog", "Lineage Tracking", "Glossary", "Data Ownership"],
      status: "Available",
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Data Governance</h1>
        <p className="text-muted-foreground">
          Data security, access control, compliance, and governance tools
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {tools.map((tool) => (
          <Card key={tool.name} className="flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <tool.icon className="h-6 w-6 text-primary" />
                  <CardTitle>{tool.name}</CardTitle>
                </div>
                <Badge variant="default">{tool.status}</Badge>
              </div>
              <CardDescription>{tool.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 space-y-4">
              <div>
                <p className="text-sm font-medium mb-2">Key Features</p>
                <div className="flex flex-wrap gap-2">
                  {tool.features.map((feature) => (
                    <Badge key={feature} variant="secondary">
                      {feature}
                    </Badge>
                  ))}
                </div>
              </div>
              <Button asChild disabled={!tool.url} className="w-full">
                <a href={tool.url} target="_blank" rel="noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Open {tool.name}
                </a>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
