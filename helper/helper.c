#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <glob.h>

#define MMIO_BASE_ADDR   0xFE0B0000
#define MMIO_OFFSET      0x800
#define MMIO_REG_AB      0xAB
#define MMIO_REG_AD      0xAD

static void write_file(const char *path, const char *val) {
    int fd = open(path, O_WRONLY);
    if (fd >= 0) {
        write(fd, val, strlen(val));
        close(fd);
    }
}

static void call_acpi(const char *cmd) {
    write_file("/proc/acpi/call", cmd);
}

static void write_mmio(unsigned char val_ab, unsigned char val_ad) {
    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (fd < 0) return;

    void *map = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, MMIO_BASE_ADDR);
    if (map != MAP_FAILED) {
        volatile unsigned char *regs = (volatile unsigned char *)map;
        regs[MMIO_OFFSET + MMIO_REG_AB] = val_ab;
        regs[MMIO_OFFSET + MMIO_REG_AD] = val_ad;
        munmap(map, 4096);
    }
    close(fd);
}

static int read_mmio(unsigned char *val_ab, unsigned char *val_ad, unsigned char *val_temp) {
    int fd = open("/dev/mem", O_RDONLY | O_SYNC);
    if (fd < 0) return -1;

    void *map = mmap(NULL, 4096, PROT_READ, MAP_SHARED, fd, MMIO_BASE_ADDR);
    if (map != MAP_FAILED) {
        volatile unsigned char *regs = (volatile unsigned char *)map;
        if (val_ab) *val_ab = regs[MMIO_OFFSET + MMIO_REG_AB];
        if (val_ad) *val_ad = regs[MMIO_OFFSET + MMIO_REG_AD];
        if (val_temp) *val_temp = regs[MMIO_OFFSET + 0xB0];
        munmap(map, 4096);
        close(fd);
        return 0;
    }
    close(fd);
    return -1;
}

static void set_platform_profile(const char *profile) {
    write_file("/sys/firmware/acpi/platform_profile", profile);
}

static void set_fan_mode(const char *val) {
    write_file("/sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/fan_mode", val);
    write_file("/sys/bus/platform/devices/VPC2004:00/fan_mode", val);
}

static void set_rapl(const char *pl1, const char *pl2) {
    write_file("/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_power_limit_uw", pl1);
    write_file("/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_1_power_limit_uw", pl2);
}

static void set_epp(const char *epp) {
    glob_t gl;
    if (glob("/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference", 0, NULL, &gl) == 0) {
        for (size_t i = 0; i < gl.gl_pathc; ++i) {
            write_file(gl.gl_pathv[i], epp);
        }
        globfree(&gl);
    }
}

static void set_conservation(int enable) {
    const char *v = enable ? "1" : "0";
    write_file("/sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/conservation_mode", v);
    write_file("/sys/bus/platform/devices/VPC2004:00/conservation_mode", v);
}

static void set_fn_lock(int enable) {
    const char *v = enable ? "1" : "0";
    write_file("/sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/fn_lock", v);
    write_file("/sys/bus/platform/devices/VPC2004:00/fn_lock", v);
}

static void toggle_camera(int enable) {
    if (enable) {
        system("/sbin/modprobe uvcvideo >/dev/null 2>&1 || /usr/bin/modprobe uvcvideo >/dev/null 2>&1");
    } else {
        system("/sbin/modprobe -r uvcvideo >/dev/null 2>&1 || /usr/bin/modprobe -r uvcvideo >/dev/null 2>&1");
    }
}

static void fix_permissions(void) {
    chmod("/sys/firmware/acpi/platform_profile", 0666);
    chmod("/sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/fan_mode", 0666);
    chmod("/sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/conservation_mode", 0666);
    chmod("/sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/fn_lock", 0666);
    chmod("/sys/bus/platform/devices/VPC2004:00/fan_mode", 0666);
    chmod("/sys/bus/platform/devices/VPC2004:00/conservation_mode", 0666);
    chmod("/sys/bus/platform/devices/VPC2004:00/fn_lock", 0666);
    chmod("/proc/acpi/call", 0666);
    chmod("/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_power_limit_uw", 0666);
    chmod("/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_1_power_limit_uw", 0666);
    chmod("/sys/kernel/debug", 0755);
    chmod("/sys/kernel/debug/ec/ec0/io", 0666);
    chmod("/dev/hidraw0", 0666);
    chmod("/dev/hidraw1", 0666);
    chmod("/dev/hidraw2", 0666);
    chmod("/dev/hidraw3", 0666);
    chmod("/dev/input/event11", 0666);
    chmod("/sys/devices/system/cpu/intel_pstate/no_turbo", 0666);

    glob_t gl;
    if (glob("/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference", 0, NULL, &gl) == 0) {
        for (size_t i = 0; i < gl.gl_pathc; ++i) chmod(gl.gl_pathv[i], 0666);
        globfree(&gl);
    }
    if (glob("/sys/devices/system/cpu/cpu*/power/energy_perf_bias", 0, NULL, &gl) == 0) {
        for (size_t i = 0; i < gl.gl_pathc; ++i) chmod(gl.gl_pathv[i], 0666);
        globfree(&gl);
    }

    // Ensure battery charging is unblocked (clear battery firmware flash mode)
    call_acpi("\\_SB.PC00.LPCB.EC0.VPC0.MHCF 0");
    call_acpi("\\_SB.PC00.LPCB.EC0.VPC0.SBMC 0x05");
    call_acpi("\\_SB.PC00.LPCB.EC0.VPC0.SBMC 0x06");
    call_acpi("\\_SB.PC00.LPCB.EC0.VPC0.SBMC 0x00");
}

int main(int argc, char *argv[]) {
    // Elevate to root
    if (setuid(0) != 0 || setgid(0) != 0) {
        // Continue even if setuid fails (e.g. running under sudo)
    }

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <action> [args...]\n", argv[0]);
        return 1;
    }

    const char *action = argv[1];

    if (strcmp(action, "fan-extreme") == 0) {
        call_acpi("\\_SB.GZFD.WMAA 0 0x0D 1");
        call_acpi("\\_SB.GZFD.WMAA 0 0x2C 3");
        call_acpi("\\_SB.GZFD.WMAA 0 0x39 5");
        set_fan_mode("2");
        set_platform_profile("performance");
        set_rapl("65000000", "95000000");
        set_epp("performance");
        usleep(40000);
        write_mmio(0x79, 0xFF);
        printf("OK: fan-extreme applied\n");
    }
    else if (strcmp(action, "fan-dust-burst") == 0) {
        call_acpi("\\_SB.GZFD.WMAA 0 0x0D 1");
        call_acpi("\\_SB.GZFD.WMAA 0 0x2C 3");
        call_acpi("\\_SB.GZFD.WMAA 0 0x39 5");
        set_fan_mode("2");
        set_platform_profile("performance");
        usleep(25000);
        write_mmio(0x79, 0xFF);
        printf("OK: fan-dust-burst applied\n");
    }
    else if (strcmp(action, "fan-dust-rest") == 0) {
        call_acpi("\\_SB.GZFD.WMAA 0 0x2C 2");
        call_acpi("\\_SB.GZFD.WMAA 0 0x39 0");
        set_fan_mode("0");
        set_platform_profile("balanced");
        usleep(40000);
        write_mmio(0x39, 0x11);
        printf("OK: fan-dust-rest applied\n");
    }
    else if (strcmp(action, "fan-standard") == 0) {
        call_acpi("\\_SB.GZFD.WMAA 0 0x2C 2");
        call_acpi("\\_SB.GZFD.WMAA 0 0x39 0");
        set_fan_mode("0");
        set_platform_profile("balanced");
        set_rapl("45000000", "65000000");
        set_epp("balance_power");
        usleep(40000);
        write_mmio(0x39, 0x22);
        printf("OK: fan-standard applied\n");
    }
    else if (strcmp(action, "fan-silent") == 0) {
        call_acpi("\\_SB.GZFD.WMAA 0 0x2C 1");
        call_acpi("\\_SB.GZFD.WMAA 0 0x39 0");
        set_fan_mode("0");
        set_platform_profile("balanced");
        set_rapl("30000000", "40000000");
        set_epp("power");
        usleep(40000);
        write_mmio(0x39, 0x11);
        printf("OK: fan-silent applied\n");
    }
    else if (strcmp(action, "profile") == 0 && argc >= 3) {
        const char *p = argv[2];
        if (strcmp(p, "quiet") == 0 || strcmp(p, "low-power") == 0) {
            set_platform_profile("low-power");
            call_acpi("\\_SB.GZFD.WMAA 0 0x2C 1");
            set_rapl("35000000", "45000000");
            set_epp("power");
            set_fan_mode("1");
        } else if (strcmp(p, "performance") == 0) {
            set_platform_profile("performance");
            call_acpi("\\_SB.GZFD.WMAA 0 0x2C 3");
            call_acpi("\\_SB.GZFD.WMAA 0 0x39 5");
            set_rapl("65000000", "95000000");
            set_epp("performance");
            set_fan_mode("4");
        } else {
            set_platform_profile("balanced");
            call_acpi("\\_SB.GZFD.WMAA 0 0x2C 2");
            call_acpi("\\_SB.GZFD.WMAA 0 0x39 0");
            set_rapl("45000000", "65000000");
            set_epp("balance_power");
            set_fan_mode("0");
        }
        printf("OK: profile %s applied\n", p);
    }
    else if (strcmp(action, "camera") == 0 && argc >= 3) {
        toggle_camera(strcmp(argv[2], "on") == 0);
        printf("OK: camera %s applied\n", argv[2]);
    }
    else if (strcmp(action, "conservation") == 0 && argc >= 3) {
        set_conservation(strcmp(argv[2], "on") == 0);
        printf("OK: conservation %s applied\n", argv[2]);
    }
    else if (strcmp(action, "fn-lock") == 0 && argc >= 3) {
        set_fn_lock(strcmp(argv[2], "on") == 0);
        printf("OK: fn-lock %s applied\n", argv[2]);
    }
    else if (strcmp(action, "battery-unblock") == 0) {
        call_acpi("\\_SB.PC00.LPCB.EC0.VPC0.MHCF 0");
        call_acpi("\\_SB.PC00.LPCB.EC0.VPC0.SBMC 0x05");
        call_acpi("\\_SB.PC00.LPCB.EC0.VPC0.SBMC 0x06");
        call_acpi("\\_SB.PC00.LPCB.EC0.VPC0.SBMC 0x00");
        set_conservation(0);
        printf("OK: battery charge unblocked\n");
    }
    else if (strcmp(action, "overdrive") == 0 && argc >= 3) {
        int val = atoi(argv[2]);
        if (val < 0) val = 0;
        if (val > 2) val = 2;
        char cmd[64];
        snprintf(cmd, sizeof(cmd), "\\_SB.SSFM 0 %d", val);
        call_acpi(cmd);
        call_acpi("\\_SB.SSFM 1 0");
        printf("OK: overdrive %d applied\n", val);
    }
    else if (strcmp(action, "rapid-charge") == 0 && argc >= 3) {
        if (strcmp(argv[2], "on") == 0 || strcmp(argv[2], "1") == 0) {
            call_acpi("\\_SB.PC00.LPCB.EC0.VPC0.SBMC 0x07");
            printf("OK: rapid-charge on applied\n");
        } else {
            call_acpi("\\_SB.PC00.LPCB.EC0.VPC0.SBMC 0x08");
            printf("OK: rapid-charge off applied\n");
        }
    }
    else if (strcmp(action, "no-turbo") == 0 && argc >= 3) {
        if (strcmp(argv[2], "on") == 0 || strcmp(argv[2], "1") == 0) {
            write_file("/sys/devices/system/cpu/intel_pstate/no_turbo", "1");
            printf("OK: no-turbo on applied\n");
        } else {
            write_file("/sys/devices/system/cpu/intel_pstate/no_turbo", "0");
            printf("OK: no-turbo off applied\n");
        }
    }
    else if (strcmp(action, "rgb-owner") == 0 && argc >= 3) {
        if (strcmp(argv[2], "app") == 0 || strcmp(argv[2], "1") == 0) {
            call_acpi("\\_SB.GZFD.WMAA 0 0x34 1");
            printf("OK: rgb-owner app applied\n");
        } else {
            call_acpi("\\_SB.GZFD.WMAA 0 0x34 0");
            printf("OK: rgb-owner bios applied\n");
        }
    }
    else if (strcmp(action, "wifi-powersave") == 0 && argc >= 3) {
        if (strcmp(argv[2], "off") == 0 || strcmp(argv[2], "0") == 0) {
            system("/usr/bin/iw dev wlan0 set power_save off >/dev/null 2>&1 || iw dev wlan0 set power_save off >/dev/null 2>&1");
            printf("OK: wifi-powersave off applied\n");
        } else {
            system("/usr/bin/iw dev wlan0 set power_save on >/dev/null 2>&1 || iw dev wlan0 set power_save on >/dev/null 2>&1");
            printf("OK: wifi-powersave on applied\n");
        }
    }
    else if (strcmp(action, "fan-level") == 0 && argc >= 3) {
        int level = atoi(argv[2]);
        if (level < 0) level = 0;
        if (level > 15) level = 15;
        unsigned char ad = (level << 4) | (level & 0x0F);
        unsigned char ab;
        if (level >= 13) {
            ab = 0x79;
            call_acpi("\\_SB.GZFD.WMAA 0 0x0D 1");
            call_acpi("\\_SB.GZFD.WMAA 0 0x2C 3");
            call_acpi("\\_SB.GZFD.WMAA 0 0x39 5");
            if (level >= 15) {
                set_fan_mode("2");
            } else {
                set_fan_mode("0");
            }
            set_platform_profile("performance");
            set_rapl("65000000", "95000000");
            set_epp("performance");
        } else if (level >= 7) {
            ab = 0x39;
            call_acpi("\\_SB.GZFD.WMAA 0 0x2C 2");
            call_acpi("\\_SB.GZFD.WMAA 0 0x39 0");
            set_fan_mode("0");
            set_platform_profile("balanced");
            set_rapl("45000000", "65000000");
            set_epp("balance_power");
        } else if (level >= 3) {
            ab = 0x39;
            call_acpi("\\_SB.GZFD.WMAA 0 0x2C 2");
            set_fan_mode("0");
            set_platform_profile("balanced");
            set_rapl("40000000", "55000000");
            set_epp("balance_power");
        } else {
            ab = 0x39;
            call_acpi("\\_SB.GZFD.WMAA 0 0x2C 1");
            set_fan_mode("0");
            set_platform_profile("balanced");
            set_rapl("30000000", "40000000");
            set_epp("power");
        }
        usleep(40000);
        write_mmio(ab, ad);
        printf("OK: fan-level %d (0x%02X, 0x%02X) applied\n", level, ab, ad);
    }
    else if (strcmp(action, "read-ec") == 0) {
        unsigned char ab = 0, ad = 0, temp = 0;
        if (read_mmio(&ab, &ad, &temp) == 0) {
            int fan1 = ad & 0x0F;
            int fan2 = (ad >> 4) & 0x0F;
            printf("{\"status\": \"ok\", \"mode_ab\": %d, \"level_fan1\": %d, \"level_fan2\": %d, \"ec_temp\": %d}\n",
                   ab, fan1, fan2, temp);
        } else {
            printf("{\"status\": \"error\"}\n");
        }
    }
    else if (strcmp(action, "fix-perms") == 0) {
        fix_permissions();
        printf("OK: permissions fixed\n");
    }
    else {
        fprintf(stderr, "Unknown action: %s\n", action);
        return 1;
    }

    return 0;
}
