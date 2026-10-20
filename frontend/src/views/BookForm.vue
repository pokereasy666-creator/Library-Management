<template>
  <div class="page">
    <el-card v-loading="loading" class="form-card">
      <template #header>{{ isEdit ? '编辑图书' : '发布图书' }}</template>
      <el-alert
        v-if="isEdit && !borrowed"
        type="info"
        show-icon
        :closable="false"
        title="保存后图书会重新进入【待审核】，管理员审核通过后才会在首页展示"
        class="mb"
      />
      <el-alert v-if="borrowed" type="warning" show-icon :closable="false" title="图书已借出，归还后才能编辑" class="mb" />

      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" :disabled="borrowed">
        <el-form-item label="书名" prop="title">
          <el-input v-model="form.title" maxlength="100" />
        </el-form-item>
        <el-form-item label="作者" prop="author">
          <el-input v-model="form.author" maxlength="50" />
        </el-form-item>
        <el-form-item label="图书分类" prop="category_id">
          <el-select v-model="form.category_id" placeholder="请选择分类" style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="新旧程度" prop="condition">
          <el-radio-group v-model="form.condition">
            <el-radio-button v-for="c in CONDITIONS" :key="c" :value="c">{{ c }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="图书简介" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="5" maxlength="2000" show-word-limit />
        </el-form-item>
        <el-form-item label="封面图片">
          <div>
            <el-upload
              :show-file-list="false"
              accept="image/jpeg,image/png,image/webp"
              :before-upload="beforeUpload"
              :http-request="uploadCover"
            >
              <div v-loading="uploading" class="cover-uploader">
                <img v-if="form.cover_url" :src="form.cover_url" alt="封面" />
                <div v-else class="cover-empty">
                  <el-icon :size="24"><Plus /></el-icon>
                  <span>上传封面</span>
                </div>
              </div>
            </el-upload>
            <div class="muted">支持 JPG / PNG / WEBP，不超过 2MB</div>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="submit">
            {{ isEdit ? '保存并重新提交审核' : '提交审核' }}
          </el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

import { bookApi } from '@/api'
import { CONDITIONS } from '@/utils/constants'

const MAX_COVER_BYTES = 2 * 1024 * 1024

const route = useRoute()
const router = useRouter()
const formRef = ref()
const categories = ref([])
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const borrowed = ref(false)
const isEdit = computed(() => route.name === 'edit-book')

const emptyForm = () => ({
  title: '',
  author: '',
  category_id: null,
  condition: '九成新',
  description: '',
  cover_url: '',
})
const form = reactive(emptyForm())

const rules = {
  title: [{ required: true, whitespace: true, message: '请输入书名', trigger: 'blur' }],
  author: [{ required: true, whitespace: true, message: '请输入作者', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择图书分类', trigger: 'change' }],
  condition: [{ required: true, message: '请选择新旧程度', trigger: 'change' }],
}

onMounted(async () => {
  categories.value = (await bookApi.categories()).data
})

// /publish 和 /books/:id/edit 共用这个组件，路由切换时组件会被复用，所以监听路由重新初始化
watch(
  () => route.fullPath,
  async () => {
    borrowed.value = false
    Object.assign(form, emptyForm())
    formRef.value?.clearValidate()
    if (!isEdit.value) return
    loading.value = true
    try {
      const book = (await bookApi.detail(route.params.id)).data
      for (const key of Object.keys(form)) form[key] = book[key]
      borrowed.value = book.status === 'BORROWED'
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

function beforeUpload(file) {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    ElMessage.error('仅支持 JPG、PNG、WEBP 格式的图片')
    return false
  }
  if (file.size > MAX_COVER_BYTES) {
    ElMessage.error('图片不能超过 2MB')
    return false
  }
  return true
}

async function uploadCover({ file }) {
  uploading.value = true
  try {
    form.cover_url = (await bookApi.uploadCover(file)).data.url
  } finally {
    uploading.value = false
  }
}

async function submit() {
  if (!(await formRef.value.validate().catch(() => false))) return
  saving.value = true
  try {
    if (isEdit.value) {
      await bookApi.update(route.params.id, form)
    } else {
      await bookApi.create(form)
    }
    router.push({ name: 'profile', query: { tab: 'books' } })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.form-card {
  max-width: 760px;
  margin: 0 auto;
}

.mb {
  margin-bottom: 16px;
}

.cover-uploader {
  width: 150px;
  height: 200px;
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
}

.cover-uploader:hover {
  border-color: var(--el-color-primary);
}

.cover-uploader img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 100%;
  color: #8c939d;
}
</style>
