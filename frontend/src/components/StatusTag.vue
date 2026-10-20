<template>
  <el-tag :type="item.type" size="small" disable-transitions>{{ item.label }}</el-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  map: { type: Object, required: true },
  value: { type: String, required: true },
})

const item = computed(() => props.map[props.value] || { label: props.value, type: 'info' })
</script>
