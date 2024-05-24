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
        self.progress_bar_value = 100

        self.setup_ui()
        self.setup_animations()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setSpacing(0)  # Remove spacing between widgets

        self.label = QLabel(self.message, self)
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(self.progress_bar_value)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(5)
        layout.addWidget(self.progress_bar)

        self.set_toast_color()
        self.setLayout(layout)
        self.adjustSize()

    def setup_animations(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)

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
            border-top-left-radius: 2px;
            border-top-right-radius: 2px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        """

        match self.toast_type:
            case ToastType.ERROR:
                self.label.setStyleSheet(f"background-color: red; {base_stylesheet}")
                self.progress_bar.setStyleSheet(
                    "QProgressBar::chunk { background-color: darkred; }"
                )
            case ToastType.WARNING:
                self.label.setStyleSheet(f"background-color: orange; {base_stylesheet}")
                self.progress_bar.setStyleSheet(
                    "QProgressBar::chunk { background-color: darkorange; }"
                )
            case ToastType.INFORMATION:
                self.label.setStyleSheet(f"background-color: blue; {base_stylesheet}")
                self.progress_bar.setStyleSheet(
                    "QProgressBar::chunk { background-color: darkblue; }"
                )
            case ToastType.SUCCESS:
                self.label.setStyleSheet(f"background-color: green; {base_stylesheet}")
                self.progress_bar.setStyleSheet(
                    "QProgressBar::chunk { background-color: darkgreen; }"
                )

        self.progress_bar.setStyleSheet(
            self.progress_bar.styleSheet()
            + """
            QProgressBar {
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
                background-color: rgba(0, 0, 0, 0); /* Transparent background */
            }
        """
        )

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

    def update_progress(self):
        self.elapsed_time += self.duration // 100
        self.progress_bar_value = max(
            0, 100 - (self.elapsed_time * 100 // self.duration)
        )
        self.progress_bar.setValue(self.progress_bar_value)
        if self.progress_bar_value == 0:
            self.hide()

    def update_position(self, parent_rect):
        top_center = QPoint(
            parent_rect.center().x() - self.rect().width() // 2, parent_rect.top() + 10
        )
        self.move(top_center)

    def mousePressEvent(self, event):
        self.fast_fade_out.start()
        event.accept()
