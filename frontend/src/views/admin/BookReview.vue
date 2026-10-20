<template>
  <div>
    <div class="toolbar">
      <el-select v-model="params.status" placeholder="全部状态" clearable style="width: 140px" @change="search">
        <el-option v-for="(v, k) in BOOK_STATUS" :key="k" :label="v.label" :value="k" />
      </el-select>
      <el-input
        v-model="params.keyword"
        placeholder="书名或作者"
        clearable
        style="max-width: 240px"
        @keyup.enter="search"
        @clear="search"
      />
      <el-button type="primary" @click="search">查询</el-button>
    </div>
    <el-table v-loading="loading" :data="items" empty-text="没有符合条件的图书">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand">
            <img v-if="row.cover_url" :src="row.cover_url" class="expand-cover" alt="" />
            <div>
              <p><strong>简介：</strong>{{ row.description || '无' }}</p>
              <p v-if="row.review_note"><strong>驳回原因：</strong>{{ row.review_note }}</p>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="封面" width="76">
        <template #default="{ row }">
          <img v-if="row.cover_url" :src="row.cover_url" class="cover-thumb" alt="" />
          <div v-else class="cover-thumb" />
        </template>
      </el-table-column>
      <el-table-column label="书名" min-width="150">
        <template #default="{ row }">
          <router-link :to="`/books/${row.id}`">{{ row.title }}</router-link>
          <div class="muted">{{ row.author }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="category_name" label="分类" width="100" />
      <el-table-column prop="condition" label="新旧程度" width="110" />
      <el-table-column label="发布人" width="110">
        <template #default="{ row }">{{ row.owner.nickname }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><StatusTag :map="BOOK_STATUS" :value="row.status" /></template>
      </el-table-column>
      <el-table-column label="更新时间" width="150">
        <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'PENDING'">
            <el-button link type="primary" @click="approve(row)">通过</el-button>
            <el-button link type="warning" @click="reject(row)">驳回</el-button>
          </template>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <Pager v-model:page="page" :size="size" :total="total" @change="load" />
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { ElMessageBox } from 'element-plus'

import { adminApi } from '@/api'
import Pager from '@/components/Pager.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePaged } from '@/composables/usePaged'
import { BOOK_STATUS, formatTime } from '@/utils/constants'
import { confirm } from '@/utils/confirm'

const params = reactive({ status: 'PENDING', keyword: '' })
const { items, total, page, size, loading, load, search } = usePaged(adminApi.books, params)

onMounted(load)

async function approve(row) {
  try {
    await adminApi.approveBook(row.id)
  } finally {
    load()
  }
}

async function reject(row) {
  let note
  try {
    const result = await ElMessageBox.prompt(`驳回《${row.title}》，图书将变为已下架。`, '驳回图书', {
      inputPlaceholder: '驳回原因（选填，发布人可以看到）',
      inputValidator: (v) => !v || v.length <= 255 || '不能超过 255 个字符',
      confirmButtonText: '驳回',
      cancelButtonText: '取消',
    })
    note = result.value || ''
  } catch {
    return
  }
  try {
    await adminApi.rejectBook(row.id, note)
  } finally {
    load()
  }
}

async function remove(row) {
  if (!(await confirm(`确定删除违规图书《${row.title}》吗？删除后不再展示，借还历史会保留。`))) return
  try {
    await adminApi.deleteBook(row.id)
  } finally {
    load()
  }
}
</script>

<style scoped>
.expand {
  display: flex;
  gap: 16px;
  padding: 0 24px;
}

.expand-cover {
  width: 90px;
  height: 120px;
  object-fit: cover;
  border-radius: 4px;
}

.expand p {
  margin: 0 0 8px;
  white-space: pre-wrap;
}
</style>
