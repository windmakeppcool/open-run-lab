/**
 * 解析层的共享类型定义：orlab-log 单个 run 解析后的内存结构。
 */

/** Run 状态（与 API 契约中的字符串一致） */
export type RunState = "running" | "finished" | "crashed" | "aborted";

/** 日志级别名（与 API 契约中的字符串一致） */
export type LogLevelName = "info" | "error";

/** 单个标量数据点 */
export interface ScalarPoint {
  step: number;
  /** 标量值；NaN/Inf 场景下由 API 层序列化为 null */
  value: number;
  /** ISO 8601 时间戳，缺失时为 null */
  timestamp: string | null;
}

/** 某个 key 的统计信息 */
export interface MetricStats {
  last: number | null;
  min: number | null;
  max: number | null;
  avg: number | null;
}

/** 列定义（ColumnRecord 解析结果） */
export interface ColumnInfo {
  key: string;
  /** 列类型名：scalar / image / audio / text / ... */
  type: string;
  /** 显示名，未设置时回退为 key */
  name: string;
  /** 列来源类别名：custom / system / unspecified */
  className: string;
}

/** 单条媒体文件引用（MediaRecord 中的一个 MediaItem） */
export interface MediaItemInfo {
  key: string;
  step: number;
  filename: string;
  caption: string;
  size: number;
  /** 媒体类型名，同时也是 media/ 下的子目录名：text / image / audio / ... */
  type: string;
  timestamp: string | null;
}

/** 单行终端日志（LogRecord 解析结果） */
export interface LogLineInfo {
  line: string;
  level: LogLevelName;
  timestamp: string | null;
  epoch: number;
}

/** 单个 run 的完整解析结果 */
export interface ParsedRun {
  /** run 目录名，如 run-20261113_101202-v26zt0lw */
  dirName: string;
  /** run 目录绝对路径 */
  dirPath: string;
  /** 核心数据文件（run-<id>.orlab）绝对路径 */
  orlabFile: string;
  /** run id，如 v26zt0lw */
  id: string;
  name: string;
  project: string;
  workspace: string;
  tags: string[];
  group: string;
  description: string;
  color: string;
  state: RunState;
  /** ISO 8601，缺失时为 null */
  startedAt: string | null;
  /** ISO 8601，缺失时为 null（仍在运行的 run） */
  finishedAt: string | null;
  /** 结束错误信息（state=crashed 时有值），无错误时为空串 */
  error: string;
  /** 各 scalar key 的时序点，保持写入顺序 */
  scalars: Map<string, ScalarPoint[]>;
  columns: ColumnInfo[];
  logs: LogLineInfo[];
  /** 扁平化的媒体条目（每个 MediaItem 一条） */
  media: MediaItemInfo[];
  /** 全部指标记录（scalar/media/histogram）的 step 范围 */
  stepMin: number;
  stepMax: number;
  /** files/config.yaml 解析后的对象，缺失或解析失败时为 null */
  config: Record<string, unknown> | null;
  /** files/orlab-metadata.json 解析后的对象，缺失或解析失败时为 null */
  metadata: Record<string, unknown> | null;
  /** files/ 目录下的文件名列表（排序后） */
  files: string[];
}
