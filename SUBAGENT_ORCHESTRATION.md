# Subagent Orchestration Framework

This implementation provides a framework for delegating tasks from main agents to specialized subagents. The system allows for:

1. **Subagent Management**: Create, retrieve, update, and delete specialized subagents
2. **Task Delegation**: Assign tasks to appropriate subagents based on specialization
3. **Orchestration**: Coordinate between main agents and subagents
4. **Task Tracking**: Monitor the status of delegated tasks

## Core Components

### 1. Subagent Models
- `Subagent`: Represents a specialized subagent with name, specialization, and status
- `SubagentTask`: Represents the assignment of a task to a subagent

### 2. Subagent Service
- Create, retrieve, update, and delete subagents
- Assign tasks to subagents
- Manage subagent task assignments

### 3. Orchestration Service
- Delegate tasks to appropriate subagents based on specialization
- Track orchestration information for tasks

## API Endpoints

### Subagent Endpoints
- `POST /api/subagents` - Create a new subagent
- `GET /api/subagents` - List subagents (optionally filtered by specialization)
- `GET /api/subagents/{id}` - Get a specific subagent
- `PATCH /api/subagents/{id}` - Update a subagent
- `DELETE /api/subagents/{id}` - Delete a subagent
- `POST /api/subagents/{id}/tasks` - Assign a task to a subagent
- `GET /api/subagents/{id}/tasks` - Get all tasks assigned to a subagent
- `PATCH /api/subagent-tasks/{id}/status` - Update subagent task status

### Orchestration Endpoints
- `POST /api/orchestration/tasks/{task_id}/delegate` - Delegate a task to a subagent
- `GET /api/orchestration/tasks/{task_id}/info` - Get orchestration info for a task

## Database Schema

The implementation adds two new tables to the existing database:

1. **subagents**: Stores information about subagents
2. **subagent_tasks**: Tracks task assignments to subagents

## Usage Example

1. Create a subagent:
```http
POST /api/subagents
{
  "name": "Code Reviewer",
  "specialization": "code_review",
  "description": "Specialized in code review tasks"
}
```

2. Create a task:
```http
POST /api/tasks
{
  "title": "Code Review for Feature X",
  "description": "Review the implementation of feature X",
  "specialization": "code_review"
}
```

3. Delegate the task to the subagent:
```http
POST /api/orchestration/tasks/{task_id}/delegate?specialization=code_review
```

4. Check orchestration status:
```http
GET /api/orchestration/tasks/{task_id}/info
```