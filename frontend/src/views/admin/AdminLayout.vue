<template>
  <div class="page">
    <el-menu :default-active="route.path" mode="horizontal" router class="admin-menu">
      <el-menu-item index="/admin/books">图书审核</el-menu-item>
      <el-menu-item index="/admin/users">用户管理</el-menu-item>
      <el-menu-item index="/admin/categories">分类管理</el-menu-item>
      <el-menu-item index="/admin/borrows">借阅记录</el-menu-item>
      <el-menu-item index="/admin/returns">归还记录</el-menu-item>
    </el-menu>
    <el-card>
      <router-view />
    </el-card>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<style scoped>
.admin-menu {
  margin-bottom: 16px;
  border-radius: 4px;
}
</style>
