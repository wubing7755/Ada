---
name: ada-document-artifacts
description: "Use when creating, editing, or analyzing document artifacts — DOCX, PDF, XLSX/CSV spreadsheets, SVG diagrams, and visual deliverables. Covers format-specific tools, style preservation, formula validation, and rendering checks."
version: 1.0.0
platforms: [linux, macos, windows]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [documents, docx, pdf, xlsx, spreadsheet, svg, diagrams, visual]
    related_skills: []
---

# 文档与图表处理

文档交付物的创建、编辑和分析——Word、PDF、Excel、SVG 图表。每种格式有其特定工具链和常见陷阱。

## DOCX

DOCX 是 ZIP 压缩包包含 XML。常规读取用解压工具；精确编辑（修订、批注、编号、节替换）需解包→编辑 XML→重新打包。

| 操作 | 工具/方法 |
|------|----------|
| 创建新文档 | 结构化文档库或模板，显式设置页面/边距/标题样式，验证输出 |
| 编辑现有文档 | 保留模板样式；精确编辑时走 XML 路径 |
| 替换节 | 使用段落/表格边界，不用脆弱的纯文本替换 |
| 图表 | 生成 PNG/SVG，以稳定尺寸插入 |

**陷阱**：
- 搜索工具不搜索 DOCX ZIP 内部二进制→先解压
- 避免手动 Unicode 项目符号（文档模型有原生编号）
- 创建或底层 XML 编辑后验证

## PDF

按任务选工具：

| 工具 | 适用场景 |
|------|----------|
| `pypdf` | 合并、拆分、旋转、元数据、简单页面操作 |
| `pdfplumber` | 文本/表格提取 |
| `reportlab` | 创建新 PDF |
| Poppler 工具 | 渲染页面、提取文本/布局 |
| OCR | 扫描页面无文本层时 |

PDF 表单：先检查字段→编程填充→渲染验证图像→比较位置。

## XLSX / 电子表格

规则：
- 保留现有模板格式和公式
- 用 Excel 公式计算，不要硬编码 Python 计算值
- 重新计算公式并验证零公式错误
- 分析用 pandas，公式/格式用 openpyxl
- 财务模型颜色约定：蓝色=硬编码输入，黑色=公式，绿色=内部链接，红色=外部链接，黄色=关键假设
- 数字格式有意识：单位在表头，零显示为 `-`，百分比含小数精度，财务负数用括号

**验证**：交付前打开 `.xlsx`，确认公式结果、条件格式、数据验证和打印区域。

## SVG 图表

流程图：
- 清晰的空间层次、稳定的画布尺寸、可读的字号、足够的留白
- 密集技术图表：先减少列数再缩小文字
- 先生成 SVG，需要栅格输出时再导出 PNG
- 验证文本不重叠、箭头有意义的连接

VS Code markdown 兼容 SVG：
- 用内联 SVG（markdown 预览可用）
- 避免外部字体/脚本
- 显式设置 width/height/viewBox
- 需要可搜索时保留 SVG text

**常见 SVG 渲染陷阱**（VS Code 预览）：
1. 每行必须有 `> ` 前缀（blockquote）
2. `rx` 不是 CSS 属性→用内联 `<rect rx="2">`
3. 避免特殊 Unicode（`✕` 会导致静默失败）
4. `stroke-dasharray` 必须配 `stroke-width`

## Draw.io

`.drawio` 文件是 mxGraph XML。转 SVG/PNG 时注意缺失的嵌入图片或字体。

## 视觉交付

- 提供直接文件路径和环境支持的内联预览
- 图表同时生成源文件和渲染产物
- HTML 图表保持依赖本地或清晰记录

## Common Pitfalls

- **DOCX 纯文本替换破坏格式**：节替换走 XML 路径，不用文本匹配
- **PDF 扫描页无文本层**：先用 OCR，不要假设 PDF 有可提取文本
- **硬编码计算值代替 Excel 公式**：公式保留可审计性。硬编码值在下一次数据变更时失效
- **SVG 特殊 Unicode 静默失败**：`✕` 等字符使整个 SVG 不渲染，无错误提示

## Verification Checklist

- [ ] DOCX：样式一致，编号连续，图表正确嵌入
- [ ] PDF：页面顺序正确，表单字段已填充，文本层存在（或已 OCR）
- [ ] XLSX：公式重新计算无错误，条件格式正确，数字格式一致
- [ ] SVG：viewBox 正确，文本不重叠，markdown 预览正常渲染
