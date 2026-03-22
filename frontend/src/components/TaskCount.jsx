function TaskCount({ tasks }) {
  const statusCounts = {};

  tasks.forEach((task) => {
    const status = task.status;
    if (statusCounts[status] === undefined) {
      statusCounts[status] = 0;
    }
    statusCounts[status]++;
  });

  const entries = Object.entries(statusCounts);
  if (entries.length === 0) return null;

  return (
    <div className="task-count-bar">
      {entries.map(([status, count]) => (
        <span key={status} className="task-count-badge">
          <span className="task-count-label">{status}:</span>
          <span className="task-count-value">{count}</span>
        </span>
      ))}
    </div>
  );
}

export default TaskCount;
