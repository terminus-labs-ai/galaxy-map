import { useEffect } from "react";
import SpecBadge from "./SpecBadge";
import { truncate } from "../utils/helpers";

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

export default SearchResultsModal;
