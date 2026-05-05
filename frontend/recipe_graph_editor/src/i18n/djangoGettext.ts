/** Django JavaScriptCatalog globals; fallback to English msgid when catalog not loaded (e.g. Vite dev). */

declare global {
  interface Window {
    gettext?: (msgid: string) => string;
    ngettext?: (singular: string, plural: string, count: number) => string;
  }
}

export function t(msgid: string): string {
  if (
    globalThis.window !== undefined &&
    typeof globalThis.window.gettext === "function"
  ) {
    return globalThis.window.gettext(msgid);
  }
  return msgid;
}

export function tn(singular: string, plural: string, count: number): string {
  if (
    globalThis.window !== undefined &&
    typeof globalThis.window.ngettext === "function"
  ) {
    return globalThis.window.ngettext(singular, plural, count);
  }
  return count === 1 ? singular : plural;
}
