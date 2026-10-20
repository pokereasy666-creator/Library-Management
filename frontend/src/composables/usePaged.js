import { ref } from 'vue'

// 分页列表：fetcher 接收 {page, size, ...params}，返回后端的 {code, msg, data: {total, items}}
export function usePaged(fetcher, params = {}, size = 10) {
  const items = ref([])
  const total = ref(0)
  const page = ref(1)
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const query = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== '' && v != null))
      const res = await fetcher({ page: page.value, size, ...query })
      items.value = res.data.items
      total.value = res.data.total
    } finally {
      loading.value = false
    }
  }

  function search() {
    page.value = 1
    return load()
  }

  return { items, total, page, size, loading, load, search }
}
