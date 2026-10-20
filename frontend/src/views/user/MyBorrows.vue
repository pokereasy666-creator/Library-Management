<template>
  <div>
    <div class="toolbar">
      <el-select v-model="params.status" placeholder="全部状态" clearable style="width: 140px" @change="search">
        <el-option v-for="(v, k) in BORROW_STATUS" :key="k" :label="v.label" :value="k" />
      </el-select>
      <span class="muted">展开每一行可以查看这次借阅的完整流转记录</span>
    </div>
    <el-table v-loading="loading" :data="items" empty-text="还没有借阅申请">
      <el-table-column type="expand">
        <template #default="{ row }">
          <el-timeline class="timeline">
            <el-timeline-item :timestamp="formatTime(row.created_at)">
              提交借阅申请{{ row.message ? `：${row.message}` : '' }}
            </el-timeline-item>
            <el-timeline-item v-if="row.handled_at" :timestamp="formatTime(row.handled_at)" :type="handledType(row.status)">
              {{ handledText(row.status) }}
            </el-timeline-item>
            <template v-for="r in row.returns" :key="r.id">
              <el-timeline-item :timestamp="formatTime(r.created_at)">
                提交归还申请{{ r.message ? `：${r.message}` : '' }}
              </el-timeline-item>
              <el-timeline-item
                v-if="r.handled_at"
                :timestamp="formatTime(r.handled_at)"
                :type="r.status === 'CONFIRMED' ? 'success' : 'danger'"
              >
                {{ r.status === 'CONFIRMED' ? '发布人确认归还，借阅结束' : '发布人拒绝归还' }}
              </el-timeline-item>
            </template>
          </el-timeline>
        </template>
      </el-table-column>
      <el-table-column label="图书" min-width="160">
        <template #default="{ row }"><BookLink :book="row.book" /></template>
      </el-table-column>
      <el-table-column label="发布人" width="110">
        <template #default="{ row }">{{ row.owner.nickname }}</template>
      </el-table-column>
      <el-table-column prop="message" label="申请留言" min-width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><StatusTag :map="BORROW_STATUS" :value="row.status" /></template>
      </el-table-column>
      <el-table-column label="申请时间" width="150">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'APPROVED'">
            <span v-if="hasPendingReturn(row)" class="muted">归还待确认</span>
            <el-button v-else link type="primary" @click="openReturn(row)">申请归还</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
    <Pager v-model:page="page" :size="size" :total="total" @change="load" />

    <el-dialog v-model="returnVisible" title="申请归还" width="min(480px, 92vw)">
      <p class="muted">归还《{{ current?.book.title }}》，发布人确认收到后借阅结束。</p>
      <el-input
        v-model="returnMessage"
        type="textarea"
        :rows="4"
        maxlength="255"
        show-word-limit
        placeholder="归还留言（选填），例如归还方式、时间"
      />
      <template #footer>
        <el-button @click="returnVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitReturn">提交归还申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { borrowApi, returnApi } from '@/api'
import BookLink from '@/components/BookLink.vue'
import Pager from '@/components/Pager.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePaged } from '@/composables/usePaged'
import { BORROW_STATUS, formatTime } from '@/utils/constants'

const params = reactive({ status: '' })
const { items, total, page, size, loading, load, search } = usePaged(borrowApi.mine, params)
const returnVisible = ref(false)
const returnMessage = ref('')
const submitting = ref(false)
const current = ref(null)

onMounted(load)

const HANDLED = {
  APPROVED: ['发布人同意借阅，图书已借出', 'primary'],
  RETURNED: ['发布人同意借阅，图书已借出', 'primary'],
  REJECTED: ['发布人拒绝了借阅申请', 'danger'],
  CANCELED: ['申请已失效（图书已借给他人、下架或重新审核）', 'info'],
}
const handledText = (status) => HANDLED[status]?.[0] || ''
const handledType = (status) => HANDLED[status]?.[1] || 'info'
const hasPendingReturn = (row) => row.returns.some((r) => r.status === 'PENDING')

function openReturn(row) {
  current.value = row
  returnMessage.value = ''
  returnVisible.value = true
}

async function submitReturn() {
  submitting.value = true
  try {
    await returnApi.apply({ borrow_id: current.value.id, message: returnMessage.value })
    returnVisible.value = false
    load()
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.timeline {
  padding: 8px 24px 0;
}
</style>
