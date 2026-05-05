/**
 * Bridge for static JS: Django JavaScriptCatalog defines window.gettext / ngettext.
 * shapezUiT(msgid) uses English msgids (same as djangojs .po). Vite dev: falls back to msgid.
 */
(function () {
  function locale() {
    const lang = (document.documentElement && document.documentElement.lang) || "";
    return String(lang).toLowerCase().startsWith("ko") ? "ko" : "en";
  }

  window.shapezUiLocale = locale;
  window.shapezUiT = function shapezUiT(msgid) {
    if (typeof gettext !== "undefined") {
      return gettext(msgid);
    }
    return msgid;
  };
})();
