<!-- ==================== 商品详情页 ==================== -->
<!-- 商品信息、图片、价格趋势、购买、评价 -->
<template>
  <div v-if="item" style="background:white; padding: 20px; border-radius: 8px; max-width: 800px; margin: 0 auto; box-shadow: var(--shadow-sm);">
    <button @click="$router.back()" style="background: #e2e8f0; color: #333; border: none; padding: 8px 18px; cursor: pointer; border-radius: 6px; margin-bottom: 20px; font-weight: bold; transition: var(--transition);">← 返回</button>
    
    <h2>{{ item.title }}</h2>
    <p style="color:red; font-size: 1.5em; font-weight:bold;">￥{{ item.price }}</p>
    <div style="color: #666; font-size: 0.9em; margin-bottom: 20px; display: flex; gap: 15px;">
        <span>👤 商家: {{ item.owner_name }}</span>
        <span>👀 浏览量: {{ item.views }}</span>
        <span>🕒 发布时间: {{ item.created_at.split('T')[0] }}</span>
        <span>🏷️ 分类: {{ item.category_name }}</span>
        <span>📦 库存: {{ item.stock || 0 }}</span>
        <span>📍 产地: {{ item.origin || '—' }}</span>
    </div>

    <!-- 图集展示 -->
    <div v-if="images.length > 0" style="display: flex; gap: 10px; overflow-x: auto; margin-bottom: 20px;">
        <img v-for="(img, idx) in images" :key="idx" :src="img" @click="previewImage = img" style="width: 200px; height: 200px; object-fit: cover; border-radius: 8px; border: 1px solid #eee; cursor: zoom-in;" />
    </div>


    <div v-if="cmpInfo" style="margin-bottom: 20px; background: #e0f2fe; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6;">
        <h4 style="margin: 0 0 10px 0; color: #1e40af;">📊 农产品行情大盘</h4>
        <div style="font-size: 0.9em; color: #1e3a8a; line-height: 1.6;">
            <div>当前商品分类：<strong>{{ item.category_name }}</strong></div>
            <div>该分类全站最低价：<strong style="color: #059669;">￥{{ cmpInfo.min_price }}</strong></div>
            <div>同类商品平均价：<strong style="color: #ea580c;">￥{{ cmpInfo.avg_price }}</strong></div>
            <div v-if="item.price < cmpInfo.avg_price" style="margin-top: 10px; font-weight: bold; color: #dc2626;">💡 该卖家定价（￥{{ item.price }}）低于农产品均价，是一笔划算的交易！</div>
            <div v-else style="margin-top: 10px; font-weight: bold; color: #4b5563;">💡 该卖家定价（￥{{ item.price }}）高于或等于均价。</div>
        </div>
        
        <!-- 价格趋势图 -->
        <h4 style="margin: 15px 0 10px 0; color: #1e40af;">📈 商品历史改价记录</h4>
        <div style="height: 120px; position: relative; margin-top: 30px; margin-bottom: 30px; border-bottom: 1px solid #bfdbfe;">
            <!-- SVG 画折线 -->
            <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 100 100" style="position: absolute; left: 0; top: 0; overflow: visible;">
                <polyline 
                    fill="none" 
                    stroke="#cbd5e1" 
                    stroke-width="2"
                    vector-effect="non-scaling-stroke"
                    :points="priceTrend.map((tp, i) => `${(priceTrend.length === 1 ? 50 : i / (priceTrend.length - 1) * 100)},${100 - (tp.price / maxTrendPrice * 100)}`).join(' ')"
                />
            </svg>
            <!-- 绝对定位画点和标签 -->
            <div v-for="(tp, idx) in priceTrend" :key="idx" 
                 :style="{ 
                    position: 'absolute', 
                    left: `${priceTrend.length === 1 ? 50 : (idx / (priceTrend.length - 1)) * 100}%`, 
                    top: `${100 - (tp.price / maxTrendPrice * 100)}%`,
                    transform: 'translate(-50%, -50%)',
                    zIndex: 2
                 }">
                <!-- 圆点 -->
                <div :style="{
                    width: '10px', height: '10px', borderRadius: '50%', border: '2px solid white',
                    boxShadow: '0 0 3px rgba(0,0,0,0.3)',
                    background: priceTrend.length === 1 ? '#3b82f6' : (tp.price === Math.min(...priceTrend.map(t=>t.price)) ? '#10b981' : (tp.price === Math.max(...priceTrend.map(t=>t.price)) ? '#ef4444' : '#3b82f6'))
                }"></div>
                <!-- 价格标签 (最高标红, 最低标绿) -->
                <div :style="{
                    fontSize: '0.8em', position: 'absolute', top: '-25px', left: '50%', transform: 'translateX(-50%)', fontWeight: 'bold', whiteSpace: 'nowrap',
                    color: priceTrend.length === 1 ? '#1e3a8a' : (tp.price === Math.min(...priceTrend.map(t=>t.price)) ? '#10b981' : (tp.price === Math.max(...priceTrend.map(t=>t.price)) ? '#ef4444' : '#1e3a8a'))
                }">
                    {{ priceTrend.length === 1 ? '' : (tp.price === Math.min(...priceTrend.map(t=>t.price)) ? '↓最低 ' : (tp.price === Math.max(...priceTrend.map(t=>t.price)) ? '↑最高 ' : '')) }}￥{{ tp.price }}
                </div>
                <!-- 时间标签 (精确到时分) -->
                <div style="font-size: 0.65em; color: #64748b; position: absolute; top: 15px; left: 50%; transform: translateX(-50%); white-space: nowrap;">{{ tp.date }}</div>
            </div>
        </div>
    </div>


    <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; min-height: 100px; margin-bottom: 20px;">
        <h4>物品描述：</h4>
        <p style="white-space: pre-wrap;">{{ item.description }}</p>
    </div>

    <!-- 商品评价 -->
    <div style="margin-bottom:20px;background:#f9f9f9;padding:15px;border-radius:8px;">
      <h4>商品评价</h4>
      <div v-if="reviewStats.total>0">
        <span style="color:#f39c12;font-size:1.2em;"><span v-for="i in 5" :key="i" :style="{color:i<=Math.round(reviewStats.avg_rating)?'#f39c12':'#ddd'}">★</span></span>
        <span style="margin-left:5px;font-weight:bold;">评分：{{reviewStats.avg_rating}}</span>
        <span>({{reviewStats.total}}条评价)</span>
      </div>
      <div v-if="!reviews.length" style="color:#999;">暂无评价</div>
      <div v-for="r in reviews" :key="r.id" style="border-top:1px solid #eee;padding:10px 0;">
        <div><strong>{{r.username}}</strong> <span style="color:#f39c12;"><span v-for="i in 5" :key="i" :style="{color:i<=r.rating?'#f39c12':'#ddd'}">★</span></span> <span style="color:#888;">{{r.created_at}}</span></div>
        <p>{{r.comment}}</p>
        <div v-if="r.response" style="background:#e8f5e9;padding:8px;border-radius:4px;"><span style="color:#2e7d32;">商家回复：</span>{{r.response}}</div>
        <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">
          <template v-if="!r.response && userRole==='farmer' && item && item.user_id == parseInt(userId)">
            <input v-model="replyText[r.id]" placeholder="回复评价..." style="flex:1;padding:6px;border:1px solid #ccc;border-radius:4px;">
            <button @click="doReply(r.id)" style="background:#4CAF50;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;">回复</button>
          </template>
          <button v-if="r.response && userRole==='farmer' && item && item.user_id == parseInt(userId)" @click="delReply(r.id)" style="background:#f44336;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;">删除回复</button>
          <button v-if="r.user_id == parseInt(userId)" @click="selfDelReview(r.id)" style="background:#f44336;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;">删除我的评价</button>
          <button v-if="userRole==='admin'" @click="delReview(r.id)" style="background:#f44336;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;">强制删除</button>
        </div>
      </div>
    </div>

    <div style="display: flex; gap: 15px;">
        <div v-if="item.status === 1 && item.user_id != userId && userRole !== 'admin'" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
          <span style="background:#fff3e0;padding:4px 10px;border-radius:4px;font-size:0.9em;font-weight:bold;">库存: {{item.stock}} {{item.specification}}</span>
          <label>购买数量: </label>
          <input type="number" v-model.number="buyQuantity" :min="1" :max="item.stock" style="width:60px;padding:8px;border:1px solid #ccc;border-radius:4px;">
          <button @click="buyItem" style="background: #E91E63; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 1.1em; font-weight: bold;">
            💳 立即购买
          </button>
        </div>
        <div v-else-if="item.status === 1 && item.user_id != userId && userRole !== 'admin'" style="color:#999;font-weight:bold;">⛔ 已售罄</div>

        <button @click="toggleFavorite" :style="{ background: isFavorite ? '#FF9800' : '#4CAF50', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '4px', cursor: 'pointer', fontSize: '1.1em' }">
            {{ isFavorite ? '★ 取消收藏' : '☆ 加入收藏' }}
        </button>
    </div>
  </div>

  <!-- 图片预览模态框 -->
  <div v-if="previewImage" class="preview-modal" @click="previewImage = null">
      <img :src="previewImage" @click.stop />
      <button class="close-preview" @click="previewImage = null">×</button>
  </div>
  
  <!-- AI 助手组件 -->
  <div class="ai-assistant" :class="{ 'ai-open': isAIOpen }">
      <div v-if="!isAIOpen" class="ai-bubble" @click="isAIOpen = true">
          🤖 智能助手
      </div>
      <div v-else class="ai-panel">
          <div class="ai-header">
              <span>🤖 智能导购助手</span>
              <button @click="isAIOpen = false" style="background:none;border:none;color:white;cursor:pointer;font-size:1.2em;">×</button>
          </div>
          <div class="ai-chats" ref="aiChatBox">
              <div v-for="(msg, i) in aiMessages" :key="i" :class="msg.role">
                  <span>{{ msg.content }}</span>
              </div>
          </div>
          <div class="ai-input">
              <input v-model="aiKeyword" @keyup.enter="sendAIMsg" placeholder="问点什么..." style="flex:1; padding: 6px; border: 1px solid #ddd; border-radius:4px;" />
              <button @click="sendAIMsg" class="btn bg-blue" style="padding:6px 12px; margin-left: 8px;">发送</button>
          </div>
      </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const item = ref(null)
const images = ref([])
const cmpInfo = ref(null)
const previewImage = ref(null)
const priceTrend = ref([])
const maxTrendPrice = ref(1)
const buyQuantity = ref(1)
const isFavorite = ref(false)
const userId = localStorage.getItem('user_id')
const userRole = localStorage.getItem('role')
const reviews = ref([])
const reviewStats = ref({avg_rating:0,total:0,distribution:{1:0,2:0,3:0,4:0,5:0}})
const replyText = ref({})
const token = localStorage.getItem('token')||""

// AI Assistant
const isAIOpen = ref(false)
const aiKeyword = ref('')
const aiChatBox = ref(null)
const aiMessages = ref([
    { role: 'bot', content: '您好！我是农产品二手平台智能助手。请问想了解怎么发布商品？还是关于议价、退货相关的问题？' }
])

const scrollToBottom = () => {
    nextTick(() => {
        if (aiChatBox.value) aiChatBox.value.scrollTop = aiChatBox.value.scrollHeight;
    })
}

const sendAIMsg = async () => {
    if (!aiKeyword.value.trim()) return;
    const txt = aiKeyword.value.trim();
    aiMessages.value.push({ role: 'user', content: txt });
    aiKeyword.value = '';
    scrollToBottom();
    
    try {
        const token = localStorage.getItem('token') || ''
        const res = await fetch(`http://localhost:8000/api/ai/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': token },
            body: JSON.stringify({ message: txt, item_id: item.value?.id })
        });
        const data = await res.json();
        aiMessages.value.push({ role: 'bot', content: data.reply || "网络连接异常，但我仍在听！" });
        scrollToBottom();
    } catch(e) {
        aiMessages.value.push({ role: 'bot', content: "AI 推理服务暂时离线啦~" });
        scrollToBottom();
    }
}

onMounted(async () => {
    const token = localStorage.getItem('token') || ''
    const res = await fetch(`http://localhost:8000/api/items/${route.params.id}`, {
        headers: token ? { 'Authorization': token } : {}
    })
    if (!res.ok) {
        alert('加载商品详情失败: ' + res.status)
        return
    }
    const data = await res.json()
    item.value = data
    images.value = JSON.parse(data.images || "[]")
    
    try { 
        const cmp = await fetch(`http://localhost:8000/api/items/${route.params.id}/compare`); 
        if(cmp.ok) { cmpInfo.value = await cmp.json() }
    } catch(e){}
    
    // 图表数据逻辑获取
    try {
        const tpRes = await fetch(`http://localhost:8000/api/items/${route.params.id}/price-trend`);
        if(tpRes.ok) {
            priceTrend.value = await tpRes.json();
            maxTrendPrice.value = Math.max(...priceTrend.value.map(o => o.price)) * 1.2 || 1;
        }
    } catch (e) {}
    
    loadReviews()
    
    if(userId) {
        try {
            const favRes = await fetch(`http://localhost:8000/api/users/${userId}/favorites`)
            if (favRes.ok) {
                const favs = await favRes.json()
                isFavorite.value = favs.some(f => f.id === data.id)
            }
        } catch(e) {}
    }
})

const loadReviews = async () => {
  try{const r=await fetch("http://localhost:8000/api/reviews/"+route.params.id);if(r.ok)reviews.value=await r.json();const s=await fetch("http://localhost:8000/api/reviews/stats/"+route.params.id);if(s.ok)reviewStats.value=await s.json()}catch(e){}
}
const doReply=async id=>{const txt=replyText.value[id];if(!txt)return;const r=await fetch("http://localhost:8000/api/reviews/"+id+'/response',{method:'POST',headers:{'Content-Type':'application/json','Authorization':token},body:JSON.stringify({response:txt})});if(r.ok){replyText.value[id]="";loadReviews()}}
const delReview=async id=>{if(!confirm("确定删除该评价？"))return;const r=await fetch("http://localhost:8000/api/reviews/"+id,{method:'DELETE',headers:{'Authorization':token}});if(r.ok)loadReviews()}
const delReply=async id=>{if(!confirm("确定删除回复？"))return;const r=await fetch("http://localhost:8000/api/reviews/"+id+'/response',{method:'DELETE',headers:{'Authorization':token}});if(r.ok)loadReviews()}
const selfDelReview=async id=>{if(!confirm("确定删除您的评价？"))return;const r=await fetch("http://localhost:8000/api/reviews/"+id+'/self',{method:'DELETE',headers:{'Authorization':token}});if(r.ok)loadReviews()}

const buyItem = async () => {
    if(!userId) return alert('请先登录！')
    if(buyQuantity.value < 1 || buyQuantity.value > (item.value.stock || 0)) return alert('请输入有效的购买数量！库存: ' + (item.value.stock || 0))
    if(!confirm(`您确定要花费 ￥${(item.value.price * buyQuantity.value).toFixed(2)} 购买 ${buyQuantity.value} 件商品吗？`)) return;

    try {
        const token = localStorage.getItem('token') || ''
        const res = await fetch(`http://localhost:8000/api/items/${item.value.id}/buy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': token },
            body: JSON.stringify({ quantity: buyQuantity.value })
        })
        const data = await res.json()
        if(res.ok) {
            alert(data.message + "，这笔钱已经打入了卖家的余额！")
            location.reload()
        } else {
            alert("购买失败：" + data.detail)
        }
    } catch(e) { alert("网络异常") }
}

const toggleFavorite = async () => {
    if(!userId) return alert('请先登录！')
    const res = await fetch(`http://localhost:8000/api/favorites?user_id=${userId}&item_id=${item.value.id}`, { method: 'POST' })
    const data = await res.json()
    alert(data.message)
    isFavorite.value = !isFavorite.value
}
</script>

<style scoped>
.preview-modal {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.85); z-index: 9999;
    display: flex; justify-content: center; align-items: center;
    backdrop-filter: blur(5px);
}
.preview-modal img {
    max-width: 90%; max-height: 90vh; object-fit: contain;
    border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.close-preview {
    position: absolute; top: 20px; right: 30px;
    background: #fff; color: #333; border: none; border-radius: 50%;
    width: 40px; height: 40px; font-size: 24px; cursor: pointer;
    font-weight: bold; line-height: 40px; text-align: center;
}

/* AI助手样式 */
.ai-assistant { position: fixed; bottom: 30px; right: 30px; z-index: 1000; font-family: -apple-system, sans-serif; }
.ai-bubble { 
    background: #4CAF50; color: white; padding: 12px 20px; border-radius: 30px; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; font-weight: bold; 
    transition: transform 0.3s; 
}
.ai-bubble:hover { transform: scale(1.05); }
.ai-panel { 
    width: 320px; height: 430px; 
    min-width: 280px; min-height: 350px;
    max-width: 80vw; max-height: 80vh;
    background: white; border-radius: 12px; 
    box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
    display: flex; flex-direction: column; 
    overflow: hidden; 
    resize: both; /* 允许 CSS 随意拉伸 */
}
.ai-header { background: #4CAF50; color: white; padding: 12px 15px; display: flex; justify-content: space-between; font-weight: bold; }
.ai-chats { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; background: #f9f9f9; }
.ai-chats .bot, .ai-chats .user { display: flex; max-width: 85%; }
.ai-chats .bot { align-self: flex-start; }
.ai-chats .user { align-self: flex-end; }
.ai-chats .bot span { background: white; padding: 10px 14px; border-radius: 2px 15px 15px 15px; color: #333; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.9em; line-height: 1.4; }
.ai-chats .user span { background: #E3F2FD; padding: 10px 14px; border-radius: 15px 2px 15px 15px; color: #1e3a8a; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.9em; line-height: 1.4; }
.ai-input { padding: 10px; background: white; border-top: 1px solid #eee; display: flex; }
</style>
