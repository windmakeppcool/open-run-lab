/**
 * 健康检查共享状态（一次获取，侧边栏 / 顶栏共用）
 */
import { reactive } from 'vue';
import { getHealth } from '../api';
import type { HealthInfo } from '../api/types';

export const healthState = reactive<{
  loaded: boolean;
  loading: boolean;
  data: HealthInfo | null;
  error: string | null;
}>({
  loaded: false,
  loading: false,
  data: null,
  error: null,
});

/** 触发一次健康检查（重复调用不会重复请求） */
export async function loadHealth(): Promise<void> {
  if (healthState.loading || healthState.loaded) {
    return;
  }
  healthState.loading = true;
  try {
    healthState.data = await getHealth();
    healthState.error = null;
  } catch (e) {
    healthState.error = e instanceof Error ? e.message : '数据源连接失败';
  } finally {
    healthState.loading = false;
    healthState.loaded = true;
  }
}
