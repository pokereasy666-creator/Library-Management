<template>
  <div class="layout">
    <header class="header">
      <div class="header-inner">
        <router-link to="/" class="logo">📚 图书漂流</router-link>
        <nav class="nav">
          <router-link to="/">首页</router-link>
          <router-link v-if="store.isLogin" to="/me">个人中心</router-link>
          <router-link v-if="store.isAdmin" to="/admin">管理后台</router-link>
        </nav>
        <div class="actions">
          <template v-if="store.isLogin">
            <el-button type="primary" :icon="Plus" @click="router.push('/publish')">发布图书</el-button>
            <el-dropdown @command="onCommand">
              <span class="user-name">
                {{ store.user?.nickname }}
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item v-if="store.isAdmin" command="admin">管理后台</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button @click="router.push('/login')">登录</el-button>
            <el-button type="primary" @click="router.push('/register')">注册</el-button>
          </template>
        </div>
      </div>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown, Plus } from '@element-plus/icons-vue'

import { authApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()

onMounted(async () => {
  // 刷新页面时同步一次用户信息；token 失效会被拦截器处理并跳转登录
  if (store.isLogin) {
    const res = await authApi.me()
    store.setUser(res.data)
  }
})

function onCommand(command) {
  if (command === 'profile') router.push('/me')
  if (command === 'admin') router.push('/admin')
  if (command === 'logout') {
    store.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  }
}
</script>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-inner {
  display: flex;
  align-items: center;
  gap: 24px;
  max-width: 1200px;
  height: 60px;
  margin: 0 auto;
  padding: 0 16px;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  white-space: nowrap;
}

.nav {
  display: flex;
  gap: 20px;
  flex: 1;
}

.nav a {
  color: #606266;
}

.nav a.router-link-exact-active,
.nav a[href='/admin'].router-link-active {
  color: var(--el-color-primary);
  font-weight: 600;
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  outline: none;
}

@media (max-width: 640px) {
  .header-inner {
    gap: 12px;
  }
  .nav {
    display: none;
  }
}
</style>
