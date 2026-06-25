<template>
  <!-- 日期选择组件 -->
  <div class="date-picker">
    <input type="date" :value="start" @input="$emit('update:start', $event.target.value)" /> 至 
    <input type="date" :value="end" @input="$emit('update:end', $event.target.value)" />
  </div>
</template>
<script setup>
defineProps(['start', 'end'])
defineEmits(['update:start', 'update:end'])
</script>