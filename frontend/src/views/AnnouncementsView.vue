<template>
  <div style="max-width: 800px; margin: auto;">
    <h2 style="text-align: center; color: #4CAF50;">📰 平台系统公告</h2>
    
    <div v-if="announcements.length === 0" style="text-align: center; color: #999; margin-top: 50px;">
      暂无公告...
    </div>

    <div v-for="ann in announcements" :key="ann.id" style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 20px; background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); position: relative;">
      <button v-if="isAdmin" @click="deleteAnn(ann.id)" style="position: absolute; right: 20px; top: 20px; background: #ff4d4f; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">删除</button>
      
      <h3 style="margin-top: 0; color: #333; padding-right: 60px;">{{ ann.title }}</h3>
      <p style="color: gray; font-size: 0.9em; border-bottom: 1px solid #eee; padding-bottom: 10px;">发布时间: {{ new Date(ann.created_at).toLocaleString() }}</p>
      
      <p style="white-space: pre-wrap; line-height: 1.6; color: #555;">{{ ann.content }}</p>
      
      <div v-if="getImages(ann.images).length > 0" style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px;">
        <img v-for="img in getImages(ann.images)" :src="img" :key="img" @click="previewImage = img" style="max-width: 200px; border-radius: 8px; border: 1px solid #ccc; cursor: zoom-in;">
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

const announcements = ref([])
const isAdmin = ref(localStorage.getItem('role') === 'admin')
const previewImage = ref(null)

const loadData = async () => {
    const res = await fetch('http://localhost:8000/api/announcements')
    if(res.ok) {
        announcements.value = await res.json()
    }
}

onMounted(loadData)

const deleteAnn = async (id) => {
    if(!confirm("确定要删除这条公告吗？")) return;
    const res = await fetch(`http://localhost:8000/api/announcements/${id}`, {
        method: 'DELETE',
        headers: { 'token': localStorage.getItem('token') }
    })
    if(res.ok) {
        loadData()
    }
}

const getImages = (imagesStr) => {
    try {
        return JSON.parse(imagesStr || '[]')
    } catch {
        return []
    }
}
</script>

<style scoped>
.preview-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 9999; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(5px); }
.preview-modal img { max-width: 90%; max-height: 90vh; object-fit: contain; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
.close-preview { position: absolute; top: 20px; right: 30px; background: #fff; color: #333; border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 24px; cursor: pointer; font-weight: bold; line-height: 40px; text-align: center; }
</style>
