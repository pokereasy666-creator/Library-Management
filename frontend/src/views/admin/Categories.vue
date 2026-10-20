<template>
  <div>
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="create">新增分类</el-button>
    </div>
    <el-table v-loading="loading" :data="categories" style="max-width: 600px">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="分类名称" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button link type="primary" @click="rename(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

import { adminApi, bookApi } from '@/api'
import { confirm } from '@/utils/confirm'

const categories = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    categories.value = (await bookApi.categories()).data
  } finally {
    loading.value = false
  }
}

onMounted(load)

function askName(title, inputValue = '') {
  return ElMessageBox.prompt('分类名称', title, {
    inputValue,
    inputValidator: (v) => (v && v.trim() && v.trim().length <= 32) || '请输入 1-32 个字符的分类名称',
    confirmButtonText: '保存',
    cancelButtonText: '取消',
  })
    .then(({ value }) => value.trim())
    .catch(() => null)
}

async function create() {
  const name = await askName('新增分类')
  if (!name) return
  await adminApi.createCategory(name)
  load()
}

async function rename(row) {
  const name = await askName('编辑分类', row.name)
  if (!name || name === row.name) return
  await adminApi.updateCategory(row.id, name)
  load()
}

async function remove(row) {
  if (!(await confirm(`确定删除分类「${row.name}」吗？`))) return
  await adminApi.deleteCategory(row.id)
  load()
}
</script>
