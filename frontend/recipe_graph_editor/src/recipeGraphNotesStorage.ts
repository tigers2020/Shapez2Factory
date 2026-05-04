/** 브라우저 로컬 메모 — 서버·graph_document와 무관. */
const KEY_PREFIX = "shapez-recipe-graph-notes";

export function recipeNotesStorageKey(recipeId: number): string {
  return `${KEY_PREFIX}:${recipeId}`;
}

export function loadRecipeNotes(recipeId: number): string {
  if (recipeId <= 0) {
    return "";
  }
  try {
    const raw = localStorage.getItem(recipeNotesStorageKey(recipeId));
    return typeof raw === "string" ? raw : "";
  } catch {
    return "";
  }
}

export function saveRecipeNotes(recipeId: number, text: string): void {
  if (recipeId <= 0) {
    return;
  }
  try {
    localStorage.setItem(recipeNotesStorageKey(recipeId), text);
  } catch {
    // quota / private mode
  }
}
