<template>
  <div class="page">
    <div class="toolbar">
      <el-input
        v-model="params.keyword"
        placeholder="按书名或作者搜索"
        clearable
        :prefix-icon="Search"
        style="max-width: 320px"
        @keyup.enter="search"
        @clear="search"
      />
      <el-select v-model="params.category_id" placeholder="全部分类" clearable style="width: 160px" @change="search">
        <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-button type="primary" @click="search">搜索</el-button>
    </div>

    <div v-loading="loading" class="grid">
      <el-card v-for="book in items" :key="book.id" shadow="hover" class="book-card" @click="openBook(book.id)">
        <BookCover :src="book.cover_url" :title="book.title" />
        <div class="book-title" :title="book.title">{{ book.title }}</div>
        <div class="muted">{{ book.author }}</div>
        <div class="book-meta">
          <el-tag size="small" type="success" effect="plain" disable-transitions>{{ book.condition }}</el-tag>
          <span class="muted">{{ book.category_name }}</span>
        </div>
      </el-card>
    </div>
    <el-empty v-if="!loading && items.length === 0" description="暂时没有可借阅的图书" />

    <div v-if="total > 0" class="pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="size"
        :total="total"
        layout="total, prev, pager, next"
        background
        @current-change="load"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'

import { bookApi } from '@/api'
import BookCover from '@/components/BookCover.vue'
import { usePaged } from '@/composables/usePaged'

const router = useRouter()
const categories = ref([])
const params = reactive({ keyword: '', category_id: null })
const { items, total, page, size, loading, load, search } = usePaged(bookApi.list, params, 12)

onMounted(async () => {
  load()
  categories.value = (await bookApi.categories()).data
})

function openBook(id) {
  router.push({ name: 'book', params: { id } })
}
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
  min-height: 120px;
}

.book-card {
  cursor: pointer;
}

.book-card :deep(.el-card__body) {
  padding: 12px;
}

.book-title {
  margin: 10px 0 4px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
</style>
