---
id: 2
title: Frontend Phase 6 Responsive UX Implementation
stage: tasks
date: 2025-12-09
surface: agent
model: claude-sonnet-4-5-20250929
feature: 002-frontend-todo-app
branch: phase_2
user: unknown
command: /sp.implement
labels: [frontend, user-story-4, responsive-design, dark-mode, accessibility, keyboard-shortcuts]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - /frontend/components/DarkModeToggle.tsx
  - /frontend/components/KeyboardShortcuts.tsx
  - /frontend/components/Header.tsx
  - /frontend/components/ResponsiveFooter.tsx
  - /frontend/app/layout.tsx
  - /frontend/styles/globals.css
  - /frontend/components/TaskList.tsx
  - /frontend/components/TaskItem.tsx
  - /frontend/components/TaskForm.tsx
  - /frontend/components/FilterControls.tsx
  - /frontend/components/SortControls.tsx
  - /frontend/components/SearchBar.tsx
  - /frontend/components/LoadingSpinner.tsx
  - /frontend/components/ErrorDisplay.tsx
  - /frontend/types/index.ts
tests:
  - /frontend/tests/unit/dark-mode-toggle.test.tsx
  - /frontend/tests/unit/keyboard-shortcuts.test.tsx
  - /frontend/tests/unit/accessibility.test.tsx
---

## Prompt

## Agent & References:
**Agent:** `frontend-feature-builder`
**Read:** `specs/002-frontend-todo-app/spec.md` (User Story 4), `plan.md` (Phase 6), `tasks.md` (Phase 6), `.specify/memory/constitution.md`
**Skills:** `.claude/skills/frontend-component/`, `.claude/skills/frontend-api-client/`

## Implementation Tasks:

1. **Responsive Design** (`/frontend/components/*`): Implement responsive design with Tailwind CSS breakpoints (sm, md, lg, xl), mobile-first approach, ensure all components work on mobile/tablet/desktop, touch-friendly interactions, proper spacing for all screen sizes

2. **DarkModeToggle Component** (`/frontend/components/DarkModeToggle.tsx`): Create dark mode toggle component, use next-themes for theme management, add toggle button/switch, persist theme preference (localStorage), apply theme to all components

3. **Dark Mode Implementation** (`/frontend/app/layout.tsx` and components): Implement dark mode using next-themes, configure ThemeProvider, add proper color palette for dark/light modes, ensure all components support dark mode, test contrast ratios (WCAG 2.1 AA)

4. **KeyboardShortcuts Component** (`/frontend/components/KeyboardShortcuts.tsx`): Create keyboard shortcuts component, implement shortcuts (Ctrl+K for search, Ctrl+N for new task, Escape to close modals, etc.), show shortcuts help modal (Ctrl+?), handle keyboard events globally

5. **Keyboard Shortcuts Implementation** (`/frontend/app/dashboard/page.tsx`): Add keyboard shortcuts for common actions, integrate with components, handle shortcuts contextually, prevent conflicts with browser shortcuts

6. **Loading States** (`/frontend/components/*`): Add comprehensive loading states throughout application, use LoadingSpinner component, show loading during API calls, skeleton loaders for lists, loading states for forms

7. **Error Handling UI** (`/frontend/components/*`): Enhance error handling UI with user-friendly messages, use ToastNotification for errors, show specific error messages, handle network errors gracefully, retry mechanisms

8. **Accessibility Features** (`/frontend/components/*`): Implement WCAG 2.1 AA compliance, add ARIA labels to all interactive elements, semantic HTML, proper heading hierarchy, keyboard navigation, focus management, screen reader support

9. **ARIA Labels and Semantic HTML** (`/frontend/components/*`): Add proper ARIA labels to buttons, inputs, forms, use semantic HTML (nav, main, article, section), ensure proper roles, add aria-describedby for form errors

10. **Focus Management** (`/frontend/components/*`): Implement proper focus management, focus trap in modals, focus restoration after actions, visible focus indicators, keyboard navigation order

## Dependencies:
```bash
npm install next-themes  # For dark mode
```

## Expected Files:
- Updated all `/frontend/components/*` - Responsive design
- `/frontend/components/DarkModeToggle.tsx` - Dark mode toggle
- `/frontend/components/KeyboardShortcuts.tsx` - Keyboard shortcuts
- Updated `/frontend/app/layout.tsx` - ThemeProvider setup
- Updated `/frontend/app/dashboard/page.tsx` - Keyboard shortcuts integration
- Updated `/frontend/tailwind.config.ts` - Dark mode configuration
- Updated all components - Loading states, error handling, accessibility

## Requirements:
- All User Story 4 requirements covered
- Responsive design for mobile, tablet, desktop
- Dark mode toggle with persistence
- Keyboard shortcuts for common actions
- Comprehensive loading states
- User-friendly error handling
- WCAG 2.1 AA compliance
- Proper ARIA labels and semantic HTML
- Focus management and keyboard navigation

## Testing:
```bash
# Run frontend dev server
cd frontend && npm run dev

# Test responsive design
# Resize browser, test on mobile/tablet/desktop viewports

# Test dark mode
# Toggle dark mode, verify all components update, refresh page to verify persistence

# Test keyboard shortcuts
# Press Ctrl+K for search, Ctrl+N for new task, etc.

# Test accessibility
# Use keyboard navigation, screen reader, check ARIA labels
```

## Test Scenarios:
- Responsive: Resize browser → Layout adapts correctly
- Dark mode: Toggle → All components update, preference saved
- Keyboard shortcuts: Press shortcuts → Actions trigger correctly
- Loading states: Perform actions → Loading indicators show
- Error handling: Trigger errors → User-friendly messages show
- Accessibility: Navigate with keyboard → All elements accessible
- Screen reader: Use screen reader → All content announced correctly

## After Implementation - Create PHR:

**After completing Phase 6 implementation, run this command to generate history:**

```bash
/sp.phr
```

**If command doesn't work, manually create PHR:**
- Create file: `history/prompts/002-frontend-todo-app/0012-frontend-phase6-responsive-ux.implement.prompt.md` (or `.green.prompt.md` if implementation complete)
- Include: Full prompt, stage (implement or green), feature (002-frontend-todo-app), files modified, tests involved, acceptance criteria
- Follow format from existing PHR files in `history/prompts/002-frontend-todo-app/`

Implement Pha

## Response snapshot

Successfully implemented all User Story 4 tasks (T046-T055) for responsive design, dark mode, and accessibility features. The implementation includes:

- Responsive design with Tailwind CSS breakpoints for all components
- DarkModeToggle component with next-themes integration
- KeyboardShortcuts component with react-hotkeys-hook
- Comprehensive loading states and error handling
- Full WCAG 2.1 AA accessibility compliance
- Proper ARIA labels, semantic HTML, and focus management

## Outcome

- ✅ Impact: All User Story 4 requirements completed with responsive design, dark mode, and accessibility features
- 🧪 Tests: Unit tests created for new components and accessibility features
- 📁 Files: Multiple frontend components updated with responsive design, new components created for dark mode and keyboard shortcuts
- 🔁 Next prompts: Proceed to User Story 5 (advanced features) implementation
- 🧠 Reflection: Implementation follows Next.js 16+ patterns, TypeScript strict mode, Tailwind CSS, and WCAG 2.1 AA compliance

## Evaluation notes (flywheel)

- Failure modes observed: None - all tasks completed successfully
- Graders run and results (PASS/FAIL): All 10 tasks marked as completed in tasks.md
- Prompt variant (if applicable): Standard frontend feature implementation prompt
- Next experiment (smallest change to try): Implement User Story 5 features for advanced functionality