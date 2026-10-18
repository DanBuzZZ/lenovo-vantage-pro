import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QScrollArea, QFrame,
    QSystemTrayIcon, QMenu, QButtonGroup, QGridLayout, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

from backend import LenovoHardware, LenovoDisplayManager
from styles import PRO_MAX_THEME
from widgets import (
    RadialMeter, QuickToggleCard, FanControlPanel,
    TurbineGauge, ThermalTrajectoryChart,
    MaintenancePurgeCockpit, EsportsDisplaySuiteCard,
    GamingCoreSchedulerCard
)
from osd import get_osd
from rgb_studio import RgbLightingStudioCard, get_rgb_studio
from gaming_tools import (
    WifiPingStabilizerCard, BlackboxFlightRecorderCard,
    SystemDiagnosticCard, LenovoBlackboxRecorder
)

ICON_PATH = "/usr/share/icons/hicolor/scalable/apps/vantage.png"

class LenovoVantageApp(QMainWindow):
    sig_hotkey_refresh_rate = pyqtSignal()
    sig_hotkey_fan_mode = pyqtSignal()
    sig_firmware_profile = pyqtSignal(str)
    sig_game_started = pyqtSignal(int, str)
    sig_game_stopped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lenovo Vantage Pro — Hardware Control Center")
        self.setMinimumSize(1000, 700)
        self.resize(1160, 820)
        self.smart_ac_dc_enabled = False
        self.current_refresh_hz = 165
        self.current_overdrive = 0

        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.machine_info = LenovoHardware.get_machine_info()
        bios_raw = self.machine_info.get("bios", "JMCN48WW")
        self.bios_clean = bios_raw.split("(")[0].strip() or "JMCN48WW"
        self.model_clean = self.machine_info.get("family", "IdeaPad Gaming 3 15IAH7")

        self.osd = get_osd(self)

        self.init_ui()
        self.setup_tray()

        # Connect thread-safe signals to GUI slots
        self.sig_hotkey_refresh_rate.connect(self.handle_hotkey_refresh_rate)
        self.sig_hotkey_fan_mode.connect(self.handle_hotkey_fan_mode)
        self.sig_firmware_profile.connect(self.handle_firmware_profile_changed)
        self.sig_game_started.connect(self.on_game_started)
        self.sig_game_stopped.connect(self.on_game_stopped)

        # Initialize and register Global Hotkeys (Fn+Q, Fn+R, platform_profile)
        self.hotkey_listener = LenovoHardware.get_hotkey_listener()
        self.hotkey_listener.register_callbacks(
            on_toggle_refresh_rate=lambda: self.sig_hotkey_refresh_rate.emit(),
            on_cycle_fan_mode=lambda: self.sig_hotkey_fan_mode.emit(),
            on_profile_changed=lambda p: self.sig_firmware_profile.emit(p),
        )

        # Initialize Auto Game Detector
        self.game_detector = LenovoHardware.get_game_detector()
        self.game_detector.register_callbacks(
            on_game_started=lambda pid, name: self.sig_game_started.emit(pid, name),
            on_game_stopped=lambda name: self.sig_game_stopped.emit(name),
        )

        # Telemetry Timer (1.0 Hz loop as specified)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(1000)
        self.update_telemetry()

    def init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Navigation
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(14, 24, 14, 20)
        s_layout.setSpacing(6)

        # Brand Title in Sidebar
        brand_box = QVBoxLayout()
        brand_title = QLabel("LENOVO")
        brand_title.setObjectName("brandTitle")
        brand_sub = QLabel("VANTAGE PRO")
        brand_sub.setObjectName("brandSubtitle")
        brand_box.addWidget(brand_title)
        brand_box.addWidget(brand_sub)
        s_layout.addLayout(brand_box)
        s_layout.addSpacing(22)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_dash = self.create_nav_btn("  Dashboard", 0, True)
        self.btn_bat = self.create_nav_btn("  Power & Battery", 1)
        self.btn_gpu = self.create_nav_btn("  GPU & Display", 2)
        self.btn_rgb = self.create_nav_btn("  RGB Lighting Studio", 3)
        self.btn_sys = self.create_nav_btn("  Device Specs & Diagnostics", 4)

        s_layout.addWidget(self.btn_dash)
        s_layout.addWidget(self.btn_bat)
        s_layout.addWidget(self.btn_gpu)
        s_layout.addWidget(self.btn_rgb)
        s_layout.addWidget(self.btn_sys)
        s_layout.addStretch()

        # Machine Identity Badge in Sidebar
        badge = QFrame()
        badge.setStyleSheet("background-color: #0b111e; border: 1px solid #1a2333; border-radius: 10px;")
        b_layout = QVBoxLayout(badge)
        b_layout.setContentsMargins(12, 10, 12, 10)
        b_layout.setSpacing(4)
        lbl_fam = QLabel(self.model_clean)
        lbl_fam.setStyleSheet("color: #f8fafc; font-weight: 700; font-size: 11px;")
        lbl_fam.setWordWrap(True)
        lbl_mtm = QLabel(f"MTM: {self.machine_info.get('mtm', '82S9')} • {self.bios_clean}")
        lbl_mtm.setStyleSheet("color: #64748b; font-size: 10px;")
        lbl_mtm.setWordWrap(True)
        b_layout.addWidget(lbl_fam)
        b_layout.addWidget(lbl_mtm)
        s_layout.addWidget(badge)

        main_layout.addWidget(sidebar)

        # 2. Main Content Stack
        content_box = QWidget()
        c_layout = QVBoxLayout(content_box)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # Header Bar: LENOVO VANTAGE PRO, Model, BIOS, SYSTEM OPTIMAL
        header = QWidget()
        header.setObjectName("header")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(28, 14, 28, 14)

        header_left = QVBoxLayout()
        header_left.setSpacing(2)

        self.title_view = QLabel("LENOVO VANTAGE PRO")
        self.title_view.setObjectName("headerTitle")

        self.header_meta = QLabel(f"Model: {self.model_clean}  •  BIOS: {self.bios_clean}")
        self.header_meta.setObjectName("headerMeta")

        header_left.addWidget(self.title_view)
        header_left.addWidget(self.header_meta)
        h_layout.addLayout(header_left)

        h_layout.addStretch()

        # System Optimal Pill
        self.pill_optimal = QLabel("● SYSTEM OPTIMAL")
        self.pill_optimal.setStyleSheet("""
            background-color: #064e3b;
            color: #10b981;
            border: 1px solid #10b981;
            border-radius: 6px;
            padding: 5px 12px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.5px;
        """)
        h_layout.addWidget(self.pill_optimal)

        # Active Cooling Profile Pill
        self.active_mode_pill = QLabel("⚖️ STANDARD MODE")
        self.active_mode_pill.setStyleSheet("""
            background-color: #172033;
            color: #38bdf8;
            border: 1px solid #38bdf8;
            border-radius: 6px;
            padding: 5px 12px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.5px;
        """)
        h_layout.addWidget(self.active_mode_pill)

        c_layout.addWidget(header)

        # Stacked Views
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_dashboard_view())
        self.stack.addWidget(self.create_battery_view())
        self.stack.addWidget(self.create_gpu_view())
        self.stack.addWidget(self.create_rgb_view())
        self.stack.addWidget(self.create_system_view())

        c_layout.addWidget(self.stack)
        main_layout.addWidget(content_box, stretch=1)

    def create_nav_btn(self, text: str, page_idx: int, checked: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("navBtn")
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.clicked.connect(lambda: self.switch_page(page_idx, text.strip()))
        self.nav_group.addButton(btn)
        return btn

    def switch_page(self, idx: int, title: str):
        self.stack.setCurrentIndex(idx)
        if idx == 0:
            self.header_meta.setText(f"Model: {self.model_clean}  •  BIOS: {self.bios_clean}")
        else:
            self.header_meta.setText(f"{title}  •  Model: {self.model_clean}  •  BIOS: {self.bios_clean}")

    def create_dashboard_view(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 20, 28, 28)
        layout.setSpacing(20)

        # 1. Hero Banner
        hero = QFrame()
        hero.setObjectName("heroBanner")
        h_layout = QVBoxLayout(hero)
        h_layout.setSpacing(12)

        htop = QHBoxLayout()
        v_title = QVBoxLayout()
        v_title.setSpacing(3)
        h_title = QLabel(self.model_clean)
        h_title.setObjectName("heroTitle")
        h_sub = QLabel(f"Lenovo Legion Architecture • MTM {self.machine_info.get('mtm', '82S9')} • BIOS {self.bios_clean}")
        h_sub.setObjectName("heroSubtitle")
        v_title.addWidget(h_title)
        v_title.addWidget(h_sub)
        htop.addLayout(v_title)
        htop.addStretch()

        self.pill_ac = QLabel("⚡ AC CONNECTED")
        self.pill_ac.setProperty("class", "StatusPill")
        self.pill_cons = QLabel("🔋 FULL CHARGE 100%")
        self.pill_cons.setProperty("class", "StatusPill")
        self.pill_gpu = QLabel("🎮 RTX 3050 ACTIVE")
        self.pill_gpu.setProperty("class", "StatusPill")

        htop.addWidget(self.pill_ac)
        htop.addWidget(self.pill_cons)
        htop.addWidget(self.pill_gpu)
        h_layout.addLayout(htop)

        layout.addWidget(hero)

        # 2. Sesi Pendinginan Atas: Dual TurbineGauge + FanControlPanel (with ThermalTrajectoryChart)
        sec_cooling = QVBoxLayout()
        sec_cooling.setSpacing(12)

        lbl_cooling = QLabel("THERMAL DYNAMICS & TURBINE COOLING COCKPIT")
        lbl_cooling.setProperty("class", "CardHeader")
        sec_cooling.addWidget(lbl_cooling)

        # Dual Turbine Gauges (CPU Fan & GPU Fan) centered
        turbines_layout = QHBoxLayout()
        turbines_layout.setSpacing(36)
        turbines_layout.addStretch()
        self.cpu_turbine = TurbineGauge(title="CPU Turbine Fan", fan_id="cpu")
        self.gpu_turbine = TurbineGauge(title="GPU Turbine Fan", fan_id="gpu")
        turbines_layout.addWidget(self.cpu_turbine)
        turbines_layout.addWidget(self.gpu_turbine)
        turbines_layout.addStretch()
        sec_cooling.addLayout(turbines_layout)

        # Fan Control Panel (3 pure mode cards + 60s ThermalTrajectoryChart + Live Telemetry)
        self.fan_panel = FanControlPanel()
        self.fan_panel.fan_mode_selected.connect(self.set_fan_cooling_mode)
        sec_cooling.addWidget(self.fan_panel)

        # Dedicated Hardware Purge & Dust Cleaning Cockpit
        self.purge_cockpit = MaintenancePurgeCockpit()
        self.purge_cockpit.start_purge_requested.connect(self.on_start_dust_purge)
        self.purge_cockpit.cancel_purge_requested.connect(self.on_cancel_dust_purge)
        sec_cooling.addWidget(self.purge_cockpit)
        layout.addLayout(sec_cooling)

        # 3. System Telemetry Matrix Row
        sec_telemetry = QVBoxLayout()
        sec_telemetry.setSpacing(12)
        lbl_telem = QLabel("SYSTEM TELEMETRY MATRIX & HARDWARE SENSORS")
        lbl_telem.setProperty("class", "CardHeader")
        sec_telemetry.addWidget(lbl_telem)

        # Radial Gauges Row
        gauges_frame = QFrame()
        gauges_frame.setProperty("class", "ProCard")
        g_layout = QHBoxLayout(gauges_frame)
        g_layout.setContentsMargins(14, 16, 14, 16)
        g_layout.setSpacing(18)

        self.meter_cpu_temp = RadialMeter("CPU TEMP", unit="°C", max_val=105.0)
        self.meter_cpu_load = RadialMeter("CPU LOAD", unit="%", max_val=100.0)
        self.meter_gpu_temp = RadialMeter("GPU TEMP", unit="°C", max_val=100.0)
        self.meter_ram = RadialMeter("RAM USAGE", unit="%", max_val=100.0)

        g_layout.addStretch()
        g_layout.addWidget(self.meter_cpu_temp)
        g_layout.addStretch()
        g_layout.addWidget(self.meter_cpu_load)
        g_layout.addStretch()
        g_layout.addWidget(self.meter_gpu_temp)
        g_layout.addStretch()
        g_layout.addWidget(self.meter_ram)
        g_layout.addStretch()
        sec_telemetry.addWidget(gauges_frame)

        # Telemetry Detail Boxes Grid: CPU RAPL/EPP, RTX 3050 VRAM/Power, RAM, Battery Health & Cycles
        telem_grid = QGridLayout()
        telem_grid.setSpacing(14)

        # Box 1: CPU Core & RAPL Power
        box_cpu = QFrame()
        box_cpu.setProperty("class", "StatBox")
        b1_layout = QVBoxLayout(box_cpu)
        b1_layout.setSpacing(4)
        lbl_b1_title = QLabel("INTEL CPU ARCHITECTURE & POWER")
        lbl_b1_title.setProperty("class", "StatLabel")
        self.lbl_cpu_stat = QLabel("43°C • 17% (16 Cores)")
        self.lbl_cpu_stat.setProperty("class", "StatValue")
        self.lbl_rapl_stat = QLabel("PL1: 35W | PL2: 45W | EPP: power")
        self.lbl_rapl_stat.setProperty("class", "StatSub")
        b1_layout.addWidget(lbl_b1_title)
        b1_layout.addWidget(self.lbl_cpu_stat)
        b1_layout.addWidget(self.lbl_rapl_stat)
        telem_grid.addWidget(box_cpu, 0, 0)

        # Box 2: NVIDIA RTX 3050 GPU
        box_gpu = QFrame()
        box_gpu.setProperty("class", "StatBox")
        b2_layout = QVBoxLayout(box_gpu)
        b2_layout.setSpacing(4)
        lbl_b2_title = QLabel("NVIDIA GEFORCE RTX 3050 LAPTOP")
        lbl_b2_title.setProperty("class", "StatLabel")
        self.lbl_gpu_stat = QLabel("41°C • 0% Utilization")
        self.lbl_gpu_stat.setProperty("class", "StatValue")
        self.lbl_vram_stat = QLabel("VRAM: 39 / 4096 MB (1.0%) • Active")
        self.lbl_vram_stat.setProperty("class", "StatSub")
        b2_layout.addWidget(lbl_b2_title)
        b2_layout.addWidget(self.lbl_gpu_stat)
        b2_layout.addWidget(self.lbl_vram_stat)
        telem_grid.addWidget(box_gpu, 0, 1)

        # Box 3: RAM Memory Usage
        box_ram = QFrame()
        box_ram.setProperty("class", "StatBox")
        b3_layout = QVBoxLayout(box_ram)
        b3_layout.setSpacing(4)
        lbl_b3_title = QLabel("SYSTEM RAM USAGE")
        lbl_b3_title.setProperty("class", "StatLabel")
        self.lbl_ram_stat = QLabel("8.2 GB / 15.3 GB (54%)")
        self.lbl_ram_stat.setProperty("class", "StatValue")
        self.lbl_ram_sub = QLabel("DDR4 Dual Channel High-Throughput")
        self.lbl_ram_sub.setProperty("class", "StatSub")
        b3_layout.addWidget(lbl_b3_title)
        b3_layout.addWidget(self.lbl_ram_stat)
        b3_layout.addWidget(self.lbl_ram_sub)
        telem_grid.addWidget(box_ram, 1, 0)

        # Box 4: Battery Health & Cycles
        box_bat = QFrame()
        box_bat.setProperty("class", "StatBox")
        b4_layout = QVBoxLayout(box_bat)
        b4_layout.setSpacing(4)
        lbl_b4_title = QLabel("BATTERY HEALTH & DISCHARGE")
        lbl_b4_title.setProperty("class", "StatLabel")
        self.lbl_bat_stat = QLabel("72% • Discharging (38.0W)")
        self.lbl_bat_stat.setProperty("class", "StatValue")
        self.lbl_health_stat = QLabel("Health: 86.5% • 255 Cycles (SMP Li-ion)")
        self.lbl_health_stat.setProperty("class", "StatSub")
        b4_layout.addWidget(lbl_b4_title)
        b4_layout.addWidget(self.lbl_bat_stat)
        b4_layout.addWidget(self.lbl_health_stat)
        telem_grid.addWidget(box_bat, 1, 1)

        sec_telemetry.addLayout(telem_grid)
        layout.addLayout(sec_telemetry)

        # 4. Esports Display Suite (Refresh Rate 165Hz/60Hz & Screen OverDrive)
        sec_disp = QVBoxLayout()
        sec_disp.setSpacing(12)
        lbl_disp = QLabel("ESPORTS DISPLAY & REFRESH RATE SUITE")
        lbl_disp.setProperty("class", "CardHeader")
        sec_disp.addWidget(lbl_disp)

        self.display_suite_dash = EsportsDisplaySuiteCard()
        self.display_suite_dash.refresh_rate_changed.connect(self.on_refresh_rate_changed)
        self.display_suite_dash.overdrive_changed.connect(self.on_overdrive_changed)
        self.display_suite_dash.smart_ac_dc_toggled.connect(self.on_smart_ac_dc_toggled)
        sec_disp.addWidget(self.display_suite_dash)
        layout.addLayout(sec_disp)

        # 5. Intel Alder Lake Core Scheduler & Optimizer
        sec_sched = QVBoxLayout()
        sec_sched.setSpacing(12)
        lbl_sched = QLabel("INTEL ALDER LAKE CORE SCHEDULER & OPTIMIZER")
        lbl_sched.setProperty("class", "CardHeader")
        sec_sched.addWidget(lbl_sched)

        self.scheduler_card = GamingCoreSchedulerCard()
        self.scheduler_card.no_turbo_toggled.connect(self.on_no_turbo_toggled)
        self.scheduler_card.auto_game_mode_toggled.connect(self.on_auto_game_mode_toggled)
        sec_sched.addWidget(self.scheduler_card)
        layout.addLayout(sec_sched)

        # 6. Esports Wi-Fi Latency & Blackbox Flight Recorder Suite
        sec_tools = QVBoxLayout()
        sec_tools.setSpacing(12)
        lbl_tools = QLabel("ESPORTS NETWORK & TELEMETRY FLIGHT RECORDER")
        lbl_tools.setProperty("class", "CardHeader")
        sec_tools.addWidget(lbl_tools)

        tools_row = QHBoxLayout()
        tools_row.setSpacing(14)
        self.wifi_card = WifiPingStabilizerCard()
        self.blackbox_card = BlackboxFlightRecorderCard()
        tools_row.addWidget(self.wifi_card, 1)
        tools_row.addWidget(self.blackbox_card, 1)
        sec_tools.addLayout(tools_row)
        layout.addLayout(sec_tools)

        # 7. Quick Hardware Switches (Zero pkexec, direct instant execution)
        sec_sw = QVBoxLayout()
        sec_sw.setSpacing(10)
        lbl_sw = QLabel("HARDWARE QUICK SWITCHES")
        lbl_sw.setProperty("class", "CardHeader")
        sec_sw.addWidget(lbl_sw)

        sw_grid = QGridLayout()
        sw_grid.setSpacing(14)

        self.sw_conservation = QuickToggleCard(
            "🔋", "Battery Conservation (75-80%)",
            "Limits battery charge to ~75-80% to protect Li-ion battery health under continuous AC power.",
            checked=LenovoHardware.get_conservation_mode()
        )
        self.sw_conservation.toggled.connect(self.on_conservation_toggled)

        self.sw_fn_lock = QuickToggleCard(
            "⌨️", "Fn Key Lock",
            "Switches top keyboard row priority between standard F1-F12 keys and Special Media Hotkeys.",
            checked=LenovoHardware.get_fn_lock()
        )
        self.sw_fn_lock.toggled.connect(LenovoHardware.set_fn_lock)

        self.sw_touchpad = QuickToggleCard(
            "🖱️", "Touchpad Lock",
            "Disables internal touchpad during gaming to eliminate accidental palm swipes.",
            checked=not LenovoHardware.get_touchpad_status()
        )
        self.sw_touchpad.toggled.connect(lambda locked: LenovoHardware.set_touchpad_status(not locked))

        self.sw_camera = QuickToggleCard(
            "📷", "Camera Privacy Shutter",
            "Hard unloads the kernel webcam driver (uvcvideo) to physically prevent camera streaming.",
            checked=not LenovoHardware.get_camera_status()
        )
        self.sw_camera.toggled.connect(lambda disabled: LenovoHardware.set_camera_status(not disabled))

        sw_grid.addWidget(self.sw_conservation, 0, 0)
        sw_grid.addWidget(self.sw_fn_lock, 0, 1)
        sw_grid.addWidget(self.sw_touchpad, 1, 0)
        sw_grid.addWidget(self.sw_camera, 1, 1)

        sec_sw.addLayout(sw_grid)
        layout.addLayout(sec_sw)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def create_battery_view(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 22, 28, 28)
        layout.setSpacing(20)

        lbl = QLabel("BATTERY HEALTH & POWER ANALYTICS")
        lbl.setProperty("class", "CardHeader")
        layout.addWidget(lbl)

        card = QFrame()
        card.setProperty("class", "ProCard")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(16)

        b_top = QHBoxLayout()
        self.meter_battery_main = RadialMeter("CAPACITY", unit="%", max_val=100.0)
        b_top.addWidget(self.meter_battery_main)

        b_summary = QVBoxLayout()
        b_summary.setSpacing(6)
        self.bat_cap_label = QLabel("77% Remaining")
        self.bat_cap_label.setStyleSheet("color: #f8fafc; font-size: 26px; font-weight: 800;")
        self.bat_status_label = QLabel("Status: Not charging (Conservation Limit Active)")
        self.bat_status_label.setStyleSheet("color: #38bdf8; font-size: 14px; font-weight: 600;")
        self.bat_health_badge = QLabel("Battery Health: 86.5% (Good Condition)")
        self.bat_health_badge.setStyleSheet("color: #10b981; font-size: 13px; font-weight: 700;")

        b_summary.addWidget(self.bat_cap_label)
        b_summary.addWidget(self.bat_status_label)
        b_summary.addWidget(self.bat_health_badge)
        b_summary.addStretch()
        b_top.addLayout(b_summary, stretch=1)
        c_layout.addLayout(b_top)

        c_layout.addSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(18)

        self.lbl_bat_health = QLabel("-")
        self.lbl_bat_cycles = QLabel("-")
        self.lbl_bat_full_energy = QLabel("-")
        self.lbl_bat_design_energy = QLabel("-")
        self.lbl_bat_model = QLabel("-")
        self.lbl_bat_mfg = QLabel("-")

        def make_field(label: str, val_lbl: QLabel, row: int, col: int):
            f = QVBoxLayout()
            f.setSpacing(3)
            l = QLabel(label)
            l.setStyleSheet("color: #64748b; font-size: 11px; text-transform: uppercase; font-weight: 700;")
            val_lbl.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 700;")
            f.addWidget(l)
            f.addWidget(val_lbl)
            grid.addLayout(f, row, col)

        make_field("Calculated Health", self.lbl_bat_health, 0, 0)
        make_field("Cycle Count", self.lbl_bat_cycles, 0, 1)
        make_field("Current Full Capacity", self.lbl_bat_full_energy, 0, 2)
        make_field("Factory Design Capacity", self.lbl_bat_design_energy, 1, 0)
        make_field("Battery Model Number", self.lbl_bat_model, 1, 1)
        make_field("Pack Manufacturer", self.lbl_bat_mfg, 1, 2)

        c_layout.addLayout(grid)
        layout.addWidget(card)

        # Conservation Mode Switch Card
        row_cons = QuickToggleCard(
            "🛡️", "Battery Conservation Mode (75-80%)",
            "Preserves chemical battery lifespan by stopping charge at ~80%. Recommended for desk & gaming setups.",
            checked=LenovoHardware.get_conservation_mode()
        )
        row_cons.toggled.connect(self.on_conservation_toggled)
        layout.addWidget(row_cons)

        layout.addStretch()
        return container

    def create_gpu_view(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 22, 28, 28)
        layout.setSpacing(20)

        lbl = QLabel("GRAPHICS ARCHITECTURE & TELEMETRY")
        lbl.setProperty("class", "CardHeader")
        layout.addWidget(lbl)

        # NVIDIA Discrete GPU Card
        card_nv = QFrame()
        card_nv.setProperty("class", "ProCard")
        n_layout = QVBoxLayout(card_nv)
        n_layout.setSpacing(14)

        title_box = QHBoxLayout()
        lbl_nv_title = QLabel("NVIDIA GeForce RTX 3050 Laptop GPU")
        lbl_nv_title.setStyleSheet("color: #f8fafc; font-size: 17px; font-weight: 800;")
        lbl_nv_badge = QLabel("DISCRETE ACCELERATOR")
        lbl_nv_badge.setStyleSheet("background-color: #064e3b; color: #10b981; border: 1px solid #10b981; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: 800;")
        title_box.addWidget(lbl_nv_title)
        title_box.addWidget(lbl_nv_badge)
        title_box.addStretch()
        n_layout.addLayout(title_box)

        grid_nv = QGridLayout()
        grid_nv.setSpacing(18)

        self.lbl_nv_temp = QLabel("-")
        self.lbl_nv_load = QLabel("-")
        self.lbl_nv_vram = QLabel("-")
        self.lbl_nv_driver = QLabel("-")

        def make_nv_field(label: str, val_lbl: QLabel, r: int, c: int):
            v = QVBoxLayout()
            v.setSpacing(3)
            l = QLabel(label)
            l.setStyleSheet("color: #64748b; font-size: 11px; text-transform: uppercase; font-weight: 700;")
            val_lbl.setStyleSheet("color: #f8fafc; font-size: 15px; font-weight: 700;")
            v.addWidget(l)
            v.addWidget(val_lbl)
            grid_nv.addLayout(v, r, c)

        make_nv_field("GPU Temperature", self.lbl_nv_temp, 0, 0)
        make_nv_field("Core Utilization", self.lbl_nv_load, 0, 1)
        make_nv_field("Dedicated VRAM Used", self.lbl_nv_vram, 0, 2)
        make_nv_field("NVIDIA Linux Driver", self.lbl_nv_driver, 0, 3)

        n_layout.addLayout(grid_nv)
        layout.addWidget(card_nv)

        # Intel Integrated GPU Card
        card_intel = QFrame()
        card_intel.setProperty("class", "ProCard")
        i_layout = QVBoxLayout(card_intel)
        i_layout.setSpacing(8)

        i_box = QHBoxLayout()
        lbl_intel_title = QLabel("Intel Alder Lake-P GT2 [Iris Xe Graphics]")
        lbl_intel_title.setStyleSheet("color: #f8fafc; font-size: 15px; font-weight: 700;")
        lbl_intel_badge = QLabel("INTEGRATED DISPLAY GPU")
        lbl_intel_badge.setStyleSheet("background-color: #1e3a8a; color: #60a5fa; border: 1px solid #60a5fa; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: 800;")
        i_box.addWidget(lbl_intel_title)
        i_box.addWidget(lbl_intel_badge)
        i_box.addStretch()
        i_layout.addLayout(i_box)

        lbl_intel_desc = QLabel("Primary display controller (i915 driver). Seamlessly offloads 3D graphic pipelines to RTX 3050 via PRIME Render Offload.")
        lbl_intel_desc.setStyleSheet("color: #94a3b8; font-size: 12px;")
        i_layout.addWidget(lbl_intel_desc)

        layout.addWidget(card_intel)

        # Esports Display & Refresh Rate Suite
        self.display_suite_gpu = EsportsDisplaySuiteCard()
        self.display_suite_gpu.refresh_rate_changed.connect(self.on_refresh_rate_changed)
        self.display_suite_gpu.overdrive_changed.connect(self.on_overdrive_changed)
        self.display_suite_gpu.smart_ac_dc_toggled.connect(self.on_smart_ac_dc_toggled)
        layout.addWidget(self.display_suite_gpu)

        layout.addStretch()
        return container

    def create_system_view(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 22, 28, 28)
        layout.setSpacing(20)

        lbl = QLabel("DEVICE SPECIFICATIONS & FIRMWARE ARCHITECTURE")
        lbl.setProperty("class", "CardHeader")
        layout.addWidget(lbl)

        card = QFrame()
        card.setProperty("class", "ProCard")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(18)

        def add_spec(label: str, val: str, r: int, c: int):
            v = QVBoxLayout()
            v.setSpacing(3)
            l = QLabel(label)
            l.setStyleSheet("color: #64748b; font-size: 11px; text-transform: uppercase; font-weight: 700;")
            val_lbl = QLabel(val)
            val_lbl.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 700;")
            v.addWidget(l)
            v.addWidget(val_lbl)
            grid.addLayout(v, r, c)

        add_spec("Product Family", self.machine_info.get("family", "IdeaPad Gaming 3 15IAH7"), 0, 0)
        add_spec("Machine Type Model (MTM)", self.machine_info.get("mtm", "82S9"), 0, 1)
        add_spec("System SKU", self.machine_info.get("sku", "LENOVO_MT_82S9"), 0, 2)
        add_spec("BIOS Firmware Version", self.machine_info.get("bios", "JMCN48WW(V3.11)"), 1, 0)
        add_spec("BIOS Release Date", self.machine_info.get("bios_date", "09/06/2024"), 1, 1)
        add_spec("Embedded Controller (EC)", "VPC2004:00 (ideapad_acpi)", 1, 2)
        add_spec("Operating System", "CachyOS Linux x86-64-v3 (Arch Rolling)", 2, 0)
        add_spec("Active Kernel", os.uname().release, 2, 1)
        add_spec("Power Management Engine", "ACPI platform_profile v2 & Slew Governor", 2, 2)

        c_layout.addLayout(grid)
        layout.addWidget(card)

        # 6-Point Hardware Diagnostic Self-Test Suite
        self.diagnostic_card = SystemDiagnosticCard()
        layout.addWidget(self.diagnostic_card)

        layout.addStretch()
        return container

    def create_rgb_view(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 20, 28, 28)
        layout.setSpacing(20)

        self.rgb_studio_card = RgbLightingStudioCard()
        layout.addWidget(self.rgb_studio_card)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def on_conservation_toggled(self, enabled: bool):
        LenovoHardware.set_conservation_mode(enabled)
        self.pill_cons.setText("🔋 CONSERVATION ON (75-80%)" if enabled else "🔋 FULL CHARGE 100%")
        self.pill_cons.setStyleSheet("background-color: #064e3b; color: #10b981;" if enabled else "background-color: #162032; color: #94a3b8;")

    def handle_hotkey_refresh_rate(self):
        new_hz = 60 if self.current_refresh_hz == 165 else 165
        self.on_refresh_rate_changed(new_hz)

    def handle_hotkey_fan_mode(self):
        fstatus = LenovoHardware.get_fan_cooling_status()
        current_mode = fstatus.get("active_mode", "standard")
        cycle_map = {"silent": "standard", "standard": "extreme", "extreme": "silent"}
        next_mode = cycle_map.get(current_mode, "standard")
        self.set_fan_cooling_mode(next_mode)

    def handle_firmware_profile_changed(self, profile: str):
        mode_map = {"quiet": "silent", "balanced": "standard", "performance": "extreme"}
        target_mode = mode_map.get(profile.strip(), "standard")
        self.set_fan_cooling_mode(target_mode)

    def on_game_started(self, pid: int, name: str):
        self.osd.notify_game_mode(True, name)
        self.update_telemetry()

    def on_game_stopped(self, name: str):
        self.osd.notify_game_mode(False, name)
        self.update_telemetry()

    def on_no_turbo_toggled(self, enabled: bool):
        LenovoHardware.set_no_turbo(enabled)
        self.osd.notify_no_turbo(enabled)
        self.update_telemetry()

    def on_auto_game_mode_toggled(self, enabled: bool):
        self.game_detector.set_auto_profile_enabled(enabled)
        self.update_telemetry()

    def on_start_dust_purge(self):
        LenovoHardware.start_dust_purge()
        self.osd.notify_dust_purge()
        self.update_telemetry()

    def on_cancel_dust_purge(self):
        LenovoHardware.cancel_dust_purge()
        self.update_telemetry()

    def on_refresh_rate_changed(self, hz: int):
        self.current_refresh_hz = hz
        LenovoDisplayManager.set_refresh_rate(hz)
        self.osd.notify_refresh_rate(hz)
        self.update_telemetry()

    def on_overdrive_changed(self, level: int):
        self.current_overdrive = level
        LenovoDisplayManager.set_screen_overdrive(level)
        self.update_telemetry()

    def on_smart_ac_dc_toggled(self, enabled: bool):
        self.smart_ac_dc_enabled = enabled
        self.check_smart_ac_dc()
        self.update_telemetry()

    def check_smart_ac_dc(self):
        if not self.smart_ac_dc_enabled:
            return
        bat = LenovoHardware.get_battery_info()
        is_ac = "charging" in bat["status"].lower() or bat["status"] == "Not charging"
        if is_ac and self.current_refresh_hz != 165:
            self.on_refresh_rate_changed(165)
        elif not is_ac and self.current_refresh_hz != 60:
            self.on_refresh_rate_changed(60)

    def set_fan_cooling_mode(self, mode: str):
        LenovoHardware.set_fan_cooling_mode(mode)
        self.osd.notify_mode(mode)
        self.update_telemetry()

    def update_telemetry(self):
        # 1. Sync Fan Telemetry & Cooling Dynamics
        fstatus = LenovoHardware.get_fan_cooling_status()
        self.fan_panel.update_telemetry(fstatus)
        if hasattr(self, 'purge_cockpit'):
            self.purge_cockpit.update_purge_telemetry(fstatus)

        est_rpm = fstatus.get("estimated_rpm", 0)
        cur_lvl = fstatus.get("current_level", 0)
        cpu_temp = fstatus.get("cpu_temp", 0.0)
        gpu_temp = fstatus.get("gpu_temp", 0.0)

        # Real-time Dual Turbines update
        self.cpu_turbine.set_status(rpm=est_rpm, temp=cpu_temp, level=cur_lvl)
        self.gpu_turbine.set_status(rpm=est_rpm, temp=gpu_temp, level=cur_lvl)

        # Mode status pill
        is_purge = fstatus.get("purge_active", False)
        if is_purge:
            cycle = fstatus.get("purge_cycle", 1)
            rem = fstatus.get("purge_remaining_s", 30)
            self.active_mode_pill.setText(f"🌪️ PURGE DEBU ({cycle}/5 • {rem}s)")
            self.active_mode_pill.setStyleSheet("background-color: #2a1147; color: #c084fc; border: 1px solid #c084fc; border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 800;")
        else:
            active_mode = fstatus.get("active_mode", "standard")
            if active_mode == "extreme":
                self.active_mode_pill.setText("🚀 EXTREME (100% TURBIN)")
                self.active_mode_pill.setStyleSheet("background-color: #241014; color: #ef4444; border: 1px solid #ef4444; border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 800;")
            elif active_mode == "silent":
                self.active_mode_pill.setText("🍃 SILENT (WHISPER FLOW)")
                self.active_mode_pill.setStyleSheet("background-color: #0a1e30; color: #06b6d4; border: 1px solid #06b6d4; border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 800;")
            else:
                self.active_mode_pill.setText("⚖️ STANDARD (S-CURVE DYNAMIC)")
                self.active_mode_pill.setStyleSheet("background-color: #172033; color: #38bdf8; border: 1px solid #38bdf8; border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 800;")

        # Smart AC/DC Display Rate Check & Update
        self.check_smart_ac_dc()
        disp_info = LenovoDisplayManager.get_display_info()
        self.current_refresh_hz = disp_info.get("current_hz", 165)
        self.current_overdrive = LenovoDisplayManager.get_screen_overdrive()
        if hasattr(self, 'display_suite_dash'):
            self.display_suite_dash.set_display_state(self.current_refresh_hz, self.current_overdrive, self.smart_ac_dc_enabled)
        if hasattr(self, 'display_suite_gpu'):
            self.display_suite_gpu.set_display_state(self.current_refresh_hz, self.current_overdrive, self.smart_ac_dc_enabled)

        # 2. CPU Telemetry & RAPL/EPP
        cpu = LenovoHardware.get_cpu_telemetry()
        self.meter_cpu_temp.set_value(cpu["temp_c"], subtitle=f"{cpu['freq_mhz']} MHz")
        self.meter_cpu_load.set_value(cpu["load_pct"], subtitle=f"{cpu['cores']} Cores")
        self.lbl_cpu_stat.setText(f"{cpu['temp_c']}°C • {cpu['load_pct']}% Load ({cpu['cores']} Cores @ {cpu['freq_mhz']} MHz)")

        cooling = LenovoHardware.get_cooling_telemetry()
        pl1 = cooling.get("pl1_w", 45.0)
        pl2 = cooling.get("pl2_w", 65.0)
        epp = cooling.get("epp", "balance_power")
        self.lbl_rapl_stat.setText(f"PL1: {pl1}W | PL2: {pl2}W | EPP: {epp}")

        # Intel Alder Lake Scheduler Card State
        if hasattr(self, 'scheduler_card'):
            no_turbo = LenovoHardware.get_no_turbo()
            auto_game = self.game_detector.auto_profile_enabled
            active_game = self.game_detector.active_game_name or ""
            self.scheduler_card.set_scheduler_state(no_turbo, auto_game, active_game)

        # 3. GPU Telemetry
        gpu = LenovoHardware.get_gpu_telemetry()
        if gpu["available"]:
            self.meter_gpu_temp.set_value(gpu["temp_c"], subtitle=f"Core {gpu['load_pct']}%")
            self.lbl_nv_temp.setText(f"{gpu['temp_c']} °C")
            self.lbl_nv_load.setText(f"{gpu['load_pct']} %")
            self.lbl_nv_vram.setText(f"{gpu['vram_used_mb']} / {gpu['vram_total_mb']} MB ({gpu['vram_pct']}%)")
            self.lbl_nv_driver.setText(gpu["driver"])
            self.lbl_gpu_stat.setText(f"{gpu['temp_c']}°C • {gpu['load_pct']}% Utilization")
            self.lbl_vram_stat.setText(f"VRAM: {gpu['vram_used_mb']} / {gpu['vram_total_mb']} MB ({gpu['vram_pct']}%) • Driver {gpu['driver']}")
            self.pill_gpu.setText("🎮 RTX 3050 ACTIVE")
            self.pill_gpu.setStyleSheet("background-color: #064e3b; color: #10b981;")
        else:
            self.meter_gpu_temp.set_value(0, subtitle="Sleep")
            self.lbl_gpu_stat.setText("RTX 3050 in Dynamic D3 Cold Sleep")
            self.lbl_vram_stat.setText("PCIe Bus Suspended • 0W Draw")
            self.pill_gpu.setText("🎮 RTX 3050 SLEEP")
            self.pill_gpu.setStyleSheet("background-color: #162032; color: #94a3b8;")

        # 4. RAM Telemetry
        ram = LenovoHardware.get_ram_telemetry()
        self.meter_ram.set_value(ram["pct"], subtitle=f"{ram['used_gb']}G / {ram['total_gb']}G")
        self.lbl_ram_stat.setText(f"{ram['used_gb']} GB / {ram['total_gb']} GB ({ram['pct']}%)")

        # 5. Battery Telemetry
        bat = LenovoHardware.get_battery_info()
        self.meter_battery_main.set_value(bat["capacity"], subtitle=bat["status"])
        self.bat_cap_label.setText(f"{bat['capacity']}% Battery Charge")
        self.bat_status_label.setText(f"Status: {bat['status']} ({bat['power_draw_w']}W Draw)")
        self.bat_health_badge.setText(f"Health Rating: {bat['health_pct']}% ({bat['cycle_count']} discharge cycles)")

        self.lbl_bat_health.setText(f"{bat['health_pct']}%")
        self.lbl_bat_cycles.setText(f"{bat['cycle_count']} cycles")
        self.lbl_bat_full_energy.setText(f"{bat['energy_full_wh']} Wh")
        self.lbl_bat_design_energy.setText(f"{bat['energy_design_wh']} Wh")
        self.lbl_bat_model.setText(bat["model"])
        self.lbl_bat_mfg.setText(bat["vendor"])

        draw_txt = f"({bat['power_draw_w']}W)" if bat['power_draw_w'] > 0 else ""
        self.lbl_bat_stat.setText(f"{bat['capacity']}% • {bat['status']} {draw_txt}")
        self.lbl_health_stat.setText(f"Health: {bat['health_pct']}% • {bat['cycle_count']} Cycles ({bat['vendor']} {bat['model']})")

        # AC Pill
        if "charging" in bat["status"].lower() or bat["status"] == "Not charging":
            self.pill_ac.setText("⚡ AC ADAPTER CONNECTED")
            self.pill_ac.setStyleSheet("background-color: #1e3a8a; color: #60a5fa;")
        else:
            self.pill_ac.setText("🔋 ON BATTERY POWER")
            self.pill_ac.setStyleSheet("background-color: #162032; color: #94a3b8;")

        # Conservation Pill
        cons_on = LenovoHardware.get_conservation_mode()
        if cons_on:
            self.pill_cons.setText("🔋 CONSERVATION ON (75-80%)")
            self.pill_cons.setStyleSheet("background-color: #064e3b; color: #10b981;")
        else:
            self.pill_cons.setText("🔋 FULL CHARGE 100%")
            self.pill_cons.setStyleSheet("background-color: #162032; color: #94a3b8;")

        # Feed telemetry sample to Blackbox Flight Recorder if active
        if hasattr(self, 'blackbox_card') and hasattr(self.blackbox_card, 'recorder'):
            if self.blackbox_card.recorder._active:
                sample = {
                    "cpu_temp": cpu.get("temp_c", 0.0),
                    "cpu_load": cpu.get("load_pct", 0.0),
                    "cpu_freq_mhz": cpu.get("freq_mhz", 0),
                    "gpu_temp": gpu.get("temp_c", 0.0),
                    "gpu_load": gpu.get("load_pct", 0.0),
                    "gpu_vram_pct": gpu.get("vram_pct", 0.0),
                    "fan_level": cur_lvl,
                    "estimated_rpm": est_rpm,
                    "battery_pct": bat.get("capacity", 0),
                    "battery_draw_w": bat.get("power_draw_w", 0.0),
                    "refresh_hz": self.current_refresh_hz,
                    "no_turbo": 1 if LenovoHardware.get_no_turbo() else 0,
                }
                self.blackbox_card.recorder.record_sample(sample)

    def setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray = QSystemTrayIcon(self)
        if os.path.exists(ICON_PATH):
            self.tray.setIcon(QIcon(ICON_PATH))

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0a0f1d;
                color: #f8fafc;
                border: 1px solid #1a2638;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 7px 22px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #16243d;
                color: #38bdf8;
            }
            QMenu::separator {
                height: 1px;
                background-color: #1a2638;
                margin: 4px 8px;
            }
        """)

        act_show = QAction("Open Lenovo Vantage Pro", self)
        act_show.triggered.connect(self.show_and_raise)
        menu.addAction(act_show)
        menu.addSeparator()

        act_silent = QAction("🍃 Silent Mode (Whisper Flow)", self)
        act_silent.triggered.connect(lambda: self.set_fan_cooling_mode("silent"))
        menu.addAction(act_silent)

        act_bal = QAction("⚖️ Standard Mode (Dynamic S-Curve)", self)
        act_bal.triggered.connect(lambda: self.set_fan_cooling_mode("standard"))
        menu.addAction(act_bal)

        act_perf = QAction("🚀 Extreme Mode (100% Full Speed)", self)
        act_perf.triggered.connect(lambda: self.set_fan_cooling_mode("extreme"))
        menu.addAction(act_perf)

        act_dust = QAction("🌪️ Dust Cleaner (30s Pulsation)", self)
        act_dust.triggered.connect(self.on_start_dust_purge)
        menu.addAction(act_dust)

        menu.addSeparator()
        act_cons = QAction("Toggle Battery Conservation (75-80%)", self)
        act_cons.triggered.connect(self.toggle_conservation_from_tray)
        menu.addAction(act_cons)

        menu.addSeparator()
        act_quit = QAction("Quit Vantage Pro", self)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_and_raise()

    def toggle_conservation_from_tray(self):
        cur = LenovoHardware.get_conservation_mode()
        LenovoHardware.set_conservation_mode(not cur)
        self.sw_conservation.setChecked(not cur)

    def closeEvent(self, event):
        if QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
            self.tray.showMessage(
                "Lenovo Vantage Pro",
                "Minimized to system tray. Right-click icon for instant mode toggles.",
                QSystemTrayIcon.MessageIcon.Information,
                1500
            )
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(PRO_MAX_THEME)
    window = LenovoVantageApp()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
