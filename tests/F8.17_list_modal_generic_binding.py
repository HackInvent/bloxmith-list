#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Role: Verifies generic modal field persistence for the list block.
# File Name: F8.17_list_modal_generic_binding.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2026-05-13
# -----------------------------------------------------------------------------

"""F8.17 - List modal explicit Apply binding.

The test opens the block-owned List modal in the browser and edits its textarea.
The block-owned modal JavaScript must keep edits local until the user clicks
Apply, then persist the normalized item list through the block action contract.
"""

# Test cases:
# - FB4 - Verify List modal textarea edits do not persist before Apply.
# - FB4 - Verify Apply normalizes textarea rows through the block-owned action.

from ui_smoke_common import (
    create_node,
    expect,
    graph_node_by_id,
    node_locator,
    run_playwright_smoke,
    wait_for_app_ready,
)
from block_test_packages import install_test_package, release_key


def test_list_modal_generic_binding(page, server, _blocking_errors) -> None:
    # The modal is a release module: the palette must offer the installed version.
    model = install_test_package(server, "list")
    wait_for_app_ready(page, server.base_url)
    node_id = create_node(page, release_key(model))
    node_locator(page, node_id).dblclick()
    page.wait_for_selector("[data-list-textarea]", timeout=10_000)
    page.wait_for_selector('[data-block-generic-modal-mounted="true"]', timeout=10_000)

    items_text = "alpha\nbeta"
    textarea = page.locator("[data-list-textarea]")
    textarea.fill(items_text)
    textarea.dispatch_event("input")
    page.wait_for_selector("[data-list-action='apply']:not([disabled])", timeout=10_000)
    node_before_apply = graph_node_by_id(page, node_id)
    expect(
        node_before_apply.get("config", {}).get("items") != ["alpha", "beta"],
        "The List modal must not persist the items before Apply.",
    )
    page.locator("[data-list-action='apply']").click()
    page.wait_for_function(
        """({ nodeId }) => {
          const node = [...(state?.nodes || new Map()).values()].find((item) => item.id === nodeId);
          return JSON.stringify(node?.config?.items || null) === JSON.stringify(["alpha", "beta"]);
        }""",
        arg={"nodeId": node_id},
        timeout=10_000,
    )

    node = graph_node_by_id(page, node_id)
    expect(node.get("config", {}).get("items") == ["alpha", "beta"], "The List modal did not persist the items after Apply.")


if __name__ == "__main__":
    run_playwright_smoke("F8.17_list_modal_generic_binding", test_list_modal_generic_binding)
