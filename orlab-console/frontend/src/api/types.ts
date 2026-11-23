/**
 * 后端 API 类型定义
 * 字段名与后端契约逐字一致（camelCase），可空字段用 null 表示缺省。
 */

/** 健康检查：GET /api/health */
export interface HealthInfo {
  ok: boolean;
  orlabLogDir: string;
  runCount: number;
}

/** 实验状态 */
export type RunState = 'running' | 'finished' | 'crashed' | 'aborted';

/** 各状态实验计数 */
export interface StateCounts {
  running: number;
  finished: number;
  crashed: number;
  aborted: number;
}

/** 项目信息：GET /api/projects */
export interface ProjectInfo {
  name: string;
  workspace: string | null;
  runCount: number;
  stateCounts: StateCounts;
  lastActivityAt: string | null;
  tags: string[];
}

/** 单个指标的统计摘要 */
export interface MetricStat {
  last: number | null;
  min: number | null;
  max: number | null;
  avg: number | null;
}

/** 指标摘要条目（列表接口使用） */
export interface MetricSummaryItem extends MetricStat {
  key: string;
}

/** 实验列表条目：GET /api/experiments */
export interface ExperimentListItem {
  id: string;
  name: string;
  project: string | null;
  workspace: string | null;
  state: RunState;
  startedAt: string | null;
  finishedAt: string | null;
  durationSec: number | null;
  tags: string[];
  group: string | null;
  description: string | null;
  color: string | null;
  error: string | null;
  metricSummary: MetricSummaryItem[];
}

/** 实验列表响应 */
export interface ExperimentListResponse {
  total: number;
  page: number;
  pageSize: number;
  items: ExperimentListItem[];
}

/** 实验列表查询参数 */
export interface ExperimentQuery {
  search?: string;
  status?: string;
  project?: string;
  page?: number;
  pageSize?: number;
  sort?: string;
  order?: string;
}

/** 指标列信息 */
export interface ColumnInfo {
  key: string;
  type: string;
  name: string | null;
  className: string | null;
}

/** 实验详情：GET /api/experiments/:id */
export interface ExperimentDetail {
  id: string;
  name: string;
  project: string | null;
  workspace: string | null;
  state: RunState;
  startedAt: string | null;
  finishedAt: string | null;
  durationSec: number | null;
  tags: string[];
  group: string | null;
  description: string | null;
  color: string | null;
  error: string | null;
  stepRange: [number, number] | null;
  columns: ColumnInfo[];
  scalarKeyCount: number;
  logCount: number;
  mediaCount: number;
  config: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
  files: string[];
  metrics: Record<string, MetricStat>;
}

/** 指标数据点 */
export interface MetricPoint {
  step: number;
  value: number;
  timestamp: number | null;
}

/** 指标序列响应：GET /api/experiments/:id/metrics */
export interface MetricsResponse {
  series: Record<string, MetricPoint[]>;
  truncated: boolean;
}

/** 日志条目：GET /api/experiments/:id/logs */
export interface LogItem {
  /** 日志行内容 */
  line: string;
  level: string | null;
  timestamp: string | null;
  epoch: number | null;
}

/** 日志响应 */
export interface LogsResponse {
  total: number;
  items: LogItem[];
}

/** 媒体条目：GET /api/experiments/:id/media */
export interface MediaItem {
  key: string;
  step: number | null;
  filename: string | null;
  caption: string | null;
  size: number | null;
  type: string | null;
  url: string;
}

/** 媒体响应 */
export interface MediaResponse {
  items: MediaItem[];
}
