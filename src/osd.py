"""
Lenovo Vantage Pro - Floating Luxury On-Screen Display (OSD)
Theme: Obsidian Titanium Luxury
Frameless, translucent floating HUD with dynamic glow and hardware mode feedback.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QApplication
)
from PyQt6.QtCore import (
    Qt, QRectF, QPropertyAnimation, QSequentialAnimationGroup, QPauseAnimation
)
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QPen, QPainterPath
)
from i18n import tr

def get_osd_preset(preset_key: str) -> dict:
    presets = {
        "extreme": {
            "title": tr("osd_perf_title"),
            "subtitle": tr("osd_perf_sub"),
            "icon": "🚀",
            "color": "#ef4444"
        },
        "standard": {
            "title": tr("osd_std_title"),
            "subtitle": tr("osd_std_sub"),
            "icon": "⚖️",
            "color": "#38bdf8"
        },
        "silent": {
            "title": tr("osd_silent_title"),
            "subtitle": tr("osd_silent_sub"),
            "icon": "🍃",
            "color": "#10b981"
        },
        "165hz": {
            "title": tr("osd_165hz_title"),
            "subtitle": tr("osd_165hz_sub"),
            "icon": "⚡",
            "color": "#38bdf8"
        },
        "60hz": {
            "title": tr("osd_60hz_title"),
            "subtitle": tr("osd_60hz_sub"),
            "icon": "🔋",
            "color": "#10b981"
        },
        "gamemode": {
            "title": tr("osd_game_start_title"),
            "subtitle": tr("osd_game_start_sub", name="Steam / Proton"),
            "icon": "🎮",
            "color": "#f59e0b"
        },
        "gamemode_off": {
            "title": tr("osd_game_stop_title"),
            "subtitle": tr("osd_game_stop_sub"),
            "icon": "🎮",
            "color": "#64748b"
        },
        "dust_purge": {
            "title": tr("osd_purge_title"),
            "subtitle": tr("osd_purge_sub"),
            "icon": "🌪️",
            "color": "#a855f7"
        },
        "no_turbo_on": {
            "title": tr("osd_noturbo_on_title"),
            "subtitle": tr("osd_noturbo_on_sub"),
            "icon": "❄️",
            "color": "#38bdf8"
        },
        "no_turbo_off": {
            "title": tr("osd_noturbo_off_title"),
            "subtitle": tr("osd_noturbo_off_sub"),
            "icon": "⚡",
            "color": "#f59e0b"
        }
    }
    return presets.get(preset_key, {})


class FloatingLuxuryOSD(QWidget):
    """
    Floating Luxury On-Screen Display HUD for instant tactile feedback on mode toggles.
    Obsidian Titanium styling with hardware-accelerated translucent animations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedSize(360, 95)

        self._accent_color = QColor("#38bdf8")
        self._accent_hex = "#38bdf8"

        self._init_ui()
        self._setup_animation()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 18, 14)
        main_layout.setSpacing(14)

        # Left: Icon Badge with soft halo glow
        self.icon_badge = QFrame(self)
        self.icon_badge.setFixedSize(54, 54)
        badge_layout = QVBoxLayout(self.icon_badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_icon = QLabel("⚡", self.icon_badge)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 26px; background: transparent; border: none;")
        badge_layout.addWidget(self.lbl_icon)

        # Right: Typography Column
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 2, 0, 2)
        text_layout.setSpacing(3)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_title = QLabel("PERFORMANCE MODE", self)
        self.lbl_title.setStyleSheet("""
            color: #f8fafc;
            font-size: 13px;
            font-weight: 900;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            background: transparent;
            border: none;
        """)

        self.lbl_subtitle = QLabel("100% Turbin Penuh • 85W TGP Unlocked", self)
        self.lbl_subtitle.setStyleSheet("""
            color: #94a3b8;
            font-size: 11px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        self.lbl_subtitle.setWordWrap(True)

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_subtitle)

        main_layout.addWidget(self.icon_badge)
        main_layout.addLayout(text_layout, stretch=1)

    def _setup_animation(self):
        self._anim_group = QSequentialAnimationGroup(self)

        # Fade-in: 120ms (0.0 -> 0.95)
        self._fade_in = QPropertyAnimation(self, b"windowOpacity")
        self._fade_in.setDuration(120)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(0.95)

        # Hold / Stay: 1.2 seconds (1200ms)
        self._pause = QPauseAnimation(1200)

        # Fade-out: 200ms (0.95 -> 0.0)
        self._fade_out = QPropertyAnimation(self, b"windowOpacity")
        self._fade_out.setDuration(200)
        self._fade_out.setStartValue(0.95)
        self._fade_out.setEndValue(0.0)

        self._anim_group.addAnimation(self._fade_in)
        self._anim_group.addAnimation(self._pause)
        self._anim_group.addAnimation(self._fade_out)
        self._anim_group.finished.connect(self.hide)

    def _reposition(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            # Top-center position with ergonomic 52px status margin
            x = geom.x() + (geom.width() - self.width()) // 2
            y = geom.y() + 52
            self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(1.0, 1.0, self.width() - 2.0, self.height() - 2.0)
        path = QPainterPath()
        path.addRoundedRect(rect, 16.0, 16.0)

        # Background: Obsidian #090d16 with 94% alpha (240 / 255)
        bg_color = QColor(9, 13, 22, int(255 * 0.94))
        painter.fillPath(path, QBrush(bg_color))

        # Precision 1.5px solid border in current accent color
        pen = QPen(self._accent_color, 1.5)
        painter.setPen(pen)
        painter.drawPath(path)

    def show_notification(self, title: str, subtitle: str, icon_symbol: str, accent_color: str = "#38bdf8"):
        """
        Trigger the luxury OSD display with specified content and accent styling.
        """
        self._accent_hex = accent_color
        self._accent_color = QColor(accent_color)

        self.lbl_title.setText(title)
        self.lbl_subtitle.setText(subtitle)
        self.lbl_icon.setText(icon_symbol)

        # Accent glow box
        self.icon_badge.setStyleSheet(f"""
            QFrame {{
                background-color: {accent_color}18;
                border: 1.2px solid {accent_color}55;
                border-radius: 12px;
            }}
        """)

        self._reposition()
        self.update()

        if self._anim_group.state() == QSequentialAnimationGroup.State.Running:
            self._anim_group.stop()

        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._anim_group.start()

    # Preset convenience methods
    def notify_preset(self, preset_key: str):
        cfg = get_osd_preset(preset_key)
        if cfg:
            self.show_notification(
                title=cfg["title"],
                subtitle=cfg["subtitle"],
                icon_symbol=cfg["icon"],
                accent_color=cfg["color"]
            )

    def notify_mode(self, mode: str):
        key = mode.lower()
        if key in ("extreme", "performance", "perf", "2"):
            self.notify_preset("extreme")
        elif key in ("quiet", "silent", "eco", "1"):
            self.notify_preset("silent")
        else:
            self.notify_preset("standard")

    def notify_refresh_rate(self, hz: int):
        if hz >= 120:
            self.notify_preset("165hz")
        else:
            self.notify_preset("60hz")

    def notify_game_mode(self, active: bool, game_name: str = ""):
        if active:
            name_disp = game_name if game_name else "Steam / Proton"
            sub = tr("osd_game_start_sub", name=name_disp)
            self.show_notification(tr("osd_game_start_title"), sub, "🎮", "#f59e0b")
        else:
            self.notify_preset("gamemode_off")

    def notify_dust_purge(self):
        self.notify_preset("dust_purge")

    def notify_no_turbo(self, active: bool):
        if active:
            self.notify_preset("no_turbo_on")
        else:
            self.notify_preset("no_turbo_off")


_global_osd_instance = None

def get_osd(parent=None) -> FloatingLuxuryOSD:
    """
    Get or create the singleton instance of FloatingLuxuryOSD.
    """
    global _global_osd_instance
    if _global_osd_instance is None:
        _global_osd_instance = FloatingLuxuryOSD(parent)
    return _global_osd_instance
