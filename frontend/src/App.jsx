import { useState, useEffect, useCallback } from "react";

const API = "/api";
const POLL_INTERVAL = 3000;

const COLUMNS = [
  { key: "backlog", label: "Backlog" },
  { key: "queued", label: "Queued" },
  { key: "in_progress", label: "In Progress" },
  { key: "needs_review", label: "Needs Review" },
  { key: "done", label: "Done" },
];

const SPECIALIZATIONS = ["general", "coding", "planning", "research"];

const SPEC_COLORS = {
  general: "#71717a",
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

// ── Components ───────────────────────────────────────────────────────────

function SpecBadge({ spec }) {
  return (
    <span
      className="spec-badge"
      style={{
        color: SPEC_COLORS[spec] || SPEC_COLORS.general,
        borderColor: SPEC_COLORS[spec] || SPEC_COLORS.general,
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

function TaskCard({ task, allTasks, onDelete, onMove }) {
  const [expanded, setExpanded] = useState(false);
  const colIdx = COLUMNS.findIndex((c) => c.key === task.status);

  return (
    <div
      className={`card ${task.is_blocked ? "card-blocked" : ""}`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="card-header">
        <div className="card-title">{task.title}</div>
      </div>

      <div className="card-badges">
        <SpecBadge spec={task.specialization} />
        <BlockedIndicator task={task} allTasks={allTasks} />
      </div>

      {!expanded && task.description && (
        <p className="card-desc-preview">{truncate(task.description)}</p>
      )}

      <div className="card-meta">{timeAgo(task.updated_at)}</div>

      {expanded && (
        <div className="card-expanded" onClick={(e) => e.stopPropagation()}>
          {task.description && (
            <p className="card-desc">{task.description}</p>
          )}

          {task.blocked_by.length > 0 && (
            <div className="card-blockers">
              <span className="blockers-label">Blocked by:</span>
              {task.blocked_by.map((id) => {
                const t = allTasks.find((x) => x.id === id);
                return (
                  <span key={id} className="blocker-chip">
                    {t ? t.title : id}
                  </span>
                );
              })}
            </div>
          )}

          <div className="card-actions">
            {colIdx > 0 && (
              <button
                className="btn btn-sm"
                onClick={() => onMove(task.id, COLUMNS[colIdx - 1].key)}
              >
                ← {COLUMNS[colIdx - 1].label}
              </button>
            )}
            {colIdx < COLUMNS.length - 1 && (
              <button
                className="btn btn-sm"
                onClick={() => onMove(task.id, COLUMNS[colIdx + 1].key)}
              >
                {COLUMNS[colIdx + 1].label} →
              </button>
            )}
            <button
              className="btn btn-sm btn-danger"
              onClick={() => onDelete(task.id)}
            >
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Column({ column, tasks, allTasks, onDelete, onMove }) {
  return (
    <div className="column">
      <div className="column-header">
        <span className="column-title">{column.label}</span>
        <span className="column-count">{tasks.length}</span>
      </div>
      <div className="column-body">
        {tasks.map((t) => (
          <TaskCard
            key={t.id}
            task={t}
            allTasks={allTasks}
            onDelete={onDelete}
            onMove={onMove}
          />
        ))}
      </div>
    </div>
  );
}

function AddTaskForm({ onAdd }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [spec, setSpec] = useState("general");

  const submit = () => {
    if (!title.trim()) return;
    onAdd({
      title: title.trim(),
      description: desc.trim(),
      specialization: spec,
    });
    setTitle("");
    setDesc("");
    setSpec("general");
    setOpen(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey && e.target.tagName !== "TEXTAREA") {
      e.preventDefault();
      submit();
    }
    if (e.key === "Escape") {
      setOpen(false);
    }
  };

  if (!open) {
    return (
      <button className="btn btn-add" onClick={() => setOpen(true)}>
        + New Task
      </button>
    );
  }

  return (
    <div className="add-form" onKeyDown={handleKeyDown}>
      <input
        autoFocus
        className="input"
        placeholder="Task title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <textarea
        className="input textarea"
        placeholder="Description (optional)"
        rows={2}
        value={desc}
        onChange={(e) => setDesc(e.target.value)}
      />
      <select
        className="input select"
        value={spec}
        onChange={(e) => setSpec(e.target.value)}
      >
        {SPECIALIZATIONS.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
      <div className="add-form-actions">
        <button className="btn btn-primary" onClick={submit}>
          Create
        </button>
        <button className="btn" onClick={() => setOpen(false)}>
          Cancel
        </button>
      </div>
    </div>
  );
}

// ── App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState(null);

  const fetchTasks = useCallback(async () => {
    try {
      const data = await api("/tasks");
      setTasks(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchTasks]);

  const addTask = async (task) => {
    await api("/tasks", {
      method: "POST",
      body: JSON.stringify(task),
    });
    fetchTasks();
  };

  const deleteTask = async (id) => {
    await api(`/tasks/${id}`, { method: "DELETE" });
    fetchTasks();
  };

  const moveTask = async (id, newStatus) => {
    await api(`/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: newStatus }),
    });
    fetchTasks();
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <h1 className="logo">Galaxy Map</h1>
          <span className="version">v0.2.0</span>
        </div>
        <AddTaskForm onAdd={addTask} />
      </header>

      {error && <div className="error-banner">API error: {error}</div>}

      <div className="board">
        {COLUMNS.map((col) => (
          <Column
            key={col.key}
            column={col}
            tasks={tasks.filter((t) => t.status === col.key)}
            allTasks={tasks}
            onDelete={deleteTask}
            onMove={moveTask}
          />
        ))}
      </div>
    </div>
  );
}
