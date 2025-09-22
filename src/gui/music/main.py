import sys
import os
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication

def _print_dev_banner():
    try:
        import subprocess
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        rev = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception:
        rev = "unknown"
    try:
        from . import staff_view as _sv
        sv_path = getattr(_sv, "__file__", "<no file>")
    except Exception:
        sv_path = "<import failed>"
    print(f"ONOTE Dev (Music UI): commit={rev} | staff_view={sv_path}")
from .main_window import MainWindow

def main():
    # Ensure name/domain are set as early as possible (affects macOS app menu)
    try:
        QCoreApplication.setApplicationName("ONOTE")
        QCoreApplication.setOrganizationName("ONOTE")
        if hasattr(QCoreApplication, "setOrganizationDomain"):
            QCoreApplication.setOrganizationDomain("onote.app")
        # Help Qt pick up name for macOS menu
        os.environ.setdefault("QT_MAC_APPLICATION_NAME", "ONOTE")
        # Improve process name shown in some mac tools
        sys.argv[0] = "ONOTE"
        try:
            import ctypes
            if hasattr(ctypes.pythonapi, 'Py_SetProgramName'):
                ctypes.pythonapi.Py_SetProgramName(b"ONOTE")
        except Exception:
            pass
        # Best-effort: adjust Cocoa bundle/process names if PyObjC is available
        try:
            from Foundation import NSProcessInfo, NSBundle
            NSProcessInfo.processInfo().setProcessName_("ONOTE")
            bundle = NSBundle.mainBundle()
            info = bundle.infoDictionary()
            if info is not None:
                info["CFBundleName"] = "ONOTE"
                info["CFBundleDisplayName"] = "ONOTE"
        except Exception:
            pass
    except Exception:
        pass

    app = QApplication(sys.argv)
    # Also set on the application instance
    try:
        app.setApplicationName("ONOTE")
        app.setApplicationDisplayName("ONOTE")
        app.setOrganizationName("ONOTE")
        if hasattr(app, "setOrganizationDomain"):
            app.setOrganizationDomain("onote.app")
    except Exception:
        pass

    # Dev banner to verify running code path
    _print_dev_banner()

    # Start with the welcome/desktop-style window to mirror the packaged app UX
    window = MainWindow(is_welcome_window=True)
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 