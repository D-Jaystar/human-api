import ctypes
from ctypes import wintypes
import psutil

# Laad de Windows User32 bibliotheek voor interactie met het venstersysteem
user32 = ctypes.windll.user32


def get_active_window_info() -> dict[str, str]:
    """
    Leest het actieve voorgrondvenster op Windows uit.
    Geeft een dictionary terug met de applicatienaam en de venstertitel.

    Voorbeeld:
        {
            'app_name': 'idea64.exe',
            'window_title': 'main.py - human_api'
        }
    """
    # 1. Haal de handle (HWND) op van het venster dat op dit moment focus heeft
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return {
            "app_name": "Desktop",
            "window_title": "Geen actief venster / Bureaublad",
        }

    # 2. Haal de titeltekst van het venster op
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        window_title = buffer.value
    else:
        window_title = "Ongetiteld venster"

    # 3. Haal het Process ID (PID) op van het actieve venster
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    if pid.value == 0:
        return {
            "app_name": "System",
            "window_title": window_title,
        }

    # 4. Zoek via psutil de naam van de executable op (bijv. chrome.exe, code.exe)
    try:
        process = psutil.Process(pid.value)
        app_name = process.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        app_name = "Onbekend proces"

    return {
        "app_name": app_name,
        "window_title": window_title,
    }


if __name__ == "__main__":
    print("Actieve venster informatie:")
    info = get_active_window_info()
    print(f"  Applicatie:   {info['app_name']}")
    print(f"  Venstertitel: {info['window_title']}")
