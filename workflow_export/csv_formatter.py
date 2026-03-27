from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation


def _format_price(value: object) -> str:
    if value in (None, ""):
        return "N/A"
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "N/A"
    return f"R$ {amount:.2f}"


def _latest_editor(version_history: dict) -> str:
    entries = version_history.get("entries") if isinstance(version_history, dict) else None
    if not isinstance(entries, list) or not entries:
        return "system"
    latest = entries[-1] if isinstance(entries[-1], dict) else {}
    editor = str(latest.get("actor_id") or latest.get("actorId") or "").strip()
    return editor or "system"


def format_as_csv(records: list[dict], version_context: dict) -> str:
    """Render normalized record list as CSV for business validation and download."""
    output = io.StringIO()
    fieldnames = [
        "Item",
        "Category",
        "Quantity",
        "Unit",
        "Price",
        "Source",
        "URL",
        "Version",
        "Last Edited By",
        "Notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\r\n")
    writer.writeheader()

    by_material = version_context.get("byMaterial") if isinstance(version_context, dict) else {}
    by_material = by_material if isinstance(by_material, dict) else {}

    sortable = []
    for record in records:
        if not isinstance(record, dict):
            continue
        material_id = str(record.get("materialId") or "")
        latest_values = record.get("latestValues") if isinstance(record.get("latestValues"), dict) else {}
        sortable.append((str(latest_values.get("name") or material_id), material_id, latest_values, record))

    for _, material_id, latest_values, record in sorted(sortable, key=lambda x: x[0].lower()):
        history = by_material.get(material_id) if isinstance(by_material.get(material_id), dict) else {}
        writer.writerow(
            {
                "Item": latest_values.get("name") or latest_values.get("title") or material_id,
                "Category": latest_values.get("category") or "",
                "Quantity": latest_values.get("quantity") or "",
                "Unit": latest_values.get("unit") or "un",
                "Price": _format_price(latest_values.get("price") or record.get("bestPrice")),
                "Source": record.get("preferredSource") or latest_values.get("source") or "",
                "URL": record.get("preferredUrl") or latest_values.get("url") or "",
                "Version": int(history.get("latestVersion", 0)) if isinstance(history, dict) else 0,
                "Last Edited By": _latest_editor(history),
                "Notes": latest_values.get("notes") or "",
            }
        )

    return output.getvalue()
