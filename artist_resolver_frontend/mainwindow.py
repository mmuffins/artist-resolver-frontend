import os
import asyncio
import httpx
import webbrowser
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import (
    QKeyEvent,
    QFontDatabase,
    QDragEnterEvent,
    QDropEvent,
)
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QGridLayout,
)
from artist_resolver.trackmanager import (
    TrackManager,
    TrackDetails,
)
from artist_resolver_frontend import (
    HttpServer,
    ArtistDelegate,
    ComboBoxDelegate,
    CustomTreeView,
    TrackModel,
    Toast,
    ToastType,
)


class MainWindow(QMainWindow):
    stylesheet = "./styles.qss"
    server_port = 23408

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

        self.http_server = HttpServer(self, "localhost", self.server_port, self.loop)
        self.http_server.start_server()
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
        self.track_view.setItemDelegateForColumn(
            self.track_model.get_artist_column("type"),
            ComboBoxDelegate(self.track_view, self.track_model),
        )

        self.layout.addWidget(self.track_view)

        self.add_actions_layout()

        self.clear_data()
        self.apply_column_width()

        QFontDatabase.addApplicationFont("font/NotoSansJP-Regular.ttf")
        QFontDatabase.addApplicationFont("font/NotoSansJP-Bold.ttf")
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

        self.btn_clear_data = QPushButton("Clear", self)
        self.btn_clear_data.setFixedSize(90, 30)
        self.btn_clear_data.clicked.connect(self.clear_data)
        buttons_layout.addWidget(self.btn_clear_data)

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
                    self.show_toast(f"{str(e)}", ToastType.ERROR, 1000)

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
