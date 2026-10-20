<template>
  <div v-if="total > 0" class="pager">
    <el-pagination
      :current-page="page"
      :page-size="size"
      :total="total"
      layout="total, prev, pager, next"
      background
      size="small"
      @current-change="onChange"
    />
  </div>
</template>

<script setup>
defineProps({
  page: { type: Number, required: true },
  size: { type: Number, required: true },
  total: { type: Number, required: true },
})
const emit = defineEmits(['update:page', 'change'])

function onChange(value) {
  emit('update:page', value)
  emit('change', value)
}
</script>
