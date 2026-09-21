# -----------------------------------------------------------------------------
# Role: Implements the list block runtime and UI contract.
# File Name: block.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2024-07-20
# -----------------------------------------------------------------------------

from __future__ import annotations

from html import escape
import json
from typing import Any

from bloxsmith_app.block_api import (
    APPLICATION_JSON,
    BlockDefinition,
    BlockRuntimeContext,
    BlockRuntimeOutput,
    BlockRuntimeResult,
    render_inspector_template,
    render_node_card_template,
)


# Functional behavior:
# FB1 - Emit one JSON array from the configured line-based item editor.
# FB2 - Parse JSON-looking item lines before wrapping them as {"item": value}.
# FB3 - Ignore empty editor lines while keeping older string-list configurations compatible.
# FB4 - Render modal and inspector UI from block-owned templates and structured actions.
class ListBlock(BlockDefinition):
    """Autonomous block implementation for `ListBlock`."""
    kind = "list"

    def normalize_items(self, raw_items: Any) -> list[Any]:
        """Normalize raw list items into the block storage format.

        Args:
            raw_items: Raw value received from configuration or runtime input.
        """
        if raw_items is None:
            return []
        if isinstance(raw_items, str):
            text = raw_items.strip()
            if not text:
                return []
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return [self.parse_item_line(line) for line in raw_items.splitlines() if line.strip()]
            raw_items = parsed
        if not isinstance(raw_items, list):
            raw_items = [raw_items]

        return [self.parse_item_line(item) for item in raw_items]

    def parse_item_line(self, item: Any) -> Any:
        """Parse one List editor line into a typed item value.

        Args:
            item: Item value used by this block helper.
        """
        if not isinstance(item, str):
            return item
        text = item.strip()
        if not text:
            return ""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return item

    def wrap_items(self, raw_items: Any) -> list[dict[str, Any]]:
        """Wrap normalized List values in the runtime item envelope.

        Args:
            raw_items: Raw value received from configuration or runtime input.
        """
        return [{"item": item} for item in self.normalize_items(raw_items)]

    def serialize_items(self, raw_items: Any) -> str:
        """Serialize List items for editor and persistence use.

        Args:
            raw_items: Raw value received from configuration or runtime input.
        """
        return json.dumps(self.normalize_items(raw_items), ensure_ascii=False, indent=2)

    def serialize_output_items(self, raw_items: Any) -> str:
        """Serialize List items for runtime output publication.

        Args:
            raw_items: Raw value received from configuration or runtime input.
        """
        return json.dumps(self.wrap_items(raw_items), ensure_ascii=False, indent=2)

    def render_node_card(self, *, node: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Render the List canvas card body from the block-owned template."""

        count = len(self.normalize_items(self._raw_items_from_node(node)))
        return render_node_card_template(
            block=self,
            node=node,
            node_classes=["list-node"],
            replacements={
                "title": node.get("title") or self.default_title(),
                "preview": f"{count} item{'s' if count > 1 else ''}",
                "mode": "json list",
            },
        )

    def render_modal(self, *, node: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Render the block-owned modal HTML for the provided node payload.

        Args:
            node: Serialized graph node handled by the block.
            payload: Optional UI or runtime payload provided by the framework.
        """
        items = self.normalize_items(self._raw_items_from_node(node))
        items_text = "\n".join(self.format_item_for_editor(item) for item in items)
        template = (self.directory / "block_modal.html").read_text(encoding="utf-8")
        html = (
            template.replace("{{ title }}", escape(str(node.get("title") or self.default_title())))
            .replace("{{ item_count }}", str(len(items)))
            .replace("{{ items_text }}", escape(items_text))
            .replace("{{ line_numbers }}", escape(self.line_numbers_for_text(items_text)))
            .replace("{{ count_label }}", escape(self.format_items_count(items_text)))
        )
        return {
            "html": html,
            "context": {
                "node_id": str(node.get("id") or ""),
                "item_count": len(items),
            },
        }

    def handle_ui_action(
        self,
        *,
        node: dict[str, Any],
        action: str,
        values: dict[str, Any],
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle a block-owned UI action and return the updated node payload.

        Args:
            node: Serialized graph node handled by the block.
            action: Block-owned action name requested by the frontend.
            values: Values value used by this block helper.
            payload: Optional UI or runtime payload provided by the framework.
        """
        if action == "apply":
            return self._apply_items_action(node=node, values=values)
        if action in {"inspector_update_items", "inspector_add_item", "inspector_delete_item", "inspector_move_item"}:
            return self._apply_inspector_action(node=node, action=action, values=values)
        return {"error": f"unsupported_action:{action}"}

    def render_inspector_panel(self, *, node: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Render the block-owned inspector with separate list-editing and attributes tabs."""

        items = self.normalize_items(self._raw_items_from_node(node))
        template = (self.directory / "inspector_panel.html").read_text(encoding="utf-8")
        rows_html = self._render_inspector_rows(items)
        active_tab = str((payload or {}).get("inspector_tab") or "general").strip().lower()
        html = render_inspector_template(
            template=template.replace("{{ rows_html }}", rows_html),
            node={**node, "type": self.kind, "kind": self.kind},
            payload=payload,
            replacements={
                "list_active": "" if active_tab == "ports" else "active",
                "attributes_active": "",
            },
            show_duplicate=False,
        )
        return {
            "html": html,
            "context": {
                "node_id": str(node.get("id") or ""),
                "item_count": len(items),
                "full_panel": True,
            },
        }

    def _apply_items_action(self, *, node: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
        """Provide internal ListBlock behavior for `_apply_items_action`.

        Args:
            node: Serialized graph node handled by the block.
            values: Values value used by this block helper.
        """
        next_items = self.normalize_items(values.get("items_text", ""))
        return {
            "node_patch": {
                "list": {"items": next_items},
                "config": {"items": next_items},
            },
            "message": f"[list] {node.get('id') or self.kind}: items appliques: {len(next_items)}.",
            "close_modal": False,
            "rerender": False,
            "rerender_inspector": True,
        }

    def _apply_inspector_action(self, *, node: dict[str, Any], action: str, values: dict[str, Any]) -> dict[str, Any]:
        """Provide internal ListBlock behavior for `_apply_inspector_action`.

        Args:
            node: Serialized graph node handled by the block.
            action: Block-owned action name requested by the frontend.
            values: Values value used by this block helper.
        """
        items = self.normalize_items(values.get("items", self._raw_items_from_node(node)))
        if action == "inspector_add_item":
            items.append("")
        elif action == "inspector_delete_item":
            index = self._safe_index(values.get("index"), len(items))
            if index is not None:
                items.pop(index)
        elif action == "inspector_move_item":
            index = self._safe_index(values.get("index"), len(items))
            direction = str(values.get("direction") or "")
            if index is not None and direction == "up" and index > 0:
                items[index - 1], items[index] = items[index], items[index - 1]
            elif index is not None and direction == "down" and index < len(items) - 1:
                items[index], items[index + 1] = items[index + 1], items[index]
        return {
            "node_patch": {
                "list": {"items": items},
                "config": {"items": items},
            },
            "rerender_inspector": action != "inspector_update_items",
            "close_modal": False,
        }

    def _raw_items_from_node(self, node: dict[str, Any]) -> Any:
        """Provide internal ListBlock behavior for `_raw_items_from_node`.

        Args:
            node: Serialized graph node handled by the block.
        """
        list_config = node.get("list")
        if isinstance(list_config, dict) and "items" in list_config:
            return list_config.get("items")
        config = node.get("config")
        if isinstance(config, dict):
            return config.get("items")
        return []

    def format_item_for_editor(self, item: Any) -> str:
        """Format one List item for the line-based editor.

        Args:
            item: Item value used by this block helper.
        """
        if isinstance(item, str):
            return item
        if item is None:
            return "null"
        return json.dumps(item, ensure_ascii=False, separators=(",", ":"))

    def list_text_stats(self, value: str) -> dict[str, int]:
        """Compute editor statistics for the raw List text content.

        Args:
            value: Value to normalize, render, serialize, or process.
        """
        text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
        if not text:
            return {"line_count": 1, "valid_count": 0, "empty_count": 0}
        lines = text.split("\n")
        valid_count = sum(1 for line in lines if line.strip())
        return {
            "line_count": max(1, len(lines)),
            "valid_count": valid_count,
            "empty_count": len(lines) - valid_count,
        }

    def format_items_count(self, value: str) -> str:
        """Format List editor statistics for display.

        Args:
            value: Value to normalize, render, serialize, or process.
        """
        stats = self.list_text_stats(value)
        valid_count = stats["valid_count"]
        item_label = f"{valid_count} item{'s' if valid_count > 1 else ''} valide{'s' if valid_count > 1 else ''}"
        empty_count = stats["empty_count"]
        if empty_count:
            return (
                f"{item_label} · {empty_count} ligne{'s' if empty_count > 1 else ''} "
                f"vide{'s' if empty_count > 1 else ''} ignored{'s' if empty_count > 1 else ''}"
            )
        return item_label

    def line_numbers_for_text(self, value: str) -> str:
        """Build visual line numbers for the List text editor.

        Args:
            value: Value to normalize, render, serialize, or process.
        """
        stats = self.list_text_stats(value)
        return "\n".join(str(index + 1) for index in range(stats["line_count"]))

    def _safe_index(self, value: Any, size: int) -> int | None:
        """Provide internal ListBlock behavior for `_safe_index`.

        Args:
            value: Value to normalize, render, serialize, or process.
            size: Size value used by this block helper.
        """
        try:
            index = int(value)
        except (TypeError, ValueError):
            return None
        if index < 0 or index >= size:
            return None
        return index

    def _render_inspector_rows(self, items: list[Any]) -> str:
        """Render a block-owned HTML fragment used by the modal or inspector.

        Args:
            items: Items value used by this block helper.
        """
        if not items:
            return '<div class="ports-editor-empty">Empty list. Add an item to emit data.</div>'
        rows = []
        total = len(items)
        for index, item in enumerate(items):
            item_text = escape(self.format_item_for_editor(item))
            rows.append(
                "\n".join(
                    [
                        f'<div class="list-item-row" data-list-item-row data-index="{index}">',
                        (
                            f'  <textarea rows="2" data-list-item-input data-index="{index}" '
                            f'placeholder="Item {index + 1}">{item_text}</textarea>'
                        ),
                        '  <div class="list-item-actions">',
                        (
                            f'    <button class="ghost-btn port-order-btn" type="button" data-list-inspector-action="move" '
                            f'data-direction="up" data-index="{index}"{" disabled" if index == 0 else ""}>↑</button>'
                        ),
                        (
                            f'    <button class="ghost-btn port-order-btn" type="button" data-list-inspector-action="move" '
                            f'data-direction="down" data-index="{index}"{" disabled" if index >= total - 1 else ""}>↓</button>'
                        ),
                        (
                            f'    <button class="ghost-btn port-delete-btn" type="button" '
                            f'data-list-inspector-action="delete" data-index="{index}">Delete</button>'
                        ),
                        "  </div>",
                        "</div>",
                    ]
                )
            )
        return "\n".join(rows)

    def execute_runtime(self, context: BlockRuntimeContext) -> BlockRuntimeResult:
        """Execute the block through the generic runtime context and return runtime outputs.

        Args:
            context: Generic runtime context injected by the execution engine.
        """
        items = self.normalize_items(context.config.get("items", []))
        payload = json.dumps(self.wrap_items(items), ensure_ascii=False, indent=2)
        outputs = [
            BlockRuntimeOutput(
                port_id=int(getattr(port, "id", 0) or 0),
                port_name=str(getattr(port, "name", "") or ""),
                value=payload,
                content_type=APPLICATION_JSON,
            )
            for port in context.output_ports
        ]
        return BlockRuntimeResult(
            status="success",
            outputs=outputs,
            logs=[f"[list] {context.node_id} -> {len(items)} item(s) emitted as JSON wrapper items."],
            last_message=payload,
            content_type=APPLICATION_JSON,
            worker_received=f"{len(items)} item(s)",
            metadata={"item_count": len(items)},
        )
