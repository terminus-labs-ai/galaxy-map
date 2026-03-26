# Component Architecture Plan for Galaxy Map Frontend

## Overview
This document outlines the proposed component architecture for the Galaxy Map frontend to improve separation of concerns, reusability, and maintainability.

## Component Structure

### 1. Core Components (src/components/core)
These are the fundamental building blocks that provide basic UI functionality.

#### 1.1 Layout Components
- `Header.jsx` - Main application header with logo, search, and controls
- `Board.jsx` - Main board container that organizes columns
- `Column.jsx` - Individual status column with tasks
- `TaskCard.jsx` - Individual task card display
- `TaskCountBar.jsx` - Task counter display for each status

#### 1.2 Form Components
- `InputField.jsx` - Generic input field with validation
- `SelectField.jsx` - Generic select field with options
- `TextAreaField.jsx` - Generic textarea field
- `Badge.jsx` - Status and specialization badges
- `Chip.jsx` - Interactive chips for blockers and tags

#### 1.3 Modal Components
- `Modal.jsx` - Base modal wrapper
- `CreateTaskModal.jsx` - Modal for creating new tasks
- `TaskDetailModal.jsx` - Modal for viewing and editing task details
- `SearchResultsModal.jsx` - Modal for search results
- `ProjectEditor.jsx` - Project selection and creation component

#### 1.4 Utility Components
- `StatusBadge.jsx` - Status badge display
- `SpecBadge.jsx` - Specialization badge display
- `BlockedIndicator.jsx` - Blocked task indicator
- `TimeAgo.jsx` - Relative time display component

### 2. Feature Components (src/components/features)
These components implement specific features of the application.

#### 2.1 Task Management
- `TaskList.jsx` - List of tasks with filtering and sorting
- `TaskFilterBar.jsx` - Filter controls for tasks
- `TaskHistoryTimeline.jsx` - Timeline view of task history

#### 2.2 Search and Navigation
- `SearchBar.jsx` - Main search input with dropdown results
- `ProjectFilter.jsx` - Project filtering dropdown
- `PriorityFilter.jsx` - Priority filtering controls

#### 2.3 Data Visualization
- `TaskStats.jsx` - Task statistics display
- `StatusDistributionChart.jsx` - Visual representation of tasks by status

### 3. Hooks (src/hooks)
- `useApi.jsx` - Generic API hook for making requests
- `useLocalStorage.jsx` - Local storage management hook
- `usePolling.jsx` - Polling hook for periodic updates
- `useTaskHistory.jsx` - Hook for fetching task history
- `useDragAndDrop.jsx` - Drag and drop functionality hook

### 4. Context (src/context)
- `TaskContext.jsx` - Global task state management
- `UIContext.jsx` - UI state management (modals, filters, etc.)

### 5. Utilities (src/utils)
- `api.js` - API client utility functions
- `format.js` - Formatting utilities (time, text, etc.)
- `validation.js` - Form validation utilities
- `constants.js` - Application constants

## Component Hierarchy

```
App.jsx
├── Header.jsx
│   ├── Logo.jsx
│   ├── SearchBar.jsx
│   ├── ProjectFilter.jsx
│   └── CreateTaskButton.jsx
├── TaskFilterBar.jsx
│   ├── PriorityFilter.jsx
│   └── SearchBar.jsx (reused)
├── Board.jsx
│   ├── Column.jsx
│   │   ├── TaskCard.jsx
│   │   └── TaskCountBar.jsx
│   └── DragOverlay.jsx
├── TaskCountBar.jsx
├── Modals
│   ├── CreateTaskModal.jsx
│   ├── TaskDetailModal.jsx
│   │   ├── TaskForm.jsx
│   │   ├── TaskHistoryTimeline.jsx
│   │   └── TaskActions.jsx
│   └── SearchResultsModal.jsx
└── Context Providers
    ├── TaskContext.jsx
    └── UIContext.jsx
```

## File Structure

```
src/
├── components/
│   ├── core/
│   │   ├── Header.jsx
│   │   ├── Board.jsx
│   │   ├── Column.jsx
│   │   ├── TaskCard.jsx
│   │   ├── TaskCountBar.jsx
│   │   ├── FormComponents/
│   │   │   ├── InputField.jsx
│   │   │   ├── SelectField.jsx
│   │   │   └── TextAreaField.jsx
│   │   ├── Badges/
│   │   │   ├── StatusBadge.jsx
│   │   │   └── SpecBadge.jsx
│   │   ├── Modals/
│   │   │   ├── Modal.jsx
│   │   │   ├── CreateTaskModal.jsx
│   │   │   ├── TaskDetailModal.jsx
│   │   │   └── SearchResultsModal.jsx
│   │   └── Utilities/
│   │       ├── BlockedIndicator.jsx
│   │       └── TimeAgo.jsx
│   ├── features/
│   │   ├── TaskManagement/
│   │   │   ├── TaskList.jsx
│   │   │   └── TaskFilterBar.jsx
│   │   ├── Search/
│   │   │   ├── SearchBar.jsx
│   │   │   └── SearchResultsModal.jsx
│   │   ├── DataVisualization/
│   │   │   ├── TaskStats.jsx
│   │   │   └── StatusDistributionChart.jsx
│   │   └── Project/
│   │       └── ProjectFilter.jsx
│   └── index.js (re-exports all components)
├── hooks/
│   ├── useApi.jsx
│   ├── useLocalStorage.jsx
│   ├── usePolling.jsx
│   ├── useTaskHistory.jsx
│   └── useDragAndDrop.jsx
├── context/
│   ├── TaskContext.jsx
│   └── UIContext.jsx
├── utils/
│   ├── api.js
│   ├── format.js
│   ├── validation.js
│   └── constants.js
├── App.jsx
└── main.jsx
```

## Separation of Concerns

### 1. Presentation Layer
- Pure UI components that handle rendering and user interaction
- Should be stateless where possible
- Should receive data and callbacks via props

### 2. Logic Layer
- Components that contain business logic
- Handle data processing and transformation
- Manage component-specific state

### 3. Data Layer
- Hooks for data fetching and state management
- Context providers for global state
- Utility functions for data manipulation

### 4. Container Layer
- Components that orchestrate other components
- Handle data flow between components
- Manage complex interactions

## Implementation Plan

1. **Phase 1**: Refactor existing components into new structure
2. **Phase 2**: Create new components as needed
3. **Phase 3**: Implement context providers
4. **Phase 4**: Update App.jsx to use new component structure
5. **Phase 5**: Testing and refinement

## Benefits

1. **Improved Maintainability**: Clear separation of concerns makes components easier to understand and modify
2. **Enhanced Reusability**: Components are designed to be reusable across different parts of the application
3. **Better Testing**: Smaller, focused components are easier to unit test
4. **Scalability**: The modular structure makes it easier to add new features
5. **Team Collaboration**: Clear component boundaries make it easier for multiple developers to work on different parts