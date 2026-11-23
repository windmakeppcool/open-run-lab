#!/usr/bin/env bash
# OpenRunLab 纯本地一键启动脚本
# 同时启动 orlab-console 后端（8787）与前端（5173）
# 用法：bash scripts/start-local.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/orlab-console/backend"
FRONTEND="$ROOT/orlab-console/frontend"
BACKEND_PORT="${PORT:-8787}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
HEALTH_URL="http://127.0.0.1:${BACKEND_PORT}/api/health"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  trap - EXIT INT TERM
  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if [ ! -d "$BACKEND" ] || [ ! -d "$FRONTEND" ]; then
  echo "未找到 orlab-console 前后端目录" >&2
  exit 1
fi

bash "$ROOT/scripts/check-env.sh" || exit 1

if [ ! -d "$BACKEND/node_modules" ]; then
  echo "安装后端依赖..."
  (cd "$BACKEND" && npm ci) || exit 1
fi
if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "安装前端依赖..."
  (cd "$FRONTEND" && npm ci) || exit 1
fi

echo "启动后端：http://127.0.0.1:${BACKEND_PORT}"
(cd "$BACKEND" && PORT="$BACKEND_PORT" npm run dev) &
BACKEND_PID=$!

for _ in $(seq 1 60); do
  if command -v curl >/dev/null 2>&1; then
    curl -sf "$HEALTH_URL" >/dev/null 2>&1 && break
  else
    python3 - "$BACKEND_PORT" <<'PY' >/dev/null 2>&1 && break
import socket, sys
s = socket.socket(); s.settimeout(0.3)
s.connect(("127.0.0.1", int(sys.argv[1])))
PY
  fi
  sleep 1
done

if command -v curl >/dev/null 2>&1; then
  if ! curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
    echo "后端健康检查失败：$HEALTH_URL" >&2
    exit 1
  fi
fi
echo "后端已就绪：$HEALTH_URL"

echo "启动前端：http://localhost:${FRONTEND_PORT}"
(cd "$FRONTEND" && npm run dev -- --port "$FRONTEND_PORT") &
FRONTEND_PID=$!

echo "按 Ctrl+C 停止。"
wait "$FRONTEND_PID"
