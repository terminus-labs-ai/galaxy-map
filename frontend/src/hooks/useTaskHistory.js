import { useState, useEffect, useCallback } from "react";

function api(path, options = {}) {
  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
    },
  };
  const mergedOptions = { ...defaultOptions, ...options };
  return fetch(path, mergedOptions).then(async (resp) => {
    const text = await resp.text();
    if (text) {
      try {
        return JSON.parse(text);
      } catch (e) {
        return text;
      }
    }
  });
}

export function useTaskHistory(taskId) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(false);

  const fetchHistory = useCallback(
    async (limit = 100, offset = 0) => {
      if (!taskId) {
        setHistory([]);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const data = await api(
          `/api/tasks/${taskId}/history?limit=${limit}&offset=${offset}`
        );
        setHistory(data || []);
        setHasMore((data || []).length === limit);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [taskId]
  );

  useEffect(() => {
    if (taskId) {
      fetchHistory();
    } else {
      setHistory([]);
    }
  }, [taskId, fetchHistory]);

  const loadMore = useCallback(async () => {
    if (!hasMore || loading) return;

    const currentLength = history.length;
    try {
      const data = await api(
        `/api/tasks/${taskId}/history?limit=50&offset=${currentLength}`
      );
      setHistory((prev) => [...prev, ...(data || [])]);
      setHasMore((data || []).length === 50);
    } catch (err) {
      setError(err.message);
    }
  }, [taskId, history.length, hasMore, loading]);

  return { history, loading, error, hasMore, loadMore, refetch: fetchHistory };
}
