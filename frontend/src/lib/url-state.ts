import { useCallback, useSyncExternalStore } from "react";

// View state (tab, auction, date) lives in the URL so every view is a shareable link.
const CHANGE_EVENT = "winddesk:urlchange";

function subscribe(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  window.addEventListener(CHANGE_EVENT, onChange);
  return () => {
    window.removeEventListener("popstate", onChange);
    window.removeEventListener(CHANGE_EVENT, onChange);
  };
}

export function setSearchParams(updates: Record<string, string | null>): void {
  const params = new URLSearchParams(window.location.search);
  for (const [key, value] of Object.entries(updates)) {
    if (value === null) params.delete(key);
    else params.set(key, value);
  }
  const query = params.toString();
  window.history.pushState(null, "", query ? `?${query}` : window.location.pathname);
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function useSearchParam(key: string): [string | null, (value: string | null) => void] {
  const value = useSyncExternalStore(subscribe, () =>
    new URLSearchParams(window.location.search).get(key),
  );
  const setValue = useCallback((next: string | null) => setSearchParams({ [key]: next }), [key]);
  return [value, setValue];
}
