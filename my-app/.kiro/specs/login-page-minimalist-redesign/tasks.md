# 登录页面极简化设计任务清单

## 第一阶段：拟人化小人交互增强

- [ ] 1.1 实现眼睛视差跟随功能
  - 添加鼠标移动事件监听器
  - 计算鼠标相对于视窗中心的偏移量
  - 实现眼睛位置的动态更新逻辑
  - 使用requestAnimationFrame优化动画性能
  - 添加节流机制确保60fps流畅度

- [ ] 1.2 实现密码聚焦时的机械手遮挡效果
  - 为手臂元素添加CSS类用于动画控制
  - 实现手臂抬起动画（从身体两侧移动至眼睛位置）
  - 同步触发眼睛隐藏和遮罩显示动画
  - 使用ease-out曲线确保响应感

- [ ] 1.3 实现显示密码时的眯眼表情
  - 添加眯眼效果CSS样式（transform: scaleY）
  - 实现遮罩撤除动画
  - 实现眼睛从眯起到睁开的过渡动画
  - 添加200ms延时后恢复正常状态

- [ ] 1.4 优化常态悬浮动画
  - 调整悬浮动画周期为6秒
  - 调整位移幅度为上下8像素
  - 验证动画不影响眼睛视差跟随效果

## 第二阶段：左侧视觉区域优化

- [ ] 2.1 调整文字排版位置
  - 将主标题和副标题移至左下角定位
  - 调整文字容器位置为left: 8%, bottom: 12%
  - 保持文字左对齐

- [ ] 2.2 优化对角线背景切割效果
  - 调整切割角度为20度
  - 验证切割线上方70%为极致深黑色
  - 验证切割线下方30%为极暗深灰色
  - 确保切割线锋利无模糊

- [ ] 2.3 完善底部装饰文字
  - 添加「QUANTUM ACCESS DECK」装饰文字
  - 设置字号为11px
  - 设置大写字母和0.25em字间距
  - 设置颜色为rgba(255, 255, 255, 0.4)

## 第三阶段：右侧表单区域优化

- [ ] 3.1 优化输入框样式
  - 确认移除四周边框，仅保留底部1像素实线
  - 调整圆角值为2像素
  - 验证边框颜色为rgba(15, 18, 23, 0.12)
  - 验证焦点状态边框颜色变为品牌橙色

- [ ] 3.2 优化按钮样式
  - 确认圆角值为2像素
  - 验证背景色为#0b0d12
  - 验证阴影值为0 8px 24px rgba(11, 13, 18, 0.25)
  - 验证悬停和点击状态的样式变化

- [ ] 3.3 优化忘记密码链接交互
  - 将默认文字颜色改为#8a8f9f
  - 实现悬停时变为品牌橙色
  - 添加浅橙色背景rgba(255, 122, 24, 0.08)
  - 验证过渡动画时间为200ms

- [ ] 3.4 优化Tab切换样式
  - 调整激活状态的背景色和文字颜色
  - 验证圆角值为2px
  - 优化悬停状态的视觉反馈

## 第四阶段：响应式适配完善

- [ ] 4.1 完善移动端适配
  - 调整左侧高度为220px
  - 调整小人尺寸为原来的60%
  - 调整文字区域位置
  - 移除表单面板圆角或减小至2px

- [ ] 4.2 完善平板端适配
  - 调整左侧宽度为35%
  - 调整表单区内边距
  - 验证双栏比例协调

- [ ] 4.3 验证桌面端适配
  - 确认左侧宽度为42%
  - 确认表单面板最大宽度为520px
  - 验证圆角保持设计值

## 第五阶段：可访问性增强

- [ ] 5.1 优化键盘导航
  - 验证Tab键可依次聚焦所有交互元素
  - 验证Enter键可提交表单
  - 验证Space键可切换复选框状态
  - 优化焦点轮廓样式

- [ ] 5.2 优化屏幕阅读器支持
  - 验证拟人化小人添加aria-hidden属性
  - 验证表单标签正确关联
  - 验证动态文案区域添加aria-live属性

- [ ] 5.3 添加高对比度模式支持
  - 实现prefers-contrast: high媒体查询样式
  - 验证高对比度模式下焦点状态清晰可见
  - 验证表单元素在系统中清晰可辨

## 第六阶段：性能优化与测试

- [ ] 6.1 动画性能优化
  - 为SVG元素添加will-change提示
  - 验证所有transform和opacity动画使用GPU加速
  - 验证视差动画使用requestAnimationFrame

- [ ] 6.2 浏览器兼容性测试
  - 测试Chrome最新版本
  - 测试Firefox最新版本
  - 测试Safari最新版本
  - 测试Edge最新版本

- [ ] 6.3 移动端浏览器测试
  - 测试iOS Safari
  - 测试Chrome for Android
  - 验证触摸交互正常

- [ ] 6.4 视觉回归测试
  - 对比设计稿检查视觉还原度
  - 检查所有动画效果是否符合预期
  - 检查响应式断点切换是否平滑

## 任务执行说明

### 任务1.1 眼睛视差跟随实现细节

在LoginView.vue的script部分添加鼠标移动事件监听：

```typescript
const mousePosition = reactive({ x: 0, y: 0 })
const eyeOffset = reactive({ leftX: 0, leftY: 0, rightX: 0, rightY: 0 })

const MAX_OFFSET = 2
const EYE_LEFT_BASE = { x: 43, y: 32 }
const EYE_RIGHT_BASE = { x: 57, y: 32 }

function updateEyeParallax() {
  const viewportCenter = {
    x: window.innerWidth / 2,
    y: window.innerHeight / 2
  }
  
  const deltaX = (mousePosition.x - viewportCenter.x) / viewportCenter.x
  const deltaY = (mousePosition.y - viewportCenter.y) / viewportCenter.y
  
  eyeOffset.leftX = EYE_LEFT_BASE.x + deltaX * MAX_OFFSET
  eyeOffset.leftY = EYE_LEFT_BASE.y + deltaY * MAX_OFFSET * 0.5
  eyeOffset.rightX = EYE_RIGHT_BASE.x + deltaX * MAX_OFFSET
  eyeOffset.rightY = EYE_RIGHT_BASE.y + deltaY * MAX_OFFSET * 0.5
}

function onMouseMove(event: MouseEvent) {
  mousePosition.x = event.clientX
  mousePosition.y = event.clientY
  requestAnimationFrame(updateEyeParallax)
}
```

### 任务1.2 机械手动画实现细节

在CSS中添加手臂动画样式：

```css
.hand-left,
.hand-right {
  transition: transform 0.2s ease-out;
  transform-origin: center;
}

.hand-left.raised {
  transform: translateY(-20px) translateX(10px);
}

.hand-right.raised {
  transform: translateY(-20px) translateX(-10px);
}
```

### 任务1.3 眯眼效果实现细节

在CSS中添加眯眼效果样式：

```css
.character-eyes.squinting {
  transform: scaleY(0.6);
}

@keyframes squintRecovery {
  0% { transform: scaleY(0.6); }
  50% { transform: scaleY(0.8); }
  100% { transform: scaleY(1); }
}

.character-eyes.recovering {
  animation: squintRecovery 0.2s ease-out forwards;
}
```

### 任务3.3 忘记密码链接样式调整

修改现有.link样式：

```css
.link {
  color: #8a8f9f;
  background-color: transparent;
  transition: color 0.2s ease, background-color 0.2s ease;
}

.link:hover {
  color: #ff7a18;
  background-color: rgba(255, 122, 24, 0.08);
}
```

### 任务2.1 左侧文字位置调整

在showcase-content中添加文字块：

```html
<div class="hero-text-block">
  <h1 class="hero-text__title">氛围亮度自适应</h1>
  <p class="hero-text__subtitle">让每一次输入都保持清晰与质感</p>
  <p class="hero-text__accent">QUANTUM ACCESS DECK</p>
</div>
```

添加对应CSS样式：

```css
.hero-text-block {
  position: absolute;
  left: 8%;
  bottom: 12%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hero-text__title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
}

.hero-text__subtitle {
  font-size: 16px;
  font-weight: 300;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.hero-text__accent {
  font-size: 11px;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 16px;
}
```