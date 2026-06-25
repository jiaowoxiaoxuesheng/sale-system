<!-- ==================== 发布商品 ==================== -->
<!-- 商品名称、描述、价格、产地、规格、库存、图片 -->
<template>
  <div style="background:white; padding: 20px; max-width: 500px; margin: 0 auto; border-radius: 8px;">
    <h2>发布农产品</h2>
    <form @submit.prevent="submit">
      <div style="margin-bottom:15px;"><label>商品名称: </label>
        <input v-model="form.title" required style="width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px;">
      </div>
      <div style="margin-bottom:15px;"><label>描述 (支持多行): </label>
        <textarea v-model="form.description" style="width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px;"></textarea>
      </div>
      <div style="margin-bottom:15px;"><label>价格 (￥): </label>
        <input type="number" step="0.01" min="0" v-model="form.price" required style="width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px;">

      <div style="margin-bottom:15px;">
        <label>产地：</label>
        <input v-model="form.origin" placeholder="如： 山东烟台" style="width:100%;padding:8px;margin-top:5px;box-sizing:border-box;border:1px solid #ccc;border-radius:4px;">
      </div>
      <div style="margin-bottom:15px;">
        <label>规格（kg）：</label>
        <input type="number" v-model.number="form.specification" min="0" step="0.1" placeholder="如 1" style="width:100%;padding:8px;margin-top:5px;box-sizing:border-box;border:1px solid #ccc;border-radius:4px;">
      </div>
      <div style="margin-bottom:15px;">
        <label>库存（数量）：</label>
        <input type="number" min="0" v-model="form.stock" placeholder="如： 100" style="width:100%;padding:8px;margin-top:5px;box-sizing:border-box;border:1px solid #ccc;border-radius:4px;">
      </div>
      </div>
      
      <!-- 加分项：多图上传面板 -->
      <div style="margin-bottom:20px;">
        <label>商品分类: </label>
        <select v-model="form.category_id" required style="width: 100%; padding: 8px; margin-top: 5px; margin-bottom: 15px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px;">
           <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
        </select>
        
        <label>商品展示图片 (多图): </label>
        <input type="file" @change="uploadImage" accept="image/*" style="width: 100%; margin-top: 5px;">
        <div v-if="images.length > 0" style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
          <div v-for="(img, index) in images" :key="index" style="position: relative; display: inline-block;">
            <img :src="img" style="width: 80px; height: 80px; object-fit: cover; border-radius: 4px; border: 1px solid #eee;">
            <button type="button" @click="removeImage(index)" style="position: absolute; top: -5px; right: -5px; background: red; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer; font-size: 12px; line-height: 1; display:flex; align-items:center; justify-content:center; padding:0;">×</button>
          </div>
        </div>
      </div>
      
      
      <button type="submit" style="background:#4CAF50; color:white; padding:10px; width: 100%; border: none; border-radius: 4px; cursor: pointer; font-size: 1.1em;">确认发布</button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const form = ref({ title: '', description: '', price: '', origin: '', specification: 1, stock: 0, min_stock: 0, category_id: 1 })
const images = ref([]) // 用于在页面上展示所选图片的本地缩略图预览
const imageFiles = ref([]) // 真实的文件数据，点击“发布”时才传给后端
const categories = ref([])
const router = useRouter()

onMounted(async () => {
    // 动态获取管理员创建的所有最新分类
    const res = await fetch('http://localhost:8000/api/categories')
    categories.value = await res.json()
    if(categories.value.length > 0) form.value.category_id = categories.value[0].id
})

const uploadImage = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    // 获取到文件后立刻重置 input 组件的 value，确保证实可重传同文件
    e.target.value = ''
    
    // 生成本地对象 URL 作为前端预览，不发生任何网络请求
    images.value.push(URL.createObjectURL(file))
    // 积攒真实文件，待最后点击发布按钮时，一次性传输给后端
    imageFiles.value.push(file)
}

const removeImage = (index) => {
    images.value.splice(index, 1)
    imageFiles.value.splice(index, 1)
}

const submit = async () => {
    const userId = localStorage.getItem('user_id')
    if(!userId) return alert("请先登录！")

    // 前端表单校验 (防止用户填入非法数据)
    if(form.value.title.trim() === '') return alert("商品名称不能为空或者全是空格！")
    if(parseFloat(form.value.price) < 0) return alert("价格不能为负数！")

    // 在确认发布阶段，统一把积攒的文件上传到服务器获取真实链接
    const uploadedUrls = []
    for(let i=0; i<imageFiles.value.length; i++) {
        const file = imageFiles.value[i]
        const formData = new FormData()
        formData.append('file', file)
        try {
            const res = await fetch('http://localhost:8000/api/upload', {
                method: 'POST',
                body: formData
            })
            if(res.ok) {
                const data = await res.json()
                uploadedUrls.push(data.url)
            } else {
                return alert('某张图片上传至后端仓库失败，请检查网络后再试')
            }
        } catch (err) {
            return alert('后端上传接口连接断开')
        }
    }

    // 组合最终上传给后端的 JSON 报文
    const payload = {
        title: form.value.title.trim(),
        description: form.value.description || '暂无描述',
        price: parseFloat(form.value.price),
        origin: form.value.origin || "",
        specification: form.value.specification ? String(form.value.specification) + 'kg' : '',
        stock: parseInt(form.value.stock) || 0,
        min_stock: parseInt(form.value.min_stock) || 0,
        category_id: form.value.category_id,
        user_id: parseInt(userId),
        images: JSON.stringify(uploadedUrls)
    }

    try {
        const res = await fetch('http://localhost:8000/api/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        
        if(res.ok) {
            alert('农产品商品发布成功！')
            router.push('/my-publishes')
        } else {
            const data = await res.json()
            alert('发布失败：' + (data.detail || '未知原因'))
        }
    } catch (e) {
        alert('发布异常：后端服务未启动或连接崩溃')
    }
}
</script>