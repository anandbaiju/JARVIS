"""
System control skill — hardware stats, app launcher, volume control.
All functions use Windows-native APIs (no Linux commands).
"""

import os
import subprocess
from typing import Optional

import psutil


# Map friendly names to Windows executables / commands
_APP_MAP: dict[str, str] = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "files": "explorer.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "terminal": "cmd.exe",
    "powershell": "powershell.exe",
    "vscode": "code",
    "vs code": "code",
    "code": "code",
    "task manager": "taskmgr.exe",
    "settings": "ms-settings:",
    "paint": "mspaint.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
}


def get_system_info() -> str:
    """Return current system stats: CPU, RAM, disk usage on C:\\.

    Returns:
        Formatted multi-line string with system statistics.
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")

    ram_used_gb = mem.used / (1024 ** 3)
    ram_total_gb = mem.total / (1024 ** 3)
    disk_used_gb = disk.used / (1024 ** 3)
    disk_total_gb = disk.total / (1024 ** 3)

    return (
        f"System Diagnostics:\n"
        f"  CPU Usage:  {cpu_percent}%\n"
        f"  RAM:        {ram_used_gb:.1f} GB / {ram_total_gb:.1f} GB ({mem.percent}%)\n"
        f"  Disk (C:):  {disk_used_gb:.1f} GB / {disk_total_gb:.1f} GB ({disk.percent}%)\n"
        f"  Processes:  {len(psutil.pids())} running"
    )


def open_app(app_name: str) -> str:
    """Launch a Windows application by friendly name.

    Args:
        app_name: Human-readable app name (e.g., ``"chrome"``, ``"notepad"``).

    Returns:
        Confirmation message or error string.
    """
    key = app_name.strip().lower()
    executable = _APP_MAP.get(key)

    if executable is None:
        # Try launching directly — user might have provided the actual executable
        executable = app_name.strip()

    try:
        # For UWP / URI-based apps like Settings
        if executable.startswith("ms-"):
            os.startfile(executable)
        else:
            subprocess.Popen(
                executable,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return f"Launched {app_name} successfully."
    except FileNotFoundError:
        return f"Could not find application: {app_name}. Verify it's installed and in PATH."
    except OSError as exc:
        return f"Failed to launch {app_name}: {exc}"


def set_volume(level: int) -> str:
    """Attempt to set the system volume (0–100).

    Uses ``pycaw`` if available; otherwise returns a friendly skip message.

    Args:
        level: Desired volume level (0–100).

    Returns:
        Confirmation or skip message.
    """
    level = max(0, min(100, level))

    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        # pycaw uses scalar 0.0–1.0
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level}%."
    except ImportError:
        return (
            f"Volume control requires the `pycaw` package. "
            f"Install it with: pip install pycaw comtypes"
        )
    except Exception as exc:
        return f"Volume control failed: {exc}"
