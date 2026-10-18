import os
import re
import subprocess
import psutil
import threading
import time
import glob
import select
from collections import deque
from typing import Dict, Any, Optional, List, Tuple, Callable
import evdev


class FanSlewGovernor:
    """
    Enterprise Slew-Rate Limited S-Curve Fan Governor for Lenovo IdeaPad Gaming 3 & Legion.
    Features:
    - Slew-rate limiter (1 level per 1.2s ramp-up, 1 level per 2.5s ramp-down)
    - Anti-hunting hysteresis cooldown delay (8.0s)
    - Exponentially Weighted Moving Average (EWMA) temperature smoothing (alpha = 0.3)
    - Emergency Thermal Hard-Floor (>= 87.0°C immediately overrides to 100% max cooling)
    - 60-second rolling trajectory telemetry ring buffer
    - 4 distinct modes:
        1. 'silent': Ultra-low continuous acoustic profile, Level 1-6 capped
        2. 'standard': S-Curve gradual dynamic thermal tracking, Level 1-15 buttery-smooth
        3. 'extreme': High-power continuous 100% full speed cooling
        4. 'dust_cleaner': 30-second automated cyclical pulsation (5 cycles)
    """
    def __init__(self, hardware_cls):
        self.hw = hardware_cls
        self.lock = threading.RLock()
        self._active_mode = "standard"
        self._saved_mode = "standard"

        # Levels: 0 to 15
        self._current_level = 2
        self._target_level = 2
        self._smooth_temp = 45.0
        self._last_step_time = time.time()
        self._step_up_interval = 1.2    # seconds per level up (luxury gradual acoustic gradient)
        self._step_down_interval = 2.5  # seconds per level down (gentle deceleration)
        self._down_cooldown_delay = 8.0 # seconds before starting downward descent
        self._down_cooldown_start = 0.0

        # Dust purge state (5 cycles of 3.5s blast / 2.5s drop, 30s duration)
        self._purge_active = False
        self._purge_start_time = 0.0
        self._purge_duration = 30.0
        self._purge_cycle = 0
        self._purge_phase = "idle"

        # 60-second history buffer: (timestamp, temp, current_level, target_level, rpm)
        self._history = deque(maxlen=60)
        now = time.time()
        for i in range(60):
            self._history.append((now - (59 - i), 45.0, 2, 2, 1500))

        self._last_hw_sync_time = 0.0
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="FanSlewGovernor", daemon=True)
        self._thread.start()

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            cpu = self.hw.get_cpu_telemetry()
            gpu = self.hw.get_gpu_telemetry()
            t_cpu = cpu.get("temp_c", 0.0)
            t_gpu = float(gpu.get("temp_c", 0.0))
            t_max = max(t_cpu, t_gpu)

            rapl = self.hw.get_cooling_telemetry()

            purge_rem = 0.0
            purge_elapsed = 0.0
            purge_pct = 0
            if self._purge_active:
                purge_elapsed = round(time.time() - self._purge_start_time, 1)
                purge_rem = max(0.0, round(self._purge_duration - purge_elapsed, 1))
                purge_pct = int(min(100.0, (purge_elapsed / self._purge_duration) * 100))

            est_rpm = 950 + (self._current_level * 280) if self._current_level > 0 else 0

            desc_map = {
                "silent": f"Silent Mode: Whisper Flow mendinginkan konsisten ({self._smooth_temp:.0f}°C) • Level {self._current_level}/15 (~{est_rpm} RPM)",
                "standard": f"Standard Mode: S-Curve Gradual Dynamic • Level {self._current_level}/15 (~{est_rpm} RPM) • Target Lv.{self._target_level}",
                "extreme": f"Extreme Mode: Kipas 100% Maksimal Penuh (~5,200 RPM) • Headroom Termal Penuh",
            }
            if self._purge_active:
                phase_label = "Tiup Badai 100%" if self._purge_phase == "blast" else "Peredaan Cepat"
                status_desc = f"Dust Purge: Siklus {self._purge_cycle}/5 ({phase_label}) • {int(purge_rem)}s tersisa"
            else:
                status_desc = desc_map.get(self._active_mode, "Fan Slew Governor Active")

            return {
                "active_mode": self._active_mode,
                "status_desc": status_desc,
                "cpu_temp": t_cpu,
                "gpu_temp": t_gpu,
                "max_temp": t_max,
                "smooth_temp": self._smooth_temp,
                "current_level": self._current_level,
                "target_level": self._target_level,
                "estimated_rpm": est_rpm,
                "pl1_w": rapl.get("pl1_w", 45.0),
                "pl2_w": rapl.get("pl2_w", 65.0),
                "epp": rapl.get("epp", "balance_power"),
                # Purge telemetry data
                "purge_active": self._purge_active,
                "purge_cycle": self._purge_cycle,
                "purge_phase": self._purge_phase,
                "purge_remaining_s": int(purge_rem),
                "purge_elapsed_s": purge_elapsed,
                "purge_pct": purge_pct,
                # Backward compatibility for existing UI widgets/app.py
                "dust_active": self._purge_active,
                "dust_remaining_s": int(purge_rem),
                "dust_pct": purge_pct,
                "dust_cycle": self._purge_cycle,
                "dust_phase": self._purge_phase,
                "history": list(self._history),
            }

    def set_mode(self, mode: str) -> bool:
        if mode not in ("silent", "standard", "extreme"):
            return False

        with self.lock:
            if self._purge_active:
                self.cancel_dust_purge()

            self._active_mode = mode
            target = self._calc_target_level(mode, self._smooth_temp)
            self._target_level = target
            # Quick nudge towards target
            if mode == "extreme":
                self._current_level = 15
                self.hw.run_helper("fan-extreme")
            elif mode == "silent":
                self._current_level = min(self._current_level, 4)
                self.hw.run_helper(f"fan-level {self._current_level}")
            else:
                self.hw.run_helper(f"fan-level {self._current_level}")
            return True

    def start_dust_purge(self) -> bool:
        with self.lock:
            if not self._purge_active:
                self._saved_mode = self._active_mode
                self._purge_active = True
                self._purge_start_time = time.time()
                self._purge_cycle = 1
                self._purge_phase = "blast"
                self._current_level = 15
                self._target_level = 15
                self.hw.run_helper("fan-dust-burst")
            return True

    def cancel_dust_purge(self) -> bool:
        with self.lock:
            if self._purge_active:
                self._purge_active = False
                self._purge_cycle = 0
                self._purge_phase = "idle"
                prev = self._saved_mode if self._saved_mode in ("silent", "standard", "extreme") else "standard"
                self._active_mode = prev
                self._target_level = self._calc_target_level(prev, self._smooth_temp)
                if prev == "extreme":
                    self._current_level = 15
                    self.hw.run_helper("fan-extreme")
                elif prev == "silent":
                    self._current_level = min(self._current_level, 4)
                    self.hw.run_helper("fan-silent")
                else:
                    self._current_level = 2
                    self.hw.run_helper("fan-standard")
                return True
        return False

    def stop_dust_cleaning(self) -> bool:
        return self.cancel_dust_purge()

    def _calc_target_level(self, mode: str, t_max: float) -> int:
        if t_max >= 87.0:
            return 15

        if mode == "extreme":
            return 15

        elif mode == "silent":
            if t_max < 48.0:
                return 1
            elif t_max < 56.0:
                return 2
            elif t_max < 65.0:
                return 3
            elif t_max < 74.0:
                return 4
            elif t_max < 82.0:
                return 6
            else:
                return 8

        elif mode == "standard":
            if t_max < 46.0:
                return 1
            elif t_max < 52.0:
                return 2
            elif t_max < 58.0:
                return 4
            elif t_max < 64.0:
                return 6
            elif t_max < 70.0:
                return 8
            elif t_max < 76.0:
                return 10
            elif t_max < 82.0:
                return 12
            elif t_max < 86.0:
                return 14
            else:
                return 15

        return 2

    def _loop(self):
        last_hist_time = 0.0
        while self._running:
            try:
                now = time.time()
                cpu = self.hw.get_cpu_telemetry()
                gpu = self.hw.get_gpu_telemetry()
                t_cpu = cpu.get("temp_c", 0.0)
                t_gpu = float(gpu.get("temp_c", 0.0))
                raw_max = max(t_cpu, t_gpu)

                with self.lock:
                    self._smooth_temp = round(0.3 * raw_max + 0.7 * self._smooth_temp, 1)
                    mode = self._active_mode
                    if self._purge_active:
                        elapsed = now - self._purge_start_time
                        if elapsed >= self._purge_duration:
                            self.cancel_dust_purge()
                        else:
                            cycle_idx = min(5, int(elapsed // 6.0) + 1)
                            cycle_time = elapsed % 6.0
                            self._purge_cycle = cycle_idx
                            if cycle_time < 3.5:
                                self._purge_phase = "blast"
                                target = 15
                                if self._current_level != target:
                                    self._current_level = target
                                    self.hw.run_helper("fan-dust-burst")
                            else:
                                self._purge_phase = "drop"
                                target = 1
                                if self._current_level != target:
                                    self._current_level = target
                                    self.hw.run_helper("fan-dust-rest")
                            self._target_level = target
                    else:
                        target = self._calc_target_level(mode, self._smooth_temp)
                        self._target_level = target

                        if target > self._current_level:
                            self._down_cooldown_start = 0.0
                            if self._smooth_temp >= 87.0:
                                self._current_level = 15
                                self._last_step_time = now
                                self.hw.run_helper("fan-extreme")
                            elif (now - self._last_step_time) >= self._step_up_interval:
                                self._current_level += 1
                                self._last_step_time = now
                                if mode == "extreme" and self._current_level >= 15:
                                    self.hw.run_helper("fan-extreme")
                                else:
                                    self.hw.run_helper(f"fan-level {self._current_level}")

                        elif target < self._current_level:
                            if self._down_cooldown_start == 0.0:
                                self._down_cooldown_start = now
                            elif (now - self._down_cooldown_start) >= self._down_cooldown_delay:
                                if (now - self._last_step_time) >= self._step_down_interval:
                                    self._current_level -= 1
                                    self._last_step_time = now
                                    self.hw.run_helper(f"fan-level {self._current_level}")
                        else:
                            self._down_cooldown_start = 0.0

                        if (now - self._last_hw_sync_time) >= 3.0:
                            self._last_hw_sync_time = now
                            if mode == "extreme":
                                self.hw.run_helper("fan-extreme")
                            else:
                                self.hw.run_helper(f"fan-level {self._current_level}")

                    if (now - last_hist_time) >= 1.0:
                        last_hist_time = now
                        est_rpm = 950 + (self._current_level * 280) if self._current_level > 0 else 0
                        self._history.append((now, self._smooth_temp, self._current_level, self._target_level, est_rpm))

            except Exception:
                pass

            time.sleep(0.25)

FanCoolingGovernor = FanSlewGovernor


class LenovoHardware:
    HELPER_BIN = "/usr/bin/lenovo-vantage-helper"
    VPC_PATH = "/sys/bus/platform/devices/VPC2004:00"
    PLATFORM_PROFILE = "/sys/firmware/acpi/platform_profile"
    BAT_PATH = "/sys/class/power_supply/BAT1"
    DMI_PATH = "/sys/class/dmi/id"

    @classmethod
    def run_helper(cls, action_args: str) -> bool:
        if os.path.exists(cls.HELPER_BIN):
            try:
                args = [cls.HELPER_BIN] + action_args.split()
                subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                return True
            except Exception:
                pass
        return False

    @classmethod
    def read_sysfs(cls, path: str) -> Optional[str]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception:
                return None
        return None

    @classmethod
    def write_sysfs(cls, path: str, value: str) -> bool:
        if not os.path.exists(path):
            return False
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(value))
            return True
        except PermissionError:
            cls.run_helper("fix-perms")
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(str(value))
                return True
            except Exception:
                return False
        except Exception:
            return False

    @classmethod
    def get_machine_info(cls) -> Dict[str, str]:
        info = {
            "model": cls.read_sysfs(f"{cls.DMI_PATH}/product_version") or "Lenovo Laptop",
            "family": cls.read_sysfs(f"{cls.DMI_PATH}/product_family") or "IdeaPad",
            "mtm": cls.read_sysfs(f"{cls.DMI_PATH}/product_name") or "82S9",
            "sku": cls.read_sysfs(f"{cls.DMI_PATH}/product_sku") or "",
            "bios": cls.read_sysfs(f"{cls.DMI_PATH}/bios_version") or "Unknown",
            "bios_date": cls.read_sysfs(f"{cls.DMI_PATH}/bios_date") or "",
            "vendor": cls.read_sysfs(f"{cls.DMI_PATH}/sys_vendor") or "Lenovo",
        }
        return info

    RAPL_DIR = "/sys/class/powercap/intel-rapl/intel-rapl:0"
    ACPI_CALL = "/proc/acpi/call"

    @classmethod
    def acpi_call(cls, cmd: str) -> Optional[str]:
        if not os.path.exists(cls.ACPI_CALL):
            return None
        try:
            with open(cls.ACPI_CALL, "w") as f:
                f.write(cmd.strip() + "\n")
            with open(cls.ACPI_CALL, "r") as f:
                res = f.read().replace("\x00", "").strip()
                return res if res else None
        except Exception:
            return None

    @classmethod
    def get_thermal_profile(cls) -> str:
        profile = cls.read_sysfs(cls.PLATFORM_PROFILE)
        if profile in ("low-power", "balanced", "performance"):
            return profile
        # Fallback to WMAA 0x2D
        raw = cls.acpi_call(r"\_SB.GZFD.WMAA 0 0x2D 0")
        if raw == "0x1":
            return "low-power"
        elif raw == "0x3":
            return "performance"
        return "balanced"

    @classmethod
    def set_thermal_profile(cls, profile: str) -> bool:
        if profile in ("quiet", "silent"):
            profile = "low-power"
        valid_profiles = {
            "low-power": {
                "wma_arg": 1,
                "pl1_uw": 25000000,
                "pl2_uw": 35000000,
                "epp": "power",
            },
            "balanced": {
                "wma_arg": 2,
                "pl1_uw": 45000000,
                "pl2_uw": 65000000,
                "epp": "balance_power",
            },
            "performance": {
                "wma_arg": 3,
                "pl1_uw": 75000000,
                "pl2_uw": 115000000,
                "epp": "performance",
            },
        }
        if profile not in valid_profiles:
            return False

        cfg = valid_profiles[profile]

        # 1. Execute privileged hardware helper (sets platform_profile, WMAA 0x2C, RAPL, and EPP with 0ms overhead)
        cls.run_helper(f"profile {profile}")

        # 2. Also write direct sysfs for immediate feedback
        cls.write_sysfs(cls.PLATFORM_PROFILE, profile)

        # 3. Synchronize hotkey listener profile cache to prevent redundant triggering
        if cls._hotkey_listener is not None:
            cls._hotkey_listener.update_last_profile(profile)
        return True

    @classmethod
    def get_cooling_telemetry(cls) -> Dict[str, Any]:
        profile = cls.get_thermal_profile()
        pl1_w = 0.0
        pl2_w = 0.0
        if os.path.exists(cls.RAPL_DIR):
            c0 = cls.read_sysfs(f"{cls.RAPL_DIR}/constraint_0_power_limit_uw")
            c1 = cls.read_sysfs(f"{cls.RAPL_DIR}/constraint_1_power_limit_uw")
            if c0 and c0.isdigit():
                pl1_w = round(int(c0) / 1000000, 1)
            if c1 and c1.isdigit():
                pl2_w = round(int(c1) / 1000000, 1)

        epp = cls.read_sysfs("/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference") or "unknown"
        raw_mode = cls.acpi_call(r"\_SB.GZFD.WMAA 0 0x2D 0") or "0x2"

        desc_map = {
            "low-power": "Whisper Quiet (Passive <50°C, Power-Capped 25W)",
            "balanced": "Dynamic Smooth (Hysteresis Damped, 45W/65W - No Surging)",
            "performance": "Turbo Gaming (Max Cooling Flow, Uncapped 115W PL2)",
        }

        return {
            "profile": profile,
            "raw_mode": raw_mode,
            "pl1_w": pl1_w,
            "pl2_w": pl2_w,
            "epp": epp,
            "description": desc_map.get(profile, "Standard Automatic Cooling"),
        }

    @classmethod
    def set_max_cooling_boost(cls, enabled: bool) -> bool:
        if enabled:
            cls.set_thermal_profile("performance")
            try:
                subprocess.run(["nvidia-smi", "-pm", "1"], capture_output=True, check=False)
            except Exception:
                pass
            return True
        else:
            cls.set_thermal_profile("balanced")
            return True

    _governor = None
    _hotkey_listener = None
    _game_detector = None

    @classmethod
    def get_fan_governor(cls):
        if cls._governor is None:
            cls._governor = FanCoolingGovernor(cls)
        return cls._governor

    @classmethod
    def get_hotkey_listener(cls):
        if cls._hotkey_listener is None:
            cls._hotkey_listener = LenovoHotkeyListener()
        return cls._hotkey_listener

    @classmethod
    def get_game_detector(cls):
        if cls._game_detector is None:
            cls._game_detector = AutoGameDetector()
        return cls._game_detector

    @classmethod
    def get_no_turbo(cls) -> bool:
        return IntelAlderLakeScheduler.get_no_turbo()

    @classmethod
    def set_no_turbo(cls, enable: bool) -> bool:
        return IntelAlderLakeScheduler.set_no_turbo(enable)

    @classmethod
    def pin_process_to_pcores(cls, pid: int) -> bool:
        return IntelAlderLakeScheduler.pin_process_to_pcores(pid)

    @classmethod
    def cycle_thermal_profile(cls) -> str:
        curr = cls.get_thermal_profile()
        cycle_map = {
            "low-power": "balanced",
            "balanced": "performance",
            "performance": "low-power",
        }
        nxt = cycle_map.get(curr, "balanced")
        cls.set_thermal_profile(nxt)
        return nxt

    @classmethod
    def get_fan_cooling_status(cls) -> Dict[str, Any]:
        return cls.get_fan_governor().get_status()

    @classmethod
    def set_fan_cooling_mode(cls, mode: str) -> bool:
        return cls.get_fan_governor().set_mode(mode)

    @classmethod
    def start_dust_purge(cls) -> bool:
        return cls.get_fan_governor().start_dust_purge()

    @classmethod
    def cancel_dust_purge(cls) -> bool:
        return cls.get_fan_governor().cancel_dust_purge()

    @classmethod
    def stop_dust_cleaning(cls) -> bool:
        return cls.cancel_dust_purge()

    @classmethod
    def set_rapid_charge(cls, enable: bool) -> bool:
        return cls.run_helper(f"rapid-charge {'on' if enable else 'off'}")

    @classmethod
    def set_rgb_owner(cls, app: bool) -> bool:
        return cls.run_helper(f"rgb-owner {'app' if app else 'bios'}")

    @classmethod
    def get_conservation_mode(cls) -> bool:
        val = cls.read_sysfs(f"{cls.VPC_PATH}/conservation_mode")
        return val == "1"

    @classmethod
    def set_conservation_mode(cls, enabled: bool) -> bool:
        return cls.write_sysfs(f"{cls.VPC_PATH}/conservation_mode", "1" if enabled else "0")

    @classmethod
    def get_fn_lock(cls) -> bool:
        val = cls.read_sysfs(f"{cls.VPC_PATH}/fn_lock")
        return val == "1"

    @classmethod
    def set_fn_lock(cls, enabled: bool) -> bool:
        return cls.write_sysfs(f"{cls.VPC_PATH}/fn_lock", "1" if enabled else "0")

    @classmethod
    def get_touchpad_status(cls) -> bool:
        try:
            res = subprocess.run(
                ["xinput", "list"],
                capture_output=True,
                text=True,
                check=False
            )
            for line in res.stdout.splitlines():
                if "touchpad" in line.lower() and "id=" in line.lower():
                    tid = line.split("id=")[1].split()[0]
                    props = subprocess.run(
                        ["xinput", "--list-props", tid],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    for pline in props.stdout.splitlines():
                        if "Device Enabled" in pline:
                            return pline.strip().endswith("1")
        except Exception:
            pass
        return True

    @classmethod
    def set_touchpad_status(cls, enabled: bool) -> bool:
        try:
            res = subprocess.run(
                ["xinput", "list"],
                capture_output=True,
                text=True,
                check=False
            )
            for line in res.stdout.splitlines():
                if "touchpad" in line.lower() and "id=" in line.lower():
                    tid = line.split("id=")[1].split()[0]
                    action = "enable" if enabled else "disable"
                    subprocess.run(["xinput", action, tid], check=False)
                    return True
        except Exception:
            pass
        return False

    @classmethod
    def get_camera_status(cls) -> bool:
        try:
            res = subprocess.run(["lsmod"], capture_output=True, text=True, check=False)
            return "uvcvideo" in res.stdout
        except Exception:
            return True

    @classmethod
    def set_camera_status(cls, enabled: bool) -> bool:
        return cls.run_helper(f"camera {'on' if enabled else 'off'}")

    @classmethod
    def get_mic_mute(cls) -> bool:
        try:
            res = subprocess.run(
                ["pactl", "get-source-mute", "@DEFAULT_SOURCE@"],
                capture_output=True,
                text=True,
                check=False
            )
            return "yes" in res.stdout.lower()
        except Exception:
            return False

    @classmethod
    def set_mic_mute(cls, mute: bool) -> bool:
        val = "1" if mute else "0"
        try:
            subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", val], check=False)
            return True
        except Exception:
            return False

    @classmethod
    def get_battery_info(cls) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "capacity": 0,
            "status": "Unknown",
            "health_pct": 100.0,
            "cycle_count": 0,
            "energy_full_wh": 0.0,
            "energy_design_wh": 0.0,
            "power_draw_w": 0.0,
            "model": "Unknown",
            "vendor": "Lenovo",
            "technology": "Li-ion"
        }
        if not os.path.exists(cls.BAT_PATH):
            return info

        cap = cls.read_sysfs(f"{cls.BAT_PATH}/capacity")
        if cap and cap.isdigit():
            info["capacity"] = int(cap)

        status = cls.read_sysfs(f"{cls.BAT_PATH}/status")
        if status:
            info["status"] = status

        cycles = cls.read_sysfs(f"{cls.BAT_PATH}/cycle_count")
        if cycles and cycles.isdigit():
            info["cycle_count"] = int(cycles)

        e_full = cls.read_sysfs(f"{cls.BAT_PATH}/energy_full")
        e_design = cls.read_sysfs(f"{cls.BAT_PATH}/energy_full_design")
        if e_full and e_design and e_design.isdigit() and int(e_design) > 0:
            full_uwh = int(e_full)
            design_uwh = int(e_design)
            info["energy_full_wh"] = round(full_uwh / 1_000_000, 2)
            info["energy_design_wh"] = round(design_uwh / 1_000_000, 2)
            info["health_pct"] = round((full_uwh / design_uwh) * 100, 1)

        p_now = cls.read_sysfs(f"{cls.BAT_PATH}/power_now")
        if p_now and p_now.isdigit():
            info["power_draw_w"] = round(int(p_now) / 1_000_000, 2)

        info["model"] = cls.read_sysfs(f"{cls.BAT_PATH}/model_name") or info["model"]
        info["vendor"] = cls.read_sysfs(f"{cls.BAT_PATH}/manufacturer") or info["vendor"]
        info["technology"] = cls.read_sysfs(f"{cls.BAT_PATH}/technology") or info["technology"]

        return info

    @classmethod
    def get_cpu_telemetry(cls) -> Dict[str, Any]:
        temp = 0.0
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            for key in ["coretemp", "k10temp", "acpitz", "x86_pkg_temp"]:
                if key in temps and temps[key]:
                    temp = round(temps[key][0].current, 1)
                    break

        load = round(psutil.cpu_percent(interval=None), 1)
        freq = 0
        freq_info = psutil.cpu_freq()
        if freq_info:
            freq = int(freq_info.current)

        return {
            "load_pct": load,
            "temp_c": temp,
            "freq_mhz": freq,
            "cores": psutil.cpu_count(logical=True),
        }

    @classmethod
    def get_gpu_telemetry(cls) -> Dict[str, Any]:
        info = {
            "name": "NVIDIA Discrete GPU",
            "temp_c": 0,
            "load_pct": 0,
            "vram_used_mb": 0,
            "vram_total_mb": 4096,
            "vram_pct": 0.0,
            "driver": "Unknown",
            "available": False
        }
        try:
            res = subprocess.run([
                "nvidia-smi",
                "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,driver_version",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, check=True, timeout=1.5)
            line = res.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                info["name"] = parts[0]
                info["temp_c"] = int(parts[1]) if parts[1].isdigit() else 0
                info["load_pct"] = int(parts[2]) if parts[2].isdigit() else 0
                info["vram_used_mb"] = int(parts[3]) if parts[3].isdigit() else 0
                info["vram_total_mb"] = int(parts[4]) if parts[4].isdigit() else 4096
                if info["vram_total_mb"] > 0:
                    info["vram_pct"] = round((info["vram_used_mb"] / info["vram_total_mb"]) * 100, 1)
                info["driver"] = parts[5]
                info["available"] = True
        except Exception:
            pass
        return info

    @classmethod
    def get_ram_telemetry(cls) -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        return {
            "total_gb": round(vm.total / (1024**3), 1),
            "used_gb": round(vm.used / (1024**3), 1),
            "pct": round(vm.percent, 1)
        }


class LenovoDisplayManager:
    """
    Manages display refresh rate and overdrive for Lenovo display panels.
    Interfaces with kscreen-doctor on Wayland / X11 and hardware overdrive helper.
    """
    _screen_overdrive_level: int = 0

    @classmethod
    def _get_wayland_env(cls) -> Dict[str, str]:
        env = os.environ.copy()
        if "WAYLAND_DISPLAY" not in env:
            env["WAYLAND_DISPLAY"] = "wayland-1"
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"
        if "XDG_RUNTIME_DIR" not in env:
            env["XDG_RUNTIME_DIR"] = "/run/user/1000"
        return env

    @classmethod
    def get_display_info(cls) -> Dict[str, Any]:
        """
        Query kscreen-doctor -o in user-space Wayland to detect whether currently 165Hz or 60Hz.
        """
        env = cls._get_wayland_env()
        info: Dict[str, Any] = {
            "current_hz": 165,
            "mode_id": "1",
            "resolution": "1920x1080",
            "hz_raw": "165.01",
            "overdrive": cls.get_screen_overdrive(),
            "available_hz": [60, 165],
        }
        try:
            res = subprocess.run(
                ["kscreen-doctor", "-o"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=2.0
            )
            clean_out = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", res.stdout)
            match = re.search(r"(\d+):(\d+x\d+)@([\d\.]+)\*!?", clean_out)
            if match:
                mode_id, res_str, hz_str = match.groups()
                hz_float = float(hz_str)
                info["mode_id"] = mode_id
                info["resolution"] = res_str
                info["hz_raw"] = hz_str
                info["current_hz"] = 165 if hz_float > 100 else 60
        except Exception:
            pass
        return info

    @classmethod
    def set_refresh_rate(cls, hz: int) -> bool:
        """
        Set refresh rate: 165 runs kscreen-doctor output.eDP-1.mode.1;
        60 runs kscreen-doctor output.eDP-1.mode.8.
        """
        env = cls._get_wayland_env()
        mode_arg = "output.eDP-1.mode.1" if hz == 165 else "output.eDP-1.mode.8"
        try:
            res = subprocess.run(
                ["kscreen-doctor", mode_arg],
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=3.0
            )
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def set_screen_overdrive(cls, level: int) -> bool:
        """
        Set screen overdrive level (0, 1, 2) via hardware helper.
        """
        if level < 0:
            level = 0
        elif level > 2:
            level = 2
        cls._screen_overdrive_level = level
        return LenovoHardware.run_helper(f"overdrive {level}")

    @classmethod
    def get_screen_overdrive(cls) -> int:
        """
        Get the last configured screen overdrive level (default 0).
        """
        return cls._screen_overdrive_level

    @classmethod
    def toggle_refresh_rate(cls) -> int:
        """
        Toggle refresh rate between 60Hz and 165Hz. Returns the new refresh rate.
        """
        info = cls.get_display_info()
        new_hz = 60 if info.get("current_hz", 165) == 165 else 165
        cls.set_refresh_rate(new_hz)
        return new_hz


class IntelAlderLakeScheduler:
    """
    Scheduler and Turbo Governor for Intel 12th Gen Alder Lake-H (i5-12500H: 4 P-Cores / 8 E-Cores).
    P-Cores with Hyper-Threading: CPUs 0-7
    E-Cores: CPUs 8-15
    """
    NO_TURBO_SYSFS = "/sys/devices/system/cpu/intel_pstate/no_turbo"

    @classmethod
    def get_no_turbo(cls) -> bool:
        """
        Membaca /sys/devices/system/cpu/intel_pstate/no_turbo (mengembalikan True jika '1').
        """
        val = LenovoHardware.read_sysfs(cls.NO_TURBO_SYSFS)
        return val == "1"

    @classmethod
    def set_no_turbo(cls, enable: bool) -> bool:
        """
        Memanggil helper 'no-turbo on' atau 'no-turbo off'.
        """
        action = "on" if enable else "off"
        ok = LenovoHardware.run_helper(f"no-turbo {action}")
        if not ok:
            ok = LenovoHardware.write_sysfs(cls.NO_TURBO_SYSFS, "1" if enable else "0")
        return ok

    @classmethod
    def pin_process_to_pcores(cls, pid: int) -> bool:
        """
        Mengeksekusi taskset -cp 0-7 <pid> (4 P-Cores i5-12500H dengan HT: CPU 0 sampai 7).
        """
        try:
            res = subprocess.run(
                ["taskset", "-cp", "0-7", str(pid)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            return res.returncode == 0
        except Exception:
            return False


class LenovoHotkeyListener:
    """
    Daemon listener for Lenovo IdeaPad / Legion Hotkeys and ACPI platform profile events.
    Listens on /dev/input/event11 (Ideapad extra buttons) and monitors /sys/firmware/acpi/platform_profile.
    """
    DEFAULT_DEVICE = "/dev/input/event11"
    PLATFORM_PROFILE = "/sys/firmware/acpi/platform_profile"

    # Keycodes to detect:
    # KEY_REFRESH_RATE_TOGGLE: 631 (0x277) / 562
    REFRESH_KEYCODES = {631, 0x277, 562, getattr(evdev.ecodes, "KEY_REFRESH_RATE_TOGGLE", 562)}
    # Fan cycle hotkeys: KEY_PROG1 (148), KEY_PROG3 (202), KEY_FAVORITES (364)
    FAN_CYCLE_KEYCODES = {
        148,
        202,
        364,
        getattr(evdev.ecodes, "KEY_PROG1", 148),
        getattr(evdev.ecodes, "KEY_PROG3", 202),
        getattr(evdev.ecodes, "KEY_FAVORITES", 364),
    }

    def __init__(
        self,
        device_path: str = DEFAULT_DEVICE,
        on_toggle_refresh_rate: Optional[Callable[[], None]] = None,
        on_cycle_fan_mode: Optional[Callable[[], None]] = None,
        on_profile_changed: Optional[Callable[[str], None]] = None,
        autostart: bool = True,
    ):
        self.device_path = device_path
        self.lock = threading.RLock()
        self._device: Optional[evdev.InputDevice] = None
        self._last_profile: Optional[str] = LenovoHardware.read_sysfs(self.PLATFORM_PROFILE)

        self._on_toggle_refresh_rate = on_toggle_refresh_rate
        self._on_cycle_fan_mode = on_cycle_fan_mode
        self._on_profile_changed = on_profile_changed

        self._running = False
        self._thread: Optional[threading.Thread] = None

        if autostart:
            self.start()

    def register_callbacks(
        self,
        on_toggle_refresh_rate: Optional[Callable[[], None]] = None,
        on_cycle_fan_mode: Optional[Callable[[], None]] = None,
        on_profile_changed: Optional[Callable[[str], None]] = None,
    ) -> None:
        with self.lock:
            if on_toggle_refresh_rate is not None:
                self._on_toggle_refresh_rate = on_toggle_refresh_rate
            if on_cycle_fan_mode is not None:
                self._on_cycle_fan_mode = on_cycle_fan_mode
            if on_profile_changed is not None:
                self._on_profile_changed = on_profile_changed

    def update_last_profile(self, profile: str) -> None:
        with self.lock:
            self._last_profile = profile

    def start(self) -> None:
        with self.lock:
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._loop, name="LenovoHotkeyListener", daemon=True)
                self._thread.start()

    def stop(self) -> None:
        with self.lock:
            self._running = False
            if self._device:
                try:
                    self._device.close()
                except Exception:
                    pass
                self._device = None

    def _loop(self) -> None:
        last_profile_check = 0.0
        while self._running:
            now = time.time()

            # 1. Check /sys/firmware/acpi/platform_profile for EC profile switches (e.g. Fn+Q)
            if (now - last_profile_check) >= 0.5:
                last_profile_check = now
                curr_profile = LenovoHardware.read_sysfs(self.PLATFORM_PROFILE)
                cb_profile = None
                cb_fan = None
                with self.lock:
                    if curr_profile and curr_profile != self._last_profile:
                        self._last_profile = curr_profile
                        cb_profile = self._on_profile_changed
                        cb_fan = self._on_cycle_fan_mode

                if cb_profile is not None:
                    try:
                        cb_profile(curr_profile)
                    except Exception:
                        pass
                elif cb_fan is not None:
                    try:
                        cb_fan()
                    except Exception:
                        pass

            # 2. Check /dev/input/event11 for hotkeys
            if self._device is None:
                try:
                    if os.path.exists(self.device_path):
                        self._device = evdev.InputDevice(self.device_path)
                except Exception:
                    self._device = None
                    time.sleep(0.5)
                    continue

            try:
                r, _, _ = select.select([self._device.fd], [], [], 0.5)
                if r:
                    for event in self._device.read():
                        if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                            key_name = evdev.ecodes.KEY.get(event.code, "")
                            # Match refresh rate toggle
                            if event.code in self.REFRESH_KEYCODES or key_name == "KEY_REFRESH_RATE_TOGGLE":
                                with self.lock:
                                    cb = self._on_toggle_refresh_rate
                                if cb:
                                    try:
                                        cb()
                                    except Exception:
                                        pass
                            # Match fan mode cycle (KEY_PROG1, KEY_PROG3, KEY_FAVORITES)
                            elif event.code in self.FAN_CYCLE_KEYCODES or key_name in ("KEY_PROG1", "KEY_PROG3", "KEY_FAVORITES"):
                                with self.lock:
                                    cb = self._on_cycle_fan_mode
                                if cb:
                                    try:
                                        cb()
                                    except Exception:
                                        pass
            except (OSError, IOError):
                if self._device:
                    try:
                        self._device.close()
                    except Exception:
                        pass
                self._device = None
                time.sleep(0.5)
            except Exception:
                time.sleep(0.5)


class AutoGameDetector:
    """
    Automated Game Process Detector & Performance Profile Orchestrator.
    Periodically monitors running processes (every 2.5s) to detect active games.
    """
    GAME_PROCESS_NAMES = [
        "steam_app_",
        "cs2",
        "dota2",
        "wine64-preloader",
        "proton",
        "gamescope",
        "lutris",
        "heroic",
        "apex",
        "overwatch",
        "cyberpunk2077",
    ]

    def __init__(
        self,
        auto_profile_enabled: bool = False,
        poll_interval: float = 2.5,
        on_game_started: Optional[Callable[[int, str], None]] = None,
        on_game_stopped: Optional[Callable[[str], None]] = None,
        autostart: bool = True,
    ):
        self.lock = threading.RLock()
        self.poll_interval = poll_interval
        self._auto_profile_enabled = auto_profile_enabled
        self.active_game_pid: Optional[int] = None
        self.active_game_name: Optional[str] = None
        self.is_gaming_active: bool = False
        self._previous_profile: Optional[str] = None

        self._on_game_started = on_game_started
        self._on_game_stopped = on_game_stopped

        self._running = False
        self._thread: Optional[threading.Thread] = None

        if autostart:
            self.start()

    def set_auto_profile_enabled(self, enable: bool) -> None:
        with self.lock:
            self._auto_profile_enabled = enable

    def is_auto_profile_enabled(self) -> bool:
        with self.lock:
            return self._auto_profile_enabled

    @property
    def auto_profile_enabled(self) -> bool:
        return self.is_auto_profile_enabled()

    def register_callbacks(
        self,
        on_game_started: Optional[Callable[[int, str], None]] = None,
        on_game_stopped: Optional[Callable[[str], None]] = None,
    ) -> None:
        with self.lock:
            if on_game_started is not None:
                self._on_game_started = on_game_started
            if on_game_stopped is not None:
                self._on_game_stopped = on_game_stopped

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "is_gaming_active": self.is_gaming_active,
                "active_game_pid": self.active_game_pid,
                "active_game_name": self.active_game_name,
                "auto_profile_enabled": self._auto_profile_enabled,
            }

    def start(self) -> None:
        with self.lock:
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._loop, name="AutoGameDetector", daemon=True)
                self._thread.start()

    def stop(self) -> None:
        with self.lock:
            self._running = False

    def _check_running_game(self) -> Optional[Tuple[int, str]]:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pname = (proc.info.get('name') or "").lower()
                cmdline = " ".join(proc.info.get('cmdline') or []).lower()
                for gname in self.GAME_PROCESS_NAMES:
                    g_lower = gname.lower()
                    if g_lower in pname or (g_lower == "steam_app_" and g_lower in cmdline):
                        return (proc.info['pid'], proc.info.get('name') or gname)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue
        return None

    def _loop(self) -> None:
        while self._running:
            try:
                with self.lock:
                    if self.is_gaming_active:
                        # Check if the active game process is still alive
                        pid_alive = False
                        if self.active_game_pid:
                            try:
                                p = psutil.Process(self.active_game_pid)
                                if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                                    pid_alive = True
                            except Exception:
                                pid_alive = False

                        if not pid_alive:
                            stopped_name = self.active_game_name or "Game"
                            self.is_gaming_active = False
                            self.active_game_pid = None
                            self.active_game_name = None

                            if self._auto_profile_enabled and self._previous_profile:
                                LenovoHardware.set_thermal_profile(self._previous_profile)
                                self._previous_profile = None

                            if callable(self._on_game_stopped):
                                try:
                                    self._on_game_stopped(stopped_name)
                                except Exception:
                                    pass
                    else:
                        game = self._check_running_game()
                        if game:
                            pid, name = game
                            self.is_gaming_active = True
                            self.active_game_pid = pid
                            self.active_game_name = name

                            if self._auto_profile_enabled:
                                self._previous_profile = LenovoHardware.get_thermal_profile()
                                LenovoHardware.set_thermal_profile("performance")
                                IntelAlderLakeScheduler.pin_process_to_pcores(pid)

                            if callable(self._on_game_started):
                                try:
                                    self._on_game_started(pid, name)
                                except Exception:
                                    pass
            except Exception:
                pass

            time.sleep(self.poll_interval)

