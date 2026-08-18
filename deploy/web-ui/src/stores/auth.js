import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('embeat_token') || '')
  const user = ref(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username, password) {
    loading.value = true
    try {
      const res = await api.post('/auth/login', { username, password })
      token.value = res.data.token
      user.value = res.data.user
      localStorage.setItem('embeat_token', token.value)
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      return { success: true }
    } catch (error) {
      return { success: false, message: error.response?.data?.msg || '登录失败' }
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      const res = await api.get('/auth/me')
      user.value = res.data
    } catch (error) {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('embeat_token')
    delete api.defaults.headers.common['Authorization']
  }

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('embeat_token', newToken)
    api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
  }

  return {
    token,
    user,
    loading,
    isAuthenticated,
    login,
    fetchUser,
    logout,
    setToken,
  }
})