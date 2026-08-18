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
  echo "=== profile logs ==="
  docker logs --tail 50 embeat-profile-1 2>&1
  echo "=== embeat logs ==="
  docker logs --tail 50 embeat-embeat-1 2>&1
  echo "=== gateway logs ==="
  docker logs --tail 30 embeat-gateway-1 2>&1
  echo "=== tail deploy.log ==="
  tail -40 /workspaces/deploy.log 2>&1
} > /workspaces/deploy-status.txt

echo "=== 回传部署结果到 deploy-status 分支 ==="
cd /workspaces/music-embeat-platform
git config user.email "opencode@local" 2>/dev/null
git config user.name "opencode" 2>/dev/null
# 用 worktree 回传，绝不切换主工作目录（避免覆盖 bind-mount 的配置文件）
git fetch origin deploy-status 2>/dev/null
rm -rf /workspaces/deploy-status-wt
git worktree prune --expire 1s 2>/dev/null
git worktree add --detach /workspaces/deploy-status-wt origin/deploy-status
cd /workspaces/deploy-status-wt
cp /workspaces/deploy-status.txt deploy-status.txt
git add deploy-status.txt
git commit -m "deploy status $(date -u)" 2>&1 | tail -1
git push --force origin HEAD:deploy-status 2>&1 | tail -1
cd /workspaces/music-embeat-platform
git worktree remove --force /workspaces/deploy-status-wt 2>/dev/null
echo "REPORT_DONE"
