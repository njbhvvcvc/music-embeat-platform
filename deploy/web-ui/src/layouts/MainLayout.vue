<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarCollapsed ? '64px' : '260px'" class="sidebar">
      <div class="sidebar-header">
        <div v-if="!sidebarCollapsed" class="logo">
          <div class="logo-icon">
            <i class="el-icon-headset"></i>
          </div>
          <span class="logo-text">Embeat Platform</span>
        </div>
        <el-button
          v-else
          class="logo-toggle"
          @click="sidebarCollapsed = false"
          circle
          size="small"
        >
          <i class="el-icon-menu"></i>
        </el-button>
      </div>

      <el-menu
        :collapse="sidebarCollapsed"
        :unique-opened="true"
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        :collapse-transition="false"
      >
        <el-menu-item index="/" :disabled="sidebarCollapsed">
          <el-icon><Dashboard /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>

        <el-sub-menu index="services" :disabled="sidebarCollapsed">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>服务管理</span>
          </template>
          <el-menu-item index="/services">服务概览</el-menu-item>
          <el-menu-item index="/recommend">推荐测试</el-menu-item>
          <el-menu-item index="/vectors">向量浏览</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/logs" :disabled="sidebarCollapsed">
          <el-icon><Document /></el-icon>
          <template #title>日志查看</template>
        </el-menu-item>

        <el-menu-item index="/settings" :disabled="sidebarCollapsed">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer" v-if="!sidebarCollapsed">
        <el-divider />
        <div class="version-info">
          <span class="label">版本</span>
          <span class="value">v1.0.0</span>
        </div>
      </div>
    </el-aside>

    <el-container class="main-content">
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-button
            class="collapse-btn"
            @click="sidebarCollapsed = !sidebarCollapsed"
            circle
            size="small"
          >
            <i :class="sidebarCollapsed ? 'el-icon-menu' : 'el-icon-fold'"></i>
          </el-button>

          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-for="item in breadcrumb" :key="item.path" :to="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <!-- 系统状态指示器 -->
          <div class="system-status">
            <span class="status-indicator" :class="systemHealthy ? 'healthy' : 'degraded'"></span>
            <span class="status-text">{{ systemHealthy ? '系统正常' : '部分异常' }}</span>
          </div>

          <el-dropdown @command="handleUserCommand" trigger="click">
            <span class="user-avatar">
              <el-avatar :size="32" :src="userAvatar" />
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  <span>个人中心</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Dashboard, Monitor, Document, Setting, User, SwitchButton,
  Fold, Menu, Dashboard as DashboardIcon, Headset
} from '@element-plus/icons-vue'
import { ElNotification } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const sidebarCollapsed = ref(false)
const activeMenu = computed(() => route.path)

const breadcrumb = computed(() => {
  const matched = route.matched.slice(1)
  return matched.map(r => ({
    path: r.path,
    title: r.meta.title || '未知',
  }))
})

const userAvatar = ref('')

const systemHealthy = ref(true)

async function handleUserCommand(cmd) {
  if (cmd === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

async function checkSystemHealth() {
  try {
    const res = await fetch('/api/v1/health')
    systemHealthy.value = res.ok
  } catch {
    systemHealthy.value = false
  }
}

onMounted(() => {
  checkSystemHealth()
  setInterval(checkSystemHealth, 30000)
})

watch(() => route.path, () => {
  activeMenu.value = route.path
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
  display: flex;
  background: var(--bg-primary);
}

.sidebar {
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
  height: 100%;
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-color);
  min-width: 64px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-primary);
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logo-toggle {
  color: var(--text-secondary);
  background: transparent;
  border: none;
}

.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  padding: 12px 8px;
  border: none;
  background: transparent;
}

.sidebar-menu :deep(.el-menu-item) {
  border-radius: 8px;
  margin: 4px 4px;
  height: 44px;
  line-height: 44px;
  color: var(--text-secondary);
  transition: all 0.2s ease;

  &:hover {
    background: var(--bg-hover);
    color: var(--primary-color);
  }

  &.is-active {
    background: rgba(30, 144, 255, 0.15);
    color: var(--primary-color);
    font-weight: 500;

    .el-icon {
      color: var(--primary-color);
    }
  }
}

.sidebar-menu :deep(.el-sub-menu__title) {
  height: 44px;
  line-height: 44px;
  padding: 0 16px;
  color: var(--text-secondary);
  border-radius: 8px;
  margin: 4px 4px;

  &:hover {
    background: var(--bg-hover);
    color: var(--primary-color);
  }
}

.sidebar-menu :deep(.el-menu--collapse .el-sub-menu__title) {
  padding: 0;
  justify-content: center;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}

.version-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.header {
  height: 64px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.collapse-btn {
  color: var(--text-secondary);
  background: transparent;
  border: none;
  width: 36px;
  height: 36px;
}

.collapse-btn:hover {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.header-left :deep(.el-breadcrumb) {
  font-size: 14px;
}

.header-left :deep(.el-breadcrumb__inner) {
  color: var(--text-secondary);
}

.header-left :deep(.el-breadcrumb__inner.is-link) {
  color: var(--primary-color);
}

.header-left :deep(.el-breadcrumb__inner.is-link:hover) {
  color: var(--primary-light);
}

.header-left :deep(.el-breadcrumb__separator) {
  color: var(--text-muted);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--bg-tertiary);
  border-radius: 20px;
  font-size: 12px;
  color: var(--text-secondary);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  &.healthy {
    background: var(--success-color);
    box-shadow: 0 0 8px var(--success-color);
  }

  &.degraded {
    background: var(--warning-color);
    box-shadow: 0 0 8px var(--warning-color);
  }
}

.user-avatar {
  cursor: pointer;
}

.main {
  flex: 1;
  padding: 24px;
  background: var(--bg-primary);
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>