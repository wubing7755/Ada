# Blazor WASM 预启动加载页（pre-boot loader）——2026-08 高达变身动画实测

## 适用场景

Blazor WASM 启动（下载 9MB+ 资源）期间，`<div id="app">加载中...</div>` 是唯一可见内容。
把它做成纯 CSS 像素风动画加载页（用户指定"高达变身"风格），零第三方库（NFR-008）。

## 结构决策

- 动画标记放在 `#app` 内（boot 后 Blazor 替换 #app 内容 → 动画区自动消失，无需清理）
- 样式放 index.html `<head>` 内联 `<style>`：与 app.css 解耦（app.css 属于应用态，loader 属于预启动态），loader 类名加前缀（`ms-*`/`loader-*`）防冲突
- 关键帧 `infinite` 循环：加载时长不定，动画必须可循环
- `role="status"` + `aria-label`：加载状态对屏幕阅读器可感知

## 变身动画构成（可复用的机械结构）

| 部件 | 实现 | 动画 |
|------|------|------|
| V 型天线 | 两个 clip-path 三角 + transform-origin 底部 | 收起 rotate(±78°) → 展开 rotate(±30°)，opacity 0.35→1 |
| 头部展开 | 蓝底方块 + 白色脸 inset + 边框 | scaleY 0.45 → 1（"窄方块展开"的变身感） |
| 双眼点亮 | 两个绿色横条 | step-end 时序：0-30% 灭 → 42%+ 亮 + box-shadow 辉光 |
| 变身闪光 | 头部两侧小黄块 | step-end 闪一下（36%-44%） |
| 像素进度条 | 边框容器 + 填充 span | `steps(8)` 分 8 格填充，4s 循环 |

配色用站点像素风变量字面量：#1a5fb4（主蓝）、#144a8c（深蓝）、#e6a817（天线/闪光黄）、#3ddc84（眼绿）、#e8ecf1（脸白）、#2d3a4a（边框/文字）。

## 验证方法（无视觉 provider 时验证 CSS 动画）

1. **组装独立临时页**：python 从 index.html 正则提取 `<style>` 块与 `#app` 内容，拼成独立 HTML 写到 Temp 目录，`python -m http.server 5090` 托管
2. **结构断言**：`querySelectorAll` 确认部件存在 + `getComputedStyle(el).animationName` 确认关键帧挂载
3. **时序采样**：两个时点采样 `getComputedStyle` 的 transform/opacity/width：
   - matrix 解码：`matrix(0.866025, 0.5, ...)` = 30° 旋转；`matrix(1, 0, 0, 0.45, ...)` = scaleY 0.45
   - 实测收起态 finL 约 78°（`matrix(0.207912, 0.978148, ...)`）、head scaleY 0.45、眼 opacity 0、条 0px → 展开态 finL 30°、head scaleY 1、眼 opacity 1、条 67.5px ✓
4. **真实站点确认**：加载 dev 站点，确认 boot 后首页渲染正常（loader 已被替换）+ console 零错误（重点：无 404、无 crit）
5. **创意 UI 节奏**：完整门禁（build/test/format）在用户确认效果满意后再跑；此阶段 ad-hoc 脚本聚焦"改动行为"（结构/关键帧/引导脚本在位），不做全套

## 遗留注意

- 若 WASM boot 失败，loader 会一直停留（与原先文本占位行为一致，可接受）
- 内联 `<style>` 约 4KB，属一次性预启动开销，不随应用运行
