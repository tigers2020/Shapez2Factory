/** Opt-in production: ``localStorage.setItem('shapezDebugMacroGraph','1')`` 후 새로고침. Vite 개발 서버에서는 기본 활성. */

function isViteDev(): boolean {
  try {
    return Boolean((import.meta as ImportMeta & { env?: { DEV?: boolean } }).env?.DEV);
  } catch {
    return false;
  }
}

function debugEnabled(): boolean {
  try {
    if (globalThis.localStorage?.getItem("shapezDebugMacroGraph") === "1") {
      return true;
    }
  } catch {
    /* localStorage unavailable */
  }
  return isViteDev();
}

export function macroGraphDebug(...args: unknown[]): void {
  if (debugEnabled()) {
    console.info("[macro-graph]", ...args);
  }
}
