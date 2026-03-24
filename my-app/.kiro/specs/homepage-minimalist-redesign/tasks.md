# 首页极简化设计 - 实施任务清单

## 第一阶段：结构调整与元素删除

### 1.1 删除冗余HTML元素
- [ ] 删除 `hero-stat` 元素（6个统计卡片）
- [ ] 删除 LOGO底部的两层透明方块
- [ ] 删除中文介绍外围的深色背景框
- [ ] 删除多余的装饰线条

**文件**：`src/views/HomeView.vue`

**验收标准**：
- 这些元素完全从模板中移除
- 页面结构更加简洁
- 无视觉遗留

---

### 1.2 重构左侧文字排版结构
- [ ] 创建新的文字容器结构
- [ ] 添加主标题、副标题、底部修饰的HTML元素
- [ ] 确保语义化标签使用

**文件**：`src/views/HomeView.vue`

**新增HTML结构**：
```html
<div class="hero-text-block">
  <h2 class="hero-text__title">氛围亮度自适应</h2>
  <p class="hero-text__subtitle">让每一次输入都保持清晰与质感</p>
  <p class="hero-text__accent">QUANTUM ACCESS DECK</p>
</div>
```

**验收标准**：
- 结构清晰，易于样式控制
- 语义正确
- 无多余元素

---

## 第二阶段：样式系统优化

### 2.1 建立全局色彩系统
- [ ] 在 `src/style.css` 中定义CSS变量
- [ ] 定义四种主色：黑、白、灰、橙
- [ ] 定义灰色的多个层级（浅灰、中灰、深灰）

**文件**：`src/style.css`

**CSS变量定义**：
```css
:root {
  /* 主色板 */
  --color-black: #0b0d12;
  --color-white: #ffffff;
  --color-orange: #ff7a18;
  
  /* 灰色系 */
  --color-gray-50: #f8f9fb;
  --color-gray-100: #e7e9ef;
  --color-gray-200: #d1d5e0;
  --color-gray-300: #8b92a9;
  --color-gray-400: #6b7282;
  --color-gray-500: #4d5464;
  --color-gray-600: #1a1d24;
  
  /* 背景 */
  --bg-dark: #0b0d12;
  --bg-darker: #1a1d24;
  
  /* 边框 */
  --border: #e7e9ef;
}
```

**验收标准**：
- 所有颜色都通过变量定义
- 易于全局修改
- 无硬编码颜色值

---

### 2.2 实现对角线背景切割
- [ ] 在 `.hero-content` 上添加对角线背景
- [ ] 使用 `linear-gradient` 实现锋利的切割线
- [ ] 调整切割角度和位置

**文件**：`src/views/HomeView.vue` (style部分)

**CSS实现**：
```css
.hero-content {
  position: relative;
  background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-dark) 70%, var(--bg-darker) 70%, var(--bg-darker) 100%);
}
```

**验收标准**：
- 对角线清晰可见
- 切割角度合理
- 无锯齿感

---

### 2.3 优化圆角系统
- [ ] 更新输入框圆角为 4px
- [ ] 更新按钮圆角为 4px
- [ ] 更新卡片圆角为 8px
- [ ] 检查所有元素的圆角一致性

**文件**：`src/views/HomeView.vue` (style部分)

**更新规则**：
```css
/* 输入框 */
.n-input {
  border-radius: 4px !important;
}

/* 按钮 */
.n-button {
  border-radius: 4px !important;
}

/* 卡片 */
.hero-terminal {
  border-radius: 8px;
}
```

**验收标准**：
- 所有元素圆角统一
- 整体显得硬朗
- 无不一致的圆角

---

### 2.4 重新设计输入框样式
- [ ] 去除硬边框，改为底部实线
- [ ] 设置背景为浅灰填充
- [ ] 实现焦点状态（底部线条变为橙色）
- [ ] 移除多余阴影

**文件**：`src/views/HomeView.vue` (style部分)

**CSS实现**：
```css
.n-input__input {
  border: none;
  border-bottom: 1px solid var(--border);
  background: var(--color-gray-50);
  border-radius: 4px;
  transition: border-color 0.2s ease;
}

.n-input__input:focus {
  border-bottom-color: var(--color-orange);
  outline: none;
}
```

**验收标准**：
- 输入框显得简洁
- 焦点状态有明显反馈
- 无多余阴影

---

### 2.5 优化按钮样式
- [ ] 更新登录按钮样式
- [ ] 实现悬停状态（背景变化、阴影增加）
- [ ] 优化其他按钮的样式

**文件**：`src/views/HomeView.vue` (style部分)

**CSS实现**：
```css
.cta-primary {
  background: var(--color-black);
  color: var(--color-white);
  border-radius: 4px;
  transition: background 0.2s ease, box-shadow 0.2s ease;
}

.cta-primary:hover {
  background: var(--color-gray-600);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}
```

**验收标准**：
- 按钮样式统一
- 悬停反馈明确
- 无延迟感

---

### 2.6 优化文字排版样式
- [ ] 设置主标题样式（28px，纯白，粗体）
- [ ] 设置副标题样式（14px，中灰，正常）
- [ ] 设置底部修饰样式（11px，浅灰，大字间距）
- [ ] 确保全部左对齐

**文件**：`src/views/HomeView.vue` (style部分)

**CSS实现**：
```css
.hero-text__title {
  font-size: clamp(24px, 3vw, 28px);
  color: var(--color-white);
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
}

.hero-text__subtitle {
  font-size: 14px;
  color: var(--color-gray-400);
  font-weight: 400;
  line-height: 1.5;
  margin: 8px 0 0;
}

.hero-text__accent {
  font-size: 11px;
  color: var(--color-gray-300);
  letter-spacing: 0.3em;
  margin: 16px 0 0;
}
```

**验收标准**：
- 文字清晰易读
- 层级分明
- 排版整洁有序

---

## 第三阶段：交互增强

### 3.1 实现小人视差跟随
- [ ] 获取小人元素引用
- [ ] 监听鼠标移动事件
- [ ] 计算视差偏移量
- [ ] 应用平滑过渡

**文件**：`src/views/HomeView.vue` (script部分)

**实现要点**：
- 偏移范围：±8px
- 动画：`transition: transform 0.3s ease-out`
- 仅在桌面端启用

**验收标准**：
- 眼睛随鼠标平滑跟随
- 无卡顿
- 移动端无此效果

---

### 3.2 实现密码框聚焦动画
- [ ] 监听密码输入框的焦点事件
- [ ] 创建遮罩元素（机械手/几何形状）
- [ ] 实现升起动画
- [ ] 实现撤下动画

**文件**：`src/views/HomeView.vue` (script部分)

**动画参数**：
- 升起时长：0.4s
- 缓动函数：`cubic-bezier(0.34, 1.56, 0.64, 1)`（弹性效果）
- 撤下时长：0.3s

**验收标准**：
- 动画流畅
- 交互反馈明确
- 无性能问题

---

### 3.3 实现显示密码交互
- [ ] 添加眼睛图标按钮
- [ ] 监听点击事件
- [ ] 切换密码可见性
- [ ] 实现眼睛微眯表情

**文件**：`src/views/HomeView.vue` (script部分)

**验收标准**：
- 点击反应迅速
- 密码显示/隐藏正确
- 眼睛表情变化明显

---

### 3.4 优化表单交互反馈
- [ ] 输入框焦点：底部线条变为橙色
- [ ] 按钮悬停：背景色变化，阴影增加
- [ ] 链接悬停：灰色变为橙色
- [ ] 复选框：改为黑色或橙色

**文件**：`src/views/HomeView.vue` (style部分)

**验收标准**：
- 所有交互都有视觉反馈
- 反馈及时、清晰
- 无延迟感

---

## 第四阶段：响应式适配

### 4.1 桌面端适配（≥1024px）
- [ ] 确保左右两列布局正常
- [ ] 左侧占60%，右侧占40%
- [ ] 对角线切割显示正确

**文件**：`src/views/HomeView.vue` (style部分)

**验收标准**：
- 布局正确
- 比例合理
- 无溢出

---

### 4.2 平板端适配（768px-1023px）
- [ ] 调整左右两列比例为50:50
- [ ] 调整字号和间距
- [ ] 确保对角线切割仍然清晰

**文件**：`src/views/HomeView.vue` (style部分)

**验收标准**：
- 布局合理
- 文字可读
- 无布局错乱

---

### 4.3 手机端适配（<768px）
- [ ] 改为上下堆叠布局
- [ ] 小人隐藏或缩小50%
- [ ] 调整对角线切割为水平分割
- [ ] 优化文字大小

**文件**：`src/views/HomeView.vue` (style部分)

**验收标准**：
- 布局合理
- 加载快速
- 无横向滚动

---

### 4.4 测试各断点显示效果
- [ ] 在各断点进行视觉测试
- [ ] 检查元素对齐
- [ ] 验证交互功能
- [ ] 测试移动浏览器

**验收标准**：
- 各断点显示效果良好
- 无布局错乱
- 交互功能正常

---

## 第五阶段：性能优化与测试

### 5.1 性能优化
- [ ] 检查动画帧率（目标60fps）
- [ ] 优化CSS选择器
- [ ] 使用GPU加速（transform、opacity）
- [ ] 移除不必要的重排/重绘

**文件**：`src/views/HomeView.vue`

**验收标准**：
- 动画帧率稳定在60fps
- 无性能抖动
- 首屏加载时间不增加

---

### 5.2 浏览器兼容性测试
- [ ] 测试Chrome最新版本
- [ ] 测试Firefox最新版本
- [ ] 测试Safari最新版本
- [ ] 测试Edge最新版本
- [ ] 测试移动浏览器

**验收标准**：
- 所有主流浏览器正常显示
- 无CSS兼容性问题
- 交互功能正常

---

### 5.3 可访问性检查
- [ ] 检查颜色对比度
- [ ] 验证键盘导航
- [ ] 检查屏幕阅读器兼容性
- [ ] 验证焦点指示器

**验收标准**：
- 颜色对比度达到WCAG AA标准
- 键盘导航正常
- 焦点指示器清晰

---

## 第六阶段：最终验收

### 6.1 视觉验收
- [ ] 对比原设计，确认改进明显
- [ ] 检查所有元素的视觉一致性
- [ ] 验证高级感是否达到预期

**验收标准**：
- 用户反馈"显得更高级"
- 视觉层次清晰
- 无视觉不一致

---

### 6.2 功能验收
- [ ] 所有交互功能正常
- [ ] 表单提交功能正常
- [ ] 导航功能正常

**验收标准**：
- 所有功能正常运行
- 无功能回归
- 用户体验提升

---

### 6.3 文档更新
- [ ] 更新设计文档
- [ ] 更新代码注释
- [ ] 记录实施过程中的决策

**验收标准**：
- 文档完整
- 注释清晰
- 易于后续维护

---

## 任务优先级

**高优先级**（必须完成）：
- 1.1 删除冗余HTML元素
- 1.2 重构左侧文字排版结构
- 2.1 建立全局色彩系统
- 2.2 实现对角线背景切割
- 2.3 优化圆角系统

**中优先级**（应该完成）：
- 2.4 重新设计输入框样式
- 2.5 优化按钮样式
- 2.6 优化文字排版样式
- 3.1 实现小人视差跟随
- 4.1-4.4 响应式适配

**低优先级**（可选）：
- 3.2 实现密码框聚焦动画
- 3.3 实现显示密码交互
- 5.1 性能优化
- 5.2 浏览器兼容性测试

---

## 预计工作量

| 阶段 | 任务数 | 预计时间 |
|------|--------|---------|
| 第一阶段 | 2 | 2小时 |
| 第二阶段 | 6 | 6小时 |
| 第三阶段 | 4 | 4小时 |
| 第四阶段 | 4 | 3小时 |
| 第五阶段 | 3 | 2小时 |
| 第六阶段 | 3 | 2小时 |
| **总计** | **22** | **19小时** |

---

## 注意事项

1. **保持向后兼容**：确保删除元素不会破坏其他功能
2. **渐进式增强**：先完成基础样式，再添加交互
3. **测试驱动**：每个任务完成后立即测试
4. **性能监控**：使用浏览器DevTools监控性能
5. **用户反馈**：完成后收集用户反馈，进行迭代

---

## 相关文件

- 设计规范：`design.md`
- 需求文档：`requirements.md`
- 主要实施文件：`src/views/HomeView.vue`
- 全局样式：`src/style.css`
