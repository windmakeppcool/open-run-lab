/**
 * API 层：Express 路由，按 API 契约输出 camelCase JSON。
 * 只依赖 orlab/ 解析层，不包含任何解析逻辑。
 */
import { Router, Request, Response } from "express";
import * as fs from "fs";
import * as path from "path";
import { computeMetricStats, RunStore } from "./orlab/reader";
import { MetricStats, ParsedRun, ScalarPoint } from "./orlab/types";

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

/** run 的最后活动时间（finishedAt 优先，其次全部记录里最大的时间戳），ISO 8601 或 null */
function lastActivityAt(run: ParsedRun): string | null {
  let max: string | null = run.finishedAt;
  const consider = (t: string | null) => {
    if (t && (!max || t > max)) max = t;
  };
  for (const points of run.scalars.values()) {
    for (const p of points) consider(p.timestamp);
  }
  for (const l of run.logs) consider(l.timestamp);
  for (const m of run.media) consider(m.timestamp);
  return max ?? run.startedAt;
}

/** 时长（秒）：finishedAt 与 startedAt 之差；仍在运行的 run 用最后活动时间；无法确定时为 null */
function durationSec(run: ParsedRun): number | null {
  if (!run.startedAt) return null;
  const startMs = Date.parse(run.startedAt);
  const endIso = run.finishedAt ?? lastActivityAt(run);
  const endMs = endIso ? Date.parse(endIso) : NaN;
  if (!Number.isFinite(startMs) || !Number.isFinite(endMs)) return null;
  return Math.round(endMs - startMs) / 1000;
}

/** 均匀降采样到最多 maxPoints 个点 */
function downsample(points: ScalarPoint[], maxPoints: number): { points: ScalarPoint[]; truncated: boolean } {
  if (maxPoints <= 1) {
    return { points: points.slice(0, 1), truncated: points.length > 1 };
  }
  if (points.length <= maxPoints) return { points, truncated: false };
  const out: ScalarPoint[] = [];
  const n = points.length;
  for (let i = 0; i < maxPoints; i++) {
    out.push(points[Math.round((i * (n - 1)) / (maxPoints - 1))]);
  }
  return { points: out, truncated: true };
}

/** 序列化标量值：NaN/Inf 在 JSON 中无表示，统一为 null */
function jsonNumber(v: number): number | null {
  return Number.isFinite(v) ? v : null;
}

/** 扩展名 → Content-Type */
const CONTENT_TYPES: Record<string, string> = {
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  gif: "image/gif",
  webp: "image/webp",
  bmp: "image/bmp",
  svg: "image/svg+xml",
  mp3: "audio/mpeg",
  wav: "audio/wav",
  flac: "audio/flac",
  ogg: "audio/ogg",
  m4a: "audio/mp4",
  mp4: "video/mp4",
  webm: "video/webm",
  mov: "video/quicktime",
  txt: "text/plain; charset=utf-8",
  html: "text/html; charset=utf-8",
  json: "application/json",
  yaml: "text/yaml; charset=utf-8",
  csv: "text/csv; charset=utf-8",
};

function contentTypeOf(filename: string): string {
  const ext = filename.includes(".") ? filename.slice(filename.lastIndexOf(".") + 1).toLowerCase() : "";
  return CONTENT_TYPES[ext] ?? "application/octet-stream";
}

// ---------------------------------------------------------------------------
// 响应组装
// ---------------------------------------------------------------------------

/** 列表项（实验摘要） */
function runSummary(run: ParsedRun): Record<string, unknown> {
  const summary: Array<{ key: string } & MetricStats> = [];
  // 真实数据常把 __orlab__. 系统监控指标写在最前，关键指标优先取用户自定义列，全为系统列时才回退
  const allKeys = [...run.scalars.keys()];
  const customKeys = allKeys.filter((key) => !key.startsWith("__orlab__."));
  for (const key of (customKeys.length ? customKeys : allKeys).slice(0, 8)) {
    summary.push({ key, ...computeMetricStats(run.scalars.get(key) as ScalarPoint[]) });
  }
  return {
    id: run.id,
    name: run.name,
    project: run.project,
    workspace: run.workspace,
    state: run.state,
    startedAt: run.startedAt,
    finishedAt: run.finishedAt,
    durationSec: durationSec(run),
    tags: run.tags,
    group: run.group,
    description: run.description,
    color: run.color,
    error: run.error || null,
    metricSummary: summary,
  };
}

/** 实验详情 */
function runDetail(run: ParsedRun): Record<string, unknown> {
  const metrics: Record<string, MetricStats> = {};
  for (const [key, points] of run.scalars) {
    metrics[key] = computeMetricStats(points);
  }
  return {
    id: run.id,
    name: run.name,
    project: run.project,
    workspace: run.workspace,
    state: run.state,
    startedAt: run.startedAt,
    finishedAt: run.finishedAt,
    durationSec: durationSec(run),
    tags: run.tags,
    group: run.group,
    description: run.description,
    color: run.color,
    error: run.error || null,
    stepRange: [run.stepMin, run.stepMax],
    columns: run.columns.map((c) => ({ key: c.key, type: c.type, name: c.name, className: c.className })),
    scalarKeyCount: run.scalars.size,
    logCount: run.logs.length,
    mediaCount: run.media.length,
    config: run.config,
    metadata: run.metadata,
    files: run.files,
    metrics,
  };
}

// ---------------------------------------------------------------------------
// 路由
// ---------------------------------------------------------------------------

export function createRouter(store: RunStore): Router {
  const router = Router();

  /** 统一错误处理：业务异常 500，未知 id 404 */
  const handle = (res: Response, fn: () => void) => {
    try {
      fn();
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      res.status(500).json({ error: message });
    }
  };

  /** 取 run，未找到时写 404 响应并返回 null */
  const getRun = (req: Request, res: Response): ParsedRun | null => {
    const run = store.findRun(String(req.params.id));
    if (!run) {
      res.status(404).json({ error: `实验不存在: ${req.params.id}` });
      return null;
    }
    return run;
  };

  // 健康检查
  router.get("/api/health", (_req, res) => {
    handle(res, () => {
      res.json({ ok: true, orlabLogDir: store.orlabLogDir, runCount: store.listRunDirs().length });
    });
  });

  // 项目列表
  router.get("/api/projects", (_req, res) => {
    handle(res, () => {
      interface ProjectAcc {
        name: string;
        workspace: string;
        runCount: number;
        stateCounts: { running: number; finished: number; crashed: number; aborted: number };
        lastActivityAt: string | null;
        tags: string[];
      }
      const byProject = new Map<string, ProjectAcc>();
      for (const run of store.loadAllRuns()) {
        let acc = byProject.get(run.project);
        if (!acc) {
          acc = {
            name: run.project,
            workspace: run.workspace,
            runCount: 0,
            stateCounts: { running: 0, finished: 0, crashed: 0, aborted: 0 },
            lastActivityAt: null,
            tags: [],
          };
          byProject.set(run.project, acc);
        }
        acc.runCount += 1;
        acc.stateCounts[run.state] += 1;
        const activity = lastActivityAt(run);
        if (activity && (!acc.lastActivityAt || activity > acc.lastActivityAt)) acc.lastActivityAt = activity;
        for (const tag of run.tags) {
          if (acc.tags.length < 10 && !acc.tags.includes(tag)) acc.tags.push(tag);
        }
      }
      const projects = [...byProject.values()].sort((a, b) => {
        // 按最后活动时间倒序
        return (b.lastActivityAt ?? "").localeCompare(a.lastActivityAt ?? "");
      });
      res.json({ projects });
    });
  });

  // 实验列表
  router.get("/api/experiments", (req, res) => {
    handle(res, () => {
      const search = String(req.query.search ?? "").trim().toLowerCase();
      const status = String(req.query.status ?? "").trim().toLowerCase();
      const project = String(req.query.project ?? "").trim();
      const page = Math.max(1, Math.floor(Number(req.query.page)) || 1);
      const pageSize = Math.max(1, Math.floor(Number(req.query.pageSize)) || 20);
      const sortField = String(req.query.sort ?? "startedAt");
      const order = String(req.query.order ?? "desc") === "asc" ? "asc" : "desc";

      let runs = store.loadAllRuns();
      // search：对 name/id/project 模糊匹配（不区分大小写）
      if (search) {
        runs = runs.filter(
          (r) =>
            r.name.toLowerCase().includes(search) ||
            r.id.toLowerCase().includes(search) ||
            r.project.toLowerCase().includes(search)
        );
      }
      // status：过滤 state
      if (status && status !== "all") {
        runs = runs.filter((r) => r.state === status);
      }
      // project：精确过滤
      if (project) {
        runs = runs.filter((r) => r.project === project);
      }
      // 排序
      const dir = order === "asc" ? 1 : -1;
      const cmp = (a: ParsedRun, b: ParsedRun): number => {
        if (sortField === "name") {
          return dir * a.name.localeCompare(b.name);
        }
        const av = sortField === "finishedAt" ? (a.finishedAt ?? "") : (a.startedAt ?? "");
        const bv = sortField === "finishedAt" ? (b.finishedAt ?? "") : (b.startedAt ?? "");
        return dir * av.localeCompare(bv);
      };
      runs = [...runs].sort(cmp);

      const total = runs.length;
      const items = runs.slice((page - 1) * pageSize, page * pageSize).map(runSummary);
      res.json({ total, page, pageSize, items });
    });
  });

  // 实验详情
  router.get("/api/experiments/:id", (req, res) => {
    handle(res, () => {
      const run = getRun(req, res);
      if (!run) return;
      res.json(runDetail(run));
    });
  });

  // 指标时序
  router.get("/api/experiments/:id/metrics", (req, res) => {
    handle(res, () => {
      const run = getRun(req, res);
      if (!run) return;
      const keysParam = String(req.query.keys ?? "").trim();
      const keys = keysParam
        ? keysParam
            .split(",")
            .map((k) => k.trim())
            .filter((k) => k.length > 0)
        : [...run.scalars.keys()];
      const maxPoints = Math.max(1, Math.floor(Number(req.query.maxPoints)) || 500);

      let truncated = false;
      const series: Record<string, Array<{ step: number; value: number | null; timestamp: string | null }>> = {};
      for (const key of keys) {
        const points = run.scalars.get(key);
        if (!points) continue; // 未知 key 静默跳过
        const sorted = [...points].sort((a, b) => a.step - b.step);
        const sampled = downsample(sorted, maxPoints);
        if (sampled.truncated) truncated = true;
        series[key] = sampled.points.map((p) => ({
          step: p.step,
          value: jsonNumber(p.value),
          timestamp: p.timestamp,
        }));
      }
      res.json({ series, truncated });
    });
  });

  // 终端日志（按写入顺序分页）
  router.get("/api/experiments/:id/logs", (req, res) => {
    handle(res, () => {
      const run = getRun(req, res);
      if (!run) return;
      const level = String(req.query.level ?? "").trim().toLowerCase();
      const limit = Math.max(0, Math.floor(Number(req.query.limit)) || 100);
      const offset = Math.max(0, Math.floor(Number(req.query.offset)) || 0);

      let logs = run.logs;
      if (level === "info" || level === "error") {
        logs = logs.filter((l) => l.level === level);
      }
      const total = logs.length;
      const items = logs.slice(offset, offset + limit).map((l) => ({
        line: l.line,
        level: l.level,
        timestamp: l.timestamp,
        epoch: l.epoch,
      }));
      res.json({ total, items });
    });
  });

  // 媒体列表
  router.get("/api/experiments/:id/media", (req, res) => {
    handle(res, () => {
      const run = getRun(req, res);
      if (!run) return;
      const items = run.media.map((m) => {
        const qs = `key=${encodeURIComponent(m.key)}&step=${encodeURIComponent(String(m.step))}&filename=${encodeURIComponent(m.filename)}`;
        return {
          key: m.key,
          step: m.step,
          filename: m.filename,
          caption: m.caption,
          size: m.size,
          type: m.type,
          url: `/api/experiments/${encodeURIComponent(run.id)}/media/file?${qs}`,
        };
      });
      res.json({ items });
    });
  });

  // 媒体文件字节流
  router.get("/api/experiments/:id/media/file", (req, res) => {
    handle(res, () => {
      const run = getRun(req, res);
      if (!run) return;
      const key = String(req.query.key ?? "");
      const step = Number(req.query.step);
      const filename = String(req.query.filename ?? "");
      // 只允许命中已解析出的媒体条目，文件名不直接取自用户输入，避免路径穿越
      const item = run.media.find((m) => m.key === key && m.step === step && m.filename === filename);
      if (!item) {
        res.status(404).json({ error: `媒体文件不存在: ${key}/${step}/${filename}` });
        return;
      }
      const filePath = path.join(run.dirPath, "media", item.type, item.filename);
      if (!fs.existsSync(filePath)) {
        res.status(404).json({ error: `媒体文件不存在: ${key}/${step}/${filename}` });
        return;
      }
      const data = fs.readFileSync(filePath);
      res.setHeader("Content-Type", contentTypeOf(item.filename));
      res.setHeader("Content-Length", data.length);
      res.end(data);
    });
  });

  return router;
}
