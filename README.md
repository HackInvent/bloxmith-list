# List Block

<!-- block-metadata:start -->
[![Block version: 0.1.0](https://img.shields.io/badge/block-0.1.0-blue)](model.json)
[![BloxSmith compatibility: 1.0.9](https://img.shields.io/badge/BloxSmith-1.0.9-brightgreen)](compatibility.json)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

Verified BloxSmith versions: **1.0.9** (bundled-block tests; see [test evidence](compatibility.json)).
<!-- block-metadata:end -->


## Role

`list` is a source block that emits a configured list as JSON text. It is commonly paired with `iterator`.

## Files

- `block.py`: item normalization, editor formatting, modal/inspector actions, and runtime output.
- `model.json`: default list config and output declaration.
- `block_modal.html`, `inspector_panel.html`, `assets/`: list editing UI.
- `node_card.html`: block-owned canvas card body.

## Ports

- Outputs:
  - `liste` (`id: 1`): emits `application/json` and `message/*`.

The block has no inputs.

## Configuration

- `items`: list of values. Lines entered in the UI are normalized and serialized as JSON.

## Runtime Behavior

`execute_runtime()` normalizes `config.items`, serializes the list, and emits it on every output with `application/json` content type. `config.items` may be either a list or the line-based text produced by the editor.

## UI Behavior

The block supports a modal and an inspector for editing list items, formatting line numbers, counting items, and applying row-level actions. The inspector separates list editing from block attributes: the **List** tab owns item update/apply controls, while the **Attributes** tab keeps identity and block actions. Inspector text edits stay pending until the user clicks **Apply list**; add/delete/move row actions apply immediately because they change the row structure. Modal textarea edits also stay pending until **Apply**, then the block-owned `apply` action normalizes the final list value.

## Editor Display

The canvas card is rendered by this block through `node_card.html`. It exposes the configured item count while the shared editor shell keeps ports, dragging, status, and graph links generic.

## Modal

`block_modal.html` is owned by this block. It keeps the list editor and also exposes generic editable title/config bindings.

## Maintenance Notes

Keep editor formatting separate from runtime serialization. Runtime output should remain valid JSON for iterator compatibility.

## UI surface migration

- The modal declares `data-block-runtime-refresh="autonomous"` so line edits, scroll position, and draft values survive runtime polling.
- Modal behavior stays in `assets/js/block_modal.js`; inspector behavior stays in `assets/js/inspector_panel.js`.
- Durable item updates continue to go through block-owned UI actions.

## Compatibility policy

[compatibility.json](compatibility.json) records HackInvent's verified BloxSmith versions and test evidence. Only the versions listed above have been verified, using the block-owned suites in a **bundled-block test installation**. This is not a certification of managed-package installation, every browser/OS, or live provider availability. Other framework versions are unverified, not necessarily incompatible.

The block-version badge follows `model.json`, not a published Git tag. `unversioned` means that no block release version is declared; no number is inferred from the framework version. The framework still uses `model.json` for its runtime/install contract; the tester-owned JSON does not replace it. Official integration tests run in the private `bloxmith-blocs` workspace. Test helpers and the proprietary framework are not bundled in this public block repository.
