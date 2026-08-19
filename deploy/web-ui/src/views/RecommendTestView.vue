<template>
  <div class="recommend-view">
    <div class="page-header">
      <h2>推荐测试</h2>
      <p>输入种子、搜歌选歌或直接随便听</p>
    </div>

    <el-card class="mb-20" shadow="hover">
      <el-form :model="form" label-width="80px">
        <el-form-item label="种子">
          <div class="seed-row">
            <el-input v-model="form.seed" placeholder="曲目 ID，或 '歌名 - 歌手'（留空则随机）" style="width: 320px" clearable />
            <el-button type="primary" @click="runRecommend" :loading="loading">运行推荐</el-button>
            <el-button @click="shuffleSeed" :loading="loading">随便听</el-button>
          </div>
        </el-form-item>
        <el-form-item label="搜歌选歌">
          <div class="seed-row">
            <el-select
              v-model="selectedTrack"
              filterable
              remote
              clearable
              :remote-method="searchTracks"
              :loading="searchLoading"
              placeholder="输入歌名/歌手，从曲库选歌"
              style="width: 400px"
              @change="onSelectTrack"
            >
              <el-option
                v-for="t in searchResults"
                :key="t.track_id"
                :label="`${t.title} - ${t.artist}`"
                :value="t"
              />
            </el-select>
            <span v-if="selectedTrack" class="seed-picked">{{ selectedTrack.title }} - {{ selectedTrack.artist }}</span>
          </div>
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
      </el-form>
    </el-card>

    <el-card v-if="results.length" shadow="hover">
      <div class="result-header">
        <h3>推荐结果 ({{ results.length }} 条)</h3>
        <span class="latency">耗时: {{ latency }}ms</span>
      </div>
      <div v-if="usedSeed" class="seed-used">基于：{{ usedSeed.title }} - {{ usedSeed.artist }}</div>
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
      <div class="empty-text">输入种子曲目后点击 "运行推荐"，或点 "随便听" 随机推荐</div>
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
const usedSeed = ref(null)
const searchLoading = ref(false)
const searchResults = ref([])
const selectedTrack = ref(null)
const form = reactive({
  seed: '',
  channels: ['similar', 'popular', 'same_artist', 'related_artist'],
  top_k: 20,
})

async function runRecommend() {
  loading.value = true
  try {
    const start = Date.now()
    const res = await api.post('/v1/recommend', {
      seed: form.seed,
      top_k: form.top_k,
      channels: form.channels.join(','),
    })
    latency.value = Date.now() - start
    results.value = res.data.data
    usedSeed.value = res.data.seed_track || null
    if (!results.value.length) {
      ElMessage.warning(res.data.msg || '未找到种子曲目')
    } else {
      ElMessage.success(`获取 ${results.value.length} 条推荐`)
    }
  } catch (e) {
    ElMessage.error('推荐请求失败')
  } finally {
    loading.value = false
  }
}

async function shuffleSeed() {
  form.seed = ''
  selectedTrack.value = null
  await runRecommend()
}

async function searchTracks(keyword) {
  if (!keyword || !keyword.trim()) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  try {
    const res = await api.get('/v1/tracks/search', { params: { keyword, limit: 20 } })
    searchResults.value = res.data.data || []
  } catch (e) {
    searchResults.value = []
    ElMessage.error('搜索失败')
  } finally {
    searchLoading.value = false
  }
}

function onSelectTrack(t) {
  if (t) {
    form.seed = `${t.title} - ${t.artist}`
  } else {
    form.seed = ''
  }
}
</script>

<style scoped>
.recommend-view { min-height: calc(100vh - 112px); background: var(--bg-primary); }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-header p { color: var(--text-secondary); font-size: 14px; }
.mb-20 { margin-bottom: 20px; }
.seed-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.seed-picked { color: var(--success-color); font-size: 13px; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.seed-used { color: var(--text-secondary); font-size: 13px; margin-bottom: 12px; }
.latency { color: var(--primary-color); font-weight: 600; }
.empty-state { text-align: center; padding: 48px; color: var(--text-muted); }
</style>