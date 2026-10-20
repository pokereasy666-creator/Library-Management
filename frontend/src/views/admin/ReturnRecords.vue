<template>
  <div>
    <div class="toolbar">
      <el-select v-model="params.status" placeholder="全部状态" clearable style="width: 140px" @change="search">
        <el-option v-for="(v, k) in RETURN_STATUS" :key="k" :label="v.label" :value="k" />
      </el-select>
    </div>
    <el-table v-loading="loading" :data="items" empty-text="暂无归还记录">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="图书" min-width="150">
        <template #default="{ row }"><BookLink :book="row.book" /></template>
      </el-table-column>
      <el-table-column label="借书人" width="110">
        <template #default="{ row }">{{ row.borrower.nickname }}</template>
      </el-table-column>
      <el-table-column label="发布人" width="110">
        <template #default="{ row }">{{ row.owner.nickname }}</template>
      </el-table-column>
      <el-table-column prop="message" label="归还留言" min-width="140" show-overflow-tooltip />
      <el-table-column label="处理状态" width="100">
        <template #default="{ row }"><StatusTag :map="RETURN_STATUS" :value="row.status" /></template>
      </el-table-column>
      <el-table-column label="申请时间" width="150">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="处理时间" width="150">
        <template #default="{ row }">{{ formatTime(row.handled_at) }}</template>
      </el-table-column>
    </el-table>
    <Pager v-model:page="page" :size="size" :total="total" @change="load" />
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'

import { adminApi } from '@/api'
import BookLink from '@/components/BookLink.vue'
import Pager from '@/components/Pager.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePaged } from '@/composables/usePaged'
import { RETURN_STATUS, formatTime } from '@/utils/constants'

const params = reactive({ status: '' })
const { items, total, page, size, loading, load, search } = usePaged(adminApi.returns, params)

onMounted(load)
</script>
