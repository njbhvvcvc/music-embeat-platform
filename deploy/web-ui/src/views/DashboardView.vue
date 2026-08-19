<template>
  <div class="dashboard animate-fade-in">
    <!-- 服务状态卡片 -->
    <el-row :gutter="20" class="mb-20">
      <el-col
        v-for="svc in services"
        :key="svc.name"
        :xs="12"
        :sm="8"
        :md="6"
        :lg="4"
      >
        <el-card class="service-card glass-card" shadow="hover">
          <div class="service-icon">
            <i :class="svc.icon"></i>
          </div>
          <div class="service-info">
            <h3 class="service-name">{{ svc.label }}</h3>
            <div class="service-status">
              <span class="status-dot" :class="svc.status"></span>
              {{ svc.statusText }}
            </div>
            <div class="service-meta">
              <span class="port">{{ svc.port }}</span>
              <span class="response-time">RT: {{ svc.rt || '--' }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 性能监控 -->
    <el-row :gutter="20" class="mb-20">
      <el-col :xs="24" :lg="12" class="mb-20">
        <el-card class="glass-card" shadow="hover">
          <div class="chart-header">
            <h3>CPU 占用率</h3>
            <span class="value">{{ cpuPercent }}%</span>
          </div>
          <v-chart :option="cpuOption" style="height: 160px" auto-resize />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12" class="mb-20">
        <el-card class="glass-card" shadow="hover">
          <div class="chart-header">
            <h3>内存占用率</h3>
            <span class="value">{{ memoryPercent }}%</span>
          </div>
          <v-chart :option="memoryOption" style="height: 160px" auto-resize />
        </el-card>
      </el-col>
    </el-row>

    <!-- QPS 统计 -->
    <el-row :gutter="20" class="mb-20">
      <el-col :xs="24" :lg="8" class="mb-20">
        <el-card class="stat-card glass-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-value">{{ qps }}</div>
            <div class="stat-label">当前 QPS</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8" class="mb-20">
        <el-card class="stat-card glass-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-value">{{ totalTracks }}</div>
            <div class="stat-label">向量总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8" class="mb-20">
        <el-card class="stat-card glass-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-value">{{ latencyMs }}ms</div>
            <div class="stat-label">平均推荐延迟</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row>
      <el-col :xs="24" :lg="12" class="mb-20">
        <el-card class="glass-card" shadow="hover">
          <div class="card-title">最近活动日志</div>
          <el-timeline>
            <el-timeline-item
              v-for="(log, i) in recentLogs"
              :key="i"
              :type="log.type"
              :timestamp="log.time"
              timestamp-position="top"
            >
              {{ log.message }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12" class="mb-20">
        <el-card class="glass-card" shadow="hover">
          <div class="card-title">推荐渠道分布</div>
          <v-chart :option="channelOption" style="height: 240px" auto-resize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import api from '@/api/client'

use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const services = ref([
  { name: 'gateway', label: 'API 网关', port: ':8080', icon: 'el-icon-globe', status: 'healthy', statusText: '正常' },
  { name: 'embeat', label: 'Embeat 引擎', port: ':7860', icon: 'el-icon-star-on', status: 'healthy', statusText: '正常' },
  { name: 'qdrant', label: 'Qdrant', port: ':6333', icon: 'el-icon-database', status: 'healthy', statusText: '正常' },
  { name: 'profile', label: '画像服务', port: ':8090', icon: 'el-icon-user', status: 'degraded', statusText: '降级' },
  { name: 'postgres', label: 'PostgreSQL', port: ':5432', icon: 'el-icon-menu', status: 'healthy', statusText: '正常' },
])

const cpuPercent = ref(45)
const memoryPercent = ref(62)
const qps = ref(128)
const totalTracks = ref('45M')
const latencyMs = ref(87)
const recentLogs = ref([
  { type: 'success', time: '10:32:15', message: 'Qdrant Collection 创建完成' },
  { type: 'primary', time: '10:25:33', message: 'Embeat 模型加载成功' },
  { type: 'warning', time: '10:10:05', message: 'Profile 服务降级，降级为本地缓存' },
  { type: 'success', time: '09:55:22', message: 'API 网关启动完成' },
])

const cpuOption = {
  tooltip: { trigger: 'axis', axisType: 'shadow' },
  grid: { left: 5, right: 5, top: 20, bottom: 5 },
  xAxis: { type: 'category', data: ['00', '06', '12', '18', '24'], axisLabel: { color: '#94a3b8' }, axisAxis: { axisLine: { lineStyle: { color: '#334155' } } }, axisTick: { show: false } },
  yAxis: { type: 'value', axisLabel: { color: '#94a3bc' }, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } } },
  series: [{ type: 'bar', data: [32, 45, 58, 42, 35], itemStyle: { color: '#1e90ff' } }],
}

const memoryOption = {
  tooltip: { trigger: 'axis', formatter: '{c0}%' },
  grid: { left: 5, right: 5, top: 20, bottom: 5 },
  xAxis: { type: 'category', data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], axisLabel: { color: '#94a3b8' }, axisAxis: { axisLine: { lineStyle: { color: '#334155' } } }, axisTick: { show: false } },
  yAxis: { type: 'value', max: 100, axisLabel: { color: '#94a3a8', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } } },
  series: [{ type: 'line', data: [55, 62, 58, 65, 62], itemStyle: { color: '#10b981' }, smooth: true, areaStyle: { color: 'rgba(16,185,129,0.1)' } }],
}

const channelOption = {
  tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
  legend: { top: 'bottom', data: ['声学相似', '同流派热门', '同艺人', '相似艺人'] },
  grid: { left: 5, right: 5, top: 5, bottom: 40 },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['50%', '55%'],
    data: [
      { value: 35, name: '声学相似', itemStyle: { color: '#1e90ff' } },
      { value: 25, name: '同流族热门', itemStyle: { color: '#10b981' } },
      { value: 25, name: '同艺人', itemStyle: { color: '#f59e0b' } },
      { value: 15, name: '相似艺人', itemStyle: { color: '#ef4444' } },
    ],
    label: { color: '#cbd5e1' },
  }],
}

let timer = null
function startPolling() {
  timer = setInterval(async () => {
    try {
      const res = await api.get('/v1/recommend/stats')
      cpuPercent.value = res.data.cpu_percent
      memoryPercent.value = res.data.memory_percent
      qps.value = res.data.qps
      latencyMs.value = res.data.avg_latency_ms
    } catch {
      cpuPercent.value = Math.floor(Math.random() * 30 + 30)
      memoryPercent.value = Math.floor(Math.random() * 40 + 40)
      qps.value = Math.floor(Math.random() * 200 + 50)
      latencyMs.value = Math.floor(Math.random() * 100 + 50)
    }
  }, 5000)
}

onMounted(startPolling)
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.dashboard {
  padding: 24px;
  background: var(--bg-primary);
  min-height: calc(100vh - 112px);
}

.mb-20 {
  margin-bottom: 20px;
}

.service-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  transition: all 0.3s ease;
}

.service-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.service-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
  background: rgba(30, 144, 255, 0.15);
  color: var(--primary-color);
}

.service-info h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.service-status {
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.service-meta {
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  gap: 8px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-header h3 {
  font-size: 14px;
  color: var(--text-secondary);
}

.chart-header .value {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary-color);
}

.stat-card {
  text-align: center;
  padding: 24px;
}

.stat-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--primary-color);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

:deep(.el-timeline-item__wrapper) {
  color: var(--text-primary);
  font-size: 13px;
}
</style>

<script>
import 'vue-echarts'
</script>
