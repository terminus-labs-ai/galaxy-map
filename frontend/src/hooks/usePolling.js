import { useEffect, useCallback, useRef } from "react";

function usePolling(callback, interval = 3000) {
  const savedCallback = useRef(callback);

  // Remember the latest callback on every render
  savedCallback.current = callback;

  // Start polling on mount, stop on unmount
  useEffect(() => {
    savedCallback.current();
    const id = setInterval(() => savedCallback.current(), interval);
    return () => clearInterval(id);
  }, [interval]);

  // Return a manual trigger function
  const trigger = useCallback(() => {
    savedCallback.current();
  }, []);

  return trigger;
}

export default usePolling;
