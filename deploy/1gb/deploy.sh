#!/bin/bash
# 1GB 单语种子集部署脚本
# 用法: ./deploy.sh --lang cn|jp|en|kr [--with-import]
set -eux

LANG_OPT=""
WITH_IMPORT=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --lang) LANG_OPT="--$2-only"; shift 2 ;;
    --with-import) WITH_IMPORT=true; shift ;;
    *) shift ;;
  esac
done

if [ -z "$LANG_OPT" ] && [ "$WITH_IMPORT" = true ]; then
  echo "❌ 导入时必须指定语种: --lang cn|jp|en|kr"
  exit 1
fi

echo "=========================================="
echo "  music-embeat-platform 1GB 部署 (单语种子集)"
echo "=========================================="

# 1. 检查 .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  已从 .env.example 创建 .env，请编辑 JWT_SECRET 和 POSTGRES_PASSWORD"
  exit 1
fi

# 2. 下载模型权重
mkdir -p embeat-service/checkpoints/EmbeatMLP
if [ ! -f embeat-service/checkpoints/EmbeatMLP/model.pt ]; then
  echo "📥 下载 EmbeatMLP 模型权重..."
  curl -sL -o embeat-service/checkpoints/EmbeatMLP/model.pt \
    https://raw.githubusercontent.com/gdstudio-org/Embeat/main/checkpoints/EmbeatMLP/model.pt \
    && echo "  ✅ 下载成功" || echo "  ⚠️  下载失败，请手动下载"
fi

# 3. 启动基础服务
echo "🚀 启动 Qdrant + PostgreSQL..."
docker compose -f deploy/1gb/docker-compose.yml up -d qdrant postgres

echo "⏳ 等待 Qdrant 就绪..."
sleep 15
for i in $(seq 1 30); do
  if curl -sf http://localhost:6333/healthz >/dev/null 2>&1; then
    echo "  ✅ Qdrant 就绪"
    break
  fi
  sleep 5
done

# 4. 导入子集
if [ "$WITH_IMPORT" = true ]; then
  echo "📥 导入语种子集: $LANG_OPT"
  docker compose -f deploy/1gb/docker-compose.yml stop gateway embeat profile 2>/dev/null || true

  docker compose -f deploy/1gb/docker-compose.yml run --rm \
    -e QDRANT_HOST=qdrant -e QDRANT_PORT=6333 \
    embeat python scripts/import_qdrant.py $LANG_OPT \
    --indexing-threshold 10000 --memmap-threshold 10000 --batch-size 200

  echo "✅ 子集导入完成（子集小，索引会自动后台构建）"
fi

# 5. 启动全部
echo "🚀 启动全部服务..."
docker compose -f deploy/1gb/docker-compose.yml up -d

echo ""
echo "========== 健康检查 =========="
curl -sf http://localhost:8080/health && echo " ✅ 网关正常" || echo " ❌ 网关异常"
curl -sf http://localhost:7860/health && echo " ✅ Embeat 正常" || echo " ❌ Embeat 异常"
curl -sf http://localhost:8090/health && echo " ✅ 画像服务正常" || echo " ❌ 画像服务异常"
curl -sf http://localhost:6333/healthz && echo " ✅ Qdrant 正常" || echo " ❌ Qdrant 异常"
echo "================================"

echo ""
echo "✅ 部署完成！(单语种子集模式)"
echo "  API 网关:   http://localhost:8080"
echo "  Embeat:     http://localhost:7860"
echo "  画像服务:   http://localhost:8090"
echo "  Qdrant:     http://localhost:6333/dashboard"
