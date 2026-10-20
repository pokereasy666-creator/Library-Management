<template>
  <el-descriptions v-if="user" :column="1" border style="max-width: 560px">
    <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
    <el-descriptions-item label="昵称">{{ user.nickname }}</el-descriptions-item>
    <el-descriptions-item label="角色">{{ user.role === 'ADMIN' ? '管理员' : '普通用户' }}</el-descriptions-item>
    <el-descriptions-item label="注册时间">{{ formatTime(user.created_at) }}</el-descriptions-item>
  </el-descriptions>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import { authApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { formatTime } from '@/utils/constants'

const store = useUserStore()
const user = ref(store.user)

onMounted(async () => {
  user.value = (await authApi.me()).data
  store.setUser(user.value)
})
</script>
