<template>
  <div class="service-detail-view">
    <div class="page-header">
      <el-page-header content="服务详情" @back="$router.back()" />
      <h2>{{ service.name }}</h2>
      <p>{{ service.label }}</p>
    </div>

    <el-row :gutter="20" class="mb-20">
      <el-col :xs="24" :sm="8">
        <el-card class="glass-card" shadow="hover">
          <div class="detail-item">
            <span class="label">端口</span>
            <span class="value">{{ service.port }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="glass-card" shadow="hover">
          <div class="detail-item">
            <span class="label">状态</span>
            <el-tag :type="statusType(service.status)" effect="plain">{{ service.statusText }}</el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="glass-card" shadow="hover">
          <div class="detail-item">
            <span class="label">响应时间</span>
            <span class="value text-gradient">{{ service.rt }}ms</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :sm="12">
        <el-card class="glass-card" shadow="hover">
          <div class="card-title">资源占用</div>
          <el-progress :percentage="service.cpu" :format="() => 'CPU ' + service.cpu + '%'" class="mb-20" />
          <el-progress :percentage="service.memory" :format="() => '内存 ' + service.memory + '%'" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card class="glass-card" shadow="hover">
          <div class="card-title">健康检查</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="服务名">{{ service.name }}</el-descriptions-item>
            <el-descriptions-item label="显示名">{{ service.label }}</el-descriptions-item>
            <el-descriptions-item label="端口">{{ service.port }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ service.statusText }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const service = ref({
  name: route.params.id || 'unknown',
  label: '未知服务',
  port: '--',
  status: 'unknown',
  statusText: '未知',
  rt: '--',
  cpu: 0,
  memory: 0,
})

const allServices = [
  { name: 'gateway', label: 'API 网关', port: ':8080', status: 'healthy', statusText: '正常', rt: 28, cpu: 12, memory: 35 },
  { name: 'embeat', label: 'Embeat 引擎', port: ':7860', status: 'healthy', statusText: '正常', rt: 87, cpu: 45, memory: 62 },
  { name: 'qdrant', label: 'Qdrant', port: ':6333', status: 'healthy', statusText: '正常', rt: 15, cpu: 78, memory: 82 },
  { name: 'profile', label: '画像服务', port: ':8090', status: 'degraded', statusText: '降级', rt: 'N/A', cpu: 5, memory: 22 },
  { name: 'postgres', label: 'PostgreSQL', port: ':5432', status: 'healthy', statusText: '正常', rt: 12, cpu: 22, memory: 45 },
]

const found = allServices.find((s) => s.name === route.params.id)
if (found) service.value = found

function statusType(status) {
  const map = { healthy: 'success', degraded: 'warning', down: 'danger', unknown: 'info' }
  return map[status] || 'info'
}
</script>

<style scoped>
.service-detail-view { min-height: calc(100vh - 112px); background: var(--bg-primary); padding: 24px; }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin: 16px 0 4px; }
.page-header p { color: var(--text-secondary); font-size: 14px; }
.mb-20 { margin-bottom: 20px; }
.card-title { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.detail-item { display: flex; justify-content: space-between; align-items: center; }
.detail-item .label { color: var(--text-secondary); }
.detail-item .value { color: var(--text-primary); font-weight: 600; }
.text-gradient { color: var(--primary-color); }
</style>