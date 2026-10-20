<template>
  <div v-loading="loading" class="page">
    <el-empty v-if="notFound" description="图书不存在或暂不可见">
      <el-button type="primary" @click="router.push('/')">返回首页</el-button>
    </el-empty>

    <template v-if="book">
      <el-card>
        <div class="detail">
          <div class="cover">
            <BookCover :src="book.cover_url" :title="book.title" />
          </div>
          <div class="info">
            <h1>
              {{ book.title }}
              <StatusTag :map="BOOK_STATUS" :value="book.status" />
            </h1>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="作者">{{ book.author }}</el-descriptions-item>
              <el-descriptions-item label="分类">{{ book.category_name }}</el-descriptions-item>
              <el-descriptions-item label="新旧程度">{{ book.condition }}</el-descriptions-item>
              <el-descriptions-item label="发布人">{{ book.owner.nickname }}</el-descriptions-item>
              <el-descriptions-item label="发布时间">{{ formatTime(book.created_at) }}</el-descriptions-item>
            </el-descriptions>
            <h3>图书简介</h3>
            <p class="description">{{ book.description || '暂无简介' }}</p>

            <el-alert
              v-if="isOwner && book.status === 'OFF_SHELF' && book.review_note"
              type="warning"
              :closable="false"
              :title="`审核驳回：${book.review_note}`"
              class="mb"
            />
            <div class="ops">
              <template v-if="isOwner">
                <el-button v-if="book.status !== 'BORROWED'" @click="router.push(`/books/${book.id}/edit`)">
                  编辑图书
                </el-button>
                <span class="muted">这是你发布的图书</span>
              </template>
              <el-button v-else-if="book.status === 'AVAILABLE'" type="primary" @click="openBorrow">申请借阅</el-button>
              <span v-else-if="book.status === 'BORROWED'" class="muted">图书已借出，归还后可再次借阅</span>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="comments">
        <template #header>评论留言（{{ comments.length }}）</template>
        <div v-if="store.isLogin" class="comment-form">
          <el-input
            v-model="commentText"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="说说你对这本书的看法"
          />
          <el-button type="primary" :loading="commenting" :disabled="!commentText.trim()" @click="submitComment">
            发表评论
          </el-button>
        </div>
        <p v-else class="muted">
          <router-link :to="{ name: 'login', query: { redirect: route.fullPath } }">登录</router-link> 后可以发表评论
        </p>
        <el-empty v-if="comments.length === 0" description="还没有评论" :image-size="80" />
        <div v-for="c in comments" :key="c.id" class="comment">
          <div>
            <strong>{{ c.user.nickname }}</strong>
            <span class="muted">{{ formatTime(c.created_at) }}</span>
          </div>
          <p>{{ c.content }}</p>
        </div>
      </el-card>
    </template>

    <el-dialog v-model="borrowVisible" title="申请借阅" width="min(480px, 92vw)">
      <el-input
        v-model="borrowMessage"
        type="textarea"
        :rows="4"
        maxlength="255"
        show-word-limit
        placeholder="给发布人留言（选填），例如借阅时长、联系方式"
      />
      <template #footer>
        <el-button @click="borrowVisible = false">取消</el-button>
        <el-button type="primary" :loading="borrowing" @click="submitBorrow">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { bookApi, borrowApi } from '@/api'
import BookCover from '@/components/BookCover.vue'
import StatusTag from '@/components/StatusTag.vue'
import { useUserStore } from '@/stores/user'
import { BOOK_STATUS, formatTime } from '@/utils/constants'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const book = ref(null)
const comments = ref([])
const loading = ref(false)
const notFound = ref(false)
const commentText = ref('')
const commenting = ref(false)
const borrowVisible = ref(false)
const borrowMessage = ref('')
const borrowing = ref(false)

const isOwner = computed(() => book.value && store.user?.id === book.value.owner.id)

async function load() {
  loading.value = true
  notFound.value = false
  try {
    const id = route.params.id
    book.value = (await bookApi.detail(id)).data
    comments.value = (await bookApi.comments(id)).data
  } catch {
    book.value = null
    notFound.value = true
  } finally {
    loading.value = false
  }
}

watch(() => route.params.id, (id) => id && load(), { immediate: true })

function openBorrow() {
  if (!store.isLogin) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  borrowMessage.value = ''
  borrowVisible.value = true
}

async function submitBorrow() {
  borrowing.value = true
  try {
    await borrowApi.apply({ book_id: book.value.id, message: borrowMessage.value })
    borrowVisible.value = false
  } finally {
    borrowing.value = false
  }
}

async function submitComment() {
  commenting.value = true
  try {
    const res = await bookApi.addComment(book.value.id, commentText.value)
    comments.value.push(res.data)
    commentText.value = ''
  } finally {
    commenting.value = false
  }
}
</script>

<style scoped>
.detail {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
}

.info h1 {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 16px;
  font-size: 24px;
}

.description {
  white-space: pre-wrap;
  line-height: 1.7;
  color: #606266;
}

.ops {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mb {
  margin-bottom: 12px;
}

.comments {
  margin-top: 16px;
}

.comment-form {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  margin-bottom: 16px;
}

.comment {
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.comment .muted {
  margin-left: 8px;
}

.comment p {
  margin: 6px 0 0;
  white-space: pre-wrap;
}

@media (max-width: 640px) {
  .detail {
    grid-template-columns: 1fr;
  }
  .cover {
    max-width: 220px;
  }
}
</style>
