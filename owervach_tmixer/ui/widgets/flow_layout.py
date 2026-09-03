"""Flow layout wrapper with dynamic widget insertion, removal, parent binding and wrapping."""

from __future__ import annotations

from PySide6.QtCore import QMargins, QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QLayoutItem, QWidget, QWidgetItem


class _Item:
    def __init__(self, item: QLayoutItem):
        self.item = item
        self.geometry = QRect()


class FlowLayout(QLayout):
    def __init__(
        self,
        parent: QWidget | None = None,
        margin: int = 0,
        h_spacing: int = 6,
        v_spacing: int = 6,
    ):
        super().__init__(parent)
        self._items: list[_Item] = []
        self.setContentsMargins(margin, margin, margin, margin)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing

    def __del__(self):
        while getattr(self, "_items", None):
            item = self._items.pop().item
            if hasattr(item, "deleteLater"):
                item.deleteLater()

    def addItem(self, item: QLayoutItem):
        if item.widget() and self.parentWidget():
            item.widget().setParent(self.parentWidget())
        self._items.append(_Item(item))

    def insertWidget(self, index: int, widget: QWidget):
        if self.parentWidget():
            widget.setParent(self.parentWidget())
        item = QWidgetItem(widget)
        if index < 0 or index >= len(self._items):
            self._items.append(_Item(item))
        else:
            self._items.insert(index, _Item(item))
        self.update()

    def removeWidget(self, widget: QWidget):
        for i, entry in enumerate(self._items):
            if entry.item.widget() == widget:
                self._items.pop(i)
                self.update()
                break

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items[index].item
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items.pop(index).item
        return None

    def find_index_at_pos(self, pos: QPoint) -> int:
        for i, entry in enumerate(self._items):
            if pos.y() < entry.geometry.top():
                return i
            if entry.geometry.top() <= pos.y() <= entry.geometry.bottom() + self._v_spacing:
                if pos.x() < entry.geometry.center().x():
                    return i
        return len(self._items)

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for entry in self._items:
            wid = entry.item.widget()
            if wid and not wid.isVisible():
                continue
            size = size.expandedTo(entry.item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        margins: QMargins = self.contentsMargins()
        effective = rect.adjusted(
            margins.left(), margins.top(), -margins.right(), -margins.bottom()
        )
        x = effective.x()
        y = effective.y()
        line_height = 0
        for entry in self._items:
            wid = entry.item.widget()
            if wid and not wid.isVisible():
                continue
            hint = entry.item.sizeHint()
            w = hint.width()
            h = hint.height()
            next_x = x + w + self._h_spacing
            if next_x - self._h_spacing > effective.right() and line_height > 0:
                x = effective.x()
                y = y + line_height + self._v_spacing
                next_x = x + w + self._h_spacing
                line_height = 0
            if not test_only:
                entry.geometry = QRect(QPoint(x, y), QSize(w, h))
                entry.item.setGeometry(entry.geometry)
            x = next_x
            line_height = max(line_height, h)
        return y + line_height - rect.y() + margins.bottom()
