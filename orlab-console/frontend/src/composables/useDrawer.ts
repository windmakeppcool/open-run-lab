/**
 * 实验抽屉全局状态（轻量响应式共享，无需 Pinia）
 * 任意页面调用 openExperimentDrawer(id) 即可打开全局实验详情抽屉。
 */
import { reactive } from 'vue';

export const drawerState = reactive({
  open: false,
  experimentId: '',
});

/** 打开实验详情抽屉 */
export function openExperimentDrawer(id: string): void {
  drawerState.experimentId = id;
  drawerState.open = true;
}

/** 关闭实验详情抽屉 */
export function closeExperimentDrawer(): void {
  drawerState.open = false;
}
