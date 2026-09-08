import { useCallback, useEffect, useSyncExternalStore } from "react";

const THEME_KEY = "chunky-theme";
const listeners = new Set<() => void>();

function applyTheme(dark: boolean) {
  document.documentElement.classList.toggle("dark", dark);
}

function readTheme(): boolean {
  const stored = window.localStorage.getItem(THEME_KEY);
  if (stored) {
    return stored === "dark";
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function subscribe(onStoreChange: () => void) {
  listeners.add(onStoreChange);
  return () => listeners.delete(onStoreChange);
}

export function useTheme() {
  const dark = useSyncExternalStore(subscribe, readTheme, () => false);

  useEffect(() => {
    applyTheme(dark);
  }, [dark]);

  const toggleTheme = useCallback(() => {
    const next = !readTheme();
    window.localStorage.setItem(THEME_KEY, next ? "dark" : "light");
    applyTheme(next);
    listeners.forEach((listener) => listener());
  }, []);

  return { dark, toggleTheme };
}
