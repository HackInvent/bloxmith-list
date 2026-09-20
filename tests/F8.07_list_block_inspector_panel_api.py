#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Role: Verifies list block inspector panel API behavior for the list block.
# File Name: F8.07_list_block_inspector_panel_api.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2024-11-08
# -----------------------------------------------------------------------------

"""F8.07 - Modular UI of the List inspector panel.

The test starts an isolated server, renders the `list` inspector panel from
`block.py`, checks that its declared assets are served, then exercises the
structured add/update/move/delete actions. No user data is modified outside the
test server.
"""

# Test cases:
# - FB4 - Render the List inspector panel through the block API.
# - FB4 - Verify the inspector separates list editing from block attributes through block-owned tabs.
# - FB3/FB4 - Apply add/update/delete inspector actions and verify item patches keep line-based semantics.
# - FB4 - Verify inspector assets are served by the List block package.

from __future__ import annotations

from urllib.request import urlopen

from ui_smoke_common import expect, http_json, isolated_server
from urllib.parse import quote
from block_test_packages import install_test_package, release_key, surface_payload


def list_node(items: list[object], version: str | None = None) -> dict:
    return {
        "id": "list-1",
        "kind": "list",
        "type": "list",
        **({"block_version": version} if version else {}),
        "title": "Liste Inspecteur",
        "list": {"items": items},
        "config": {"items": items},
    }


def ui_action(server, node: dict, action: str, values: dict) -> dict:
    return http_json(
        server.base_url,
        "/api/blocks/list/ui-action",
        method="POST",
        payload={"node": node, "action": action, "values": values},
    )


def main() -> None:
    with isolated_server() as server:
        # Surfaces are release assets: a bundled kind serves none of them.
        model = install_test_package(server, "list")
        key = quote(release_key(model), safe="")
        served = lambda payload, suffix: next(
            asset["path"] for asset in payload["assets"] if asset["path"].endswith(suffix))
        node = list_node(["alpha", {"nested": True}, 42], model["version"])
        rendered = surface_payload(server, model, node, "inspector_panel")
        html = str(rendered.get("html") or "")
        expect("data-list-inspector-root" in html, "The List inspector HTML must come from the block.")
        expect('data-list-inspector-tab="items"' in html, "The List inspector panel must expose the List tab.")
        expect('data-list-inspector-tab="attributes"' in html, "The List inspector panel must expose the Attributes tab.")
        expect('data-list-inspector-view="items"' in html, "The List inspector panel must isolate the items view.")
        expect('data-list-inspector-view="attributes"' in html, "The List inspector panel must isolate the attributes view.")
        expect("data-list-item-input" in html, "The inspector panel must contain the item inputs.")
        expect("data-list-inspector-apply" in html, "The List inspector panel must expose the Apply the list button.")
        assets = rendered.get("assets") or []
        for asset_path in ("assets/css/inspector_panel.css", "assets/js/inspector_panel.js"):
            with urlopen(f"{server.base_url}/api/blocks/{key}/assets/{served(rendered, asset_path)}", timeout=5) as response:
                body = response.read().decode("utf-8")
            expect("list" in body.lower(), f"List inspector asset not served: {asset_path}")

        updated = ui_action(
            server,
            node,
            "inspector_update_items",
            {"items": ['{"x":1}', "beta"]},
        )
        items = updated.get("node_patch", {}).get("list", {}).get("items")
        expect(items == [{"x": 1}, "beta"], "The List inspector update must parse the items in block.py.")
        expect(updated.get("rerender_inspector") is False, "A text update must not force an inspector rerender.")

        node = list_node(items)
        added = ui_action(server, node, "inspector_add_item", {"items": items})
        expect(added.get("node_patch", {}).get("list", {}).get("items") == [{"x": 1}, "beta", ""], "Add item incorrect.")
        expect(added.get("rerender_inspector") is True, "Add item must force an inspector rerender.")

        moved = ui_action(server, list_node(["a", "b", "c"]), "inspector_move_item", {"items": ["a", "b", "c"], "index": 2, "direction": "up"})
        expect(moved.get("node_patch", {}).get("list", {}).get("items") == ["a", "c", "b"], "Move item incorrect.")

        deleted = ui_action(server, list_node(["a", "b", "c"]), "inspector_delete_item", {"items": ["a", "b", "c"], "index": 1})
        expect(deleted.get("node_patch", {}).get("list", {}).get("items") == ["a", "c"], "Delete item incorrect.")
    print("[ok] F8.07_list_block_inspector_panel_api")


if __name__ == "__main__":
    main()
