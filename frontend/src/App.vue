<template>
  <div>
    <header class="nav">
      <div class="logo">农产品电商</div>
      <nav class="nav-links">
        <router-link to="/">首页广场</router-link>
        <router-link to="/announcements">系统公告</router-link>

        <!-- 根据登录状态显示不同导航 -->
        <template v-if="auth.token">
          <router-link v-if="auth.role==='farmer'" to="/publish">发布农产品</router-link>
          <router-link v-if="auth.role==='farmer'" to="/my-publishes">商品后台</router-link>
          <router-link v-if="auth.role==='farmer'" to="/my-sales">销售订单</router-link>
          <router-link v-if="auth.role==='consumer'" to="/my-purchases">我的订单</router-link>
          <router-link v-if="auth.role==='consumer'" to="/my-favorites">我的收藏</router-link>
          <router-link v-if="auth.role==='admin'" to="/admin-panel" style="color:red;">管理中心</router-link>
          <span style="margin-left:20px;display:flex;align-items:center;gap:8px;">
            <span style="background:#e8f5e9;padding:2px 8px;border-radius:4px;font-size:0.85em;color:#2e7d32;">{{ roleName }}</span>
            欢迎{{ auth.username }}
            <span v-if="auth.role==='farmer'" style="color:#FF9800;font-weight:bold;">(余额: ￥{{ auth.balance }})</span>
            <a href="#" @click.prevent="logout" style="color:gray;margin-left:10px;font-size:0.9em;">[退出]</a>
          </span>
</template>
        <template v-else>
          <router-link to="/login">登录/注册</router-link>
        </template>
      </nav>
    </header>
    <main style="padding: 20px;">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
import { reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const auth = reactive({
  token: '',
  username: '',
  role: '',
  balance: 0
})

const roleName = computed(() => {
  const map = {
    'farmer': '\u5546\u5bb6',
    'consumer': '\u6d88\u8d39\u8005',
    'admin': '\u7ba1\u7406\u5458'
  }
  return map[auth.role] || ''
})


onMounted(async () => {
  auth.token = localStorage.getItem('token') || ''
  const userId = localStorage.getItem('user_id')
  
  // 每次刷新请求最新余额与身份
  if(auth.token && userId) {
      try {
          const res = await fetch(`http://localhost:8000/api/me/${userId}`)
          if(res.ok) {
              const data = await res.json()
              auth.username = data.username
              auth.role = data.role
              auth.balance = data.balance
          } else {
              // 发生错误，清除登录状态
              localStorage.clear()
              auth.token = ''
              auth.role = ''
              router.push('/login')
          }
      } catch(e) {
          localStorage.clear()
          auth.token = ''
          router.push('/login')
      }
  }
})

const logout = () => {
  localStorage.clear()
  auth.token = ''
  auth.username = ''
  auth.role = ''
  router.push('/login')
  // 为了确保响应式立刻更新,强制刷新页面
  setTimeout(() => location.reload(), 100)
}
</script>

<style>
/* ================= 全局现代美化 ================= */
:root {
  --primary-color: #4CAF50;
  --primary-hover: #43A047;
  --secondary-color: #2196F3;
  --warning-color: #FF9800;
  --danger-color: #f44336;
  --bg-color: #f0f2f5;
  --card-bg: #ffffff;
  --text-main: #2c3e50;
  --text-muted: #606f7b;
  --border-radius: 12px;
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.1);
  --transition: all 0.3s ease;
}

body { 
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
  margin: 0; 
  background: var(--bg-color); 
  color: var(--text-main);
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 导航栏美化 */
.nav { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding: 12px 6%; 
  background: rgba(255, 255, 255, 0.9); 
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(0,0,0,0.05); 
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo { 
  font-weight: 800; 
  color: transparent; 
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  background-clip: text;
  -webkit-background-clip: text;
  font-size: 1.4rem; 
  letter-spacing: 0.5px;
}

.nav-links {
  display: flex;
  align-items: center;
}

.nav-links a { 
  margin-left: 20px; 
  text-decoration: none; 
  color: var(--text-muted); 
  font-weight: 600; 
  font-size: 0.95rem;
  transition: var(--transition);
  position: relative;
}

.nav-links a:hover {
  color: var(--primary-color);
}

.nav-links a.router-link-active { 
  color: var(--primary-color); 
}

.nav-links a.router-link-active::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 2px;
  background: var(--primary-color);
  border-radius: 2px;
}

/* 全局按钮美化 */
button, .btn {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  outline: none;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

button:hover, .btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
  filter: brightness(1.05);
}

button:active, .btn:active {
  transform: translateY(0);
}

/* 输入框统一美化 */
input, select, textarea {
  border: 1px solid #dcdfe6;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: var(--transition);
  outline: none;
  box-sizing: border-box;
}

input:focus, select:focus, textarea:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

/* 链接默认状态 */
a {
  color: var(--secondary-color);
  text-decoration: none;
  transition: var(--transition);
}
a:hover {
  filter: brightness(1.2);
}

/* 表格全局美化 (发布管理、购买等列表) */
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  background: var(--card-bg);
}
th {
  background: #f8f9fc;
  padding: 14px 12px;
  text-align: left;
  font-weight: 600;
  color: var(--text-muted);
  font-size: 0.9rem;
}
td {
  padding: 12px;
  border-top: 1px solid #eff2f5;
  color: var(--text-main);
  vertical-align: middle;
}
tr:hover td {
  background: #fbfdff;
}

/* 特殊功能类 */
.bg-green { background-color: var(--primary-color) !important; }
.bg-blue { background-color: var(--secondary-color) !important; }
.bg-orange { background-color: var(--warning-color) !important; }
.bg-red { background-color: var(--danger-color) !important; }

/* 弹窗遮罩美化 */
.modal-overlay {
  backdrop-filter: blur(4px);
}
.modal-content {
  border-radius: 12px !important;
  box-shadow: var(--shadow-md) !important;
  animation: modal-fade-in 0.3s ease;
}
@keyframes modal-fade-in {
  from { opacity: 0; transform: scale(0.95) translateY(-10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

main {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 30px 20px !important;
  box-sizing: border-box;
}
</style>