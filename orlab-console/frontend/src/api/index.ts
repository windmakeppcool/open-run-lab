/**
 * 后端 API 请求封装
 * 所有响应为 camelCase JSON；错误格式为 {error: string}。
 */
import type {
  ExperimentDetail,
  ExperimentListResponse,
  ExperimentQuery,
  HealthInfo,
  LogsResponse,
  MediaResponse,
  MetricsResponse,
  ProjectInfo,
} from './types';

const BASE = '/api';

/** 接口请求异常（携带后端返回的 error 信息） */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** 通用 GET 请求：拼接查询参数并解析 JSON / 错误 */
async function request<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(BASE + path, window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== '') {
        url.searchParams.set(key, String(value));
      }
    }
  }
  let res: Response;
  try {
    res = await fetch(url.toString());
  } catch {
    throw new ApiError('无法连接后端服务，请确认后端已启动', 0);
  }
  if (!res.ok) {
    let message = `请求失败（HTTP ${res.status}）`;
    try {
      const body = (await res.json()) as { error?: unknown };
      if (body && typeof body.error === 'string' && body.error) {
        message = body.error;
      }
    } catch {
      // 响应不是 JSON 时保留默认提示
    }
    throw new ApiError(message, res.status);
  }
  return (await res.json()) as T;
}

/** 健康检查与数据来源信息 */
export function getHealth(): Promise<HealthInfo> {
  return request<HealthInfo>('/health');
}

/** 项目列表（含状态计数与最近活动时间） */
export function getProjects(): Promise<{ projects: ProjectInfo[] }> {
  return request<{ projects: ProjectInfo[] }>('/projects');
}

/** 实验列表（分页 / 筛选 / 排序） */
export function getExperiments(query: ExperimentQuery = {}): Promise<ExperimentListResponse> {
  return request<ExperimentListResponse>('/experiments', {
    search: query.search,
    status: query.status,
    project: query.project,
    page: query.page,
    pageSize: query.pageSize,
    sort: query.sort,
    order: query.order,
  });
}

/** 实验详情 */
export function getExperiment(id: string): Promise<ExperimentDetail> {
  return request<ExperimentDetail>(`/experiments/${encodeURIComponent(id)}`);
}

/** 实验指标序列（keys 为逗号分隔的指标名，缺省取全部） */
export function getExperimentMetrics(id: string, keys?: string[], maxPoints = 500): Promise<MetricsResponse> {
  return request<MetricsResponse>(`/experiments/${encodeURIComponent(id)}/metrics`, {
    keys: keys && keys.length ? keys.join(',') : undefined,
    maxPoints,
  });
}

/** 实验日志（分页 + 级别过滤） */
export function getExperimentLogs(
  id: string,
  params: { level?: string; limit?: number; offset?: number } = {},
): Promise<LogsResponse> {
  return request<LogsResponse>(`/experiments/${encodeURIComponent(id)}/logs`, {
    level: params.level,
    limit: params.limit,
    offset: params.offset,
  });
}

/** 实验媒体文件 */
export function getExperimentMedia(id: string): Promise<MediaResponse> {
  return request<MediaResponse>(`/experiments/${encodeURIComponent(id)}/media`);
}
