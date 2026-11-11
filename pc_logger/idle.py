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
    last_input = LASTINPUTINFO()
    last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)

    user32.GetLastInputInfo(ctypes.byref(last_input))

    elapsed_ms = kernel32.GetTickCount() - last_input.dwTime

    return elapsed_ms / 1000.0