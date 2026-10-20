<template>
  <span v-if="book.is_deleted">{{ book.title }} <span class="muted">（已删除）</span></span>
  <router-link v-else :to="`/books/${book.id}`">{{ book.title }}</router-link>
</template>

<script setup>
defineProps({ book: { type: Object, required: true } })
</script>
