"""
System control skill — hardware stats, app launcher, URL opening, volume control.
All functions use Windows-native APIs (no Linux commands).
"""

import os
import subprocess
import webbrowser
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
    "brave": "brave.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
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
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "telegram": "telegram.exe",
    "whatsapp": "whatsapp.exe",
    "slack": "slack.exe",
    "obs": "obs64.exe",
    "steam": "steam.exe",
    "vlc": "vlc.exe",
    "media player": "wmplayer.exe",
    "snipping tool": "snippingtool.exe",
    "clock": "ms-clock:",
    "alarm": "ms-clock:",
    "calendar": "outlookcal:",
    "mail": "outlookmail:",
    "maps": "bingmaps:",
    "camera": "microsoft.windows.camera:",
    "store": "ms-windows-store:",
    "xbox": "xbox:",
}

# Common website shortcuts — maps friendly names to URLs
_SITE_MAP: dict[str, str] = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "chatgpt": "https://chat.openai.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "linkedin": "https://www.linkedin.com",
    "whatsapp web": "https://web.whatsapp.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "wikipedia": "https://www.wikipedia.org",
    "spotify": "https://open.spotify.com",
    "twitch": "https://www.twitch.tv",
    "figma": "https://www.figma.com",
    "notion": "https://www.notion.so",
    "drive": "https://drive.google.com",
    "google drive": "https://drive.google.com",
    "docs": "https://docs.google.com",
    "sheets": "https://sheets.google.com",
    "maps": "https://maps.google.com",
    "google maps": "https://maps.google.com",
    "news": "https://news.google.com",
    "translate": "https://translate.google.com",
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
        if executable.startswith("ms-") or executable.endswith(":"):
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


def open_url(url: str) -> str:
    """Open a URL in the default web browser.

    Args:
        url: The full URL to open (must start with http:// or https://).

    Returns:
        Confirmation message.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        webbrowser.open(url)
        return f"Opened {url} in your browser."
    except Exception as exc:
        return f"Failed to open URL: {exc}"


def open_website(site_name: str) -> str:
    """Open a known website by friendly name (e.g., 'youtube', 'github').

    Args:
        site_name: Friendly name of the website.

    Returns:
        Confirmation message or error if site not recognised.
    """
    key = site_name.strip().lower()
    url = _SITE_MAP.get(key)

    if url:
        return open_url(url)

    # If not in the map, try as a direct domain
    if "." in site_name:
        return open_url(site_name)

    # Try as a .com domain
    return open_url(f"https://www.{key}.com")


def search_google(query: str) -> str:
    """Open a Google search in the default browser.

    Args:
        query: The search query.

    Returns:
        Confirmation message.
    """
    import urllib.parse
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    return f"Searching Google for: {query}"


def search_youtube(query: str) -> str:
    """Open a YouTube search in the default browser.

    Args:
        query: The search query.

    Returns:
        Confirmation message.
    """
    import urllib.parse
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    webbrowser.open(url)
    return f"Searching YouTube for: {query}"


def set_volume(level: int) -> str:
    """Attempt to set the system volume (0-100).

    Uses ``pycaw`` if available; otherwise returns a friendly skip message.

    Args:
        level: Desired volume level (0-100).

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
        # pycaw uses scalar 0.0-1.0
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level}%."
    except ImportError:
        return (
            f"Volume control requires the `pycaw` package. "
            f"Install it with: pip install pycaw comtypes"
        )
    except Exception as exc:
        return f"Volume control failed: {exc}"
