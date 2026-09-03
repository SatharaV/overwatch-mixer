"""Modal prompts for adding tags and selecting categories."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.ui.styles import theme


class AddTagPromptDialog(QDialog):
    """Modal prompt to add a tag with existing category autocomplete and Enter support."""

    def __init__(self, title_name: str, existing_categories: list[str], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"Etiqueta para {title_name}")
        self.resize(380, 230)
        self.setStyleSheet("background-color: #16171B; color: #FFFFFF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel(f"Asignar etiqueta a: <b>{title_name}</b>")
        lbl.setStyleSheet(f"font-size: 13px; color: {theme.accent()};")
        layout.addWidget(lbl)

        hint = QLabel("Escribe una etiqueta simple (ej. 'OP', 'Tóxico') O una categoría con valor (ej. 'Molestia' y valor '10').")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 11px; color: #9A9FA8;")
        layout.addWidget(hint)

        self.cb_category = QComboBox()
        self.cb_category.setView(QListView())
        self.cb_category.setEditable(True)
        self.cb_category.lineEdit().setPlaceholderText("Etiqueta o Categoría (ej. Tier, Molestia, OP)")
        for cat in existing_categories:
            self.cb_category.addItem(cat)
        if self.cb_category.lineEdit():
            self.cb_category.lineEdit().returnPressed.connect(self._on_save_clicked)
        layout.addWidget(self.cb_category)

        self.edit_val = QLineEdit()
        self.edit_val.setPlaceholderText("Valor o puntuación opcional (ej. 10, God, S, Mucho)")
        self.edit_val.returnPressed.connect(self._on_save_clicked)
        layout.addWidget(self.edit_val)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("background-color: #22252D; border: 1px solid #333845; border-radius: 6px; padding: 7px 14px; font-weight: 600;")
        btn_box.addWidget(btn_cancel)

        btn_ok = QPushButton("Guardar Etiqueta")
        btn_ok.setProperty("primary", True)
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self._on_save_clicked)
        btn_ok.setStyleSheet(f"background-color: {theme.accent()}; color: #000; font-weight: 800; border-radius: 6px; padding: 7px 16px;")
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)

    def _on_save_clicked(self):
        key = self.cb_category.currentText().strip()
        val = self.edit_val.text().strip()
        if not key and not val:
            QMessageBox.warning(self, "Campo requerido", "Por favor escribe al menos el nombre de la etiqueta.")
            return
        self.accept()

    def get_data(self) -> tuple[str, str]:
        key = self.cb_category.currentText().strip()
        val = self.edit_val.text().strip()
        if key and not val:
            return key, "✓"
        if val and not key:
            return val, "✓"
        return key, val


def QInputDialog_getItem(parent, title: str, label: str, items: list[str]) -> tuple[str, bool]:
    """Helper dialog to pick an item from a combobox cleanly."""
    diag = QDialog(parent)
    diag.setWindowTitle(title)
    diag.resize(320, 140)
    diag.setStyleSheet("background-color: #16171B; color: #FFF;")
    layout = QVBoxLayout(diag)
    layout.addWidget(QLabel(label))
    cb = QComboBox()
    cb.setView(QListView())
    cb.addItems(items)
    cb.setStyleSheet("background-color: #1F222A; border: 1px solid #333845; padding: 6px; border-radius: 5px;")
    layout.addWidget(cb)
    btns = QHBoxLayout()
    btn_c = QPushButton("Cancelar")
    btn_c.clicked.connect(diag.reject)
    btn_ok = QPushButton("Aceptar")
    btn_ok.clicked.connect(diag.accept)
    btn_ok.setStyleSheet(f"background-color: {theme.accent()}; color: #000; font-weight: 800;")
    btns.addWidget(btn_c)
    btns.addWidget(btn_ok)
    layout.addLayout(btns)
    ok = (diag.exec() == QDialog.DialogCode.Accepted)
    return cb.currentText(), ok
