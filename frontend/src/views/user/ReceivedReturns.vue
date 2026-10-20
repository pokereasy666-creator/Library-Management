<template>
  <div>
    <div class="toolbar">
      <el-select v-model="params.status" placeholder="全部状态" clearable style="width: 140px" @change="search">
        <el-option v-for="(v, k) in RETURN_STATUS" :key="k" :label="v.label" :value="k" />
      </el-select>
    </div>
    <el-table v-loading="loading" :data="items" empty-text="还没有收到归还申请">
      <el-table-column label="图书" min-width="160">
        <template #default="{ row }"><BookLink :book="row.book" /></template>
      </el-table-column>
      <el-table-column label="借书人" width="110">
        <template #default="{ row }">{{ row.borrower.nickname }}</template>
      </el-table-column>
      <el-table-column prop="message" label="归还留言" min-width="160" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }"><StatusTag :map="RETURN_STATUS" :value="row.status" /></template>
      </el-table-column>
      <el-table-column label="申请时间" width="150">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'PENDING'">
            <el-button link type="primary" @click="confirmReturn(row)">确认归还</el-button>
            <el-button link type="danger" @click="rejectReturn(row)">拒绝归还</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
    <Pager v-model:page="page" :size="size" :total="total" @change="load" />
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'

import { returnApi } from '@/api'
import BookLink from '@/components/BookLink.vue'
import Pager from '@/components/Pager.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePaged } from '@/composables/usePaged'
import { RETURN_STATUS, formatTime } from '@/utils/constants'
import { confirm } from '@/utils/confirm'

const params = reactive({ status: '' })
const { items, total, page, size, loading, load, search } = usePaged(returnApi.received, params)

onMounted(load)

async function confirmReturn(row) {
  if (!(await confirm(`确认已收到《${row.book.title}》？确认后图书重新进入待漂流，可以再次被借阅。`))) return
  try {
    await returnApi.confirm(row.id)
  } finally {
    load()
  }
}

async function rejectReturn(row) {
  if (!(await confirm(`拒绝这次归还？图书将保持已借出状态，借书人可以重新提交归还申请。`))) return
  try {
    await returnApi.reject(row.id)
  } finally {
    load()
  }
}
</script>
