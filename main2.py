import os
import argparse
import sys
import asyncio
from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex, pyqtSlot
from TrackManager import TrackManager, TrackDetails
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeView,
)


class TrackModel(QAbstractItemModel):
    def __init__(self, track_manager):
        super().__init__()
        self.track_manager = track_manager
        self.layoutChanged.connect(self.custom_layout_changed)
        self.track_column_mappings = [
            {
                "property": "file_path",
                "display_name": "File Path",
                "width": 100,
                "editable": False,
            },
            {
                "property": "update_file",
                "display_name": "Update",
                "width": 100,
                "editable": False,
            },
            {
                "property": "title",
                "display_name": "Track Title",
                "width": 100,
                "editable": True,
            },
            {
                "property": "album",
                "display_name": "Album",
                "width": 100,
                "editable": True,
            },
            {
                "property": "artist_string",
                "display_name": "Artist(s)",
                "width": 100,
                "editable": True,
            },
        ]
        self.artist_column_mappings = [
            {
                "property": "include",
                "display_name": "Include",
                "width": 100,
                "editable": True,
            },
            {
                "property": "mbid",
                "display_name": "MBID",
                "width": 100,
                "editable": False,
            },
            {
                "property": "type",
                "display_name": "Type",
                "width": 100,
                "editable": False,
            },
            {
                "property": "name",
                "display_name": "Artist",
                "width": 100,
                "editable": False,
            },
            {
                "property": "custom_name",
                "display_name": "Custom Name",
                "width": 100,
                "editable": True,
            },
        ]

    @pyqtSlot()
    def custom_layout_changed(self):
        self.create_unique_artist_index()

    def create_unique_artist_index(self):
        self.track_index = []
        for track in self.track_manager.tracks:
            for artist in track.mbArtistDetails:
                self.track_index.append({"track": track, "artist": artist})

    def get_unique_artist(self, track, artist):
        for index, track_info in enumerate(self.track_index):
            if track_info["track"] == track and track_info["artist"] == artist:
                return index, track_info
        return None, None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role not in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
            Qt.ItemDataRole.CheckStateRole,
        ):
            return None

        if not index.parent().isValid():
            if role == Qt.ItemDataRole.CheckStateRole:
                return None

            track = self.track_manager.tracks[index.row()]
            column = index.column()
            property_name = self.track_column_mappings[column]["property"]
            if property_name == "artist_string":
                return track.get_artist_string()
            return getattr(track, property_name, None)

        property_name = self.artist_column_mappings[index.column()]["property"]
        track = index.parent().internalPointer()
        artist = track.mbArtistDetails[index.row()]

        if role == Qt.ItemDataRole.CheckStateRole:
            if property_name == "include":
                return (
                    Qt.CheckState.Checked if artist.include else Qt.CheckState.Unchecked
                )
            return None

        return getattr(artist, property_name, None)

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False

        if role == Qt.ItemDataRole.EditRole or role == Qt.ItemDataRole.CheckStateRole:
            if not index.parent().isValid():
                track = self.track_manager.tracks[index.row()]
                column = index.column()
                property_name = self.track_column_mappings[column]["property"]
                if property_name == "artist_string":
                    track.artist = [value]
                else:
                    setattr(track, property_name, value)
            else:
                track = index.parent().internalPointer()
                artist = track.mbArtistDetails[index.row()]
                property_name = self.artist_column_mappings[index.column()]["property"]

                if (
                    property_name == "include"
                    and role == Qt.ItemDataRole.CheckStateRole
                ):
                    artist.include = value == Qt.CheckState.Checked
                else:
                    setattr(artist, property_name, value)

            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if section < len(self.track_column_mappings):
                return self.track_column_mappings[section]["display_name"]
            return self.artist_column_mappings[
                section - len(self.track_column_mappings)
            ]["display_name"]
        return None

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            if row < len(self.track_manager.tracks):
                return self.createIndex(row, column, self.track_manager.tracks[row])
            return QModelIndex()
        else:
            track = parent.internalPointer()
            if row < len(track.mbArtistDetails):
                _, track_info = self.get_unique_artist(
                    track, track.mbArtistDetails[row]
                )
                if track_info:
                    return self.createIndex(row, column, track_info)
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()

        if isinstance(item, dict):  # It's a track-artist mapping
            track = item["track"]
            row = self.track_manager.tracks.index(track)
            return self.createIndex(row, 0, track)

        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self.track_manager.tracks)
        else:
            track = parent.internalPointer()
            if isinstance(track, TrackDetails):
                return len(track.mbArtistDetails)
        return 0

    def columnCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self.track_column_mappings)
        else:
            return len(self.artist_column_mappings)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled

        column = index.column()
        if not index.parent().isValid():
            editable = self.track_column_mappings[column]["editable"]
        else:
            editable = self.artist_column_mappings[column]["editable"]

        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if editable:
            flags |= Qt.ItemFlag.ItemIsEditable
            if (
                index.parent().isValid()
                and self.artist_column_mappings[column]["property"] == "include"
            ):
                flags |= Qt.ItemFlag.ItemIsUserCheckable

        return flags


class MainWindow(QMainWindow):
    def __init__(self, app, api_host, api_port):
        super().__init__()

        self.api_host = api_host
        self.api_port = api_port
        self.track_manager = TrackManager(host=self.api_host, port=self.api_port)

        self.initUI()
        self.show()

        app.exec()

    def initUI(self) -> None:
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
        self.btn_load_files.clicked.connect(self.load_directory)
        self.layout.addWidget(self.btn_load_files)

        self.track_view = QTreeView(self)
        self.layout.addWidget(self.track_view)
        self.clear_data()

    def load_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            "C:/Users/email_000/Desktop/music/sample/spiceandwolf",
        )
        if directory:

            async def load_and_update():
                self.clear_data()

                await self.track_manager.load_directory(directory)
                await self.track_manager.update_artists_info_from_db()

                self.track_model.layoutChanged.emit()
                self.track_view.expandAll()

            asyncio.run(load_and_update())
            print(f"Selected directory: {directory}")

    def clear_data(self) -> TrackModel:
        self.track_manager = TrackManager(host=self.api_host, port=self.api_port)
        self.track_model = TrackModel(self.track_manager)
        self.track_view.setModel(self.track_model)


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

    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    MainWindow(app, api_host, api_port)


if __name__ == "__main__":
    main()
