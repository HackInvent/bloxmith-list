/**
 * Role: Mounts the list block inspector panel frontend.
 * File Name: inspector_panel.js
 * Author: Alexandre EL
 * Email: alex@hackinvent.com
 * Created Date: 2024-06-13
 */
/**
 * Collect raw list item editor values from the inspector rows.
 *
 * @param {HTMLElement} root - Mounted list inspector root.
 * @returns {string[]} Item values in current visual order.
 */
function collectItems(root) {
  return [...root.querySelectorAll("[data-list-item-input]")].map((input) => input.value);
}

/**
 * Persist the current list item values through the block UI action contract.
 *
 * @param {HTMLElement} root - Mounted list inspector root.
 * @param {object} api - Generic block UI API exposing block actions.
 * @returns {Promise<object>} Action response from the GraphController pipeline.
 */
function applyItems(root, api) {
  return api.applyAction("inspector_update_items", { items: collectItems(root) });
}

/**
 * Switch the block-owned List inspector subtab without involving the generic inspector renderer.
 *
 * @param {HTMLElement} root - Mounted list inspector root.
 * @param {string} tab - Local List inspector tab name.
 */
function selectLocalTab(root, tab) {
  const nextTab = tab === "attributes" ? "attributes" : "items";
  root.querySelectorAll("[data-list-inspector-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.listInspectorTab === nextTab);
  });
  root.querySelectorAll("[data-list-inspector-view]").forEach((view) => {
    view.classList.toggle("hidden", view.dataset.listInspectorView !== nextTab);
  });
}

/**
 * Bind item row editing so text changes stay pending until Apply.
 *
 * @param {HTMLElement} root - Mounted inspector root.
 * @param {object} api - Generic block UI API exposing block actions.
 */
export function mount(root, api) {
  const applyButton = root.querySelector("[data-list-inspector-apply]");
  let dirty = false;
  selectLocalTab(root, "items");

  /**
   * Mark the inspector list rows as changed and enable Apply.
   */
  const markDirty = () => {
    dirty = true;
    if (applyButton) {
      applyButton.disabled = false;
    }
  };

  /**
   * Persist pending item row edits through the block UI action contract.
   */
  const flushInput = () => {
    if (!dirty) {
      return;
    }
    void applyItems(root, api).then(() => {
      dirty = false;
      if (applyButton) {
        applyButton.disabled = true;
      }
    }).catch((error) => {
      api.log?.(`[error] Mise à jour Liste impossible: ${error.message}`);
    });
  };

  root.addEventListener("input", (event) => {
    if (!event.target.closest("[data-list-item-input]")) {
      return;
    }
    markDirty();
  });

  root.addEventListener("change", (event) => {
    if (event.target.closest("[data-list-item-input]")) {
      markDirty();
    }
  });

  root.addEventListener("click", (event) => {
    const tabButton = event.target.closest("[data-list-inspector-tab]");
    if (tabButton) {
      event.preventDefault();
      selectLocalTab(root, tabButton.dataset.listInspectorTab || "items");
      return;
    }
    if (event.target.closest("[data-list-inspector-apply]")) {
      event.preventDefault();
      flushInput();
      return;
    }
    const button = event.target.closest("[data-list-inspector-action]");
    if (!button || button.disabled) {
      return;
    }
    event.preventDefault();
    const action = button.dataset.listInspectorAction || "";
    const index = Number.parseInt(button.dataset.index || "-1", 10);
    const items = collectItems(root);
    let payloadAction = "";
    const values = { items };

    if (action === "add") {
      payloadAction = "inspector_add_item";
    } else if (action === "delete") {
      payloadAction = "inspector_delete_item";
      values.index = index;
    } else if (action === "move") {
      payloadAction = "inspector_move_item";
      values.index = index;
      values.direction = button.dataset.direction || "";
    }
    if (!payloadAction) {
      return;
    }
    void api.applyAction(payloadAction, values).catch((error) => {
      api.log?.(`[error] Action Liste impossible: ${error.message}`);
    });
  });
}
