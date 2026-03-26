import { useState, useEffect } from "react";

const SPECIALIZATIONS = ["diego", "intake", "planning", "claude-code", "coding", "research"];

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

export default CreateTaskModal;