# Design Document: Interactive Miku Login Character

## Overview

This design document provides the technical implementation details for the interactive Miku character feature on the FormFlow login and registration pages. The character is a multi-layered animated component that responds to user interactions through mouse tracking, focus states, and CSS-driven animations. The implementation focuses on performance optimization through GPU-accelerated CSS transitions and minimal JavaScript event handling.

The character consists of three z-index layers containing body images, pupils, and hands. Each layer can be independently animated to create expressions and reactions. The design prioritizes smooth 60fps animations by limiting layout thrashing and using transform/opacity changes exclusively. The state machine approach ensures predictable behavior across all interaction scenarios while maintaining separation between visual presentation and interaction logic.

## Architecture

### System Architecture

The interactive character follows a layered architecture with clear separation between state management, event handling, and visual rendering. The Vue3 component serves as the container and orchestrates the interaction between the DOM elements and the state machine. CSS handles all visual transitions and animations through hardware-accelerated properties. JavaScript manages the state machine transitions and pupil tracking calculations.

The architecture supports both the core interaction requirements and the optional bonus features through a modular design. Each character component (body, pupils, hands) is independently controllable while sharing a common state context. This allows for flexible expression combinations without code duplication. The design also anticipates potential future extensions such as additional expressions or interactive elements.

### Component Structure

```
InteractiveMiku.vue (Container Component)
├── CharacterContainer (Wrapper with breathing animation)
│   ├── Layer1-Body (Z-index: 1)
│   │   ├── body-open.png (Visible in idle/account focus)
│   │   └── body-closed.png (Visible in password focus)
│   ├── Layer2-Pupils (Z-index: 2)
│   │   ├── left-pupil.png
│   │   └── right-pupil.png
│   └── Layer3-Hands (Z-index: 3)
│       ├── left-hand.png
│       └── right-hand.png (Mirror of left)
└── StateManager (JavaScript module)
    ├── State Machine
    ├── Mouse Tracker
    └── Event Handlers
```

The component structure uses absolute positioning within a relative container to enable precise layer stacking. Each layer contains its respective images with independent transform and opacity controls. The state manager module is separated from the Vue component to enable potential reuse across multiple pages or components.

### Data Flow

```
User Input Events
       │
       ▼
┌──────────────────┐
│ Event Listeners  │ ←─ mousemove, focus, blur, input, click
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ State Machine    │ ←─ CurrentState: idle | account-focus | password-focus
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ State Transition │ ←─ Determine target state based on events
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ CSS Class Update │ ←─ Apply .is-hiding, .has-focus classes
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ CSS Transitions  │ ←─ GPU-accelerated transform/opacity changes
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Visual Update    │ ←─ Character renders new state
└──────────────────┘
```

The data flow follows a unidirectional pattern from user input through state management to visual updates. Event listeners capture user interactions and pass them to the state machine for processing. The state machine determines the appropriate target state and triggers CSS class updates. CSS transitions handle the visual interpolation between states automatically.

### State Machine

The character operates with three primary states and optional sub-states for bonus features. Each state defines the visible elements and their target positions. Transitions between states are triggered by specific events and use CSS transitions for smooth visual changes.

```
┌─────────────────────────────────────────────────────────────┐
│                    STATE MACHINE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐                                           │
│   │    IDLE     │ ←────────────────────────────────────┐    │
│   │             │                                     │    │
│   │ Body: open  │                                     │    │
│   │ Pupils:     │                                     │    │
│   │   tracking  │                                     │    │
│   │ Hands: down │                                     │    │
│   └──────┬──────┘                                     │    │
│          │ focus                                      │    │
│          ▼                                            │    │
│   ┌─────────────┐                              blur  │    │
│   │ ACCOUNT-    │ ←───────────────────────────────────┘    │
│   │   FOCUS     │                                          │
│   │             │                                          │
│   │ Body: open  │                                          │
│   │ Pupils:     │                                          │
│   │   biased    │                                          │
│   │ Hands: down │                                          │
│   └──────┬──────┘                                          │
│          │ password focus                                  │
│          ▼                                                  │
│   ┌─────────────┐ ←───────────────────────────────┐        │
│   │ PASSWORD-   │                                │        │
│   │   FOCUS     │                                │        │
│   │             │                                │        │
│   │ Body: closed│                                │        │
│   │ Pupils:     │                                │        │
│   │   hidden    │                                │        │
│   │ Hands: up   │                                │        │
│   └───��─────────┘                                │        │
│          │ blur                                  │        │
│          └───────────────────────────────────────┘        │
│                                                             │
│   BONUS SUB-STATES (Optional):                             │
│   ┌─────────────┐  typing    ┌─────────────┐               │
│   │   IDLE      │ ─────────► │   TYPING    │               │
│   │             │            │             │               │
│   │ Hands: down │            │ Hands: move │               │
│   └─────────────┘            └─────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The state machine ensures predictable behavior by defining clear transition conditions. Each state has specific visual configurations that are applied through CSS classes. The optional bonus states are independent of the core state machine and can be enabled or disabled via configuration.

## Components and Interfaces

### Vue Component Interface

```typescript
// InteractiveMiku.vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  /**
   * Enable bonus interactions (typing hand movement, password toggle reaction)
   */
  enableBonusInteractions?: boolean
  /**
   * Custom eye socket boundary radius in pixels
   */
  eyeSocketRadius?: number
  /**
   * Custom pupil tracking speed multiplier (0.1 - 2.0)
   */
  trackingSpeed?: number
}

const props = withDefaults(defineProps<Props>(), {
  enableBonusInteractions: false,
  eyeSocketRadius: 8,
  trackingSpeed: 1.0
})

// Emits for parent component communication
const emit = defineEmits<{
  (e: 'state-change', state: 'idle' | 'account-focus' | 'password-focus'): void
  (e: 'pupil-move', position: { x: number; y: number }): void
}>()

// Refs for DOM element access
const characterContainer = ref<HTMLElement | null>(null)
const leftPupil = ref<HTMLElement | null>(null)
const rightPupil = ref<HTMLElement | null>(null)
const leftHand = ref<HTMLElement | null>(null)
const rightHand = ref<HTMLElement | null>(null)

// State management
const currentState = ref<'idle' | 'account-focus' | 'password-focus'>('idle')
const isPasswordVisible = ref(false)
const lastTypingTime = ref(0)

// Event handlers
const handleMouseMove = (event: MouseEvent) => { /* ... */ }
const handleFocus = (event: FocusEvent) => { /* ... */ }
const handleBlur = (event: FocusEvent) => { /* ... */ }
const handleInput = (event: InputEvent) => { /* ... */ }
const handlePasswordToggle = () => { /* ... */ }

// Lifecycle
onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
  // Focus/blur listeners attached to form inputs
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>

<template>
  <div 
    ref="characterContainer"
    class="miku-character"
    :class="{
      'is-hiding': currentState === 'password-focus',
      'has-focus': currentState !== 'idle',
      'bonus-enabled': enableBonusInteractions
    }"
  >
    <div class="miku-layer layer-body">
      <img src="/login/body-open.png" class="body-open" alt="Miku body with open eyes" />
      <img src="/login/body-closed.png" class="body-closed" alt="Miku body with closed eyes" />
    </div>
    
    <div class="miku-layer layer-pupils">
      <img ref="leftPupil" src="/login/pupil.png" class="pupil left" alt="Left pupil" />
      <img ref="rightPupil" src="/login/pupil.png" class="pupil right" alt="Right pupil" />
    </div>
    
    <div class="miku-layer layer-hands">
      <img ref="leftHand" src="/login/hand.png" class="hand left" alt="Left hand" />
      <img ref="rightHand" src="/login/hand.png" class="hand right" alt="Right hand" />
    </div>
  </div>
</template>
```

The Vue component provides a clean interface for integrating the interactive character into the login page. Props allow customization of behavior while maintaining sensible defaults. Emits enable parent components to track character state for analytics or coordinated animations. The template structure mirrors the z-index layering requirements.

### State Manager Module

```typescript
// stateManager.ts
type CharacterState = 'idle' | 'account-focus' | 'password-focus'

interface StateContext {
  currentState: CharacterState
  previousState: CharacterState | null
  isTyping: boolean
  lastInteractionTime: number
}

class StateManager {
  private context: StateContext = {
    currentState: 'idle',
    previousState: null,
    isTyping: false,
    lastInteractionTime: 0
  }
  
  private listeners: Set<(state: CharacterState) => void> = new Set()
  
  /**
   * Transition to a new state if the transition is valid
   */
  transition(newState: CharacterState): void {
    const validTransitions: Record<CharacterState, CharacterState[]> = {
      'idle': ['account-focus', 'password-focus'],
      'account-focus': ['idle', 'password-focus'],
      'password-focus': ['idle', 'account-focus']
    }
    
    if (validTransitions[this.context.currentState]?.includes(newState)) {
      this.context.previousState = this.context.currentState
      this.context.currentState = newState
      this.notifyListeners()
    }
  }
  
  /**
   * Get current state
   */
  getState(): CharacterState {
    return this.context.currentState
  }
  
  /**
   * Subscribe to state changes
   */
  subscribe(listener: (state: CharacterState) => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }
  
  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.context.currentState))
  }
  
  /**
   * Mark typing activity (for bonus features)
   */
  markTyping(): void {
    this.context.isTyping = true
    this.context.lastInteractionTime = Date.now()
    // Auto-clear typing flag after 500ms of no input
    setTimeout(() => {
      this.context.isTyping = false
    }, 500)
  }
}

export const stateManager = new StateManager()
export type { CharacterState, StateContext }
```

The state manager provides a centralized, testable module for character state management. The observer pattern allows multiple components to react to state changes without tight coupling. The transition validation ensures the character only moves through valid state paths.

## Data Models

### Character Configuration

```typescript
interface CharacterConfig {
  /**
   * Asset paths relative to public directory
   */
  assets: {
    bodyOpen: string
    bodyClosed: string
    pupil: string
    hand: string
  }
  /**
   * Animation timing configuration
   */
  timing: {
    bodyTransition: string      // '0.2s ease-in-out'
    pupilTransition: string     // '0.1s ease-out'
    handTransition: string      // '0.4s cubic-bezier(0.4, 0, 0.2, 1)'
    breathingDuration: string   // '3s ease-in-out infinite'
    breathingDistance: number   // 5 (pixels)
  }
  /**
   * Eye socket boundaries for pupil tracking
   */
  eyeSocket: {
    left: { x: number; y: number; radius: number }
    right: { x: number; y: number; radius: number }
  }
  /**
   * Hand position offsets
   */
  handPositions: {
    hidden: { x: number; y: number }
    visible: { x: number; y: number }
  }
  /**
   * Gaze bias direction for account focus (0-1, where 0=left, 0.5=center, 1=right)
   */
  accountGazeBias: number
}

const defaultConfig: CharacterConfig = {
  assets: {
    bodyOpen: '/login/body-open.png',
    bodyClosed: '/login/body-closed.png',
    pupil: '/login/pupil.png',
    hand: '/login/hand.png'
  },
  timing: {
    bodyTransition: '0.2s ease-in-out',
    pupilTransition: '0.1s ease-out',
    handTransition: '0.4s cubic-bezier(0.4, 0, 0.2, 1)',
    breathingDuration: '3s ease-in-out infinite',
    breathingDistance: 5
  },
  eyeSocket: {
    left: { x: 0, y: 0, radius: 8 },
    right: { x: 0, y: 0, radius: 8 }
  },
  handPositions: {
    hidden: { x: 0, y: 50 },
    visible: { x: 0, y: 0 }
  },
  accountGazeBias: 0.7 // Slightly right-biased toward input form
}
```

The configuration model allows for easy customization of timing, positions, and assets without modifying core logic. Default values match the requirements specification while enabling future theming or animation adjustments.

### Pupil Position

```typescript
interface PupilPosition {
  x: number // Offset from center in pixels
  y: number // Offset from center in pixels
}

interface TrackedPosition {
  raw: PupilPosition      // Raw mouse position
  constrained: PupilPosition // Position after boundary constraint
  biased: PupilPosition   // Position with gaze bias applied
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Pupil Boundary Constraint

*For any* mouse position within the viewport, the constrained pupil position SHALL always be within the defined eye socket radius of the center point.

**Validates: Requirements 4.2, 4.3**

### Property 2: State Transition Completeness

*For any* focus or blur event on form inputs, the character SHALL transition to a valid state within 100 milliseconds and remain in that state until another valid transition occurs.

**Validates: Requirements 3.5, 5.2, 7.5**

### Property 3: Hand Position Determinism

*For any* password focus event, the hands SHALL move from their hidden position (translateY=50px) to their visible position (translateY=0px) using the specified cubic-bezier transition, and the reverse SHALL occur on password blur.

**Validates: Requirements 6.4, 6.5, 6.6, 7.3, 7.4**

### Property 4: Eye State Consistency

*For any* password focus event, the body-closed.png SHALL have opacity 1 and body-open.png SHALL have opacity 0. Conversely, when password loses focus, body-open.png SHALL have opacity 1 and body-closed.png SHALL have opacity 0.

**Validates: Requirements 6.1, 6.2, 7.1**

### Property 5: Pupil Visibility Toggle

*For any* password focus event, the pupil elements SHALL have opacity 0. When password loses focus, the pupil elements SHALL have opacity 1.

**Validates: Requirements 6.3, 7.2**

### Property 6: Breathing Animation Continuity

*For any* state transition, the breathing animation SHALL continue uninterrupted with consistent 3-second cycle duration and 5-pixel amplitude.

**Validates: Requirements 1.4, 1.5**

### Property 7: Mouse Tracking Continuity

*For any* mouse movement event, the pupil position SHALL update within 50 milliseconds and the transition duration SHALL be 0.1 seconds or less.

**Validates: Requirements 4.4, 4.5**

### Property 8: Transition Timing Consistency

*For any* state transition involving body, pupils, or hands, the transition durations SHALL match the specified values (body: 0.2s, pupils: 0.1s, hands: 0.4s).

**Validates: Requirements 8.2, 8.3, 8.4**

## Error Handling

### Error Scenarios and Responses

The character implementation handles several error scenarios gracefully to ensure a consistent user experience. Missing or failed image loads result in graceful degradation where the character appears without the missing layer but continues functioning. JavaScript errors in event handlers are caught and logged without breaking the login form functionality. The state machine includes safeguards against invalid transitions that could cause unexpected visual states.

```typescript
// Error boundary wrapper
const withErrorHandler = <T extends (...args: any[]) => any>(
  handler: T,
  fallback: ReturnType<T>
): T => {
  return ((...args: Parameters<T>) => {
    try {
      return handler(...args)
    } catch (error) {
      console.error('[MikuCharacter] Error in event handler:', error)
      return fallback(...args)
    }
  }) as T
}

// Image load error handling
const handleImageError = (event: Event, layer: string) => {
  const img = event.target as HTMLImageElement
  console.warn(`[MikuCharacter] Failed to load ${layer} image`)
  img.style.display = 'none'
}
```

### Fallback States

If the state machine encounters an invalid transition or the configuration is malformed, the character defaults to the idle state with basic mouse tracking. This ensures the login form remains functional even if the character encounters errors. The breathing animation continues regardless of other component states to maintain visual appeal.

## Testing Strategy

### Dual Testing Approach

The interactive character requires both unit tests for specific behaviors and property-based tests for universal correctness guarantees. Unit tests verify concrete examples and edge cases such as boundary conditions and error handling. Property tests validate that the character behaves correctly across all possible inputs and states.

### Unit Testing Focus Areas

Unit tests should cover the state machine transition logic with all valid and invalid transition paths. Image loading and error handling paths require verification. The pupil tracking algorithm needs tests for positions at and beyond boundary limits. Event handler debouncing and rate limiting should be verified.

### Property-Based Testing Configuration

Property tests use a JavaScript property testing library such as fast-check. Each property test runs with a minimum of 100 iterations with varied input generation. Tests are tagged with the feature name and property number for traceability.

```typescript
// Example property test structure
import { fc, test } from '@fast-check/jest'

test('Property 1: Pupil Boundary Constraint', async () => {
  await fc.assert(
    fc.property(
      fc.nat(), // mouseX
      fc.nat(), // mouseY
      (mouseX, mouseY) => {
        const constrained = constrainPupilPosition(mouseX, mouseY, 8)
        return Math.abs(constrained.x) <= 8 && Math.abs(constrained.y) <= 8
      }
    ),
    { verbose: true }
  )
})
```

### Test Tag Format

All tests include a comment tag following this format:

```javascript
// Feature: interactive-miku-login, Property 1: Pupil Boundary Constraint
```

This enables test discovery and filtering during development and CI/CD processes.

## Implementation Details

### HTML Structure

```html
<!-- Character Container -->
<div class="miku-character" id="mikuCharacter">
  
  <!-- Layer 1: Body (Z-index: 1) -->
  <div class="miku-layer layer-body">
    <img 
      src="/login/body-open.png" 
      class="body-image body-open" 
      alt="Miku with open eyes"
    />
    <img 
      src="/login/body-closed.png" 
      class="body-image body-closed" 
      alt="Miku with closed eyes"
    />
  </div>
  
  <!-- Layer 2: Pupils (Z-index: 2) -->
  <div class="miku-layer layer-pupils">
    <div class="eye-socket left">
      <img 
        src="/login/pupil.png" 
        class="pupil-image" 
        alt="Left pupil"
      />
    </div>
    <div class="eye-socket right">
      <img 
        src="/login/pupil.png" 
        class="pupil-image" 
        alt="Right pupil"
      />
    </div>
  </div>
  
  <!-- Layer 3: Hands (Z-index: 3) -->
  <div class="miku-layer layer-hands">
    <img 
      src="/login/hand.png" 
      class="hand-image hand-left" 
      alt="Left hand"
    />
    <img 
      src="/login/hand.png" 
      class="hand-image hand-right" 
      alt="Right hand"
    />
  </div>
  
</div>
```

The HTML structure uses semantic class names that clearly indicate layer purpose and element type. Each layer is wrapped in a container div for independent positioning. Eye sockets provide visual boundaries for pupil movement.

### CSS Styling

```css
/* Character Container */
.miku-character {
  position: relative;
  width: 300px;
  height: 400px;
  /* Breathing animation */
  animation: breathe 3s ease-in-out infinite;
}

@keyframes breathe {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

/* Layer Base Styles */
.miku-layer {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

/* Layer 1: Body */
.layer-body {
  z-index: 1;
}

.body-image {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: opacity 0.2s ease-in-out;
}

.body-open {
  opacity: 1;
}

.body-closed {
  opacity: 0;
}

/* Password focus state */
.miku-character.is-hiding .body-open {
  opacity: 0;
}

.miku-character.is-hiding .body-closed {
  opacity: 1;
}

/* Layer 2: Pupils */
.layer-pupils {
  z-index: 2;
}

.eye-socket {
  position: absolute;
  /* Position eye sockets based on character design */
  top: 85px;
  width: 30px;
  height: 30px;
  overflow: hidden;
}

.eye-socket.left {
  left: 95px;
}

.eye-socket.right {
  right: 95px;
}

.pupil-image {
  position: absolute;
  width: 16px;
  height: 16px;
  /* Center pupil in socket */
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  transition: transform 0.1s ease-out, opacity 0.1s ease-out;
}

/* Hide pupils in password focus */
.miku-character.is-hiding .pupil-image {
  opacity: 0;
}

/* Layer 3: Hands */
.layer-hands {
  z-index: 3;
}

.hand-image {
  position: absolute;
  width: 80px;
  height: 80px;
  bottom: 50px;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.hand-left {
  left: 30px;
  transform: translateY(50px); /* Hidden by default */
}

.hand-right {
  right: 30px;
  transform: translateY(50px) scaleX(-1); /* Hidden + mirrored */
}

/* Password focus: hands rise */
.miku-character.is-hiding .hand-left {
  transform: translateY(0);
}

.miku-character.is-hiding .hand-right {
  transform: translateY(0) scaleX(-1);
}

/* Bonus: Typing animation */
.miku-character.bonus-enabled.is-typing .hand-left {
  animation: typingHand 0.3s ease-in-out;
}

@keyframes typingHand {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}
```

The CSS uses GPU-accelerated properties (transform, opacity) exclusively for smooth 60fps animations. Transition timing matches the requirements specification. The cubic-bezier curve creates a natural spring effect for hand movements.

### JavaScript Implementation

```typescript
// Mouse tracking and state management
class InteractiveMiku {
  private container: HTMLElement
  private leftPupil: HTMLElement
  private rightPupil: HTMLElement
  private leftHand: HTMLElement
  private rightHand: HTMLElement
  private stateManager: StateManager
  private eyeSocketRadius: number = 8
  private trackingSpeed: number = 1.0
  private accountGazeBias: number = 0.7
  
  constructor(containerId: string, config?: Partial<CharacterConfig>) {
    this.container = document.getElementById(containerId)
    if (!this.container) throw new Error('Character container not found')
    
    // Initialize element references
    this.leftPupil = this.container.querySelector('.pupil.left')
    this.rightPupil = this.container.querySelector('.pupil.right')
    this.leftHand = this.container.querySelector('.hand-left')
    this.rightHand = this.container.querySelector('.hand-right')
    
    // Apply configuration
    if (config?.eyeSocket?.left?.radius) {
      this.eyeSocketRadius = config.eyeSocket.left.radius
    }
    if (config?.trackingSpeed) {
      this.trackingSpeed = config.trackingSpeed
    }
    if (config?.accountGazeBias !== undefined) {
      this.accountGazeBias = config.accountGazeBias
    }
    
    this.stateManager = new StateManager()
    this.bindEvents()
  }
  
  /**
   * Bind all event listeners
   */
  private bindEvents(): void {
    document.addEventListener('mousemove', this.handleMouseMove.bind(this))
    
    // Focus/blur listeners for form inputs
    const accountInput = document.querySelector<HTMLInputElement>('#account')
    const passwordInput = document.querySelector<HTMLInputElement>('#password')
    
    accountInput?.addEventListener('focus', () => {
      this.stateManager.transition('account-focus')
    })
    
    passwordInput?.addEventListener('focus', () => {
      this.stateManager.transition('password-focus')
      this.container.classList.add('is-hiding')
    })
    
    passwordInput?.addEventListener('blur', () => {
      this.stateManager.transition('idle')
      this.container.classList.remove('is-hiding')
    })
    
    // Bonus: typing detection
    accountInput?.addEventListener('input', () => {
      this.stateManager.markTyping()
      this.container.classList.add('is-typing')
      setTimeout(() => {
        this.container.classList.remove('is-typing')
      }, 300)
    })
  }
  
  /**
   * Handle mouse movement for pupil tracking
   */
  private handleMouseMove(event: MouseEvent): void {
    const state = this.stateManager.getState()
    
    // Skip tracking in password focus state
    if (state === 'password-focus') return
    
    // Get eye socket positions relative to viewport
    const leftSocket = this.leftPupil.parentElement!.getBoundingClientRect()
    const rightSocket = this.rightPupil.parentElement!.getBoundingClientRect()
    
    // Calculate pupil positions
    const leftPosition = this.calculatePupilPosition(
      event.clientX, event.clientY,
      leftSocket.left + leftSocket.width / 2,
      leftSocket.top + leftSocket.height / 2,
      state === 'account-focus'
    )
    
    const rightPosition = this.calculatePupilPosition(
      event.clientX, event.clientY,
      rightSocket.left + rightSocket.width / 2,
      rightSocket.top + rightSocket.height / 2,
      state === 'account-focus'
    )
    
    // Apply positions
    this.updatePupilPosition(this.leftPupil, leftPosition)
    this.updatePupilPosition(this.rightPupil, rightPosition)
  }
  
  /**
   * Calculate constrained pupil position with optional gaze bias
   */
  private calculatePupilPosition(
    mouseX: number,
    mouseY: number,
    socketCenterX: number,
    socketCenterY: number,
    applyBias: boolean
  ): { x: number; y: number } {
    // Calculate raw offset from socket center
    let offsetX = (mouseX - socketCenterX) * 0.1 * this.trackingSpeed
    let offsetY = (mouseY - socketCenterY) * 0.1 * this.trackingSpeed
    
    // Apply gaze bias toward input form (right side)
    if (applyBias) {
      offsetX = offsetX * (1 - this.accountGazeBias) + 
                (this.accountGazeBias * 10) // Bias 10px right
    }
    
    // Constrain to eye socket radius
    const distance = Math.sqrt(offsetX * offsetX + offsetY * offsetY)
    if (distance > this.eyeSocketRadius) {
      const ratio = this.eyeSocketRadius / distance
      offsetX *= ratio
      offsetY *= ratio
    }
    
    return { x: offsetX, y: offsetY }
  }
  
  /**
   * Update pupil DOM position
   */
  private updatePupilPosition(
    pupil: HTMLElement,
    position: { x: number; y: number }
  ): void {
    pupil.style.transform = `translate(calc(-50% + ${position.x}px), calc(-50% + ${position.y}px))`
  }
}
```

The JavaScript implementation separates concerns into distinct methods for event handling, position calculation, and DOM updates. The pupil tracking algorithm uses vector mathematics to constrain movement within the circular eye socket boundary. The gaze bias feature shifts pupil position toward the input form during account focus.

### Integration

```typescript
// Initialize character on login page
document.addEventListener('DOMContentLoaded', () => {
  const character = new InteractiveMiku('mikuCharacter', {
    eyeSocket: { left: { radius: 8 }, right: { radius: 8 } },
    trackingSpeed: 1.0,
    accountGazeBias: 0.7
  })
  
  // Vue component integration
  // In a Vue component, use refs and lifecycle hooks instead
})
```

## Performance Considerations

### GPU Acceleration

All animations use CSS transform and opacity properties which are GPU-accelerated in modern browsers. This prevents layout thrashing and ensures smooth 60fps animations even on lower-powered devices. The breathing animation uses translateY which is also GPU-accelerated.

### Event Throttling

Mouse move events are not throttled because the CSS transition of 0.1s provides natural smoothing. The browser's compositor handles rapid updates efficiently. For older browsers, requestAnimationFrame could be added as a fallback.

### Memory Management

Event listeners are properly removed on component unmount to prevent memory leaks. Image elements are loaded once and reused. The state manager uses weak references where possible to allow garbage collection.