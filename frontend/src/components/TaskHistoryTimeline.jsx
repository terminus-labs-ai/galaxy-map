import { useState } from "react";

// Event type colors and icons
const EVENT_TYPES = {
  status_change: {
    color: "#22c55e", // green-500
    icon: "🔄",
    label: "Status Change",
  },
  metadata_update: {
    color: "#3b82f6", // blue-500
    icon: "📝",
    label: "Metadata Update",
  },
  assignment: {
    color: "#fb923c", // orange-500
    icon: "👤",
    label: "Assignment",
  },
  comment: {
    color: "#8b5cf6", // violet-500
    icon: "💬",
    label: "Comment",
  },
};

// Format timestamp to relative time
function timeAgo(timestamp) {
  if (!timestamp) return "Unknown time";
  
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now - then;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} week${Math.floor(diffDays / 7) > 1 ? "s" : ""} ago`;
  
  return then.toLocaleDateString();
}

// Format value for display
function formatValue(value) {
  if (value === null || value === undefined) return "null";
  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

// Compare old and new values for display
function ValueComparison({ oldVal, newVal }) {
  if (oldVal === null && newVal === null) return null;
  if (oldVal === null) {
    return (
      <div className="history-value-comparison">
        <span className="history-value-added">+ {formatValue(newVal)}</span>
      </div>
    );
  }
  if (newVal === null) {
    return (
      <div className="history-value-comparison">
        <span className="history-value-removed">- {formatValue(oldVal)}</span>
      </div>
    );
  }
  if (oldVal === newVal) {
    return (
      <div className="history-value-comparison">
        <span className="history-value-unchanged">{formatValue(oldVal)}</span>
      </div>
    );
  }

  return (
    <div className="history-value-comparison">
      <div className="history-value-row">
        <span className="history-value-label">Old:</span>
        <span className="history-value-removed">{formatValue(oldVal)}</span>
      </div>
      <div className="history-value-row">
        <span className="history-value-label">New:</span>
        <span className="history-value-added">{formatValue(newVal)}</span>
      </div>
    </div>
  );
}

// Expandable detail section
function HistoryDetails({ details }) {
  const [expanded, setExpanded] = useState(false);

  if (!details || Object.keys(details).length === 0) return null;

  return (
    <div className="history-details">
      <button
        className="history-details-toggle"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="history-details-icon">
          {expanded ? "▼" : "▶"}
        </span>
        <span className="history-details-label">Details</span>
      </button>
      {expanded && (
        <div className="history-details-content">
          <pre>{JSON.stringify(details, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

// Single history entry
function HistoryEntry({ entry }) {
  const eventType = EVENT_TYPES[entry.event_type] || EVENT_TYPES.metadata_update;
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="history-entry">
      <div className="history-entry-header" onClick={() => setExpanded(!expanded)}>
        <div className="history-entry-icon" style={{ color: eventType.color }}>
          {eventType.icon}
        </div>
        <div className="history-entry-content">
          <div className="history-entry-title">
            <span style={{ color: eventType.color }}>{eventType.label}</span>
            {entry.changed_by && (
              <span className="history-entry-changed-by"> by {entry.changed_by}</span>
            )}
          </div>
          <div className="history-entry-time">{timeAgo(entry.timestamp)}</div>
        </div>
        <div className="history-entry-toggle">
          {expanded ? "▼" : "▶"}
        </div>
      </div>
      
      {expanded && (
        <div className="history-entry-body">
          <ValueComparison oldVal={entry.old_value} newVal={entry.new_value} />
          <HistoryDetails details={entry.details} />
        </div>
      )}
    </div>
  );
}

// Compact mode - show only last 5 entries
function CompactTimeline({ history }) {
  const recentHistory = history.slice(0, 5);
  
  return (
    <div className="history-timeline history-timeline-compact">
      {recentHistory.map((entry) => (
        <HistoryEntry key={entry.id} entry={entry} />
      ))}
      {history.length > 5 && (
        <div className="history-more-entries">
          +{history.length - 5} more entries
        </div>
      )}
    </div>
  );
}

// Full mode - scrollable timeline
function FullTimeline({ history, hasMore, onLoadMore, loading }) {
  return (
    <div className="history-timeline history-timeline-full">
      {history.map((entry) => (
        <HistoryEntry key={entry.id} entry={entry} />
      ))}
      {hasMore && (
        <button className="history-load-more" onClick={onLoadMore} disabled={loading}>
          {loading ? "Loading..." : "Load more"}
        </button>
      )}
      {history.length === 0 && (
        <div className="history-empty">
          No history entries yet
        </div>
      )}
    </div>
  );
}

// Main component
export function TaskHistoryTimeline({ history, loading, error, hasMore, onLoadMore, compact = false }) {
  if (loading && history.length === 0) {
    return (
      <div className="history-loading">
        <span className="history-spinner">⟳</span>
        <span>Loading history...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="history-error">
        Error loading history: {error}
      </div>
    );
  }

  if (!history || history.length === 0) {
    return (
      <div className="history-empty">
        No history entries yet
      </div>
    );
  }

  if (compact) {
    return <CompactTimeline history={history} />;
  }

  return (
    <FullTimeline
      history={history}
      hasMore={hasMore}
      onLoadMore={onLoadMore}
      loading={loading}
    />
  );
}
