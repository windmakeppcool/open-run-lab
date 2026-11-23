/**
 * 服务入口：组装 Express 应用并启动 HTTP 服务。
 * 端口默认 8787（env PORT 可覆盖）；orlab-log 目录默认 ../testdata/orlab-log（env ORLAB_LOGDIR 可覆盖）。
 */
import * as path from "path";
import cors from "cors";
import express from "express";
import { createRouter } from "./routes";
import { RunStore } from "./orlab/reader";

/** orlab-log 目录：env ORLAB_LOGDIR 优先，否则取 backend 包目录的 ../testdata/orlab-log */
const ORLAB_LOGDIR = process.env.ORLAB_LOGDIR
  ? path.resolve(process.env.ORLAB_LOGDIR)
  : path.resolve(__dirname, "../../testdata/orlab-log");

const PORT = Number(process.env.PORT) || 8787;

// 启动时扫描 ORLAB_LOGDIR 下的 run-* 目录，请求时懒加载并缓存
const store = new RunStore(ORLAB_LOGDIR);

const app = express();
app.use(cors()); // 允许任意来源
app.use(express.json());
app.use(createRouter(store));

// 兜底 404：未匹配的路由
app.use((_req, res) => {
  res.status(404).json({ error: "接口不存在" });
});

app.listen(PORT, () => {
  console.log(`orlab-console backend 已启动: http://127.0.0.1:${PORT} (orlab-log: ${ORLAB_LOGDIR})`);
});
