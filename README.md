# music-embeat-platform

基于 GD Studio API + Embeat 推荐引擎的开源音乐服务平台。
部署在任何带 Docker 的云服务器或本地机器上。

## 🌟 特性

- **GD Studio API 音乐源**: 网易云/QQ/酷我/咪咕/B站/Apple 多源聚合
- **Embeat 推荐引擎**: 4路召回 + 重排序，毫秒级响应
- **Qdrant 向量数据库**: 45M 曲目向量检索
- **用户画像云存储**: 播放历史/收藏/种子池生成
- **MusicFree 插件**: 桌面客户端一键安装
- **运维控制台**: Vue3 + ElementPlus 现代化界面
- **Cloudflare Tunnel**: 免费获得 HTTPS 公网地址

## 🚀 快速部署

### 云服务器部署 (任意 VPS / 本地 Docker)

```bash
# 1. 克隆
git clone https://github.com/yourname/music-embeat-platform.git
cd music-embeat-platform

# 2. 配置
cp .env.example .env
vim .env   # 修改 JWT_SECRET、POSTGRES_PASSWORD

# 3. 下载模型权重 (约 2MB)
mkdir -p embeat-service/checkpoints/EmbeatMLP
wget -O embeat-service/checkpoints/EmbeatMLP/model.pt \
  https://github.com/gdstudio-org/Embeat/releases/latest/download/EmbeatMLP.pt

# 4. 更新 Qdrant 向量库 (45M 或华语子集)
make import-qdrant-cn     # 华语子集 (~30min)
make import-qdrant-full   # 全量 45M (~2h)

# 5. 启动
make build
make ui-deploy   # 构建前端 UI

# 6. 自检
make check
```

### 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| API 网关 | `:8080` | 所有 API 入口 |
| Embeat 引擎 | `:7860` | 推荐/向量 API |
| 用户画像 | `:8090` | 画像事件/种子 API |
| Qdrant | `:6333` | 向量数据库 |
| PostgreSQL | `:5432` | 用户画像存储 |
| Nginx | `:80/:443` | HTTPS 反代 |
| 运维控制台 | `:3000` | Web UI |

### Cloudflare Tunnel (获取 HTTPS)

```bash
# 安装 cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# 登录并创建隧道
cloudflared tunnel login
cloudflared tunnel create embeat-platform
cloudflared tunnel route dns embeat-platform api.yourdomain.com

# 启动隧道
cloudflared tunnel run embeat-platform
```

## 📖 接口文档

### 公共接口 (无需鉴权)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/search?keyword=&source=` | 搜索音乐 |
| GET | `/api/v1/url?id=&source=&br=` | 获取播放链接 |
| GET | `/api/v1/pic?id=&source=&size=` | 获取专辑封面 |
| GET | `/api/v1/lyric?id=&source=` | 获取歌词 |
| GET | `/health` | 健康检查 |

### 推荐接口 (需 JWT)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/recommend` | 智能推荐 (body: seed, top_k, channels) |
| POST | `/api/v1/vector` | 获取向量 (body: track_id) |

### 画像接口 (需 JWT)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/events/play` | 记录播放 |
| POST | `/api/v1/events/favorite` | 记录收藏 |
| POST | `/api/v1/events/skip` | 记录跳过 |
| GET | `/api/v1/seeds` | 获取种子曲目 |

## 🏗️ 架构

```
nginx(:80/443)
  │ (HTTPS + 限流)
  ▼
gateway(:8080)     ← A1: API 网关
  ├── embeat(:7860)     ← A3: 推荐引擎
  │   ├── qdrant(:6333) ← A4: 向量数据库
  │   └── checkpoints/  ← EmbeatMLP 权重
  ├── profile(:8090)    ← A5: 用户画像
  │   └── postgres(:5432)
  └── GD Studio API     ← A2: 音乐源

web-ui(:3000)      ← A6: 运维控制台 + MusicFree 插件
```

## 🤖 子 AI 角色

| Agent | 职责 | 实现位置 |
|-------|------|----------|
| A1: API 网关 | 路由/限流/鉴权/GD Studio API 适配 | `gateway/` |
| A2: 音乐源适配 | GD Studio API 标准化转换 | `gateway/app/clients/gdstudio.py` |
| A3: 推荐引擎 | 4路召回 + 去重/重排/Qdrant | `embeat-service/` |
| A4: 向量库运维 | 全量导入/优化/监控 | `embeat-service/scripts/` |
| A5: 画像云存储 | 播放/收藏/跳过 → 种子池 | `profile-service/` |
| A6: 前端插件 | MusicFree 插件 + 运维 UI | `musicfree-plugin/` + `deploy/web-ui/` |

## ⌚️ 常用命令

```bash
make up            # 启动
make down           # 停止
make logs           # 日志
make build          # 构建
make check          # 自检(lint + 类型 + 测试)
make test           # 单元测试
make deploy         # 一键部署 (含自检)
make benchmark      # 性能测试
make self-check     # 文件完整性校验
make clean          # 清理缓存
```

## 🔧 自检机制

项目内置多层自检，确保部署安全：

| 检测项 | 触发时机 | 说明 |
|--------|----------|------|
| 文件完整性 | `make self-check` | 验证所有关键文件存在 + 关键内容 |
| Python 语法 | `make self-check` | `compile()` 校验每个 `.py` |
| 端口冲突 | `make self-check` | 检查 8080/7860/8090/6333/5432 |
| API 契约 | `make test-contract` | 验证接口响应格式 |
| 服务健康 | `make deploy` | curl 健康检查端点 |

```bash
python scripts/self_check.py --report  # 输出 JSON 报告
```