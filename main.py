import os
import argparse
import sys
import asyncio
import httpx
from Toast import Toast, ToastType
from TrackManager import TrackManager, TrackDetails
from PyQt6.QtCore import (
    Qt,
    QAbstractItemModel,
    QModelIndex,
)
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QTreeView,
)


class TrackModel(QAbstractItemModel):

    header_names = [
        {"display_name": "ID", "width": 120},
        {"display_name": "Type", "width": 80},
        {"display_name": "Name", "width": 150},
        {"display_name": "Set", "width": 15},
        {"display_name": "Custom Name", "width": 200},
    ]

    track_column_mappings = [
        {
            "property": "title",
            "roles": [
                Qt.ItemDataRole.DisplayRole,
            ],
            "flags": [
                Qt.ItemFlag.ItemIsEnabled,
                Qt.ItemFlag.ItemIsSelectable,
            ],
        },
        {
            "property": "album",
            "roles": [
                Qt.ItemDataRole.DisplayRole,
            ],
            "flags": [
                Qt.ItemFlag.ItemIsEnabled,
                Qt.ItemFlag.ItemIsSelectable,
            ],
        },
        {
            "property": "formatted_artist",
            "roles": [
                Qt.ItemDataRole.DisplayRole,
            ],
            "flags": [
                Qt.ItemFlag.ItemIsEnabled,
                Qt.ItemFlag.ItemIsSelectable,
            ],
        },
        {
            "property": None,
            "roles": [],
            "flags": [
                Qt.ItemFlag.ItemIsEnabled,
                Qt.ItemFlag.ItemIsSelectable,
            ],
        },
        {
            "property": "formatted_new_artist",
            "roles": [
                Qt.ItemDataRole.DisplayRole,
            ],
            "flags": [
                Qt.ItemFlag.ItemIsEnabled,
                Qt.ItemFlag.ItemIsSelectable,
            ],
        },
    ]

    artist_column_mappings = [
        {
            "property": "mbid",
            "roles": [
                Qt.ItemDataRole.DisplayRole,
            ],
            "flags": [
                Qt.ItemFlag.ItemIsEnabled,
                Qt.ItemFlag.ItemIsSelectable,
            ],
        },
        {
            "property": "type",
            "roles": [
                Qt.ItemDataRole.DisplayRole,
            ],
            "flags": [
                Qt.ItemFlag.ItemIsEnabled,
                Qt.ItemFlag.ItemIsSelectable,
            ],
        },
        {
            "property": "name",
            "roles": [
                Qt.ItemDataRole.DisplayRole,
            ],
            "flags": [
                Qt.ItemFlag.ItemIsEnabled,
                Qt.ItemFlag.ItemIsSelectable,
            ],
        },
        {
            "property": "include",
            "roles": [
                Qt.ItemDataRole.CheckStateRole,
            ],
            "flags": [
                Qt.ItemFlag.ItemIsEnabled,
                Qt.ItemFlag.ItemIsSelectable,
                Qt.ItemFlag.ItemIsUserCheckable,
            ],
        },
        {
            "property": "custom_name",
            "roles": [
                Qt.ItemDataRole.DisplayRole,
                Qt.ItemDataRole.EditRole,
            ],
            "flags": [
                Qt.ItemFlag.ItemIsEnabled,
                Qt.ItemFlag.ItemIsSelectable,
                Qt.ItemFlag.ItemIsEditable,
            ],
        },
    ]

    def __init__(self, track_manager):
        super().__init__()
        self.track_manager = track_manager

    def create_unique_artist_index(self):
        """
        Creates a list containing all tracks and artists.
        This is required to uniquely identify artist rows as they can be referenced in multiple tracks
        """

        self.track_index = []
        for track in self.track_manager.tracks:
            for artist in track.mbArtistDetails:
                self.track_index.append({"track": track, "artist": artist})

    def get_unique_artist(self, track, artist):
        """Retrieves the unique index of a track-artist combination"""
        for index, track_info in enumerate(self.track_index):
            if track_info["track"] == track and track_info["artist"] == artist:
                return index, track_info
        return None, None

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows"""
        if not parent.isValid():
            return len(self.track_manager.tracks)
        else:
            track = parent.internalPointer()
            if isinstance(track, TrackDetails):
                return len(track.mbArtistDetails)
        return 0

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns"""
        if not parent.isValid():
            return len(self.track_column_mappings)
        else:
            return len(self.artist_column_mappings)

    def columnWidth(self, section):
        """Returns the width of the column"""
        if section < len(self.header_names):
            return self.header_names[section]["width"]
        return 100  # Default width if section index is out of range

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Returns a string to be displayed in the header of a column"""
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if section < len(self.header_names):
                return self.header_names[section]["display_name"]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Returns data requested by an item from the underlying data object"""
        if not index.isValid():
            return None

        if not index.parent().isValid():
            # items without parents are track objects
            return self.data_track(index, role)

        # items with parents are artist objects
        return self.data_artist(index, role)

    def data_track(self, index, role=Qt.ItemDataRole.DisplayRole):
        track = self.track_manager.tracks[index.row()]
        column = index.column()
        column_mapping = self.track_column_mappings[column]

        if role not in column_mapping.get("roles", []):
            return None

        value = getattr(track, column_mapping["property"], None)

        if role == Qt.ItemDataRole.CheckStateRole:
            value = Qt.CheckState.Checked if value else Qt.CheckState.Unchecked

        return value

    def data_artist(self, index, role=Qt.ItemDataRole.DisplayRole):
        track = index.parent().internalPointer()
        artist = track.mbArtistDetails[index.row()]
        column_mapping = self.artist_column_mappings[index.column()]

        if role not in column_mapping.get("roles", []):
            return None

        value = getattr(artist, column_mapping["property"], None)

        if role == Qt.ItemDataRole.CheckStateRole:
            value = Qt.CheckState.Checked if value else Qt.CheckState.Unchecked

        return value

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Writes data back to the underlying data object once an item was modified"""
        if not index.isValid():
            return False

        was_edited = False

        if not index.parent().isValid():
            # items without parents are track objects
            was_edited = self.setData_track(index, value, role)
        else:
            was_edited = self.setData_artist(index, value, role)

        if was_edited:
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def setData_track(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        track = self.track_manager.tracks[index.row()]
        column_mapping = self.track_column_mappings[index.column()]

        if role not in column_mapping.get("roles", []):
            return False

        setattr(track, column_mapping["property"], value)

        if role == Qt.ItemDataRole.CheckStateRole:
            self.layoutChanged.emit()

        return True

    def setData_artist(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        track = index.parent().internalPointer()
        artist = track.mbArtistDetails[index.row()]
        column_mapping = self.artist_column_mappings[index.column()]

        if role not in column_mapping.get("roles", []):
            return False

        if role == Qt.ItemDataRole.CheckStateRole:
            value = value == Qt.CheckState.Checked.value

        setattr(artist, column_mapping["property"], value)

        if role == Qt.ItemDataRole.CheckStateRole:
            self.layoutChanged.emit()

        return True

    def index(self, row, column, parent=QModelIndex()):
        """Returns the index of the element at the given position and column"""
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
        """Returns the parent of the element at index"""
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()

        if isinstance(item, dict):  # It's a track-artist mapping
            track = item["track"]
            row = self.track_manager.tracks.index(track)
            return self.createIndex(row, 0, track)

        return QModelIndex()

    def flags(self, index):
        """Returns the item flags for the specified index, e.g. selectable, editable, checkable"""
        flags = Qt.ItemFlag.NoItemFlags

        if not index.isValid():
            return flags

        column = index.column()
        if not index.parent().isValid():
            column_mapping = self.track_column_mappings[column]
        else:
            column_mapping = self.artist_column_mappings[column]

        for flag in column_mapping.get("flags", []):
            flags |= flag

        return flags


class MainWindow(QMainWindow):
    def __init__(self, app, api_host, api_port):
        super().__init__()

        self.api_host = api_host
        self.api_port = api_port
        self.track_manager = self.create_track_manager()

        self.initUI()
        self.show()
        # self.check_server_health()

        app.exec()

    def initUI(self) -> None:
        self.toast = None
        self.setWindowTitle("Track Manager")
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout()
        central_widget.setLayout(self.layout)

        self.cb_replace_original_title = QCheckBox("Replace original title", self)
        self.cb_replace_original_title.setChecked(True)
        self.layout.addWidget(self.cb_replace_original_title)

        self.cb_overwrite_existing_original_title = QCheckBox(
            "Overwrite existing values", self
        )
        self.layout.addWidget(self.cb_overwrite_existing_original_title)

        self.cb_replace_original_artist = QCheckBox("Replace original artists", self)
        self.cb_replace_original_artist.setChecked(True)
        self.layout.addWidget(self.cb_replace_original_artist)

        self.cb_overwrite_existing_original_artist = QCheckBox(
            "Overwrite existing values", self
        )
        self.layout.addWidget(self.cb_overwrite_existing_original_artist)

        self.btn_save = QPushButton("Save", self)
        self.btn_save.clicked.connect(self.save_changes)
        self.layout.addWidget(self.btn_save)

        self.btn_load_files = QPushButton("Select Folder", self)
        self.btn_load_files.clicked.connect(self.load_directory)
        self.layout.addWidget(self.btn_load_files)

        self.track_view = QTreeView(self)
        self.layout.addWidget(self.track_view)
        self.clear_data()
        self.apply_column_width()

    def create_track_manager(self) -> TrackManager:
        try:
            return TrackManager(self.api_host, self.api_port)
        except Exception as e:
            self.show_toast(
                f"Failed to create a TrackManager object: {str(e)}", ToastType.ERROR
            )
            return None

    async def check_server_health(self):
        try:
            api_is_healthy = await self.track_manager.get_server_health()

            if not api_is_healthy:
                self.show_toast(
                    f"The server is not healthy. Please check the server status.",
                    ToastType.ERROR,
                )
        except httpx.RequestError as e:
            self.show_toast(
                f"Could not reach the server at {self.api_host}:{self.api_port}: {str(e)}",
                ToastType.ERROR,
            )
        except Exception as e:
            self.show_toast(
                f"An unexpected error occurred when trying to contact the server: {str(e)}",
                ToastType.ERROR,
            )

    def save_changes(self) -> None:
        async def run():
            try:
                await self.track_manager.send_changes_to_db()
            except Exception as e:
                self.show_toast(
                    f"An error occurred when sending update data to the server: {str(e)}",
                    ToastType.ERROR,
                )

            try:
                await self.track_manager.save_files()
                self.show_toast("Metadata saved successfully!", ToastType.SUCCESS)
            except Exception as e:
                self.show_toast(
                    f"An error occurred when updating the files: {str(e)}",
                    ToastType.ERROR,
                )

        asyncio.run(run())

    def load_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            "C:/Users/email_000/Desktop/music/sample/spiceandwolf",
        )
        if directory:

            async def load_and_update():
                self.clear_data()
                await self.check_server_health()

                try:
                    await self.track_manager.load_directory(directory)
                except Exception as e:
                    self.show_toast(
                        f"An error occurred when reading directory {directory}: {str(e)}",
                        ToastType.ERROR,
                    )
                try:
                    await self.track_manager.update_artists_info_from_db()
                except Exception as e:
                    self.show_toast(
                        f"An error occurred querying the server for information: {str(e)}",
                        ToastType.ERROR,
                    )

                if self.cb_replace_original_title.isChecked():
                    self.track_manager.replace_original_title(
                        overwrite=self.cb_overwrite_existing_original_title.isChecked()
                    )

                if self.cb_replace_original_artist.isChecked():
                    self.track_manager.replace_original_artist(
                        overwrite=self.cb_overwrite_existing_original_artist.isChecked()
                    )

                self.track_model.create_unique_artist_index()
                self.track_view.expandAll()

            asyncio.run(load_and_update())

    def clear_data(self) -> TrackModel:
        self.track_manager = TrackManager(host=self.api_host, port=self.api_port)
        self.track_model = TrackModel(self.track_manager)
        self.track_view.setModel(self.track_model)

    def show_toast(self, message: str, toast_type: ToastType) -> None:
        if self.toast and self.toast.isVisible():
            self.toast.hide()

        self.toast = Toast(message, toast_type=toast_type, parent=self)
        self.toast.update_position(self.geometry())
        self.toast.show()

    def apply_column_width(self) -> None:
        for i in range(len(self.track_model.header_names)):
            self.track_view.setColumnWidth(i, self.track_model.columnWidth(i))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            selected_indexes = self.track_view.selectedIndexes()
            if selected_indexes:
                selected_index = selected_indexes[0]
                if selected_index.isValid():
                    track_item = selected_index.internalPointer()
                    if isinstance(track_item, TrackDetails):
                        self.track_manager.remove_track(track_item)
                        self.track_model.layoutChanged.emit()

    def moveEvent(self, event):
        if self.toast and self.toast.isVisible():
            self.toast.update_position(self.geometry())

    def resizeEvent(self, event):
        if self.toast and self.toast.isVisible():
            self.toast.update_position(self.geometry())


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
