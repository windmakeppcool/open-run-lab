/**
 * 通用格式化工具：时间戳本地时区展示、时长人性化、数值展示。
 */

/** 补零 */
function pad(n: number): string {
  return String(n).padStart(2, '0');
}

/** 时间戳格式化为本地时区字符串，缺省返回 — */
export function formatDateTime(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return '—';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/** 秒数人性化（如 4分12秒 / 1小时3分5秒），缺省返回 — */
export function formatDuration(sec: number | null | undefined): string {
  if (sec === null || sec === undefined || !Number.isFinite(sec)) {
    return '—';
  }
  const total = Math.max(0, Math.round(sec));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  if (hours > 0) {
    return `${hours}小时${minutes}分${seconds}秒`;
  }
  if (minutes > 0) {
    return `${minutes}分${seconds}秒`;
  }
  return `${seconds}秒`;
}

/** 数值展示（保留有效数字，缺省返回 —） */
export function formatNumber(value: number | null | undefined, digits = 4): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return '—';
  }
  if (value !== 0 && (Math.abs(value) >= 1e6 || Math.abs(value) < 1e-4)) {
    return value.toExponential(2);
  }
  // 去掉多余的小数尾零
  return String(Number(value.toFixed(digits)));
}

/** 文件大小人性化 */
export function formatSize(size: number | null | undefined): string {
  if (size === null || size === undefined || !Number.isFinite(size) || size < 0) {
    return '—';
  }
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}
