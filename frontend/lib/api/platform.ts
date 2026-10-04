import { api } from '@/lib/api/client'
import type {
  CatalogSearchResult,
  CatalogTable,
  Dag,
  DagRun,
  EltRun,
  MonitoringSample,
  PlatformHealth,
  PlatformLinks,
  QualityResult,
  SalesDay,
  SalesSummary,
  StorageBucket,
  StorageObject,
  StorageStats,
  TaskInstance,
  TopProduct,
  CategoryBreakdown,
  WarehouseTable,
} from '@/types/platform'

async function get<T>(path: string): Promise<T> {
  const response = await api.get<T>(path)
  return response.data
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const response = await api.post<T>(path, body)
  return response.data
}

async function patch<T>(path: string, body?: unknown): Promise<T> {
  const response = await api.patch<T>(path, body)
  return response.data
}

export function getPlatformHealth(): Promise<PlatformHealth> {
  return get<PlatformHealth>('/platform/health')
}

export function getPlatformLinks(): Promise<PlatformLinks> {
  return get<PlatformLinks>('/links')
}

export function getSalesDaily(limit = 120): Promise<SalesDay[]> {
  return get<SalesDay[]>(`/warehouse/sales?limit=${limit}`)
}

export function getSalesSummary(): Promise<SalesSummary> {
  return get<SalesSummary>('/warehouse/sales/summary')
}

export function getTopProducts(limit = 10): Promise<TopProduct[]> {
  return get<TopProduct[]>(`/warehouse/products/top?limit=${limit}`)
}

export function getCategoryBreakdown(): Promise<CategoryBreakdown[]> {
  return get<CategoryBreakdown[]>('/warehouse/categories')
}

export function getEltRuns(limit = 50): Promise<EltRun[]> {
  return get<EltRun[]>(`/warehouse/elt-runs?limit=${limit}`)
}

export function getQualityResults(limit = 20): Promise<QualityResult[]> {
  return get<QualityResult[]>(`/warehouse/quality?limit=${limit}`)
}

export function getWarehouseTables(): Promise<WarehouseTable[]> {
  return get<WarehouseTable[]>('/warehouse/tables')
}

export function listDags(limit = 100): Promise<Dag[]> {
  return get<Dag[]>(`/pipelines/dags?limit=${limit}`)
}

export function listDagRuns(dagId: string, limit = 25): Promise<DagRun[]> {
  return get<DagRun[]>(`/pipelines/dags/${encodeURIComponent(dagId)}/runs?limit=${limit}`)
}

export function listDagRunTasks(
  dagId: string,
  runId: string
): Promise<TaskInstance[]> {
  return get<TaskInstance[]>(
    `/pipelines/dags/${encodeURIComponent(dagId)}/runs/${encodeURIComponent(runId)}/tasks`
  )
}

export function triggerDag(
  dagId: string,
  conf?: Record<string, unknown>
): Promise<DagRun> {
  return post<DagRun>(
    `/pipelines/dags/${encodeURIComponent(dagId)}/trigger`,
    conf ?? {}
  )
}

export function setDagPaused(dagId: string, paused: boolean): Promise<Dag> {
  return patch<Dag>(
    `/pipelines/dags/${encodeURIComponent(dagId)}/pause?paused=${paused}`,
    {}
  )
}

export function listCatalogTables(limit = 50): Promise<CatalogTable[]> {
  return get<CatalogTable[]>(`/catalog/tables?limit=${limit}`)
}

export function searchCatalog(q: string): Promise<CatalogSearchResult[]> {
  return get<CatalogSearchResult[]>(
    `/catalog/search?q=${encodeURIComponent(q)}`
  )
}

export function getTableLineage(fqn: string): Promise<unknown> {
  return get<unknown>(`/catalog/lineage/${encodeURIComponent(fqn)}`)
}

export function listStorageBuckets(): Promise<StorageBucket[]> {
  return get<StorageBucket[]>('/storage/buckets')
}

export function listStorageObjects(
  bucket?: string,
  prefix = '',
  limit = 100
): Promise<{ bucket: string; count: number; objects: StorageObject[] }> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (bucket) params.set('bucket', bucket)
  if (prefix) params.set('prefix', prefix)
  return get<{ bucket: string; count: number; objects: StorageObject[] }>(
    `/storage/objects?${params.toString()}`
  )
}

export function getStorageStats(): Promise<StorageStats[]> {
  return get<StorageStats[]>('/storage/stats')
}

export function queryMonitoring(q: string): Promise<MonitoringSample[]> {
  return get<MonitoringSample[]>(
    `/monitoring/query?q=${encodeURIComponent(q)}`
  )
}
