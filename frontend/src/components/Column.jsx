import { useState } from "react";
import TaskCard from "./TaskCard";

function Column({ column, tasks, allTasks, onOpenDetail }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="column" style={{ minWidth: collapsed ? "60px" : "" }}>
      <div className="column-header" style={{ borderTopColor: column.color }}>
        <button
          className="collapse-toggle"
          onClick={() => setCollapsed(!collapsed)}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: "12px",
            color: "#71717a",
            marginRight: "6px",
            padding: "0",
            lineHeight: "1",
          }}
          title={collapsed ? "Expand column" : "Collapse column"}
        >
          {collapsed ? "▶" : "▼"}
        </button>
        <span className="column-title">{column.label}</span>
        <span className="column-count">{tasks.length}</span>
      </div>
      {!collapsed && (
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
      )}
    </div>
  );
}

export default Column;