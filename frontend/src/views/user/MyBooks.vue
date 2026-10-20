<template>
  <div>
    <div class="toolbar">
      <el-select v-model="params.status" placeholder="全部状态" clearable style="width: 140px" @change="search">
        <el-option v-for="(v, k) in BOOK_STATUS" :key="k" :label="v.label" :value="k" />
      </el-select>
      <el-button type="primary" @click="router.push('/publish')">发布图书</el-button>
    </div>
    <el-table v-loading="loading" :data="items" empty-text="还没有发布过图书">
      <el-table-column label="封面" width="76">
        <template #default="{ row }">
          <img v-if="row.cover_url" :src="row.cover_url" class="cover-thumb" alt="" />
          <div v-else class="cover-thumb" />
        </template>
      </el-table-column>
      <el-table-column label="书名" min-width="160">
        <template #default="{ row }">
          <router-link :to="`/books/${row.id}`">{{ row.title }}</router-link>
          <div class="muted">{{ row.author }} · {{ row.category_name }}</div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><StatusTag :map="BOOK_STATUS" :value="row.status" /></template>
      </el-table-column>
      <el-table-column label="说明" min-width="180">
        <template #default="{ row }">
          <span v-if="row.status === 'PENDING'" class="muted">等待管理员审核</span>
          <span v-else-if="row.status === 'OFF_SHELF' && row.review_note">驳回原因：{{ row.review_note }}</span>
          <span v-else-if="row.status === 'OFF_SHELF'" class="muted">已下架，编辑后可重新提交审核</span>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="150">
        <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status !== 'BORROWED'" link type="primary" @click="router.push(`/books/${row.id}/edit`)">
            编辑
          </el-button>
          <el-button v-if="['PENDING', 'AVAILABLE'].includes(row.status)" link type="danger" @click="offShelf(row)">
            下架
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <Pager v-model:page="page" :size="size" :total="total" @change="load" />
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'

import { bookApi } from '@/api'
import Pager from '@/components/Pager.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePaged } from '@/composables/usePaged'
import { BOOK_STATUS, formatTime } from '@/utils/constants'
import { confirm } from '@/utils/confirm'

const router = useRouter()
const params = reactive({ status: '' })
const { items, total, page, size, loading, load, search } = usePaged(bookApi.mine, params)

onMounted(load)

async function offShelf(row) {
  if (!(await confirm(`确定下架《${row.title}》吗？下架后不再对外展示，待处理的借阅申请会失效。`))) return
  await bookApi.offShelf(row.id)
  load()
}
</script>
