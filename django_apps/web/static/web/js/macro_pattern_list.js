/**
 * Staff macro catalog list — delete via API only.
 */
(function () {
  "use strict";

  function getCookie(name) {
    if (!document.cookie) {
      return null;
    }
    const parts = document.cookie.split(";");
    for (let i = 0; i < parts.length; i += 1) {
      const cookie = parts[i].trim();
      if (cookie.startsWith(name + "=")) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return null;
  }

  const statusEl = document.getElementById("macro-list-status");

  function setStatus(msg, isError) {
    if (!statusEl) {
      return;
    }
    statusEl.textContent = msg || "";
    statusEl.classList.toggle("text-rose-300", Boolean(isError));
    statusEl.classList.toggle("text-amber-200/90", !isError && Boolean(msg));
  }

  document.querySelectorAll(".macro-list-delete").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const url = btn.getAttribute("data-delete-url");
      const code = btn.getAttribute("data-recipe-code") || "recipe";
      if (!url || !window.confirm("Delete macro recipe " + code + "?")) {
        return;
      }
      const csrftoken = getCookie("csrftoken");
      const headers = {};
      if (csrftoken) {
        headers["X-CSRFToken"] = csrftoken;
      }
      try {
        const res = await fetch(url, { method: "DELETE", credentials: "same-origin", headers });
        const text = await res.text();
        let data = null;
        try {
          data = text ? JSON.parse(text) : null;
        } catch (e) {
          data = { ok: false };
        }
        if (!res.ok) {
          throw new Error((data && data.error) || res.statusText || "delete failed");
        }
        setStatus("Deleted " + code + ". Reloading…");
        window.location.reload();
      } catch (e) {
        setStatus(String(e.message || e), true);
      }
    });
  });
})();
