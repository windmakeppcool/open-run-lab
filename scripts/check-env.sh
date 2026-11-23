#!/usr/bin/env bash
# OpenRunLab 纯本地环境校验工具
# 用法：bash scripts/check-env.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/orlab-console/backend"
FRONTEND="$ROOT/orlab-console/frontend"
PROTOS_DIR="${ORLAB_PROTOS_DIR:-$ROOT/protos}"
ORLAB_LOGDIR="${ORLAB_LOGDIR:-$ROOT/orlab-console/testdata/orlab-log}"
BACKEND_PORT="${PORT:-8787}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

FAILED=0
WARNED=0

ok()   { printf '  [OK]   %s\n' "$1"; }
warn() { printf '  [WARN] %s\n' "$1"; WARNED=$((WARNED + 1)); }
fail() { printf '  [FAIL] %s\n' "$1"; FAILED=$((FAILED + 1)); }

section() { printf '\n%s\n' "$1"; }

section "1. 运行时版本"

if command -v python3 >/dev/null 2>&1; then
  PY_VER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "0.0")"
  PY_MAJOR="${PY_VER%%.*}"
  PY_MINOR="${PY_VER##*.}"
  if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 9 ]; then
    ok "python3 $PY_VER (>= 3.9)"
  else
    fail "python3 $PY_VER 版本过低，需要 >= 3.9"
  fi
else
  fail "未找到 python3（仅使用控制台时可以不安装）"
fi

if command -v node >/dev/null 2>&1; then
  NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
  if [ "$NODE_MAJOR" -ge 18 ]; then
    ok "node $(node -v) (>= 18)"
  else
    fail "node $(node -v) 版本过低，需要 >= 18"
  fi
else
  fail "未找到 node，需要 Node.js >= 18"
fi

if command -v npm >/dev/null 2>&1; then
  ok "npm $(npm -v)"
else
  fail "未找到 npm"
fi

section "2. 仓库资源"

if [ -d "$PROTOS_DIR" ]; then
  ok "proto 定义目录存在：$PROTOS_DIR"
else
  fail "proto 定义目录不存在：$PROTOS_DIR"
fi

if [ -d "$ORLAB_LOGDIR" ]; then
  ok "实验数据目录存在：$ORLAB_LOGDIR"
elif mkdir -p "$ORLAB_LOGDIR" 2>/dev/null; then
  ok "已创建实验数据目录：$ORLAB_LOGDIR"
else
  fail "无法创建实验数据目录：$ORLAB_LOGDIR"
fi

if [ -f "$BACKEND/package.json" ] && [ -f "$FRONTEND/package.json" ]; then
  ok "控制台前后端 package.json 存在"
else
  fail "控制台前后端 package.json 缺失"
fi

section "3. 控制台依赖"

if [ -d "$BACKEND/node_modules" ]; then
  ok "后端依赖已安装"
else
  warn "后端依赖未安装，请执行：cd orlab-console/backend && npm ci"
fi

if [ -d "$FRONTEND/node_modules" ]; then
  ok "前端依赖已安装"
else
  warn "前端依赖未安装，请执行：cd orlab-console/frontend && npm ci"
fi

section "4. 端口占用"

check_port() {
  local port="$1" name="$2"
  if python3 - "$port" <<'PY' >/dev/null 2>&1
import socket, sys
s = socket.socket()
s.settimeout(0.3)
try:
    s.connect(("127.0.0.1", int(sys.argv[1])))
except OSError:
    sys.exit(1)
sys.exit(0)
PY
  then
    warn "$name 端口 $port 已被占用"
  else
    ok "$name 端口 $port 可用"
  fi
}

if command -v python3 >/dev/null 2>&1; then
  check_port "$BACKEND_PORT" "后端"
  check_port "$FRONTEND_PORT" "前端"
else
  warn "缺少 python3，跳过端口检测"
fi

section "5. 外部服务依赖"

ok "未检测到 Docker / 云数据库 / 云消息队列依赖（纯本地运行）"

printf '\n----------------------------------------\n'
if [ "$FAILED" -gt 0 ]; then
  printf '环境校验失败：%d 项错误，%d 项警告\n' "$FAILED" "$WARNED"
  exit 1
fi
printf '环境校验通过（%d 项警告）\n' "$WARNED"
exit 0
