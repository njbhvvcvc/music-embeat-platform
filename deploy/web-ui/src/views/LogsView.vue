<template>
  <div class="logs-view">
    <div class="page-header">
      <h2>日志查看</h2>
      <p>实时监控服务日志和异常告警</p>
    </div>

    <el-card class="mb-20">
      <el-form :inline="true">
        <el-form-item label="服务">
          <el-select v-model="selectedService" placeholder="选择服务" style="width: 180px">
            <el-option label="全部" value="all" />
            <el-option label="网关" value="gateway" />
            <el-option label="Embeat" value="embeat" />
            <el-option label="Qdrant" value="qdrant" />
            <el-option label="Profile" value="profile" />
            <el-option label="Postgres" value="postgres" />
          </el-select>
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="selectedLevel" placeholder="选择级别" style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="INFO" value="INFO" />
            <el-option label="WARN" value="WARN" />
            <el-option label="ERROR" value="ERROR" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="refresh">刷新</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="logs-container" shadow="hover">
      <div class="logs-list" ref="logsContainer">
        <div v-for="(log, i) in filteredLogs" :key="i" class="log-item" :class="log.level.toLowerCase()">
          <span class="log-level">{{ log.level }}</span>
          <span class="log-service">[{{ log.service }}]</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
        <el-empty v-if="!filteredLogs.length && !loading" description="暂无日志" :image-size="60" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/client'

const logsContainer = ref()
const selectedService = ref('all')
const selectedLevel = ref('')
const logs = ref([])
const loading = ref(false)
let timer = null

const filteredLogs = computed(() => {
  if (!selectedLevel.value) return logs.value
  return logs.value.filter((l) => l.level === selectedLevel.value)
})

async function refresh() {
  loading.value = true
  try {
    const res = await api.get('/v1/ops/logs', {
      params: { service: selectedService.value, limit: 300 },
    })
    logs.value = res.data.data || []
  } catch (e) {
    ElMessage.error('日志拉取失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 10000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.logs-view { min-height: calc(100vh - 112px); background: var(--bg-primary); }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-header p { color: var(--text-secondary); font-size: 14px; }
.mb-20 { margin-bottom: 20px; }
.logs-container { height: 500px; border-radius: 12px; }
.logs-list { height: 100%; overflow-y: auto; font-family: 'JetBrains Mono', monospace; }
.log-item { display: flex; align-items: center; gap: 12px; padding: 4px 16px; font-size: 12px; border-bottom: 1px solid var(--border-light); }
.log-time { color: var(--text-muted); width: 80px; flex-shrink: 0; }
.log-level { width: 60px; flex-shrink: 0; font-weight: 600; }
.log-level.INFO { color: #3b82f6; }
.log-level.WARN { color: #f59e0b; }
.log-level.ERROR { color: #ef4444; }
.log-service { color: #a78bfa; width: 100px; flex-shrink: 0; }
.log-msg { color: var(--text-secondary); flex: 1; word-break: break-all; }
</style>
