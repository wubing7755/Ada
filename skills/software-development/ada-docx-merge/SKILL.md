---
name: ada-docx-merge
description: "Use when merging Word .docx chapters with format fidelity."
version: 1.0.0
platforms: [windows, linux, macos]
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [docx, word, merge, styles, xml, document]
    related_skills: [ada-document-artifacts]
---

# DOCX 跨文档章节级合并

把多个 docx（内容源 + 格式模板）按章节归属合并为一个新文档，**格式以指定模板为准**。
典型场景：甲方模板 + 内容源文档，按"第 X~Y 章用 A 文档、第 Z 章用 B 文档"合并；文档模板作为格式基座。

## When to Use（何时用）

- 用户要求把文档 A 的若干章插入/替换文档 B，且指定格式基准
- 多份同项目文档需要按章节整合
- 需要"整章替换"而非逐句融合
- 单工件提取：从文档 A 抽一张大表 + 表注（如需求—设计追踪矩阵 144×6）到"模板副本新建的独立文档"，格式/页面方向完全保持源文档

## 核心策略

**以格式模板 docx 为基座**（复制整个 zip），只对 `word/document.xml` 做元素级手术：
1. 删除基座中要替换的章节（body 子元素切片）
2. 从源文档提取块（body 子元素切片，按"标题文本 + pStyle"精确定位边界）
3. 深拷贝块元素插入基座 body
4. 基座的 styles.xml / numbering.xml / settings.xml / 页眉页脚 / 分节结构**原样保留** → "格式以模板为准"自动成立，无需事后清洗

**不要**用内容源做基座再套模板格式——事后清洗样式/编号/页面设置极易出错。

## 合并前必做分析（证据驱动，先看 XML 再动手）

1. **章节树**：python-docx 遍历标题段落。确认各文档章节结构、哪些章节是**空 H2 壳**（只有标题无内容——这通常是"该章以另一文档为准"的信号，不是错误）。
2. **标题编号机制**：检查 `styles.xml` 中 Heading 样式定义（`w:numPr`/`numId`）。同源文档的标题编号通常在**样式级**而非段落级 → 保留基座 styles/numbering 后编号自动正确，绝不手工编号。
3. **跨文档样式语义**：样式数量接近 ≠ styleId 一致。**同源文档的 styleId 分配可能不同**：
   - 同义不同名：'段落' 在 A 是 `afffffffff1`、在 B 是 `afffffff8`
   - 同名不同义：`afffffffff1` 在 A 是"段落"、在 B 是"标准文件_三级条标题"
   必须建 **styleId → 样式名 → 基座 styleId** 映射，按名重映射内容里的 pStyle/rStyle/tblStyle 引用。
4. **图片格式**：先查 `<w:drawing>` 计数，**为 0 不代表没图片**——这些文档常用 **VML**（`<w:pict>` + `<v:imagedata r:id="rIdX">`）。用 `r:id` 扫描 imagedata 并对照 media 文件数。
5. **分节符/书签/域**：统计 `w:sectPr`（段落级）、`bookmarkStart`、TOC 域、`updateFields`。搬入块内的 sectPr 和 bookmark 必须清除（ID 冲突、节结构错乱）。
6. **表格位置**：表格（w:tbl）是 body 子元素，与段落交错。用表格前后 Caption 段落文本定位。合并前确认"边界外"的表格归属（如源文档第 6 章的追踪矩阵不在前 5 章范围 → 不搬入是正确行为）。

## 合并步骤

1. 复制基座 zip → 产物；lxml 解析 `word/document.xml`。
2. 定位边界：`find_para(root, text, style_id)`（文本精确匹配 + pStyle 匹配标题段落），`body.index(el)` 切片提取/删除。
3. 提取基座标题 pPr：取基座 Heading 1-4 段落的 pPr 深拷贝（含段落级 rPr，如黑体字号）；模板无 H5/H6 段落时构造（pStyle + 与 H1 相同 rPr）。
4. 块转换（深拷贝后）：
   - 移除 `bookmarkStart/bookmarkEnd`、段落级 `w:sectPr`
   - pStyle/rStyle 按名重映射到基座 styleId（无映射打 WARN）
   - **标题段落**：pPr 整体替换为基座标题 pPr（格式严格以模板为准）
   - **正文段落**：pPr 删除视觉直接格式 `spacing/ind/jc/pageBreakBefore/outlineLvl`（按基座样式渲染）；保留 keepNext/numPr/rPr
   - **表格内段落**：只重映射 pStyle，不动直接格式（避免破坏表格）
   - **VML 图片**：`<v:imagedata r:id>` → 源 rels → media 文件 → 复制到产物 `word/media/`（同名且内容不同则重命名 `image_mN.ext`）→ 追加 rels 条目（新 rId）→ 更新属性
   - `[Content_Types].xml` 追加缺失扩展名注册
5. 组装：删除基座目标区间 → 按顺序插入块（`body.insert(pos, el)` 逆序插）。
6. settings.xml 加 `<w:updateFields w:val="true"/>` → Word 打开自动刷新 TOC 域。
7. 写出产物 zip（lxml `tostring(xml_declaration=True, encoding='UTF-8', standalone=True)`）。

## 关键代码片段

```python
VML = 'urn:schemas-microsoft-com:vml'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def wq(t): return '{%s}%s' % (W, t)
def rq(t): return '{%s}%s' % (R, t)

# 样式按名映射: {src_styleId: tpl_styleId}
def build_style_map(src_styles_xml, tpl_styles_xml):
    # 解析两份 styles.xml: styleId -> <w:name w:val>
    # 基座按名建 {name: styleId}; 源按 id 查名; 同名即映射
    return mapping

# 图片重映射
for im in block.iter('{%s}imagedata' % VML):
    rid = im.get(rq('id'))
    # rid -> 源 rels Target(media/xxx) -> 复制文件 -> 新 rId -> im.set(rq('id'), new_rid)
```

## 后处理（交付前必做，用户验收前必须处理）

1. **接受修订（tracked changes）**：源文档常带甲方修订（`w:ins`/`w:del`）。不做 → Word 把修订显示为**页面右侧灰色批注框（气球）**，用户看到"灰色背景+文字"必被退回。处理：`w:ins` 解开（子元素提升到父级，含 rPr/trPr 内空 ins）、`w:del` 删除（含 delText）；顺序上先清批注引用再解 ins 再删 del。方向（接受 vs 拒绝）交付时说明。
2. **移除悬空批注引用**：若 comments.xml 部件未搬入，document.xml 里残留的 `commentRangeStart/commentRangeEnd/commentReference` 指向不存在的批注 → Word 报错/空白气泡。必须删除。
3. **统一页面宽度**：模板自身可能混用页面（如目录节 US Letter 12240×15840、正文节 A4 11906×16838）→ 翻页宽度明显不一致。交付前把所有 sectPr 的 `pgSz` 统一为 A4（去掉 orient/code 属性），`pgMar` 统一。注意：**这是模板自身的缺陷**，三个同源文档都有；只修产物还是连模板一起修，交付时向用户说明。
   **横向节（landscape）**：若某章（如宽表章节）需要横向，构造分节符段落 `<w:p><w:pPr><w:sectPr><w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/><w:pgMar .../></w:sectPr></w:pPr></w:p>`。分节符语义：**sectPr 定义它之前的节**；body 末尾 sectPr 定义最后一个节。第 X 章横向 = 在 X 章 H1 前插 A4 分节符、X 章末尾（下一章 H1 前）插 landscape 分节符。**页面统一逻辑必须跳过 `orient="landscape"` 的节**，否则横向被改回纵向。
4. **统一表注/图注**（用户常要求"所有表注/图注格式以某基准注为准"）：全部注统一为基座 Caption 样式（如 affa）+ `jc=center` + `ind firstLineChars=0 firstLine=0`。pPr 重建按 schema 顺序 pStyle→ind→jc→rPr。**识别**：Caption 样式段落 或 正则 `^(表|图)[ -]?\d`（排除"图像条目新增""图层管理功能"类以图/表开头的标题正文误报）。无 run 的空 Caption 段落是源残留，直接删除。
5. **重算 SEQ 域静态编号**：图/表注编号是 `SEQ 图`/`SEQ 表` 域，合并后静态结果可能跳号/缺号（用户 Word 打开若 updateFields 未生效会看到"图 18 后无图 17"）。按文档顺序重算结果 w:t。**坑**：instrText 被拆成多个 run（`' SEQ '`、`'图'`、`' \* ARABIC '`），判断域类型用标签字符 `'图' in txt`/`'表' in txt`（field_label 未定时），不要用 `'SEQ' in txt`——标签 run 单独成 run 时不含 'SEQ'，会漏判。状态机：fldChar begin → in_field；instrText 定 label；separate 后结果区 w:t 数字改写；end 重置。
6. **条目正文格式对齐**（用户要求"某章设计条目格式与另一章基准条目一致"）：只对齐正文段落样式、不改标题层级/文字。基准模式通常为：【标签】段落（`【设计编号】`等）→ Normal Indent，`SR-\d+` 来源值 → Normal Indent，SD 编号/名称/描述正文/约束正文 → Normal（无 pStyle）。按区域（两个 H2 之间）遍历段落，状态机跟踪「设计要求及约束」/「设计」标题，其下正文段落按内容分类重建 pPr（**跳过分节符段落**）。图注（Caption）跳过。

## 补充图合并（第 2 份源文档只补图）

用户常再给一份"完善版"文档，要求把其中比基线版**多出的图**合入合并产物（内容不改，只加图）。方法与坑（已实测）：

1. **找独有图**：按 media **内容哈希（md5）** 对比基线版与完善版——文件名相同但内容相同不算新增；`新哈希集合 - 基线哈希集合` = 独有 media（完善版通常 = 基线全部图 + 独有新图）。
2. **定位图片段**：完善版 rels 反查独有 media → rId，扫 `v:imagedata` 定位图片段。**必须用 lxml body 直接子元素索引**——python-docx `doc.paragraphs` 含表格内段落，索引与 lxml 不一致，按 python-docx 索引取"前一段/后一段"会取错上下文。
3. **判定替换 vs 新增**：图片段含 `w:del`（原图在 del 里）= **替换**（完善版删旧图插新图）；纯 `w:ins` = **新增**。替换 = 找目标图注段（图注名匹配子串）→ 替换其图片段 + 图注段；新增 = 锚点段后插入图片段 + 图注段。合并产物缺图（图注前无图片段）常常正是因为基线源文档自身修订 del 删了图——完善版补图正是修复，此时"替换"实为"插入补图"。
4. **图注归属用显式映射表**：图片段后紧邻的"图"开头段落可能是**下一张图**的图注（实测：image36 后紧邻"可用 Widget 插件展示"图注，误抓导致图注重名重复）。每张独有图显式指定图注名（无图注 = None），后邻图注名须包含指定名才算归属。
5. **图片重命名冲突**：`image_mN.ext` 重命名必须 while 循环检查产物中未被占用（`cand_path not in out_files`），否则覆盖已有图——症状：media 总数少于"基座 + 新增"。
6. **提取时接受修订**：图片段在 `w:ins` 内 → 解开 ins、删 del、移批注引用（复用 accept_revisions 的段落级版）。
7. 插入后统一图注（Caption 格式）+ reseq 重算图编号（新增图注数量计入编号）。

## 图片原位替换（按设计编号/条目匹配，改既有文档）

用户已有成稿 docx（某章每个设计条目含旧图），要求把新生成的 PNG（**文件名 = 设计编号**，如 `SD-1.png`）按编号替换**指定章节内**对应条目的旧图，其他章节同编号不动。用户确认的\"原位替换\"= 位置/图注/显示尺寸/段落结构全不变，只换图内容。已验证的最稳做法：

1. **按标记段提取条目区域，不要按样式层级**：同文档不同子章节层级可能不同（实测 5.2.1 条目是 H4 名 + H5 设计标题；5.2.2+ 多一层 H4 子分组 + H5 条目 + H6 设计标题），按 style 层级提取会张冠李戴（SD-13~17 全挂到\"线型\"名下）。可靠方式：找所有 `【设计编号】` 标记段（**与 SD-x 值在相邻两段**，不在同段），条目区域 = `[设计编号段, 下一个设计编号段)`；区域内图片 rId = 该条目旧图。条目名 = 从设计编号段**往回扫**最近的条目名段落（style=4/5 且文本非\"设计要求及约束\"/\"设计\"），遇标题样式(H1/H2/H3)停。
2. **核对映射**：png 文件名(SD-x) ∩ 目标章节带图条目集合；显式报告\"无对应条目/条目无旧图\"的例外（不要静默跳过）。
3. **替换前安全检查**：每个目标 rId 全局引用次数必须 = 1（VML imagedata 计数）；每个目标 media 文件必须只被 1 个 rId 引用（rels 反查）→ 覆盖 media 内容不会误伤其他章节；新旧文件 magic bytes 都要合法（PNG = `89504e470d0a1a0a`）。
4. **原位替换 = 只覆盖 media 内容**：复制源 docx → 新文件；zipfile 读出全部条目，仅把 `word/media/imageN.png` 内容换成新 png（保留原 ZipInfo 元数据，`zout.writestr(item, data[item.filename])`）；**document.xml 零改动**（md5 应完全一致）。比\"删图段+插新段\"或\"改 rId 指向\"更保真——图注、VML shape 尺寸、rId 全部不动。
5. **验证**：media md5 == 新 png md5；document.xml md5 与源一致；非 media 文件零差异；python-docx 可打开；目标 rId 仍在。
6. 交付提醒：原位替换保留旧图框尺寸，新图宽高比不同会拉伸——需按新图比例调尺寸时改 VML shape style width/height。

## 单工件提取（大表/图 + 表注 → 模板副本独立文档）

用户有时要求"把文档 A 第 6 章的某张表复制到从模板新建的文档中，格式不变（含页面方向）"。与整章合并不同，只搬一个表格 + 表注，但格式保真要求等同。

1. **定位源工件**：用 lxml body 直接子元素索引定位 `表注段(pStyle=caption styleId) + 紧随的 w:tbl`。表格行数（如 144×6）是可靠指纹。
2. **表注样式重映射**：源表注 pStyle 是源 caption styleId（如 `affc`），**在模板中该 styleId 可能是完全不同的样式**（实测： 的 `affc`=caption，模板的 `affc`=Hyperlink 字符样式，模板 caption 是 `affa`）。必须按样式名"caption"映射到模板的 caption styleId，否则表注渲染成超链接样式。
3. **表注含 SEQ 域**：表注文字是"表" + 连字符 + `SEQ 表 \* ARABIC` 域 + 名称。SEQ 域静态缓存值保留（如"表-5"），模板无 `settings.xml`/无 `updateFields` 时 Word 打开**不会**自动重算 → 显示保持"表-5"。
4. **表格本体深拷贝**：纯直接格式的表格（无 tblStyle、无 pStyle/rStyle 引用、无表格内图片）可直接深拷贝，无 rId/media 依赖。
5. **目标文档**：复制模板 zip → 产物；删除模板对应章节的空表（表注 + 空 tbl + 尾随空段）；插入源表注 + 源表格。模板的引导句（如"本文档是依据文件《软件需求规格说明》…"）保留还是删除交付时向用户确认。
6. **页面方向**：源文档第 6 章是横向（由该章结束分节符的 landscape 定义）。模板正文通常是单节（仅 body 末尾 sectPr）。构造两个分节符段落：目标章 H1 前插 A4 分节符、目标章末尾（下一章 H1 前）插 landscape 分节符。分节符语义：**段落内嵌 sectPr 定义它之前的节**，body 末尾 sectPr 定义最后一节。

## 跨文档表格本体替换（改既有文档的某张表）

用户要求\"用文档 B 的表替换文档 A 第 X 章的同名表\"（如用需求设计追踪矩阵.docx 的已清理表替换 _替换图.docx 第 6 章表-5）。可靠做法：

1. **定位两表**：行数（144×6）是最可靠指纹；目标文档按\"表注段 + 紧随 w:tbl\"定位，`body.index(el)` 拿到索引。
2. **兼容性预检**：源表是否纯直接格式（无 tblStyle / 无 pStyle/rStyle 引用 / 无表格内 rId）→ 若纯直接格式则可整体深拷贝替换，无 rels/media 依赖。检查源表引用的样式 ⊆ 目标 styles.xml。
3. **替换**：`tgt_body.replace(tgt_tbl, copy.deepcopy(src_tbl))`——只换表格本体，表注段/分节符/周围段落零改动。
4. **结构清理**：源表若带空 run（只有 rPr 无内容节点，Word 编辑残留）会引入与目标不一致的结构；替换前清理或替换后按\"单段单 run\"目标结构核对。
5. **验证**：语义签名对比（忽略 rsid/paraId/textId/lastRenderedPageBreak/proofErr）源表 vs 替换后表 = 0 差异；表注编号保持目标文档的（\"表-5\"不变成\"表-1\"）；横向节保持；周围段落未动。

## 单元格只改文本不动格式（内容清洗类）

需求如\"删除父项层级列单元格内 `UR-38 / SR-48` 前缀，只留 SR-48，格式不变\"：目标单元格多为**单段单 run**，`<w:t>` 内是纯文本 → 直接 `t.text = re.sub(r'^UR-\\d+\\s*/\\s*', '', t.text.strip())`，不碰 tcPr/pPr/rPr 任何节点。验证：UR 残留 = 0、`jc=center` 计数不变（143/143）、run 数不变、其他列零改动。若发现某格多一个空 run（Word 残留），视\"与目标结构一致\"要求决定是否清理。

## 语义级 XML 对比（格式保真验证）

合并/提取后验证"格式与源完全一致"时，**不要用字符串比较**：lxml 序列化会带不同的命名空间前缀声明空白（`<w:tblPr                                    >` vs `<w:tblPr                >`），`re.sub(r'xmlns:\w+="[^"]*"', '', s)` 也去不掉前缀长度差异，产生假 diff。用**递归签名**：`tag + 排序后的 attrs（忽略 rsid*/paraId/textId 等元数据属性）+ 子元素签名递归`，文本不参与（内容另行抽查）。签名相等 = 语义级格式一致。实测：tblPr/tblGrid/单元格 tcPr/pPr/rPr 逐节点对比。

## 验证（必做）

- `docx_validate.py`（productivity/docx 技能自带）：`ok: true` 且 `issues: []`
- 章节树对比：各章归属与需求一致
- 引用完整性：pStyle/rStyle 引用 ⊆ styles.xml styleId；numId 引用 ⊆ numbering.xml；rId 引用 ⊆ rels；imagedata rId ⊆ 图片 rels
- 图片计数 = 基座 + 各块之和；未引用的孤儿 rels/media 无害可保留
- 标题 pPr 抽样：与基座标题 pPr 逐字段一致
- 最终验收：Word 打开（updateFields 自动刷目录），检查标题编号/图片/目录

## 坑

详细代码模式、诊断要点与本类任务用户偏好见 `references/word-xml-merge-pitfalls.md`。

- **Python 3.11 f-string 不能含反斜杠**（`f"{re.findall(r'\"', s)}"` 语法错误）→ 预编译正则或字符串拼接。
- 空 H2 章节 + 该章"以另一文档为准"是常见需求结构，不是数据错误。
- 边界外内容（如源文档第 6 章的表）不搬入是正确行为；合并前把边界外归属讲清楚，避免误判"丢失"。
- 用 `<w:pict>` VML 的文档，`<w:drawing>` 计数=0 会误导"无图片"判断。
- 三个同源文档 styles.xml 数量接近但 styleId 分配不同——**永远按样式名映射，不要假设 styleId 兼容**。
- 源文档带修订时，搬入内容会把 ins/del 一起带入 → 交付前必须"接受修订"，否则 Word 右侧灰色修订气球。
- 批注引用（commentRange/commentReference）随块搬入但批注部件不搬 → 悬空引用，必须删除。
- 模板自身节宽不一致（Letter 目录节 / A4 正文节）是模板缺陷，三个同源文档都有——先确认"格式以模板为准"是否包含修正此缺陷，交付前统一 pgSz/pgMar。
- **样式重映射函数定义了但没调用**（最常见 bug）：写了 `remap_style_attrs` 却在 `process_para` 里忘了调用 → 搬入段落保留源 styleId，正文渲染成模板"标准文件_三级条标题"、图注 pStyle 失效回退 Normal。写完立即 grep 确认映射函数真的被调用；验证 pStyle 分布应全为基座 styleId。
- **Word 自动修复掩盖无效样式引用**：Word 打开时自动把 document.xml 引用的缺失 styleId 补进 styles.xml → `docx_validate` 通过、引用完整性"无缺失"，但样式语义全错（用户看到乱格式）。检测：`md5(产物 styles.xml) != md5(模板 styles.xml)` 说明被修复过/有问题，必须查 pStyle 是否残留源 styleId。
- SEQ 域重算后表注编号会按全文顺序连续化（如模板"表 6"顺位变"表 4"）——这是 Word 更新域的实际行为，交付时说明。
- **分节符段落会被后处理误删（最阴险的节破坏 bug）**：`align_entry_format`/`unify_captions` 等任何"重建 pPr"的逻辑，遇到分节符段落（空段落 + `w:pPr/w:sectPr`）会把 pPr 重建为普通段落，**sectPr 丢失** → 节边界合并（症状：第 5 章被并入第 6 章的横向节）。所有遍历/重建逻辑必须 `if pPr.find(wq('sectPr')) is not None: continue`。
- **Word 打开弹"该文档包含的域可能引用了其他文件"**：这是 `updateFields=true` + TOC/PAGEREF 域的标准提示（PAGEREF 是引用类域，Word 措辞保守），无害，让用户点"是"（目录/编号刷新，内容格式不变）。不是文档损坏。
- **分析/修改必须基于脚本刚生成的干净产物**：用户用 Word 打开并保存后 styles.xml 被改写（补齐缺失样式、重命名样式），md5 不再等于模板。任何后续分析读到的都是被污染状态，会得出错误结论（如 pStyle=afffffffff1 显示为"段落"）。要修改就先重新跑合并脚本再立即分析。
- **python-docx `doc.paragraphs` 含表格内段落**，索引 ≠ lxml body 直接子元素（`[el for el in body if el.tag == wq('p')]`）。跨文档取"前一段/后一段"上下文、定位锚点时，两种视角混用会取错段落（实测：同一图片段的"前一段"在两种视角下分别是引导句和空段落）。上下文/锚点分析统一用 lxml 视角。
- **lxml `el.find('{ns}tag')` 只找直接子元素**：找嵌套的 `v:imagedata`（在 `w:r/w:pict/v:shape` 内）要用 `el.find('.//{VML}imagedata')` 或 `el.iter('{VML}imagedata')`——直接 find 返回 None 导致"找不到图片段"误判。
- **单工件提取时源 caption styleId 在模板中可能同名不同义**： 的 `affc`=caption，模板的 `affc`=Hyperlink 字符样式（模板 caption 是 `affa`）。表注必须按样式名映射，不能保留源 styleId——否则表注显示为超链接样式（蓝色下划线）。
- **模板无 settings.xml 时无 updateFields**：Word 打开不自动刷新域 → SEQ 静态缓存值保留（表注显示"表-5"而非重算的"表-1"）。若用户手动更新域（Ctrl+A→F9）编号会变，交付时说明"保持编号则勿更新该域"。
- **字符串比较 XML 产生假 diff**：lxml 序列化命名空间前缀声明空白不同（`<w:tblPr  ...>` vs `<w:tblPr ...>`），`strip_ns` 正则对比误报"格式不一致"。用忽略元数据属性（rsid/paraId）的递归签名做语义比较。
- **条目提取别按样式层级**：同文档不同子章节标题层级可能不同（5.2.1 条目 H4 / 5.2.2+ 多一层 H4 子分组），按 style 提取 SD 归属全错（SD-13~17 全挂到"线型"名下）。按 `【设计编号】` 标记段（与 SD-x 在相邻两段）定位条目区域 `[设计编号段, 下一个设计编号段)` 最可靠。
正文标识符被拆到多个 `<w:t>`：正文叙述里的 `SD-6` 常是 `"SD"` + `"-6 规定"` + `"…"` 三个 t 节点（Word 自动拆分），单 t 正则匹配必为 0。修复 = 段落级拼接全文替换 + 回写首 t 节点、其余 t 置空（保留 run 结构）。表格单元格内标识符通常是单节点可直接改，两者路径不同。详见下文「编号重排 + 交叉引用同步」。
- **原位替换图片 = 覆盖 media 内容而非改 XML**：document.xml md5 与源一致才算真·原位；改 rId 或删插段都会动结构。前提：目标 rId/media 全局仅被引用一次（替换前必须核验全局引用计数）。

## 验证补充

- 后处理后 `w:ins`/`w:del`/`commentRangeStart`/`commentReference` 残留 = 0
- 所有 sectPr 的 pgSz 完全一致（无 Letter/A4 混用）
- 产物 pStyle 分布全部为基座 styleId（无 `affffffffffb`/`affc`/`TOC3` 等源 styleId 残留）
- 产物 styles.xml md5 == 模板 styles.xml md5（未被 Word 修复）
- 表注/图注统一计数 = 预期注数；SEQ 重算后图/表编号连续
- 空 Caption 段落（无 run）已删除

## 编号重排 + 交叉引用同步（如 SD-n 设计编号）

场景：某章 N 个设计条目 SD 编号乱序/重复（实测 207 条目、152 唯一编号、55 个重复），需按出现顺序重排为 SD-1..SD-N，并同步第 6 章追踪矩阵表"设计编号/章节"列与正文引用。正确性靠**单一事实源 + 按索引映射 + 独立重扫**保证，不靠肉眼检查。

1. **单一事实源**：先提取全部条目（按文档出现顺序），生成 `mapping`（出现序号、旧SD、设计名称、所在H2、H2内序号），新编号=出现序号。存 JSON artifact；所有修改引用它，绝不在修改过程中临时算号。
2. **按索引映射，不要按旧值字典查找（关键 bug）**：旧编号有重复（如 SD-2 出现两次）时，`old2new` 字典会塌缩——两个不同条目查同一旧号得到**同一个**新号。条目修改必须 `mapping[i]['new_sd']`（按条目索引），不能 `old2new[旧号]`。表列更新可用名称映射（名称唯一才可靠）。
3. **交叉引用表按"设计名称"匹配，不按旧编号**：追踪矩阵"设计编号"列用设计名称查映射更新；名称匹配不到的行保留原值并标注。
4. **独立重扫验证**：重新解包产物、从头扫描（不依赖修改脚本记忆），断言：新编号唯一、1..N 连续无跳号、表列与章节按名称交叉一致。任一断言失败即中止。
5. **产出对照表**：旧→新→名称→章节 .md，供人工抽查。

**正文自由文本引用同步（不可全自动，先出决策表给用户审）**：正文引用旧编号时无法靠编号定位（旧号重复 + 无名称上下文），盲改字典会改错。分类判定：
- **A 类·图注**（"SD-1 XX设计示意图"）：文本含设计名称 → 名称精确匹配 → 可靠可自动
- **B 类·叙述**（"SD-6 规定的保护流程"）：按所在条目标题 + 语义上下文推断 → 需人工确认
- **C 类·无法确定**：保留原值 + 标注
先输出决策表 .md（位置/类别/原文/推断指向/建议新编号/依据），用户逐条确认后才写入；写入后重扫断言正文无残留旧编号。分类陷阱：叙述文本里恰好含某设计名称字样会被误判为 A 类图注——以"是否 `SD-X 名称示意图` 句式"为准。

**正文替换的跨 `<w:t>` 拆分陷阱（最易踩）**：正文里 `SD-6` 常被 Word 拆成多个文本节点（实测 `"SD"`、`"-6 规定"`、`"的保护流程…"` 分属 3 个 `<w:t>`），按单节点正则匹配**永远为 0**（脚本报"changed: 0"但索引和文本都对）。诊断：dump 目标段落的所有 `<w:t>` 看是否拆分。修复：**段落级全文替换 + 回写首个 t 节点**——拼接该段全部 `w:t` 得完整文本 → 在完整文本上做正则替换（负前瞻 `SD-{num}(?!\d)` 防 SD-1 误配 SD-11）→ 把替换后全文写回**第一个** `w:t`，其余 `w:t` 文本置空串（保留 run 结构，格式不变）。改后验证：目标段落含新号、不含旧号。

**目标文件被 Word 占用**：docx 在 Word 中打开时 zip 写回抛 `PermissionError`。不要强写（会与 Word 句柄冲突、可能覆盖未保存改动）。用户偏好：**复制一份新文件作为修改目标**（如 `xxx_设计编号排序.docx`），原文件不动——既绕开锁也保留原件。

### 追踪矩阵补行（缺失章节条目 → 表-4/表-5）

场景：表-5 需求—设计追踪矩阵缺某章全部条目需补行；表-4 流程图追踪表缺对应流程图行。

1. **条目提取不能只认单一标题样式**：同一章内标题样式可能不一致。判定条目标题用"下一段是 `设计要求及约束`"模式，不是 styleId 白名单。分组标题（无 SD 编号）会误判为条目——过滤 sd 为空者，编号连续无缺口才是完整集。
2. **章节号推算 + 用 TOC 静态缓存验证**：旧 CSV 有章节号↔旧SD 映射且旧SD→新SD 是线性平移时可推算；但必须验证——TOC 域静态文本就是 Word 渲染后的真实编号，与推算一致才可信。标题段落可能无 numPr（编号在样式定义里），不能只信 numPr。
3. **跨来源编号体系必须先验证同一性**：用外部来源填"父项层级/父需求"列前，先在已知重叠记录上验证编号体系一致。一个冲突点即否决整张映射。**但别放弃找源**：SRS md 里 `SR-x` 与 `REQ-F-x` 可能是同一体系，父项 = 条目 Source 字段的 `REQ-F-y`。精确匹配必须负前瞻（`REQ-F-40(?!\d)`），否则误配 REQ-F-402/403。
4. **数据缺口给选项，不编造**：某列无可靠来源时，给出 A 留空 / B 启发式（可能错）/ C 用户提供源文件 三个选项让用户决策，绝不擅自填充。
5. **行组织方式先问用户**：多 SR 对一 SD 时两种方案——A 一行多 SR 用 `；` 连接 / B 每 SR 一行拆分。用户选择后按现有格式执行。
6. **克隆现有行 XML 保格式**：`copy.deepcopy` 现成数据行，仅改写各 `w:t` 文本（设第一个 t，其余 t 置空串），tcPr/pPr/rPr 全不动 → 格式 100% 保持。表中间插入 `anchor.addprevious(tr)`；表尾追加 `last.addnext(tr); last = tr` 链式。
7. **表-4 图号列 = 表内序号，不是正文图号**：新增行图号续接表内最大图号，不要抄正文图号。
8. **图注无"图 X"编号的图也要收**：扫描图片段 `v:imagedata` 找图，不是只匹配"图 X"文本。
9. **SR 规范化 + 内容疑点交用户**：源可能有前导零（SR-062 → SR-62）写入前规范化；内容级疑点不改原文，列待确认项，用户裁决后按原文保留。
10. **验证**：行数断言、章节顺序、图号连续、新增行与模板行**语义签名一致**（tag+排序 attrib，忽略 rsid/paraId/textId）、`zipfile.testzip()` OK。写前先备份原文件。
