import os
import argparse
import sys
from artist_resolver_frontend import MainWindow


def configure_qt_environment():
    import PyQt6

    pyqt_root = os.path.join(os.path.dirname(PyQt6.__file__), "Qt6")
    plugin_path = os.path.join(pyqt_root, "plugins")
    qml_path = os.path.join(pyqt_root, "qml")
    platform_plugin_path = os.path.join(plugin_path, "platforms")

    # Prefer the wheel's bundled Qt plugins over any system-wide Qt plugin paths.
    os.environ["QT_PLUGIN_PATH"] = plugin_path
    os.environ["QML2_IMPORT_PATH"] = qml_path
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platform_plugin_path


def main():
    configure_qt_environment()

    from PyQt6.QtWidgets import QApplication

    parser = argparse.ArgumentParser(prog="Artist Relation Resolver")
    parser.add_argument(
        "-s",
        "--host",
        type=str,
        required=False,
        help="host of the Artist Relation Resolver API",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=str,
        required=False,
        help="Port of the Artist Relation Resolver API",
    )

    args = parser.parse_args()

    api_host = args.host if args.host else os.getenv("ARTIST_RESOLVER_HOST", None)
    api_port = args.port if args.port else os.getenv("ARTIST_RESOLVER_PORT", None)

    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    main_window = MainWindow(app, api_host, api_port)

    try:
        main_window.loop.run_forever()
    except RuntimeError as e:
        print(f"Caught RuntimeError when the loop was closed: {e}")


if __name__ == "__main__":
    main()
