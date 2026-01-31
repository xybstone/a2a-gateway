# 版本控制和发布

## 版本号规范

遵循语义化版本（SemVer）：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复

示例：
- `1.0.0` → `1.1.0`（新增技能）
- `1.1.0` → `1.1.1`（Bug 修复）
- `1.1.1` → `2.0.0`（API 重大变更）

## 发布流程

### 1. 开发分支

```bash
# 创建功能分支
git checkout -b feature/add-review-pr-skill

# 开发完成，提交
git add .
git commit -m "feat: add review_pr skill"
git push origin feature/add-review-pr-skill
```

### 2. Pull Request

- 在 GitHub/GitLab 创建 PR
- 要求至少 1 人 Code Review
- CI 必须通过（测试 + Lint）
- 更新 CHANGELOG.md

### 3. 合并到 develop

```bash
# PR 通过后，合并到 develop
git checkout develop
git merge feature/add-review-pr-skill
git push origin develop
```

### 4. 创建 Release

```bash
# 从 develop 创建 release 分支
git checkout -b release/1.1.0

# 更新版本号
# pyproject.toml: version = "1.1.0"
# a2a_gateway/__init__.py: __version__ = "1.1.0"

# 提交
git commit -am "chore: bump version to 1.1.0"

# 合并到 main
git checkout main
git merge release/1.1.0
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main --tags

# 合并回 develop
git checkout develop
git merge main
git push origin develop
```

### 5. 构建 Docker 镜像

```bash
# 构建
docker build -t a2a-gateway:v1.1.0 .
docker tag a2a-gateway:v1.1.0 a2a-gateway:latest

# 推送
docker push a2a-gateway:v1.1.0
docker push a2a-gateway:latest
```

### 6. 更新 CHANGELOG.md

```markdown
## [1.1.0] - 2026-01-31

### Added
- review_pr 技能
- Prometheus 指标
- Grafana 仪表板

### Fixed
- PTY 输出解析问题
- Redis 连接池泄漏

### Changed
- 提升并发任务数限制（5 → 10）
```

## 回滚流程

### 1. 快速回滚（Docker/K8s）

```bash
# Docker
docker-compose pull a2a-gateway:v1.0.0
docker-compose up -d

# Kubernetes
kubectl set image deployment/a2a-gateway gateway=a2a-gateway:v1.0.0
```

### 2. 数据迁移

```bash
# 如需回退数据，使用 Redis 备份
redis-cli --rdb backup-2026-01-31.rdb
redis-cli --pipe < backup-2026-01-31.rdb
```
