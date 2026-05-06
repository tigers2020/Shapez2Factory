/** Writes macro graph status line in the Django-embedded shell (`#macro-graph-status`). */
export function setGlobalStatus(msg: string, isError: boolean): void {
  const el = document.getElementById("macro-graph-status");
  if (!el) {
    return;
  }
  el.textContent = msg;
  el.classList.toggle("text-rose-300", isError);
  el.classList.toggle("text-amber-200/90", !isError && Boolean(msg));
}
