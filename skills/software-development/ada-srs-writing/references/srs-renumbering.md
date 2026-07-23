# SRS 需求重编号程序

当需求文档中的编号因删除/合并/重排出现跳号时，使用以下可靠方法一次性重编号。

## 前提

- 文档中的每个需求头格式为 `REQ-F-XXX <emoji> [Actor:...]`，后跟 `空行` + `Title` + 标题文本 + `空行` + `Description`
- 已废弃的需求编号在文档中以"已合并"、"已删除"注解的形式存在
- 重编号前必须 `git stash` 保存当前状态

## 步骤

### 1. 识别真实需求头

```python
import re
with open('SRS.md', 'r') as f: lines = f.readlines()

genuine_f = []
for i, l in enumerate(lines):
    m = re.match(r'^(REQ-F-\d{3})\s+(🔴|🟡|🟢)\s+\[Actor:.+\]', l.strip())
    if not m: continue
    # 必须是后跟空行 + Title 的才算是真实需求头
    if i+5 >= len(lines): continue
    if lines[i+1].strip(): continue  # 空行
    if lines[i+2].strip() != 'Title': continue
    if not lines[i+3].strip(): continue  # 标题文本非空
    if lines[i+4].strip(): continue  # 空行
    if lines[i+5].strip() != 'Description': continue
    genuine_f.append(m.group(1))
```

### 2. 构建映射

物理顺序 → 连续编号：

```python
mapping = {}
for new_id, old_id in enumerate(genuine_f, 1):
    mapping[old_id] = f'REQ-F-{new_id:03d}'
```

### 3. 替换全文（关键）

必须使用负向零宽断言防止部分匹配：

```python
for old, new in sorted(mapping.items(), key=lambda x: -len(x[0])):
    pattern = r'(?<![A-Za-z0-9-])' + re.escape(old) + r'(?![0-9])'
    content = re.sub(pattern, new, content)
```

## 常见折戟原因

- 多次重编号导致同一旧 ID 出现在多个真实需求头上 → 需要 `git checkout` 恢复干净版本
- 后缀 `(?![0-9])` 写成 `(?<![0-9])` 导致 REQ-F-1 同时匹配 REQ-F-10
- 真实需求检测只用 `^REQ-F` 开头判断，忽略了交叉引用文本恰好也是行首

## 安全回退

如果重编号出现 ID 重复或跳号：

```bash
git checkout <commit> -- docs/SRS.md  # 恢复干净版本
# 从步骤 1 重新开始
```
