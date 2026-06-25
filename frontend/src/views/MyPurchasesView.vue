<!-- ==================== 我的订单 ==================== -->
<!-- 查看购买记录、支付、确认收货、申请售后、评价 -->
<template>
  <div style="background:white; padding: 20px; border-radius: 8px; max-width: 900px; margin: 0 auto;">
    <h2>🛍️ 我的购买</h2>
    
    <div v-if="purchases.length === 0" style="text-align: center; color: #999; padding: 40px;">
      暂无购买记录
    </div>
    
    <table v-else style="width: 100%; border-collapse: collapse;">
      <thead>
        <tr style="background: #f5f5f5; border-bottom: 2px solid #ddd;">
          <th style="padding: 12px; text-align: left;">商品名称</th>
          <th style="padding: 12px; text-align: left;">卖家</th>
          <th style="padding: 12px; text-align: center;">价格</th><th style="padding:12px;text-align:center;">数量</th><th style="padding:12px;text-align:center;">订单状态</th>
          <th style="padding: 12px; text-align: center;">购买时间</th>
          <th style="padding: 12px; text-align: center;">操作</th><th style="padding:12px;text-align:center;">数量</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="purchase in purchases" :key="purchase.id" style="border-bottom: 1px solid #eee;">
          <td style="padding: 12px;">
            <router-link :to="`/item/${purchase.item_id}`" style="color: #2196F3; text-decoration: none; cursor: pointer;">
              {{ purchase.item_title }}
            </router-link>
          </td>
          <td style="padding: 12px;">{{ purchase.seller_name }}</td>
          <td style="padding: 12px; text-align: center; color: red; font-weight: bold;">¥{{ purchase.price }}</td>
          <td style="padding:12px;text-align:center;">x{{ purchase.quantity || 1 }}</td><td style="padding:12px;text-align:center;font-size:0.9em;">
            <span :style="'background:'+statusColor[purchase.logistics_status]+';color:white;padding:3px 10px;border-radius:12px;font-weight:bold;'">{{statusLabel[purchase.logistics_status]||purchase.logistics_status}}</span>
          </td><td>{{ formatDate(purchase.created_at) }}</td>
          <td style="padding: 12px; text-align: center;">
            <button @click="payOrder(purchase.id)" v-if="purchase.payment_status==='unpaid'" style="background:#ff9800;color:white;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;margin:2px;">付款</button>
            <button @click="confirmOrder(purchase.id)" v-if="purchase.logistics_status==='shipped'" style="background:#4CAF50;color:white;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;margin:2px;">确认收货</button>
            <span v-if="purchase.reviewed" style="color:#999;font-size:0.85em;">已评价</span><router-link v-if="purchase.can_review&&!purchase.reviewed" :to="'/write-review/'+purchase.id" style="margin:2px;font-size:0.85em;">评价</router-link>
            <button @click="requestAfterSales(purchase.id)" v-if="purchase.logistics_status==='completed'" style="background:#f44336;color:white;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;margin:2px;">申请售后</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const purchases = ref([])
const tok=localStorage.getItem('token')||''
const userId = localStorage.getItem('user_id')

const statusLabel={pending:"待付款",pending_shipment:"待发货",shipped:"已发货",completed:"已完成",after_sales:"售后"}
const statusColor={pending:"#FF9800",pending_shipment:"#2196F3",shipped:"#4CAF50",completed:"#9E9E9E",after_sales:"#f44336"}

const requestAfterSales=async id=>{const reason=prompt("请输入售后原因：");if(!reason)return;const r=await fetch("http://localhost:8000/api/purchases/"+id+"/after-sales?reason="+encodeURIComponent(reason),{method:"POST",headers:{"Authorization":tok||""}});const d=await r.json();alert(d.message||d.detail);location.reload()}

const payOrder=async id=>{const r=await fetch("http://localhost:8000/api/purchases/"+id+'/pay',{method:'PUT',headers:{'Authorization':tok||''}});const d=await r.json();alert(d.message||d.detail);location.reload()}

const confirmOrder=async id=>{const r=await fetch("http://localhost:8000/api/purchases/"+id+'/confirm-received',{method:'PUT',headers:{'Authorization':tok||''}});const d=await r.json();alert(d.message||d.detail);location.reload()}

const formatDate = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN')
}

onMounted(async () => {
  if (!userId) {
    alert('请先登录！')
    return
  }
  
  try {
    const res = await fetch(`http://localhost:8000/api/users/${userId}/purchases`)
    if (res.ok) {
      purchases.value = await res.json()
    } else {
      alert('加载购买记录失败')
    }
  } catch (e) {
    alert('网络错误: ' + e.message)
  }
})

const contactSeller = (sellerName) => {
  alert(`请通过平台站内信联系 "${sellerName}" 卖家`)
}
</script>

<style scoped>
table {
  width: 100%;
}

th, td {
  padding: 12px;
}

tbody tr:hover {
  background: #f9f9f9;
}
</style>
