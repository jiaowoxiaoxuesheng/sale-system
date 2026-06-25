<template>
  <!-- 价格区间组件 -->
  <div class="price-slider">
    <input type="number" placeholder="最低价" :value="min" @input="$emit('update:min', $event.target.value)" /> -
    <input type="number" placeholder="最高价" :value="max" @input="$emit('update:max', $event.target.value)" />
  </div>
</template>
<script setup>
defineProps(['min', 'max'])
defineEmits(['update:min', 'update:max'])
</script>
<style scoped>
input { width: 80px; padding: 5px; margin: 0 5px; }
</style>