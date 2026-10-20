import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.config.errorHandler = (err) => {
  // 接口错误已由请求拦截器弹窗提示，调用方只用它中断后续流程，这里不再重复输出
  if (err?.isAxiosError) return
  console.error(err)
}
app.mount('#app')
