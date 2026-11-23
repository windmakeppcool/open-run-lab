/**
 * 路由配置：工作台 / 项目空间 / 实验记录 / 实验对比 / 用户与权限
 */
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'overview',
      component: () => import('../views/OverviewView.vue'),
      meta: { title: '工作台' },
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('../views/ProjectsView.vue'),
      meta: { title: '项目空间' },
    },
    {
      path: '/experiments',
      name: 'experiments',
      component: () => import('../views/ExperimentsView.vue'),
      meta: { title: '实验记录' },
    },
    {
      path: '/compare',
      name: 'compare',
      component: () => import('../views/CompareView.vue'),
      meta: { title: '实验对比' },
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('../views/UsersView.vue'),
      meta: { title: '用户与权限' },
    },
    // 未匹配路径回到工作台
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
});

export default router;
