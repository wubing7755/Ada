# 隐私安全的全新仓库初始提交（GitHub Pages 用户站）

背景（2026-08 真实项目实测）：远程仓库提交历史暴露个人信息（作者邮箱等），用户删除远程仓库，要求同名重建并以单初始提交推送。

## 触发场景

- 需要清除 git 历史中的个人信息（作者邮箱、旧提交内容）
- 同名仓库删除后重建（`gh repo create` 同名空仓）
- 以"初始提交"形态发布当前项目（不要旧历史）

## 步骤

1. 先写/更新 README（用户要求双语时：README.md 中文默认 + README.en.md 英文镜像），内容先输出对话审阅再落盘
2. 配置隐私作者（仓库级，影响本仓所有后续提交）：
   ```sh
   git config user.name "<userid>"
   git config user.email "<userid>@users.noreply.github.com"   # GitHub 隐私邮箱
   ```
3. 建同名空仓库：`gh repo create <name> --public`（确认同名已被删除；失败=删除未传播，稍等重试）
4. 单初始提交（orphan 分支替换 main）：
   ```sh
   git checkout --orphan fresh-main   # 无历史、index 清空、工作树保留
   git add -A                          # gitignored 的 .hermes/、data/ 等自动排除
   git commit -m "chore: 初始提交（...）"
   git branch -D main && git branch -m fresh-main main
   git push -u origin main             # 空仓直接 push，无需 --force
   ```
5. 清理残留引用：`git fetch --prune origin`（旧仓库的 origin/chore/*、origin/feature/* 等 remote-tracking 引用被清掉）；删掉已合并的本地旧分支
6. 验证：`gh api repos/{owner}/{repo}/commits --jq 'length'` = 1；`--jq '.[0].commit.author.email'` 确认 noreply 邮箱

## 删除本地初始提交（回到未提交态，等 bug 修复后重新初始提交）

用户可能测试后发现 bug，要求先删本地提交、修复后重新做初始提交：

```sh
git update-ref -d HEAD   # 删除分支 ref → HEAD 变成 unborn（"No commits yet"）
git reset                # 清空 index → 全部文件变 untracked
```

此时 `git status` 显示 "No commits yet" + 顶层条目全 untracked；`.hermes/` 等 gitignored 文件不在列表。

## 注意

- 远端已推的初始提交在本地删除后仍在；修正后的初始提交需 **force push**（`git push -f origin main`）覆盖——全新仓库无他人历史，安全
- 旧历史虽从分支删除，仍存于本地 reflog/对象库；彻底清除（若用户在意本地）：
  `git reflog expire --expire=now --all && git gc --prune=now`
- `gh pr merge --delete-branch` 后本地残留 remote-tracking 引用由 `git fetch --prune` 清理（实测）
- 仓库重建后 GitHub Pages 需重新启用（Settings → Pages → Source: GitHub Actions，或 `gh api` 设 build_type=workflow），否则 deploy-pages 失败
