<template>
  <div class="admin-container">
    <h2 style="color: var(--danger-color); margin-bottom: 30px;">⚙️ 后台管理中心 <span style="font-size:0.5em;color:#999;">(Admin Only)</span></h2>
    
    <div style="display: flex; gap: 30px; flex-wrap: wrap;">
      <!-- 分类管理 -->
      <div class="admin-panel" style="flex: 1; min-width: 250px;">
        <h3>📁 商品分类管理</h3>
        <ul class="cat-list">
          <li v-for="cat in categories" :key="cat.id">
            <span>{{ cat.name }}</span>
            <button @click="deleteCategory(cat.id)" class="icon-btn" title="删除">🗑️</button>
          </li>
        </ul>
        <div style="display: flex; gap: 10px; margin-top:20px;">
          <input v-model="newCategory" placeholder="新增类别名..." style="flex:1;">
          <button @click="addCategory" class="btn bg-blue">添加类别</button>
        </div>
      </div>

      <!-- 全局商品管理 (下架权) -->
      <div class="admin-panel" style="flex: 2; min-width: 400px;">
        <h3>🔨 全局商品状态强制管理</h3>
        <table class="admin-table" style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 2px solid #ddd;"><th>ID</th><th>标题</th><th>商家</th><th>状态</th><th>强制操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id" style="border-bottom: 1px solid #eee;">
              <td style="padding: 10px;">{{ item.id }}</td>
              <td>{{ item.title }}</td>
            <td>{{ item.owner_name }}</td>
            <td>
              <span v-if="item.status === 1" class="status-tag status-green">售卖中</span>
              <span v-else-if="item.status === 2" class="status-tag status-blue">已售出</span>
              <span v-else class="status-tag status-orange">强制下架</span>
            </td>
            <td>
              <button v-if="item.status === 1" @click="forceTakeDown(item.id)" class="btn bg-orange">违规强制下架</button>
              <button v-if="item.status === 3" @click="relistItem(item.id)" class="btn bg-green">重新上架</button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>

      <!-- 账号管理 -->
      <div class="admin-panel" style="flex: 1; min-width: 300px;">
        <h3>👥 平台账号管理</h3>
        <table class="admin-table" style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 2px solid #ddd;"><th>用户名</th><th>角色</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id" style="border-bottom: 1px solid #eee;">
              <td style="padding: 10px;">{{ u.username }}</td>
              <td>{{ u.role === 'admin' ? '管理员' : '用户' }}</td>
              <td>
                <span :class="u.is_active ? 'status-tag status-green' : 'status-tag status-red'">{{ u.is_active ? '正常' : '已禁用' }}</span>
              </td>
              <td>
                <button v-if="u.role !== 'admin'" @click="toggleUser(u.id)" :class="u.is_active ? 'btn bg-red btn-small' : 'btn bg-green btn-small'">
                  {{ u.is_active ? '禁用' : '解禁' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 增加：发布系统公告 -->
    <div class="admin-panel" style="margin-top: 30px;">
      <h3>📢 发布系统公告 <span style="font-size:0.6em;color:var(--text-muted)">(全站可见)</span></h3>
      <div style="display: flex; flex-direction: column; gap: 15px; max-width: 600px;">
        <input v-model="announcement.title" placeholder="公告标题..." required />
        <textarea v-model="announcement.content" placeholder="公告内容..." rows="4" required></textarea>
        
        <div style="display: flex; align-items: center; gap: 10px;">
          <label style="font-weight:bold; color: var(--text-muted)">上传配图: </label>
          <input type="file" @change="uploadAnnounceImage" accept="image/*" style="border: none; padding: 0;" />
        </div>
        <div v-if="announcement.images.length > 0" style="display: flex; gap:10px; flex-wrap: wrap;">
          <div v-for="(img, index) in announcement.images" :key="index" style="position: relative; display: inline-block;">
            <img :src="img" style="width: 80px; height: 80px; object-fit: cover; border-radius: 4px; border: 1px solid #eee;">
            <button type="button" @click="removeAnnounceImage(index)" style="position: absolute; top: -5px; right: -5px; background: red; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer; font-size: 12px; line-height: 1; display:flex; align-items:center; justify-content:center; padding:0;">×</button>
          </div>
        </div>

        <button @click="publishAnnouncement" class="btn bg-blue" style="width: 120px;">确认发布公告</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const categories = ref([])
const items = ref([])
const users = ref([])
const newCategory = ref('')
const announcement = ref({ title: '', content: '', images: [] }) // images 用于本地预览URL
const announceFiles = ref([]) // 存储待上传的真实文件对象
const token = localStorage.getItem('token')

const loadData = async () => {
    // 载入分类
    const resCat = await fetch('http://localhost:8000/api/categories')
    categories.value = await resCat.json()

    // 载入所有商品进行强制管理
    const resItem = await fetch('http://localhost:8000/api/admin/all-items')
    items.value = await resItem.json()

    // 载入所有用户列表
    const resUsers = await fetch('http://localhost:8000/api/admin/users', {
        headers: { 'Authorization': token }
    })
    if(resUsers.ok) users.value = await resUsers.json()
}

const addCategory = async () => {
    if(!newCategory.value) return 
    const res = await fetch('http://localhost:8000/api/categories', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': token
        },
        body: JSON.stringify({ name: newCategory.value })
    })
    if(res.ok) {
        newCategory.value = ''
        loadData()
    } else {
        alert("添加分类失败")
    }
}

const deleteCategory = async (cat_id) => {
    if(!confirm("确定要删除这个分类吗？")) return;
    const res = await fetch(`http://localhost:8000/api/categories/${cat_id}`, {
        method: 'DELETE',
        headers: { 'Authorization': token }
    })
    if(res.ok) {
        loadData()
    } else {
        alert("删除失败，可能该分类正在被使用或无权限")
    }
}

const removeAnnounceImage = (index) => {
    announcement.value.images.splice(index, 1)
    announceFiles.value.splice(index, 1)
}

const uploadAnnounceImage = async (e) => {
    const file = e.target.files[0]
    if(!file) return

    e.target.value = ''
    
    // 生成前端临时预览地址，点击“发布公告”时才发往后端
    announcement.value.images.push(URL.createObjectURL(file))
    announceFiles.value.push(file)
}

const publishAnnouncement = async () => {
    if(!announcement.value.title || !announcement.value.content) return alert("标题和内容必填")
    
    // 遍历并发起正式的图片上传请求
    const uploadedUrls = []
    for(const file of announceFiles.value) {
        const formData = new FormData()
        formData.append('file', file)
        const uploadRes = await fetch('http://localhost:8000/api/upload', {
            method: 'POST',
            body: formData
        })
        if(uploadRes.ok) {
            const data = await uploadRes.json()
            uploadedUrls.push(data.url)
        } else {
            return alert("图片上传给服务器时发生错误")
        }
    }

    const res = await fetch('http://localhost:8000/api/announcements', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': token 
        },
        body: JSON.stringify({
            title: announcement.value.title,
            content: announcement.value.content,
            images: JSON.stringify(uploadedUrls)
        })
    })
    
    if(res.ok) {
        alert("公告发布成功！")
        announcement.value = { title: '', content: '', images: [] }
        announceFiles.value = []
    } else {
        alert("发布失败！")
    }
}

const forceTakeDown = async (item_id) => {
    if(!confirm("强制下架不会赔偿商家，是否确认？")) return;
    // 使用原先就写好的批量状态修改接口，但仅勾选1个
    const res = await fetch('http://localhost:8000/api/items/batch-status', {
        method: 'PUT',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': token 
        },
        body: JSON.stringify({ item_ids: [item_id], status: 3 })
    })
    if(res.ok) {
        alert("下架成功！")
        loadData()
    } else {
        const data = await res.json()
        alert("下架失败: " + (data.detail || "未知错误"))
    }
}

const relistItem = async (item_id) => {
    if(!confirm("确定要为该商品解除限制并重新上架吗？")) return;
    const res = await fetch('http://localhost:8000/api/items/batch-status', {
        method: 'PUT',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': token 
        },
        body: JSON.stringify({ item_ids: [item_id], status: 1 })
    })
    if(res.ok) {
        alert("重新上架成功！")
        loadData()
    } else {
        const data = await res.json()
        alert("操作失败: " + (data.detail || "未知错误"))
    }
}

const toggleUser = async (userId) => {
    if(!confirm("确定要修改该账号的使用状态吗？")) return;
    const res = await fetch(`http://localhost:8000/api/admin/users/${userId}/toggle-status`, {
        method: 'PUT',
        headers: { 'Authorization': token }
    });
    if(res.ok) {
        alert("更改状态成功");
        loadData();
    } else {
        const data = await res.json();
        alert("操作失败: " + data.detail);
    }
}

onMounted(loadData)
</script>

<style scoped>
.admin-container {
  padding: 10px;
}
.admin-panel {
  background: var(--card-bg);
  padding: 24px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-sm);
}
.admin-panel h3 {
  margin-top: 0;
  border-bottom: 2px solid var(--bg-color);
  padding-bottom: 10px;
  margin-bottom: 20px;
}
.cat-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.cat-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  background: var(--bg-color);
  margin-bottom: 8px;
  transition: var(--transition);
}
.cat-list li:hover {
  background: #e4e7eb;
}
.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  transition: transform 0.2s;
}
.icon-btn:hover {
  transform: scale(1.2);
}
.status-tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: bold;
}
.status-green { background: rgba(76, 175, 80, 0.1); color: var(--primary-color); }
.status-blue { background: rgba(33, 150, 243, 0.1); color: var(--secondary-color); }
.status-orange { background: rgba(255, 152, 0, 0.1); color: var(--warning-color); }
.status-red { background: rgba(244, 67, 54, 0.1); color: var(--danger-color); }
.btn-small { padding: 4px 10px; font-size: 0.9em; }
</style>
