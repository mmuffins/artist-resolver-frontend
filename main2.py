import os
import argparse
import sys
import asyncio
from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex
from TrackManager import TrackManager
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

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self.track_manager.tracks)
        elif parent.internalPointer() in self.track_manager.tracks:
            track = parent.internalPointer()
            return len(track.mbArtistDetails)
        return 0

    def columnCount(self, parent=QModelIndex()):
        return 5  # Adjust based on number of columns needed

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if not index.parent().isValid():
                track = self.track_manager.tracks[index.row()]
                column = index.column()
                if column == 0:
                    return track.title
                elif column == 1:
                    return track.album
                elif column == 2:
                    return track.get_artist_string()
                # Add more columns as needed
            else:
                track = index.parent().internalPointer()
                artist = track.mbArtistDetails[index.row()]
                column = index.column()
                if column == 0:
                    return artist.name
                elif column == 1:
                    return artist.type
                elif column == 2:
                    return artist.custom_name
                # Add more columns as needed
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False

        if role == Qt.ItemDataRole.EditRole:
            if not index.parent().isValid():
                track = self.track_manager.tracks[index.row()]
                column = index.column()
                if column == 0:
                    track.title = value
                elif column == 1:
                    track.album = value
                elif column == 2:
                    track.artist = [value]
                # Add more columns as needed
            else:
                track = index.parent().internalPointer()
                artist = track.mbArtistDetails[index.row()]
                column = index.column()
                if column == 0:
                    artist.name = value
                elif column == 1:
                    artist.type = value
                elif column == 2:
                    artist.custom_name = value
                # Add more columns as needed
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if section == 0:
                return "Title"
            elif section == 1:
                return "Album"
            elif section == 2:
                return "Artist(s)"
            # Add more columns as needed
        return None

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            return self.createIndex(row, column, self.track_manager.tracks[row])
        elif parent.internalPointer() in self.track_manager.tracks:
            track = parent.internalPointer()
            return self.createIndex(row, column, track.mbArtistDetails[row])
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()

        if item in self.track_manager.tracks:
            return QModelIndex()

        for track in self.track_manager.tracks:
            if item in track.mbArtistDetails:
                row = self.track_manager.tracks.index(track)
                return self.createIndex(row, 0, track)

        return QModelIndex()

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled

        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )


class TrackManagerGUI(QMainWindow):
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
        # directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        # if directory:
        directory = "C:/Users/email_000/Desktop/music/sample/spiceandwolf"
        
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
    TrackManagerGUI(app, api_host, api_port)


if __name__ == "__main__":
    main()
