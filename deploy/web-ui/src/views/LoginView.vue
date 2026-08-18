<template>
  <div class="login-bg">
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <div class="login-logo">LOGO</div>
          <h1 class="text-gradient">Embeat Platform</h1>
          <p class="login-desc">Music Recommendation &amp; Operations Console</p>
        </div>
        <el-form ref="formRef" :model="form" :rules="rules">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="Username" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="Password" />
          </el-form-item>
          <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">登录</el-button>
        </el-form>
        <p class="hint">默认: admin / embeat123</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({ username: 'admin', password: 'embeat123' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate()
  loading.value = true
  try {
    const result = await authStore.login(form.username, form.password)
    if (result.success) {
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error(result.message)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-bg { min-height: 100vh; background: linear-gradient(135deg, #0a0e17, #111827); display: flex; align-items: center; justify-content: center; }
.login-container { z-index: 2; }
.login-card { width: 420px; padding: 48px 40px; background: #1e293b; border: 1px solid #334155; border-radius: 24px; }
.login-header { text-align: center; margin-bottom: 32px; }
.login-logo { width: 64px; height: 64px; margin: 0 auto 16px; background: linear-gradient(135deg, #1e90ff, #4da6ff); border-radius: 16px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }
.text-gradient { background: linear-gradient(135deg, #1e90ff, #4da6ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.login-desc { font-size: 14px; color: #64748b; }
.login-btn { width: 100%; height: 48px; font-size: 16px; border-radius: 12px; background: linear-gradient(135deg, #1e90ff, #0066cc); }
.hint { text-align: center; margin-top: 20px; color: #64748b; font-size: 12px; }
</style>
