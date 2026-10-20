export const BOOK_STATUS = {
  PENDING: { label: '待审核', type: 'warning' },
  AVAILABLE: { label: '待漂流', type: 'success' },
  BORROWED: { label: '已借出', type: 'primary' },
  OFF_SHELF: { label: '已下架', type: 'info' },
}

export const BORROW_STATUS = {
  PENDING: { label: '待处理', type: 'warning' },
  APPROVED: { label: '借阅中', type: 'primary' },
  REJECTED: { label: '已拒绝', type: 'danger' },
  CANCELED: { label: '已失效', type: 'info' },
  RETURNED: { label: '已归还', type: 'success' },
}

export const RETURN_STATUS = {
  PENDING: { label: '待确认', type: 'warning' },
  CONFIRMED: { label: '已确认归还', type: 'success' },
  REJECTED: { label: '拒绝归还', type: 'danger' },
}

export const USER_STATUS = {
  ACTIVE: { label: '正常', type: 'success' },
  DISABLED: { label: '已禁用', type: 'danger' },
}

export const CONDITIONS = ['全新', '九成新', '八成新', '七成新及以下']

export function formatTime(value) {
  return value ? value.replace('T', ' ').slice(0, 16) : '-'
}
