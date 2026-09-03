"""Application entry point with global dark palette enforcement for Wayland/Hyprland & Windows."""

from __future__ import annotations

import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QIcon
from PySide6.QtWidgets import QApplication

from owervach_tmixer import APP_TITLE, ORG_NAME
from owervach_tmixer.ui.dialogs.settings_dialog import SettingsDialog
from owervach_tmixer.ui.main_window import QWIDGETSIZE_MAX, MainWindow, create_splash_screen
from owervach_tmixer.ui.styles import theme

__all__ = ["MainWindow", "SettingsDialog", "QWIDGETSIZE_MAX", "main"]


def main():
    # 0. Registrar AppUserModelID en Windows ANTES de QApplication para forzar icono blanco en Barra de Tareas y Alt+Tab
    if sys.platform == "win32":
        try:
            import ctypes
            app_id = "sathara.overwatch.teammixer.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    app = QApplication(sys.argv)
    app.setDesktopFileName("owervach-tmixer")

    from owervach_tmixer.utils import get_resource_path

    # Prioridad absoluta: Icono artesanal blanco IcoFX
    icon_candidates = [
        "assets/overwatch-logo-white.ico",
        "assets/overwatch-logo-white.png",
        "assets/overwatch-logo-white.svg",
        "assets/overwatch-logo.svg",
        "assets/overwatch-logo.png",
        "assets/overwatch-logo.ico",
        "assets/icon.svg",
    ]
    icon_path = None
    for cand in icon_candidates:
        p = get_resource_path(cand)
        if p.exists():
            icon_path = p
            break

    app_icon = QIcon(str(icon_path)) if icon_path and icon_path.exists() else None
    if app_icon and not app_icon.isNull():
        app.setWindowIcon(app_icon)

    app.setApplicationName(APP_TITLE)
    app.setOrganizationName(ORG_NAME)

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#121316"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#16171E"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1F222A"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#16171E"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1E2028"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#61ab02"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    app.setStyleSheet(theme.build_stylesheet())

    window = MainWindow()
    if app_icon and not app_icon.isNull():
        window.setWindowIcon(app_icon)

    if sys.platform == "win32":
        try:
            import ctypes
            # 1. Desbloqueo a 1ms para fluidez a 144Hz / 240Hz nativos
            ctypes.windll.winmm.timeBeginPeriod(1)
            # 2. Blindaje de modo oscuro nativo en Windows
            hwnd = int(window.winId())
            dark_flag = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark_flag), ctypes.sizeof(dark_flag))
            dark_brush = ctypes.windll.gdi32.CreateSolidBrush(0x00161312)
            set_class_long = getattr(ctypes.windll.user32, "SetClassLongPtrW", ctypes.windll.user32.SetClassLongW)
            set_class_long(hwnd, -10, dark_brush)
        except Exception:
            pass

    if getattr(window, "_start_maximized", False):
        window.showMaximized()
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
