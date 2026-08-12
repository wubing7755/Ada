# 内容数据录入：Markdown 填写模板工作流

## 触发

用户需要提供批量内容数据（博客/项目/经历/技能/个人资料），对话粘贴不可靠、长文本易丢时。

## 流程

1. 以内容源 schema（XML）为基准生成 `content/数据填写模板.md`：
   - 每字段一行留白，标注必填/可省、格式约束（日期 `YYYY-MM-DD`；多语言字段 zh/en 分行；熟练程度 `90%`/`75`/`4/5`）
   - 重复条目（文章/项目/经历/技能）以 `### 条目 N` 编号，开头注明"复制本节继续编号"
   - 说明"md 仅为录入表单，数据源仍是 content/*.xml"
2. 可自动获取的字段预填：
   - GitHub 项目：`GET https://api.github.com/users/{owner}/repos?per_page=100&sort=updated`（无凭据）预填 name/仓库 URL/英文描述；**语言与 Star 不填**——站点运行时用同一 API 合并
   - 预填后给特殊条目加注（fork 仓库、GitHub profile 配置仓库"如不展示可删除本节"）
3. 用户填完说"数据已填写" → agent 读取 md → 转写为 `content/*.xml`（XML 保持为唯一内容源，勿把 md 变成源）
4. converter 重跑 → 浏览器验证 → 提交

## 要点与坑

- **用户编辑模板过程中不要提交半成品**：模板是进行中文档，等"数据已填写"一次性读取→转换→验证→提交；用户删条目/重编号是正常编辑，不要 git add
- converter 忽略 `content/` 下非 XML 文件（已验证，模板可放同目录）
- 演示图片规范位置 `wwwroot/media/projects/`（随站点发布）；`content/` 不进发布产物，用户误放的图片要移走并说明
- 占位素材（如占位演示截图）可接入占位条目：`<demo><image>media/projects/placeholder.png</image></demo>`，真实素材到位后替换路径

## 新增内容字段的端到端链路（以 demoUrl 为例）

用户提供数据暴露模型缺口时，新增字段的完整改动链：

1. `content/*.xml` schema（如 `<demo><url>…</url></demo>`，与 image/video 并列）
2. `tools/ContentConverter`：解析 + `[JsonPropertyName]` 输出（snake_case/camelCase 显式映射）
3. Blazor `Models/` 属性
4. 组件渲染（未配置不渲染，遵循"不渲染空区域"原则）
5. UI 资源键（zh/en）
6. SDD 文档：3.3 数据表 + 对应 SD-XX 描述（先输出变更文本到对话待批准，批准后改文档）
7. 单测（JSON 反序列化断言）

## 预填脚本骨架（Python，Temp 目录，跑完清理）

```python
import json, re, sys, urllib.request
TEMPLATE = r"C:/.../content/数据填写模板.md"
API = "https://api.github.com/users/{owner}/repos?per_page=100&sort=updated"
req = urllib.request.Request(API, headers={"User-Agent": "site"})
repos = json.load(urllib.request.urlopen(req, timeout=30))
# 以 "## N. 节" 为锚点，re.sub(pattern, new_section, text) 替换对应节
# 注意 Windows 下显式 C:/ 路径调用 python，勿用 /c/ MSYS 路径
```
