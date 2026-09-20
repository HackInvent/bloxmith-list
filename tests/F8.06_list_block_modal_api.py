#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Role: Verifies list block modal API behavior for the list block.
# File Name: F8.06_list_block_modal_api.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2024-10-02
# -----------------------------------------------------------------------------

"""F8.06 - Modular UI of the List modal.

The test starts an isolated server, renders the `list` modal from `block.py`,
checks that its declared assets are served, then applies a change as structured
JSON. No user data is modified outside the test server.
"""

# Test cases:
# - FB4 - Render the List modal through the block API and verify editor controls are present.
# - FB3/FB4 - Apply line-based item edits through a structured UI action and verify the node patch keeps compatible saved data.
# - FB4 - Verify modal assets are declared and served from the block package.

from __future__ import annotations

from urllib.request import urlopen

from ui_smoke_common import expect, http_json, isolated_server
from urllib.parse import quote
from block_test_packages import install_test_package, release_key, surface_payload


def main() -> None:
    with isolated_server() as server:
        # Surfaces are release assets: a bundled kind serves none of them.
        model = install_test_package(server, "list")
        key = quote(release_key(model), safe="")
        served = lambda payload, suffix: next(
            asset["path"] for asset in payload["assets"] if asset["path"].endswith(suffix))
        node = {
            "id": "list-1",
            "kind": "list",
            "type": "list",
            "block_version": model["version"],
            "title": "Liste API",
            "list": {"items": ["alpha", '{"nested":true}', "42"]},
            "config": {"items": ["alpha", '{"nested":true}', "42"]},
        }

        rendered = surface_payload(server, model, node, "modal")
        modal_html = str(rendered.get("html") or "")
        expect("data-list-textarea" in modal_html, "The List modal HTML must come from the block.")
        expect("data-block-runtime-refresh=\"autonomous\"" in modal_html, "The List modal must own its runtime refresh.")
        expect("data-block-apply" in modal_html, "The List modal must expose the Apply button.")
        expect(
            "data-block-config-field=\"items\"" not in modal_html,
            "The List modal must no longer autosave the textarea through the generic binding.",
        )
        assets = rendered.get("assets") or []
        for asset_path in ("assets/css/block_modal.css", "assets/js/block_modal.js"):
            with urlopen(f"{server.base_url}/api/blocks/{key}/assets/{served(rendered, asset_path)}", timeout=5) as response:
                body = response.read().decode("utf-8")
            expect("list" in body.lower(), f"List asset not served: {asset_path}")

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
        expect(items == [{"item": "toto"}, 42, "texte long"], "The List block must parse the structured JSON in block.py.")
        expect(applied.get("close_modal") is False, "Apply must not close the List modal.")
    print("[ok] F8.06_list_block_modal_api")


if __name__ == "__main__":
    main()
