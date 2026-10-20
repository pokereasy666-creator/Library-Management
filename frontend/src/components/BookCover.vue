<template>
  <img v-if="src" :src="src" :alt="title" class="book-cover" />
  <div v-else class="book-cover placeholder">
    <span>{{ title }}</span>
  </div>
</template>

<script setup>
defineProps({
  src: { type: String, default: '' },
  title: { type: String, default: '' },
})
</script>

<style scoped>
.book-cover {
  display: block;
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 4px;
  background: #ebeef5;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background: linear-gradient(135deg, #e6f0ff, #f2e8ff);
  color: #606266;
  font-weight: 600;
  text-align: center;
  word-break: break-all;
}
</style>
