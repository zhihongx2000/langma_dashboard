# Git 提交规范

## 目的
- 统一团队的 Git 提交流程，降低误提交、覆盖远程分支和拉取冲突的概率。
- 本文档重点说明两件事：如何把本地更改上传到远程仓库；如何从远程仓库拉取更新或恢复文件。

## 基本原则
- 优先使用功能分支开发，不建议直接在主分支上长期开发。
- 提交前先同步远程最新代码，减少后续冲突。
- 一次提交只解决一个明确问题，不把无关变更混在一起。
- 不提交 .env、密钥、构建产物、缓存文件和本地临时文件。

## 提交信息建议
- 建议使用 Conventional Commits 风格。
- 常用前缀示例：
  - feat：新增功能
  - fix：缺陷修复
  - docs：文档变更
  - refactor：重构但不改行为
  - test：测试补充或调整
  - chore：工程杂项

提交信息示例：

```bash
git commit -m "feat: add user profiling dashboard skeleton"
git commit -m "docs: add git workflow guide"
git commit -m "fix: correct prompt version selector state"
```

## 将本地更改上传到远程仓库

### 推荐流程：功能分支开发后推送远程
1. 查看当前状态，确认有哪些文件发生变化。

```bash
git status
```

2. 查看当前所在分支。

```bash
git branch --show-current
```

3. 先同步主分支最新代码。

```bash
git fetch origin
git switch main
git pull --rebase origin main
```

4. 基于最新主分支创建功能分支。

```bash
git switch -c feat/user-profiling-page
```

5. 开发完成后，再次检查本地变更。

```bash
git status
git diff
```

6. 只暂存本次需要提交的文件。

```bash
git add 路径/文件1 路径/文件2
```

如果需要暂存全部已跟踪和未跟踪文件：

```bash
git add .
```

7. 提交本地更改。

```bash
git commit -m "feat: add user profiling dashboard skeleton"
```

8. 首次推送当前分支到远程仓库。

```bash
git push -u origin feat/user-profiling-page
```

9. 后续继续推送同一分支时，直接执行：

```bash
git push
```

10. 推送成功后，在代码托管平台发起合并请求或按团队流程继续处理。

### 如果你已经在功能分支上开发了一段时间
在推送前，先把远程主分支的最新改动同步到本地，再处理冲突：

```bash
git fetch origin
git rebase origin/main
```

如果团队更偏向 merge 流程，也可以使用：

```bash
git fetch origin
git merge origin/main
```

处理完冲突、通过验证后，再执行推送。

## 从远程仓库拉取更新

### 拉取当前分支的最新内容
如果当前分支已经跟踪远程分支，最简单的方式是：

```bash
git pull --rebase
```

如果希望明确指定远程和分支：

```bash
git pull --rebase origin main
```

### 只更新远程信息，不立即合并
适合先看远程变化，再决定下一步：

```bash
git fetch origin
git branch -r
git log --oneline --decorate --graph --all
```

### 拉取远程某个分支到本地
如果远程已有某个分支，本地还没有，可以这样创建并切换：

```bash
git fetch origin
git switch -c feat/remote-branch origin/feat/remote-branch
```

## 从远程仓库拉取单个文件

### 用远程主分支中的某个文件覆盖本地版本
先抓取远程最新内容，再恢复指定文件：

```bash
git fetch origin
git restore --source origin/main -- 路径/文件
```

如果 Git 版本较旧，没有 restore，也可以使用：

```bash
git fetch origin
git checkout origin/main -- 路径/文件
```

### 查看远程某个文件的内容再决定是否恢复

```bash
git fetch origin
git show origin/main:路径/文件
```

## 拉取前本地有未提交改动怎么办

### 方案一：先提交
如果改动已经成型，优先提交到本地分支：

```bash
git add .
git commit -m "wip: save local progress"
git pull --rebase origin main
```

### 方案二：先暂存
如果暂时不想提交，可以先 stash：

```bash
git stash push -m "temp before pull"
git pull --rebase origin main
git stash pop
```

如果 stash pop 后有冲突，需要手动处理并重新检查。

## 冲突处理建议
- 冲突出现后，先看清是本地变更还是远程变更覆盖了什么内容。
- 不要为了快速结束冲突而整段覆盖，先确认业务逻辑和配置是否都保留。
- rebase 冲突处理完成后继续执行：

```bash
git add 已解决的文件
git rebase --continue
```

- 如果确认本次 rebase 不应继续，可执行：

```bash
git rebase --abort
```

## 禁止事项
- 不要提交 .env 或任何真实密钥。
- 不要在不理解差异的情况下使用强制推送覆盖公共分支。
- 不要把功能开发、文档调整、依赖升级和大范围格式化混在同一个提交里。
- 不要在拉取远程代码前忽略本地未提交改动的风险。

## 推荐的日常最小流程

```bash
git fetch origin
git switch main
git pull --rebase origin main
git switch -c feat/short-description
git add .
git commit -m "feat: short description"
git push -u origin feat/short-description
```