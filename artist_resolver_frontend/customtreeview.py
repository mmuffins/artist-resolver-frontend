from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QTreeView,
)
from artist_resolver_frontend import (
    ToastType
)


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
