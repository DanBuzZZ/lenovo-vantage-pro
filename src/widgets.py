import math
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QTimer
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont, QLinearGradient, QRadialGradient, QPainterPath, QPixmap
)
from i18n import tr, get_current_language


class RadialMeter(QWidget):
    """
    Vector-drawn 240-degree circular arc gauge with dynamic color transitions.
    """
    def __init__(self, title: str, unit: str = "%", max_val: float = 100.0, parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.max_val = max_val
        self._value = 0.0
        self._subtitle = ""
        self._accent_color = QColor("#38bdf8")
        self.setFixedSize(140, 155)

    def set_title(self, title: str):
        self.title = title
        self.update()

    def set_value(self, val: float, subtitle: str = "", color: str = None):
        self._value = max(0.0, min(float(val), self.max_val))
        self._subtitle = subtitle
        if color:
            self._accent_color = QColor(color)
        else:
            pct = (self._value / self.max_val) * 100
            if pct > 80:
                self._accent_color = QColor("#f43f5e")
            elif pct > 65:
                self._accent_color = QColor("#f59e0b")
            else:
                self._accent_color = QColor("#38bdf8")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        size = 110.0
        margin_x = (w - size) / 2.0
        margin_y = 10.0
        rect = QRectF(margin_x, margin_y, size, size)

        start_angle = -210 * 16
        span_angle_full = -240 * 16
        pct = max(0.0, min(1.0, self._value / self.max_val))
        span_angle_active = int(span_angle_full * pct)

        # Background track
        pen_track = QPen(QColor("#1e293b"), 8)
        pen_track.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_track)
        painter.drawArc(rect, start_angle, span_angle_full)

        # Active progress arc
        if pct > 0.005:
            pen_active = QPen(self._accent_color, 8)
            pen_active.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_active)
            painter.drawArc(rect, start_angle, span_angle_active)

        # Center Text (Value & Unit)
        painter.setPen(QColor("#ffffff"))
        font_val = QFont("-apple-system, Segoe UI, sans-serif", 18, QFont.Weight.Bold)
        painter.setFont(font_val)

        val_text = f"{int(self._value)}" if self._value == int(self._value) else f"{self._value:.1f}"
        if self.unit == "°C":
            val_text += "°"
        elif self.unit == "%":
            val_text += "%"
        painter.drawText(QRectF(margin_x, margin_y + 32, size, 30), Qt.AlignmentFlag.AlignCenter, val_text)

        # Sub-indicator
        painter.setPen(QColor("#94a3b8"))
        font_sub = QFont("-apple-system, Segoe UI, sans-serif", 9, QFont.Weight.DemiBold)
        painter.setFont(font_sub)
        sub_txt = self._subtitle if self._subtitle else (self.unit if self.unit not in ["%", "°C"] else "")
        painter.drawText(QRectF(margin_x, margin_y + 60, size, 20), Qt.AlignmentFlag.AlignCenter, sub_txt)

        # Bottom Title Label
        painter.setPen(QColor("#cbd5e1"))
        font_title = QFont("-apple-system, Segoe UI, sans-serif", 10, QFont.Weight.Bold)
        painter.setFont(font_title)
        painter.drawText(QRectF(0, h - 25, w, 22), Qt.AlignmentFlag.AlignCenter, self.title.upper())


class ModernToggle(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self.update()
            self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_color = QColor("#0284c7") if self._checked else QColor("#1e293b")
        painter.setBrush(QBrush(track_color))
        border_pen = QPen(QColor("#38bdf8") if self._checked else QColor("#334155"), 1)
        painter.setPen(border_pen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 13, 13)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#ffffff")))
        x_pos = self.width() - 22 if self._checked else 4
        painter.drawEllipse(x_pos, 4, 18, 18)


class ThermalCockpitCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, mode_id: str, title: str, badge: str, desc: str, accent: str, led_symbol: str, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.accent = accent
        self._is_active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        top = QHBoxLayout()
        self.led = QLabel(f"● {title}")
        self.led.setStyleSheet(f"color: {accent}; font-size: 15px; font-weight: 800; letter-spacing: 0.3px;")

        self.badge_lbl = QLabel(badge)
        self.badge_lbl.setStyleSheet(f"""
            background-color: {accent}22;
            color: {accent};
            border: 1px solid {accent}66;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 700;
        """)
        top.addWidget(self.led)
        top.addStretch()
        top.addWidget(self.badge_lbl)
        layout.addLayout(top)

        self.desc_lbl = QLabel(desc)
        self.desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)

        self.update_style()

    def set_active(self, active: bool):
        self._is_active = active
        self.update_style()

    def update_style(self):
        if self._is_active:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #111e38;
                    border: 2px solid {self.accent};
                    border-radius: 14px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame {{
                    background-color: #0f172a;
                    border: 1px solid #1e293b;
                    border-radius: 14px;
                }}
                QFrame:hover {{
                    border-color: #334155;
                    background-color: #141f35;
                }}
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.mode_id)


class QuickToggleCard(QFrame):
    toggled = pyqtSignal(bool)

    def __init__(self, icon_char: str, title: str, desc: str, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 12px;
                padding: 14px 18px;
            }
            QFrame:hover {
                border-color: #334155;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        icon_box = QLabel(icon_char)
        icon_box.setStyleSheet("""
            background-color: #162032;
            color: #38bdf8;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 700;
            padding: 8px 10px;
        """)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_box)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 700;")
        self.desc_lbl = QLabel(desc)
        self.desc_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.desc_lbl.setWordWrap(True)
        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.desc_lbl)
        layout.addLayout(text_layout, stretch=1)

        self.switch = ModernToggle(checked=checked)
        self.switch.toggled.connect(self.toggled.emit)
        layout.addWidget(self.switch, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def update_text(self, title: str, desc: str):
        self.title_lbl.setText(title)
        self.desc_lbl.setText(desc)

    def setChecked(self, checked: bool):
        self.switch.setChecked(checked)

    def isChecked(self) -> bool:
        return self.switch.isChecked()


class CoolingDynamicsCard(QFrame):
    boost_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 14px;
                padding: 16px 20px;
            }
            QFrame:hover {
                border-color: #334155;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(18)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        self.icon_lbl = QLabel("❄️")
        self.icon_lbl.setStyleSheet("font-size: 16px;")
        self.title_lbl = QLabel("ACPI Embedded Controller Thermal Dynamics")
        self.title_lbl.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 700;")
        header_row.addWidget(self.icon_lbl)
        header_row.addWidget(self.title_lbl)
        header_row.addStretch()
        left_layout.addLayout(header_row)

        self.desc_lbl = QLabel("Dynamic Smooth (Hysteresis Damped, 45W/65W - No Surging)")
        self.desc_lbl.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 600;")
        left_layout.addWidget(self.desc_lbl)

        pills_row = QHBoxLayout()
        pills_row.setSpacing(10)
        self.pill_power = QLabel("PL1: 45W | PL2: 65W")
        self.pill_power.setStyleSheet("background-color: #162032; color: #94a3b8; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600;")
        self.pill_epp = QLabel("EPP: balance_power")
        self.pill_epp.setStyleSheet("background-color: #162032; color: #94a3b8; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600;")
        self.pill_wmi = QLabel("WMI: GameZone 0x2C Sync")
        self.pill_wmi.setStyleSheet("background-color: #162032; color: #10b981; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600;")

        pills_row.addWidget(self.pill_power)
        pills_row.addWidget(self.pill_epp)
        pills_row.addWidget(self.pill_wmi)
        pills_row.addStretch()
        left_layout.addLayout(pills_row)

        layout.addLayout(left_layout, stretch=1)

        boost_layout = QVBoxLayout()
        boost_layout.setSpacing(4)
        boost_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_b = QLabel("TURBO BOOST")
        lbl_b.setStyleSheet("color: #cbd5e1; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;")
        self.switch_boost = ModernToggle()
        self.switch_boost.toggled.connect(self.boost_toggled.emit)
        boost_layout.addWidget(lbl_b, alignment=Qt.AlignmentFlag.AlignCenter)
        boost_layout.addWidget(self.switch_boost, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(boost_layout)

    def update_telemetry(self, data: dict):
        self.desc_lbl.setText(data.get("description", "Standard Automatic Cooling"))
        pl1 = data.get("pl1_w", 45.0)
        pl2 = data.get("pl2_w", 65.0)
        self.pill_power.setText(f"PL1: {pl1}W | PL2: {pl2}W")
        self.pill_epp.setText(f"EPP: {data.get('epp', 'balance_power')}")
        prof = data.get("profile", "balanced")
        is_perf = (prof == "performance")
        if self.switch_boost.isChecked() != is_perf:
            self.switch_boost.setChecked(is_perf)


class FanModeCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, mode_id: str, icon_str: str, title: str, subtitle: str, desc: str, accent: str, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.icon_str = icon_str
        self.accent = accent
        self._is_active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(5)

        # Header Row: Icon + Title + Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self.title_lbl = QLabel(f"{icon_str} {title}")
        self.title_lbl.setStyleSheet("color: #f8fafc; font-size: 13px; font-weight: 800; letter-spacing: 0.3px;")

        self.badge_lbl = QLabel("STANDBY")
        self.badge_lbl.setStyleSheet("""
            background-color: #1e293b;
            color: #94a3b8;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 9px;
            font-weight: 800;
        """)

        top_row.addWidget(self.title_lbl)
        top_row.addStretch()
        top_row.addWidget(self.badge_lbl)
        layout.addLayout(top_row)

        # Subtitle
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet(f"color: {accent}; font-size: 11px; font-weight: 700;")
        layout.addWidget(self.sub_lbl)

        # Description
        self.desc_lbl = QLabel(desc)
        self.desc_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; line-height: 1.3;")
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)
        layout.addStretch()

        self.update_style()

    def update_text(self, title: str, subtitle: str, desc: str = ""):
        self.title_lbl.setText(f"{self.icon_str} {title}")
        self.sub_lbl.setText(subtitle)
        if desc:
            self.desc_lbl.setText(desc)

    def set_active(self, active: bool, badge_text: str = None):
        self._is_active = active
        if badge_text:
            self.badge_lbl.setText(badge_text)
        else:
            active_word = "ACTIVE" if get_current_language() == "en" else "AKTIF"
            self.badge_lbl.setText(active_word if active else "STANDBY")

        if active:
            self.badge_lbl.setStyleSheet(f"""
                background-color: {self.accent}22;
                color: {self.accent};
                border: 1px solid {self.accent}88;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: 800;
            """)
        else:
            self.badge_lbl.setStyleSheet("""
                background-color: #1e293b;
                color: #64748b;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: 800;
            """)
        self.update_style()

    def update_style(self):
        if self._is_active:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #111e38;
                    border: 2px solid {self.accent};
                    border-radius: 12px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame {{
                    background-color: #0f172a;
                    border: 1px solid #1e293b;
                    border-radius: 12px;
                }}
                QFrame:hover {{
                    border-color: #334155;
                    background-color: #141f35;
                }}
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.mode_id)


class TurbineGauge(QWidget):
    """
    Circular tachometer gauge with continuously rotating aerodynamic aerofoil fan blades (60 FPS),
    outer temperature gradient ring (Sapphire <50°C -> Amber 50-70°C -> Crimson >70°C),
    and center telemetry readout.
    """
    def __init__(self, title_or_parent=None, fan_id: str = "fan", parent=None, title: str = None):
        if isinstance(title_or_parent, QWidget):
            super().__init__(title_or_parent)
            self.title = title or ""
            self.fan_id = fan_id
        else:
            super().__init__(parent)
            self.title = title if title is not None else (str(title_or_parent) if title_or_parent is not None else "")
            self.fan_id = fan_id

        self.setFixedSize(190, 195)
        self._rpm = 0
        self._display_rpm = 0.0
        self._temp_c = 42.0
        self._subtitle = self.title
        self._power_w = 0.0
        self._angle = 0.0
        self._rot_speed = 0.0
        self._target_rot_speed = 0.0
        self._blades_pixmap = None
        self._blades_color = None
        self._dial_pixmap = None
        self._dial_color = None

        # Efficient smooth rotation timer (25 FPS)
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._on_animation_frame)
        self._timer.start()

    def set_title(self, title: str):
        self.title = title
        self._subtitle = title
        self.update()

    def set_status(self, rpm: int, temp: float, level: int = 0, power_w: float = 0.0):
        sub = self.title if self.title else f"Level {level}/15"
        self.set_telemetry(rpm=rpm, temp_c=temp, subtitle=sub, power_w=power_w)

    def set_telemetry(self, rpm: int, temp_c: float, subtitle: str = "", power_w: float = 0.0):
        self._rpm = max(0, int(rpm))
        self._temp_c = float(temp_c)
        if subtitle:
            self._subtitle = subtitle
        self._power_w = float(power_w)
        if self._rpm > 0:
            self._target_rot_speed = max(0.8, min(8.0, (self._rpm / 3000.0) * 3.0))
        else:
            self._target_rot_speed = 0.0
        self.update()

    def _on_animation_frame(self):
        if not self.isVisible():
            return
        self._rot_speed += (self._target_rot_speed - self._rot_speed) * 0.1
        self._display_rpm += (self._rpm - self._display_rpm) * 0.12
        if abs(self._rot_speed) > 0.01:
            self._angle = (self._angle + self._rot_speed) % 360.0
            self.update()
        elif abs(self._display_rpm - self._rpm) > 1.0:
            self.update()

    def _render_blades_pixmap(self, temp_color: QColor) -> QPixmap:
        size = 160
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = size / 2.0
        cy = size / 2.0
        r_hub = 40.0
        r_tip = 68.0
        num_blades = 9

        p.translate(cx, cy)
        for i in range(num_blades):
            p.save()
            p.rotate(i * (360.0 / num_blades))

            blade = QPainterPath()
            blade.moveTo(r_hub - 2.0, -2.5)
            blade.cubicTo(r_hub + 10.0, 6.5, r_tip - 8.0, 8.5, r_tip, 3.0)
            blade.quadTo(r_tip + 2.0, 0.0, r_tip, -2.0)
            blade.cubicTo(r_tip - 9.0, 0.5, r_hub + 8.0, -4.0, r_hub - 2.0, -2.5)
            blade.closeSubpath()

            grad = QLinearGradient(r_hub, 0, r_tip, 0)
            grad.setColorAt(0.0, QColor(15, 23, 42, 180))
            grad.setColorAt(0.5, QColor(30, 41, 59, 230))
            grad.setColorAt(1.0, QColor(temp_color.red(), temp_color.green(), temp_color.blue(), 130))

            p.setBrush(QBrush(grad))
            p.setPen(QPen(QColor(temp_color.red(), temp_color.green(), temp_color.blue(), 75), 0.8))
            p.drawPath(blade)
            p.restore()
        p.end()
        return pix

    def _render_dial_pixmap(self, temp_color: QColor) -> QPixmap:
        w = self.width()
        h = self.height()
        pix = QPixmap(w, h)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = w / 2.0
        cy = 92.0
        r_outer = 80.0
        r_hub = 40.0

        # Outer Track
        rect_outer = QRectF(cx - r_outer, cy - r_outer, r_outer * 2.0, r_outer * 2.0)
        start_angle = 225 * 16
        full_span = -270 * 16
        pen_track = QPen(QColor("#141d2e"), 5)
        pen_track.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen_track)
        p.drawArc(rect_outer, start_angle, full_span)

        # Outer Ticks
        for i in range(13):
            tick_angle_deg = 225.0 - (i * (270.0 / 12.0))
            rad = math.radians(tick_angle_deg)
            p.setPen(QPen(QColor("#1e293b"), 1.5))
            x1 = cx + (r_outer + 4.0) * math.cos(rad)
            y1 = cy - (r_outer + 4.0) * math.sin(rad)
            x2 = cx + (r_outer + 8.0) * math.cos(rad)
            y2 = cy - (r_outer + 8.0) * math.sin(rad)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Center Hub
        hub_grad = QRadialGradient(cx, cy, r_hub)
        hub_grad.setColorAt(0.0, QColor("#111827"))
        hub_grad.setColorAt(0.7, QColor("#0b111e"))
        hub_grad.setColorAt(1.0, QColor("#070b12"))
        p.setBrush(QBrush(hub_grad))
        p.setPen(QPen(QColor("#1e293b"), 2))
        p.drawEllipse(QPointF(cx, cy), r_hub, r_hub)

        # Metallic inner accent rim
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(temp_color.red(), temp_color.green(), temp_color.blue(), 80), 1))
        p.drawEllipse(QPointF(cx, cy), r_hub - 3.0, r_hub - 3.0)

        p.end()
        return pix

    def _get_temp_color(self, temp: float) -> QColor:
        if temp < 50.0:
            return QColor("#38bdf8")
        elif temp <= 70.0:
            ratio = (temp - 50.0) / 20.0
            r = int(56 + (245 - 56) * ratio)
            g = int(189 + (158 - 189) * ratio)
            b = int(248 + (11 - 248) * ratio)
            return QColor(r, g, b)
        else:
            ratio = min(1.0, (temp - 70.0) / 18.0)
            r = int(245 + (244 - 245) * ratio)
            g = int(158 + (63 - 158) * ratio)
            b = int(11 + (94 - 11) * ratio)
            return QColor(r, g, b)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = 92.0
        r_outer = 80.0
        r_hub = 40.0

        temp_color = self._get_temp_color(self._temp_c)

        # 1. Static Dial Pixmap
        if self._dial_pixmap is None or self._dial_color != temp_color:
            self._dial_pixmap = self._render_dial_pixmap(temp_color)
            self._dial_color = temp_color
        painter.drawPixmap(0, 0, self._dial_pixmap)

        # 2. Rotating Aerofoil Fan Blades (cached pixmap)
        if self._blades_pixmap is None or self._blades_color != temp_color:
            self._blades_pixmap = self._render_blades_pixmap(temp_color)
            self._blades_color = temp_color

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._angle)
        painter.drawPixmap(QPointF(-self._blades_pixmap.width() / 2.0, -self._blades_pixmap.height() / 2.0), self._blades_pixmap)
        painter.restore()

        # 3. Active Progress Arc
        pct_rpm = min(1.0, max(0.0, self._display_rpm / 5500.0))
        if pct_rpm > 0.005:
            rect_outer = QRectF(cx - r_outer, cy - r_outer, r_outer * 2.0, r_outer * 2.0)
            start_angle = 225 * 16
            full_span = -270 * 16
            active_span = int(full_span * pct_rpm)
            pen_active = QPen(temp_color, 5)
            pen_active.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_active)
            painter.drawArc(rect_outer, start_angle, active_span)

        # 4. Center Readouts
        painter.setPen(QColor("#ffffff"))
        font_rpm = QFont("JetBrains Mono", 14, QFont.Weight.Bold)
        font_rpm.setStyleHint(QFont.StyleHint.Monospace)
        painter.setFont(font_rpm)
        rpm_str = f"{int(round(self._display_rpm))}"
        painter.drawText(QRectF(cx - r_hub, cy - 20, r_hub * 2, 22), Qt.AlignmentFlag.AlignCenter, rpm_str)

        painter.setPen(QColor("#64748b"))
        font_unit = QFont("-apple-system, Segoe UI, sans-serif", 8, QFont.Weight.Bold)
        painter.setFont(font_unit)
        painter.drawText(QRectF(cx - r_hub, cy + 1, r_hub * 2, 11), Qt.AlignmentFlag.AlignCenter, "RPM")

        painter.setPen(temp_color)
        font_sub = QFont("-apple-system, Segoe UI, sans-serif", 8, QFont.Weight.DemiBold)
        painter.setFont(font_sub)
        pwr_text = f"{self._temp_c:.0f}°C  •  {self._power_w:.0f}W"
        painter.drawText(QRectF(cx - r_hub, cy + 14, r_hub * 2, 14), Qt.AlignmentFlag.AlignCenter, pwr_text)

        # 4. Center Hub (Titanium Obsidian core)
        hub_grad = QRadialGradient(cx, cy, r_hub)
        hub_grad.setColorAt(0.0, QColor("#111827"))
        hub_grad.setColorAt(0.7, QColor("#0b111e"))
        hub_grad.setColorAt(1.0, QColor("#070b12"))
        painter.setBrush(QBrush(hub_grad))
        painter.setPen(QPen(QColor("#1e293b"), 2))
        painter.drawEllipse(QPointF(cx, cy), r_hub, r_hub)

        # Metallic inner accent rim
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(temp_color.red(), temp_color.green(), temp_color.blue(), 80), 1))
        painter.drawEllipse(QPointF(cx, cy), r_hub - 3.0, r_hub - 3.0)

        # 5. Center Readouts
        painter.setPen(QColor("#ffffff"))
        font_rpm = QFont("JetBrains Mono", 14, QFont.Weight.Bold)
        font_rpm.setStyleHint(QFont.StyleHint.Monospace)
        painter.setFont(font_rpm)
        rpm_str = f"{int(round(self._display_rpm))}"
        painter.drawText(QRectF(cx - r_hub, cy - 20, r_hub * 2, 22), Qt.AlignmentFlag.AlignCenter, rpm_str)

        painter.setPen(QColor("#64748b"))
        font_unit = QFont("-apple-system, Segoe UI, sans-serif", 8, QFont.Weight.Bold)
        painter.setFont(font_unit)
        painter.drawText(QRectF(cx - r_hub, cy + 1, r_hub * 2, 11), Qt.AlignmentFlag.AlignCenter, "RPM")

        painter.setPen(temp_color)
        font_sub = QFont("-apple-system, Segoe UI, sans-serif", 8, QFont.Weight.DemiBold)
        painter.setFont(font_sub)
        pwr_text = f"{self._temp_c:.0f}°C  •  {self._power_w:.0f}W"
        painter.drawText(QRectF(cx - r_hub, cy + 14, r_hub * 2, 14), Qt.AlignmentFlag.AlignCenter, pwr_text)

        # 6. Bottom Subtitle Badge
        painter.setPen(QColor("#94a3b8"))
        font_bot = QFont("-apple-system, Segoe UI, sans-serif", 8, QFont.Weight.Bold)
        painter.setFont(font_bot)
        bot_txt = self._subtitle.upper() if self._subtitle else "AERODYNAMIC TURBINE"
        painter.drawText(QRectF(0, h - 18, w, 16), Qt.AlignmentFlag.AlignCenter, bot_txt)


class ThermalTrajectoryChart(QFrame):
    """
    Real-time rolling 60-second telemetry spline graph showing thermal trajectory
    (cyan gradient area) alongside gradual stepped fan level curve (amber dashed line).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(195)
        self.setMinimumWidth(320)
        self.setStyleSheet("""
            QFrame {
                background-color: #080d16;
                border: 1px solid #1a2333;
                border-radius: 12px;
            }
        """)
        self._history = []

    def set_history(self, history_points: list):
        self._history = list(history_points) if history_points else []
        self.update()

    def update_history(self, history_points: list):
        self.set_history(history_points)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        top_m = 36
        left_m = 38
        right_m = 42
        bottom_m = 24

        gw = max(10, w - left_m - right_m)
        gh = max(10, h - top_m - bottom_m)

        # 1. Header Row
        painter.setPen(QColor("#94a3b8"))
        font_hdr = QFont("-apple-system, Segoe UI, sans-serif", 9, QFont.Weight.Bold)
        painter.setFont(font_hdr)
        painter.drawText(QRectF(left_m, 12, 450, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         tr("acoustic_trajectory_title"))

        # Legend & Live Badges on Top Right
        latest_temp = 0.0
        latest_lvl = 0
        if self._history:
            latest = self._history[-1]
            latest_temp = latest[1]
            latest_lvl = latest[2]

        legend_font = QFont("-apple-system, Segoe UI, sans-serif", 8, QFont.Weight.DemiBold)
        painter.setFont(legend_font)

        temp_legend = "● Temp (°C)" if get_current_language() == "en" else "● Suhu (°C)"
        painter.setPen(QColor("#38bdf8"))
        painter.drawText(QRectF(w - right_m - 240, 12, 70, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, temp_legend)

        painter.setPen(QColor("#f59e0b"))
        painter.drawText(QRectF(w - right_m - 165, 12, 75, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "--- Fan Lv")

        painter.setPen(QColor("#e2e8f0"))
        cur_str = f"{latest_temp:.0f}°C | Lv.{latest_lvl}"
        painter.drawText(QRectF(w - right_m - 85, 12, 85, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, cur_str)

        # 2. Gridlines & Axes
        axis_font = QFont("-apple-system, Segoe UI, sans-serif", 8, QFont.Weight.DemiBold)
        painter.setFont(axis_font)

        pen_grid_h = QPen(QColor("#162032"), 1, Qt.PenStyle.DashLine)
        temp_ticks = [30.0, 50.0, 70.0, 90.0]
        for t_val in temp_ticks:
            norm_y = (t_val - 30.0) / 60.0
            y = top_m + gh - (norm_y * gh)

            painter.setPen(pen_grid_h)
            painter.drawLine(QPointF(left_m, y), QPointF(left_m + gw, y))

            painter.setPen(QColor("#475569"))
            painter.drawText(QRectF(0, y - 8, left_m - 4, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{int(t_val)}°")

            fan_equiv = int(round((t_val - 30.0) / 60.0 * 15.0))
            painter.drawText(QRectF(left_m + gw + 4, y - 8, right_m - 6, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"Lv.{fan_equiv}")

        pen_grid_v = QPen(QColor("#131b2a"), 1, Qt.PenStyle.SolidLine)
        time_ticks = [(-60.0, "-60s"), (-45.0, "-45s"), (-30.0, "-30s"), (-15.0, "-15s"), (0.0, "NOW")]
        for dt_val, lbl_str in time_ticks:
            norm_x = (dt_val + 60.0) / 60.0
            x = left_m + (norm_x * gw)

            painter.setPen(pen_grid_v)
            painter.drawLine(QPointF(x, top_m), QPointF(x, top_m + gh))

            painter.setPen(QColor("#475569"))
            painter.drawText(QRectF(x - 20, top_m + gh + 4, 40, 16), Qt.AlignmentFlag.AlignCenter, lbl_str)

        # 3. Plot Curves
        if not self._history or len(self._history) < 2:
            empty_msg = "Recording EC cooling dynamics (60s rolling telemetry)..." if get_current_language() == "en" else "Merekam trajektori respons dinamika pendingin EC (60s rolling telemetry)..."
            painter.setPen(QColor("#334155"))
            painter.drawText(QRectF(left_m, top_m, gw, gh), Qt.AlignmentFlag.AlignCenter, empty_msg)
            return

        t_now = self._history[-1][0]
        valid_points = [p for p in self._history if (t_now - p[0]) <= 62.0]
        if len(valid_points) < 2:
            valid_points = self._history[-2:]

        coords_temp = []
        coords_fan = []
        for p in valid_points:
            t_pt = p[0]
            temp_val = float(p[1])
            lvl_val = float(p[2])

            dt = max(0.0, min(60.0, t_now - t_pt))
            norm_x = 1.0 - (dt / 60.0)
            x = left_m + norm_x * gw

            norm_t = max(0.0, min(1.0, (temp_val - 30.0) / 60.0))
            y_temp = top_m + gh - (norm_t * gh)

            norm_f = max(0.0, min(1.0, lvl_val / 15.0))
            y_fan = top_m + gh - (norm_f * gh)

            coords_temp.append(QPointF(x, y_temp))
            coords_fan.append(QPointF(x, y_fan))

        # Temperature Spline with Area Gradient
        temp_path = QPainterPath()
        temp_path.moveTo(coords_temp[0])

        for k in range(len(coords_temp) - 1):
            p0 = coords_temp[max(0, k - 1)]
            p1 = coords_temp[k]
            p2 = coords_temp[k + 1]
            p3 = coords_temp[min(len(coords_temp) - 1, k + 2)]

            dx = (p2.x() - p1.x()) / 3.0
            c1 = QPointF(p1.x() + dx, p1.y() + (p2.y() - p0.y()) / 6.0)
            c2 = QPointF(p2.x() - dx, p2.y() - (p3.y() - p1.y()) / 6.0)
            temp_path.cubicTo(c1, c2, p2)

        fill_path = QPainterPath(temp_path)
        fill_path.lineTo(coords_temp[-1].x(), top_m + gh)
        fill_path.lineTo(coords_temp[0].x(), top_m + gh)
        fill_path.closeSubpath()

        grad_temp = QLinearGradient(0, top_m, 0, top_m + gh)
        grad_temp.setColorAt(0.0, QColor(56, 189, 248, 70))
        grad_temp.setColorAt(1.0, QColor(56, 189, 248, 0))
        painter.fillPath(fill_path, QBrush(grad_temp))

        pen_temp = QPen(QColor("#38bdf8"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen_temp)
        painter.drawPath(temp_path)

        p_last_t = coords_temp[-1]
        painter.setBrush(QBrush(QColor(56, 189, 248, 90)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(p_last_t, 5.0, 5.0)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(p_last_t, 2.5, 2.5)

        # Fan Level Gradual Stepped Curve (Amber Dashed)
        fan_path = QPainterPath()
        fan_path.moveTo(coords_fan[0])
        for k in range(1, len(coords_fan)):
            p_prev = coords_fan[k - 1]
            p_cur = coords_fan[k]
            fan_path.lineTo(p_cur.x(), p_prev.y())
            fan_path.lineTo(p_cur.x(), p_cur.y())

        pen_fan = QPen(QColor("#f59e0b"), 1.8, Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen_fan)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(fan_path)

        p_last_f = coords_fan[-1]
        painter.setBrush(QBrush(QColor("#f59e0b")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(p_last_f, 3.0, 3.0)


class FanControlPanel(QFrame):
    fan_mode_selected = pyqtSignal(str)
    stop_dust_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0b111e;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        # 1. Header
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        lbl_icon = QLabel("❄️")
        lbl_icon.setStyleSheet("font-size: 16px;")
        self.lbl_title = QLabel("COOLING & THERMAL DYNAMICS (FAN CONTROL)" if get_current_language() == "en" else "KONTROL PENDINGINAN & POLISI KIPAS (FAN CONTROL)")
        self.lbl_title.setStyleSheet("color: #f8fafc; font-size: 13px; font-weight: 800; letter-spacing: 0.5px;")

        self.lbl_hw = QLabel("EMBEDDED CONTROLLER DYNAMICS")
        self.lbl_hw.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: 800; background-color: #162032; padding: 2px 8px; border-radius: 4px;")

        header_row.addWidget(lbl_icon)
        header_row.addWidget(self.lbl_title)
        header_row.addStretch()
        header_row.addWidget(self.lbl_hw)
        main_layout.addLayout(header_row)

        # 2. 3 Fan Mode Cards in a responsive Grid
        grid_cards = QGridLayout()
        grid_cards.setSpacing(10)
        grid_cards.setContentsMargins(0, 0, 0, 0)

        self.card_silent = FanModeCard(
            "silent", "🍃",
            "SILENT" if get_current_language() == "en" else "SENYAP",
            "Whisper Flow",
            "Passive & Quiet Cooling: Fans run whisper-quiet without noise." if get_current_language() == "en" else "Mendinginkan Pasif & Senyap: Kipas berputar konsisten tanpa bising.",
            "#06b6d4"
        )
        self.card_standard = FanModeCard(
            "standard", "⚖️",
            "STANDARD" if get_current_language() == "en" else "STANDAR",
            "S-Curve Dynamic",
            "Gradual Step-Free Curve: Smooth stepped transitions with thermal hysteresis." if get_current_language() == "en" else "Kenaikan Bertahap Bebas Sentakan: Transisi halus berundak dengan peredaman histeresis.",
            "#38bdf8"
        )
        self.card_extreme = FanModeCard(
            "extreme", "🚀",
            "EXTREME" if get_current_language() == "en" else "EKSTREM",
            "100% Full Turbine" if get_current_language() == "en" else "100% Turbin Penuh",
            "Max Thermal Headroom: 100% full speed (~5,200 RPM) for heavy gaming." if get_current_language() == "en" else "Headroom Termal Maksimal: 100% putaran penuh (~5,200 RPM) untuk gaming berat.",
            "#f43f5e"
        )

        self.card_silent.clicked.connect(self.fan_mode_selected.emit)
        self.card_standard.clicked.connect(self.fan_mode_selected.emit)
        self.card_extreme.clicked.connect(self.fan_mode_selected.emit)

        grid_cards.addWidget(self.card_silent, 0, 0)
        grid_cards.addWidget(self.card_standard, 0, 1)
        grid_cards.addWidget(self.card_extreme, 0, 2)
        main_layout.addLayout(grid_cards)

        # 3. Real-time Rolling Thermal Trajectory Chart
        self.trajectory_chart = ThermalTrajectoryChart(self)
        self.turbine_gauge = None
        main_layout.addWidget(self.trajectory_chart)

        # 4. Live Status & Telemetry Banner
        status_box = QFrame()
        status_box.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 10px; padding: 10px;")
        s_layout = QVBoxLayout(status_box)
        s_layout.setContentsMargins(12, 10, 12, 10)
        s_layout.setSpacing(8)

        row_telemetry = QHBoxLayout()
        row_telemetry.setSpacing(10)

        self.lbl_status = QLabel("Standard Mode: Dynamic tracking active")
        self.lbl_status.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 700;")
        row_telemetry.addWidget(self.lbl_status)
        row_telemetry.addStretch()

        self.pill_temp = QLabel("Suhu: -")
        self.pill_temp.setStyleSheet("background-color: #162032; color: #f8fafc; border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 700;")
        self.pill_power = QLabel("PL1: 45W | PL2: 65W")
        self.pill_power.setStyleSheet("background-color: #162032; color: #94a3b8; border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 600;")
        self.pill_epp = QLabel("EPP: balance_power")
        self.pill_epp.setStyleSheet("background-color: #162032; color: #10b981; border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 600;")

        row_telemetry.addWidget(self.pill_temp)
        row_telemetry.addWidget(self.pill_power)
        row_telemetry.addWidget(self.pill_epp)
        s_layout.addLayout(row_telemetry)

        main_layout.addWidget(status_box)

    def update_telemetry(self, data: dict):
        mode = data.get("active_mode", "standard")
        self.card_silent.set_active(mode == "silent")
        self.card_standard.set_active(mode == "standard")
        self.card_extreme.set_active(mode == "extreme")

        self.lbl_status.setText(data.get("status_desc", "Fan Cooling Active"))
        max_t = float(data.get("max_temp", 0.0))
        cpu_t = float(data.get("cpu_temp", 0.0))
        gpu_t = float(data.get("gpu_temp", 0.0))
        smooth_t = float(data.get("smooth_temp", max_t))
        est_rpm = int(data.get("estimated_rpm", 0))
        cur_lvl = int(data.get("current_level", 0))
        pl1 = float(data.get("pl1_w", 45.0))
        pl2 = float(data.get("pl2_w", 65.0))

        self.pill_temp.setText(f"Suhu: {smooth_t:.0f}°C (CPU: {cpu_t:.0f}°C | GPU: {gpu_t:.0f}°C)")
        if smooth_t > 70:
            self.pill_temp.setStyleSheet("background-color: #450a0a; color: #f43f5e; border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 700;")
        elif smooth_t >= 50:
            self.pill_temp.setStyleSheet("background-color: #451a03; color: #f59e0b; border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 700;")
        else:
            self.pill_temp.setStyleSheet("background-color: #162032; color: #38bdf8; border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 700;")

        self.pill_power.setText(f"PL1: {pl1}W | PL2: {pl2}W")
        self.pill_epp.setText(f"EPP: {data.get('epp', 'balance_power')}")

        if getattr(self, "turbine_gauge", None) is not None:
            self.turbine_gauge.set_telemetry(
                rpm=est_rpm,
                temp_c=smooth_t,
                subtitle=f"Level {cur_lvl}/15",
                power_w=pl1
            )

        history = data.get("history", [])
        self.trajectory_chart.set_history(history)

    def retranslate_ui(self):
        title_txt = "COOLING & THERMAL DYNAMICS (FAN CONTROL)" if get_current_language() == "en" else "KONTROL PENDINGINAN & POLISI KIPAS (FAN CONTROL)"
        self.lbl_title.setText(title_txt)
        self.card_silent.update_text(
            "SILENT" if get_current_language() == "en" else "SENYAP",
            "Whisper Flow",
            "Passive & Quiet Cooling: Fans run whisper-quiet without noise." if get_current_language() == "en" else "Mendinginkan Pasif & Senyap: Kipas berputar konsisten tanpa bising."
        )
        self.card_standard.update_text(
            "STANDARD" if get_current_language() == "en" else "STANDAR",
            "S-Curve Dynamic",
            "Gradual Step-Free Curve: Smooth stepped transitions with thermal hysteresis." if get_current_language() == "en" else "Kenaikan Bertahap Bebas Sentakan: Transisi halus berundak dengan peredaman histeresis."
        )
        self.card_extreme.update_text(
            "EXTREME" if get_current_language() == "en" else "EKSTREM",
            "100% Full Turbine" if get_current_language() == "en" else "100% Turbin Penuh",
            "Max Thermal Headroom: 100% full speed (~5,200 RPM) for heavy gaming." if get_current_language() == "en" else "Headroom Termal Maksimal: 100% putaran penuh (~5,200 RPM) untuk gaming berat."
        )
        self.trajectory_chart.update()


class SquareWaveProgress(QWidget):
    """
    Square-Wave Progress Visualizer for 5-Round Acoustic Shockwave Maintenance.
    Renders 5 pulsation blocks representing cyclical 100% Blast and Level 1 Rest cycles.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(84)
        self.setMinimumWidth(320)
        self._active = False
        self._cycle = 0
        self._phase = "idle"
        self._completed = False

    def set_state(self, active: bool, cycle: int, phase: str, completed: bool = False):
        self._active = active
        self._cycle = max(0, min(5, cycle))
        self._phase = phase.lower()
        self._completed = completed
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        total_blocks = 5
        spacing = 8
        margin_x = 4
        margin_y = 6
        avail_w = w - (2 * margin_x) - (spacing * (total_blocks - 1))
        block_w = max(20.0, avail_w / total_blocks)
        block_h = h - (2 * margin_y)

        font_header = QFont("-apple-system, Segoe UI, sans-serif", 9, QFont.Weight.Bold)
        font_sub = QFont("-apple-system, Segoe UI, sans-serif", 8, QFont.Weight.DemiBold)

        for i in range(1, total_blocks + 1):
            bx = margin_x + (i - 1) * (block_w + spacing)
            by = margin_y
            block_rect = QRectF(bx, by, block_w, block_h)

            if self._completed:
                bg_color = QColor("#082f49")
                border_color = QColor("#0284c7")
                wave_active_color = QColor("#38bdf8")
                hdr_color = QColor("#38bdf8")
                sub_color = QColor("#7dd3fc")
                sub_text = "SELESAI"
                is_current = False
                is_blast = False
                is_past = True
            elif self._active:
                if i < self._cycle:
                    bg_color = QColor("#0b192c")
                    border_color = QColor("#0369a1")
                    wave_active_color = QColor("#38bdf8")
                    hdr_color = QColor("#38bdf8")
                    sub_color = QColor("#0284c7")
                    sub_text = "TERISI"
                    is_current = False
                    is_blast = False
                    is_past = True
                elif i == self._cycle:
                    is_current = True
                    is_past = False
                    is_blast = ("100" in self._phase or "tiup" in self._phase or "blast" in self._phase)
                    if is_blast:
                        bg_color = QColor("#082845")
                        border_color = QColor("#00e5ff")
                        wave_active_color = QColor("#00f0ff")
                        hdr_color = QColor("#ffffff")
                        sub_color = QColor("#00e5ff")
                        sub_text = "BLAST 100%"
                    else:
                        bg_color = QColor("#141c2b")
                        border_color = QColor("#475569")
                        wave_active_color = QColor("#64748b")
                        hdr_color = QColor("#cbd5e1")
                        sub_color = QColor("#94a3b8")
                        sub_text = "REST (LVL 1)"
                else:
                    bg_color = QColor("#090e17")
                    border_color = QColor("#1a2333")
                    wave_active_color = QColor("#1e293b")
                    hdr_color = QColor("#475569")
                    sub_color = QColor("#334155")
                    sub_text = "STANDBY"
                    is_current = False
                    is_blast = False
                    is_past = False
            else:
                bg_color = QColor("#090e17")
                border_color = QColor("#1a2333")
                wave_active_color = QColor("#1e293b")
                hdr_color = QColor("#64748b")
                sub_color = QColor("#334155")
                sub_text = "IDLE"
                is_current = False
                is_blast = False
                is_past = False

            painter.setBrush(QBrush(bg_color))
            pen_border = QPen(border_color, 2.0 if (is_current and is_blast) else 1.0)
            painter.setPen(pen_border)
            painter.drawRoundedRect(block_rect, 8.0, 8.0)

            painter.setFont(font_header)
            painter.setPen(hdr_color)
            painter.drawText(QRectF(bx, by + 6, block_w, 16), Qt.AlignmentFlag.AlignCenter, f"RONDE {i}")

            wave_top = by + 26
            wave_bot = by + block_h - 22
            wave_mid_x = bx + 8 + (block_w - 16) * 0.58
            p_start = QPointF(bx + 8, wave_bot)
            p_crest_l = QPointF(bx + 8, wave_top)
            p_crest_r = QPointF(wave_mid_x, wave_top)
            p_trough_l = QPointF(wave_mid_x, wave_bot)
            p_end = QPointF(bx + block_w - 8, wave_bot)

            if is_past or (is_current and is_blast):
                pulse_path = QPainterPath()
                pulse_path.moveTo(p_start)
                pulse_path.lineTo(p_crest_l)
                pulse_path.lineTo(p_crest_r)
                pulse_path.lineTo(p_trough_l)
                pulse_path.closeSubpath()
                fill_color = QColor(wave_active_color)
                fill_color.setAlpha(60 if (is_current and is_blast) else 40)
                painter.fillPath(pulse_path, QBrush(fill_color))

            wave_pen = QPen(wave_active_color, 2.0)
            wave_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            wave_pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(wave_pen)

            wave_path = QPainterPath()
            wave_path.moveTo(p_start)
            wave_path.lineTo(p_crest_l)
            wave_path.lineTo(p_crest_r)
            wave_path.lineTo(p_trough_l)
            wave_path.lineTo(p_end)
            painter.drawPath(wave_path)

            painter.setFont(font_sub)
            painter.setPen(sub_color)
            painter.drawText(QRectF(bx, by + block_h - 18, block_w, 14), Qt.AlignmentFlag.AlignCenter, sub_text)


class MaintenancePurgeCockpit(QFrame):
    start_purge_requested = pyqtSignal()
    cancel_purge_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("maintenancePurgeCockpit")
        self.setStyleSheet("""
            QFrame#maintenancePurgeCockpit {
                background-color: #0b111e;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)

        self._is_active = False
        self._was_active = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        lbl_icon = QLabel("🌪️")
        lbl_icon.setStyleSheet("font-size: 16px;")

        self.lbl_title = QLabel(tr("purge_title"))
        self.lbl_title.setStyleSheet("color: #f8fafc; font-size: 13px; font-weight: 800; letter-spacing: 0.5px;")

        self.badge = QLabel(tr("purge_badge"))
        self.badge.setStyleSheet("""
            background-color: #0c2136;
            color: #38bdf8;
            border: 1px solid #0284c7;
            border-radius: 4px;
            padding: 3px 10px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.8px;
        """)

        header_row.addWidget(lbl_icon)
        header_row.addWidget(self.lbl_title)
        header_row.addStretch()
        header_row.addWidget(self.badge)
        layout.addLayout(header_row)

        self.desc_lbl = QLabel(tr("purge_desc"))
        self.desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)

        self.wave_progress = SquareWaveProgress(self)
        layout.addWidget(self.wave_progress)

        status_box = QFrame()
        status_box.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 10px; padding: 10px;")
        s_layout = QVBoxLayout(status_box)
        s_layout.setContentsMargins(12, 10, 12, 10)
        s_layout.setSpacing(8)

        status_row = QHBoxLayout()
        self.lbl_status = QLabel(tr("purge_idle"))
        self.lbl_status.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 700; letter-spacing: 0.3px;")

        self.lbl_countdown = QLabel("30s remaining" if get_current_language() == "en" else "30s tersisa")
        self.lbl_countdown.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")

        status_row.addWidget(self.lbl_status)
        status_row.addStretch()
        status_row.addWidget(self.lbl_countdown)
        s_layout.addLayout(status_row)

        self.countdown_bar = QProgressBar()
        self.countdown_bar.setObjectName("purgeCountdownBar")
        self.countdown_bar.setRange(0, 100)
        self.countdown_bar.setValue(0)
        self.countdown_bar.setFixedHeight(8)
        self.countdown_bar.setTextVisible(False)
        self.countdown_bar.setStyleSheet("""
            QProgressBar#purgeCountdownBar {
                background-color: #162032;
                border: none;
                border-radius: 4px;
            }
            QProgressBar#purgeCountdownBar::chunk {
                background-color: #38bdf8;
                border-radius: 4px;
            }
        """)
        s_layout.addWidget(self.countdown_bar)
        layout.addWidget(status_box)

        self.btn_action = QPushButton(tr("purge_start_btn"))
        self.btn_action.setObjectName("purgeActionBtn")
        self.btn_action.setFixedHeight(42)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self._on_action_clicked)
        self._apply_button_style(active=False)
        layout.addWidget(self.btn_action)

    def _apply_button_style(self, active: bool):
        if active:
            self.btn_action.setStyleSheet("""
                QPushButton#purgeActionBtn {
                    background-color: #7f1d1d;
                    color: #fecaca;
                    border: 1px solid #ef4444;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                }
                QPushButton#purgeActionBtn:hover {
                    background-color: #991b1b;
                    border-color: #f87171;
                }
                QPushButton#purgeActionBtn:pressed {
                    background-color: #450a0a;
                }
            """)
        else:
            self.btn_action.setStyleSheet("""
                QPushButton#purgeActionBtn {
                    background-color: #0284c7;
                    color: #ffffff;
                    border: 1px solid #38bdf8;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                }
                QPushButton#purgeActionBtn:hover {
                    background-color: #0369a1;
                    border-color: #7dd3fc;
                }
                QPushButton#purgeActionBtn:pressed {
                    background-color: #0c4a6e;
                }
            """)

    def _on_action_clicked(self):
        if self._is_active:
            self.cancel_purge_requested.emit()
        else:
            self.start_purge_requested.emit()

    def retranslate_ui(self):
        self.lbl_title.setText(tr("purge_title"))
        self.badge.setText(tr("purge_badge"))
        self.desc_lbl.setText(tr("purge_desc"))
        if self._is_active:
            self.btn_action.setText(tr("purge_cancel_btn"))
        else:
            self.btn_action.setText(tr("purge_start_btn"))

    def update_purge_telemetry(self, purge_data: dict):
        is_active = purge_data.get("dust_active", purge_data.get("active", False))
        rem = float(purge_data.get("dust_remaining_s", purge_data.get("remaining_s", 0.0)))
        pct = int(purge_data.get("dust_pct", purge_data.get("pct", 0)))
        cycle = int(purge_data.get("dust_cycle", purge_data.get("cycle", 0)))
        phase = str(purge_data.get("dust_phase", purge_data.get("phase", "idle")))

        if is_active:
            self._is_active = True
            self._was_active = True
            self.btn_action.setText(tr("purge_cancel_btn"))
            self._apply_button_style(active=True)

            status_text = f"Status: ROUND {cycle}/5 - {phase.upper()}" if get_current_language() == "en" else f"Status: RONDE {cycle}/5 - {phase.upper()}"
            self.lbl_status.setText(status_text)
            self.lbl_countdown.setText(f"{int(rem)}s remaining" if get_current_language() == "en" else f"{int(rem)}s tersisa")
            self.countdown_bar.setValue(pct)
            self.wave_progress.set_state(active=True, cycle=cycle, phase=phase, completed=False)
        else:
            self._is_active = False
            self.btn_action.setText(tr("purge_start_btn"))
            self._apply_button_style(active=False)

            if getattr(self, "_was_active", False) and rem <= 0.5:
                self.lbl_status.setText("Status: COMPLETED" if get_current_language() == "en" else "Status: SELESAI")
                self.lbl_countdown.setText("Done" if get_current_language() == "en" else "Selesai")
                self.countdown_bar.setValue(100)
                self.wave_progress.set_state(active=False, cycle=5, phase="done", completed=True)
            else:
                self.lbl_status.setText(tr("purge_idle"))
                self.lbl_countdown.setText("30s remaining" if get_current_language() == "en" else "30s tersisa")
                self.countdown_bar.setValue(0)
                self.wave_progress.set_state(active=False, cycle=0, phase="idle", completed=False)


class EsportsDisplaySuiteCard(QFrame):
    refresh_rate_changed = pyqtSignal(int)
    overdrive_changed = pyqtSignal(int)
    smart_ac_dc_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("esportsDisplaySuiteCard")
        self.setStyleSheet("""
            QFrame#esportsDisplaySuiteCard {
                background-color: #0b111e;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)

        self._current_hz = 165
        self._current_od = 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        lbl_icon = QLabel("🖥️")
        lbl_icon.setStyleSheet("font-size: 16px;")

        self.lbl_title = QLabel(tr("display_suite_title"))
        self.lbl_title.setStyleSheet("color: #f8fafc; font-size: 13px; font-weight: 800; letter-spacing: 0.5px;")

        badge = QLabel('15.6" IPS 1920x1080')
        badge.setStyleSheet("""
            background-color: #162032;
            color: #38bdf8;
            border: 1px solid #1e293b;
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 700;
        """)

        header_row.addWidget(lbl_icon)
        header_row.addWidget(self.lbl_title)
        header_row.addStretch()
        header_row.addWidget(badge)
        layout.addLayout(header_row)

        hz_section = QVBoxLayout()
        hz_section.setSpacing(6)

        self.lbl_hz_sec = QLabel(tr("refresh_rate_title"))
        self.lbl_hz_sec.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;")
        hz_section.addWidget(self.lbl_hz_sec)

        hz_frame = QFrame()
        hz_frame.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 3px;")
        hz_layout = QHBoxLayout(hz_frame)
        hz_layout.setContentsMargins(4, 4, 4, 4)
        hz_layout.setSpacing(6)

        self.btn_hz_60 = QPushButton(tr("btn_60hz"))
        self.btn_hz_60.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hz_60.setFixedHeight(36)

        self.btn_hz_90 = QPushButton(tr("btn_90hz"))
        self.btn_hz_90.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hz_90.setFixedHeight(36)

        self.btn_hz_120 = QPushButton(tr("btn_120hz"))
        self.btn_hz_120.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hz_120.setFixedHeight(36)

        self.btn_hz_165 = QPushButton(tr("btn_165hz"))
        self.btn_hz_165.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hz_165.setFixedHeight(36)

        self.btn_hz_60.clicked.connect(lambda: self._on_hz_clicked(60))
        self.btn_hz_90.clicked.connect(lambda: self._on_hz_clicked(90))
        self.btn_hz_120.clicked.connect(lambda: self._on_hz_clicked(120))
        self.btn_hz_165.clicked.connect(lambda: self._on_hz_clicked(165))

        hz_layout.addWidget(self.btn_hz_60)
        hz_layout.addWidget(self.btn_hz_90)
        hz_layout.addWidget(self.btn_hz_120)
        hz_layout.addWidget(self.btn_hz_165)
        hz_section.addWidget(hz_frame)
        layout.addLayout(hz_section)

        od_section = QVBoxLayout()
        od_section.setSpacing(6)

        self.lbl_od_sec = QLabel(tr("overdrive_title"))
        self.lbl_od_sec.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;")
        od_section.addWidget(self.lbl_od_sec)

        od_frame = QFrame()
        od_frame.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 3px;")
        od_layout = QHBoxLayout(od_frame)
        od_layout.setContentsMargins(4, 4, 4, 4)
        od_layout.setSpacing(6)

        self.btn_od_off = QPushButton(tr("od_off"))
        self.btn_od_off.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_od_off.setFixedHeight(34)

        self.btn_od_normal = QPushButton(tr("od_normal"))
        self.btn_od_normal.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_od_normal.setFixedHeight(34)

        self.btn_od_extreme = QPushButton(tr("od_extreme"))
        self.btn_od_extreme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_od_extreme.setFixedHeight(34)

        self.btn_od_off.clicked.connect(lambda: self._on_od_clicked(0))
        self.btn_od_normal.clicked.connect(lambda: self._on_od_clicked(1))
        self.btn_od_extreme.clicked.connect(lambda: self._on_od_clicked(2))

        od_layout.addWidget(self.btn_od_off)
        od_layout.addWidget(self.btn_od_normal)
        od_layout.addWidget(self.btn_od_extreme)
        od_section.addWidget(od_frame)
        layout.addLayout(od_section)

        ac_frame = QFrame()
        ac_frame.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 10px 14px;")
        ac_layout = QHBoxLayout(ac_frame)
        ac_layout.setContentsMargins(10, 6, 10, 6)
        ac_layout.setSpacing(12)

        lbl_smart_icon = QLabel("🔌")
        lbl_smart_icon.setStyleSheet("font-size: 16px;")

        smart_text_box = QVBoxLayout()
        smart_text_box.setSpacing(2)
        self.lbl_smart_title = QLabel(tr("smart_ac_dc_title"))
        self.lbl_smart_title.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: 700;")
        self.lbl_smart_desc = QLabel(tr("smart_ac_dc_desc"))
        self.lbl_smart_desc.setStyleSheet("color: #64748b; font-size: 11px;")
        smart_text_box.addWidget(self.lbl_smart_title)
        smart_text_box.addWidget(self.lbl_smart_desc)

        self.toggle_smart = ModernToggle(checked=True, parent=self)
        self.toggle_smart.toggled.connect(self.smart_ac_dc_toggled.emit)

        ac_layout.addWidget(lbl_smart_icon)
        ac_layout.addLayout(smart_text_box, stretch=1)
        ac_layout.addWidget(self.toggle_smart)
        layout.addWidget(ac_frame)

        self._update_hz_style(165)
        self._update_od_style(1)

    def _update_hz_style(self, hz: int):
        # Determine active bracket
        if hz >= 150:
            target = 165
        elif hz >= 110:
            target = 120
        elif hz >= 80:
            target = 90
        else:
            target = 60
        self._current_hz = target

        inactive_style = """
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid transparent;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #121c2e;
                color: #f8fafc;
            }
        """

        self.btn_hz_60.setStyleSheet("""
            QPushButton {
                background-color: #065f46;
                color: #ecfdf5;
                border: 1px solid #10b981;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 800;
            }
        """ if target == 60 else inactive_style)

        self.btn_hz_90.setStyleSheet("""
            QPushButton {
                background-color: #0f766e;
                color: #f0fdfa;
                border: 1px solid #14b8a6;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 800;
            }
        """ if target == 90 else inactive_style)

        self.btn_hz_120.setStyleSheet("""
            QPushButton {
                background-color: #1d4ed8;
                color: #eff6ff;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 800;
            }
        """ if target == 120 else inactive_style)

        self.btn_hz_165.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                border: 1px solid #38bdf8;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 800;
            }
        """ if target == 165 else inactive_style)

    def _update_od_style(self, level: int):
        self._current_od = level
        styles = {
            "inactive": """
                QPushButton {
                    background-color: transparent;
                    color: #94a3b8;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #121c2e;
                    color: #f8fafc;
                }
            """,
            "off_active": """
                QPushButton {
                    background-color: #334155;
                    color: #f8fafc;
                    border: 1px solid #64748b;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 800;
                }
            """,
            "normal_active": """
                QPushButton {
                    background-color: #0284c7;
                    color: #ffffff;
                    border: 1px solid #38bdf8;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 800;
                }
            """,
            "extreme_active": """
                QPushButton {
                    background-color: #991b1b;
                    color: #fef2f2;
                    border: 1px solid #f43f5e;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 800;
                }
            """
        }

        self.btn_od_off.setStyleSheet(styles["off_active"] if level == 0 else styles["inactive"])
        self.btn_od_normal.setStyleSheet(styles["normal_active"] if level == 1 else styles["inactive"])
        self.btn_od_extreme.setStyleSheet(styles["extreme_active"] if level == 2 else styles["inactive"])

    def _on_hz_clicked(self, hz: int):
        if hz != self._current_hz:
            self._update_hz_style(hz)
            self.refresh_rate_changed.emit(hz)

    def _on_od_clicked(self, level: int):
        if level != self._current_od:
            self._update_od_style(level)
            self.overdrive_changed.emit(level)

    def set_display_state(self, current_hz: int, overdrive: int, smart_ac_dc: bool):
        self._update_hz_style(current_hz)
        self._update_od_style(max(0, min(2, overdrive)))
        self.toggle_smart.blockSignals(True)
        self.toggle_smart.setChecked(smart_ac_dc)
        self.toggle_smart.blockSignals(False)

    def retranslate_ui(self):
        self.lbl_title.setText(tr("display_suite_title"))
        self.lbl_hz_sec.setText(tr("refresh_rate_title"))
        self.btn_hz_60.setText(tr("btn_60hz"))
        self.btn_hz_90.setText(tr("btn_90hz"))
        self.btn_hz_120.setText(tr("btn_120hz"))
        self.btn_hz_165.setText(tr("btn_165hz"))
        self.lbl_od_sec.setText(tr("overdrive_title"))
        self.btn_od_off.setText(tr("od_off"))
        self.btn_od_normal.setText(tr("od_normal"))
        self.btn_od_extreme.setText(tr("od_extreme"))
        self.lbl_smart_title.setText(tr("smart_ac_dc_title"))
        self.lbl_smart_desc.setText(tr("smart_ac_dc_desc"))


class GamingCoreSchedulerCard(QFrame):
    """
    Intel Alder Lake Hybrid Architecture Optimizer Card.
    Provides P-Core affinity pinning for games, No-Turbo silent cooling toggle,
    and automatic game detection profile orchestration.
    """
    no_turbo_toggled = pyqtSignal(bool)
    auto_game_mode_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("gamingCoreSchedulerCard")
        self.setStyleSheet("""
            QFrame#gamingCoreSchedulerCard {
                background-color: #0b111e;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(16)

        # Header: Title & Architecture Badge
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        lbl_icon = QLabel("🧠")
        lbl_icon.setStyleSheet("font-size: 16px;")

        self.lbl_title = QLabel(tr("scheduler_title"))
        self.lbl_title.setStyleSheet("color: #f8fafc; font-size: 13px; font-weight: 800; letter-spacing: 0.5px;")

        badge = QLabel("12C / 16T (4P + 8E)")
        badge.setStyleSheet("""
            background-color: #162032;
            color: #38bdf8;
            border: 1px solid #1e293b;
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 700;
        """)

        header_row.addWidget(lbl_icon)
        header_row.addWidget(self.lbl_title)
        header_row.addStretch()
        header_row.addWidget(badge)
        layout.addLayout(header_row)

        # Section 1: P-Core Game Thread Pinning
        pin_section = QVBoxLayout()
        pin_section.setSpacing(6)

        self.lbl_pin_sec = QLabel(tr("pcore_pinning_title"))
        self.lbl_pin_sec.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;")
        pin_section.addWidget(self.lbl_pin_sec)

        pin_frame = QFrame()
        pin_frame.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 12px;")
        pin_layout = QVBoxLayout(pin_frame)
        pin_layout.setContentsMargins(12, 10, 12, 10)
        pin_layout.setSpacing(8)

        status_row = QHBoxLayout()
        self.lbl_pinning_status = QLabel(tr("pcore_status_idle"))
        self.lbl_pinning_status.setStyleSheet("""
            background-color: #121a29;
            color: #64748b;
            border: 1px solid #1e293b;
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.5px;
        """)

        cores_layout_info = QLabel("P-Cores: CPU 0–7 | E-Cores: CPU 8–15")
        cores_layout_info.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 600;")

        status_row.addWidget(self.lbl_pinning_status)
        status_row.addStretch()
        status_row.addWidget(cores_layout_info)
        pin_layout.addLayout(status_row)

        self.lbl_desc = QLabel(tr("pcore_pinning_desc"))
        self.lbl_desc.setStyleSheet("color: #94a3b8; font-size: 11px; line-height: 1.4;")
        self.lbl_desc.setWordWrap(True)
        pin_layout.addWidget(self.lbl_desc)

        pin_section.addWidget(pin_frame)
        layout.addLayout(pin_section)

        # Section 2: Intel No-Turbo Switch
        no_turbo_frame = QFrame()
        no_turbo_frame.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 10px 14px;")
        no_turbo_layout = QHBoxLayout(no_turbo_frame)
        no_turbo_layout.setContentsMargins(10, 8, 10, 8)
        no_turbo_layout.setSpacing(12)

        lbl_turbo_icon = QLabel("❄️")
        lbl_turbo_icon.setStyleSheet("font-size: 16px;")

        turbo_text_box = QVBoxLayout()
        turbo_text_box.setSpacing(2)
        self.lbl_turbo_title = QLabel(tr("no_turbo_title"))
        self.lbl_turbo_title.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: 700;")
        self.lbl_turbo_desc = QLabel(tr("no_turbo_desc"))
        self.lbl_turbo_desc.setStyleSheet("color: #64748b; font-size: 11px;")
        self.lbl_turbo_desc.setWordWrap(True)
        turbo_text_box.addWidget(self.lbl_turbo_title)
        turbo_text_box.addWidget(self.lbl_turbo_desc)

        self.toggle_no_turbo = ModernToggle(checked=False, parent=self)
        self.toggle_no_turbo.toggled.connect(self.no_turbo_toggled.emit)

        no_turbo_layout.addWidget(lbl_turbo_icon)
        no_turbo_layout.addLayout(turbo_text_box, stretch=1)
        no_turbo_layout.addWidget(self.toggle_no_turbo)
        layout.addWidget(no_turbo_frame)

        # Section 3: Auto-Game Mode Switch
        auto_game_frame = QFrame()
        auto_game_frame.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 10px 14px;")
        auto_game_layout = QHBoxLayout(auto_game_frame)
        auto_game_layout.setContentsMargins(10, 8, 10, 8)
        auto_game_layout.setSpacing(12)

        lbl_game_icon = QLabel("🎮")
        lbl_game_icon.setStyleSheet("font-size: 16px;")

        game_text_box = QVBoxLayout()
        game_text_box.setSpacing(2)
        self.lbl_game_title = QLabel(tr("auto_game_title"))
        self.lbl_game_title.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: 700;")
        self.lbl_game_desc = QLabel(tr("auto_game_desc"))
        self.lbl_game_desc.setStyleSheet("color: #64748b; font-size: 11px;")
        self.lbl_game_desc.setWordWrap(True)
        game_text_box.addWidget(self.lbl_game_title)
        game_text_box.addWidget(self.lbl_game_desc)

        self.toggle_auto_game = ModernToggle(checked=False, parent=self)
        self.toggle_auto_game.toggled.connect(self.auto_game_mode_toggled.emit)

        auto_game_layout.addWidget(lbl_game_icon)
        auto_game_layout.addLayout(game_text_box, stretch=1)
        auto_game_layout.addWidget(self.toggle_auto_game)
        layout.addWidget(auto_game_frame)

    def retranslate_ui(self):
        self.lbl_title.setText(tr("scheduler_title"))
        self.lbl_pin_sec.setText(tr("pcore_pinning_title"))
        self.lbl_desc.setText(tr("pcore_pinning_desc"))
        self.lbl_turbo_title.setText(tr("no_turbo_title"))
        self.lbl_turbo_desc.setText(tr("no_turbo_desc"))
        self.lbl_game_title.setText(tr("auto_game_title"))
        self.lbl_game_desc.setText(tr("auto_game_desc"))

    def set_scheduler_state(self, no_turbo: bool, auto_game: bool, active_game: str = ""):
        self.toggle_no_turbo.blockSignals(True)
        self.toggle_no_turbo.setChecked(no_turbo)
        self.toggle_no_turbo.blockSignals(False)

        self.toggle_auto_game.blockSignals(True)
        self.toggle_auto_game.setChecked(auto_game)
        self.toggle_auto_game.blockSignals(False)

        if active_game:
            self.lbl_pinning_status.setText(f"STATUS: GAMING (P-CORES PINNED • {active_game.upper()})")
            self.lbl_pinning_status.setStyleSheet("""
                background-color: #064e3b;
                color: #34d399;
                border: 1px solid #10b981;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.5px;
            """)
        else:
            self.lbl_pinning_status.setText(tr("pcore_status_idle"))
            self.lbl_pinning_status.setStyleSheet("""
                background-color: #121a29;
                color: #64748b;
                border: 1px solid #1e293b;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
            """)


