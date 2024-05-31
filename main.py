import os
import argparse
import sys
import asyncio
import httpx
import webbrowser
from Toast import Toast, ToastType
from artist_resolver.trackmanager import (
    TrackManager,
    TrackDetails,
    MbArtistDetails,
    SimpleArtistDetails,
)
from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex, QTimer
from PyQt6.QtGui import (
    QKeyEvent,
    QPalette,
    QColor,
    QPainter,
    QFontDatabase,
    QDragEnterEvent,
    QDropEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QTreeView,
    QHBoxLayout,
    QGridLayout,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)


class ArtistDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.model = model
        self.custom_name_column = self.get_custom_name_column()

    def get_custom_name_column(self):
        for i, column in enumerate(self.model.artist_column_mappings):
            if column["property"] == "custom_name":
                return i
        return -1

    def apply_custom_name_edited_condition(self, artist, option):
        if not artist.custom_name_edited:
            # set to red if the artist was not edited
            option.palette.setColor(QPalette.ColorRole.Text, QColor(255, 23, 62))
            return True
        return False

    def apply_server_data_condition(self, artist, option):
        if not artist.has_server_data and isinstance(artist, MbArtistDetails):
            # set to blue if artist was not updated from server but has mbartist details
            option.palette.setColor(QPalette.ColorRole.Text, QColor(0, 128, 255))
            return True
        elif artist.has_server_data:
            # set to purple if artist was updated from server
            option.palette.setColor(QPalette.ColorRole.Text, QColor(164, 97, 240))
            return True
        return False

    def apply_custom_name_edited_true_condition(self, artist, option):
        if artist.custom_name_edited:
            # set to green if the artist was edited
            option.palette.setColor(QPalette.ColorRole.Text, QColor(58, 235, 157))
            return True
        return False

    def apply_invalid_relation_true_condition(self, artist, option):
        if artist.invalid_relation:
            # set to ?? if the artist is likely to be an incorrect relation
            option.palette.setColor(QPalette.ColorRole.Text, QColor(255, 0, 0))
            return True
        return False

    def apply_include_condition(self, artist, option, color_modified):
        if not artist.include:
            if color_modified:
                # Get the current text color
                current_color = option.palette.color(QPalette.ColorRole.Text)
                # Reduce the color intensity
                reduced_color = QColor(
                    int(current_color.red() * 0.7),
                    int(current_color.green() * 0.7),
                    int(current_color.blue() * 0.7),
                )
                option.palette.setColor(QPalette.ColorRole.Text, reduced_color)
            else:
                # grey out entire line if the artist is not included
                option.palette.setColor(QPalette.ColorRole.Text, QColor(95, 95, 95))

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        column = index.column()
        color_modified = False

        if not index.parent().isValid():
            # This is a track item (parent)
            track = index.internalPointer()
            # bold text for track rows
            font = option.font
            font.setPixelSize(int(font.pixelSize() * 1.08))
            font.setBold(True)
            option.font = font
        else:
            # This is an artist item
            track = index.parent().internalPointer()
            artist = track.artist_details[index.row()]

            # Apply conditions
            if column == self.custom_name_column:
                color_modified |= self.apply_custom_name_edited_condition(
                    artist, option
                )
                color_modified |= self.apply_server_data_condition(artist, option)
                color_modified |= self.apply_custom_name_edited_true_condition(
                    artist, option
                )

            # Apply the include condition last
            self.apply_include_condition(artist, option, color_modified)

        super().paint(painter, option, index)


class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                cell_value = index.data(Qt.ItemDataRole.DisplayRole)
                clipboard = QApplication.clipboard()
                clipboard.setText(cell_value)
                self.main_window.show_toast(f"Copied {cell_value}", ToastType.INFO, 500)
        super().mousePressEvent(event)


class TrackModel(QAbstractItemModel):

    header_names = [
        {"display_name": "Title", "width": 100},
        {"display_name": "Type", "width": 100},
        {"display_name": "Name", "width": 220},
        {"display_name": "Set", "width": 15},
        {"display_name": "Custom Name", "width": 340},
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
            "roles": [],
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
        self.track_index = []

    def create_unique_artist_index(self):
        """
        Creates a list containing all tracks and artists.
        This is required to uniquely identify artist rows as they can be referenced in multiple tracks
        """

        self.track_index = []
        for track in self.track_manager.tracks:
            for artist in track.artist_details:
                self.track_index.append({"track": track, "artist": artist})

    def get_unique_artist(self, track, artist):
        """Retrieves the unique index of a track-artist combination"""
        for index, track_info in enumerate(self.track_index):
            if track_info["track"] == track and track_info["artist"] == artist:
                return index, track_info
        return None, None

    def remove_track(self, track):
        """Removes a track from the trackmodel image and the track manager"""
        # I never made removing individual rows work without crashing the application
        # so this is the next best thing
        self.beginResetModel()
        self.track_manager.remove_track(track)
        self.create_unique_artist_index()
        self.endResetModel()

    async def load_files(
        self,
        files: list[str],
        replace_original_title: bool,
        overwrite_original_title: bool,
        replace_original_artist: bool,
        overwrite_original_artist: bool,
        read_artist_json: bool,
    ):
        """Loads files and reads their metadata"""
        # a proper implementation would use beginInsertRows in the track model,
        # but that crashes randomly and I can't figure out why,
        # so just resetting the view is easier and has only very minor side effects

        self.beginResetModel()

        try:
            await self.track_manager.load_files(files, read_artist_json)
        except Exception as e:
            raise Exception(f"An error occurred when reading files: {str(e)}")

        try:
            await self.track_manager.update_artists_info_from_db()
        except Exception as e:
            raise Exception(
                f"An error occurred querying the server for information: {str(e)}"
            )

        if replace_original_title:
            self.track_manager.replace_original_title(
                overwrite=overwrite_original_title
            )

        if replace_original_artist:
            self.track_manager.replace_original_artist(
                overwrite=overwrite_original_artist
            )

        self.create_unique_artist_index()
        self.endResetModel()

    async def save_files(self):
        """Saves changes to loaded files"""
        try:
            await self.track_manager.send_changes_to_db()
        except Exception as e:
            raise Exception(
                f"An error occurred when sending update data to the server: {str(e)}"
            )

        try:
            await self.track_manager.save_files()
        except Exception as e:
            raise Exception(f"An error occurred when updating the files: {str(e)}")

    def get_musicbrainz_url(self, item):
        base_url = "https://musicbrainz.org"
        if isinstance(item, TrackDetails):
            return (
                f"{base_url}/track/{item.mb_track_id}" if item.mb_track_id else None
            )

        if (
            isinstance(item, dict)
            and item["artist"]
            and isinstance(item["artist"], MbArtistDetails)
        ):
            return f"{base_url}/artist/{item["artist"].mbid}" if item["artist"].mbid else None

        return None

    async def convert_track_to_simple_artist(
        self,
        track,
        replace_original_title: bool,
        overwrite_original_title: bool,
        replace_original_artist: bool,
        overwrite_original_artist: bool,
    ):
        """Re-imports track, ensuring that all artist_detail objects are simple artists"""

        # only run if the track either has no artist details or artist details are simple artists
        if not track.artist_details or (
            track.artist_details
            and isinstance(track.artist_details[0], SimpleArtistDetails)
        ):
            return

        file_path = track.file_path

        self.remove_track(track)
        await self.load_files(
            [file_path],
            replace_original_title,
            overwrite_original_title,
            replace_original_artist,
            overwrite_original_artist,
            False,
        )

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows"""
        if not parent.isValid():
            return len(self.track_manager.tracks)
        else:
            track = parent.internalPointer()
            if isinstance(track, TrackDetails):
                return len(track.artist_details)
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
        artist = track.artist_details[index.row()]
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
        artist = track.artist_details[index.row()]
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
            if row < len(track.artist_details):
                _, track_info = self.get_unique_artist(track, track.artist_details[row])
                if track_info:
                    return self.createIndex(row, column, track_info)
        return QModelIndex()

    def parent(self, index):
        """Returns the parent of the element at index"""
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()

        if isinstance(item, dict) and "track" in item:  # It's a track-artist mapping
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
    stylesheet = "./styles.qss"

    def __init__(self, app, api_host, api_port):
        super().__init__()

        self.app = app
        self.is_closing = False
        self.api_host = api_host
        self.api_port = api_port
        self.track_manager = self.create_track_manager()

        # Create and start the asyncio event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Use QTimer to periodically run the event loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_async_tasks)
        # the loop runs each millisecond, setting the value higher sometimes caused
        # weird issues where async actions would randomly fail or time out
        self.timer.start(1)

        self.initUI()
        self.show()
        asyncio.ensure_future(self.check_server_health(), loop=self.loop)

        app.exec()

    def apply_styles(self):
        try:
            with open(self.stylesheet, "r") as file:
                self.setStyleSheet(file.read())
        except Exception as e:
            self.show_toast(f"Error loading stylesheet: {e}", ToastType.ERROR, 10000)

    def initUI(self) -> None:
        self.toast = None
        self.setWindowTitle("Track Manager")
        self.setGeometry(100, 100, 1300, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout()
        central_widget.setLayout(self.layout)

        self.track_view = CustomTreeView(self)

        # Assign the model here to ensure it's created before setting the delegate
        self.track_model = TrackModel(self.track_manager)
        self.track_view.setModel(self.track_model)
        self.track_view.setItemDelegate(ArtistDelegate(self, self.track_model))

        self.layout.addWidget(self.track_view)

        self.add_actions_layout()

        self.clear_data()
        self.apply_column_width()

        QFontDatabase.addApplicationFont("font/NotoSansJP.ttf")
        self.app.setStyle("Fusion")
        self.apply_styles()

        self.setAcceptDrops(True)

    def add_actions_layout(self):
        # Bottom layout for checkboxes and buttons
        bottom_layout = QHBoxLayout()
        checkboxes_layout = self.create_checkboxes_layout()
        bottom_layout.addLayout(checkboxes_layout)

        buttons_layout = self.create_buttons_layout()
        bottom_layout.addStretch(1)
        bottom_layout.addLayout(buttons_layout)

        self.layout.addLayout(bottom_layout)

    def create_checkboxes_layout(self):
        checkboxes_layout = QGridLayout()

        self.cb_replace_original_title = QCheckBox("Replace original title", self)
        self.cb_replace_original_title.setChecked(True)
        checkboxes_layout.addWidget(self.cb_replace_original_title, 0, 0)

        self.cb_overwrite_existing_original_title = QCheckBox(
            "Overwrite existing values", self
        )
        checkboxes_layout.addWidget(self.cb_overwrite_existing_original_title, 1, 0)

        self.cb_replace_original_artist = QCheckBox("Replace original artists", self)
        self.cb_replace_original_artist.setChecked(True)
        checkboxes_layout.addWidget(self.cb_replace_original_artist, 0, 1)

        self.cb_overwrite_existing_original_artist = QCheckBox(
            "Overwrite existing values", self
        )
        checkboxes_layout.addWidget(self.cb_overwrite_existing_original_artist, 1, 1)

        return checkboxes_layout

    def create_buttons_layout(self):
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)  # Increase horizontal spacing between buttons
        buttons_layout.setContentsMargins(
            0, 10, 0, 0
        )  # Add top margin to move buttons up

        self.btn_open_in_musicbrainz = QPushButton("MusicBrains", self)
        self.btn_open_in_musicbrainz.setFixedSize(90, 30)
        self.btn_open_in_musicbrainz.clicked.connect(self.open_in_musicbrainz)
        buttons_layout.addWidget(self.btn_open_in_musicbrainz)

        self.btn_convert_to_simple_artist = QPushButton("Convert", self)
        self.btn_convert_to_simple_artist.setFixedSize(90, 30)
        self.btn_convert_to_simple_artist.clicked.connect(
            self.convert_track_to_simple_artist
        )
        buttons_layout.addWidget(self.btn_convert_to_simple_artist)

        self.btn_load_files = QPushButton("Load Files", self)
        self.btn_load_files.setFixedSize(120, 30)
        self.btn_load_files.clicked.connect(self.load_files_dialog)
        buttons_layout.addWidget(self.btn_load_files)

        self.btn_save = QPushButton("Save", self)
        self.btn_save.setFixedSize(90, 30)
        self.btn_save.clicked.connect(self.save_changes)
        buttons_layout.addWidget(self.btn_save)

        return buttons_layout

    def create_track_manager(self) -> TrackManager:
        try:
            return TrackManager(self.api_host, self.api_port)
        except Exception as e:
            self.show_toast(
                f"Failed to create a TrackManager object: {str(e)}",
                ToastType.ERROR,
                10000,
            )
            return None

    def run_async_tasks(self):
        """Runs pending asyncio tasks."""
        if not self.is_closing:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop.run_forever()

    async def check_server_health(self):
        try:
            api_is_healthy = await self.track_manager.get_server_health()

            if not api_is_healthy:
                self.show_toast(
                    f"The server is not healthy. Please check the server status.",
                    ToastType.ERROR,
                    10000,
                )
        except httpx.RequestError as e:
            self.show_toast(
                f"Could not reach the server at {self.api_host}:{self.api_port}: {str(e)}",
                ToastType.ERROR,
                10000,
            )
        except Exception as e:
            self.show_toast(
                f"An unexpected error occurred when trying to contact the server: {str(e)}",
                ToastType.ERROR,
                10000,
            )

    def open_in_musicbrainz(self) -> None:
        selected_indexes = self.track_view.selectedIndexes()
        if selected_indexes:
            selected_index = selected_indexes[0]
            if selected_index.isValid():
                item = selected_index.internalPointer()
                try:
                    url = self.track_model.get_musicbrainz_url(item)
                    if url:
                        webbrowser.open(url)
                    else:
                        self.show_toast(
                            "No URL available for this track.", ToastType.INFO
                        )
                except Exception as e:
                    self.show_toast(f"{str(e)}", ToastType.ERROR, 10000)

    def convert_track_to_simple_artist(self) -> None:
        async def run(track_item):
            try:
                await self.track_model.convert_track_to_simple_artist(
                    track_item,
                    self.cb_replace_original_title.isChecked(),
                    self.cb_overwrite_existing_original_title.isChecked(),
                    self.cb_replace_original_artist.isChecked(),
                    self.cb_overwrite_existing_original_artist.isChecked(),
                )
                self.track_view.expandAll()
            except Exception as e:
                self.show_toast(f"{str(e)}", ToastType.ERROR, 10000)

        selected_indexes = self.track_view.selectedIndexes()
        if selected_indexes:
            selected_index = selected_indexes[0]
            if selected_index.isValid():
                track_item = selected_index.internalPointer()
                if isinstance(track_item, TrackDetails):
                    asyncio.ensure_future(run(track_item), loop=self.loop)

    def save_changes(self) -> None:
        async def run():
            try:
                await self.track_model.save_files()
                self.show_toast(
                    f"Successfully updated all files!", ToastType.SUCCESS, 500
                )
            except Exception as e:
                self.show_toast(f"{str(e)}", ToastType.ERROR, 10000)

        asyncio.ensure_future(run(), loop=self.loop)

    def load_files(self, files: list[str]) -> None:
        async def load_and_update():
            await self.check_server_health()

            try:
                await self.track_model.load_files(
                    files,
                    self.cb_replace_original_title.isChecked(),
                    self.cb_overwrite_existing_original_title.isChecked(),
                    self.cb_replace_original_artist.isChecked(),
                    self.cb_overwrite_existing_original_artist.isChecked(),
                    True,
                )
            except Exception as e:
                self.show_toast(f"{str(e)}", ToastType.ERROR, 10000)

            self.track_view.expandAll()

        asyncio.ensure_future(load_and_update(), loop=self.loop)

    def load_files_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files", "", "MP3 Files (*.mp3)"
        )
        if files:
            self.clear_data()
            self.load_files(files)

    def clear_data(self) -> TrackModel:
        self.track_manager = TrackManager(host=self.api_host, port=self.api_port)
        self.track_model = TrackModel(self.track_manager)
        self.track_view.setModel(self.track_model)

    def show_toast(
        self, message: str, toast_type: ToastType, duration: int = 3000
    ) -> None:
        if self.toast and self.toast.isVisible():
            self.toast.hide()

        self.toast = Toast(
            message, toast_type=toast_type, duration=duration, parent=self
        )
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
                        self.track_model.remove_track(track_item)
                        self.track_view.expandAll()

    def moveEvent(self, event):
        if self.toast and self.toast.isVisible():
            self.toast.update_position(self.geometry())

    def resizeEvent(self, event):
        if self.toast and self.toast.isVisible():
            self.toast.update_position(self.geometry())

    def closeEvent(self, event):
        """Handle the window close event to stop the asyncio event loop and exit the application."""
        self.is_closing = True
        self.timer.stop()
        self.loop.stop()
        self.loop.close()
        self.app.quit()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files = []
        for url in urls:
            local_path = url.toLocalFile()
            if os.path.isdir(local_path):
                for root, _, filenames in os.walk(local_path):
                    for filename in filenames:
                        if filename.lower().endswith(".mp3"):
                            files.append(os.path.join(root, filename))
            elif os.path.isfile(local_path) and local_path.lower().endswith(".mp3"):
                files.append(local_path)

        if files:
            self.load_files(files)


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
    main_window = MainWindow(app, api_host, api_port)

    try:
        main_window.loop.run_forever()
    except RuntimeError as e:
        print(f"Caught RuntimeError when the loop was closed: {e}")


if __name__ == "__main__":
    main()
