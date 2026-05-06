import { EDITOR_LAYOUT_CONSOLE_DEBUG_LS_KEY } from "./constants";

/**
 * Opt-in editor layout diagnostics via `console.log` (full JSON string so DevTools does not collapse `{…}`).
 *
 * Enable any one:
 * - `globalThis.__SHAPEZ_DEBUG_GRAPH_LAYOUT__ = true`
 * - `localStorage` / `sessionStorage` key `shapezDebugGraphLayout` = `'1'` or `'true'`
 * - URL query `?debugGraphLayout=1` (or `=true`)
 */
export function isEditorGraphLayoutConsoleDebugEnabled(): boolean {
  if (typeof globalThis === "undefined") {
    return false;
  }
  const g = globalThis as unknown as Record<string, unknown>;
  if (g.__SHAPEZ_DEBUG_GRAPH_LAYOUT__ === true) {
    return true;
  }
  const storageMatch = (store?: Storage): boolean => {
    try {
      const v = store?.getItem(EDITOR_LAYOUT_CONSOLE_DEBUG_LS_KEY);
      return v === "1" || v === "true";
    } catch {
      return false;
    }
  };
  if (
    storageMatch((globalThis as { localStorage?: Storage }).localStorage) ||
    storageMatch((globalThis as { sessionStorage?: Storage }).sessionStorage)
  ) {
    return true;
  }
  try {
    const search = (globalThis as { location?: { search?: string } }).location?.search;
    if (typeof search === "string" && search.length > 1) {
      const qs = new URLSearchParams(search);
      const q = qs.get("debugGraphLayout");
      if (q === "1" || q === "true") {
        return true;
      }
    }
  } catch {
    /* ignore */
  }
  return false;
}
