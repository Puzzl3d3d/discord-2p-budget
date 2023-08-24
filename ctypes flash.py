import ctypes, time

# Define necessary structures
class FLASHWINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("hwnd", ctypes.c_void_p),
                ("dwFlags", ctypes.c_uint),
                ("uCount", ctypes.c_uint),
                ("dwTimeout", ctypes.c_uint)]

hwnd = ctypes.windll.user32.GetForegroundWindow()

# Define function
def flash_window(count=5):
    FLASHW_STOP = 0
    FLASHW_CAPTION = 1
    FLASHW_TRAY = 2
    FLASHW_ALL = 3
    FLASHW_TIMER = 4
    FLASHW_TIMERNOFG = 12

    info = FLASHWINFO(0, hwnd, FLASHW_ALL | FLASHW_TIMERNOFG, count, 0)
    info.cbSize = ctypes.sizeof(info)
    ctypes.windll.user32.FlashWindowEx(ctypes.byref(info))

# Test the function
time.sleep(2)
flash_window()

input("Done")