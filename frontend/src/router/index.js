import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/views/Home.vue') },
      { path: 'books/:id', name: 'book', component: () => import('@/views/BookDetail.vue') },
      { path: 'publish', name: 'publish', component: () => import('@/views/BookForm.vue'), meta: { requiresAuth: true } },
      {
        path: 'books/:id/edit',
        name: 'edit-book',
        component: () => import('@/views/BookForm.vue'),
        meta: { requiresAuth: true },
      },
      { path: 'me', name: 'profile', component: () => import('@/views/user/Profile.vue'), meta: { requiresAuth: true } },
      { path: 'login', name: 'login', component: () => import('@/views/Login.vue') },
      { path: 'register', name: 'register', component: () => import('@/views/Register.vue') },
      {
        path: 'admin',
        component: () => import('@/views/admin/AdminLayout.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
        redirect: { name: 'admin-books' },
        children: [
          { path: 'books', name: 'admin-books', component: () => import('@/views/admin/BookReview.vue') },
          { path: 'users', name: 'admin-users', component: () => import('@/views/admin/Users.vue') },
          { path: 'categories', name: 'admin-categories', component: () => import('@/views/admin/Categories.vue') },
          { path: 'borrows', name: 'admin-borrows', component: () => import('@/views/admin/BorrowRecords.vue') },
          { path: 'returns', name: 'admin-returns', component: () => import('@/views/admin/ReturnRecords.vue') },
        ],
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const store = useUserStore()
  if (to.matched.some((r) => r.meta.requiresAuth) && !store.isLogin) {
    ElMessage.warning('请先登录')
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.matched.some((r) => r.meta.requiresAdmin) && !store.isAdmin) {
    ElMessage.error('无管理员权限')
    return { name: 'home' }
  }
  if ((to.name === 'login' || to.name === 'register') && store.isLogin) {
    return { name: 'home' }
  }
})

export default router
