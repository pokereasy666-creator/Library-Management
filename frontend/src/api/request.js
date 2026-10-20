import axios from 'axios'
import { ElMessage } from 'element-plus'

import router from '@/router'
import { useUserStore } from '@/stores/user'

const request = axios.create({ baseURL: '/api', timeout: 15000 })

request.interceptors.request.use((config) => {
  const store = useUserStore()
  if (store.token) {
    config.headers.Authorization = `Bearer ${store.token}`
  }
  return config
})

// 后端统一返回 {code, msg, data}：写操作成功弹出 msg，任何失败都弹出错误提示
request.interceptors.response.use(
  (response) => {
    const body = response.data
    if (response.config.method !== 'get') {
      ElMessage.success(body.msg)
    }
    return body
  },
  (error) => {
    const status = error.response?.status
    const msg =
      error.response?.data?.msg || (error.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '网络错误，请稍后重试')
    ElMessage.error(msg)
    if (status === 401) {
      useUserStore().logout()
      const current = router.currentRoute.value
      if (current.name !== 'login') {
        router.push({ name: 'login', query: { redirect: current.fullPath } })
      }
    }
    return Promise.reject(error)
  },
)

export default request
