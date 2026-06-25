<!-- ==================== 写评价 ==================== -->
<!-- 星级评分 + 文字留言 -->
<template>
  <div style="max-width:500px;margin:30px auto;background:white;padding:30px;border-radius:8px;">
    <h2>写评价</h2>
    <div style="margin:20px 0;">
      <label style="font-weight:bold;">评分：</label>
      <div style="font-size:30px;cursor:pointer;margin-top:8px;">
        <span v-for="i in 5" :key="i" @click="form.rating=i" :style="{color:i<=form.rating?'#f39c12':'#ddd'}">★</span>
        <span style="font-size:14px;color:#888;margin-left:10px;">{{form.rating}}星</span>
      </div>
    </div>
    <div style="margin:20px 0;">
      <label style="font-weight:bold;">评价内容：</label>
      <textarea v-model="form.comment" rows="4" placeholder="请分享您的购买体验" style="width:100%;padding:10px;margin-top:8px;border:1px solid #ccc;border-radius:4px;box-sizing:border-box;"></textarea>
    </div>
    <div style="display:flex;gap:15px;">
      <button @click="$router.back()" style="flex:1;background:#999;color:white;border:none;padding:10px;border-radius:4px;cursor:pointer;">取消</button>
      <button @click="submit()" style="flex:1;background:#4CAF50;color:white;border:none;padding:10px;border-radius:4px;cursor:pointer;font-weight:bold;">提交评价</button>
    </div>
  </div>
</template>

<script setup>
import {ref,onMounted} from "vue"
import {useRoute,useRouter} from "vue-router"
const route=useRoute();const router=useRouter()
const form=ref({rating:5,comment:""})
const pid=parseInt(route.params.purchaseId)
const tok=localStorage.getItem("token")||""
const iid=ref(null)

onMounted(async()=>{
  try{
    const r=await fetch("http://localhost:8000/api/users/"+localStorage.getItem("user_id")+'/purchases')
    if(r.ok){
      const p=(await r.json()).find(x=>x.id==pid)
      if(p) iid.value=p.item_id
    }
  }catch(e){console.error(e)}
})

const submit=async()=>{
  if(!iid.value) return alert("未找到订单信息")
  try{
    const r=await fetch("http://localhost:8000/api/reviews",{method:"POST",headers:{"Content-Type":"application/json","Authorization":tok},body:JSON.stringify({item_id:iid.value,purchase_id:pid,rating:form.value.rating,comment:form.value.comment})})
    const d=await r.json()
    if(r.ok){alert("评价成功");router.push("/my-purchases")}
    else if(d.detail==='已评价'){alert("您已评价");router.push("/my-purchases")}else alert("评价失败:"+JSON.stringify(d))
  }catch(e){alert("网络异常")}
}
</script>
