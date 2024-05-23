import os
import argparse
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QTreeWidget,
    QTreeWidgetItem,
)
from PyQt6.QtCore import Qt
from TrackManager import TrackManager
import asyncio

class TrackManagerGUI(QMainWindow):
    data_mapping = {
        "file_path": {
            "source_object": "track_details",
            "property": "file_path",
            "display_name": "File Path",
            "width": 100,
            "editable": False,
            "display": True,
        },
        "update_file": {
            "source_object": "track_details",
            "property": "update_file",
            "display_name": "Update",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "title": {
            "source_object": "track_details",
            "property": "title",
            "display_name": "Track Title",
            "width": 100,
            "editable": False,
            "display": True,
        },
        "original_title": {
            "source_object": "track_details",
            "property": "original_title",
            "display_name": "Orig Title",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "track_artist": {
            "source_object": "track_details",
            "property": "artist",
            "display_name": "Track Artist",
            "width": 100,
            "editable": False,
            "display": True,
        },
        "artist_sort": {
            "source_object": "mbartist_details",
            "property": "sort_name",
            "display_name": "Sort Artist",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "original_artist": {
            "source_object": "track_details",
            "property": "original_artist",
            "display_name": "Orig Artist",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "album": {
            "source_object": "track_details",
            "property": "album",
            "display_name": "Album",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "product": {
            "source_object": "track_details",
            "property": "product",
            "display_name": "Product",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "original_album": {
            "source_object": "track_details",
            "property": "original_album",
            "display_name": "Orig Album",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "album_artist": {
            "source_object": "track_details",
            "property": "album_artist",
            "display_name": "Album Artist",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "grouping": {
            "source_object": "track_details",
            "property": "grouping",
            "display_name": "Grouping",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "mbid": {
            "source_object": "mbartist_details",
            "property": "mbid",
            "display_name": "MBID",
            "width": 100,
            "editable": False,
            "display": True,
        },
        "type": {
            "source_object": "mbartist_details",
            "property": "type",
            "display_name": "Type",
            "width": 85,
            "editable": False,
            "display": True,
        },
        "artist": {
            "source_object": "mbartist_details",
            "property": "name",
            "display_name": "Artist",
            "width": 100,
            "editable": False,
            "display": True,
        },
        "joinphrase": {
            "source_object": "mbartist_details",
            "property": "joinphrase",
            "display_name": "Join Phrase",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "include": {
            "source_object": "mbartist_details",
            "property": "include",
            "display_name": "Include",
            "width": 30,
            "editable": True,
            "display": True,
        },
        "custom_name": {
            "source_object": "mbartist_details",
            "property": "custom_name",
            "display_name": "Custom Name",
            "width": 100,
            "editable": True,
            "display": True,
        },
        "custom_original_name": {
            "source_object": "mbartist_details",
            "property": "custom_original_name",
            "display_name": "Custom Orig Name",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "updated_from_server": {
            "source_object": "mbartist_details",
            "property": "updated_from_server",
            "display_name": "Has Server Information",
            "width": 100,
            "editable": False,
            "display": False,
        },
    }

    def __init__(self, app, api_host, api_port):
        super().__init__()

        self.api_host = api_host
        self.api_port = api_port
        self.track_manager = TrackManager(api_host, api_port)

        self.initUI()
        self.show()

        app.exec()

    def initUI(self):
        self.setWindowTitle("Track Manager")
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout()
        central_widget.setLayout(self.layout)

        # Adding UI components
        self.cb_replace_original_title = QCheckBox("Replace original title", self)
        self.layout.addWidget(self.cb_replace_original_title)

        self.cb_overwrite_existing_original_title = QCheckBox(
            "Overwrite existing values", self
        )
        self.layout.addWidget(self.cb_overwrite_existing_original_title)

        self.cb_replace_original_artist = QCheckBox("Replace original artists", self)
        self.layout.addWidget(self.cb_replace_original_artist)

        self.cb_overwrite_existing_original_artist = QCheckBox(
            "Overwrite existing values", self
        )
        self.layout.addWidget(self.cb_overwrite_existing_original_artist)

        self.btn_save = QPushButton("Save", self)
        self.layout.addWidget(self.btn_save)

        self.btn_load_files = QPushButton("Select Folder", self)
        self.btn_load_files.clicked.connect(self.handle_load_files_click)
        self.layout.addWidget(self.btn_load_files)

        # Placeholder for the table
        self.track_table = QTreeWidget()
        self.track_table.setHeaderLabels(
            [value["display_name"] for value in self.data_mapping.values() if value["display"]]
        )
        self.track_table.setColumnCount(len([value for value in self.data_mapping.values() if value["display"]]))
        self.layout.addWidget(self.track_table)

    def handle_load_files_click(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.load_directory())

    async def load_directory(self):
        # directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        # if directory:
        directory = "C:/Users/email_000/Desktop/music/sample/spiceandwolf"
        await self.track_manager.load_directory(directory)
        await self.track_manager.update_artists_info_from_db()
        self.populate_table()

    def populate_table(self):
        self.track_table.clear()
        for track in self.track_manager.tracks:
            track_item = QTreeWidgetItem()
            track_item.setText(0, track.title)
            self.track_table.addTopLevelItem(track_item)
            for artist in track.mbArtistDetails:
                artist_item = QTreeWidgetItem()
                for col, key in enumerate(self.data_mapping.keys()):
                    mapping = self.data_mapping[key]
                    if mapping["display"]:
                        if mapping["source_object"] == "track_details":
                            value = getattr(track, mapping["property"])
                        elif mapping["source_object"] == "mbartist_details":
                            value = getattr(artist, mapping["property"])
                        else:
                            value = ""
                        if isinstance(value, list):
                            value = ", ".join(value)
                        artist_item.setText(col, str(value) if value else "")
                track_item.addChild(artist_item)

    def create_track_manager(self) -> TrackManager:
        try:
            return TrackManager(self.api_host, self.api_port)
        except Exception as e:
            print(f"EXCEPTION: {e}")

def main():
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

    app = QApplication(sys.argv)
    gui = TrackManagerGUI(app, api_host, api_port)

if __name__ == "__main__":
    main()
