import { ElMessageBox } from 'element-plus'

export function confirm(message, title = '提示') {
  return ElMessageBox.confirm(message, title, { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' })
    .then(() => true)
    .catch(() => false)
}
