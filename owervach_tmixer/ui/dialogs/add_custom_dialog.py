"""Unified custom item creation modal (Heroes & Maps) with interactive Drag & Drop zone."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from owervach_tmixer.ui.styles import theme

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class _ImageDropZone(QFrame):
    """Interactive drag & drop box for selecting or dropping an image file."""

    file_selected = Signal(Path)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(140)
        self._image_path: Path | None = None
        self._is_drag_over = False

        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(6)
        self.main_layout.setAlignment(Qt.AlignCenter)

        # Empty state widgets
        self.icon_label = QLabel("🖼️")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        self.main_layout.addWidget(self.icon_label)

        self.text_label = QLabel("Arrastra una imagen aquí")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #E0E5F0; background: transparent; border: none;")
        self.main_layout.addWidget(self.text_label)

        self.sub_label = QLabel("o haz clic para explorar archivos (PNG, JPG, WEBP)")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet("font-size: 11px; font-weight: 500; color: #787D8C; background: transparent; border: none;")
        self.main_layout.addWidget(self.sub_label)

        # Preview widget (initially hidden)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background: transparent; border: none;")
        self.preview_label.hide()
        self.main_layout.addWidget(self.preview_label)

    def _update_style(self):
        accent = theme.accent()
        if self._is_drag_over:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(97, 171, 2, 0.12);
                    border: 2px dashed {accent};
                    border-radius: 8px;
                }}
            """)
        elif self._image_path:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #1A1C24;
                    border: 1.5px solid {accent};
                    border-radius: 8px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #16171D;
                    border: 2px dashed #303442;
                    border-radius: 8px;
                }
                QFrame:hover {
                    background-color: #1B1E26;
                    border-color: #4A5064;
                }
            """)

    def set_image_path(self, path: Path | None):
        self._image_path = path
        if path and path.exists():
            pix = QPixmap(str(path))
            if not pix.isNull():
                scaled = pix.scaled(90, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled)
                self.preview_label.show()
                self.icon_label.hide()
                self.text_label.setText(f"✅ {path.name}")
                self.text_label.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {theme.accent()}; background: transparent; border: none;")
                self.sub_label.setText("Haz clic o arrastra otra imagen para cambiarla")
            else:
                self._show_empty_state()
        else:
            self._show_empty_state()
        self._update_style()

    def _show_empty_state(self):
        self.preview_label.hide()
        self.icon_label.show()
        self.text_label.setText("Arrastra una imagen aquí")
        self.text_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #E0E5F0; background: transparent; border: none;")
        self.sub_label.setText("o haz clic para explorar archivos (PNG, JPG, WEBP)")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar imagen", "",
                "Imágenes (*.png *.jpg *.jpeg *.webp);;Todos los archivos (*.*)"
            )
            if path:
                p = Path(path)
                if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                    self.set_image_path(p)
                    self.file_selected.emit(p)
                else:
                    QMessageBox.warning(self, "Formato no válido", "Por favor selecciona una imagen PNG, JPG o WEBP.")
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                p = Path(url.toLocalFile())
                if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                    self._is_drag_over = True
                    self._update_style()
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._is_drag_over = False
        self._update_style()
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self._is_drag_over = False
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                p = Path(url.toLocalFile())
                if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                    self.set_image_path(p)
                    self.file_selected.emit(p)
                    event.acceptProposedAction()
                    return
        self._update_style()
        event.ignore()


class AddCustomItemDialog(QDialog):
    """Unified modal for creating a new custom Hero or Map."""

    def __init__(self, item_type: str = "hero", parent: QWidget | None = None):
        super().__init__(parent)
        self._item_type = item_type  # "hero" or "map"
        self._selected_image: Path | None = None

        title = "Añadir Héroe Personalizado" if item_type == "hero" else "Añadir Mapa Personalizado"
        self.setWindowTitle(title)
        self.resize(480, 520)
        self.setMinimumWidth(440)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        self.setStyleSheet("background-color: #121317;")

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. Header Banner
        header_icon = "🎭" if self._item_type == "hero" else "🗺️"
        header_title = "AÑADIR HÉROE NUEVO" if self._item_type == "hero" else "AÑADIR MAPA NUEVO"

        lbl_header = QLabel(f"{header_icon}  {header_title}")
        lbl_header.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 900;
            color: {theme.accent()};
            padding-bottom: 6px;
            border-bottom: 1px solid #282A33;
        """)
        layout.addWidget(lbl_header)

        # 2. Form Layout
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignLeft)

        # Name input
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("Ej: " + ("Hazard" if self._item_type == "hero" else "Hanaoka"))
        self.edit_name.setFixedHeight(36)
        self.edit_name.setStyleSheet("""
            QLineEdit {
                background-color: #181A22;
                border: 1px solid #2E3342;
                border-radius: 6px;
                padding: 0 12px;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit:focus { border-color: #61ab02; }
        """)

        name_lbl = QLabel("Nombre:")
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #D0D4E0;")
        form.addRow(name_lbl, self.edit_name)

        # Type ComboBox (Role or Mode)
        self.cb_type = QComboBox()
        self.cb_type.setFixedHeight(36)
        self.cb_type.setStyleSheet("""
            QComboBox {
                background-color: #181A22;
                border: 1px solid #2E3342;
                border-radius: 6px;
                padding: 0 12px;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 600;
            }
            QComboBox:focus { border-color: #61ab02; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox QAbstractItemView {
                background-color: #1E212B;
                border: 1px solid #333848;
                color: #FFFFFF;
                selection-background-color: #303648;
            }
        """)

        if self._item_type == "hero":
            self.cb_type.addItems(["Tanque", "Daño", "Apoyo"])
            type_label_txt = "Rol del héroe:"
        else:
            self.cb_type.addItems(["Control", "Escort", "Hybrid", "Push", "Flashpoint", "Clash", "Assault"])
            type_label_txt = "Modo de juego:"

        type_lbl = QLabel(type_label_txt)
        type_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #D0D4E0;")
        form.addRow(type_lbl, self.cb_type)

        layout.addLayout(form)

        # 3. Interactive Image Drop Zone
        img_sec_lbl = QLabel("Imagen / Retrato (Opcional):")
        img_sec_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #D0D4E0; margin-top: 4px;")
        layout.addWidget(img_sec_lbl)

        self.drop_zone = _ImageDropZone(self)
        self.drop_zone.file_selected.connect(self._on_image_selected)
        layout.addWidget(self.drop_zone)

        layout.addStretch(1)

        # 4. Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #1E2028;
                border: 1px solid #303442;
                border-radius: 6px;
                color: #C0C5D2;
                font-size: 13px;
                font-weight: 700;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #282C38; color: #FFFFFF; }
            QPushButton:pressed { background-color: #14151B; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel, 1)

        self.btn_save = QPushButton("💾 Guardar")
        self.btn_save.setProperty("primary", True)
        self.btn_save.setFixedHeight(40)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.accent()};
                border: 1px solid {theme.accent()};
                border-radius: 6px;
                color: #000000;
                font-size: 13px;
                font-weight: 800;
                padding: 0 18px;
            }}
            QPushButton:hover {{
                background-color: #72c704;
                border-color: #72c704;
            }}
            QPushButton:pressed {{ background-color: #4a8402; }}
        """)
        self.btn_save.clicked.connect(self._on_save_clicked)
        btn_box.addWidget(self.btn_save, 2)

        layout.addLayout(btn_box)

    def _on_image_selected(self, path: Path):
        self._selected_image = path

    def _on_save_clicked(self):
        name = self.edit_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Campo requerido", "Por favor introduce un nombre.")
            self.edit_name.setFocus()
            return
        self.accept()

    def get_data(self) -> tuple[str, str, Path | None]:
        """Returns (name, role_or_mode, image_path_or_none)."""
        name = self.edit_name.text().strip()
        type_val = self.cb_type.currentText()
        return name, type_val, self._selected_image
