from PyQt6.QtCore import QObject, pyqtSignal


class PreferencesBus(QObject):
    """Lightweight event bus to broadcast Preferences updates across dialogs.

    Also tracks whether the Preferences dialog is currently open, so other dialogs
    (e.g., Page Setup) can decide whether to auto-apply staged defaults immediately
    or leave them pending for the Preferences close prompt.
    """

    # Emitted when any preferences values change (payload optional)
    preferences_updated = pyqtSignal(dict)
    # Emitted when Preferences dialog open state changes
    preferences_dialog_open_changed = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._preferences_dialog_open = False

    def set_preferences_dialog_open(self, is_open: bool) -> None:
        if self._preferences_dialog_open == is_open:
            return
        self._preferences_dialog_open = is_open
        try:
            self.preferences_dialog_open_changed.emit(is_open)
        except Exception:
            pass

    def is_preferences_open(self) -> bool:
        return bool(self._preferences_dialog_open)


# Global singleton instance
preferences_bus = PreferencesBus()


