from artist_resolver.trackmanager import (
    TrackDetails,
    MbArtistDetails,
    SimpleArtistDetails,
)
from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex


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
        if isinstance(item, TrackDetails) and item.mb_track_id:
            return f"{base_url}/track/{item.mb_track_id}"

        if (
            isinstance(item, dict)
            and isinstance(item["artist"], MbArtistDetails)
            and not isinstance(item["artist"], SimpleArtistDetails)
            and item["artist"]
            and item["artist"].mbid
        ):
            mbid = item["artist"].mbid
            return f"{base_url}/artist/{mbid}"

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
