"""
Lenovo Vantage Pro - Internationalization (i18n) Engine
Supports dynamic real-time switching between English (EN) and Bahasa Indonesia (ID).
Persists language selection across reboots in ~/.config/lenovo-vantage/config.json.
"""

import os
import json
from typing import Dict, Any, Callable, List
from PyQt6.QtCore import QObject, pyqtSignal

CONFIG_DIR = os.path.expanduser("~/.config/lenovo-vantage")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # App & Header
        "app_title": "Lenovo Vantage Pro — Hardware Control Center",
        "brand_title": "LENOVO",
        "brand_subtitle": "VANTAGE PRO",
        "header_title": "LENOVO VANTAGE PRO",
        "header_meta": "Model: {model}  •  BIOS: {bios}",
        "system_optimal": "● SYSTEM OPTIMAL",
        "active_mode_silent": "🍃 SILENT MODE",
        "active_mode_standard": "⚖️ STANDARD MODE",
        "active_mode_extreme": "🚀 EXTREME MODE",
        "active_mode_silent_full": "🍃 SILENT (WHISPER FLOW)",
        "active_mode_standard_full": "⚖️ STANDARD (S-CURVE DYNAMIC)",
        "active_mode_extreme_full": "🚀 EXTREME (100% TURBINE)",
        "purge_pill": "🌪️ DUST PURGE ({cycle}/5 • {rem}s)",

        # Navigation
        "nav_dashboard": "  Dashboard",
        "nav_battery": "  Power & Battery",
        "nav_gpu": "  GPU & Display",
        "nav_rgb": "  RGB Lighting Studio",
        "nav_diagnostics": "  Device Specs & Diagnostics",

        # Dashboard - Cooling Dynamics
        "cooling_dynamics_title": "DUAL TURBINE THERMAL DYNAMICS",
        "cooling_dynamics_sub": "DIRECT MMIO REGISTER CONTROL & GRADUAL SLEW STABILIZATION",
        "cpu_turbine": "CPU TURBINE",
        "gpu_turbine": "GPU TURBINE",
        "acoustic_trajectory_title": "REAL-TIME ACOUSTIC & THERMAL TRAJECTORY (S-CURVE DYNAMICS)",

        # Fan Modes
        "fan_silent_title": "🍃 SILENT",
        "fan_silent_sub": "Whisper Flow (Passive Cooling)",
        "fan_standard_title": "⚖️ STANDARD",
        "fan_standard_sub": "S-Curve Dynamic (Step-Free Curve)",
        "fan_extreme_title": "🚀 EXTREME",
        "fan_extreme_sub": "100% Full Turbine (Max Thermal Headroom)",

        # Maintenance Purge & Dust Cleaner
        "purge_title": "HARDWARE PURGE & DUST CLEANER",
        "purge_badge": "ACOUSTIC SHOCKWAVE MAINTENANCE",
        "purge_desc": "Ejects micro-dust from copper fins through extreme angular acceleration cycles (3.5s 100% Blast ↔ 2.5s Drop Level 1, 5 Rounds).",
        "purge_start_btn": "Start Dust Cleaner (30s)",
        "purge_cancel_btn": "Stop Purge",
        "purge_idle": "Status: IDLE",
        "purge_blast": "Status: ROUND {cycle}/5 - STORM BLAST 100% (~5,200 RPM)",
        "purge_rest": "Status: ROUND {cycle}/5 - REST STEP (~1,200 RPM)",
        "purge_done": "Status: COMPLETED (30s Cycle Done)",
        "purge_sec_remaining": "{sec}s remaining",

        "display_suite_title": "ESPORTS DISPLAY & OVERDRIVE SUITE",
        "refresh_rate_title": "PANEL REFRESH RATE LOCK (KWIN WAYLAND)",
        "btn_165hz": "⚡ 165.01 Hz Esports",
        "btn_120hz": "🚀 120.00 Hz Pro Gaming",
        "btn_90hz": "⚖️ 90.00 Hz Fluid Dynamic",
        "btn_60hz": "🍃 59.96 Hz Power Saver",
        "osd_120hz_title": "120.00 HZ PRO GAMING LOCK",
        "osd_120hz_sub": "Pro Esports Precision • 120 FPS High Fluidity",
        "osd_90hz_title": "90.00 HZ DYNAMIC FLUID LOCK",
        "osd_90hz_sub": "Balanced Smoothness • Power Optimized",
        "overdrive_title": "SCREEN OVERDRIVE (ODV2 FAST GTG)",
        "od_off": "Off",
        "od_normal": "Normal",
        "od_extreme": "Extreme (Fast GtG)",
        "smart_ac_dc_title": "SMART AC/DC AUTO-SWITCH",
        "smart_ac_dc_desc": "Automatically switch to 60Hz on Battery, 165Hz on AC Adapter",

        # Intel Alder Lake Scheduler
        "scheduler_title": "INTEL ALDER LAKE CORE SCHEDULER & OPTIMIZER",
        "pcore_pinning_title": "P-CORE GAME THREAD PINNING (TASKSET CPU 0-7)",
        "pcore_pinning_desc": "Pins main game threads to 4 Golden Cove P-Cores to eliminate micro-stuttering in Linux.",
        "pcore_status_idle": "STATUS: IDLE (NO GAME DETECTED)",
        "pcore_status_active": "STATUS: GAMING (P-CORES PINNED: {name})",
        "no_turbo_title": "No-Turbo Silent Cooling",
        "no_turbo_desc": "Disables clock boost to keep CPU cool (<45°C) without fan noise during light gaming/emulation.",
        "auto_game_title": "Auto-Game Mode Profile",
        "auto_game_desc": "Automatically switches to 165Hz, Extreme Fan, and OverDrive when game launches.",

        # Hardware Quick Switches & Telemetry
        "card_conservation_title": "Battery Conservation",
        "card_conservation_sub": "Caps charge at 75-80% to prolong battery lifespan.",
        "pill_cons_on": "🔋 CONSERVATION ON (75-80%)",
        "pill_cons_off": "🔋 FULL CHARGE 100%",
        "card_rapid_charge_title": "Rapid Charge",
        "card_rapid_charge_sub": "Accelerates battery charging up to 80% in 30 minutes.",
        "card_fn_lock_title": "Fn-Lock",
        "card_fn_lock_sub": "Prioritizes F1-F12 standard function keys.",
        "card_touchpad_title": "Touchpad Lock",
        "card_touchpad_sub": "Disables internal touchpad during gaming sessions.",
        "telemetry_cpu_title": "CPU METRICS & POWER",
        "telemetry_gpu_title": "RTX 3050 DEDICATED GPU",
        "telemetry_ram_title": "SYSTEM MEMORY & SWAP",
        "telemetry_bat_title": "BATTERY & CHARGING HEALTH",
        "battery_charge_prefix": "Charge",
        "battery_cycles_prefix": "Cycles",
        "battery_health_prefix": "Health",

        # Device Specifications
        "specs_header": "DEVICE SPECIFICATIONS & FIRMWARE ARCHITECTURE",
        "spec_family": "Product Family",
        "spec_mtm": "Machine Type Model (MTM)",
        "spec_sku": "System SKU",
        "spec_bios": "BIOS Firmware Version",
        "spec_bios_date": "BIOS Release Date",
        "spec_ec": "Embedded Controller (EC)",
        "spec_os": "Operating System",
        "spec_kernel": "Active Kernel",
        "spec_power_engine": "Power Management Engine",

        # RGB Lighting Studio & 5-Slot Profile Architecture
        "rgb_title": "4-ZONE RGB LIGHTING STUDIO",
        "rgb_controller_badge": "ITE 8295 HARDWARE CONTROLLER",
        "rgb_slots_header": "5-SLOT CYCLIC PROFILES (FN + SPACE)",
        "rgb_slot_label": "SLOT {num}",
        "rgb_slot_active_badge": "ACTIVE PROFILE",
        "rgb_cycle_btn": "Cycle Profile (Fn + Space)",
        "rgb_save_slot_btn": "Save Customization to Slot {num}",
        "rgb_owner_title": "LIGHT CONTROL OWNERSHIP",
        "rgb_owner_app": "Vantage Pro Studio (5 Customizable Slots + OSD)",
        "rgb_owner_bios": "ITE Hardware Standalone (Factory ROM Effects)",
        "rgb_visual_topology": "VISUAL KEYBOARD TOPOLOGY (4-ZONE ILLUMINATION)",
        "rgb_zone_1_name": "ZONE 1",
        "rgb_zone_2_name": "ZONE 2",
        "rgb_zone_3_name": "ZONE 3",
        "rgb_zone_4_name": "ZONE 4",
        "rgb_zone_1_keys": "WASD / Left",
        "rgb_zone_2_keys": "Center Left",
        "rgb_zone_3_keys": "Center Right",
        "rgb_zone_4_keys": "Numpad / Right",
        "rgb_presets_title": "QUICK LIGHTING PRESETS",
        "rgb_preset_vantage_cyan": "💎 Vantage Cyan",
        "rgb_preset_cyber_neon": "⚡ Cyber Neon",
        "rgb_preset_crimson_fury": "🔥 Crimson Fury",
        "rgb_preset_emerald_stealth": "🍃 Emerald Stealth",
        "rgb_preset_smooth_wave": "🌊 Smooth Wave",
        "rgb_preset_off": "🌙 Off",
        "rgb_brightness_title": "BRIGHTNESS",
        "rgb_speed_title": "EFFECT SPEED",
        "rgb_pattern_title": "LIGHTING PATTERN",
        "rgb_palette_title": "QUICK COLOR PALETTE & ZONE ASSIGNMENT",
        "rgb_apply_single_active": "Apply to: SELECTED ZONE (Click for All)",
        "rgb_apply_all_active": "Apply to: ALL ZONES (Click for Single)",
        "rgb_pick_color": "Pick Color...",
        "rgb_selected": "SELECTED",
        "rgb_off": "Off",
        "rgb_low": "Low (50%)",
        "rgb_high": "High (100%)",
        "rgb_eff_static": "Static",
        "rgb_eff_breathing": "Breathing",
        "rgb_eff_smooth_wave": "Smooth Wave",
        "rgb_eff_wave": "Wave",
        "rgb_sync_perf_title": "SYNC RGB WITH CPU PERFORMANCE MODE",
        "rgb_sync_perf_sub": "Automatically switch keyboard lighting profile (Extreme: Crimson Fury, Standard: Vantage Cyan, Silent: Off) when performance mode changes (Fn + Q).",
        "rgb_sync_perf_active": "SYNC ACTIVE (AUTO)",
        "rgb_sync_perf_disabled": "SYNC OFF (MANUAL ONLY)",
        "tray_cycle_rgb": "Cycle RGB Profile (Fn + Space)",
        "tray_cycle_brightness": "Cycle Keyboard Brightness (Off / 50% / 100%)",
        "osd_rgb_title": "KEYBOARD RGB PROFILE",
        "osd_rgb_off_sub": "BACKLIGHT OFF • 0% BRIGHTNESS",
        "osd_brightness_title": "KEYBOARD BACKLIGHT",
        "osd_brightness_off": "0% • BACKLIGHT OFF",
        "osd_brightness_low": "50% • LOW BRIGHTNESS",
        "osd_brightness_high": "100% • HIGH BRIGHTNESS",

        # Gaming Tools: Wi-Fi, Blackbox, Diagnostics
        "wifi_title": "ESPORTS WI-FI LOW-LATENCY STABILIZER",
        "wifi_sub": "WLAN0 SUB-MILLISECOND JITTER SUPPRESSION & MICRO-SLEEP BYPASS",
        "wifi_anti_jitter_btn": "Esports Anti-Jitter Lock (0ms Sleep)",
        "wifi_unlock_btn": "Unlock Anti-Jitter (Enable Power Save)",
        "wifi_explanation": "Disabling Wi-Fi power-save eliminates latency spikes during competitive gaming.",
        "wifi_ps_on": "● POWER SAVE: ON",
        "wifi_ps_locked": "● ESPORTS ANTI-JITTER LOCK (0ms SLEEP)",
        "wifi_gateway_title": "GATEWAY ROUND-TRIP",
        "wifi_measuring": "Measuring latency...",
        "wifi_chip_ssid": "Connected SSID",
        "wifi_chip_ch": "Channel / Freq",
        "wifi_chip_tx": "TX Power",
        "wifi_chip_gw": "Default Gateway",
        "wifi_ping_optimal": "Minimal Jitter • Optimal Esports Performance",
        "wifi_ping_stable": "Stable Connection • Ready to Play",
        "wifi_ping_high": "High Latency Detected",
        "wifi_ping_fail": "Gateway Unresponsive",

        "blackbox_title": "BLACKBOX TELEMETRY FLIGHT RECORDER",
        "blackbox_sub": "HIGH-RESOLUTION 1 Hz HARDWARE CHRONICLE & THERMAL CRUISE LOG",
        "blackbox_session_name": "Session Name:",
        "blackbox_start_btn": "Start Flight Recording",
        "blackbox_stop_btn": "Stop Recording",
        "blackbox_open_btn": "Open Sessions Folder",
        "blackbox_status_idle": "● RECORDER STANDBY",
        "blackbox_status_active": "● RECORDING LIVE FLIGHT",
        "blackbox_recording_pill": "● RECORDING TELEMETRY",
        "blackbox_saved_pill": "● SESSION SAVED",
        "blackbox_metric_duration": "SESSION DURATION",
        "blackbox_metric_samples": "TOTAL SAMPLES (1 HZ)",
        "blackbox_metric_peak_cpu": "PEAK CPU TEMP",
        "blackbox_metric_peak_gpu": "PEAK GPU TEMP",
        "blackbox_metric_max_fan": "MAX FAN RPM",
        "blackbox_storage_prefix": "Storage: {path}",
        "blackbox_file_active": "Active File: {path}",
        "blackbox_file_saved": "Saved: {path}",
        "blackbox_samples_suffix": "{samples} Samples",

        "diag_title": "SYSTEM HARDWARE DIAGNOSTIC SUITE",
        "diag_sub": "6-POINT AUTOMATED ARCHITECTURE & BUS INTEGRITY VERIFICATION",
        "diag_run_btn": "Run System Diagnostic (6 Checks)",
        "diag_running": "Running System Tests...",
        "diag_complete": "Diagnostic Completed Successfully",
        "diag_starting": "Starting 6 hardware subsystem audits...",
        "diag_test_progress": "Testing {current}/{total}: {msg}",
        "diag_status_passed": "● SYSTEM STATUS OPTIMAL: ALL {passed}/{total} SUBSYSTEMS PASSED",
        "diag_status_warning": "● SYSTEM OPERATIONAL WITH NOTICES: {passed}/{total} PASSED, WARNINGS PRESENT",
        "diag_status_failed": "● HARDWARE ATTENTION NEEDED: SUBSYSTEM FAILURE DETECTED",
        "diag_test_duration": "Test Duration: {dur} ms",
        "diag_test1_title": "Battery Health & SBS Chipset",
        "diag_test1_desc": "Capacity, charge cycle count, and ACPI MHCF flash block status.",
        "diag_test2_title": "Dual Turbine Cooling & MMIO Control",
        "diag_test2_desc": "Direct MMIO register 0xAB/0xAD and dual fan turbine RPM.",
        "diag_test3_title": "Intel Alder Lake Heterogeneous Topology",
        "diag_test3_desc": "P-Cores 0-7, E-Cores 8-15, and intel_pstate no_turbo interface.",
        "diag_test4_title": "Esports Display Bus & ACPI Screen OverDrive",
        "diag_test4_desc": "KWin Wayland 165Hz/60Hz modes and ACPI SSFM ODV2 register.",
        "diag_test5_title": "NVIDIA RTX 3050 PCIe Bus & Driver",
        "diag_test5_desc": "Official driver, 4GB VRAM, and dynamic PCIe D3 Cold state.",
        "diag_test6_title": "Wi-Fi Low-Latency Subsystem",
        "diag_test6_desc": "wlan0 round-trip ping latency to gateway and 0ms micro-sleep lock.",

        # Tray Menu
        "tray_open": "Open Lenovo Vantage Pro",
        "tray_thermal": "Thermal Profile",
        "tray_silent": "🍃 Silent Mode (Whisper Flow)",
        "tray_standard": "⚖️ Standard Mode (Dynamic S-Curve)",
        "tray_extreme": "🚀 Extreme Mode (100% Full Speed)",
        "tray_dust": "🌪️ Dust Cleaner (30s Pulsation)",
        "tray_cons": "Toggle Battery Conservation (75-80%)",
        "tray_refresh": "Display Refresh Rate",
        "tray_language": "Language / Bahasa",
        "tray_lang_en": "English [EN]",
        "tray_lang_id": "Bahasa Indonesia [ID]",
        "tray_quit": "Quit",

        # OSD Notifications
        "osd_perf_title": "PERFORMANCE MODE",
        "osd_perf_sub": "100% Full Turbine • 85W TGP Unlocked",
        "osd_std_title": "STANDARD BALANCED",
        "osd_std_sub": "Intelligent Dynamic S-Curve Flow",
        "osd_silent_title": "QUIET SILENT FLOW",
        "osd_silent_sub": "Whisper Quiet Acoustic Profile",
        "osd_165hz_title": "165.01 HZ ESPORTS LOCK",
        "osd_165hz_sub": "KWin Wayland Ultra-Fluid High Refresh Rate",
        "osd_60hz_title": "59.96 HZ POWER SAVER",
        "osd_60hz_sub": "Energy Efficient Battery Lock",
        "osd_purge_title": "DUST PURGE STARTED",
        "osd_purge_sub": "30s Acoustic Shockwave Cycle Active",
        "osd_game_start_title": "GAME MODE ENGAGED",
        "osd_game_start_sub": "P-Core Thread Pinning Active: {name}",
        "osd_game_stop_title": "GAME SESSION ENDED",
        "osd_game_stop_sub": "Hardware Restored to Standard Profile",
        "osd_noturbo_on_title": "NO-TURBO SILENT ACTIVE",
        "osd_noturbo_on_sub": "CPU Boost Disabled for Cool Acoustics",
        "osd_noturbo_off_title": "TURBO BOOST RESTORED",
        "osd_noturbo_off_sub": "Full High-Clock Performance Unlocked",
    },
    "id": {
        # App & Header
        "app_title": "Lenovo Vantage Pro — Pusat Kontrol Perangkat Keras",
        "brand_title": "LENOVO",
        "brand_subtitle": "VANTAGE PRO",
        "header_title": "LENOVO VANTAGE PRO",
        "header_meta": "Model: {model}  •  BIOS: {bios}",
        "system_optimal": "● SISTEM OPTIMAL",
        "active_mode_silent": "🍃 MODE SENYAP",
        "active_mode_standard": "⚖️ MODE STANDAR",
        "active_mode_extreme": "🚀 MODE EKSTREM",
        "active_mode_silent_full": "🍃 SENYAP (WHISPER FLOW)",
        "active_mode_standard_full": "⚖️ STANDAR (KURVA-S DINAMIS)",
        "active_mode_extreme_full": "🚀 EKSTREM (100% TURBIN)",
        "purge_pill": "🌪️ PURGE DEBU ({cycle}/5 • {rem}s)",

        # Navigation
        "nav_dashboard": "  Dasbor",
        "nav_battery": "  Daya & Baterai",
        "nav_gpu": "  GPU & Layar",
        "nav_rgb": "  Studio Lampu RGB",
        "nav_diagnostics": "  Spesifikasi & Diagnostik",

        # Dashboard - Cooling Dynamics
        "cooling_dynamics_title": "DINAMIKA TERMAL DUAL TURBIN",
        "cooling_dynamics_sub": "KONTROL REGISTER LANGSUNG MMIO & STABILISASI SLEW BERTAHAP",
        "cpu_turbine": "TURBIN CPU",
        "gpu_turbine": "TURBIN GPU",
        "acoustic_trajectory_title": "TRAJEKTORI AKUSTIK & TERMAL REAL-TIME (DINAMIKA KURVA-S)",

        # Fan Modes
        "fan_silent_title": "🍃 SENYAP",
        "fan_silent_sub": "Whisper Flow (Putar Pelan & Senyap)",
        "fan_standard_title": "⚖️ STANDAR",
        "fan_standard_sub": "Kurva-S Dinamis (Kenaikan Bertahap)",
        "fan_extreme_title": "🚀 EKSTREM",
        "fan_extreme_sub": "100% Turbin Penuh (Pendinginan Maksimal)",

        # Maintenance Purge & Dust Cleaner
        "purge_title": "HARDWARE PURGE & PEMBERSIH DEBU",
        "purge_badge": "PERAWATAN GELOMBANG KEJUT AKUSTIK",
        "purge_desc": "Melontarkan debu mikro dari celah heatsink tembaga melalui siklus percepatan sudut ekstrem (3.5s Tiup 100% ↔ 2.5s Drop Level 1, 5 Ronde).",
        "purge_start_btn": "Mulai Pembersihan Debu (30s)",
        "purge_cancel_btn": "Hentikan Pembersihan",
        "purge_idle": "Status: SIAGA",
        "purge_blast": "Status: RONDE {cycle}/5 - TIUP BADAI 100% (~5,200 RPM)",
        "purge_rest": "Status: RONDE {cycle}/5 - FASE JEDA (~1,200 RPM)",
        "purge_done": "Status: SELESAI (Siklus 30s Berakhir)",
        "purge_sec_remaining": "{sec}d tersisa",

        # Esports Display & OverDrive Suite
        "display_suite_title": "SUITE TAMPILAN ESPORTS & OVERDRIVE",
        "refresh_rate_title": "PENGUNCI REFRESH RATE PANEL (KWIN WAYLAND)",
        "btn_165hz": "⚡ 165.01 Hz Kunci Esports",
        "btn_120hz": "🚀 120.00 Hz Pro Gaming",
        "btn_90hz": "⚖️ 90.00 Hz Dinamis Seimbang",
        "btn_60hz": "🍃 59.96 Hz Hemat Daya",
        "osd_120hz_title": "KUNCI 120.00 HZ PRO GAMING",
        "osd_120hz_sub": "Presisi Esports Pro • 120 FPS Sangat Mulus",
        "osd_90hz_title": "KUNCI 90.00 HZ DINAMIS SEIMBANG",
        "osd_90hz_sub": "Transisi Halus Seimbang • Hemat Daya Baterai",
        "overdrive_title": "OVERDRIVE LAYAR (ODV2 FAST GTG)",
        "od_off": "Mati",
        "od_normal": "Normal",
        "od_extreme": "Ekstrem (Fast GtG)",
        "smart_ac_dc_title": "PERALIHAN CERDAS AC/DC",
        "smart_ac_dc_desc": "Otomatis beralih ke 60Hz saat Baterai, 165Hz saat Tercolok Charger",

        # Intel Alder Lake Scheduler
        "scheduler_title": "PENJADWAL & PENGOPTIMAL INTEL ALDER LAKE",
        "pcore_pinning_title": "PENGUNCIAN THREAD GAME KE P-CORE (TASKSET CPU 0-7)",
        "pcore_pinning_desc": "Mengunci thread game utama pada 4 Performance Cores (CPU 0–7) untuk menghilangkan micro-stuttering di Linux.",
        "pcore_status_idle": "STATUS: SIAGA (TIDAK ADA GAME)",
        "pcore_status_active": "STATUS: GAMING (P-CORE TERKUNCI: {name})",
        "no_turbo_title": "Pendinginan Senyap No-Turbo",
        "no_turbo_desc": "Menonaktifkan clock boost untuk menjaga CPU dingin (<45°C) tanpa desah kipas saat emulasi/game ringan.",
        "auto_game_title": "Profil Mode Game Otomatis",
        "auto_game_desc": "Otomatis beralih ke 165Hz, Kipas Ekstrem, dan OverDrive saat game Steam/Proton terbuka.",

        # Hardware Quick Switches & Telemetry
        "card_conservation_title": "Konservasi Baterai",
        "card_conservation_sub": "Membatasi pengisian di 75-80% untuk memperpanjang usia baterai.",
        "pill_cons_on": "🔋 KONSERVASI AKTIF (75-80%)",
        "pill_cons_off": "🔋 PENGISIAN PENUH 100%",
        "card_rapid_charge_title": "Pengisian Cepat (Rapid Charge)",
        "card_rapid_charge_sub": "Mempercepat pengisian daya baterai hingga 80% dalam 30 menit.",
        "card_fn_lock_title": "Kunci Fn (Fn-Lock)",
        "card_fn_lock_sub": "Mengutamakan fungsi standar tombol F1-F12.",
        "card_touchpad_title": "Kunci Touchpad",
        "card_touchpad_sub": "Menonaktifkan touchpad internal saat bermain game.",
        "telemetry_cpu_title": "METRIK CPU & DAYA",
        "telemetry_gpu_title": "GPU DISKRIT RTX 3050",
        "telemetry_ram_title": "MEMORI SISTEM & SWAP",
        "telemetry_bat_title": "KESEHATAN BATERAI & DAYA",
        "battery_charge_prefix": "Daya",
        "battery_cycles_prefix": "Siklus",
        "battery_health_prefix": "Kesehatan",

        # Device Specifications
        "specs_header": "SPESIFIKASI PERANGKAT & ARSITEKTUR FIRMWARE",
        "spec_family": "Keluarga Produk",
        "spec_mtm": "Machine Type Model (MTM)",
        "spec_sku": "SKU Sistem",
        "spec_bios": "Versi Firmware BIOS",
        "spec_bios_date": "Tanggal Rilis BIOS",
        "spec_ec": "Embedded Controller (EC)",
        "spec_os": "Sistem Operasi",
        "spec_kernel": "Kernel Aktif",
        "spec_power_engine": "Mesin Manajemen Daya",

        # RGB Lighting Studio & 5-Slot Profile Architecture
        "rgb_title": "STUDIO PENCAHAYAAN RGB 4-ZONA",
        "rgb_controller_badge": "KONTROLER PERANGKAT KERAS ITE 8295",
        "rgb_slots_header": "MESIN SIKLUS PROFIL 5-SLOT (FN + SPASI)",
        "rgb_slot_label": "SLOT {num}",
        "rgb_slot_active_badge": "PROFIL AKTIF",
        "rgb_cycle_btn": "Ganti Profil (Fn + Spasi)",
        "rgb_save_slot_btn": "Simpan Kustomisasi ke Slot {num}",
        "rgb_owner_title": "PEMEGANG KENDALI LAMPU",
        "rgb_owner_app": "Studio Vantage Pro (Aplikasi / 5 Slot Kustom + OSD)",
        "rgb_owner_bios": "Firmware Chip ITE (ROM Bawaan Pabrik)",
        "rgb_visual_topology": "TOPOLOGI KEYBOARD VISUAL (ILUMINASI 4-ZONA)",
        "rgb_zone_1_name": "ZONA 1",
        "rgb_zone_2_name": "ZONA 2",
        "rgb_zone_3_name": "ZONA 3",
        "rgb_zone_4_name": "ZONA 4",
        "rgb_zone_1_keys": "WASD / Kiri",
        "rgb_zone_2_keys": "Tengah Kiri",
        "rgb_zone_3_keys": "Tengah Kanan",
        "rgb_zone_4_keys": "Numpad / Kanan",
        "rgb_presets_title": "PRESET PENCAHAYAAN CEPAT",
        "rgb_preset_vantage_cyan": "💎 Vantage Cyan",
        "rgb_preset_cyber_neon": "⚡ Cyber Neon",
        "rgb_preset_crimson_fury": "🔥 Crimson Fury",
        "rgb_preset_emerald_stealth": "🍃 Emerald Stealth",
        "rgb_preset_smooth_wave": "🌊 Gelombang Halus",
        "rgb_preset_off": "🌙 Mati",
        "rgb_brightness_title": "KECERAHAN",
        "rgb_speed_title": "KECEPATAN EFEK",
        "rgb_pattern_title": "POLA EFEK PENCAHAYAAN",
        "rgb_palette_title": "PALET WARNA CEPAT & PENUGASAN ZONA",
        "rgb_apply_single_active": "Terapkan ke: ZONA TERPILIH (Klik utk Semua)",
        "rgb_apply_all_active": "Terapkan ke: SEMUA ZONA (Klik utk Satuan)",
        "rgb_pick_color": "Pilih Warna...",
        "rgb_selected": "TERPILIH",
        "rgb_off": "Mati",
        "rgb_low": "Rendah (50%)",
        "rgb_high": "Tinggi (100%)",
        "rgb_eff_static": "Statis",
        "rgb_eff_breathing": "Pernapasan",
        "rgb_eff_smooth_wave": "Gelombang Halus",
        "rgb_eff_wave": "Gelombang",
        "rgb_sync_perf_title": "SINKRONKAN RGB DENGAN MODE PERFORMA CPU",
        "rgb_sync_perf_sub": "Otomatis mengganti profil pencahayaan keyboard (Ekstrem: Crimson Fury, Standar: Vantage Cyan, Senyap: Mati) saat mode performa berganti (Fn + Q).",
        "rgb_sync_perf_active": "SINKRONISASI AKTIF (OTOMATIS)",
        "rgb_sync_perf_disabled": "SINKRONISASI NONAKTIF (HANYA MANUAL)",
        "tray_cycle_rgb": "Ganti Profil RGB (Fn + Spasi)",
        "tray_cycle_brightness": "Ganti Kecerahan Keyboard (Mati / 50% / 100%)",
        "osd_rgb_title": "PROFIL RGB KEYBOARD",
        "osd_rgb_off_sub": "LAMPU KEYBOARD MATI • 0% KECERAHAN",
        "osd_brightness_title": "KECERAHAN KEYBOARD",
        "osd_brightness_off": "0% • LAMPU MATI",
        "osd_brightness_low": "50% • REDUP",
        "osd_brightness_high": "100% • TERANG",

        # Gaming Tools: Wi-Fi, Blackbox, Diagnostics
        "wifi_title": "STABILISATOR WI-FI RENDAH-LATENSI ESPORTS",
        "wifi_sub": "PENEKAN JITTER SUB-MILIDETIK WLAN0 & BYPASS MICRO-SLEEP",
        "wifi_anti_jitter_btn": "Kunci Anti-Jitter (0ms Sleep)",
        "wifi_unlock_btn": "Lepas Kunci Anti-Jitter (Aktifkan Power Save)",
        "wifi_explanation": "Mematikan power-save Wi-Fi mencegah lonjakan ping saat bermain game kompetitif.",
        "wifi_ps_on": "● POWER SAVE: AKTIF",
        "wifi_ps_locked": "● KUNCI ANTI-JITTER ESPORTS (0ms SLEEP)",
        "wifi_gateway_title": "ROUND-TRIP GATEWAY",
        "wifi_measuring": "Mengukur latency...",
        "wifi_chip_ssid": "SSID Terhubung",
        "wifi_chip_ch": "Kanal / Frekuensi",
        "wifi_chip_tx": "Daya TX",
        "wifi_chip_gw": "Default Gateway",
        "wifi_ping_optimal": "Jitter Minimum • Performa Esports Optimal",
        "wifi_ping_stable": "Koneksi Stabil • Siap Bermain",
        "wifi_ping_high": "Latensi Terdeteksi Agak Tinggi",
        "wifi_ping_fail": "Gateway Tidak Merespon",

        "blackbox_title": "PEREKAM PENERBANGAN TELEMETRI BLACKBOX",
        "blackbox_sub": "PENCATATAN 1HZ SENSOR PERANGKAT KERAS & EKSPOR CSV/JSON",
        "blackbox_session_name": "Nama Sesi:",
        "blackbox_start_btn": "Mulai Rekam Penerbangan",
        "blackbox_stop_btn": "Hentikan Rekaman",
        "blackbox_open_btn": "Buka Folder Sesi",
        "blackbox_status_idle": "● PEREKAM SIAGA",
        "blackbox_status_active": "● SEDANG MEREKAM LIVE",
        "blackbox_recording_pill": "● SEDANG MEREKAM TELEMETRI",
        "blackbox_saved_pill": "● SESI TERSIMPAN",
        "blackbox_metric_duration": "DURASI SESI",
        "blackbox_metric_samples": "TOTAL SAMPEL (1 HZ)",
        "blackbox_metric_peak_cpu": "PEAK SUHU CPU",
        "blackbox_metric_peak_gpu": "PEAK SUHU GPU",
        "blackbox_metric_max_fan": "MAX FAN RPM",
        "blackbox_storage_prefix": "Penyimpanan: {path}",
        "blackbox_file_active": "File Aktif: {path}",
        "blackbox_file_saved": "Tersimpan: {path}",
        "blackbox_samples_suffix": "{samples} Sampel",

        "diag_title": "SUITE DIAGNOSTIK HARDWARE SISTEM",
        "diag_sub": "VERIFIKASI KESEHATAN & HARDWARE 6-POIN OTOMATIS",
        "diag_run_btn": "Jalankan Diagnostik Sistem (6 Pengujian)",
        "diag_running": "Sedang Menjalankan Pengujian...",
        "diag_complete": "Diagnostik Berhasil Diselesaikan",
        "diag_starting": "Memulai 6 pengujian hardware...",
        "diag_test_progress": "Pengujian {current}/{total}: {msg}",
        "diag_status_passed": "● STATUS SISTEM OPTIMAL: SEMUA {passed}/{total} SUBSISTEM LULUS (PASSED)",
        "diag_status_warning": "● SISTEM BERFUNGSI DENGAN CATATAN: {passed}/{total} LULUS, TERDAPAT PERINGATAN",
        "diag_status_failed": "● PERIKSA PERANGKAT KERAS: DITEMUKAN SUBSISTEM GAGAL",
        "diag_test_duration": "Durasi Uji: {dur} ms",
        "diag_test1_title": "Kesehatan Baterai & Chipset SBS",
        "diag_test1_desc": "Kapasitas, siklus pengisian daya, dan status ACPI MHCF flash block.",
        "diag_test2_title": "Pendingin Turbin Ganda & Kontrol MMIO",
        "diag_test2_desc": "Direct MMIO register 0xAB/0xAD dan putaran turbin kipas ganda.",
        "diag_test3_title": "Topologi Heterogen Intel Alder Lake",
        "diag_test3_desc": "P-Cores 0-7, E-Cores 8-15, dan intel_pstate no_turbo interface.",
        "diag_test4_title": "Bus Layar Esports & OverDrive ACPI",
        "diag_test4_desc": "Mode KWin Wayland 165Hz/60Hz dan register ACPI SSFM ODV2.",
        "diag_test5_title": "Bus PCIe & Driver NVIDIA RTX 3050",
        "diag_test5_desc": "Driver resmi, VRAM 4GB, dan dynamic PCIe D3 Cold state.",
        "diag_test6_title": "Subsistem Rendah Latensi Wi-Fi",
        "diag_test6_desc": "Latensi round-trip wlan0 ke gateway dan kunci micro-sleep 0ms.",

        # Tray Menu
        "tray_open": "Buka Lenovo Vantage Pro",
        "tray_thermal": "Profil Termal",
        "tray_silent": "🍃 Mode Senyap (Whisper Flow)",
        "tray_standard": "⚖️ Mode Standar (Kurva-S Dinamis)",
        "tray_extreme": "🚀 Mode Ekstrem (100% Kecepatan Penuh)",
        "tray_dust": "🌪️ Pembersih Debu (Pulsasi 30 Detik)",
        "tray_cons": "Alihkan Konservasi Baterai (75-80%)",
        "tray_refresh": "Refresh Rate Layar",
        "tray_language": "Bahasa / Language",
        "tray_lang_en": "English [EN]",
        "tray_lang_id": "Bahasa Indonesia [ID]",
        "tray_quit": "Keluar",

        # OSD Notifications
        "osd_perf_title": "MODE PERFORMA",
        "osd_perf_sub": "100% Turbin Penuh • 85W TGP Terbuka",
        "osd_std_title": "STANDAR SEIMBANG",
        "osd_std_sub": "Kurva-S Dinamis Bebas Sentakan",
        "osd_silent_title": "MODE SENYAP",
        "osd_silent_sub": "Profil Akustik Whisper Flow Pasif",
        "osd_165hz_title": "KUNCI 165.01 HZ ESPORTS",
        "osd_165hz_sub": "KWin Wayland Ultra-Mulus Refresh Rate Tinggi",
        "osd_60hz_title": "59.96 HZ HEMAT DAYA",
        "osd_60hz_sub": "Kunci Hemat Energi Daya Baterai",
        "osd_purge_title": "PEMBERSIHAN DEBU DIMULAI",
        "osd_purge_sub": "Siklus Gelombang Kejut 30 Detik Aktif",
        "osd_game_start_title": "MODE GAME AKTIF",
        "osd_game_start_sub": "Penguncian Thread P-Core Aktif: {name}",
        "osd_game_stop_title": "SESI GAME BERAKHIR",
        "osd_game_stop_sub": "Profil Hardware Dipulihkan ke Standar",
        "osd_noturbo_on_title": "NO-TURBO SENYAP AKTIF",
        "osd_noturbo_on_sub": "Boost CPU Dimatikan untuk Menjaga Suhu Dingin",
        "osd_noturbo_off_title": "TURBO BOOST DIPULIHKAN",
        "osd_noturbo_off_sub": "Performa Penuh Jam Tinggi Terbuka",
    }
}


class LanguageManager(QObject):
    """
    Central Internationalization Manager.
    Manages current language, string lookups, and emits signals on language switch.
    """
    language_changed = pyqtSignal(str)

    _instance = None

    @classmethod
    def get_instance(cls) -> "LanguageManager":
        if cls._instance is None:
            cls._instance = LanguageManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        self._current_lang = "id"  # Default to Indonesian or load from config
        self._load_config()

    def _load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    cfg = json.load(f)
                    saved_lang = cfg.get("language")
                    if saved_lang in ("en", "id"):
                        self._current_lang = saved_lang
        except Exception:
            pass

    def _save_config(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            cfg = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r") as f:
                        cfg = json.load(f)
                except Exception:
                    cfg = {}
            cfg["language"] = self._current_lang
            with open(CONFIG_FILE, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    @property
    def current_language(self) -> str:
        return self._current_lang

    def set_language(self, lang: str):
        if lang not in ("en", "id"):
            return
        if self._current_lang != lang:
            self._current_lang = lang
            self._save_config()
            self.language_changed.emit(lang)

    def tr(self, key: str, **kwargs) -> str:
        lang_dict = TRANSLATIONS.get(self._current_lang, TRANSLATIONS["en"])
        text = lang_dict.get(key)
        if text is None:
            # Fallback to English
            text = TRANSLATIONS["en"].get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


# Helper functions for clean consumption across modules
def tr(key: str, **kwargs) -> str:
    return LanguageManager.get_instance().tr(key, **kwargs)

def get_current_language() -> str:
    return LanguageManager.get_instance().current_language

def set_language(lang: str):
    LanguageManager.get_instance().set_language(lang)

def get_language_manager() -> LanguageManager:
    return LanguageManager.get_instance()
