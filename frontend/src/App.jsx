import { useState, useEffect, useCallback } from "react";

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

// ── Components ───────────────────────────────────────────────────────

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


function MetadataEditor({ value, onChange }) {
  const [text, setText] = useState(JSON.stringify(value || {}, null, 2));
  const [error, setError] = useState(null);

  // Sync when external value changes (e.g. poll refresh)
  useEffect(() => {
    try {
      const current = JSON.parse(text);
      if (JSON.stringify(current) !== JSON.stringify(value || {})) {
        setText(JSON.stringify(value || {}, null, 2));
        setError(null);
      }
    } catch {
      // If current text is invalid, don't overwrite user's edits
    }
  }, [value]);

  function handleChange(e) {
    const newText = e.target.value;
    setText(newText);
    try {
      const parsed = JSON.parse(newText);
      setError(null);
      onChange(parsed);
    } catch {
      setError("Invalid JSON");
    }
  }

  return (
    <div>
      <textarea className="modal-textarea modal-meta-editor" rows={6} value={text} onChange={handleChange} spellCheck={false} />
      {error && <div className="meta-error">{error}</div>}
    </div>
  );
}


function BlockerEditor({ blockedBy, allTasks, taskId, onChange }) {
  const available = allTasks.filter(
    (t) => t.id !== taskId && !blockedBy.includes(t.id)
  );

  return (
    <div className="blocker-editor">
      <div className="blocker-chips">
        {blockedBy.map((id) => {
          const t = allTasks.find((x) => x.id === id);
          return (
            <span key={id} className="blocker-chip blocker-chip-removable">
              {t ? truncate(t.title, 30) : id}
              <button
                className="blocker-remove"
                onClick={() => onChange(blockedBy.filter((b) => b !== id))}
              >
                ×
              </button>
            </span>
          );
        })}
      </div>
      {available.length > 0 && (
        <select
          className="input select blocker-select"
          value=""
          onChange={(e) => {
            if (e.target.value) onChange([...blockedBy, e.target.value]);
          }}
        >
          <option value="">Add blocker...</option>
          {available.map((t) => (
            <option key={t.id} value={t.id}>
              {truncate(t.title, 40)}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}

function CreateTaskModal({ onClose, onCreate }) {
  const [draft, setDraft] = useState({
    title: "",
    description: "",
    specialization: "diego",
  });

  // Escape key handler
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  });

  function handleCreate() {
    if (!draft.title.trim()) return;
    onCreate({
      title: draft.title.trim(),
      description: draft.description.trim(),
      specialization: draft.specialization,
    });
    onClose();
  }

  function setField(key, value) {
    setDraft((d) => ({ ...d, [key]: value }));
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-badges">
            <span style={{ fontSize: "14px", fontWeight: "500" }}>Create Task</span>
          </div>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Title */}
          <div className="modal-field">
            <label className="modal-label">Title</label>
            <input
              autoFocus
              className="modal-input"
              placeholder="Task title"
              value={draft.title}
              onChange={(e) => setField("title", e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCreate();
              }}
            />
          </div>

          {/* Description */}
          <div className="modal-field">
            <label className="modal-label">Description</label>
            <textarea
              className="modal-textarea"
              rows={4}
              placeholder="Description (optional)"
              value={draft.description}
              onChange={(e) => setField("description", e.target.value)}
            />
          </div>

          {/* Specialization */}
          <div className="modal-field">
            <label className="modal-label">Specialization</label>
            <select
              className="input select"
              value={draft.specialization}
              onChange={(e) => setField("specialization", e.target.value)}
            >
              {SPECIALIZATIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <div className="modal-footer-left" />
          <div className="modal-footer-right">
            <button className="btn btn-sm" onClick={onClose}>
              Cancel
            </button>
            <button
              className="btn btn-sm btn-primary"
              onClick={handleCreate}
              disabled={!draft.title.trim()}
            >
              Create
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SearchResultsModal({ searchQuery, searchResults, allTasks, onClose, onOpenDetail }) {
  // Escape key handler
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-search" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-badges">
            <span style={{ fontSize: "14px", fontWeight: "500" }}>
              Search Results ({searchResults.length})
            </span>
          </div>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Body */}
        <div className="modal-body search-results">
          {searchResults.length === 0 ? (
            <div className="search-no-results">
              No results for "{searchQuery}"
            </div>
          ) : (
            <div className="search-results-list">
              {searchResults.map((task) => (
                <div
                  key={task.id}
                  className="search-result-item"
                  onClick={() => {
                    onOpenDetail(task.id);
                    onClose();
                  }}
                >
                  <div className="search-result-header">
                    <div className="search-result-title">{task.title}</div>
                    <SpecBadge spec={task.specialization} />
                  </div>
                  {task.description && (
                    <div className="search-result-desc">
                      {truncate(task.description, 80)}
                    </div>
                  )}
                  <div className="search-result-meta">
                    <span className="search-result-id">{task.id}</span>
                    <span className="search-result-status">{task.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TaskDetailModal({ taskId, allTasks, onClose, onUpdate, onDelete, columns }) {
  const task = allTasks.find((t) => t.id === taskId);
  const [draft, setDraft] = useState(null);

  // Initialize draft when task changes
  useEffect(() => {
    if (task) {
      setDraft({
        title: task.title,
        description: task.description || "",
        specialization: task.specialization,
        priority: task.priority,
        blocked_by: [...task.blocked_by],
        metadata: task.metadata ? JSON.parse(JSON.stringify(task.metadata)) : {},
      });
    }
  }, [taskId, task?.updated_at]);

  // Escape key handler
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") tryClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  });

  if (!task || !draft || !columns) return null;

  const isDirty =
    draft.title !== task.title ||
    draft.description !== (task.description || "") ||
    draft.specialization !== task.specialization ||
    draft.priority !== task.priority ||
    JSON.stringify(draft.blocked_by) !== JSON.stringify(task.blocked_by) ||
    JSON.stringify(draft.metadata) !== JSON.stringify(task.metadata || {});

  function tryClose() {
    if (isDirty) {
      if (!window.confirm("You have unsaved changes. Discard them?")) return;
    }
    onClose();
  }

  function handleSave() {
    const fields = {};
    if (draft.title !== task.title) fields.title = draft.title;
    if (draft.description !== (task.description || ""))
      fields.description = draft.description;
    if (draft.specialization !== task.specialization)
      fields.specialization = draft.specialization;
    if (draft.priority !== task.priority) fields.priority = draft.priority;
    if (JSON.stringify(draft.blocked_by) !== JSON.stringify(task.blocked_by))
      fields.blocked_by = draft.blocked_by;
    if (JSON.stringify(draft.metadata) !== JSON.stringify(task.metadata || {}))
      fields.metadata = draft.metadata;
    if (Object.keys(fields).length > 0) onUpdate(task.id, fields);
  }

  const colIdx = columns.findIndex((c) => c.key === task.status);

  function handleMove(newStatus) {
    onUpdate(task.id, { status: newStatus });
  }

  function handleDelete() {
    if (!window.confirm("Delete this task?")) return;
    onDelete(task.id);
    onClose();
  }

  function setField(key, value) {
    setDraft((d) => ({ ...d, [key]: value }));
  }

  return (
    <div className="modal-overlay" onClick={tryClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-badges">
            <SpecBadge spec={draft.specialization} />
            <BlockedIndicator task={task} allTasks={allTasks} />
          </div>
          <button className="modal-close" onClick={tryClose}>
            ×
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Title */}
          <div className="modal-field">
            <label className="modal-label">Title</label>
            <input
              className="modal-input"
              value={draft.title}
              onChange={(e) => setField("title", e.target.value)}
            />
          </div>

          {/* Description */}
          <div className="modal-field">
            <label className="modal-label">Description</label>
            <textarea
              className="modal-textarea"
              rows={4}
              value={draft.description}
              placeholder="No description"
              onChange={(e) => setField("description", e.target.value)}
            />
          </div>

          {/* Specialization + Priority row */}
          <div className="modal-row">
            <div className="modal-field modal-field-half">
              <label className="modal-label">Specialization</label>
              <select
                className="input select"
                value={draft.specialization}
                onChange={(e) => setField("specialization", e.target.value)}
              >
                {SPECIALIZATIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div className="modal-field modal-field-half">
              <label className="modal-label">Priority</label>
              <input
                className="modal-input"
                type="number"
                value={draft.priority}
                onChange={(e) =>
                  setField("priority", parseInt(e.target.value, 10) || 0)
                }
              />
            </div>
          </div>

          {/* Blockers */}
          <div className="modal-field">
            <label className="modal-label">Blocked by</label>
            <BlockerEditor
              blockedBy={draft.blocked_by}
              allTasks={allTasks}
              taskId={taskId}
              onChange={(ids) => setField("blocked_by", ids)}
            />
          </div>

          {/* Read-only metadata */}
          <div className="modal-meta-grid">
            <div className="modal-meta-item">
              <span className="modal-meta-key">ID</span>
              <span className="modal-meta-value">{task.id}</span>
            </div>
            <div className="modal-meta-item">
              <span className="modal-meta-key">Status</span>
              <span className="modal-meta-value">{task.status}</span>
            </div>
            <div className="modal-meta-item">
              <span className="modal-meta-key">Updated</span>
              <span className="modal-meta-value">
                {timeAgo(task.updated_at)}
              </span>
            </div>
            <div className="modal-meta-item">
              <span className="modal-meta-key">Created</span>
              <span className="modal-meta-value">
                {timeAgo(task.created_at)}
              </span>
            </div>
          </div>

          {/* Metadata JSON */}
          <div className="modal-field">
            <label className="modal-label">Metadata</label>
            <MetadataEditor value={draft.metadata} onChange={(val) => setField("metadata", val)} />
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <div className="modal-footer-left">
            {colIdx > 0 && (
              <button
                className="btn btn-sm"
                onClick={() => handleMove(columns[colIdx - 1].key)}
              >
                ← {columns[colIdx - 1].label}
              </button>
            )}
            {colIdx < columns.length - 1 && (
              <button
                className="btn btn-sm"
                onClick={() => handleMove(columns[colIdx + 1].key)}
              >
                {columns[colIdx + 1].label} →
              </button>
            )}
          </div>
          <div className="modal-footer-right">
            <button
              className="btn btn-sm btn-danger"
              onClick={handleDelete}
            >
              Delete
            </button>
            {isDirty && (
              <button
                className="btn btn-sm btn-primary"
                onClick={handleSave}
              >
                Save
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function TaskCard({ task, allTasks, onOpenDetail }) {
  return (
    <div
      className={`card ${task.is_blocked ? "card-blocked" : ""}`}
      onClick={() => onOpenDetail(task.id)}
    >
      <div className="card-header">
        <div className="card-title">{task.title}</div>
      </div>

      <div className="card-badges">
        <SpecBadge spec={task.specialization} />
        <BlockedIndicator task={task} allTasks={allTasks} />
      </div>

      {task.description && (
        <p className="card-desc-preview">{truncate(task.description)}</p>
      )}

      <div className="card-meta">{timeAgo(task.updated_at)}</div>
    </div>
  );
}

function Column({ column, tasks, allTasks, onOpenDetail }) {
  return (
    <div className="column">
      <div className="column-header" style={{ borderTopColor: column.color }}>
        <span className="column-title">{column.label}</span>
        <span className="column-count">{tasks.length}</span>
      </div>
      <div className="column-body">
        {tasks.map((t) => (
          <TaskCard
            key={t.id}
            task={t}
            allTasks={allTasks}
            onOpenDetail={onOpenDetail}
          />
        ))}
      </div>
    </div>
  );
}

// ── App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [columns, setColumns] = useState([]);
  const [error, setError] = useState(null);
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  // Fetch statuses once on mount and build columns
  useEffect(() => {
    async function fetchStatuses() {
      try {
        const statuses = await api("/statuses");
        setColumns(statuses);
        setError(null);
      } catch (err) {
        setError(`Failed to load statuses: ${err.message}`);
      }
    }
    fetchStatuses();
  }, []);

  const fetchTasks = useCallback(async () => {
    try {
      // Build status query from all available statuses (from columns)
      const statusQuery = columns.map((c) => c.key).join(",");
      const data = await api(`/tasks?status=${statusQuery}`);
      setTasks(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }, [columns]);

  // Poll for task updates
  useEffect(() => {
    if (columns.length === 0) return; // Wait for columns to load
    fetchTasks();
    const interval = setInterval(fetchTasks, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchTasks, columns.length]);

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

  const updateTask = async (id, fields) => {
    await api(`/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(fields),
    });
    fetchTasks();
  };

  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearchOpen(false);
      return;
    }

    setIsSearching(true);
    try {
      const results = await api(`/tasks/search?q=${encodeURIComponent(query)}`);
      setSearchResults(results);
      if (results.length > 0) {
        setIsSearchOpen(true);
      }
    } catch (err) {
      setError(`Search failed: ${err.message}`);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <h1 className="logo">Galaxy Map</h1>
          <span className="version">v0.2.0</span>
        </div>
        <div className="header-search">
          <input
            type="text"
            className="search-input"
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            onFocus={() => searchQuery && setIsSearchOpen(true)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && searchResults.length > 0) {
                setIsSearchOpen(true);
              }
            }}
          />
          {isSearching && <div className="search-spinner">⟳</div>}
        </div>
        <button className="btn btn-add" onClick={() => setIsCreateModalOpen(true)}>
          + New Task
        </button>
      </header>

      {error && <div className="error-banner">API error: {error}</div>}

      <div className="board">
        {columns.map((col) => (
          <Column
            key={col.key}
            column={col}
            tasks={tasks.filter((t) => t.status === col.key)}
            allTasks={tasks}
            onOpenDetail={setSelectedTaskId}
          />
        ))}
      </div>

      {isCreateModalOpen && (
        <CreateTaskModal
          onClose={() => setIsCreateModalOpen(false)}
          onCreate={addTask}
        />
      )}

      {isSearchOpen && searchResults.length > 0 && (
        <SearchResultsModal
          searchQuery={searchQuery}
          searchResults={searchResults}
          allTasks={tasks}
          onClose={() => setIsSearchOpen(false)}
          onOpenDetail={setSelectedTaskId}
        />
      )}

      {selectedTaskId && (
        <TaskDetailModal
          taskId={selectedTaskId}
          allTasks={tasks}
          onClose={() => setSelectedTaskId(null)}
          onUpdate={updateTask}
          onDelete={deleteTask}
          columns={columns}
        />
      )}
    </div>
  );
}
