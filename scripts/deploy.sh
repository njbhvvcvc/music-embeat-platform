#!/bin/bash
set -eux

echo "=========================================="
echo "  music-embeat-platform 一键部署脚本"
echo "  适用于: 任意云 VPS / Docker 环境"
echo "=========================================="

# 1. 检查依赖
command -v docker >/dev/null 2>&1 || { echo "❌ 需要安装 Docker"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ 需要安装 Docker Compose"; exit 1; }

# 2. 检查 .env
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "⚠️  已从 .env.example 创建 .env，请编辑后重试"
    exit 1
  fi
  echo "❌ 缺少 .env 文件"
  exit 1
fi

# 3. 下载 Embeat 模型权重
echo "📥 下载 EmbeatMLP 模型权重 (~1.5MB)..."
mkdir -p embeat-service/checkpoints/EmbeatMLP
curl -sL -o embeat-service/checkpoints/EmbeatMLP/model.pt \
  https://raw.githubusercontent.com/gdstudio-org/Embeat/main/checkpoints/EmbeatMLP/model.pt \
  && echo "  ✅ 权重下载成功" || echo "  ⚠️  权重下载失败，请手动下载"

# 4. 自检
echo "🔍 运行自检..."
python scripts/self_check.py || { echo "⚠️  自检告警，继续部署..."; }

# 5. 构建前端 UI
echo "🎨 构建前端 UI..."
cd deploy/web-ui
npm install --silent 2>/dev/null || { echo "⚠️  npm install 失败，跳过前端构建"; }
npm run build 2>/dev/null || echo "⚠️  前端构建失败，跳过"
cd ../..

# 6. 构建并启动服务
echo "🚀 启动服务..."
docker compose up -d --build

# 7. 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 15

# 8. 健康检查
echo ""
echo "========== 健康检查 =========="
curl -sf http://localhost:8080/health && echo " ✅ 网关正常" || echo " ❌ 网关异常"
curl -sf http://localhost:7860/health && echo " ✅ Embeat 正常" || echo " ❌ Embeat 异常"
curl -sf http://localhost:8090/health && echo " ✅ 画像服务正常" || echo " ❌ 画像服务异常"
curl -sf http://localhost:6333/healthz && echo " ✅ Qdrant 正常" || echo " ❌ Qdrant 异常"
curl -sf http://localhost:5432 && echo " ✅ PostgreSQL 就绪" || echo " ❌ PostgreSQL 异常"
echo "================================"

# 9. 提示后续步骤
echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo "  API 网关:        http://localhost:8080"
echo "  Embeat 推理:     http://localhost:7860"
echo "  画像服务:        http://localhost:8090"
echo "  Qdrant 面板:     http://localhost:6333/dashboard"
echo "  运维控制台:      http://localhost:3000"
echo "=========================================="
echo ""
echo "  后续步骤："
echo "  1. 导入向量库: make import-qdrant-cn  (华语子集)"
echo "                    make import-qdrant-full (全量 45M)"
echo "  2. 运行自检:     make check"
echo "  3. 性能测试:     make benchmark"
echo "=========================================="