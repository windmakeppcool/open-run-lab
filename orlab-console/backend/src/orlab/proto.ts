/**
 * proto 定义加载与 Record 信封解码。
 *
 * 使用 protobufjs 在运行时加载仓库根目录 protos/ 下的 .proto 文件（不做 codegen）。
 * record.proto 引用了 google/protobuf/timestamp.proto：
 *   1. 优先依赖 protobufjs 对 google/protobuf/common 类型的内置支持；
 *   2. 若内置支持不可用（解析失败），回退到 vendored 的 timestamp.proto（backend/proto/）。
 */
import * as fs from "fs";
import * as path from "path";
import protobuf from "protobufjs";

/** protos 源码根目录（backend 包目录的 ../../../protos） */
const PROTO_DIR = process.env.ORLAB_PROTOS_DIR
  ? path.resolve(process.env.ORLAB_PROTOS_DIR)
  : path.resolve(__dirname, "../../../../protos");

/** vendored proto 目录（内置 common 不可用时的回退） */
const VENDORED_PROTO_DIR = path.resolve(__dirname, "../../proto");

/** 需要加载的 proto 文件（record.proto 已 import 其余文件，此处显式列出便于校验） */
const PROTO_FILES = [
  "orlab/record/v1/record.proto",
  "orlab/run/v1/run.proto",
  "orlab/metric/data/v1/data.proto",
  "orlab/metric/column/v1/column.proto",
  "orlab/terminal/v1/log.proto",
  "orlab/save/v1/save.proto",
];

/** protobufjs 解码出的 int64 可能是 Long 对象，统一转 number */
function num(v: unknown): number {
  if (v === null || v === undefined) return 0;
  if (typeof v === "number") return v;
  if (typeof v === "object" && typeof (v as { toNumber?: unknown }).toNumber === "function") {
    return (v as { toNumber: () => number }).toNumber();
  }
  return Number(v);
}

/** google.protobuf.Timestamp → ISO 8601 字符串，缺失时返回 null */
function tsToIso(ts: unknown): string | null {
  if (!ts || typeof ts !== "object") return null;
  const t = ts as { seconds?: unknown; nanos?: unknown };
  const seconds = num(t.seconds);
  const nanos = num(t.nanos);
  if (!Number.isFinite(seconds)) return null;
  return new Date(seconds * 1000 + nanos / 1e6).toISOString();
}

/** 解码后的各 Record 子类型（时间戳统一转 ISO 8601，int64 统一转 number） */
export interface StartRecordData {
  project: string;
  workspace: string;
  public: boolean;
  name: string;
  description: string;
  tags: string[];
  group: string;
  jobType: string;
  color: string;
  id: string;
  resume: number;
  startedAt: string | null;
}

export interface FinishRecordData {
  /** 0=RUNNING 1=FINISHED 2=CRASHED 3=ABORTED */
  state: number;
  error: string;
  finishedAt: string | null;
}

export interface ColumnRecordData {
  /** 1=CUSTOM 2=SYSTEM */
  columnClass: number;
  /** 1=SCALAR 2=IMAGE 3=AUDIO 4=TEXT ... 10=HISTOGRAM */
  columnType: number;
  columnKey: string;
  columnName: string;
  sectionName: string;
}

export interface ScalarRecordData {
  key: string;
  step: number;
  type: number;
  timestamp: string | null;
  value: number;
}

export interface MediaItemData {
  filename: string;
  sha256: string;
  size: number;
  caption: string;
}

export interface MediaRecordData {
  key: string;
  step: number;
  type: number;
  timestamp: string | null;
  items: MediaItemData[];
}

export interface HistogramRecordData {
  key: string;
  step: number;
  type: number;
  timestamp: string | null;
}

export interface LogRecordData {
  line: string;
  /** 0=INFO 1=ERROR */
  level: number;
  timestamp: string | null;
  epoch: number;
}

export interface SaveRecordData {
  name: string;
  sourcePath: string;
  targetPath: string;
  /** 0=NOW 1=END 2=LIVE */
  policy: number;
  /** 0=CUSTOM 1=CONFIG 2=METADATA 3=REQUIREMENTS 4=CONDA */
  type: number;
}

export type DecodedRecord =
  | { kind: "start"; num: number; timestamp: string | null; start: StartRecordData }
  | { kind: "finish"; num: number; timestamp: string | null; finish: FinishRecordData }
  | { kind: "column"; num: number; timestamp: string | null; column: ColumnRecordData }
  | { kind: "scalar"; num: number; timestamp: string | null; scalar: ScalarRecordData }
  | { kind: "media"; num: number; timestamp: string | null; media: MediaRecordData }
  | { kind: "histogram"; num: number; timestamp: string | null; histogram: HistogramRecordData }
  | { kind: "log"; num: number; timestamp: string | null; log: LogRecordData }
  | { kind: "save"; num: number; timestamp: string | null; save: SaveRecordData }
  | { kind: "other"; num: number; timestamp: string | null };

/**
 * 加载 proto 定义。
 * useVendored=false 时 google/protobuf/* 交给 protobufjs 内置 common 处理；
 * 失败则以 useVendored=true 重试，从 backend/proto/ 读取 vendored 的 timestamp.proto。
 */
function loadRoot(useVendored: boolean): protobuf.Root {
  const root = new protobuf.Root();
  root.resolvePath = (_origin: string, target: string): string => {
    if (target.startsWith("google/protobuf/")) {
      // 内置 common：原样返回即可被 protobufjs 识别；否则指向 vendored 文件
      return useVendored ? path.join(VENDORED_PROTO_DIR, target) : target;
    }
    // orlab/... 的相对导入统一解析到 protos 根目录
    return path.resolve(PROTO_DIR, target);
  };
  root.loadSync(PROTO_FILES.map((f) => path.resolve(PROTO_DIR, f)));
  return root;
}

let root: protobuf.Root;
try {
  // 先验证 protobufjs 对 google/protobuf/common 类型的内置支持
  root = loadRoot(false);
} catch {
  // 内置支持不可用，回退到 vendored 的 timestamp.proto
  root = loadRoot(true);
}

const RecordType = root.lookupType("orlab.record.v1.Record");

/** 将一条完整的 Record 字节解码为类型化的普通对象 */
export function decodeRecord(buf: Buffer): DecodedRecord {
  const rec = RecordType.decode(buf) as unknown as {
    num?: unknown;
    timestamp?: unknown;
    start?: Record<string, unknown> | null;
    finish?: Record<string, unknown> | null;
    column?: Record<string, unknown> | null;
    scalar?: Record<string, unknown> | null;
    media?: Record<string, unknown> | null;
    histogram?: Record<string, unknown> | null;
    log?: Record<string, unknown> | null;
    save?: Record<string, unknown> | null;
  };
  const n = num(rec.num);
  const ts = tsToIso(rec.timestamp);

  if (rec.start) {
    const s = rec.start;
    return {
      kind: "start",
      num: n,
      timestamp: ts,
      start: {
        project: String(s.project ?? ""),
        workspace: String(s.workspace ?? ""),
        public: Boolean(s.public),
        name: String(s.name ?? ""),
        description: String(s.description ?? ""),
        tags: Array.isArray(s.tags) ? s.tags.map((t) => String(t)) : [],
        group: String(s.group ?? ""),
        jobType: String(s.jobType ?? ""),
        color: String(s.color ?? ""),
        id: String(s.id ?? ""),
        resume: num(s.resume),
        startedAt: tsToIso(s.startedAt),
      },
    };
  }
  if (rec.finish) {
    const f = rec.finish;
    return {
      kind: "finish",
      num: n,
      timestamp: ts,
      finish: {
        state: num(f.state),
        error: String(f.error ?? ""),
        finishedAt: tsToIso(f.finishedAt),
      },
    };
  }
  if (rec.column) {
    const c = rec.column;
    return {
      kind: "column",
      num: n,
      timestamp: ts,
      column: {
        columnClass: num(c.columnClass),
        columnType: num(c.columnType),
        columnKey: String(c.columnKey ?? ""),
        columnName: String(c.columnName ?? ""),
        sectionName: String(c.sectionName ?? ""),
      },
    };
  }
  if (rec.scalar) {
    const s = rec.scalar;
    const value = s.value as { number?: unknown } | null | undefined;
    return {
      kind: "scalar",
      num: n,
      timestamp: ts,
      scalar: {
        key: String(s.key ?? ""),
        step: num(s.step),
        type: num(s.type),
        timestamp: tsToIso(s.timestamp),
        value: value ? num(value.number) : 0,
      },
    };
  }
  if (rec.media) {
    const m = rec.media;
    const value = m.value as { items?: unknown[] } | null | undefined;
    const items: MediaItemData[] = Array.isArray(value?.items)
      ? value.items.map((it) => {
          const i = it as Record<string, unknown>;
          return {
            filename: String(i.filename ?? ""),
            sha256: String(i.sha256 ?? ""),
            size: num(i.size),
            caption: String(i.caption ?? ""),
          };
        })
      : [];
    return {
      kind: "media",
      num: n,
      timestamp: ts,
      media: {
        key: String(m.key ?? ""),
        step: num(m.step),
        type: num(m.type),
        timestamp: tsToIso(m.timestamp),
        items,
      },
    };
  }
  if (rec.histogram) {
    const h = rec.histogram;
    return {
      kind: "histogram",
      num: n,
      timestamp: ts,
      histogram: {
        key: String(h.key ?? ""),
        step: num(h.step),
        type: num(h.type),
        timestamp: tsToIso(h.timestamp),
      },
    };
  }
  if (rec.log) {
    const l = rec.log;
    return {
      kind: "log",
      num: n,
      timestamp: ts,
      log: {
        line: String(l.line ?? ""),
        level: num(l.level),
        timestamp: tsToIso(l.timestamp),
        epoch: num(l.epoch),
      },
    };
  }
  if (rec.save) {
    const s = rec.save;
    return {
      kind: "save",
      num: n,
      timestamp: ts,
      save: {
        name: String(s.name ?? ""),
        sourcePath: String(s.sourcePath ?? ""),
        targetPath: String(s.targetPath ?? ""),
        policy: num(s.policy),
        type: num(s.type),
      },
    };
  }
  return { kind: "other", num: n, timestamp: ts };
}
