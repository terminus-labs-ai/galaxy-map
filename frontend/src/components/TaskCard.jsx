import { useState, useEffect, useCallback } from "react";

export default function TaskCard({ task, allTasks, onOpenDetail, SpecBadge, BlockedIndicator, timeAgo, truncate }) {
  const descriptionPreview = task.description
    ? task.description.length > 100
      ? task.description.slice(0, 100).trimEnd() + "..."
      : task.description
    : "";

  return (
    <div
      className={`card ${task.is_blocked ? "card-blocked" : ""}`}
      title={descriptionPreview}
      onClick={() => onOpenDetail(task.id)}
    >
      <div className="card-header">
        <div className="card-title">{task.title}</div>
      </div>

      <div className="card-badges">
        <SpecBadge spec={task.specialization} />
        <BlockedIndicator task={task} allTasks={allTasks} />
        {task.project_id && (
          <span className="project-badge">{task.project_id}</span>
        )}
      </div>

      {task.description && (
        <p className="card-desc-preview">{truncate(task.description)}</p>
      )}

      <div className="card-meta">
        <div>Updated: {timeAgo(task.updated_at)}</div>
        <div>Created: {timeAgo(task.created_at)}</div>
      </div>
    </div>
  );
}