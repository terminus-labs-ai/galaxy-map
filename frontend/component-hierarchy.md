# Component Hierarchy and File Structure

## Overview
This document defines the component hierarchy and file structure for the Galaxy Map frontend application.

## Component Hierarchy

### Root Component
```
App.jsx
├── Header
│   ├── Logo
│   ├── SearchBar
│   ├── ProjectFilter
│   └── CreateTaskButton
├── TaskFilterBar
│   ├── PriorityFilter
│   └── LocalSearchFilter
├── Board
│   ├── Column
│   │   ├── TaskCard
│   │   └── TaskCountBar
│   └── DragOverlay
├── TaskCountBar
├── Modals
│   ├── CreateTaskModal
│   ├── TaskDetailModal
│   └── SearchResultsModal
└── Context Providers
    ├── TaskContext
    └── UIContext
```

## File Structure

### src/components/core/
```
Header.jsx
Board.jsx
Column.jsx
TaskCard.jsx
TaskCountBar.jsx
FormComponents/
├── InputField.jsx
├── SelectField.jsx
└── TextAreaField.jsx
Badges/
├── StatusBadge.jsx
└── SpecBadge.jsx
Modals/
├── Modal.jsx
├── CreateTaskModal.jsx
├── TaskDetailModal.jsx
└── SearchResultsModal.jsx
Utilities/
├── BlockedIndicator.jsx
└── TimeAgo.jsx
```

### src/components/features/
```
TaskManagement/
├── TaskList.jsx
└── TaskFilterBar.jsx
Search/
├── SearchBar.jsx
└── SearchResultsModal.jsx
DataVisualization/
├── TaskStats.jsx
└── StatusDistributionChart.jsx
Project/
└── ProjectFilter.jsx
```

### src/hooks/
```
useApi.jsx
useLocalStorage.jsx
usePolling.jsx
useTaskHistory.jsx
useDragAndDrop.jsx
```

### src/context/
```
TaskContext.jsx
UIContext.jsx
```

### src/utils/
```
api.js
format.js
validation.js
constants.js
```

## Component Responsibilities

### Core Components
- **Header.jsx**: Main application header with navigation controls
- **Board.jsx**: Container for organizing columns and tasks
- **Column.jsx**: Individual status column displaying tasks
- **TaskCard.jsx**: Individual task card with key information
- **TaskCountBar.jsx**: Displays task counts per status
- **InputField.jsx**: Generic input field component
- **SelectField.jsx**: Generic select dropdown component
- **TextAreaField.jsx**: Generic textarea component
- **StatusBadge.jsx**: Displays status with appropriate styling
- **SpecBadge.jsx**: Displays specialization with color coding
- **Modal.jsx**: Base modal wrapper component
- **CreateTaskModal.jsx**: Modal for creating new tasks
- **TaskDetailModal.jsx**: Modal for viewing/editing task details
- **SearchResultsModal.jsx**: Modal for displaying search results
- **BlockedIndicator.jsx**: Shows blocked status indicator
- **TimeAgo.jsx**: Displays relative time

### Feature Components
- **TaskList.jsx**: Displays list of tasks with filtering
- **TaskFilterBar.jsx**: Filter controls for tasks
- **SearchBar.jsx**: Search input with results dropdown
- **ProjectFilter.jsx**: Project filtering dropdown
- **PriorityFilter.jsx**: Priority filtering controls
- **TaskStats.jsx**: Task statistics display
- **StatusDistributionChart.jsx**: Visual representation of task distribution

## Data Flow

1. **App.jsx** - Main container that orchestrates all components
2. **Context Providers** - Manage global state (tasks, UI state)
3. **Hooks** - Handle data fetching and side effects
4. **Components** - Handle presentation and user interaction
5. **Utilities** - Provide helper functions and constants

## Implementation Notes

- All components should be functional and use hooks
- Components should be self-contained with clear props
- State management should be centralized in context providers
- API calls should be handled through hooks
- Components should be designed for reusability
- All styling should be handled through CSS classes