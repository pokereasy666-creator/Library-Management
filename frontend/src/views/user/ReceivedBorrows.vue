<template>
  <div>
    <div class="toolbar">
      <el-select v-model="params.status" placeholder="全部状态" clearable style="width: 140px" @change="search">
        <el-option v-for="(v, k) in BORROW_STATUS" :key="k" :label="v.label" :value="k" />
      </el-select>
    </div>
    <el-table v-loading="loading" :data="items" empty-text="还没有收到借阅申请">
      <el-table-column label="图书" min-width="160">
        <template #default="{ row }"><BookLink :book="row.book" /></template>
      </el-table-column>
      <el-table-column label="申请人" width="110">
        <template #default="{ row }">{{ row.borrower.nickname }}</template>
      </el-table-column>
      <el-table-column prop="message" label="申请留言" min-width="160" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><StatusTag :map="BORROW_STATUS" :value="row.status" /></template>
      </el-table-column>
      <el-table-column label="申请时间" width="150">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'PENDING'">
            <el-button link type="primary" @click="approve(row)">同意</el-button>
            <el-button link type="danger" @click="reject(row)">拒绝</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
    <Pager v-model:page="page" :size="size" :total="total" @change="load" />
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'

import { borrowApi } from '@/api'
import BookLink from '@/components/BookLink.vue'
import Pager from '@/components/Pager.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePaged } from '@/composables/usePaged'
import { BORROW_STATUS, formatTime } from '@/utils/constants'
import { confirm } from '@/utils/confirm'

const params = reactive({ status: '' })
const { items, total, page, size, loading, load, search } = usePaged(borrowApi.received, params)

onMounted(load)

async function approve(row) {
  const ok = await confirm(
    `同意 ${row.borrower.nickname} 借阅《${row.book.title}》？图书将变为已借出，这本书的其他待处理申请会自动失效。`,
  )
  if (!ok) return
  try {
    await borrowApi.approve(row.id)
  } finally {
    load()
  }
}

async function reject(row) {
  if (!(await confirm(`拒绝 ${row.borrower.nickname} 的借阅申请？`))) return
  try {
    await borrowApi.reject(row.id)
  } finally {
    load()
  }
}
</script>
