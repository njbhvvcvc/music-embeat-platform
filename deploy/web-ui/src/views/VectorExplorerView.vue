<template>
  <div class="vector-view">
    <div class="page-header">
      <h2>向量浏览</h2>
      <p>查询曲目向量、查看 Qdrant 索引状态</p>
    </div>

    <el-card class="mb-20">
      <el-form :inline="true" :model="form">
        <el-form-item label="Track ID">
          <el-input v-model="form.track_id" placeholder="请输入 Track ID" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="queryVector">查询向量</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="vector" class="mb-20">
      <div class="vector-info">
        <p><strong>Track ID:</strong> {{ vector.track_id }}</p>
        <p><strong>维度:</strong> {{ vector.data.length }}</p>
        <p><strong>向量:</strong> {{ vector.data.slice(0, 10).map(v => v.toFixed(4)).join(', ') }} ...</p>
      </div>
    </el-card>

    <el-card>
      <div class="stats-grid">
        <el-row :gutter="20">
          <el-col :xs="12" :sm="6">
            <div class="stat-card">
              <div class="stat-value">45M</div>
              <div class="stat-label">向量总数</div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="6">
            <div class="stat-card">
              <div class="stat-value">64</div>
              <div class="stat-label">向量维度</div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="6">
            <div class="stat-card">
              <div class="stat-value">{{ collectionStatus }}</div>
              <div class="stat-label">Collection 状态</div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="6">
            <div class="stat-card">
              <div class="stat-value">{{ indexProgress }}%</div>
              <div class="stat-label">索引进度</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/client'

const vector = ref(null)
const collectionStatus = ref('就绪')
const indexProgress = ref(100)
const form = reactive({
  track_id: '',
})

async function queryVector() {
  if (!form.track_id) {
    ElMessage.warning('请输入 Track ID')
    return
  }
  try {
    const res = await api.post('/vector', { track_id: form.track_id })
    vector.value = {
      track_id: form.track_id,
      data: res.data.data,
    }
  } catch (e) {
    ElMessage.error('查询失败')
  }
}

onMounted(() => {
  api.get('/qdrant/info').then(res => {
    collectionStatus.value = res.data.status || '就绪'
    indexProgress.value = res.data.indexed / res.data.total * 100 || 100
  }).catch(() => {})
})
</script>

<style scoped>
.vector-view { min-height: calc(100vh - 112px); background: var(--bg-primary); }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-header p { color: var(--text-secondary); font-size: 14px; }
.mb-20 { margin-bottom: 20px; }
.stat-card { text-align: center; padding: 24px 16px; border: 1px solid var(--border-color); border-radius: 12px; background: var(--bg-tertiary); }
.stat-value { font-size: 28px; font-weight: 700; color: var(--primary-color); }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
</style>
