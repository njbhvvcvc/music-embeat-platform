<template>
  <div class="settings-view">
    <div class="page-header">
      <h2>系统设置</h2>
      <p>配置您的 Embeat Platform 环境</p>
    </div>

    <el-card shadow="hover">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="服务配置" name="services">
          <div class="settings-form">
            <el-form :model="settings.services" label-width="140px">
              <el-form-item label="GD Studio API">
                <el-input v-model="settings.services.gd_api_base" />
                <div class="hint">GD Studio 音乐 API 地址</div>
              </el-form-item>
              <el-form-item label="JWT Secret">
                <el-input v-model="settings.services.jwt_secret" type="password" />
                <div class="hint">用于身份验证的密钥</div>
              </el-form-item>
              <el-form-item label="Qdrant 地址">
                <el-input v-model="settings.services.qdrant_host" />
              </el-form-item>
              <el-form-item label="Qdrant 端口">
                <el-input-number v-model="settings.services.qdrant_port" :min="1" :max="65535" />
              </el-form-item>
              <el-form-item label="Embeat 模型路径">
                <el-input v-model="settings.services.embeat_model_path" />
              </el-form-item>
              <el-form-item label="Track2Vec 开关">
                <el-switch v-model="settings.services.track2vec_enabled" />
                <div class="hint">启用后开启第 5 路召回（需下载 Track2Vec 权重）</div>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveSettings">保存</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane label="部署信息" name="deploy">
          <div class="deploy-info">
            <div class="version-card">
              <h3>版本信息</h3>
              <p>项目版本: <strong>v1.0.0</strong></p>
              <p>Python: <strong>3.11</strong></p>
              <p>Vue: <strong>3.4</strong></p>
              <p>Qdrant: <strong>v1.13</strong></p>
              <p>PostgreSQL: <strong>16</strong></p>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="站点开关" name="ops">
          <div class="ops-panel">
            <div class="ops-actions">
              <el-button type="danger" plain :loading="acting" @click="doStop">一键停止服务</el-button>
              <el-button type="success" plain :loading="acting" @click="doStart">一键启动服务</el-button>
              <el-button @click="fetchStatus">刷新状态</el-button>
            </div>
            <div class="ops-hint">
              停止后前端与 API 立即不可访问，节省计算资源；网关保留以便再次启动。
              <br />注意：真正的额度是按 Codespaces 运行时长计费，长时间不用建议直接休眠/停止整个 Codespaces（闲置约 30 分钟会自动休眠）。
            </div>
            <el-table :data="servicesStatus" size="small" style="max-width: 560px">
              <el-table-column prop="name" label="服务" width="120" />
              <el-table-column label="状态" width="140">
                <template #default="{ row }">
                  <el-tag :type="row.state === 'running' ? 'success' : 'info'">
                    {{ stateText(row.state) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="cid" label="容器" />
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="系统信息" name="system">
          <div class="system-info">
            <el-row :gutter="40">
              <el-col :xs="12" :sm="8">
                <div class="info-item">
                  <span class="label">CPU</span>
                  <span class="value">2 vCPU (x86)</span>
                </div>
              </el-col>
              <el-col :xs="12" :sm="8">
                <div class="info-item">
                  <span class="label">内存</span>
                  <span class="value">4 GB</span>
                </div>
              </el-col>
              <el-col :xs="12" :sm="8">
                <div class="info-item">
                  <span class="label">磁盘</span>
                  <span class="value">40 GB SSD</span>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api/client'

const activeTab = ref('services')

const settings = ref({
  services: {
    gd_api_base: 'https://music-api.gdstudio.xyz/api.php',
    jwt_secret: '********',
    qdrant_host: 'qdrant',
    qdrant_port: 6333,
    embeat_model_path: '/app/checkpoints/EmbeatMLP',
    track2vec_enabled: false,
  },
})

const servicesStatus = ref([])
const acting = ref(false)

function stateText(state) {
  const map = { running: '运行中', exited: '已停止', absent: '不存在' }
  return map[state] || state
}

async function fetchStatus() {
  try {
    const res = await api.get('/v1/ops/status')
    servicesStatus.value = res.data.data || []
  } catch (e) {
    ElMessage.error('获取状态失败')
  }
}

async function doStop() {
  try {
    await ElMessageBox.confirm('确定停止所有服务吗？前端和 API 将立即不可访问。', '一键停止', {
      type: 'warning',
      confirmButtonText: '停止',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  acting.value = true
  try {
    const res = await api.post('/v1/ops/stop')
    ElMessage.success(res.data.msg || '已停止')
    fetchStatus()
  } catch (e) {
    ElMessage.error('停止失败')
  } finally {
    acting.value = false
  }
}

async function doStart() {
  acting.value = true
  try {
    const res = await api.post('/v1/ops/start')
    ElMessage.success(res.data.msg || '已启动')
    setTimeout(fetchStatus, 3000)
  } catch (e) {
    ElMessage.error('启动失败')
  } finally {
    acting.value = false
  }
}

async function saveSettings() {
  try {
    await api.post('/settings', settings.value)
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(fetchStatus)
</script>

<style scoped>
.settings-view { min-height: calc(100vh - 112px); background: var(--bg-primary); }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-header p { color: var(--text-secondary); font-size: 14px; margin-bottom: 20px; }
.hint { color: var(--text-muted); font-size: 12px; margin-top: 4px; }
.version-card h3 { color: var(--text-primary); margin-bottom: 12px; }
.version-card p { color: var(--text-secondary); font-size: 14px; }
.info-item { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--border-light); }
.info-item .label { color: var(--text-secondary); font-size: 14px; }
.info-item .value { color: var(--text-primary); font-weight: 600; }
.ops-actions { margin-bottom: 16px; }
.ops-hint { color: var(--text-muted); font-size: 12px; margin-bottom: 16px; line-height: 1.8; }
</style>
