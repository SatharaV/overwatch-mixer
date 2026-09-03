"""Drag & drop helpers shared by the player cells, team panels, and dock panels."""

from __future__ import annotations

import json
from typing import Set

from PySide6.QtCore import QMimeData, QEvent, Qt
from PySide6.QtWidgets import QWidget

DND_MIME = "application/x-owervach-player"

_active_highlights: set[QWidget] = set()
_registered_slots: set[QWidget] = set()


def register_slot(widget: QWidget):
    _registered_slots.add(widget)


def unregister_slot(widget: QWidget):
    _registered_slots.discard(widget)


def make_payload(kind: str, name: str, team=None, idx=None, names=None) -> dict:
    payload = {"kind": kind, "name": name}
    if team is not None:
        payload["team"] = team
    if idx is not None:
        payload["idx"] = idx
    if names is not None:
        payload["names"] = names
    return payload


def payload_to_mime(payload: dict) -> QMimeData:
    mime = QMimeData()
    mime.setData(DND_MIME, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    return mime


def payload_from(mime: QMimeData) -> dict | None:
    if mime is None or not mime.hasFormat(DND_MIME):
        return None
    try:
        data = json.loads(bytes(mime.data(DND_MIME)).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    if data.get("kind") in ("slot", "bench", "saved", "bench_multi", "saved_multi") and data.get("name"):
        return data
    return None


def set_drop_highlight(widget: QWidget, on: bool):
    """Toggle the [dropTarget] dynamic property, unpolish/polish, and force an immediate repaint."""
    if on:
        _active_highlights.add(widget)
    else:
        _active_highlights.discard(widget)

    widget.setProperty("dropTarget", bool(on))
    style = widget.style()
    if style:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def clear_all_drop_highlights():
    """Globally purge any lingering drop target and hover highlights, forcing immediate repaints."""
    while _active_highlights:
        w = _active_highlights.pop()
        try:
            w.setProperty("dropTarget", False)
            w.setProperty("hovered", False)
            w.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, False)
            style = w.style()
            if style:
                style.unpolish(w)
                style.polish(w)
            w.update()
        except Exception:
            pass

    for w in list(_registered_slots):
        try:
            needs_update = False
            if w.property("dropTarget"):
                w.setProperty("dropTarget", False)
                needs_update = True
            if w.property("hovered"):
                w.setProperty("hovered", False)
                needs_update = True
            w.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, False)
            if needs_update:
                style = w.style()
                if style:
                    style.unpolish(w)
                    style.polish(w)
                w.update()
        except Exception:
            pass
