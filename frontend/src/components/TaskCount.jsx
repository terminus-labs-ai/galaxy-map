function TaskCount({ tasks }) {
  const statusCounts = {};
  
  // Count tasks by status
  tasks.forEach((task) => {
    const status = task.status;
    if (statusCounts[status] === undefined) {
      statusCounts[status] = 0;
    }
    statusCounts[status]++;
  });

  // Build badges for each status
  const badges = Object.entries(statusCounts).map(([status, count]) => (
    <span
      key={status}
      style={{
        display: "inline-flex",
        alignItems: "center",
        backgroundColor: "#e5e7eb",
        borderRadius: "12px",
        padding: "4px 10px",
        margin: "0 4px",
        fontSize: "12px",
        fontWeight: "500",
      }}
    >
      <span style={{ marginRight: "4px" }}>{status}:</span>
      <span style={{ fontWeight: "bold" }}>{count}</span>
    </span>
  ));

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "center",
        padding: "10px",
        backgroundColor: "#f9fafb",
        borderRadius: "8px",
        marginBottom: "16px",
        gap: "8px",
      }}
    >
      {badges}
    </div>
  );
}

export default TaskCount;
