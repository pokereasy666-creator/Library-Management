import request from './request'

export const authApi = {
  register: (data) => request.post('/auth/register', data),
  login: (data) => request.post('/auth/login', data),
  me: () => request.get('/users/me'),
}

export const bookApi = {
  categories: () => request.get('/categories'),
  list: (params) => request.get('/books', { params }),
  detail: (id) => request.get(`/books/${id}`),
  create: (data) => request.post('/books', data),
  update: (id, data) => request.put(`/books/${id}`, data),
  offShelf: (id) => request.post(`/books/${id}/off-shelf`),
  mine: (params) => request.get('/users/me/books', { params }),
  comments: (id) => request.get(`/books/${id}/comments`),
  addComment: (id, content) => request.post(`/books/${id}/comments`, { content }),
  uploadCover: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request.post('/uploads/cover', form)
  },
}

export const borrowApi = {
  apply: (data) => request.post('/borrows', data),
  mine: (params) => request.get('/borrows/mine', { params }),
  received: (params) => request.get('/borrows/received', { params }),
  approve: (id) => request.post(`/borrows/${id}/approve`),
  reject: (id) => request.post(`/borrows/${id}/reject`),
}

export const returnApi = {
  apply: (data) => request.post('/returns', data),
  mine: (params) => request.get('/returns/mine', { params }),
  received: (params) => request.get('/returns/received', { params }),
  confirm: (id) => request.post(`/returns/${id}/confirm`),
  reject: (id) => request.post(`/returns/${id}/reject`),
}

export const adminApi = {
  users: (params) => request.get('/admin/users', { params }),
  setUserStatus: (id, status) => request.put(`/admin/users/${id}/status`, { status }),
  books: (params) => request.get('/admin/books', { params }),
  approveBook: (id) => request.post(`/admin/books/${id}/approve`),
  rejectBook: (id, note) => request.post(`/admin/books/${id}/reject`, { note }),
  deleteBook: (id) => request.delete(`/admin/books/${id}`),
  createCategory: (name) => request.post('/admin/categories', { name }),
  updateCategory: (id, name) => request.put(`/admin/categories/${id}`, { name }),
  deleteCategory: (id) => request.delete(`/admin/categories/${id}`),
  borrows: (params) => request.get('/admin/borrows', { params }),
  returns: (params) => request.get('/admin/returns', { params }),
}
