.PHONY: up down logs ps build ui-deploy test lint clean deploy import-qdrant-cn import-qdrant-full benchmark self-check

# ========== 服务管理 ==========

up:
	docker compose up -d

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

build:
	docker compose up -d --build

restart:
	@read -p "服务名: " svc; docker compose restart $$svc

# ========== UI ==========

ui-deploy:
	cd deploy/web-ui && npm install && npm run build

# ========== 测试 & 自检 ==========

test: test-gateway test-embeat test-profile

test-gateway:
	cd gateway && python -m pytest tests/ -v --tb=short

test-embeat:
	cd embeat-service && python -m pytest tests/ -v --tb=short

test-profile:
	cd profile-service && python -m pytest tests/ -v --tb=short

test-contract:
	cd gateway && python -m pytest tests/contract/ -v --tb=short

lint:
	cd gateway && ruff check . && ruff format --check .
	cd embeat-service && ruff check . && ruff format --check .
	cd profile-service && ruff check . && ruff format --check .

typecheck:
	cd gateway && mypy app/ --strict
	cd embeat-service && mypy app/ --strict
	cd profile-service && mypy app/ --strict

check: lint typecheck test

# ========== 向量库 ==========

import-qdrant-cn:
	docker compose run --rm embeat python scripts/import_qdrant.py --cn-only

import-qdrant-full:
	docker compose run --rm embeat python scripts/import_qdrant.py --full

import-qdrant-sample:
	docker compose run --rm embeat python scripts/import_qdrant.py --sample 1000

benchmark:
	docker compose run --rm embeat python scripts/benchmark.py --seed "晴天 - Jay Chou" --runs 10

validate-recall:
	docker compose run --rm embeat python scripts/validate_recall.py --seed "晴天 - Jay Chou"

# ========== 部署 ==========

deploy: check build ui-deploy up
	@echo "✅ 部署完成，执行健康检查..."
	@sleep 15
	@curl -sf http://localhost:8080/health && echo " ✅ 网关正常" || echo " ❌ 网关异常"
	@curl -sf http://localhost:7860/health && echo " ✅ Embeat 正常" || echo " ❌ Embeat 异常"
	@curl -sf http://localhost:8090/health && echo " ✅ 画像服务正常" || echo " ❌ 画像服务异常"

# ---- RAW 4GB 部署（全套，内存优化）----
deploy-raw:
	bash deploy/clawcloud/deploy.sh

deploy-raw-import:
	bash deploy/clawcloud/deploy.sh --with-import --import-mode full

# ---- ClawCloud 8GB 部署（全套）----
deploy-clawcloud:
	bash deploy/clawcloud/deploy.sh

deploy-clawcloud-import:
	bash deploy/clawcloud/deploy.sh --with-import --import-mode full

# ---- 1GB 单语种子集部署 ----
deploy-1gb:
	bash deploy/1gb/deploy.sh --lang cn

deploy-1gb-import:
	bash deploy/1gb/deploy.sh --lang cn --with-import

deploy-1gb-jp:
	bash deploy/1gb/deploy.sh --lang jp

deploy-1gb-jp-import:
	bash deploy/1gb/deploy.sh --lang jp --with-import

deploy-1gb-en:
	bash deploy/1gb/deploy.sh --lang en

deploy-1gb-en-import:
	bash deploy/1gb/deploy.sh --lang en --with-import

deploy-1gb-kr:
	bash deploy/1gb/deploy.sh --lang kr

deploy-1gb-kr-import:
	bash deploy/1gb/deploy.sh --lang kr --with-import

# ========== 工具 ==========

self-check:
	python scripts/self_check.py --report

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete
	@find . -type f -name '.coverage' -delete
	@find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name 'node_modules' -path '*/web-ui/*' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name 'dist' -path '*/web-ui/*' -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ 清理完成"