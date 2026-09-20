/**
 * Role: Mounts the list block modal frontend.
 * File Name: block_modal.js
 * Author: Alexandre EL
 * Email: alex@hackinvent.com
 * Created Date: 2024-05-07
 */
/**
 * Compute line and item counters for the raw textarea content.
 *
 * @param {string} value - Raw editor content, one potential item per line.
 * @returns {{lineCount: number, validCount: number, emptyCount: number}} Editor statistics.
 */
function getStats(value) {
  const text = String(value || "").replace(/\r\n?/g, "\n");
  if (!text) {
    return { lineCount: 1, validCount: 0, emptyCount: 0 };
  }
  const lines = text.split("\n");
  const validCount = lines.filter((line) => line.trim()).length;
  return {
    lineCount: Math.max(1, lines.length),
    validCount,
    emptyCount: lines.length - validCount,
  };
}

/**
 * Format list editor statistics for the user-facing counter.
 *
 * @param {{validCount: number, emptyCount: number}} stats - Statistics returned by getStats.
 * @returns {string} Localized counter label.
 */
function formatCount(stats) {
  const itemLabel = `${stats.validCount} item${stats.validCount > 1 ? "s" : ""} valide${stats.validCount > 1 ? "s" : ""}`;
  if (stats.emptyCount > 0) {
    return `${itemLabel} · ${stats.emptyCount} ligne${stats.emptyCount > 1 ? "s" : ""} vide${stats.emptyCount > 1 ? "s" : ""} ignored${stats.emptyCount > 1 ? "s" : ""}`;
  }
  return itemLabel;
}

/**
 * Synchronize visual line numbers and item counters with the textarea state.
 *
 * @param {HTMLElement} root - Mounted List modal root.
 */
function syncEditor(root) {
  const textarea = root.querySelector("[data-list-textarea]");
  const lineNumbers = root.querySelector("[data-list-line-numbers]");
  const count = root.querySelector("[data-list-count]");
  if (!textarea) {
    return;
  }
  const stats = getStats(textarea.value);
  if (lineNumbers) {
    lineNumbers.textContent = Array.from({ length: stats.lineCount }, (_, index) => String(index + 1)).join("\n");
    lineNumbers.scrollTop = textarea.scrollTop;
  }
  if (count) {
    count.textContent = formatCount(stats);
  }
}

/**
 * Bind the List modal editor and keep textarea edits pending until Apply.
 *
 * @param {HTMLElement} root - Mounted modal root.
 * @param {object} api - Generic block UI API exposing block actions and modal close.
 */
export function mount(root, api) {
  const textarea = root.querySelector("[data-list-textarea]");
  const applyButton = root.querySelector("[data-list-action='apply']");
  if (!textarea) {
    return;
  }
  let dirty = false;

  /**
   * Mark modal textarea content as changed and enable Apply.
   */
  const markDirty = () => {
    dirty = true;
    if (applyButton) {
      applyButton.disabled = false;
    }
  };

  /**
   * Persist the raw one-item-per-line textarea content through block.py.
   */
  const apply = () => {
    if (!dirty) {
      return;
    }
    void api.applyAction("apply", { items_text: textarea.value }).then(() => {
      dirty = false;
      if (applyButton) {
        applyButton.disabled = true;
      }
    }).catch((error) => {
      api.log?.(`[error] Application Liste impossible: ${error.message}`);
    });
  };
  /**
   * Remove ignored empty lines while keeping the one-line-per-item format.
   */
  const removeEmpty = () => {
    textarea.value = String(textarea.value || "")
      .replace(/\r\n?/g, "\n")
      .split("\n")
      .filter((line) => line.trim())
      .join("\n");
    syncEditor(root);
    markDirty();
    textarea.focus();
  };
  /**
   * Clear all modal content and mark the editor dirty.
   */
  const clear = () => {
    textarea.value = "";
    syncEditor(root);
    markDirty();
    textarea.focus();
  };

  root.addEventListener("click", (event) => {
    const action = event.target.closest("[data-list-action]")?.dataset.listAction || "";
    if (!action) {
      return;
    }
    event.preventDefault();
    if (action === "apply") {
      apply();
      return;
    }
    if (action === "close") {
      api.close();
      return;
    }
    if (action === "remove-empty") {
      removeEmpty();
      return;
    }
    if (action === "clear") {
      clear();
    }
  });

  textarea.addEventListener("input", () => {
    syncEditor(root);
    markDirty();
  });
  textarea.addEventListener("scroll", () => syncEditor(root));
  textarea.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      apply();
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      api.close();
    }
  });

  syncEditor(root);
  textarea.focus();
}
