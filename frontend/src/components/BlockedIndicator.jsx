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

export default BlockedIndicator;