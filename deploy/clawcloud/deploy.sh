#!/bin/bash
# RAW 4GB 部署脚本
# 用法: ./deploy.sh [--with-import] [--import-mode full|cn|sample]
set -eux

WITH_IMPORT=false
IMPORT_MODE="full"

while [[ $# -gt 0 ]]; do
  case $1 in
    --with-import) WITH_IMPORT=true; shift ;;
    --import-mode) IMPORT_MODE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

echo "=========================================="
echo "  music-embeat-platform RAW 部署 (4GB 优化)"
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

# 3. 构建并启动基础服务 (qdrant + postgres)
echo "🚀 启动 Qdrant + PostgreSQL..."
docker compose -f deploy/raw/docker-compose.yml up -d qdrant postgres

# 4. 等待 Qdrant 就绪
echo "⏳ 等待 Qdrant 就绪..."
sleep 15
for i in $(seq 1 30); do
  if curl -sf http://localhost:6333/healthz >/dev/null 2>&1; then
    echo "  ✅ Qdrant 就绪"
    break
  fi
  sleep 5
done

# 5. 可选：导入数据
if [ "$WITH_IMPORT" = true ]; then
  echo "📥 开始导入数据 (模式: $IMPORT_MODE)..."
  # 导入时只跑 qdrant，停掉其他服务省内存
  docker compose -f deploy/raw/docker-compose.yml stop gateway embeat profile 2>/dev/null || true

  case $IMPORT_MODE in
    full)
      docker compose -f deploy/raw/docker-compose.yml run --rm \
        -e QDRANT_HOST=qdrant -e QDRANT_PORT=6333 \
        embeat python scripts/import_qdrant.py --full \
        --indexing-threshold 10000000 --memmap-threshold 0 --batch-size 200
      ;;
    cn)
      docker compose -f deploy/raw/docker-compose.yml run --rm \
        -e QDRANT_HOST=qdrant -e QDRANT_PORT=6333 \
        embeat python scripts/import_qdrant.py --cn-only \
        --indexing-threshold 10000000 --memmap-threshold 0 --batch-size 200
      ;;
    sample)
      docker compose -f deploy/raw/docker-compose.yml run --rm \
        -e QDRANT_HOST=qdrant -e QDRANT_PORT=6333 \
        embeat python scripts/import_qdrant.py --sample 1000 --batch-size 200
      ;;
  esac

  echo "🔨 导入完成，触发索引构建（需要额外内存，建议此时停掉其他服务）..."
  docker compose -f deploy/raw/docker-compose.yml run --rm \
    -e QDRANT_HOST=qdrant -e QDRANT_PORT=6333 \
    embeat python scripts/build_index.py || echo "⚠️  索引构建失败，可稍后手动执行"
fi

# 6. 启动全部服务
echo "🚀 启动全部服务..."
docker compose -f deploy/raw/docker-compose.yml up -d

# 7. 健康检查
echo ""
echo "========== 健康检查 =========="
curl -sf http://localhost:8080/health && echo " ✅ 网关正常" || echo " ❌ 网关异常"
curl -sf http://localhost:7860/health && echo " ✅ Embeat 正常" || echo " ❌ Embeat 异常"
curl -sf http://localhost:8090/health && echo " ✅ 画像服务正常" || echo " ❌ 画像服务异常"
curl -sf http://localhost:6333/healthz && echo " ✅ Qdrant 正常" || echo " ❌ Qdrant 异常"
echo "================================"

echo ""
echo "✅ 部署完成！"
echo "  API 网关:   http://localhost:8080"
echo "  Embeat:     http://localhost:7860"
echo "  画像服务:   http://localhost:8090"
echo "  Qdrant:     http://localhost:6333/dashboard"
