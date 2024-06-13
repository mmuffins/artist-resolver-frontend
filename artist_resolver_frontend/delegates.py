from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtGui import (
    QPalette,
    QColor,
    QPainter,
)
from PyQt6.QtWidgets import (
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QComboBox,
)
from artist_resolver.trackmanager import (
    MbArtistDetails,
    SimpleArtistDetails,
)


class ArtistDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.model = model
        self.custom_name_column = self.model.get_artist_column("custom_name")

    def apply_simple_artist_condition(self, artist, option):
        if not isinstance(artist, SimpleArtistDetails):
            return False

        if artist.has_server_data:
            # set to purple if artist was updated from server
            option.palette.setColor(QPalette.ColorRole.Text, QColor(164, 97, 240))
            return True
        else:
            # set to red if the artist was not edited
            option.palette.setColor(QPalette.ColorRole.Text, QColor(255, 23, 62))
            return True
        return False

    def apply_mbartist_condition(self, artist, option):
        if not isinstance(artist, MbArtistDetails) or isinstance(
            artist, SimpleArtistDetails
        ):
            return False

        if artist.has_server_data:
            # set to purple if artist was updated from server
            option.palette.setColor(QPalette.ColorRole.Text, QColor(164, 97, 240))
            return True
        else:
            # set to blue if artist was not updated from server but has mbartist details
            option.palette.setColor(QPalette.ColorRole.Text, QColor(0, 128, 255))
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
            # set to orange if the artist is likely to be an incorrect relation
            option.palette.setColor(QPalette.ColorRole.Text, QColor(255, 128, 0))
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

                color_modified |= self.apply_simple_artist_condition(artist, option)
                color_modified |= self.apply_mbartist_condition(artist, option)
                color_modified |= self.apply_custom_name_edited_true_condition(
                    artist, option
                )
                color_modified |= self.apply_invalid_relation_true_condition(
                    artist, option
                )

            # Apply the include condition last
            self.apply_include_condition(artist, option, color_modified)

        super().paint(painter, option, index)


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.model = model
        self.type_column = self.model.get_artist_column("type")

    def createEditor(self, parent, option, index):
        if index.column() == self.type_column:
            comboBox = QComboBox(parent)
            comboBox.addItems(["Person", "Character", "Group"])
            return comboBox
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if index.column() == self.type_column:
            value = index.model().data(index, Qt.ItemDataRole.EditRole)
            if isinstance(value, str):
                editor.setCurrentText(value)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == self.type_column:
            value = editor.currentText()
            model.setData(index, value, Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)
