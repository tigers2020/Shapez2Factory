/** Django JavaScriptCatalog globals; fallback to English msgid when catalog not loaded (e.g. Vite dev). */

declare global {
  interface Window {
    gettext?: (msgid: string) => string;
    ngettext?: (singular: string, plural: string, count: number) => string;
  }
}

export function t(msgid: string): string {
  if (typeof window !== "undefined" && typeof window.gettext === "function") {
    return window.gettext(msgid);
  }
  return msgid;
}

export function tn(singular: string, plural: string, count: number): string {
  if (typeof window !== "undefined" && typeof window.ngettext === "function") {
    return window.ngettext(singular, plural, count);
  }
  return count === 1 ? singular : plural;
}
