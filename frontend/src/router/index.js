import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import WriteReviewView from '../views/WriteReviewView.vue'
import SalesView from '../views/SalesView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/login', component: () => import('../views/LoginView.vue') },
  { path: '/item/:id', component: () => import('../views/ItemDetailView.vue') },
  { path: '/announcements', component: () => import('../views/AnnouncementsView.vue') },
  // 必须需要登录验证权限的路由
  { path: '/publish', component: () => import('../views/PublishView.vue'), meta: { requiresAuth: true } },
  { path: '/my-publishes', component: () => import('../views/MyPublishesView.vue'), meta: { requiresAuth: true } },
  { path: '/my-purchases', component: () => import('../views/MyPurchasesView.vue'), meta: { requiresAuth: true } },
  { path: '/my-sales', component: SalesView, meta: { requiresAuth: true } },
  { path: '/write-review/:purchaseId', component: () => import('../views/WriteReviewView.vue'), meta: { requiresAuth: true } },
  { path: '/my-favorites', component: () => import('../views/MyFavoritesView.vue'), meta: { requiresAuth: true } },
  { path: '/admin-panel', component: () => import('../views/AdminPanelView.vue'), meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    alert("该页面需要登录权限控制，请先登录！")
    next('/login')
  } else {
    next()
  }
})

export default router