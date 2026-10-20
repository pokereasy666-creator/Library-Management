<template>
  <div class="page">
    <el-card>
      <el-tabs :model-value="tab" @tab-change="onTabChange">
        <el-tab-pane v-for="t in tabs" :key="t.name" :label="t.label" :name="t.name">
          <!-- 每次切换都重新挂载，保证看到的是最新状态 -->
          <component :is="t.component" v-if="tab === t.name" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import MyBooks from './MyBooks.vue'
import MyBorrows from './MyBorrows.vue'
import MyReturns from './MyReturns.vue'
import ProfileInfo from './ProfileInfo.vue'
import ReceivedBorrows from './ReceivedBorrows.vue'
import ReceivedReturns from './ReceivedReturns.vue'

const tabs = [
  { name: 'info', label: '基本信息', component: ProfileInfo },
  { name: 'books', label: '我发布的图书', component: MyBooks },
  { name: 'borrows', label: '我的借阅申请', component: MyBorrows },
  { name: 'received-borrows', label: '收到的借阅申请', component: ReceivedBorrows },
  { name: 'received-returns', label: '收到的归还申请', component: ReceivedReturns },
  { name: 'returns', label: '我的归还记录', component: MyReturns },
]

const route = useRoute()
const router = useRouter()
const tab = computed(() => (tabs.some((t) => t.name === route.query.tab) ? route.query.tab : 'info'))

function onTabChange(name) {
  router.replace({ query: { tab: name } })
}
</script>
