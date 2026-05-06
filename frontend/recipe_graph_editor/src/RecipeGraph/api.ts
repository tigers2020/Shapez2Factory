function getCookie(name: string): string | null {
  if (!document.cookie) {
    return null;
  }
  const parts = document.cookie.split(";");
  for (const element of parts) {
    const cookie = element.trim();
    if (cookie.startsWith(name + "=")) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return null;
}

export type RecipeGraphRecomputeResponse = {
  ok: boolean;
  error?: string;
  graph_document?: unknown;
  react_flow?: { version: number; nodes: unknown[]; edges: unknown[] };
  validation?: { ok: boolean; issues?: unknown[] };
  steps_synced?: boolean;
  warnings?: unknown[];
};

export async function postRecipeGraphRecompute(
  url: string,
  body: Record<string, unknown>,
): Promise<RecipeGraphRecomputeResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const csrf = getCookie("csrftoken");
  if (csrf) {
    headers["X-CSRFToken"] = csrf;
  }
  const res = await fetch(url, {
    method: "POST",
    headers,
    credentials: "same-origin",
    body: JSON.stringify(body),
  });
  const text = await res.text();
  let data: RecipeGraphRecomputeResponse = { ok: false, error: res.statusText };
  try {
    data = text ? (JSON.parse(text) as RecipeGraphRecomputeResponse) : { ok: false };
  } catch {
    data = { ok: false, error: text || res.statusText };
  }
  if (!res.ok) {
    const err = data.error || res.statusText || "request failed";
    throw new Error(typeof err === "string" ? err : "request failed");
  }
  if (!data.ok) {
    const err = data.error || "recompute failed";
    throw new Error(typeof err === "string" ? err : "recompute failed");
  }
  return data;
}
