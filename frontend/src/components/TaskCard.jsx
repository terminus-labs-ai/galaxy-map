import { useState, useEffect, useCallback } from "react";
import TaskCount from "./components/TaskCount";
import {
  DndContext,
  MouseSensor,
  TouchSensor,
  useSensor,
  useSensors,
  DragOverlay,
  defaultDropAnimationSideEffects,
} from "@dnd-kit/core";

const API = "/api";
const POLL_INTERVAL = 3000;

const SPECIALIZATIONS = ["diego", "intake", "planning", "claude-code", "coding", "research"];

const SPEC_COLORS = {
  diego: "#71717a",
  intake: "#5599ff",
  coding: "#a78bfa",
  planning: "#fb923c",
  research: "#34d399",
};

// ── Helpers ──────────────────────────────────────────────────────────────

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  if (res.status === 204) return null;
  return res.json();
}

function timeAgo(iso) {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function truncate(text, maxLen = 120) {
  if (!text || text.length <= maxLen) return text;
  return text.slice(0, maxLen).trimEnd() + "…";
}

// ── Components ─────────────────────────────────────────────────────────

function SpecBadge({ spec }) {
  return (
    <span
      className="spec-badge"
      style={{
        color: SPEC_COLORS[spec] || SPEC_COLORS.diego,
        borderColor: SPEC_COLORS[spec] || SPEC_COLORS.diego,
      }}
    >
      {spec}
    </span>
  );
}

function BlockedIndicator({ task, allTasks }) {
  if (!task.is_blocked) return null;

  const blockerNames = task.blocked_by
    .map((id) => {
      const t = allTasks.find((x) => x.id === id);
      return t ? t.title : id;
    })
    .join(", ");

  return (
    <span className="blocked-badge" title={`Blocked by: ${blockerNames}`}>
      blocked
    </span>
  );
}

function TaskCard({ task, allTasks, onOpenDetail }) {
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

export default TaskCard;