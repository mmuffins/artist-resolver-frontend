from enum import Enum
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QEasingCurve,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
)


class ToastType(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"
    SUCCESS = "success"


class Toast(QWidget):
    def __init__(
        self, message, toast_type=ToastType.INFORMATION, duration=3000, parent=None
    ):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.message = message
        self.duration = duration
        self.toast_type = toast_type

        self.elapsed_time = 0

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
        self.timer = QTimer(self)

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

    def set_toast_color(self):
        base_stylesheet = """
            color: white;
            padding: 20px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            border-bottom-left-radius: 5px;
            border-bottom-right-radius: 5px;
            font-size: 16px;
            font-weight: bold;
        """

        match self.toast_type:
            case ToastType.ERROR:
                self.label.setStyleSheet(f"background-color: red; {base_stylesheet}")
            case ToastType.WARNING:
                self.label.setStyleSheet(f"background-color: orange; {base_stylesheet}")
            case ToastType.INFORMATION:
                self.label.setStyleSheet(f"background-color: blue; {base_stylesheet}")
            case ToastType.SUCCESS:
                self.label.setStyleSheet(f"background-color: green; {base_stylesheet}")

    def showEvent(self, event):
        self.animation_group.start()
        self.timer.start(self.duration // 100)
        super().showEvent(event)

    def show(self):
        self.setWindowOpacity(0)
        super().show()
        self.raise_()

    def hide(self):
        self.timer.stop()
        super().hide()

    def update_position(self, parent_rect):
        top_center = QPoint(
            parent_rect.center().x() - self.rect().width() // 2, parent_rect.top() + 10
        )
        self.move(top_center)

    def mousePressEvent(self, event):
        self.fast_fade_out.start()
        event.accept()
