# GitHub Codespaces 部署指南

免费额度：4GB RAM / 32GB 磁盘 / 60小时每月 / 不活动 30 分钟自动挂起

## 第一步：推送到 GitHub

```bash
cd F:\Projects\music-embeat-platform
git init
git add .
git commit -m "init"
gh repo create music-embeat-platform --public   # 或手动在 github.com 创建
git push -u origin main
```

## 第二步：创建 Codespace

1. 打开 `https://github.com/<你>/music-embeat-platform`
2. 点 **Code** → **Codespaces** → **Create codespace on main**
3. 等 1-2 分钟，环境自动装好 Docker

## 第三步：部署

在 Codespace 终端运行：

```bash
# 只启动服务（已有数据则跳过导入）
bash deploy/codespaces/deploy.sh

# 或首次导入全量 45M
bash deploy/codespaces/deploy.sh --with-import
```

导入约 2-3 小时，期间内存 ~3GB（memmap 模式）。

## 第四步：访问

Codespaces 自动转发端口，访问：
- API 网关：`https://<codespace名>-8080.app.github.dev`
- Qdrant 面板：`https://<codespace名>-6333.app.github.dev/dashboard`

## 第五步：备份数据（重要！）

Codespace 删除后数据全丢。定期打包 Qdrant 传到 WebDAV：

```bash
# 在 Codespace 里
docker compose -f deploy/clawcloud/docker-compose.yml stop qdrant
tar czf /tmp/qdrant_backup.tar.gz -C qdrant-data .
# 用 rclone / curl 上传到你的 WebDAV
# 恢复时解压回 qdrant-data 卷
```

## 注意事项

- 不活动 30 分钟自动挂起，RAM/CPU 释放但**磁盘保留**
- 每月 60 小时额度用完后需等下月或付费
- 全量 45M 占 ~15GB 磁盘，剩余空间够系统+Docker
- 删除 Codespace 前务必备份 Qdrant 数据到 WebDAV
