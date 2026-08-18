#!/bin/bash
# GitHub Codespaces 部署脚本 (4GB 优化, 全量 45M 可跑)
# 在 Codespace 终端里运行: bash deploy/codespaces/deploy.sh [--with-import]
set -eux

WITH_IMPORT=false
while [[ $# -gt 0 ]]; do
  case $1 in
    --with-import) WITH_IMPORT=true; shift ;;
    *) shift ;;
  esac
done

echo "=========================================="
echo "  music-embeat-platform - GitHub Codespaces"
echo "  规格: 4GB RAM / 32GB 磁盘 / 60h月免费"
echo "=========================================="

# 1. .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  已创建 .env，请修改 JWT_SECRET 和 POSTGRES_PASSWORD"
fi

# 2. 模型权重
mkdir -p embeat-service/checkpoints/EmbeatMLP
if [ ! -f embeat-service/checkpoints/EmbeatMLP/model.pt ]; then
  echo "📥 下载 EmbeatMLP 模型权重..."
  curl -sL -o embeat-service/checkpoints/EmbeatMLP/model.pt \
    https://raw.githubusercontent.com/gdstudio-org/Embeat/main/checkpoints/EmbeatMLP/model.pt
fi

# 3. 构建前端 (Vue UI)
echo "🎨 构建前端管理后台..."
cd deploy/web-ui
if [ ! -d node_modules ]; then npm install 2>&1 | tail -3; fi
npm run build 2>&1 | tail -5
cd ../..
echo "  ✅ 前端构建完成 -> deploy/web-ui/dist"

# 4. 启动基础服务
echo "🚀 启动 Qdrant + PostgreSQL..."
docker compose -f deploy/clawcloud/docker-compose.yml up -d qdrant postgres

echo "⏳ 等待 Qdrant 就绪..."
sleep 15
for i in $(seq 1 30); do
  curl -sf http://localhost:6333/healthz >/dev/null 2>&1 && break
  sleep 5
done

# 5. 导入全量 (4GB memmap 模式)
if [ "$WITH_IMPORT" = true ]; then
  echo "📥 导入全量 45M (memmap 模式, 不建索引)..."
  docker compose -f deploy/clawcloud/docker-compose.yml stop gateway embeat profile 2>/dev/null || true
  docker compose -f deploy/clawcloud/docker-compose.yml run --rm \
    -e QDRANT_HOST=qdrant -e QDRANT_PORT=6333 \
    embeat python scripts/import_qdrant.py --full \
    --indexing-threshold 10000000 --memmap-threshold 0 --batch-size 200
  echo "✅ 全量导入完成"
  echo "💡 建议: 导入后打包 Qdrant 数据传到 WebDAV 备份 (见 docs/CODESPACES.md)"
fi

# 6. 启动全部 (含 Nginx 前端)
docker compose -f deploy/clawcloud/docker-compose.yml up -d

echo ""
echo "========== 健康检查 =========="
curl -sf http://localhost/health && echo " ✅ 前端(Nginx)" || echo " ❌ 前端"
curl -sf http://localhost:8080/health && echo " ✅ 网关" || echo " ❌ 网关"
curl -sf http://localhost:7860/health && echo " ✅ Embeat" || echo " ❌ Embeat"
curl -sf http://localhost:8090/health && echo " ✅ 画像" || echo " ❌ 画像"
curl -sf http://localhost:6333/healthz && echo " ✅ Qdrant" || echo " ❌ Qdrant"
echo "================================"

echo ""
echo "✅ 部署完成！端口已自动转发，访问 Codespaces 提供的 URL 即可"
echo "  前端管理:   https://<codespace>-80.app.github.dev"
echo "  API 网关:   https://<codespace>-8080.app.github.dev"
echo "  Qdrant:     https://<codespace>-6333.app.github.dev/dashboard"
