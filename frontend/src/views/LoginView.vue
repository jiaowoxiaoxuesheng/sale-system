<template>
  <div style="max-width:420px;margin:50px auto;background:white;padding:30px;border-radius:8px;">
    <h2 style="text-align:center;color:#4CAF50;">农产品电商</h2>
    <div v-if="mode=='login'">
      <h3 style="text-align:center;">用户登录</h3>
      <input v-model="form.username" placeholder="用户名" style="width:100%;padding:10px;margin:8px 0;box-sizing:border-box;"><br>
      <input type="password" v-model="form.password" placeholder="密码" style="width:100%;padding:10px;margin:8px 0;box-sizing:border-box;"><br>
      <button @click="doLogin" style="width:100%;padding:10px;background:#4CAF50;color:white;border:none;border-radius:4px;cursor:pointer;font-size:16px;">登录</button>
      <p style="text-align:center;margin-top:15px;">没有账号？ <a href="#" @click="mode='register'">立即注册</a></p>
    </div>
    <div v-if="mode=='register'">
      <h3 style="text-align:center;">用户注册</h3>
      <input v-model="form.username" placeholder="用户名" style="width:100%;padding:10px;margin:8px 0;box-sizing:border-box;"><br>
      <input type="password" v-model="form.password" placeholder="请输入密码" style="width:100%;padding:10px;margin:8px 0;box-sizing:border-box;"><br>
      <input type="password" v-model="form.confirm_password" placeholder="确认密码" style="width:100%;padding:10px;margin:8px 0;box-sizing:border-box;"><br>
      <select v-model="form.role" style="width:100%;padding:10px;margin:8px 0;">
        <option value="consumer">普通消费者</option>
        <option value="farmer">农户商家</option>
      </select><br>
      <button @click="doRegister" style="width:100%;padding:10px;background:#2196F3;color:white;border:none;border-radius:4px;cursor:pointer;font-size:16px;">注册</button>
      <p style="text-align:center;margin-top:15px;"><a href="#" @click="mode='login'">返回登录</a></p>
    </div>
    <p style="text-align:center;font-size:12px;color:gray;">注：首个注册的用户将自动成为管理员</p>
  </div>
</template>

<!-- ==================== 用户登录注册 ==================== -->
<!-- 支持三类角色选择、密码二次确认 -->
<script setup>
import {ref} from "vue"
import {useRouter} from "vue-router"
const router=useRouter()
const mode=ref('login')
const form=ref({username:"",password:"",confirm_password:"",role:"consumer"})

  // 登录操作：验证账号密码，保存 token 到 localStorage
  const doLogin=async()=>{
  const r=await fetch("http://localhost:8000/api/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:form.value.username,password:form.value.password})})
  const d=await r.json()
  if(!r.ok){alert(d.detail);return}
  localStorage.setItem("token",d.token);localStorage.setItem("user_id",d.user_id)
  localStorage.setItem("username",d.username);localStorage.setItem("role",d.role)
  alert(d.message);location.href="/"
}

  // 注册操作：验证密码一致性，选择用户角色（消费者/商家）
  const doRegister=async()=>{
  if(!form.value.username||!form.value.password)return alert("请填写用户名和密码")
  if(form.value.password!==form.value.confirm_password)return alert("两次密码输入不一致")
  const r=await fetch("http://localhost:8000/api/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(form.value)})
  const d=await r.json()
  if(!r.ok)return alert(d.detail)
  alert(d.message);mode.value='login';
  form.value.password="";form.value.confirm_password=""
}
</script>
