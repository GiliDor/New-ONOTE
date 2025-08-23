import pytest
from PyQt6.QtWidgets import QApplication
from src.gui.music.main_window import MainWindow

@pytest.fixture
def app():
    """Create a QApplication instance for testing."""
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def main_window(app):
    """Create a MainWindow instance for testing."""
    window = MainWindow(is_welcome_window=False)
    yield window
    window.close()

def test_window_creation(main_window):
    """Test that the window is created with correct properties."""
    assert main_window.windowTitle() == "ONOTE"
    assert not main_window.is_welcome_window
    assert main_window.staff_view is not None
    assert main_window.score_document is not None

def test_new_score(main_window):
    """Test creating a new score."""
    initial_windows = len(main_window.windows)
    main_window.new_score()
    assert len(main_window.windows) == initial_windows + 1

def test_open_score(main_window):
    """Test opening a score."""
    initial_windows = len(main_window.windows)
    main_window.open_score()
    # Note: This test will show a file dialog, which needs to be handled manually
    # The window count should not change if no file is selected
    assert len(main_window.windows) == initial_windows 