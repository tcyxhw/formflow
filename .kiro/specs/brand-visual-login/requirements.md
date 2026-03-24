# Requirements Document

## Introduction

This document defines the requirements for redesigning the login and registration pages with a professional brand visual design. The new design replaces the existing anthropomorphic mascot with a sophisticated SaaS-style visual experience that emphasizes brand presence and professional appeal. The design follows a split-layout pattern with a deep, tech-focused left side and a clean, minimal right side for the form.

## Glossary

- **Brand_Visual_Panel**: The left-side visual area containing background gradients, floating cards, and product mockup
- **Form_Panel**: The right-side authentication form area
- **Floating_Card**: Small glass-morphism cards that float around the main product mockup
- **Product_Mockup**: A simulated system interface displayed on the left panel
- **Light_Spot**: Soft gradient orbs used for background atmosphere
- **Parallax_Effect**: Subtle mouse-following movement for depth perception

## Requirements

### Requirement 1

**User Story:** As a user, I want to see a professional and trustworthy login page, so that I feel confident entering my credentials.

#### Acceptance Criteria

1. THE Page SHALL use a split layout with left side at 55% width and right side at 45% width
2. THE Left side SHALL have a dark, tech-focused design with deep blue/purple gradients
3. THE Right side SHALL have a light, clean design with white background
4. THE Two sides SHALL create strong visual contrast for clear separation of purposes
5. THE Design SHALL convey professionalism and trustworthiness

### Requirement 2

**User Story:** As a user, I want an immersive left-side brand experience, so that the login page feels like a complete product showcase.

#### Acceptance Criteria

1. THE Left side background SHALL use gradient: `#0B1020 -> #111A35 -> #1A2450`
2. THE Background SHALL include two soft light spots:
   - Blue spot: `#3B82F6` at top-left area
   - Purple spot: `#8B5CF6` at bottom-center area
3. THE Background SHALL overlay subtle textures (grid lines, circles, geometric shapes) at low opacity
4. THE Light spots SHALL slowly drift with 8-12 second cycle period
5. THE Background textures SHALL only provide texture, not dominate the visual

### Requirement 3

**User Story:** As a user, I want to see a product mockup on the left side, so that I understand the product's value proposition.

#### Acceptance Criteria

1. THE Left side SHALL display a floating product interface mockup in the center
2. THE Mockup SHALL be styled as:
   - Border radius: 20px
   - Semi-transparent dark card
   - Glass-morphism effect
   - Subtle border: `rgba(255,255,255,0.08)`
   - Soft, large shadow
3. THE Mockup content SHALL include:
   - Top navigation bar
   - Left sidebar menu
   - 2-3 data modules in center
   - A line chart or bar chart
   - A status panel
4. THE Mockup content SHALL use placeholder data, not real functionality
5. THE Mockup SHALL have a gentle floating animation (8px up/down, 6s cycle)

### Requirement 4

**User Story:** As a user, I want to see floating information cards around the mockup, so that the left side feels layered and dynamic.

#### Acceptance Criteria

1. THE Left side SHALL have 3 floating glass-morphism cards
2. THE Card 1 (Smart Analysis):
   - Icon: Lightning/AI spark
   - Title: "智能分析"
   - Subtitle: "自动提取关键数据"
3. THE Card 2 (Real-time Sync):
   - Icon: Refresh/Cloud sync
   - Title: "实时同步"
   - Subtitle: "跨端数据即时更新"
4. THE Card 3 (Team Collaboration):
   - Icon: User group
   - Title: "团队协作"
   - Subtitle: "高效共享与管理"
5. THE Cards SHALL be positioned at:
   - Card 1: Top-left of mockup
   - Card 2: Right side of mockup
   - Card 3: Bottom-left of mockup
6. THE Cards SHALL have:
   - Semi-transparent glass effect
   - Small border radius
   - Subtle glowing edge
7. THE Cards SHALL float at different speeds (6-10px displacement) for layered effect

### Requirement 5

**User Story:** As a user, I want to see brand messaging on the left side, so that I understand the product's value.

#### Acceptance Criteria

1. THE Left side SHALL display brand messaging at bottom-left or bottom-center area
2. THE Login page main title SHALL be: "欢迎回来，继续你的高效工作流"
3. THE Login page subtitle SHALL be: "统一管理数据、任务与协作流程，让每一步都更流畅。"
4. THE Registration page main title SHALL be: "开启你的高效协作体验"
5. THE Registration page subtitle SHALL be: "从注册开始，快速连接团队、任务与业务数据"
6. THE Messaging SHALL include 3 feature highlights:
   - 智能处理任务
   - 实时同步数据
   - 多端无缝协作
7. THE Title SHALL be 1-2 lines maximum
8. THE Subtitle SHALL be 1-2 lines maximum
9. THE Feature highlights SHALL be limited to 3 items maximum

### Requirement 6

**User Story:** As a user, I want smooth animations that feel premium, so that the page feels polished and modern.

#### Acceptance Criteria

1. THE Background light spots SHALL drift slowly (8-12s cycle, small displacement)
2. THE Product mockup SHALL float gently (8px up/down, 6s cycle, no rotation)
3. THE Floating cards SHALL move at different speeds (6-10px displacement) creating depth
4. THE Mouse parallax effect SHALL be subtle (small offset on mouse move)
5. THE Animations SHALL feel premium, not flashy or distracting
6. THE Parallax effect SHALL only add "feeling", not 3D炫耀

### Requirement 7

**User Story:** As a user, I want a clean and focused form area on the right side, so that I can easily complete authentication.

#### Acceptance Criteria

1. THE Right side SHALL have white or very light gray background (`#FFFFFF`)
2. THE Form container SHALL be centered with width 380px-420px
3. THE Form SHALL include:
   - Logo
   - Title: "登录账号"
   - Subtitle: "欢迎回来，请输入你的账户信息"
   - Account input field
   - Password input field
   - Primary login button
   - Secondary links: Register, Forgot password
4. THE Input fields SHALL have:
   - Large size
   - Border radius: 12px
   - Border color: `#D1D5DB`
5. THE Primary button SHALL use brand color
6. THE Form SHALL have adequate whitespace and padding
7. THE Right side SHALL remain clean and focused on conversion

### Requirement 8

**User Story:** As a developer, I want a consistent color palette that is reliable and professional.

#### Acceptance Criteria

1. THE Left side colors SHALL use:
   - Background dark: `#0B1020`
   - Deep blue: `#16213E`
   - Highlight blue: `#3B82F6`
   - Highlight purple: `#8B5CF6`
   - Primary text: `#F8FAFC`
   - Secondary text: `rgba(248,250,252,0.72)`
2. THE Right side colors SHALL use:
   - Background: `#FFFFFF`
   - Divider: `#E5E7EB`
   - Input border: `#D1D5DB`
   - Text: `#111827`
3. THE Color palette SHALL be consistent and professional
4. THE Colors SHALL not clash or appear unprofessional

### Requirement 9

**User Story:** As a user, I want the login and registration pages to share the same left-side design with different text, so that the experience is consistent.

#### Acceptance Criteria

1. THE Login and registration pages SHALL share the same left-side visual structure
2. THE Left side content SHALL remain mostly unchanged between pages
3. ONLY the brand messaging text SHALL change between pages
4. THE Transition between login and registration SHALL be smooth
5. THE User experience SHALL be consistent across both pages

### Requirement 10

**User Story:** As a developer, I want the implementation to be maintainable and follow project conventions.

#### Acceptance Criteria

1. THE New design SHALL replace the existing anthropomorphic mascot completely
2. THE InteractiveMiku component SHALL be removed from the login page
3. THE New components SHALL follow Vue3 composition API pattern
4. THE Styles SHALL use scoped CSS or CSS modules
5. THE Design SHALL be responsive for mobile devices
6. THE Implementation SHALL not break existing authentication functionality