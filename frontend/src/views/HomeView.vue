<template>
  <div>
    <div class="filters">
      <input v-model="query.keyword" placeholder="搜索农产品名称..." />
      <select v-model="query.categoryId" style="padding: 5px; border-radius: 4px; border: 1px solid #ccc;">
        <option value="">全部分类</option>
        <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
      </select>
      <PriceSlider v-model:min="query.minPrice" v-model:max="query.maxPrice" />
      <DatePicker v-model:start="query.startDate" v-model:end="query.endDate" />
      <button @click="fetchData">组合搜索</button>
      <button @click="exportData" style="background: #2196F3;">导出数据(CSV)</button>
    </div>

    <div style="display: flex; gap: 20px; margin-bottom: 20px;">
      <div class="panel hot-panel">
        <h3>🔥 热门商品推荐</h3>
        <ul>
          <li v-for="hot in hotItems" :key="hot.id">{{ hot.title }} - 👁 {{ hot.views }}次浏览</li>
        </ul>
      </div>
      <div class="panel chart-panel" style="flex: 1; position: relative;">
        <h3 v-if="!currentCategoryChart">📈 价格趋势 (分类均价) - 点击柱子查看详情</h3>
        <h3 v-else>📈 {{ currentCategoryChart }} 价格连线趋势图 (按日统计)</h3>
        <button v-if="currentCategoryChart" @click="resetChartToCategories" style="position: absolute; right: 20px; top: 15px; padding: 4px 12px; cursor: pointer; background: #e2e8f0; color: #333; border: none; border-radius: 4px; font-weight: bold;">← 返回总览</button>
        <div id="chart" style="width: 100%; height: 280px; margin-top: 10px;"></div>
      </div>
    </div>

    <div class="item-grid" v-if="items.length">
      <div class="card card-hover" v-for="item in items" :key="item.id" @click="$router.push('/item/' + item.id)">
        <div style="border:2px solid #bbb;border-radius:8px;padding:10px 12px;background:#f5f5f5;margin-bottom:12px;text-align:center;font-weight:bold;">
          <h3 v-html="highlight(item.title)" style="margin:0;font-size:1.1rem;"></h3>
        </div>
        <span v-if="item.is_lowest" class="lowest-badge">💰 史低好价</span>
        <p style="color:var(--danger-color); font-weight:bold; font-size:1.2rem;">￥{{ item.price }}</p>
        <p v-if="item.is_lowest" style="font-size:0.75rem; color:#e67e22;">历史低至 ￥{{ item.lowest_price }}</p>
<p v-if="item.avg_rating" style="font-size:0.85rem; color:#f39c12;">评分: ★ {{ Number(item.avg_rating).toFixed(1) }} ({{item.review_count}}条评论)</p>
                  <p style="font-size:0.85rem; color: var(--text-muted); display:flex; align-items:center; gap:8px; margin-top: auto;">
          <span style="background:var(--bg-color); padding: 4px 8px; border-radius: 6px;">{{ item.category_name }}</span>
          <span>👁 {{ item.views }}</span>
          <span style="margin-left:auto;">{{ item.created_at }}</span>
        </p>
      </div>
    </div>
    <div v-else style="margin-top: 20px;">无相关物品</div>

    <Pagination :current-page="query.page" :total="total" :size="query.size" @page-change="onPageChange" />
  </div>
</template>

<!-- ==================== 首页商品广场 ==================== -->
<!-- 商品列表 + 搜索筛选 + 热门推荐 + 价格趋势 -->
<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import Pagination from '../components/Pagination.vue'
import PriceSlider from '../components/PriceSlider.vue'
import DatePicker from '../components/DatePicker.vue'

const items = ref([])
const total = ref(0)
const hotItems = ref([])
const categories = ref([])
const query = ref({ keyword: '', categoryId: '', minPrice: '', maxPrice: '', startDate: '', endDate: '', page: 1, size: 8 })

  // 获取商品列表（支持关键词、分类、价格范围等多条件检索）
  const fetchData = async () => {
    let url = `http://localhost:8000/api/items?page=${query.value.page}&size=${query.value.size}`
    if (query.value.keyword) url += `&keyword=${query.value.keyword}`
    if (query.value.categoryId) url += `&category_id=${query.value.categoryId}`
    if (query.value.minPrice) url += `&min_price=${query.value.minPrice}`
    if (query.value.maxPrice) url += `&max_price=${query.value.maxPrice}`
    try {
        const res = await fetch(url)
        const data = await res.json()
        if (!res.ok) { items.value = []; total.value = 0; return }
        items.value = data.items || []
        total.value = data.total || 0
    } catch(e) { console.error('需要先启动后端服务器!') }
}

const currentCategoryChart = ref('')

  // 加载分类列表、热门商品和价格趋势图表
  const fetchAdvancedData = async () => {
    fetch('http://localhost:8000/api/categories')
        .then(res => res.json())
        .then(data => categories.value = data)
    const resHot = await fetch('http://localhost:8000/api/hot-items')
    hotItems.value = await resHot.json()
    await initCategoryChart()
}

const initCategoryChart = async () => {
    const resTrend = await fetch('http://localhost:8000/api/price-trends')
    const trendData = await resTrend.json()
    currentCategoryChart.value = ''
    nextTick(() => {
        const myChart = echarts.init(document.getElementById('chart'))
        myChart.clear()
        myChart.setOption({
            grid: { top: 30, right: 30, bottom: 20, left: 20, containLabel: true },
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: trendData.map(t => t.category_name) },
            yAxis: { type: 'value' },
            series: [{ name: '平均价格', type: 'bar', barMaxWidth: 50, data: trendData.map(t => t.avg_price), itemStyle: { color: '#4169E1' } }]
        })
        myChart.off('click')
        myChart.on('click', async (params) => {
            const catName = params.name
            currentCategoryChart.value = catName
            const res = await fetch(`http://localhost:8000/api/price-trends/${catName}`)
            const lineData = await res.json()
            myChart.clear()
            myChart.setOption({
                grid: { top: 30, right: 30, bottom: 20, left: 20, containLabel: true },
                tooltip: { trigger: 'axis' },
                xAxis: { type: 'category', data: lineData.map(d => d.date) },
                yAxis: { type: 'value' },
                series: [{ name: '每日均价', type: 'line', smooth: true, data: lineData.map(d => d.avg_price), areaStyle: {} }]
            })
            myChart.off('click')
        })
    })
}

const resetChartToCategories = () => { initCategoryChart() }

const exportData = () => { window.open('http://localhost:8000/api/export-items') }

const onPageChange = (p) => { query.value.page = p; fetchData() }

const highlight = (title) => {
    if (!query.value.keyword) return title;
    const reg = new RegExp(`(${query.value.keyword})`, 'gi');
    return title.replace(reg, '<span style="background: yellow; color: red;">$1</span>');
}

onMounted(() => {
    fetchData()
    fetchAdvancedData()
})
</script>

<style scoped>
.filters { 
  display: flex; gap: 15px; 
  background: var(--card-bg); 
  padding: 20px; 
  border-radius: var(--border-radius); 
  flex-wrap: wrap; margin-bottom: 25px;
  box-shadow: var(--shadow-sm);
  align-items: center;
}
.panel { 
  background: var(--card-bg); 
  padding: 20px; 
  border-radius: var(--border-radius); 
  box-shadow: var(--shadow-sm); 
  transition: var(--transition);
}
.panel:hover { box-shadow: var(--shadow-md); }
.item-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); 
  gap: 24px; 
}
.card { 
  background: var(--card-bg); 
  padding: 20px; 
  border-radius: var(--border-radius); 
  box-shadow: var(--shadow-sm); 
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
}
.card.card-hover { cursor: pointer; }
.card.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}
.card h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 1.1rem;
  line-height: 1.4;
}
.card p { margin: 5px 0; }
.hot-panel { background: linear-gradient(135deg, #fff9e6 0%, #ffffff 100%); border-left: 4px solid var(--warning-color); }
.chart-panel { background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%); border-left: 4px solid var(--secondary-color); }
.lowest-badge {
  display: inline-block;
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 4px;
  background: linear-gradient(135deg, #fff3e0, #ffe0b2);
  border: 1px solid #ff9800;
  color: #e65100;
  font-weight: 600;
}
</style>
