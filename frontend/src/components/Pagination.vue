<template>
  <div class="pagination">
    <button :disabled="currentPage <= 1" @click="$emit('page-change', currentPage - 1)">上一页</button>
    <span> 第 {{ currentPage }} 页 </span>
    <button @click="$emit('page-change', currentPage + 1)">下一页</button>
  </div>
</template>
<script setup>
defineProps(['currentPage', 'total', 'size'])
defineEmits(['page-change'])
</script>
<style scoped>
.pagination { display: flex; justify-content: center; gap: 10px; margin-top: 20px; }
button { padding: 5px 15px; cursor: pointer; }
</style>