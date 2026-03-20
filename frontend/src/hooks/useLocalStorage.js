import { useState, useCallback } from "react";

function useLocalStorage(key, initialValue) {
  // SSR safety: check if window exists
  const hasWindow = typeof window !== "undefined";

  // Initialize state
  const [storedValue, setStoredValue] = useState(() => {
    if (!hasWindow) {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading from localStorage for key "${key}":`, error);
      return initialValue;
    }
  });

  // Update localStorage and state
  const setValue = useCallback(
    (value) => {
      if (!hasWindow) {
        return;
      }

      try {
        const newValue =
          value instanceof Function ? value(storedValue) : value;
        setStoredValue(newValue);
        window.localStorage.setItem(key, JSON.stringify(newValue));
      } catch (error) {
        console.warn(`Error writing to localStorage for key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  // Remove item from localStorage
  const removeValue = useCallback(() => {
    if (!hasWindow) {
      return;
    }

    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.warn(`Error removing from localStorage for key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
}

export default useLocalStorage;
