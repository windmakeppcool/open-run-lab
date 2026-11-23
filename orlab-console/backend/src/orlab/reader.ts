/**
 * orlab-log 解析层：
 *   1. LevelDB log 二进制格式读取（与 SDK 侧 open_run_lab/sdk/internal/core_python/store 保持一致）；
 *   2. Record 流 → 单个 run 的内存结构（ParsedRun）；
 *   3. run 目录扫描与按 mtime+size 失效的内存缓存。
 *
 * 二进制格式要点：
 *   - 文件头 7 字节：b":ORL"(4) + magic uint16 LE 0xE1D6(2) + version uint8 2(1)；
 *   - 块大小 32768 字节，记录头 7 字节：checksum uint32 LE + data_length uint16 LE + data_type uint8；
 *   - data_type：1=FULL 2=FIRST 3=MIDDLE 4=LAST，跨块记录由 FIRST..LAST 拼接；
 *   - checksum = 标准 IEEE CRC32（zlib 语义）对 [data_type 字节, ...data] 连续计算；
 *   - 容错：文件可能正被写入、尾部截断或单条损坏，遇到不完整/校验失败时优雅停止，
 *     返回已读到的记录，而不是抛垮整个请求。
 */
import * as fs from "fs";
import * as path from "path";
import * as YAML from "yaml";
import { decodeRecord, DecodedRecord } from "./proto";
import {
  ColumnInfo,
  LogLineInfo,
  LogLevelName,
  MediaItemInfo,
  MetricStats,
  ParsedRun,
  RunState,
  ScalarPoint,
} from "./types";

// ---------------------------------------------------------------------------
// LevelDB log 常量（与 Python 参考实现一致）
// ---------------------------------------------------------------------------
const BLOCK_LEN = 32768;
const HEADER_LEN = 7;
const DATA_LEN = BLOCK_LEN - HEADER_LEN;

const TYPE_FULL = 1;
const TYPE_FIRST = 2;
const TYPE_MIDDLE = 3;
const TYPE_LAST = 4;

const FILE_IDENT = Buffer.from(":ORL", "ascii");
const FILE_MAGIC = 0xe1d6;
const FILE_VERSION = 2;

// ---------------------------------------------------------------------------
// CRC32（标准 IEEE 多项式 0xEDB88320，init/xorout 均为 0xFFFFFFFF，与 zlib.crc32 一致）
// ---------------------------------------------------------------------------
const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[i] = c >>> 0;
  }
  return table;
})();

function crc32(buf: Buffer): number {
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    crc = CRC_TABLE[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

// ---------------------------------------------------------------------------
// 二进制记录读取
// ---------------------------------------------------------------------------

/** 单段记录读取结果；null 表示文件在此处正常/异常终止 */
interface RawSegment {
  dataType: number;
  data: Buffer;
}

/**
 * 从 pos 处读取一段记录（含块边界补 0 的跳过）。
 * 返回 null 表示文件提前结束（尾部截断等），调用方应优雅停止。
 */
function readSegment(buf: Buffer, pos: number): { segment: RawSegment | null; next: number } {
  let offset = pos % BLOCK_LEN;
  let spaceLeft = BLOCK_LEN - offset;
  // 剩余空间不足一个记录头：跳过填充字节，归位到下一个块
  if (spaceLeft < HEADER_LEN) {
    if (pos + spaceLeft > buf.length) return { segment: null, next: buf.length };
    pos += spaceLeft;
  }
  if (pos + HEADER_LEN > buf.length) return { segment: null, next: buf.length };
  const checksum = buf.readUInt32LE(pos);
  const dataLength = buf.readUInt16LE(pos + 4);
  const dataType = buf.readUInt8(pos + 6);
  pos += HEADER_LEN;
  if (pos + dataLength > buf.length) return { segment: null, next: buf.length };
  const data = buf.subarray(pos, pos + dataLength);
  pos += dataLength;
  // checksum 覆盖 [data_type 字节, ...data]
  const withType = Buffer.allocUnsafe(dataLength + 1);
  withType[0] = dataType;
  data.copy(withType, 1);
  if (crc32(withType) !== checksum) return { segment: null, next: pos };
  return { segment: { dataType, data }, next: pos };
}

/**
 * 读取整个 .orlab 文件的完整记录列表（每项为一条 Record 的 protobuf 字节）。
 * 0 字节文件返回空列表；版本不匹配抛出明确错误；
 * 尾部截断 / 单条损坏时优雅停止并返回已读到的记录。
 */
export function readOrlabRecords(filePath: string): Buffer[] {
  const buf = fs.readFileSync(filePath);
  if (buf.length === 0) return [];
  if (buf.length < HEADER_LEN) {
    throw new Error("无效的 orlab 数据文件（文件头不完整）");
  }
  const ident = buf.subarray(0, 4);
  const magic = buf.readUInt16LE(4);
  const version = buf.readUInt8(6);
  if (!ident.equals(FILE_IDENT) || magic !== FILE_MAGIC) {
    throw new Error("无效的 orlab 数据文件（文件头标识不匹配）");
  }
  if (version !== FILE_VERSION) {
    throw new Error("文件由不兼容的 SDK 版本创建");
  }

  const records: Buffer[] = [];
  let pos = HEADER_LEN; // 文件头占第一个块的前 7 字节
  let pending: Buffer[] | null = null; // 跨块记录的分段缓存

  for (;;) {
    const { segment, next } = readSegment(buf, pos);
    if (segment === null) break; // 截断 / 校验失败：优雅停止
    pos = next;
    const { dataType, data } = segment;
    if (pending === null) {
      if (dataType === TYPE_FULL) {
        records.push(Buffer.from(data));
      } else if (dataType === TYPE_FIRST) {
        pending = [Buffer.from(data)];
      } else {
        break; // 非法的起始类型，停止解析
      }
      continue;
    }
    // 跨块记录的后续分段
    if (dataType === TYPE_MIDDLE || dataType === TYPE_LAST) {
      pending.push(Buffer.from(data));
      if (dataType === TYPE_LAST) {
        records.push(Buffer.concat(pending));
        pending = null;
      }
      continue;
    }
    break; // 跨块记录被打断，停止解析
  }
  return records;
}

// ---------------------------------------------------------------------------
// 枚举名映射
// ---------------------------------------------------------------------------

/** ColumnType → 列类型名 */
const COLUMN_TYPE_NAMES: Record<number, string> = {
  0: "unspecified",
  1: "scalar",
  2: "image",
  3: "audio",
  4: "text",
  5: "video",
  6: "echarts",
  7: "object3d",
  8: "molecule",
  9: "html",
  10: "histogram",
};

/** ColumnType → media/ 子目录名（与 SDK 的 adapter.medium 映射一致） */
const MEDIA_TYPE_DIRS: Record<number, string> = {
  2: "image",
  3: "audio",
  4: "text",
  5: "video",
  6: "echarts",
  7: "object3d",
  8: "molecule",
  9: "html",
};

/** ColumnClass → 列来源类别名 */
const COLUMN_CLASS_NAMES: Record<number, string> = {
  0: "unspecified",
  1: "custom",
  2: "system",
};

/** RunState 枚举 → API 状态字符串 */
const RUN_STATE_NAMES: Record<number, RunState> = {
  0: "running",
  1: "finished",
  2: "crashed",
  3: "aborted",
};

/** LogLevel 枚举 → API 日志级别字符串 */
const LOG_LEVEL_NAMES: Record<number, LogLevelName> = {
  0: "info",
  1: "error",
};

/** 媒体类型 → media/ 子目录名，未知类型回退为 unknown */
export function mediaTypeDir(columnType: number): string {
  return MEDIA_TYPE_DIRS[columnType] ?? "unknown";
}

// ---------------------------------------------------------------------------
// run 解析
// ---------------------------------------------------------------------------

/** 计算一组标量点的统计信息（last/min/max/avg），忽略 NaN/Inf */
export function computeMetricStats(points: ScalarPoint[]): MetricStats {
  const values = points.map((p) => p.value);
  const last = values.length > 0 ? values[values.length - 1] : null;
  const finite = values.filter((v) => Number.isFinite(v));
  if (finite.length === 0) {
    return { last, min: null, max: null, avg: null };
  }
  let min = finite[0];
  let max = finite[0];
  let sum = 0;
  for (const v of finite) {
    if (v < min) min = v;
    if (v > max) max = v;
    sum += v;
  }
  return { last, min, max, avg: sum / finite.length };
}

/** 解析单个 run 目录：读取 .orlab 记录流并组装 ParsedRun */
export function parseRun(dirPath: string): ParsedRun {
  const dirName = path.basename(dirPath);
  const entries = fs.readdirSync(dirPath);
  const dataFile = entries.filter((f) => f.endsWith(".orlab")).sort()[0];
  if (!dataFile) {
    throw new Error(`run 目录缺少 .orlab 数据文件: ${dirName}`);
  }
  const orlabFile = path.join(dirPath, dataFile);

  const scalars = new Map<string, ScalarPoint[]>();
  const columns: ColumnInfo[] = [];
  const logs: LogLineInfo[] = [];
  const media: MediaItemInfo[] = [];
  let stepMin = Number.POSITIVE_INFINITY;
  let stepMax = Number.NEGATIVE_INFINITY;
  let start: Extract<DecodedRecord, { kind: "start" }>["start"] | null = null;
  let finish: Extract<DecodedRecord, { kind: "finish" }>["finish"] | null = null;

  const noteStep = (step: number) => {
    if (step < stepMin) stepMin = step;
    if (step > stepMax) stepMax = step;
  };

  for (const raw of readOrlabRecords(orlabFile)) {
    let rec: DecodedRecord;
    try {
      rec = decodeRecord(raw);
    } catch {
      // 单条 protobuf 解码失败时跳过该条，不影响其余记录
      continue;
    }
    switch (rec.kind) {
      case "start":
        start = rec.start;
        break;
      case "finish":
        finish = rec.finish;
        break;
      case "column":
        columns.push({
          key: rec.column.columnKey,
          type: COLUMN_TYPE_NAMES[rec.column.columnType] ?? "unspecified",
          name: rec.column.columnName || rec.column.columnKey,
          className: COLUMN_CLASS_NAMES[rec.column.columnClass] ?? "unspecified",
        });
        break;
      case "scalar": {
        noteStep(rec.scalar.step);
        const arr = scalars.get(rec.scalar.key) ?? [];
        arr.push({ step: rec.scalar.step, value: rec.scalar.value, timestamp: rec.scalar.timestamp });
        scalars.set(rec.scalar.key, arr);
        break;
      }
      case "media": {
        noteStep(rec.media.step);
        for (const item of rec.media.items) {
          media.push({
            key: rec.media.key,
            step: rec.media.step,
            filename: item.filename,
            caption: item.caption,
            size: item.size,
            type: mediaTypeDir(rec.media.type),
            timestamp: rec.media.timestamp,
          });
        }
        break;
      }
      case "histogram":
        noteStep(rec.histogram.step);
        break;
      case "log":
        logs.push({
          line: rec.log.line,
          level: LOG_LEVEL_NAMES[rec.log.level] ?? "info",
          timestamp: rec.log.timestamp,
          epoch: rec.log.epoch,
        });
        break;
      default:
        // save / other：文件内容直接取自 run 目录 files/，此处无需处理
        break;
    }
  }

  // files/ 目录下的文件列表与 config/metadata 内容
  const filesDir = path.join(dirPath, "files");
  let files: string[] = [];
  if (fs.existsSync(filesDir)) {
    files = fs
      .readdirSync(filesDir)
      .filter((f) => fs.statSync(path.join(filesDir, f)).isFile())
      .sort();
  }
  let config: Record<string, unknown> | null = null;
  try {
    const parsed: unknown = YAML.parse(fs.readFileSync(path.join(filesDir, "config.yaml"), "utf8"));
    if (parsed && typeof parsed === "object") config = parsed as Record<string, unknown>;
  } catch {
    // config.yaml 缺失或解析失败时保持 null
  }
  let metadata: Record<string, unknown> | null = null;
  try {
    const parsed: unknown = JSON.parse(fs.readFileSync(path.join(filesDir, "orlab-metadata.json"), "utf8"));
    if (parsed && typeof parsed === "object") metadata = parsed as Record<string, unknown>;
  } catch {
    // orlab-metadata.json 缺失或解析失败时保持 null
  }

  // 缺少 StartRecord 时的兜底：id 取目录名末段
  const fallbackId = dirName.includes("-") ? dirName.slice(dirName.lastIndexOf("-") + 1) : dirName;

  return {
    dirName,
    dirPath,
    orlabFile,
    id: start?.id || fallbackId,
    name: start?.name || fallbackId,
    project: start?.project ?? "",
    workspace: start?.workspace ?? "",
    tags: start?.tags ?? [],
    group: start?.group ?? "",
    description: start?.description ?? "",
    color: start?.color ?? "",
    state: finish ? RUN_STATE_NAMES[finish.state] ?? "running" : "running",
    startedAt: start?.startedAt ?? null,
    finishedAt: finish?.finishedAt ?? null,
    error: finish?.error ?? "",
    scalars,
    columns,
    logs,
    media,
    stepMin: Number.isFinite(stepMin) ? stepMin : 0,
    stepMax: Number.isFinite(stepMax) ? stepMax : 0,
    config,
    metadata,
    files,
  };
}

// ---------------------------------------------------------------------------
// run 目录扫描与缓存
// ---------------------------------------------------------------------------

interface CacheEntry {
  /** 失效依据：数据文件 + config/metadata 的 mtime+size */
  fingerprint: string;
  run: ParsedRun;
}

/**
 * run 存储：启动时扫描 ORLAB_LOGDIR 下的 run-* 目录，请求时懒加载并缓存，
 * 按文件 mtime+size 变化失效（运行中的 run 增长时整体重解析）。
 */
export class RunStore {
  readonly orlabLogDir: string;
  private runDirs: string[] = [];
  private cache = new Map<string, CacheEntry>();

  constructor(orlabLogDir: string) {
    this.orlabLogDir = orlabLogDir;
    this.scan();
  }

  /** 启动时扫描 orlab-log 目录下的 run-* 目录 */
  scan(): void {
    if (!fs.existsSync(this.orlabLogDir)) {
      this.runDirs = [];
      return;
    }
    this.runDirs = fs
      .readdirSync(this.orlabLogDir)
      .filter((name) => name.startsWith("run-") && fs.statSync(path.join(this.orlabLogDir, name)).isDirectory())
      .sort()
      .map((name) => path.join(this.orlabLogDir, name));
  }

  /** 全部 run 目录路径 */
  listRunDirs(): string[] {
    return [...this.runDirs];
  }

  /** 解析（或取缓存）单个 run */
  loadRun(dirPath: string): ParsedRun {
    const fingerprint = this.fingerprint(dirPath);
    const cached = this.cache.get(dirPath);
    if (cached && cached.fingerprint === fingerprint) return cached.run;
    const run = parseRun(dirPath);
    this.cache.set(dirPath, { fingerprint, run });
    return run;
  }

  /** 解析（或取缓存）全部 run */
  loadAllRuns(): ParsedRun[] {
    return this.runDirs.map((dir) => this.loadRun(dir));
  }

  /** 按 run id（或目录名）查找 run，未找到返回 null */
  findRun(id: string): ParsedRun | null {
    for (const dir of this.runDirs) {
      const run = this.loadRun(dir);
      if (run.id === id || run.dirName === id) return run;
    }
    return null;
  }

  /** 缓存失效依据：数据文件与 config/metadata 文件的 mtime+size */
  private fingerprint(dirPath: string): string {
    const parts: string[] = [];
    for (const f of this.relevantFiles(dirPath)) {
      try {
        const st = fs.statSync(f);
        parts.push(`${f}:${st.mtimeMs}:${st.size}`);
      } catch {
        parts.push(`${f}:missing`);
      }
    }
    return parts.join("|");
  }

  private relevantFiles(dirPath: string): string[] {
    const files: string[] = [];
    try {
      for (const f of fs.readdirSync(dirPath)) {
        if (f.endsWith(".orlab")) files.push(path.join(dirPath, f));
      }
    } catch {
      // 目录不可读时交由 parseRun 抛出明确错误
    }
    files.push(path.join(dirPath, "files", "config.yaml"));
    files.push(path.join(dirPath, "files", "orlab-metadata.json"));
    return files;
  }
}
