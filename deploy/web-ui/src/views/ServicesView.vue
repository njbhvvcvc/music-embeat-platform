<template>
  <div class="services-view">
    <div class="page-header">
      <h2>服务概览</h2>
      <p>监控所有微服务的运行状态和健康指标</p>
    </div>

    <el-table :data="services" style="width: 100%" v-loading="loading">
      <el-table-column prop="name" label="服务名称" width="140">
        <template #default="{ row }">
          <span class="status-dot" :class="row.status"></span>
          {{ row.label }}
        </template>
      </el-table-column>
      <el-table-column prop="port" label="端口" width="120" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" effect="plain">{{ row.statusText }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="延迟" width="120">
        <template #default="{ row }">
          <span class="text-gradient">{{ row.rt }}ms</span>
        </template>
      </el-table-column>
      <el-table-column label="CPU" width="120">
        <template #default="{ row }">
          <el-progress :percentage="row.cpu" :format="() => ''" />
        </template>
      </el-table-column>
      <el-table-column label="内存" width="120">
        <template #default="{ row }">
          <el-progress :percentage="row.memory" :format="() => ''" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button type="primary" link @click="testService(row)">测试</el-button>
          <el-button type="primary" link @click="viewDetails(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'

const loading = ref(false)
const services = ref([
  { name: 'gateway', label: 'API 网关', port: ':8080', status: 'healthy', statusText: '正常', rt: 28, cpu: 12, memory: 35 },
  { name: 'embeat', label: 'Embeat 引擎', port: ':7860', status: 'healthy', statusText: '正常', rt: 87, cpu: 45, memory: 62 },
  { name: 'qdrant', label: 'Qdrant', port: ':6333', status: 'healthy', statusText: '正常', rt: 15, cpu: 78, memory: 82 },
  { name: 'profile', label: '画像服务', port: ':8090', status: 'degraded', statusText: '降级', rt: 'N/A', cpu: 5, memory: 22 },
  { name: 'postgres', label: 'PostgreSQL', port: ':5432', status: 'healthy', statusText: '正常', rt: 12, cpu: 22, memory: 45 },
])

function statusType(status) {
  const map = { healthy: 'success', degraded: 'warning', down: 'danger', unknown: 'info' }
  return map[status] || 'info'
}

async function testService(row) {
  const res = await api.get(`/v1/health?service=${row.name}`)
  console.log(res.data)
}

function viewDetails(row) {
  // 路由到详情页
}

onMounted(() => {
  // 开始轮询
})
</script>

<style scoped>
.services-view { min-height: calc(100vh - 112px); background: var(--bg-primary); }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-header p { color: var(--text-secondary); font-size: 14px; }
.mb-20 { margin-bottom: 20px; }
.text-gradient { color: var(--primary-color); }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; }
.status-dot.healthy { background: #10b981; }
.status-dot.degraded { background: #f59e0b; }
.status-dot.down { background: #ef4444; }
</style>
