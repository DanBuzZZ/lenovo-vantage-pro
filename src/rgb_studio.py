"""
Lenovo Vantage Pro - 4-Zone RGB Lighting Studio
Hardware Controller for ITE 8295 (USB 048d:c973)
Obsidian Titanium Luxury Interface & Direct ioctl Protocol
"""

import os
import sys
import glob
import json
import fcntl
import logging
from typing import List, Tuple, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QColorDialog, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor
from i18n import tr, get_current_language

logger = logging.getLogger("lenovo_vantage.rgb_studio")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def HIDIOCSFEATURE(length: int) -> int:
    """
    Linux HIDRAW ioctl HIDIOCSFEATURE definition.
    _IOWR('H', 0x06, struct hidraw_report_descriptor)
    """
    IOC_DIR = 3
    IOC_TYPE = ord('H')
    IOC_NR = 0x06
    return (IOC_DIR << 30) | (length << 16) | (IOC_TYPE << 8) | IOC_NR


CONFIG_PATH = os.path.expanduser("~/.config/lenovo-vantage/rgb_state.json")

EFFECT_CODES: Dict[str, int] = {
    "static": 0x01,
    "breath": 0x03,
    "breathing": 0x03,
    "wave": 0x04,
    "smooth": 0x06,
    "smooth_wave": 0x06,
}

EFFECT_NAMES: Dict[int, str] = {
    0x01: "static",
    0x03: "breathing",
    0x04: "wave",
    0x06: "smooth_wave",
}

PRESETS: Dict[str, Dict[str, Any]] = {
    "vantage_cyan": {
        "name": "Vantage Cyan",
        "effect": "static",
        "speed": 1,
        "brightness": 2,
        "zone_colors": [(56, 189, 248), (56, 189, 248), (56, 189, 248), (56, 189, 248)],
    },
    "cyber_neon": {
        "name": "Cyber Neon",
        "effect": "static",
        "speed": 1,
        "brightness": 2,
        "zone_colors": [(56, 189, 248), (236, 72, 153), (245, 158, 11), (16, 185, 129)],
    },
    "crimson_fury": {
        "name": "Crimson Fury",
        "effect": "static",
        "speed": 1,
        "brightness": 2,
        "zone_colors": [(239, 68, 68), (239, 68, 68), (239, 68, 68), (239, 68, 68)],
    },
    "emerald_stealth": {
        "name": "Emerald Stealth",
        "effect": "static",
        "speed": 1,
        "brightness": 2,
        "zone_colors": [(16, 185, 129), (16, 185, 129), (16, 185, 129), (16, 185, 129)],
    },
    "smooth_wave": {
        "name": "Smooth Wave",
        "effect": "smooth_wave",
        "speed": 2,
        "brightness": 2,
        "zone_colors": [(56, 189, 248), (236, 72, 153), (245, 158, 11), (16, 185, 129)],
    },
    "breathing": {
        "name": "Breathing",
        "effect": "breathing",
        "speed": 2,
        "brightness": 2,
        "zone_colors": [(56, 189, 248), (56, 189, 248), (56, 189, 248), (56, 189, 248)],
    },
    "off": {
        "name": "Off",
        "effect": "static",
        "speed": 1,
        "brightness": 0,
        "zone_colors": [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)],
    },
}

LUXURY_PALETTE = [
    ("#38bdf8", "Cyan"),
    ("#3b82f6", "Blue"),
    ("#6366f1", "Indigo"),
    ("#a855f7", "Purple"),
    ("#ec4899", "Pink"),
    ("#ef4444", "Crimson"),
    ("#f97316", "Orange"),
    ("#f59e0b", "Amber"),
    ("#10b981", "Emerald"),
    ("#f8fafc", "White"),
]


DEFAULT_SLOTS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Vantage Cyan",
        "effect": "static",
        "speed": 1,
        "brightness": 2,
        "zone_colors": [(56, 189, 248), (56, 189, 248), (56, 189, 248), (56, 189, 248)],
    },
    {
        "id": 2,
        "name": "Cyber Neon",
        "effect": "static",
        "speed": 1,
        "brightness": 2,
        "zone_colors": [(56, 189, 248), (236, 72, 153), (245, 158, 11), (16, 185, 129)],
    },
    {
        "id": 3,
        "name": "Crimson Fury",
        "effect": "breathing",
        "speed": 2,
        "brightness": 2,
        "zone_colors": [(239, 68, 68), (239, 68, 68), (239, 68, 68), (239, 68, 68)],
    },
    {
        "id": 4,
        "name": "Spectrum Wave",
        "effect": "smooth_wave",
        "speed": 2,
        "brightness": 2,
        "zone_colors": [(56, 189, 248), (236, 72, 153), (245, 158, 11), (16, 185, 129)],
    },
    {
        "id": 5,
        "name": "Backlight Off",
        "effect": "static",
        "speed": 1,
        "brightness": 0,
        "zone_colors": [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)],
    },
]


class LenovoRgbStudio:
    """
    Hardware Controller for Lenovo 4-Zone RGB Keyboard Backlight.
    Communicates with ITE 8295 (USB 048d:c973) via 33-byte feature report ioctl.
    Features a 5-Slot Profile State Machine matching OEM Lenovo Vantage and Fn+Space cycles.
    """
    _instance: Optional["LenovoRgbStudio"] = None

    @classmethod
    def get_instance(cls) -> "LenovoRgbStudio":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, hidraw_path: Optional[str] = None):
        self.dev_path: str = hidraw_path or self.find_hidraw_device()
        self.effect: str = "static"
        self.speed: int = 1
        self.brightness: int = 2
        self.zone_colors: List[Tuple[int, int, int]] = [
            (56, 189, 248),
            (56, 189, 248),
            (56, 189, 248),
            (56, 189, 248),
        ]
        self.current_preset: Optional[str] = "vantage_cyan"

        # 5-Slot Cyclic Profiles State Machine
        self.active_slot: int = 0  # 0..4 (representing Slot 1..5)
        self.slots: List[Dict[str, Any]] = [dict(s) for s in DEFAULT_SLOTS]
        self.control_owner: str = "app"  # "app" (Vantage Pro) or "bios" (ITE chip)
        self.sync_with_performance: bool = False  # Auto-sync RGB profile with Fn+Q / CPU thermal mode

        self.ensure_rgb_owner()
        self.load_state()

    def find_hidraw_device(self, target_vid: str = "048d", target_pid: str = "c973") -> str:
        """
        Inspect /sys/class/hidraw/hidraw* to locate the ITE 8295 device.
        Fallback to /dev/hidraw0 if detection yields no matches.
        """
        sys_hidraw_dir = "/sys/class/hidraw"
        if os.path.exists(sys_hidraw_dir):
            entries = sorted(os.listdir(sys_hidraw_dir))
            for entry in entries:
                entry_path = os.path.join(sys_hidraw_dir, entry)
                uevent_path = os.path.join(entry_path, "device", "uevent")
                if os.path.isfile(uevent_path):
                    try:
                        with open(uevent_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read().upper()
                            if target_vid.upper() in content and target_pid.upper() in content:
                                dev_node = f"/dev/{entry}"
                                if os.path.exists(dev_node):
                                    logger.debug(f"Discovered RGB hidraw node: {dev_node}")
                                    return dev_node
                    except Exception as e:
                        logger.debug(f"Error checking {uevent_path}: {e}")
        return "/dev/hidraw0"

    def ensure_rgb_owner(self):
        """
        Synchronize RGB ownership with current control_owner setting.
        """
        try:
            from backend import LenovoHardware
            LenovoHardware.set_rgb_owner(self.control_owner == "app")
        except Exception:
            pass

    def set_control_owner(self, owner: str) -> bool:
        """
        Sets RGB lighting control owner: 'app' (Vantage Pro 5-Slot Engine) or 'bios' (ITE chip Standalone).
        """
        owner_clean = "app" if str(owner).lower().strip() == "app" else "bios"
        self.control_owner = owner_clean
        self.ensure_rgb_owner()
        self.save_state()
        return True

    def set_sync_with_performance(self, enabled: bool) -> bool:
        """
        Enables or disables automatic synchronization of RGB profile with CPU/fan performance modes.
        """
        self.sync_with_performance = bool(enabled)
        self.save_state()
        return self.sync_with_performance

    def cycle_profile(self) -> Tuple[int, str, Dict[str, Any]]:
        """
        Advances to next saved profile slot (Slot 1 -> Slot 2 -> Slot 3 -> Slot 4 -> Slot 5 [Off] -> Slot 1),
        applies the hardware payload to ITE 8295, saves state, and returns:
        (slot_number_1_based, slot_name, slot_dict)
        """
        self.active_slot = (self.active_slot + 1) % len(self.slots)
        self.apply_slot(self.active_slot)
        slot = self.slots[self.active_slot]
        return (self.active_slot + 1, slot["name"], slot)

    def cycle_brightness(self) -> int:
        """
        Cycles keyboard backlight through the 3 native hardware brightness levels:
        High 100% (2) -> Low 50% (1) -> Off 0% (0) -> High 100% (2)...
        Or if currently 0: 0 -> 1 -> 2.
        Updates active profile slot, applies to ITE 8295, and persists state.
        """
        next_b = {0: 1, 1: 2, 2: 0}.get(self.brightness, 2)
        self.apply_state(
            effect=self.effect,
            speed=self.speed,
            brightness=next_b,
            zone_colors=self.zone_colors
        )
        if 0 <= self.active_slot < len(self.slots):
            self.slots[self.active_slot]["brightness"] = next_b
        self.save_state()
        return next_b

    def apply_slot(self, slot_idx: int) -> bool:
        """
        Applies a saved profile slot by 0-based index (0..4).
        """
        if not (0 <= slot_idx < len(self.slots)):
            return False
        self.active_slot = slot_idx
        slot = self.slots[slot_idx]
        success = self.apply_state(
            effect=slot["effect"],
            speed=slot["speed"],
            brightness=slot["brightness"],
            zone_colors=slot["zone_colors"]
        )
        self.current_preset = None
        self.save_state()
        return success

    def save_current_to_slot(self, slot_idx: int) -> bool:
        """
        Saves current lighting parameters (effect, speed, brightness, zone colors)
        to the specified profile slot (0..4).
        """
        if not (0 <= slot_idx < len(self.slots)):
            return False
        self.slots[slot_idx]["effect"] = self.effect
        self.slots[slot_idx]["speed"] = self.speed
        self.slots[slot_idx]["brightness"] = self.brightness
        self.slots[slot_idx]["zone_colors"] = [list(c) for c in self.zone_colors]
        return self.save_state()

    def send_feature_report(self, payload: bytearray) -> bool:
        """
        Sends 33-byte feature report using ioctl HIDIOCSFEATURE(33).
        """
        if len(payload) != 33:
            logger.error(f"Payload length must be 33 bytes, got {len(payload)}")
            return False

        cmd = HIDIOCSFEATURE(33)
        for attempt in range(2):
            try:
                with open(self.dev_path, "rb+") as fd:
                    res = fcntl.ioctl(fd, cmd, payload)
                    if res == 33 or res >= 0:
                        return True
            except (PermissionError, FileNotFoundError, OSError) as e:
                logger.warning(f"Error sending feature report to {self.dev_path} (attempt {attempt+1}): {e}")
                if attempt == 0:
                    self.dev_path = self.find_hidraw_device()
        return False

    def apply_state(self, effect: str, speed: int, brightness: int, zone_colors: list) -> bool:
        """
        Constructs 33-byte payload and applies RGB state to the hardware controller.
        - payload[0] = 0xcc (Report ID)
        - payload[1] = 0x16 (Lighting cmd)
        - payload[2] = Effect code: 0x01 (Static), 0x03 (Breath), 0x06 (Smooth), 0x04 (Wave)
        - payload[3] = Speed (1..4)
        - payload[4] = Brightness (0..2)
        - payload[5..17] = 12 bytes = [R0, G0, B0, R1, G1, B1, R2, G2, B2, R3, G3, B3]
        - payload[17..33] = 0x00 padding
        """
        effect_str = str(effect).lower().strip()
        effect_code = EFFECT_CODES.get(effect_str, 0x01)
        clamped_speed = max(1, min(4, int(speed)))
        clamped_brightness = max(0, min(2, int(brightness)))

        normalized_colors: List[Tuple[int, int, int]] = []
        for i in range(4):
            if i < len(zone_colors):
                c = zone_colors[i]
                if isinstance(c, (list, tuple)) and len(c) >= 3:
                    r, g, b = max(0, min(255, int(c[0]))), max(0, min(255, int(c[1]))), max(0, min(255, int(c[2])))
                elif isinstance(c, str) and c.startswith("#"):
                    qc = QColor(c)
                    r, g, b = qc.red(), qc.green(), qc.blue()
                else:
                    r, g, b = 56, 189, 248
            else:
                r, g, b = 56, 189, 248
            normalized_colors.append((r, g, b))

        payload = bytearray(33)
        payload[0] = 0xcc
        payload[1] = 0x16
        payload[2] = effect_code
        payload[3] = clamped_speed
        payload[4] = clamped_brightness

        for i, (r, g, b) in enumerate(normalized_colors):
            payload[5 + i * 3] = r
            payload[5 + i * 3 + 1] = g
            payload[5 + i * 3 + 2] = b

        success = self.send_feature_report(payload)

        self.effect = effect_str
        self.speed = clamped_speed
        self.brightness = clamped_brightness
        self.zone_colors = normalized_colors
        self.save_state()

        return success

    def apply_preset(self, preset_name: str) -> bool:
        """
        Applies a named preset profile.
        Available: 'vantage_cyan', 'cyber_neon', 'crimson_fury', 'emerald_stealth',
                   'smooth_wave', 'breathing', 'off'
        """
        name = str(preset_name).lower().strip()
        if name not in PRESETS:
            logger.warning(f"Unknown preset: {preset_name}")
            return False

        p = PRESETS[name]
        self.current_preset = name
        return self.apply_state(
            effect=p["effect"],
            speed=p["speed"],
            brightness=p["brightness"],
            zone_colors=p["zone_colors"]
        )

    def save_state(self) -> bool:
        """
        Persists current RGB configuration and 5-slot data to ~/.config/lenovo-vantage/rgb_state.json.
        """
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            data = {
                "active_slot": self.active_slot,
                "control_owner": self.control_owner,
                "sync_with_performance": self.sync_with_performance,
                "slots": [
                    {
                        "id": s.get("id", i + 1),
                        "name": s.get("name", f"Slot {i+1}"),
                        "effect": s.get("effect", "static"),
                        "speed": s.get("speed", 1),
                        "brightness": s.get("brightness", 2),
                        "zone_colors": [list(c) for c in s.get("zone_colors", [])],
                    }
                    for i, s in enumerate(self.slots)
                ],
                "effect": self.effect,
                "speed": self.speed,
                "brightness": self.brightness,
                "zone_colors": [list(c) for c in self.zone_colors],
                "preset": self.current_preset,
            }
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save RGB state: {e}")
            return False

    def load_state(self) -> bool:
        """
        Loads saved RGB configuration and 5 profile slots from ~/.config/lenovo-vantage/rgb_state.json.
        """
        if not os.path.isfile(CONFIG_PATH):
            return False

        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.active_slot = max(0, min(len(DEFAULT_SLOTS) - 1, int(data.get("active_slot", 0))))
            self.control_owner = str(data.get("control_owner", "app")).lower()
            self.sync_with_performance = bool(data.get("sync_with_performance", False))

            loaded_slots = data.get("slots")
            if isinstance(loaded_slots, list) and len(loaded_slots) == 5:
                self.slots = []
                for i, s in enumerate(loaded_slots):
                    parsed_colors = [
                        (max(0, min(255, int(c[0]))), max(0, min(255, int(c[1]))), max(0, min(255, int(c[2]))))
                        for c in s.get("zone_colors", [])
                    ]
                    if len(parsed_colors) != 4:
                        parsed_colors = DEFAULT_SLOTS[i]["zone_colors"]
                    self.slots.append({
                        "id": i + 1,
                        "name": s.get("name", DEFAULT_SLOTS[i]["name"]),
                        "effect": s.get("effect", DEFAULT_SLOTS[i]["effect"]),
                        "speed": max(1, min(4, int(s.get("speed", 1)))),
                        "brightness": max(0, min(2, int(s.get("brightness", 2)))),
                        "zone_colors": parsed_colors,
                    })

            self.effect = data.get("effect", self.effect)
            self.speed = max(1, min(4, int(data.get("speed", self.speed))))
            self.brightness = max(0, min(2, int(data.get("brightness", self.brightness))))

            loaded_colors = data.get("zone_colors")
            if isinstance(loaded_colors, list) and len(loaded_colors) == 4:
                self.zone_colors = [
                    (max(0, min(255, int(c[0]))), max(0, min(255, int(c[1]))), max(0, min(255, int(c[2]))))
                    for c in loaded_colors
                ]
            self.current_preset = data.get("preset", self.current_preset)
            return True
        except Exception as e:
            logger.error(f"Failed to load RGB state: {e}")
            return False


class KeyboardZoneBlock(QFrame):
    """
    Individual Visual Keyboard Zone Block (Zone 1..4).
    Displays zone name, key group label, active color swatch with hex code,
    and handles selection / color picking.
    """
    clicked = pyqtSignal(int)
    color_change_requested = pyqtSignal(int)

    def __init__(self, zone_idx: int, zone_name: str, key_label: str, initial_color: Tuple[int, int, int], parent=None):
        super().__init__(parent)
        self.zone_idx = zone_idx
        self.zone_name = zone_name
        self.key_label = key_label
        self.current_color = initial_color
        self.is_selected = False

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(138)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # Header: Zone Index & Status Indicator
        top_row = QHBoxLayout()
        self.lbl_zone = QLabel(self.zone_name)
        self.lbl_zone.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 800; letter-spacing: 0.8px;")

        self.lbl_select_indicator = QLabel("SELECTED" if zone_idx == 0 else "")
        self.lbl_select_indicator.setStyleSheet("color: #38bdf8; font-size: 9px; font-weight: 800; letter-spacing: 0.5px;")

        top_row.addWidget(self.lbl_zone)
        top_row.addStretch()
        top_row.addWidget(self.lbl_select_indicator)
        layout.addLayout(top_row)

        # Key range label (e.g., WASD / Kiri)
        self.lbl_keys = QLabel(self.key_label)
        self.lbl_keys.setStyleSheet("color: #cbd5e1; font-size: 12px; font-weight: 700;")
        layout.addWidget(self.lbl_keys)

        # Color Pill Swatch Frame
        self.swatch = QFrame()
        self.swatch.setFixedHeight(32)
        self.swatch.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        swatch_layout = QHBoxLayout(self.swatch)
        swatch_layout.setContentsMargins(8, 0, 8, 0)

        self.lbl_hex = QLabel("#38BDF8")
        self.lbl_hex.setStyleSheet("font-size: 11px; font-weight: 800; font-family: monospace;")
        swatch_layout.addWidget(self.lbl_hex, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.swatch)

        self.btn_pick = QPushButton(tr("rgb_pick_color"))
        self.btn_pick.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pick.setFixedHeight(26)
        self.btn_pick.setStyleSheet("""
            QPushButton {
                background-color: #162032;
                color: #94a3b8;
                border: 1px solid #233148;
                border-radius: 5px;
                font-size: 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #38bdf8;
                border-color: #38bdf8;
            }
        """)
        self.btn_pick.clicked.connect(lambda: self.color_change_requested.emit(self.zone_idx))
        layout.addWidget(self.btn_pick)

        self.update_color(self.current_color)
        self.set_selected(zone_idx == 0)

    def retranslate_ui(self, zone_name: str, key_label: str):
        self.zone_name = zone_name
        self.key_label = key_label
        self.lbl_zone.setText(self.zone_name)
        self.lbl_keys.setText(self.key_label)
        self.lbl_select_indicator.setText(tr("rgb_selected") if self.is_selected else "")
        self.btn_pick.setText(tr("rgb_pick_color"))

    def mousePressEvent(self, event):
        self.clicked.emit(self.zone_idx)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.lbl_select_indicator.setText(tr("rgb_selected") if selected else "")
        self._update_frame_style()

    def update_color(self, rgb: Tuple[int, int, int]):
        self.current_color = rgb
        r, g, b = rgb
        hex_str = f"#{r:02X}{g:02X}{b:02X}"
        self.lbl_hex.setText(hex_str)

        # WCAG AAA luminance check for swatch label contrast
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        text_color = "#080c14" if luminance > 0.5 else "#ffffff"
        self.lbl_hex.setStyleSheet(f"color: {text_color}; font-size: 11px; font-weight: 800; font-family: monospace;")

        self.swatch.setStyleSheet(f"""
            QFrame {{
                background-color: {hex_str};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
            }}
        """)
        self._update_frame_style()

    def _update_frame_style(self):
        r, g, b = self.current_color
        hex_str = f"#{r:02X}{g:02X}{b:02X}"
        if self.is_selected:
            border_style = "border: 1.5px solid #38bdf8;"
            bg_style = "background-color: #131d2e;"
        else:
            border_style = f"border: 1px solid #1e293b; border-bottom: 3px solid {hex_str};"
            bg_style = "background-color: #0b111e;"

        self.setStyleSheet(f"""
            QFrame {{
                {bg_style}
                {border_style}
                border-radius: 10px;
            }}
        """)


class RgbLightingStudioCard(QFrame):
    """
    Obsidian Titanium Luxury 4-Zone RGB Lighting Studio Card.
    Hardware controller for ITE 8295 (USB 048d:c973).
    Features 5-Slot Cyclic Profiles (Fn + Space) and Hardware Ownership Control.
    """
    preset_selected = pyqtSignal(str)
    slot_changed = pyqtSignal(int, str)
    brightness_cycled = pyqtSignal(int)
    sync_perf_toggled = pyqtSignal(bool)
    state_changed = pyqtSignal()

    def __init__(self, studio: Optional[LenovoRgbStudio] = None, parent=None):
        super().__init__(parent)
        self.studio = studio or LenovoRgbStudio.get_instance()
        self.selected_zone = 0
        self.apply_to_all_zones = False

        self.setObjectName("rgbLightingStudioCard")
        self.setStyleSheet("""
            QFrame#rgbLightingStudioCard {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(16)

        # 1. Header: Title, Icon, Ownership Toggle & Architecture Badge
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        lbl_icon = QLabel("⌨️")
        lbl_icon.setStyleSheet("font-size: 16px;")

        self.lbl_title = QLabel(tr("rgb_title"))
        self.lbl_title.setStyleSheet("color: #f8fafc; font-size: 13px; font-weight: 800; letter-spacing: 0.5px;")

        # Ownership Switcher: App vs BIOS
        self.owner_box = QFrame()
        self.owner_box.setStyleSheet("background-color: #080d16; border: 1px solid #1e293b; border-radius: 6px;")
        owner_layout = QHBoxLayout(self.owner_box)
        owner_layout.setContentsMargins(2, 2, 2, 2)
        owner_layout.setSpacing(2)

        self.btn_owner_app = QPushButton(tr("rgb_owner_app"))
        self.btn_owner_app.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_owner_app.setFixedHeight(22)
        self.btn_owner_app.clicked.connect(lambda: self._set_control_owner("app"))

        self.btn_owner_bios = QPushButton(tr("rgb_owner_bios"))
        self.btn_owner_bios.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_owner_bios.setFixedHeight(22)
        self.btn_owner_bios.clicked.connect(lambda: self._set_control_owner("bios"))

        owner_layout.addWidget(self.btn_owner_app)
        owner_layout.addWidget(self.btn_owner_bios)

        self.badge = QLabel(tr("rgb_controller_badge"))
        self.badge.setStyleSheet("""
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
        header_row.addWidget(self.owner_box)
        header_row.addWidget(self.badge)
        layout.addLayout(header_row)

        # 1.5 5-Slot Cyclic Profiles Section (Fn + Space)
        slots_section = QVBoxLayout()
        slots_section.setSpacing(6)

        slots_header = QHBoxLayout()
        self.lbl_slots_title = QLabel(tr("rgb_slots_header"))
        self.lbl_slots_title.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;")
        slots_header.addWidget(self.lbl_slots_title)
        slots_header.addStretch()

        self.lbl_active_slot_badge = QLabel("ACTIVE: SLOT 1 / 5")
        self.lbl_active_slot_badge.setStyleSheet("""
            background-color: #0c4a6e;
            color: #38bdf8;
            border: 1px solid #0284c7;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 800;
        """)
        slots_header.addWidget(self.lbl_active_slot_badge)
        slots_section.addLayout(slots_header)

        slots_frame = QFrame()
        slots_frame.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 4px;")
        slots_layout = QHBoxLayout(slots_frame)
        slots_layout.setContentsMargins(4, 4, 4, 4)
        slots_layout.setSpacing(6)

        self.slot_buttons: List[QPushButton] = []
        self.slot_icons = ["💎", "⚡", "🔥", "🌊", "🌙"]
        for i in range(5):
            slot_name = self.studio.slots[i].get("name", f"Slot {i+1}")
            btn = QPushButton(f"{self.slot_icons[i]} Slot {i+1}: {slot_name}")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda checked=False, idx=i: self._on_slot_clicked(idx))
            self.slot_buttons.append(btn)
            slots_layout.addWidget(btn)

        slots_section.addWidget(slots_frame)

        # Slot action buttons row
        slot_actions = QHBoxLayout()
        slot_actions.setSpacing(8)

        self.btn_cycle_profile = QPushButton("🔁 " + tr("rgb_cycle_btn"))
        self.btn_cycle_profile.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cycle_profile.setFixedHeight(30)
        self.btn_cycle_profile.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                border: 1px solid #38bdf8;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 11px;
                font-weight: 800;
            }
            QPushButton:hover {
                background-color: #0369a1;
                border-color: #7dd3fc;
            }
        """)
        self.btn_cycle_profile.clicked.connect(self.cycle_profile)

        self.btn_save_slot = QPushButton("💾 " + tr("rgb_save_slot_btn", num=self.studio.active_slot + 1))
        self.btn_save_slot.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save_slot.setFixedHeight(30)
        self.btn_save_slot.setStyleSheet("""
            QPushButton {
                background-color: #162032;
                color: #cbd5e1;
                border: 1px solid #233148;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #f8fafc;
                border-color: #38bdf8;
            }
        """)
        self.btn_cycle_bright = QPushButton("🔆 " + tr("tray_cycle_brightness"))
        self.btn_cycle_bright.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cycle_bright.setFixedHeight(30)
        self.btn_cycle_bright.setStyleSheet("""
            QPushButton {
                background-color: #162032;
                color: #cbd5e1;
                border: 1px solid #233148;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #f8fafc;
                border-color: #38bdf8;
            }
        """)
        self.btn_cycle_bright.clicked.connect(self.cycle_brightness)

        slot_actions.addWidget(self.btn_cycle_profile)
        slot_actions.addWidget(self.btn_cycle_bright)
        slot_actions.addWidget(self.btn_save_slot)
        slot_actions.addStretch()
        slots_section.addLayout(slot_actions)

        layout.addLayout(slots_section)

        # 1.6 Performance Mode Sync Card
        sync_card = QFrame()
        sync_card.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 6px 12px;")
        sync_layout = QHBoxLayout(sync_card)
        sync_layout.setContentsMargins(10, 8, 10, 8)
        sync_layout.setSpacing(12)

        sync_text_layout = QVBoxLayout()
        sync_text_layout.setSpacing(2)
        self.lbl_sync_title = QLabel(tr("rgb_sync_perf_title"))
        self.lbl_sync_title.setStyleSheet("color: #f8fafc; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        self.lbl_sync_sub = QLabel(tr("rgb_sync_perf_sub"))
        self.lbl_sync_sub.setStyleSheet("color: #64748b; font-size: 10px;")
        self.lbl_sync_sub.setWordWrap(True)
        sync_text_layout.addWidget(self.lbl_sync_title)
        sync_text_layout.addWidget(self.lbl_sync_sub)
        sync_layout.addLayout(sync_text_layout, stretch=1)

        self.btn_sync_perf = QPushButton()
        self.btn_sync_perf.setFixedHeight(28)
        self.btn_sync_perf.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sync_perf.clicked.connect(self._toggle_sync_performance)
        sync_layout.addWidget(self.btn_sync_perf)

        layout.addWidget(sync_card)


        # 2. Visual Keyboard Preview (4 Horizontal Zones)
        kb_section = QVBoxLayout()
        kb_section.setSpacing(6)

        self.lbl_kb_title = QLabel(tr("rgb_visual_topology"))
        self.lbl_kb_title.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;")
        kb_section.addWidget(self.lbl_kb_title)

        zones_container = QFrame()
        zones_container.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 10px; padding: 4px;")
        zones_layout = QHBoxLayout(zones_container)
        zones_layout.setContentsMargins(6, 6, 6, 6)
        zones_layout.setSpacing(8)

        self.zone_blocks: List[KeyboardZoneBlock] = []
        zone_specs = [
            (0, tr("rgb_zone_1_name"), tr("rgb_zone_1_keys")),
            (1, tr("rgb_zone_2_name"), tr("rgb_zone_2_keys")),
            (2, tr("rgb_zone_3_name"), tr("rgb_zone_3_keys")),
            (3, tr("rgb_zone_4_name"), tr("rgb_zone_4_keys")),
        ]

        for idx, z_name, k_label in zone_specs:
            init_color = self.studio.zone_colors[idx] if idx < len(self.studio.zone_colors) else (56, 189, 248)
            block = KeyboardZoneBlock(idx, z_name, k_label, init_color, parent=self)
            block.clicked.connect(self._on_zone_selected)
            block.color_change_requested.connect(self._open_color_dialog_for_zone)
            self.zone_blocks.append(block)
            zones_layout.addWidget(block)

        kb_section.addWidget(zones_container)
        layout.addLayout(kb_section)

        # 3. Quick Preset Buttons Row
        preset_section = QVBoxLayout()
        preset_section.setSpacing(6)

        self.lbl_preset_title = QLabel(tr("rgb_presets_title"))
        self.lbl_preset_title.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;")
        preset_section.addWidget(self.lbl_preset_title)

        presets_frame = QFrame()
        presets_frame.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 3px;")
        presets_layout = QHBoxLayout(presets_frame)
        presets_layout.setContentsMargins(4, 4, 4, 4)
        presets_layout.setSpacing(6)

        self.preset_buttons: Dict[str, QPushButton] = {}
        preset_items = [
            ("vantage_cyan", tr("rgb_preset_vantage_cyan")),
            ("cyber_neon", tr("rgb_preset_cyber_neon")),
            ("crimson_fury", tr("rgb_preset_crimson_fury")),
            ("emerald_stealth", tr("rgb_preset_emerald_stealth")),
            ("smooth_wave", tr("rgb_preset_smooth_wave")),
            ("off", tr("rgb_preset_off")),
        ]

        for p_key, p_label in preset_items:
            btn = QPushButton(p_label)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda checked=False, k=p_key: self._on_preset_clicked(k))
            self.preset_buttons[p_key] = btn
            presets_layout.addWidget(btn)

        preset_section.addWidget(presets_frame)
        layout.addLayout(preset_section)

        # 4. Controls Matrix (Brightness, Speed, Effect Mode)
        controls_grid = QGridLayout()
        controls_grid.setSpacing(12)

        # A. Brightness Control
        box_bright = QFrame()
        box_bright.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 8px;")
        bright_layout = QVBoxLayout(box_bright)
        bright_layout.setContentsMargins(8, 6, 8, 6)
        bright_layout.setSpacing(6)

        self.lbl_b_title = QLabel(tr("rgb_brightness_title"))
        self.lbl_b_title.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;")
        bright_layout.addWidget(self.lbl_b_title)

        b_btns_row = QHBoxLayout()
        b_btns_row.setSpacing(6)
        self.btn_bright_off = QPushButton(tr("rgb_off"))
        self.btn_bright_low = QPushButton(tr("rgb_low"))
        self.btn_bright_high = QPushButton(tr("rgb_high"))
        for btn in (self.btn_bright_off, self.btn_bright_low, self.btn_bright_high):
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(30)
            b_btns_row.addWidget(btn)

        self.btn_bright_off.clicked.connect(lambda: self._set_brightness(0))
        self.btn_bright_low.clicked.connect(lambda: self._set_brightness(1))
        self.btn_bright_high.clicked.connect(lambda: self._set_brightness(2))
        bright_layout.addLayout(b_btns_row)
        controls_grid.addWidget(box_bright, 0, 0)

        # B. Speed Control
        box_speed = QFrame()
        box_speed.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 8px;")
        speed_layout = QVBoxLayout(box_speed)
        speed_layout.setContentsMargins(8, 6, 8, 6)
        speed_layout.setSpacing(6)

        self.lbl_s_title = QLabel(tr("rgb_speed_title"))
        self.lbl_s_title.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;")
        speed_layout.addWidget(self.lbl_s_title)

        s_btns_row = QHBoxLayout()
        s_btns_row.setSpacing(6)
        self.speed_buttons: Dict[int, QPushButton] = {}
        for spd in (1, 2, 3, 4):
            btn = QPushButton(f"{spd}x")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda checked=False, s=spd: self._set_speed(s))
            self.speed_buttons[spd] = btn
            s_btns_row.addWidget(btn)
        speed_layout.addLayout(s_btns_row)
        controls_grid.addWidget(box_speed, 0, 1)

        layout.addLayout(controls_grid)

        # 5. Effect Mode Selector
        effect_box = QFrame()
        effect_box.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 8px;")
        eff_layout = QVBoxLayout(effect_box)
        eff_layout.setContentsMargins(8, 6, 8, 6)
        eff_layout.setSpacing(6)

        self.lbl_eff_title = QLabel(tr("rgb_pattern_title"))
        self.lbl_eff_title.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;")
        eff_layout.addWidget(self.lbl_eff_title)

        eff_row = QHBoxLayout()
        eff_row.setSpacing(6)
        self.effect_buttons: Dict[str, QPushButton] = {}
        effect_items = [
            ("static", tr("rgb_eff_static")),
            ("breathing", tr("rgb_eff_breathing")),
            ("smooth_wave", tr("rgb_eff_smooth_wave")),
            ("wave", tr("rgb_eff_wave")),
        ]
        for e_key, e_label in effect_items:
            btn = QPushButton(e_label)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda checked=False, ek=e_key: self._set_effect(ek))
            self.effect_buttons[e_key] = btn
            eff_row.addWidget(btn)
        eff_layout.addLayout(eff_row)
        layout.addWidget(effect_box)

        # 6. Custom Color Palette & Multi-Zone Assignment
        palette_box = QFrame()
        palette_box.setStyleSheet("background-color: #080d16; border: 1px solid #1a2333; border-radius: 8px; padding: 8px;")
        pal_layout = QVBoxLayout(palette_box)
        pal_layout.setContentsMargins(8, 6, 8, 6)
        pal_layout.setSpacing(8)

        pal_top = QHBoxLayout()
        self.lbl_pal_title = QLabel(tr("rgb_palette_title"))
        self.lbl_pal_title.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;")

        self.btn_all_zones = QPushButton(tr("rgb_apply_single_active"))
        self.btn_all_zones.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_all_zones.setFixedHeight(26)
        self.btn_all_zones.setStyleSheet("""
            QPushButton {
                background-color: #121a29;
                color: #94a3b8;
                border: 1px solid #1e293b;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                color: #f8fafc;
                border-color: #38bdf8;
            }
        """)
        self.btn_all_zones.clicked.connect(self._toggle_apply_all_zones)

        pal_top.addWidget(self.lbl_pal_title)
        pal_top.addStretch()
        pal_top.addWidget(self.btn_all_zones)
        pal_layout.addLayout(pal_top)

        # Color Swatches Bar
        swatches_row = QHBoxLayout()
        swatches_row.setSpacing(6)

        for hex_code, color_name in LUXURY_PALETTE:
            sw_btn = QPushButton()
            sw_btn.setToolTip(f"{color_name} ({hex_code})")
            sw_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            sw_btn.setFixedHeight(28)
            sw_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_code};
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    border: 2px solid #ffffff;
                }}
            """)
            sw_btn.clicked.connect(lambda checked=False, h=hex_code: self._apply_color_from_hex(h))
            swatches_row.addWidget(sw_btn)

        # Dialog Launcher Button
        self.btn_custom_dialog = QPushButton(tr("rgb_pick_color"))
        self.btn_custom_dialog.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_custom_dialog.setFixedHeight(28)
        self.btn_custom_dialog.setStyleSheet("""
            QPushButton {
                background-color: #162032;
                color: #38bdf8;
                border: 1px solid #233148;
                border-radius: 6px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1e293b;
                border-color: #38bdf8;
                color: #ffffff;
            }
        """)
        self.btn_custom_dialog.clicked.connect(lambda: self._open_color_dialog_for_zone(self.selected_zone))
        swatches_row.addWidget(self.btn_custom_dialog)

        pal_layout.addLayout(swatches_row)
        layout.addWidget(palette_box)

    def retranslate_ui(self):
        self.lbl_title.setText(tr("rgb_title"))
        self.badge.setText(tr("rgb_controller_badge"))
        self.lbl_slots_title.setText(tr("rgb_slots_header"))
        self.btn_cycle_profile.setText("🔁 " + tr("rgb_cycle_btn"))
        self.btn_cycle_bright.setText("🔆 " + tr("tray_cycle_brightness"))
        self.lbl_sync_title.setText(tr("rgb_sync_perf_title"))
        self.lbl_sync_sub.setText(tr("rgb_sync_perf_sub"))
        self.btn_owner_app.setText(tr("rgb_owner_app"))
        self.btn_owner_bios.setText(tr("rgb_owner_bios"))

        self.lbl_kb_title.setText(tr("rgb_visual_topology"))
        zone_specs = [
            (tr("rgb_zone_1_name"), tr("rgb_zone_1_keys")),
            (tr("rgb_zone_2_name"), tr("rgb_zone_2_keys")),
            (tr("rgb_zone_3_name"), tr("rgb_zone_3_keys")),
            (tr("rgb_zone_4_name"), tr("rgb_zone_4_keys")),
        ]
        for idx, (z_name, k_label) in enumerate(zone_specs):
            if idx < len(self.zone_blocks):
                self.zone_blocks[idx].retranslate_ui(z_name, k_label)

        self.lbl_preset_title.setText(tr("rgb_presets_title"))
        preset_items = [
            ("vantage_cyan", tr("rgb_preset_vantage_cyan")),
            ("cyber_neon", tr("rgb_preset_cyber_neon")),
            ("crimson_fury", tr("rgb_preset_crimson_fury")),
            ("emerald_stealth", tr("rgb_preset_emerald_stealth")),
            ("smooth_wave", tr("rgb_preset_smooth_wave")),
            ("off", tr("rgb_preset_off")),
        ]
        for p_key, p_label in preset_items:
            if p_key in self.preset_buttons:
                self.preset_buttons[p_key].setText(p_label)

        self.lbl_b_title.setText(tr("rgb_brightness_title"))
        self.btn_bright_off.setText(tr("rgb_off"))
        self.btn_bright_low.setText(tr("rgb_low"))
        self.btn_bright_high.setText(tr("rgb_high"))

        self.lbl_s_title.setText(tr("rgb_speed_title"))

        self.lbl_eff_title.setText(tr("rgb_pattern_title"))
        effect_items = [
            ("static", tr("rgb_eff_static")),
            ("breathing", tr("rgb_eff_breathing")),
            ("smooth_wave", tr("rgb_eff_smooth_wave")),
            ("wave", tr("rgb_eff_wave")),
        ]
        for e_key, e_label in effect_items:
            if e_key in self.effect_buttons:
                self.effect_buttons[e_key].setText(e_label)

        self.lbl_pal_title.setText(tr("rgb_palette_title"))
        if self.apply_to_all_zones:
            self.btn_all_zones.setText(tr("rgb_apply_all_active"))
        else:
            self.btn_all_zones.setText(tr("rgb_apply_single_active"))
        self.btn_custom_dialog.setText(tr("rgb_pick_color"))

        # Sync UI with loaded studio state
        self._sync_ui_from_studio()

    def _sync_ui_from_studio(self):
        """
        Updates all UI buttons, previews, and active indicators based on studio state.
        """
        # 0. Update Profile Slots & Ownership
        cur_slot = self.studio.active_slot
        self.lbl_active_slot_badge.setText(f"{tr('rgb_slot_active_badge')}: {cur_slot + 1} / 5")
        self.btn_save_slot.setText(f"💾 {tr('rgb_save_slot_btn', num=cur_slot + 1)}")

        for i, btn in enumerate(self.slot_buttons):
            s_data = self.studio.slots[i]
            btn.setText(f"{self.slot_icons[i]} Slot {i+1}: {s_data['name']}")
            if i == cur_slot:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0284c7;
                        color: #ffffff;
                        border: 1.5px solid #38bdf8;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: 800;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #94a3b8;
                        border: 1px solid #1e293b;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #121c2e;
                        color: #f8fafc;
                        border-color: #38bdf8;
                    }
                """)

        # Ownership Styling
        is_app = (self.studio.control_owner == "app")
        self.btn_owner_app.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                border: 1px solid #38bdf8;
                border-radius: 4px;
                padding: 1px 8px;
                font-size: 10px;
                font-weight: 800;
            }
        """ if is_app else """
            QPushButton {
                background-color: transparent;
                color: #64748b;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 1px 8px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #cbd5e1;
            }
        """)

        self.btn_owner_bios.setStyleSheet("""
            QPushButton {
                background-color: #d97706;
                color: #ffffff;
                border: 1px solid #f59e0b;
                border-radius: 4px;
                padding: 1px 8px;
                font-size: 10px;
                font-weight: 800;
            }
        """ if not is_app else """
            QPushButton {
                background-color: transparent;
                color: #64748b;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 1px 8px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #cbd5e1;
            }
        """)

        # Performance Mode Sync Button Styling
        is_sync = self.studio.sync_with_performance
        self.btn_sync_perf.setText("⚡ " + tr("rgb_sync_perf_active") if is_sync else "🔒 " + tr("rgb_sync_perf_disabled"))
        if is_sync:
            self.btn_sync_perf.setStyleSheet("""
                QPushButton {
                    background-color: #0284c7;
                    color: #ffffff;
                    border: 1px solid #38bdf8;
                    border-radius: 6px;
                    padding: 0 14px;
                    font-size: 11px;
                    font-weight: 800;
                }
                QPushButton:hover {
                    background-color: #0369a1;
                    border-color: #7dd3fc;
                }
            """)
        else:
            self.btn_sync_perf.setStyleSheet("""
                QPushButton {
                    background-color: #162032;
                    color: #94a3b8;
                    border: 1px solid #233148;
                    border-radius: 6px;
                    padding: 0 14px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #1e293b;
                    color: #f8fafc;
                    border-color: #38bdf8;
                }
            """)

        # 1. Update Zone Swatches
        for i, block in enumerate(self.zone_blocks):
            if i < len(self.studio.zone_colors):
                block.update_color(self.studio.zone_colors[i])
            block.set_selected(i == self.selected_zone)

        # 2. Update Presets Active State
        cur_preset = self.studio.current_preset
        for p_key, btn in self.preset_buttons.items():
            is_active = (cur_preset == p_key)
            if is_active:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0284c7;
                        color: #ffffff;
                        border: 1px solid #38bdf8;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: 800;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #94a3b8;
                        border: 1px solid transparent;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #121c2e;
                        color: #f8fafc;
                    }
                """)

        # 3. Update Brightness Buttons
        b_val = self.studio.brightness
        for btn, target in ((self.btn_bright_off, 0), (self.btn_bright_low, 1), (self.btn_bright_high, 2)):
            if b_val == target:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0284c7;
                        color: #ffffff;
                        border: 1px solid #38bdf8;
                        border-radius: 5px;
                        font-size: 11px;
                        font-weight: 800;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #94a3b8;
                        border: 1px solid transparent;
                        border-radius: 5px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #121c2e;
                        color: #f8fafc;
                    }
                """)


        # 4. Update Speed Buttons
        s_val = self.studio.speed
        for spd, btn in self.speed_buttons.items():
            if s_val == spd:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0284c7;
                        color: #ffffff;
                        border: 1px solid #38bdf8;
                        border-radius: 5px;
                        font-size: 11px;
                        font-weight: 800;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #94a3b8;
                        border: 1px solid transparent;
                        border-radius: 5px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #121c2e;
                        color: #f8fafc;
                    }
                """)

        # 5. Update Effect Buttons
        eff_val = self.studio.effect
        for ek, btn in self.effect_buttons.items():
            if eff_val in (ek, ek.replace("_", "")):
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0284c7;
                        color: #ffffff;
                        border: 1px solid #38bdf8;
                        border-radius: 5px;
                        font-size: 11px;
                        font-weight: 800;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #94a3b8;
                        border: 1px solid transparent;
                        border-radius: 5px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #121c2e;
                        color: #f8fafc;
                    }
                """)

    def _on_zone_selected(self, zone_idx: int):
        self.selected_zone = zone_idx
        for i, block in enumerate(self.zone_blocks):
            block.set_selected(i == self.selected_zone)

    def _on_preset_clicked(self, preset_key: str):
        self.studio.apply_preset(preset_key)
        self._sync_ui_from_studio()
        self.preset_selected.emit(preset_key)
        self.state_changed.emit()

    def _set_brightness(self, brightness: int):
        self.studio.apply_state(
            effect=self.studio.effect,
            speed=self.studio.speed,
            brightness=brightness,
            zone_colors=self.studio.zone_colors
        )
        self._sync_ui_from_studio()
        self.state_changed.emit()

    def _set_speed(self, speed: int):
        self.studio.apply_state(
            effect=self.studio.effect,
            speed=speed,
            brightness=self.studio.brightness,
            zone_colors=self.studio.zone_colors
        )
        self._sync_ui_from_studio()
        self.state_changed.emit()

    def _set_effect(self, effect_name: str):
        self.studio.apply_state(
            effect=effect_name,
            speed=self.studio.speed,
            brightness=self.studio.brightness if self.studio.brightness > 0 else 2,
            zone_colors=self.studio.zone_colors
        )
        self._sync_ui_from_studio()
        self.state_changed.emit()

    def _toggle_apply_all_zones(self):
        self.apply_to_all_zones = not self.apply_to_all_zones
        if self.apply_to_all_zones:
            self.btn_all_zones.setText(tr("rgb_apply_all_active"))
            self.btn_all_zones.setStyleSheet("""
                QPushButton {
                    background-color: #0369a1;
                    color: #ffffff;
                    border: 1px solid #38bdf8;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 10px;
                    font-weight: 800;
                }
            """)
        else:
            self.btn_all_zones.setText(tr("rgb_apply_single_active"))
            self.btn_all_zones.setStyleSheet("""
                QPushButton {
                    background-color: #121a29;
                    color: #94a3b8;
                    border: 1px solid #1e293b;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 10px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    color: #f8fafc;
                    border-color: #38bdf8;
                }
            """)

    def _apply_color_from_hex(self, hex_code: str):
        qc = QColor(hex_code)
        rgb = (qc.red(), qc.green(), qc.blue())
        self._apply_rgb_to_zones(rgb)

    def _apply_rgb_to_zones(self, rgb: Tuple[int, int, int]):
        new_colors = list(self.studio.zone_colors)
        if self.apply_to_all_zones:
            new_colors = [rgb, rgb, rgb, rgb]
        else:
            if 0 <= self.selected_zone < len(new_colors):
                new_colors[self.selected_zone] = rgb

        # Setting custom color overrides named preset indicator
        self.studio.current_preset = None
        self.studio.apply_state(
            effect=self.studio.effect,
            speed=self.studio.speed,
            brightness=self.studio.brightness if self.studio.brightness > 0 else 2,
            zone_colors=new_colors
        )
        self._sync_ui_from_studio()
        self.state_changed.emit()

    def _open_color_dialog_for_zone(self, zone_idx: int):
        self.selected_zone = zone_idx
        for i, block in enumerate(self.zone_blocks):
            block.set_selected(i == self.selected_zone)

        init_c = self.studio.zone_colors[zone_idx]
        initial_qcolor = QColor(init_c[0], init_c[1], init_c[2])
        chosen = QColorDialog.getColor(initial_qcolor, self, f"Pilih Warna RGB - Zona {zone_idx + 1}")
        if chosen.isValid():
            rgb = (chosen.red(), chosen.green(), chosen.blue())
            self._apply_rgb_to_zones(rgb)

    def cycle_profile(self) -> Tuple[int, str, Dict[str, Any]]:
        """
        Cycles to next profile slot (1..5), syncs UI, emits slot_changed, and returns slot info.
        """
        slot_num, slot_name, slot_data = self.studio.cycle_profile()
        self._sync_ui_from_studio()
        self.slot_changed.emit(slot_num, slot_name)
        self.state_changed.emit()
        return slot_num, slot_name, slot_data

    def _on_slot_clicked(self, idx: int):
        self.studio.apply_slot(idx)
        self._sync_ui_from_studio()
        slot = self.studio.slots[idx]
        self.slot_changed.emit(idx + 1, slot["name"])
        self.state_changed.emit()

    def save_active_slot(self):
        self.studio.save_current_to_slot(self.studio.active_slot)
        self._sync_ui_from_studio()
        self.state_changed.emit()

    def _set_control_owner(self, owner: str):
        self.studio.set_control_owner(owner)
        self._sync_ui_from_studio()
        self.state_changed.emit()

    def cycle_brightness(self) -> int:
        """
        Cycles keyboard backlight through 3 brightness levels (Off -> 50% -> 100%),
        syncs UI, emits brightness_cycled, and returns the new level.
        """
        new_b = self.studio.cycle_brightness()
        self._sync_ui_from_studio()
        self.brightness_cycled.emit(new_b)
        self.state_changed.emit()
        return new_b

    def _toggle_sync_performance(self):
        cur = self.studio.sync_with_performance
        self.studio.set_sync_with_performance(not cur)
        self._sync_ui_from_studio()
        self.sync_perf_toggled.emit(not cur)


def get_rgb_studio() -> LenovoRgbStudio:
    """Helper function to retrieve singleton instance of LenovoRgbStudio."""
    return LenovoRgbStudio.get_instance()
