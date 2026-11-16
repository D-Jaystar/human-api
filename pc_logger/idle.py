import ctypes
from ctypes import wintypes

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def get_idle_duration_sec() -> float:
    """
    Meet hoeveel seconden het geleden is dat er een toets- of muisinvoer plaatsvond.
    """
    last_input = LASTINPUTINFO()
    last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)

    user32.GetLastInputInfo(ctypes.byref(last_input))

    elapsed_ms = kernel32.GetTickCount() - last_input.dwTime

    return elapsed_ms / 1000.0


def is_user_afk(threshold_sec: int = 180) -> bool:
    """
    Bepaalt of de gebruiker AFK is op basis van een drempelwaarde (standaard 3 min / 180s).
    """
    return get_idle_duration_sec() >= threshold_sec
