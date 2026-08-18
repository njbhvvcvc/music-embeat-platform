#!/bin/bash
# 部署并把结果回传到 deploy-status 分支, 供本地 opencode 确认 (无需人工操作)
set +e

echo "=== 部署开始 $(date -u) ==="
bash deploy/codespaces/deploy.sh > /workspaces/deploy.log 2>&1
RC=$?

{
  echo "DEPLOY_RC=$RC"
  echo "TIME=$(date -u)"
  echo "=== docker ps ==="
  docker ps --format 'table {{.Names}}\t{{.Status}}' 2>&1
  echo "=== tail deploy.log ==="
  tail -60 /workspaces/deploy.log 2>&1
} > /workspaces/deploy-status.txt

echo "=== 回传部署结果到 deploy-status 分支 ==="
cd /workspaces/music-embeat-platform
git config user.email "opencode@local" 2>/dev/null
git config user.name "opencode" 2>/dev/null
git fetch origin deploy-status 2>/dev/null
git checkout -f -B deploy-status origin/deploy-status 2>/dev/null || git checkout -f -b deploy-status
cp /workspaces/deploy-status.txt deploy-status.txt
git add deploy-status.txt
git commit -m "deploy status $(date -u)" 2>&1 | tail -1
git push --force origin deploy-status 2>&1 | tail -1
echo "REPORT_DONE"
