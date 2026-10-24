"use client"

import { ExternalLink } from "lucide-react"
import useSWR from "swr"

import { fetcher } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { PlatformLinks } from "@/types/platform"

export function SupersetLink() {
  const { data: links } = useSWR<PlatformLinks>("/platform/links", fetcher)

  if (!links?.superset) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ExternalLink className="h-5 w-5" />
          Apache Superset
        </CardTitle>
        <CardDescription>Data visualization &amp; business intelligence</CardDescription>
      </CardHeader>
      <CardContent>
        <Button asChild>
          <a href={links.superset} target="_blank" rel="noreferrer">
            Open Superset
          </a>
        </Button>
      </CardContent>
    </Card>
  )
}
