#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Role: Verifies list JSON output behavior for the list block.
# File Name: F5.01_list_json_output.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2024-08-26
# -----------------------------------------------------------------------------

"""F5.01 - List block with a JSON wrapper output.

The test runs a `list -> display` graph in an isolated server and checks that
the list block emits a JSON list of `{ "item": ... }` objects, consumable by
downstream blocks. JSON lines are parsed before wrapping.
"""

# Test cases:
# - FB1 - Run list -> display and verify the list output is application/json.
# - FB2/FB3 - Verify plain text, JSON object, and numeric lines are parsed, empty lines ignored, and wrapped as {"item": value}.

import json

from ui_smoke_common import (
    create_run_api,
    data_edge,
    display_node,
    expect,
    graph_payload,
    isolated_server,
    wait_for_run_terminal,
)


def list_node(items: list[str]) -> dict:
    return {
        "id": "list-1",
        "kind": "list",
        "title": "Liste test",
        "position": {"x": 80, "y": 120},
        "inputs": [],
        "outputs": [
            {
                "id": 1,
                "name": "liste",
                "title": "Liste",
                "emits": ["application/json", "message/*"],
                "multiplicity": "many",
            }
        ],
        "config": {"items": items},
    }


def main() -> None:
    with isolated_server() as server:
        document = graph_payload(
            "F5 List JSON",
            [list_node(["alpha", '{"toto":"toto"}', "42"]), display_node("display-1", "Affichage", 360, 120)],
            [data_edge("edge-list-display", "list-1", 1, "display-1", 1)],
        )
        created = create_run_api(server, document)
        run = wait_for_run_terminal(server, str(created.get("run_id") or ""))
        expect(run.get("status") == "success", "The list -> display run must succeed.")

        output = run.get("output_values", {}).get("list-1:1", {})
        parsed = json.loads(str(output.get("value") or "[]"))
        expect(
            parsed == [{"item": "alpha"}, {"item": {"toto": "toto"}}, {"item": 42}],
            "La sortie list wrapper n'est pas le JSON attendu.",
        )
        expect(output.get("content_type") == "application/json", "The list content_type must be application/json.")
        expect("alpha" in str(run.get("worker_rows", {}).get("display-1", {}).get("received") or ""), "Display does not receive the list.")
    print("[ok] F5.01_list_json_output")


if __name__ == "__main__":
    main()
