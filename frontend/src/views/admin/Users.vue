<template>
  <div>
    <div class="toolbar">
      <el-input
        v-model="params.keyword"
        placeholder="用户名或昵称"
        clearable
        style="max-width: 240px"
        @keyup.enter="search"
        @clear="search"
      />
      <el-button type="primary" @click="search">查询</el-button>
    </div>
    <el-table v-loading="loading" :data="items">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" min-width="120" />
      <el-table-column prop="nickname" label="昵称" min-width="120" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'ADMIN' ? 'danger' : 'info'" size="small">
            {{ row.role === 'ADMIN' ? '管理员' : '普通用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><StatusTag :map="USER_STATUS" :value="row.status" /></template>
      </el-table-column>
      <el-table-column label="注册时间" width="150">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <template v-if="row.role !== 'ADMIN'">
            <el-button v-if="row.status === 'ACTIVE'" link type="danger" @click="setStatus(row, 'DISABLED')">
              禁用
            </el-button>
            <el-button v-else link type="primary" @click="setStatus(row, 'ACTIVE')">启用</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
    <Pager v-model:page="page" :size="size" :total="total" @change="load" />
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'

import { adminApi } from '@/api'
import Pager from '@/components/Pager.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePaged } from '@/composables/usePaged'
import { USER_STATUS, formatTime } from '@/utils/constants'
import { confirm } from '@/utils/confirm'

const params = reactive({ keyword: '' })
const { items, total, page, size, loading, load, search } = usePaged(adminApi.users, params)

onMounted(load)

async function setStatus(row, status) {
  const text = status === 'DISABLED' ? `禁用用户 ${row.username}？禁用后该用户立即无法登录和操作。` : `启用用户 ${row.username}？`
  if (!(await confirm(text))) return
  await adminApi.setUserStatus(row.id, status)
  load()
}
</script>
