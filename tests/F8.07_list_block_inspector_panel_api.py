#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Role: Verifies list block inspector panel API behavior for the list block.
# File Name: F8.07_list_block_inspector_panel_api.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2024-11-08
# -----------------------------------------------------------------------------

"""F8.07 - UI modulaire du panneau inspecteur List.

Le test démarre un serveur isolé, demande le rendu du panneau inspecteur
`list` depuis `block.py`, vérifie que ses assets déclarés sont servis, puis
teste les actions structurées add/update/move/delete. Aucune donnée utilisateur
n'est modifiée hors du serveur de test.
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
        # Les surfaces sont des assets de release : le bundled kind n'en sert aucun.
        model = install_test_package(server, "list")
        key = quote(release_key(model), safe="")
        served = lambda payload, suffix: next(
            asset["path"] for asset in payload["assets"] if asset["path"].endswith(suffix))
        node = list_node(["alpha", {"nested": True}, 42], model["version"])
        rendered = surface_payload(server, model, node, "inspector_panel")
        html = str(rendered.get("html") or "")
        expect("data-list-inspector-root" in html, "Le HTML inspecteur List doit venir du bloc.")
        expect('data-list-inspector-tab="items"' in html, "Le panneau inspecteur List doit exposer l'onglet Liste.")
        expect('data-list-inspector-tab="attributes"' in html, "Le panneau inspecteur List doit exposer l'onglet Attributs.")
        expect('data-list-inspector-view="items"' in html, "Le panneau inspecteur List doit isoler la vue items.")
        expect('data-list-inspector-view="attributes"' in html, "Le panneau inspecteur List doit isoler la vue attributs.")
        expect("data-list-item-input" in html, "Le panneau inspecteur doit contenir les inputs d'items.")
        expect("data-list-inspector-apply" in html, "Le panneau inspecteur List doit exposer le bouton Appliquer la liste.")
        assets = rendered.get("assets") or []
        for asset_path in ("assets/css/inspector_panel.css", "assets/js/inspector_panel.js"):
            with urlopen(f"{server.base_url}/api/blocks/{key}/assets/{served(rendered, asset_path)}", timeout=5) as response:
                body = response.read().decode("utf-8")
            expect("list" in body.lower(), f"Asset inspecteur List non servi: {asset_path}")

        updated = ui_action(
            server,
            node,
            "inspector_update_items",
            {"items": ['{"x":1}', "beta"]},
        )
        items = updated.get("node_patch", {}).get("list", {}).get("items")
        expect(items == [{"x": 1}, "beta"], "Update inspecteur List doit parser les items côté block.py.")
        expect(updated.get("rerender_inspector") is False, "Update texte ne doit pas forcer un rerender inspecteur.")

        node = list_node(items)
        added = ui_action(server, node, "inspector_add_item", {"items": items})
        expect(added.get("node_patch", {}).get("list", {}).get("items") == [{"x": 1}, "beta", ""], "Add item incorrect.")
        expect(added.get("rerender_inspector") is True, "Add item doit forcer un rerender inspecteur.")

        moved = ui_action(server, list_node(["a", "b", "c"]), "inspector_move_item", {"items": ["a", "b", "c"], "index": 2, "direction": "up"})
        expect(moved.get("node_patch", {}).get("list", {}).get("items") == ["a", "c", "b"], "Move item incorrect.")

        deleted = ui_action(server, list_node(["a", "b", "c"]), "inspector_delete_item", {"items": ["a", "b", "c"], "index": 1})
        expect(deleted.get("node_patch", {}).get("list", {}).get("items") == ["a", "c"], "Delete item incorrect.")
    print("[ok] F8.07_list_block_inspector_panel_api")


if __name__ == "__main__":
    main()
