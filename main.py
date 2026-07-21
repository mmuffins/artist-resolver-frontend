import os
import argparse
import sys
from pathlib import Path
from xml.sax.saxutils import escape


def configure_fontconfig() -> None:
    if "FONTCONFIG_FILE" in os.environ:
        return
    if sys.platform != "linux" or "DEVENV_ROOT" not in os.environ:
        return

    project_root = Path(__file__).resolve().parent
    font_dir = project_root / "font"
    cache_dir = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache"))
    config_dir = cache_dir / "artist-resolver-frontend"
    config_dir.mkdir(parents=True, exist_ok=True)

    fontconfig_file = config_dir / "fonts.conf"
    fontconfig_file.write_text(
        "\n".join(
            [
                '<?xml version="1.0"?>',
                '<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">',
                "<fontconfig>",
                f"  <dir>{escape(str(font_dir))}</dir>",
                '  <cachedir prefix="xdg">fontconfig</cachedir>',
                "</fontconfig>",
            ]
        ),
        encoding="utf-8",
    )
    os.environ["FONTCONFIG_FILE"] = str(fontconfig_file)


configure_fontconfig()
from artist_resolver_frontend import MainWindow  # noqa: E402


def main():

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
