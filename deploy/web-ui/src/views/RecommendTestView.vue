<template>
  <div class="recommend-view">
    <div class="page-header">
      <h2>推荐测试</h2>
      <p>输入种子曲目，测试 Embeat 推荐引擎的效果</p>
    </div>

    <el-card class="mb-20" shadow="hover">
      <el-form :model="form" label-width="80px">
        <el-form-item label="种子">
          <el-input v-model="form.seed" placeholder="请输入曲目 ID 或 '歌名 - 歌手'" style="width: 320px" />
        </el-form-item>
        <el-form-item label="召回渠道">
          <el-checkbox-group v-model="form.channels">
            <el-checkbox value="similar">声学相似</el-checkbox>
            <el-checkbox value="popular">同流派热门</el-checkbox>
            <el-checkbox value="same_artist">同艺人</el-checkbox>
            <el-checkbox value="related_artist">相似艺人</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.top_k" :min="1" :max="50" style="width: 100px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="runRecommend" :loading="loading">运行推荐</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="results.length" shadow="hover">
      <div class="result-header">
        <h3>推荐结果 ({{ results.length }} 条)</h3>
        <span class="latency">耗时: {{ latency }}ms</span>
      </div>
      <el-table :data="results" style="width: 100%">
        <el-table-column prop="channel" label="渠道" width="120" />
        <el-table-column prop="title" label="歌曲" />
        <el-table-column prop="artist" label="歌手" />
        <el-table-column prop="score" label="得分" width="80">
          <template #default="{ row }">
            {{ (row.score * 100).toFixed(0) }}/100
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-else-if="!loading" class="empty-state" shadow="hover">
      <div class="empty-text">输入种子曲目后点击 "运行推荐"</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/client'

const loading = ref(false)
const latency = ref(0)
const results = ref([])
const form = reactive({
  seed: '晴天 - Jay Chou',
  channels: ['similar', 'popular', 'same_artist', 'related_artist'],
  top_k: 20,
})

async function runRecommend() {
  loading.value = true
  try {
    const start = Date.now()
    const res = await api.post('/recommend', {
      seed: form.seed,
      top_k: form.top_k,
      channels: form.channels.join(','),
    })
    latency.value = Date.now() - start
    results.value = res.data.data
    ElMessage.success(`获取 ${results.value.length} 条推荐`)
  } catch (e) {
    ElMessage.error('推荐请求失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.recommend-view { min-height: calc(100vh - 112px); background: var(--bg-primary); }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-header p { color: var(--text-secondary); font-size: 14px; }
.mb-20 { margin-bottom: 20px; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.latency { color: var(--primary-color); font-weight: 600; }
.empty-state { text-align: center; padding: 48px; color: var(--text-muted); }
</style>
