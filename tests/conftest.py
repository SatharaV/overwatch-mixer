"""Shared fixtures for tests (isolated temporary directories for Windows & Linux)."""

import os
import platformdirs
import pytest
from PySide6.QtWidgets import QMessageBox

os.environ["QT_QPA_PLATFORM"] = os.environ.get("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def isolate_storage(tmp_path, monkeypatch):
    """Aisla 100% los datos tanto en Windows como en Linux para no tocar nunca AppData real."""
    test_data = tmp_path / "data"
    test_config = tmp_path / "config"
    test_data.mkdir(parents=True, exist_ok=True)
    test_config.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        platformdirs,
        "user_data_dir",
        lambda appname=None, *a, **k: str(test_data / (appname or "app")),
    )
    monkeypatch.setattr(
        platformdirs,
        "user_config_dir",
        lambda appname=None, *a, **k: str(test_config / (appname or "app")),
    )

    monkeypatch.setenv("XDG_DATA_HOME", str(test_data))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(test_config))

    return test_data / "owervach-tmixer"


@pytest.fixture
def app_dir(isolate_storage):
    isolate_storage.mkdir(parents=True, exist_ok=True)
    return isolate_storage


@pytest.fixture
def dialogs(monkeypatch):
    calls = []

    def _record(kind, *a):
        title = a[1] if len(a) > 1 else ""
        text = a[2] if len(a) > 2 else ""
        calls.append((kind, title, text))

    def question(*a, **k):
        _record("question", *a)
        return QMessageBox.Yes

    monkeypatch.setattr(QMessageBox, "question", staticmethod(question))
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: _record("warning", *a)))
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: _record("information", *a)))
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda *a, **k: _record("critical", *a)))

    from owervach_tmixer.main import MainWindow

    def _toast(self, message, kind="info"):
        _record(kind, None, "", message)

    monkeypatch.setattr(MainWindow, "show_toast", _toast)
    return calls


@pytest.fixture
def make_window(app_dir, dialogs, qapp):
    windows = []

    def _make():
        from owervach_tmixer.main import MainWindow
        w = MainWindow()
        windows.append(w)
        return w

    yield _make

    for w in windows:
        try:
            w.close()
            w.deleteLater()
        except Exception:
            pass
    qapp.processEvents()