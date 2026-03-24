# Implementation Plan: Interactive Miku Login Character

## Overview

This implementation plan breaks down the interactive Miku character feature into discrete coding tasks. The character consists of three z-index layers (body, pupils, hands) with CSS-driven animations and JavaScript event handling. The implementation follows the state machine design with transitions between idle, account-focus, and password-focus states. Each task builds on previous steps and includes references to the requirements it satisfies.

## Tasks

- [x] 1. Set up project structure and create character component
  - Create InteractiveMiku.vue component file in components directory
  - Set up basic template structure with three z-index layers
  - Add placeholder image assets from my-app/public/login/ directory
  - Configure component props for customization options
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 2. Implement CSS styling and animations
  - [x] 2.1 Create base character container with breathing animation
    - Write CSS for .miku-character container with relative positioning
    - Implement @keyframes breathe animation (5px float, 3s cycle)
    - Add animation property to container
    - _Requirements: 1.4, 1.5_

  - [x] 2.2 Style layer positioning and z-index management
    - Write CSS for .miku-layer with absolute positioning
    - Set z-index values: body=1, pupils=2, hands=3
    - Configure layer containers to fill parent dimensions
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 2.3 Implement body layer transitions
    - Style body-open and body-closed images with opacity transitions
    - Set body transition duration to 0.2s ease-in-out
    - Configure default state (body-open opacity: 1, body-closed opacity: 0)
    - _Requirements: 3.1, 3.2, 6.1, 6.2, 8.2_

  - [x] 2.4 Implement pupil layer styling
    - Style eye-socket containers with overflow hidden
    - Position pupils within eye sockets
    - Set pupil transition duration to 0.1s ease-out
    - Configure default pupil opacity to 1
    - _Requirements: 3.3, 4.1, 4.5, 8.3_

  - [x] 2.5 Implement hand layer with cubic-bezier transitions
    - Style hand images with transform transitions
    - Set hand transition to 0.4s cubic-bezier(0.4, 0, 0.2, 1)
    - Configure hidden state (translateY 50px)
    - Configure visible state (translateY 0)
    - Mirror right hand with scaleX(-1)
    - _Requirements: 3.2, 6.4, 6.5, 6.6, 7.3, 7.4, 8.4_

  - [ ]* 2.6 Write property test for CSS transitions
    - **Property 8: Transition Timing Consistency**
    - **Validates: Requirements 8.2, 8.3, 8.4**

- [x] 3. Implement state management module
  - [x] 3.1 Create StateManager class
    - Implement state transitions with validation
    - Define valid transition paths between states
    - Add observer pattern for state change notifications
    - Add typing detection for bonus features
    - _Requirements: 3.4, 3.5, 5.2, 7.5_

  - [x] 3.2 Integrate state manager with Vue component
    - Initialize state manager in component setup
    - Subscribe to state changes
    - Apply CSS classes based on state (.is-hiding, .has-focus)
    - _Requirements: 3.4, 3.5, 6.7, 7.1, 7.2_

  - [ ]* 3.3 Write property test for state transitions
    - **Property 2: State Transition Completeness**
    - **Validates: Requirements 3.5, 5.2, 7.5**

- [ ] 4. Implement mouse tracking and pupil movement
  - [x] 4.1 Create mouse move event handler
    - Add document-level mousemove listener
    - Calculate mouse position relative to eye sockets
    - Skip tracking in password-focus state
    - _Requirements: 3.3, 4.1, 4.4, 4.6_

  - [x] 4.2 Implement pupil position calculation algorithm
    - Calculate offset from socket center
    - Apply tracking speed multiplier
    - Implement boundary constraint (max radius 8px)
    - Add gaze bias for account-focus state
    - _Requirements: 4.2, 4.3, 4.5, 5.1, 5.3, 5.4_

  - [x] 4.3 Apply calculated positions to DOM elements
    - Update left pupil transform
    - Update right pupil transform
    - Use translate(-50%, -50%) as base offset
    - _Requirements: 4.4, 4.5_

  - [ ]* 4.4 Write property test for pupil boundary constraint
    - **Property 1: Pupil Boundary Constraint**
    - **Validates: Requirements 4.2, 4.3**

  - [ ]* 4.5 Write unit tests for pupil tracking
    - Test positions at boundary limits
    - Test positions beyond boundary (should be clamped)
    - Test gaze bias calculation
    - _Requirements: 4.2, 4.3, 5.1, 5.3_

- [ ] 5. Implement focus and blur event handling
  - [x] 5.1 Add focus listeners to form inputs
    - Attach focus listener to account input
    - Attach focus listener to password input
    - Attach blur listener to password input
    - _Requirements: 3.1, 3.2, 5.1, 6.1, 7.1_

  - [x] 5.2 Implement state transitions on focus events
    - Transition to account-focus on account input focus
    - Transition to password-focus on password input focus
    - Add .is-hiding class on password focus
    - _Requirements: 5.1, 5.2, 6.1, 6.7_

  - [x] 5.3 Implement state restoration on blur events
    - Transition to idle on password blur
    - Remove .is-hiding class
    - Restore pupil visibility
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_

  - [ ]* 5.4 Write property test for eye state consistency
    - **Property 4: Eye State Consistency**
    - **Validates: Requirements 6.1, 6.2, 7.1**

  - [ ]* 5.5 Write property test for pupil visibility toggle
    - **Property 5: Pupil Visibility Toggle**
    - **Validates: Requirements 6.3, 7.2**

- [ ] 6. Implement hand movement animations
  - [x] 6.1 Verify hand CSS transitions
    - Confirm hidden state (translateY 50px) works
    - Confirm visible state (translateY 0) works
    - Verify cubic-bezier timing function
    - _Requirements: 6.4, 6.5, 6.6, 7.3, 7.4_

  - [ ]* 6.2 Write property test for hand position determinism
    - **Property 3: Hand Position Determinism**
    - **Validates: Requirements 6.4, 6.5, 6.6, 7.3, 7.4**

- [ ] 7. Implement bonus interactions (optional)
  - [x] 7.1 Add typing detection for hand movement
    - Add input event listener to account field
    - Mark typing activity in state manager
    - Add .is-typing class for animation trigger
    - _Requirements: 9.1_

  - [x] 7.2 Implement password visibility toggle reaction
    - Add click listener to password toggle button
    - Trigger partial hand drop on toggle
    - Add shy glance expression
    - _Requirements: 9.2_

  - [x] 7.3 Add bonus feature configuration
    - Add enableBonusInteractions prop
    - Wrap bonus code in conditional check
    - Ensure bonus features don't affect core functionality
    - _Requirements: 9.3, 9.4, 9.5_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Integrate with login page
  - [x] 9.1 Add InteractiveMiku component to login page
    - Import component in LoginView.vue
    - Place component in left side of split layout
    - Configure props for login page context
    - _Requirements: 1.1, 1.2_

  - [ ] 9.2 Add InteractiveMiku component to registration page
    - Import component in RegisterView.vue
    - Place component in left side of split layout
    - Configure props for registration page context
    - _Requirements: 1.1, 1.2_

  - [ ] 9.3 Style character container background
    - Add light blue gradient background
    - Ensure background complements character colors
    - Position character slightly below center line
    - _Requirements: 1.3_

- [ ] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- All CSS transitions use GPU-accelerated properties (transform, opacity)
- Mouse tracking is skipped in password-focus state for privacy
- State machine ensures predictable behavior across all interactions