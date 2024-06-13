from enum import Enum
from PyQt6.QtCore import (
    Qt,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QEasingCurve,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)


class ToastType(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "information"
    SUCCESS = "success"


class Toast(QWidget):
    stylesheet = "./styles.qss"

    def __init__(self, message, toast_type=ToastType.INFO, duration=3000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.message = message
        self.duration = duration
        self.toast_type = toast_type

        self.setup_ui()
        self.setup_animations()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.label = QLabel(self.message, self)
        layout.addWidget(self.label)

        self.set_toast_color()
        self.setLayout(layout)
        self.adjustSize()

    def setup_animations(self):

        self.animation_group = QSequentialAnimationGroup()

        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(500)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.fast_fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fast_fade_out.setDuration(200)
        self.fast_fade_out.setStartValue(1)
        self.fast_fade_out.setEndValue(0)
        self.fast_fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fast_fade_out.finished.connect(self.hide)

        self.animation_group.addAnimation(self.fade_in)
        self.animation_group.addPause(self.duration)
        self.animation_group.addAnimation(self.fade_out)
        self.animation_group.finished.connect(self.hide)

    def apply_styles(self):
        try:
            with open(self.stylesheet, "r") as file:
                style_sheet = file.read()
                self.setStyleSheet(style_sheet)
                self.app.setStyleSheet(style_sheet)
        except Exception as e:
            print(f"Error loading stylesheet: {e}")

    def set_toast_color(self):
        base_class = "toast"

        match self.toast_type:
            case ToastType.ERROR:
                self.label.setProperty("class", f"{base_class} toast-error")
            case ToastType.WARNING:
                self.label.setProperty("class", f"{base_class} toast-warning")
            case ToastType.INFO:
                self.label.setProperty("class", f"{base_class} toast-information")
            case ToastType.SUCCESS:
                self.label.setProperty("class", f"{base_class} toast-success")

        self.label.setStyleSheet("")  # Apply the style

    def showEvent(self, event):
        self.animation_group.start()
        super().showEvent(event)

    def show(self):
        self.setWindowOpacity(0)
        super().show()
        self.raise_()

    def hide(self):
        super().hide()

    def update_position(self, parent_rect):
        top_center = QPoint(
            parent_rect.center().x() - self.rect().width() // 2, parent_rect.top() + 10
        )
        self.move(top_center)

    def mousePressEvent(self, event):
        self.fast_fade_out.start()
        event.accept()
