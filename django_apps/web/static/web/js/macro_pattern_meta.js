/**
 * Staff macro recipe metadata editor (PATCH JSON API).
 */
(function () {
  "use strict";

  function readJsonScript(id) {
    const el = document.getElementById(id);
    if (!el || !el.textContent) {
      return null;
    }
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      console.error("macro meta:", id, e);
      return null;
    }
  }

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

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  const bootstrap = readJsonScript("macro-meta-bootstrap");
  const catalog = readJsonScript("macro-meta-catalog");
  const recipe = readJsonScript("macro-meta-recipe");
  const root = document.getElementById("macro-meta-form-root");
  const statusEl = document.getElementById("macro-meta-status");

  if (!bootstrap || !bootstrap.api_recipe_detail || !recipe || !root) {
    return;
  }

  function setStatus(msg, isError) {
    if (!statusEl) {
      return;
    }
    statusEl.textContent = msg || "";
    statusEl.classList.toggle("text-rose-300", Boolean(isError));
    statusEl.classList.toggle("text-amber-200/90", !isError && Boolean(msg));
  }

  async function api(method, url, body) {
    const headers = { "Content-Type": "application/json" };
    const csrftoken = getCookie("csrftoken");
    if (csrftoken) {
      headers["X-CSRFToken"] = csrftoken;
    }
    const res = await fetch(url, {
      method,
      headers,
      credentials: "same-origin",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (e) {
      data = { ok: false, error: text };
    }
    if (!res.ok) {
      throw new Error((data && data.error) || res.statusText || "request failed");
    }
    return data;
  }

  function buildFamilyOptions(selectedId) {
    const fam = (catalog && catalog.families) || [];
    return fam
      .map(function (f) {
        const sel = String(f.id) === String(selectedId) ? " selected" : "";
        return (
          '<option value="' +
          esc(f.id) +
          '"' +
          sel +
          ">" +
          esc(f.code) +
          " (" +
          esc(f.signature) +
          ")</option>"
        );
      })
      .join("");
  }

  function buildStrategyOptions(selected) {
    const codes = (catalog && catalog.strategy_codes) || [];
    return codes
      .map(function (c) {
        const sel = c === selected ? " selected" : "";
        return '<option value="' + esc(c) + '"' + sel + ">" + esc(c) + "</option>";
      })
      .join("");
  }

  function buildOpOptions(selected) {
    const ops = (catalog && catalog.operations) || [];
    return ops
      .map(function (o) {
        const sel = o.value === selected ? " selected" : "";
        return '<option value="' + esc(o.value) + '"' + sel + ">" + esc(o.label) + "</option>";
      })
      .join("");
  }

  function renderStepRow(step, index) {
    const inputs = JSON.stringify(step.input_slots || []);
    const outputs = JSON.stringify(step.output_slots || []);
    return (
      '<tr class="border-b border-neutral-800" data-step-row="' +
      index +
      '">' +
      '<td class="py-2 pr-2"><input type="number" min="1" class="macro-step-idx w-16 rounded border border-neutral-700 bg-neutral-900 px-2 py-1 font-mono text-xs" value="' +
      esc(step.step_index) +
      '" /></td>' +
      '<td class="py-2 pr-2"><select class="macro-step-op w-full rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs">' +
      buildOpOptions(step.operation) +
      "</select></td>" +
      '<td class="py-2 pr-2"><textarea rows="2" class="macro-step-in w-full rounded border border-neutral-700 bg-neutral-900 px-2 py-1 font-mono text-xs">' +
      esc(inputs) +
      "</textarea></td>" +
      '<td class="py-2 pr-2"><textarea rows="2" class="macro-step-out w-full rounded border border-neutral-700 bg-neutral-900 px-2 py-1 font-mono text-xs">' +
      esc(outputs) +
      "</textarea></td>" +
      '<td class="py-2 pr-2"><input type="text" class="macro-step-note w-full rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs" value="' +
      esc(step.note || "") +
      '" /></td>' +
      '<td class="py-2"><button type="button" class="macro-step-remove rounded border border-rose-900/60 px-2 py-1 text-xs text-rose-200 hover:bg-rose-950/40">Remove</button></td>' +
      "</tr>"
    );
  }

  function collectSteps(rootEl) {
    const rows = rootEl.querySelectorAll("tr[data-step-row]");
    const steps = [];
    rows.forEach(function (row) {
      const idx = parseInt(row.querySelector(".macro-step-idx").value, 10);
      const op = row.querySelector(".macro-step-op").value;
      let inputSlots;
      let outputSlots;
      try {
        inputSlots = JSON.parse(row.querySelector(".macro-step-in").value || "[]");
        outputSlots = JSON.parse(row.querySelector(".macro-step-out").value || "[]");
      } catch (e) {
        throw new Error("Invalid JSON in step slots");
      }
      if (!Array.isArray(inputSlots) || !Array.isArray(outputSlots)) {
        throw new Error("Step slots must be JSON arrays");
      }
      steps.push({
        step_index: idx,
        operation: op,
        input_slots: inputSlots,
        output_slots: outputSlots,
        note: row.querySelector(".macro-step-note").value || "",
      });
    });
    return steps;
  }

  const stepsHtml = (recipe.steps || []).map(function (s, i) {
    return renderStepRow(s, i);
  });

  root.innerHTML =
    '<form class="rounded-xl border border-neutral-800 bg-neutral-900/40 p-6">' +
    '<div class="grid gap-4 md:grid-cols-2">' +
    '<label class="block text-xs text-neutral-400">Family<br /><select class="macro-family mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm">' +
    buildFamilyOptions(recipe.family_id) +
    "</select></label>" +
    '<label class="block text-xs text-neutral-400">Recipe code<br /><input class="macro-code mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 font-mono text-sm" value="' +
    esc(recipe.code) +
    '" /></label>' +
    '<label class="block text-xs text-neutral-400">Strategy<br /><select class="macro-strategy mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 font-mono text-sm">' +
    buildStrategyOptions(recipe.strategy_code) +
    "</select></label>" +
    '<label class="block text-xs text-neutral-400">Display name<br /><input class="macro-name mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm" value="' +
    esc(recipe.name) +
    '" /></label>' +
    '<div class="md:col-span-2 rounded-lg border border-neutral-800 bg-neutral-950/50 p-3 text-xs text-neutral-300">' +
    "<p class=\"font-semibold text-amber-200/80\">Derived from graph</p>" +
    '<p class="mt-1 text-[11px] text-neutral-500">Update the canvas and <span class="text-neutral-400">commit</span> the graph, or PATCH <code class="font-mono">graph_document</code>, to refresh op / stage / waste cost and solver priority (lower numbers sort first; more operations increase the score).</p>' +
    '<ul class="mt-2 grid gap-1 font-mono text-sm sm:grid-cols-2">' +
    "<li>Op cost: <span class=\"macro-ro-oc text-emerald-200/90\">" +
    esc(recipe.estimated_operation_cost) +
    "</span></li>" +
    "<li>Stage cost: <span class=\"macro-ro-sc text-emerald-200/90\">" +
    esc(recipe.estimated_stage_cost) +
    "</span></li>" +
    "<li>Waste cost: <span class=\"macro-ro-wc text-emerald-200/90\">" +
    esc(recipe.estimated_waste_cost) +
    "</span></li>" +
    "<li>Priority: <span class=\"macro-ro-pr text-emerald-200/90\">" +
    esc(recipe.priority) +
    "</span></li>" +
    "</ul></div>" +
    '<label class="flex items-center gap-2 text-sm text-neutral-300 md:col-span-2"><input type="checkbox" class="macro-active h-4 w-4 rounded border-neutral-600"' +
    (recipe.is_active ? " checked" : "") +
    " /> Active in catalog</label>" +
    "</div>" +
    '<section class="mt-8">' +
    '<div class="flex items-center justify-between gap-2">' +
    '<h2 class="text-xs font-semibold uppercase tracking-wide text-amber-200/80">DB steps</h2>' +
    '<button type="button" class="macro-add-step rounded border border-neutral-600 px-3 py-1 text-xs text-neutral-200 hover:border-amber-400/50">Add step</button>' +
    "</div>" +
    '<p class="mt-1 text-[11px] text-neutral-500">Pattern Lab may use graph-derived steps when <code class="font-mono">graph_document</code> is set.</p>' +
    '<table class="mt-3 w-full text-left text-xs">' +
    "<thead><tr class=\"text-neutral-500\">" +
    "<th class=\"pb-2 pr-2\">#</th><th class=\"pb-2 pr-2\">Operation</th><th class=\"pb-2 pr-2\">input_slots</th><th class=\"pb-2 pr-2\">output_slots</th><th class=\"pb-2 pr-2\">Note</th><th></th>" +
    "</tr></thead>" +
    '<tbody class="macro-step-body">' +
    stepsHtml.join("") +
    "</tbody></table>" +
    "</section>" +
    '<div class="mt-8 flex flex-wrap justify-end gap-3">' +
    '<button type="button" class="macro-meta-save rounded-lg border border-amber-500/50 bg-amber-500/20 px-4 py-2 text-sm font-semibold text-amber-50 hover:bg-amber-500/30">Save metadata</button>' +
    "</div>" +
    "</form>";

  root.querySelector(".macro-add-step").addEventListener("click", function () {
    const tbody = root.querySelector(".macro-step-body");
    const nextIdx =
      tbody.querySelectorAll("tr").length > 0
        ? Math.max.apply(
            null,
            Array.prototype.map.call(tbody.querySelectorAll(".macro-step-idx"), function (el) {
              return parseInt(el.value, 10) || 0;
            }),
          ) + 1
        : 1;
    const tempStep = {
      step_index: nextIdx,
      operation: (catalog.operations[0] && catalog.operations[0].value) || "stacker",
      input_slots: [],
      output_slots: [],
      note: "",
    };
    tbody.insertAdjacentHTML("beforeend", renderStepRow(tempStep, tbody.children.length));
    wireRemove();
  });

  function wireRemove() {
    root.querySelectorAll(".macro-step-remove").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const tr = btn.closest("tr");
        if (tr) {
          tr.remove();
        }
      });
    });
  }
  wireRemove();

  function applyRecipeSnapshot(r) {
    if (!r) {
      return;
    }
    const oc = root.querySelector(".macro-ro-oc");
    const sc = root.querySelector(".macro-ro-sc");
    const wc = root.querySelector(".macro-ro-wc");
    const pr = root.querySelector(".macro-ro-pr");
    if (oc) {
      oc.textContent = r.estimated_operation_cost;
    }
    if (sc) {
      sc.textContent = r.estimated_stage_cost;
    }
    if (wc) {
      wc.textContent = r.estimated_waste_cost;
    }
    if (pr) {
      pr.textContent = r.priority;
    }
  }

  root.querySelector(".macro-meta-save").addEventListener("click", async function () {
    try {
      const steps = collectSteps(root);
      const payload = {
        family_id: parseInt(root.querySelector(".macro-family").value, 10),
        code: root.querySelector(".macro-code").value.trim(),
        strategy_code: root.querySelector(".macro-strategy").value,
        name: root.querySelector(".macro-name").value.trim(),
        is_active: root.querySelector(".macro-active").checked,
        steps: steps,
      };
      const data = await api("PATCH", bootstrap.api_recipe_detail, payload);
      applyRecipeSnapshot(data.recipe);
      setStatus("Saved.");
    } catch (e) {
      setStatus(String(e.message || e), true);
    }
  });
})();
