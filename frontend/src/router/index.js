import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import WriteReviewView from '../views/WriteReviewView.vue'
import SalesView from '../views/SalesView.vue'

// ==================== 路由配置 ====================
// 各页面路由及权限控制
// 游客可访问: 首页、商品详情、公告
// 需要登录: 发布、商品管理、订单、评价、收藏、管理中心
const routes = [
      // 首页广场：浏览商品列表、搜索、热门推荐、价格趋势
    { path: '/', component: HomeView },
      // 登录/注册：支持三类角色选择、密码二次确认
    { path: '/login', component: () => import('../views/LoginView.vue') },
      // 商品详情：查看信息、购买、查看评价
    { path: '/item/:id', component: () => import('../views/ItemDetailView.vue') },
      // 系统公告：管理员发布的公告列表
    { path: '/announcements', component: () => import('../views/AnnouncementsView.vue') },
  // 必须需要登录验证权限的路由
      // 发布商品（商家）：农产品发布表单，含产地/规格/库存
    { path: '/publish', component: () => import('../views/PublishView.vue'), meta: { requiresAuth: true } },
      // 商品后台（商家）：商品管理、编辑、多条件检索、销售统计饼图
    { path: '/my-publishes', component: () => import('../views/MyPublishesView.vue'), meta: { requiresAuth: true } },
      // 我的订单（消费者）：查看购买记录、支付、确认收货、申请售后
    { path: '/my-purchases', component: () => import('../views/MyPurchasesView.vue'), meta: { requiresAuth: true } },
      // 销售订单（商家）：查看卖出记录、发货、处理售后
    { path: '/my-sales', component: SalesView, meta: { requiresAuth: true } },
      // 写评价（消费者）：对已完成的订单进行星级评分和留言
    { path: '/write-review/:purchaseId', component: () => import('../views/WriteReviewView.vue'), meta: { requiresAuth: true } },
      // 我的收藏（消费者）：查看收藏的商品
    { path: '/my-favorites', component: () => import('../views/MyFavoritesView.vue'), meta: { requiresAuth: true } },
      // 管理中心（管理员）：分类管理、商品强制下架、账号管理、发布公告
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