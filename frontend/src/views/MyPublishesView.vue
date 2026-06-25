<template>
  <div class="publish-container">
    <h2 style="margin-bottom:20px; color:var(--text-main);">商品后台</h2>

    <!-- 销量统计 -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px;margin-bottom:20px;">
      <div style="background:var(--card-bg);padding:15px;border-radius:8px;box-shadow:var(--shadow-sm);text-align:center;">
        <div style="font-size:1.8em;font-weight:bold;color:var(--primary-color);">{{stats.active_products}}</div>
        <div style="font-size:0.85em;color:var(--text-muted);">在售商品</div>
      </div>
      <div style="background:var(--card-bg);padding:15px;border-radius:8px;box-shadow:var(--shadow-sm);text-align:center;">
        <div style="font-size:1.8em;font-weight:bold;color:var(--secondary-color);">{{stats.sold_products}}</div>
        <div style="font-size:0.85em;color:var(--text-muted);">已售商品</div>
      </div>
      <div style="background:var(--card-bg);padding:15px;border-radius:8px;box-shadow:var(--shadow-sm);text-align:center;">
        <div style="font-size:1.8em;font-weight:bold;color:var(--warning-color);">{{stats.total_orders}}</div>
        <div style="font-size:0.85em;color:var(--text-muted);">订单总数</div>
      </div>
      <div style="background:var(--card-bg);padding:15px;border-radius:8px;box-shadow:var(--shadow-sm);text-align:center;">
        <div style="font-size:1.8em;font-weight:bold;color:var(--danger-color);">￥{{stats.total_revenue}}</div>
        <div style="font-size:0.85em;color:var(--text-muted);">总营收</div>
      </div>
    </div>

    <!-- 销售饼图 -->
    <div style="background:var(--card-bg);padding:20px;border-radius:8px;box-shadow:var(--shadow-sm);margin-bottom:20px;">
      <h3 style="margin:0 0 15px 0;color:var(--text-main);">单品销售统计饼图</h3>
      <div id="salesPieChart" style="width:100%;height:300px;"></div>
    </div>

    <!-- 多条件检索 -->
    <div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;background:var(--card-bg);padding:15px;border-radius:8px;box-shadow:var(--shadow-sm);align-items:center;">
      <input v-model="filterKeyword" placeholder="商品名称" style="flex:1;min-width:120px;padding:8px;border:1px solid #ddd;border-radius:4px;">
      <select v-model="filterCatId" style="padding:8px;border:1px solid #ddd;border-radius:4px;">
        <option value="0">全部分类</option>
        <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
      </select>
      <input v-model="filterOrigin" placeholder="产地" style="width:100px;padding:8px;border:1px solid #ddd;border-radius:4px;">
      <input v-model="filterMinPrice" type="number" placeholder="最低价" style="width:90px;padding:8px;border:1px solid #ddd;border-radius:4px;">
      <input v-model="filterMaxPrice" type="number" placeholder="最高价" style="width:90px;padding:8px;border:1px solid #ddd;border-radius:4px;">
      <button @click="load" class="btn bg-green" style="padding:8px 16px;">检索</button>
      <button @click="resetFilters" class="btn" style="background:#e2e8f0;color:#333;padding:8px 16px;">重置</button>
    </div>
    <div style="margin-bottom: 20px; display: flex; gap: 15px;">
      <button @click="batchUpdateStatus(1)" class="btn bg-green">批量上架</button>
      <button @click="batchUpdateStatus(2)" class="btn bg-blue">批量标记已售出</button>
      <button @click="batchUpdateStatus(3)" class="btn bg-orange">批量下架</button>
    </div>
    
    <table class="publish-table">
      <thead>
        <tr style="border-bottom: 2px solid #ddd;">
          <th style="padding: 10px;"><input type="checkbox" @change="toggleAll" :checked="selected.length === items.length && items.length > 0"/> 全选</th>
          <th>商品图片</th>
          <th>标题</th>
          <th>价格</th>
          <th>状态</th>
          <th>库存</th><th>产地</th><th>规格</th><th>浏览量</th>
          <th>发布时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td style="padding: 10px; width: 60px;"><input v-if="item.status === 1" type="checkbox" :value="item.id" v-model="selected" style="transform: scale(1.2);"/></td>
          <td>
            <img :src="getCover(item.images)" alt="cover" @click="previewImage = getCover(item.images)" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px; box-shadow: var(--shadow-sm); cursor: zoom-in;" v-if="getCover(item.images)">
            <span v-else style="color:var(--text-muted); font-size:0.85em; background:var(--bg-color); padding: 4px 8px; border-radius: 4px;">无图</span>
          </td>
          <td style="font-weight: 500;">{{ item.title }}</td>
          <td style="color: var(--danger-color); font-weight: bold; font-size: 1.1em;">￥{{ item.price }}</td>
          <td>
            <span class="status-tag" :class="item.status === 1 ? 'status-green' : (item.status === 2 ? 'status-blue' : 'status-orange')">
              {{ item.status === 1 ? '售卖中' : (item.status === 2 ? '已售出' : '已下架') }}
            </span>
          </td>
          <td style="color:var(--text-muted)">👁 {{ item.stock }}</td><td>{{ item.origin || "-" }}</td><td>{{ item.specification || "-" }}</td><td>{{ item.views }}</td>
          <td style="color:var(--text-muted)">{{ item.created_at.split(' ')[0] }}</td>
          <td>
            <button v-if="item.status === 1" @click="openEditModal(item)" class="btn bg-blue btn-action">修改</button>
            <button v-if="item.status === 1 || item.status === 2" @click="deleteItem(item.id)" class="btn bg-red btn-action">删除</button>
          </td>
        </tr>
        <tr v-if="items.length === 0">
          <td colspan="8" style="text-align: center; padding: 20px; color: gray;">暂无发布的商品</td>
        </tr>
      </tbody>
    </table>

    <!-- 编辑模态框 -->
    <div v-if="editingItem" class="modal-overlay">
      <div class="modal-content">
        <h3>修改商品信息</h3>
        <div style="margin-bottom: 10px;">
          <label>类别：</label>
          <select v-model="editForm.category_id" style="width: 100%; padding: 8px; margin-top: 5px;">
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
        </div>
        <div style="margin-bottom: 10px;">
          <label>价格：</label>
          <input type="number" v-model="editForm.price" style="width: 100%; padding: 8px; margin-top: 5px;">
        </div>
        <div style="margin-bottom: 20px;">
          <label>描述：</label>
          <textarea v-model="editForm.description" rows="4" style="width: 100%; padding: 8px; margin-top: 5px;"></textarea>
        <div style="margin-bottom:10px;">
          <label>产地</label><input v-model="editForm.origin" style="width:100%;padding:8px;margin-top:5px;">
        </div>
        <div style="margin-bottom:10px;">
          <label>规格</label><input v-model="editForm.specification" style="width:100%;padding:8px;margin-top:5px;">
        </div>
        <div style="margin-bottom:10px;">
          <label>库存</label><input type="number" min="0" v-model="editForm.stock" style="width:100%;padding:8px;margin-top:5px;">
        </div>
        <div style="margin-bottom:10px;">
          <label>商品图片：</label>
          <input type="file" @change="editUploadImage" accept="image/*" style="width:100%;margin-top:5px;">
          <div v-if="editImages.length > 0" style="margin-top:10px;display:flex;gap:10px;flex-wrap:wrap;">
            <div v-for="(img, idx) in editImages" :key="idx" style="position:relative;">
              <img :src="img" style="width:60px;height:60px;object-fit:cover;border-radius:4px;border:1px solid #eee;">
              <button type="button" @click="removeEditImage(idx)" style="position:absolute;top:-5px;right:-5px;background:red;color:white;border:none;border-radius:50%;width:18px;height:18px;cursor:pointer;font-size:10px;line-height:1;">×</button>
            </div>
          </div>
        </div>
        </div>
        <div style="text-align: right;">
          <button @click="editingItem = null" class="btn bg-orange" style="margin-right: 10px;">取消</button>
          <button @click="saveEdit" class="btn bg-green">保存</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 图片预览模态框 -->
  <div v-if="previewImage" class="preview-modal" @click="previewImage = null">
      <img :src="previewImage" @click.stop />
      <button class="close-preview" @click="previewImage = null">×</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

import * as echarts from 'echarts'

const items = ref([])
const filterKeyword = ref('')
const filterOrigin = ref('')
const filterCat = ref('')
const filterCatId = ref(0)
const filterMinPrice = ref('')
const filterMaxPrice = ref('')
const selected = ref([])
const categories = ref([])
const stats = ref({total_products:0, active_products:0, sold_products:0, total_orders:0, total_revenue:0})
const editingItem = ref(null)
const editForm = ref({
    title: '',
    description: '',
    price: 0,
    origin: '',
    specification: '',
    stock: 0,
    category_id: null,
    user_id: 0,
    images: '[]'
})
const userId = localStorage.getItem('user_id')
const editImages = ref([])
const editImageFiles = ref([])
const previewImage = ref(null)

const load = async () => {
    try {
        let url = `http://localhost:8000/api/users/${userId}/items`
        const params = []
        if(filterKeyword.value) params.push('keyword=' + encodeURIComponent(filterKeyword.value))
        if(filterOrigin.value) params.push('origin=' + encodeURIComponent(filterOrigin.value))
        if(filterCatId.value > 0) params.push('category_id=' + filterCatId.value)
        if(filterMinPrice.value) params.push('min_price=' + filterMinPrice.value)
        if(filterMaxPrice.value) params.push('max_price=' + filterMaxPrice.value)
        if(params.length) url += '?' + params.join('&')
        const res = await fetch(url)
        items.value = await res.json()
        selected.value = []

        const resCat = await fetch('http://localhost:8000/api/categories')
        categories.value = await resCat.json()

        // Load stats
        try {
            const s = await fetch('http://localhost:8000/api/merchant/stats/' + userId)
            if(s.ok) stats.value = await s.json()
        } catch(e) {}
    } catch (e) {
        console.error(e)
    }
}

const getCover = (imagesJson) => {
    try {
        const arr = JSON.parse(imagesJson)
        return arr.length > 0 ? arr[0] : null
    } catch { return null }
}

const deleteItem = async (id) => {
    if(!confirm('确定永久删除该商品吗？')) return
    await fetch(`http://localhost:8000/api/items/${id}`, { method: 'DELETE' })
    load()
}

const batchUpdateStatus = async (status) => {
    if(!selected.value.length) return alert('请先勾选需要操作的商品')
    const res = await fetch('http://localhost:8000/api/items/batch-status', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': localStorage.getItem('token') || '' },
        body: JSON.stringify({ item_ids: selected.value, status })
    })
    const data = await res.json()
    alert(data.message || '批量修改成功')
    load()
}

const toggleAll = (e) => {
    selected.value = e.target.checked ? items.value.map(i => i.id) : []
}

const openEditModal = (item) => {
    editingItem.value = item.id
    editImages.value = JSON.parse(item.images || "[]")
    editForm.value = {
        title: item.title,
        description: item.description,
        price: parseFloat(item.price),
        origin: item.origin || '',
        specification: item.specification || '',
        stock: item.stock || 0,
        category_id: item.category_id,
        user_id: parseInt(userId),
        images: item.images || '[]'
    }
}

const editUploadImage = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    e.target.value = ""
    const formData = new FormData()
    formData.append("file", file)
    try {
        const res = await fetch("http://localhost:8000/api/upload", { method: "POST", body: formData })
        if (res.ok) {
            const data = await res.json()
            editImages.value.push(data.url)
            const images = JSON.parse(editForm.value.images || "[]")
            images.push(data.url)
            editForm.value.images = JSON.stringify(images)
        }
    } catch(e) { console.error(e) }
}

const removeEditImage = (idx) => {
    editImages.value.splice(idx, 1)
    const images = JSON.parse(editForm.value.images || "[]")
    images.splice(idx, 1)
    editForm.value.images = JSON.stringify(images)
}

const saveEdit = async () => {
    try {
        const res = await fetch(`http://localhost:8000/api/items/${editingItem.value}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(editForm.value)
        })
        if (res.ok) {
            alert('修改成功')
            editingItem.value = null
            load()
        } else {
            const data = await res.json()
            alert('修改失败: ' + (data.detail || '未知原因'))
        }
    } catch (e) {
        console.error(e)
        alert('网络错误')
    }
}

const resetFilters = () => {
    filterKeyword.value = ''
    filterOrigin.value = ''
    filterCatId.value = 0
    filterMinPrice.value = ''
    filterMaxPrice.value = ''
    load()
}

const loadSalesChart = async () => {
    try {
        const r = await fetch('http://localhost:8000/api/merchant/item-sales/' + userId)
        if(!r.ok) return
        const data = await r.json()
        const chartDom = document.getElementById('salesPieChart')
        if(!chartDom) return
        const myChart = echarts.init(chartDom)
        const top5 = data.slice(0, 5)
        const others = data.slice(5)
        const otherSum = others.reduce((s, x) => s + (x.total_revenue || 0), 0)
        const pieData = top5.map(x => ({name: x.title, value: x.total_revenue}))
        if(otherSum > 0) pieData.push({name: '其他', value: otherSum})
        myChart.setOption({
            tooltip: {trigger: 'item', formatter: '{b}: ￥{c} ({d}%)'},
            series: [{
                type: 'pie', radius: '60%', center: ['50%', '50%'],
                data: pieData,
                label: {formatter: '{b}: ￥{c}'},
                emphasis: {itemStyle: {shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)'}}
            }]
        })
        window.addEventListener('resize', () => myChart.resize())
    } catch(e) { console.error(e) }
}

onMounted(() => {
    load()
    setTimeout(loadSalesChart, 200)
})
</script>

<style scoped>
.publish-container {
  background: transparent;
  padding: 0;
}
.btn-action {
  padding: 6px 12px;
  font-size: 0.9em;
  margin-right: 8px;
}
.status-tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.85em;
  font-weight: bold;
}
.status-green { background: rgba(76, 175, 80, 0.1); color: var(--primary-color); }
.status-blue { background: rgba(33, 150, 243, 0.1); color: var(--secondary-color); }
.status-orange { background: rgba(255, 152, 0, 0.1); color: var(--warning-color); }

.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.modal-content {
  background: var(--card-bg);
  padding: 30px;
  border-radius: 12px;
  width: 450px;
  box-shadow: var(--shadow-md);
}
.modal-content h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: var(--text-main);
  border-bottom: 2px solid var(--bg-color);
  padding-bottom: 10px;
}
.preview-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 9999; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(5px); }
.preview-modal img { max-width: 90%; max-height: 90vh; object-fit: contain; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
.close-preview { position: absolute; top: 20px; right: 30px; background: #fff; color: #333; border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 24px; cursor: pointer; font-weight: bold; line-height: 40px; text-align: center; }
</style>
