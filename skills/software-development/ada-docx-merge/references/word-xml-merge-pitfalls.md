# docx 合并实战细节（来自多轮交付报告合并）

真实文档合并项目实战沉淀。场景：`详细设计报告_模板.docx`（甲方模板基座）+ `详细设计报告_通用.docx`（内容源）+ `详细设计报告.docx`（5.2 来源），章节归属混合（1~4章+5.1+5.3 用通用版、5.2 用报告版、第6章插入通用版、6章后保留模板）。

## 工作流要点

1. 每次修改前先跑合并脚本生成干净产物，**立即**分析（不要隔轮再读磁盘文件——用户 Word 保存会污染）。
2. 合并脚本保持幂等可复现：`_merge_build.py`（合并+后处理）、`_merge_verify.py`（验证）。交付 = 重新生成，不是改磁盘文件。
3. 交付说明固定提醒：Word 打开"域可能引用其他文件"提示点"是"；**不要先用 Word 保存**。

## 关键代码模式

### styleId 按名重映射（必须在 process_para 里真正调用）
```python
# 映射表: {src_styleId: tpl_styleId}，按样式名匹配，同名取基座第一个
# process_para 内：
ps = pPr.find(wq('pStyle'))
if ps is not None:
    v = ps.get(wq('val'))
    if v in style_map:
        ps.set(wq('val'), style_map[v])  # 真正重写！写完再判断标题
sid = para_style_id(p)  # 映射后的值
if sid in heading_ppr:  # heading_ppr = 基座标题 styleId 集合
    # 标题：pPr 整体替换为基座标题 pPr
```
经典 bug：写了 `remap_style_attrs` 函数但 process_para 没调用 → 搬入段落保留源 styleId（如 `afffffffff1`），基座里它是"标准文件_三级条标题"，正文全渲染成条标题。

### VML 图片重映射
```python
VML = 'urn:schemas-microsoft-com:vml'
for im in block.iter('{%s}imagedata' % VML):
    rid = im.get(rq('id'))  # rq = relationships 命名空间
    # rid -> src_rels[rid] Target='media/xxx' -> 读 src_files['word/media/xxx']
    # 复制到产物；文件名冲突且内容不同 -> image_mN.ext
    # 追加 rels: (新rId, image类型, 'media/'+base)
    # im.set(rq('id'), new_rid)
```

### 分节符构造（横向节）
```python
def make_sect_para(w, h, margins, orient=None):
    p = etree.Element(wq('p'))
    pPr = etree.SubElement(p, wq('pPr'))
    sectPr = etree.SubElement(pPr, wq('sectPr'))
    pgSz = etree.SubElement(sectPr, wq('pgSz'))
    pgSz.set(wq('w'), w); pgSz.set(wq('h'), h)
    if orient: pgSz.set(wq('orient'), orient)
    pgMar = etree.SubElement(sectPr, wq('pgMar'))
    for k, v in margins.items(): pgMar.set(wq(k), str(v))
    return p
# 第X章横向：X章H1前插 A4 分节符；下一章H1前插 landscape 分节符
```
sectPr 元素顺序：pgSz 在 pgMar 前（schema 要求）。

### SEQ 域重算状态机
```python
for p in root.iter(wq('p')):
    in_field, field_label = False, None
    for r in p.findall(wq('r')):
        fld = r.find(wq('fldChar'))
        if fld is not None:
            t = fld.get(wq('fldCharType'))
            if t == 'begin': in_field, field_label = True, None
            elif t == 'end': in_field, field_label = False, None
            continue
        if not in_field: continue
        instr = r.find(wq('instrText'))
        if instr is not None:
            txt = instr.text or ''
            if field_label is None:  # 不能要求 'SEQ' 在同 run
                if '图' in txt: field_label = '图'
                elif '表' in txt: field_label = '表'
            continue
        if field_label in ('图', '表'):
            t_el = r.find(wq('t'))
            if t_el is not None and (t_el.text or '').strip().isdigit():
                counters[field_label] = counters.get(field_label, 0) + 1
                t_el.text = str(counters[field_label])
```

### 接受修订
```python
# 1. 移除 commentRangeStart/End/commentReference（批注部件未搬入时悬空）
# 2. w:ins 解开：子元素逐个 insert 到父级 ins 原位置，然后 remove ins
# 3. w:del 删除整个元素（含 delText）
# 注意 rPr/trPr 内的空 ins/del 标记也要清
```

### 表注/图注统一
```python
CAP_RE = re.compile(r'^(表|图)[ -]?\d')
# 识别：pStyle == 基座 Caption styleId 或 CAP_RE 匹配（排除"图像条目新增"等误报）
# 重建 pPr（顺序 pStyle->ind->jc->rPr）：
#   pStyle=Caption styleId, ind firstLineChars=0 firstLine=0, jc=center, 保留原 rPr
# 无 run 的空 Caption 段落 -> 删除
# 所有重建前检查 sectPr 跳过
```

### 条目正文格式对齐
```python
# 区域 = 两个边界 H2 之间（如 公共功能 -> 目标项目 是 5.1）
# 状态机跟踪「设计要求及约束」H4 /「设计」H4
# 其下正文段落分类：
#   text.startswith('【') or re.match(r'^SR-\d+', text) -> Normal Indent(afd)
#   其余（SD值/名称/描述/约束/引导句）-> Normal（无 pStyle，重建 pPr 只留 rPr）
# Caption(affa) 跳过；含 sectPr 的段落跳过；标题重置状态
```

### 条目区域提取与图片原位替换（改既有文档，按设计编号匹配）
```python
# 条目区域 = [【设计编号】段, 下一个【设计编号】段)；SD 值与标记在相邻两段
for i, ch in enumerate(body_p_paras):          # lxml 直接子元素视角
    if pt(ch).strip() == '【设计编号】':
        j = i + 1
        while j < len(body_p_paras):            # 找下一段的 SD-x
            m = re.match(r'^SD[-－]?(\d+)', pt(body_p_paras[j]).strip())
            if m: sd = 'SD-' + m.group(1); break
            j += 1
# 条目名 = 往回扫最近的 style in ('4','5') 且文本非 设计要求及约束/设计，遇 H1/H2/H3 停

# 原位替换 = 复制源 docx，zipfile 重写仅覆盖 media 内容（保留 ZipInfo 元数据）
zout = zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED)
for it in items:                                # items = zin.infolist()
    zout.writestr(it, data[it.filename])        # data[media] 已换成新 png bytes
# 验证：document.xml md5 == 源；非 media 文件零差异；media md5 == 新 png
# 前置安全检查：目标 rId 全局引用==1、目标 media 只被 1 个 rId 引用（rels 反查）
```

## 诊断要点

- 产物 styles.xml md5 ≠ 模板 md5 → 被 Word 修复过（补缺失样式/重命名）。此时 pStyle 分布看起来"正常"（无缺失）但语义全错。
- pStyle 分布应全为基座 styleId；残留 `afffffffff1`/`affffffffffb`/`affc`/`TOC3` 等源 styleId = 重映射没生效或 Word 污染。
- 节结构检查：列所有 sectPr 的 pgSz/orient，确认横向节只覆盖目标章（分节符被误删的症状：某章被并入相邻横向节）。
- 表注/图注编号连续化：表/图注文本 `^(表|图)[ -]?\d` 提取序列，跳号=SEQ 静态结果未重算或注被误删。

## 用户偏好（本类任务）

- 复述需求确认边界后再执行；边界确认通常包括：替换语义（整章替换）、子节跟随、命名、第 5 章后是否动。
- "只改格式不改内容"、"不改标题层级"这类约束要严格执行——处理范围严格限定，别顺手改别的。
- 交付说明里主动列出：Word 提示处理、模板自身缺陷（如节宽不一致）、编号顺位变化（表 6→表 4）。
- 中间产物（分析/合并/替换脚本）留在工作目录，用户允许并默认可复现；用户整理目录后路径会变，执行前先 search_files 确认当前实际路径（本类项目源文件曾从根目录移到 `详细设计报告\` 子目录）。
