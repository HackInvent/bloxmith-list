#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Role: Verifies list block modal API behavior for the list block.
# File Name: F8.06_list_block_modal_api.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2024-10-02
# -----------------------------------------------------------------------------

"""F8.06 - UI modulaire du modal List.

Le test démarre un serveur isolé, demande le rendu du modal `list` depuis
`block.py`, vérifie que ses assets déclarés sont servis, puis applique une
modification sous forme JSON structurée. Aucune donnée utilisateur n'est
modifiée hors du serveur de test.
"""

# Test cases:
# - FB4 - Render the List modal through the block API and verify editor controls are present.
# - FB3/FB4 - Apply line-based item edits through a structured UI action and verify the node patch keeps compatible saved data.
# - FB4 - Verify modal assets are declared and served from the block package.

from __future__ import annotations

from urllib.request import urlopen

from ui_smoke_common import expect, http_json, isolated_server


def main() -> None:
    with isolated_server() as server:
        node = {
            "id": "list-1",
            "kind": "list",
            "type": "list",
            "title": "Liste API",
            "list": {"items": ["alpha", '{"nested":true}', "42"]},
            "config": {"items": ["alpha", '{"nested":true}', "42"]},
        }

        rendered = http_json(server.base_url, "/api/blocks/list/modal", method="POST", payload={"node": node})
        modal_html = str(rendered.get("html") or "")
        expect("data-list-textarea" in modal_html, "Le HTML du modal List doit venir du bloc.")
        expect("data-block-runtime-refresh=\"autonomous\"" in modal_html, "Le modal List doit gérer son refresh runtime.")
        expect("data-block-apply" in modal_html, "Le modal List doit exposer le bouton Appliquer.")
        expect(
            "data-block-config-field=\"items\"" not in modal_html,
            "Le modal List ne doit plus autosauvegarder le textarea via binding generique.",
        )
        assets = rendered.get("assets") or []
        expect(
            {"kind": "css", "path": "assets/css/block_modal.css"} in assets,
            "Le CSS du modal List doit être déclaré par le bloc.",
        )
        expect(
            {"kind": "js", "path": "assets/js/block_modal.js"} in assets,
            "Le JS du modal List doit être déclaré par le bloc.",
        )

        for asset_path in ("assets/css/block_modal.css", "assets/js/block_modal.js"):
            with urlopen(f"{server.base_url}/api/blocks/list/assets/{asset_path}", timeout=5) as response:
                body = response.read().decode("utf-8")
            expect("list" in body.lower(), f"Asset List non servi: {asset_path}")

        applied = http_json(
            server.base_url,
            "/api/blocks/list/ui-action",
            method="POST",
            payload={
                "node": node,
                "action": "apply",
                "values": {"items_text": '{"item":"toto"}\n42\n\ntexte long'},
            },
        )
        items = applied.get("node_patch", {}).get("list", {}).get("items")
        expect(items == [{"item": "toto"}, 42, "texte long"], "Le bloc List doit parser le JSON structuré côté block.py.")
        expect(applied.get("close_modal") is False, "Appliquer ne doit pas fermer le modal List.")
    print("[ok] F8.06_list_block_modal_api")


if __name__ == "__main__":
    main()
