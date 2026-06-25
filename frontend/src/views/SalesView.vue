<template>
  <div style="background:white;padding:20px;border-radius:8px;max-width:1100px;margin:0 auto;">
    <h2 style="margin-bottom:20px;">我的销售订单</h2>
    <div v-if="sales.length===0" style="text-align:center;color:#999;padding:40px;">暂无销售订单</div>
    <table v-else style="width:100%;border-collapse:collapse;background:white;">
      <thead>
        <tr style="border-bottom:2px solid #ddd;">
          <th style="padding:12px;text-align:left;">商品</th>
          <th style="padding:12px;text-align:left;">买家</th>
          <th style="padding:12px;text-align:center;">单价</th>
          <th style="padding:12px;text-align:center;">数量</th>
          <th style="padding:12px;text-align:center;">总价</th>
          <th style="padding:12px;text-align:center;">订单状态</th>
          <th style="padding:12px;text-align:center;">时间</th>
          <th style="padding:12px;text-align:center;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in sales" :key="s.id" style="border-bottom:1px solid #eee;">
          <td style="padding:12px;">{{s.item_title}}</td>
          <td style="padding:12px;">{{s.buyer_name}}</td>
          <td style="padding:12px;text-align:center;color:red;font-weight:bold;">¥{{s.price}}</td>
          <td style="padding:12px;text-align:center;">{{s.quantity||1}}</td>
          <td style="padding:12px;text-align:center;color:red;font-weight:bold;">¥{{(s.price*(s.quantity||1)).toFixed(2)}}</td>
          <td style="padding:12px;text-align:center;">
            <span :style="'background:'+statusColor[s.logistics_status]+';color:white;padding:3px 10px;border-radius:12px;font-size:0.85em;font-weight:bold;display:inline-block;'">{{statusText[s.logistics_status]||s.logistics_status}}</span>
          </td>
          <td style="padding:12px;text-align:center;font-size:0.85em;">{{fmt(s.created_at)}}</td>
          <td style="padding:12px;text-align:center;">
            <button @click="ship(s)" v-if="s.logistics_status==='pending_shipment'" style="background:#2196F3;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;margin:2px;font-size:0.9em;">确认发货</button>
            <button @click="track(s)" v-if="s.tracking_number" style="background:#e2e8f0;color:#333;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;margin:2px;font-size:0.9em;">查看物流</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import {ref,onMounted} from "vue"
const sales=ref([]),uid=localStorage.getItem("user_id"),tok=localStorage.getItem("token")
const fmt=iso=>new Date(iso).toLocaleString()
const statusText={pending:"待付款",pending_shipment:"待发货",shipped:"已发货",completed:"已完成",after_sales:"售后"}
const statusColor={pending:"#FF9800",pending_shipment:"#2196F3",shipped:"#4CAF50",completed:"#9E9E9E",after_sales:"#f44336"}

const load=async()=>{const r=await fetch("http://localhost:8000/api/users/"+uid+'/sales',{headers:{"Authorization":tok||""}});if(r.ok)sales.value=await r.json()}

const ship=async(sale)=>{
  const comp=prompt("物流公司:")
  if(!comp)return
  const no=prompt("运单号:")
  if(!no)return
  const r=await fetch("http://localhost:8000/api/purchases/"+sale.id+'/logistics',{method:"PUT",headers:{"Content-Type":"application/json","Authorization":tok||""},body:JSON.stringify({logistics_status:"shipped",logistics_company:comp,tracking_number:no})})
  const d=await r.json();alert(d.message||d.detail);load()
}

const track=(s)=>{alert("物流公司:"+s.logistics_company+'\n'+"运单号:"+s.tracking_number+'\n'+"状态:"+statusText[s.logistics_status])}

onMounted(load)
</script>
