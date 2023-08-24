# -- coding: utf-8 --
'''
Module of Windows API for creating taskbar balloon tip
notification in the taskbar's tray notification area.
'''


import time
import ctypes
import atexit
from threading import RLock

''' Defines ctypes windows api.
'''

import ctypes
from ctypes import Structure, windll, sizeof, POINTER, WINFUNCTYPE
from ctypes.wintypes import (
    DWORD, HICON, HWND, UINT, WCHAR, WORD, BYTE,
    LPCWSTR, INT, LPVOID, HINSTANCE, HMENU, LPARAM,
    WPARAM, HBRUSH, HMODULE, ATOM, BOOL, HANDLE
)
LRESULT = LPARAM
HRESULT = HANDLE
HCURSOR = HICON


class GUID(Structure):
    _fields_ = [
        ('Data1', DWORD),
        ('Data2', WORD),
        ('Data3', WORD),
        ('Data4', BYTE * 8)
    ]


class DLLVERSIONINFO(Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('dwMajorVersion', DWORD),
        ('dwMinorVersion', DWORD),
        ('dwBuildNumber', DWORD),
        ('dwPlatformID', DWORD),
    ]


def get_DLLVERSIONINFO(*largs):
    version_info = DLLVERSIONINFO(*largs)
    version_info.cbSize = sizeof(DLLVERSIONINFO)
    return version_info


def MAKEDLLVERULL(major, minor, build, sp):
    return (major << 48) | (minor << 32) | (build << 16) | sp


NOTIFYICONDATAW_fields = [
    ("cbSize", DWORD),
    ("hWnd", HWND),
    ("uID", UINT),
    ("uFlags", UINT),
    ("uCallbackMessage", UINT),
    ("hIcon", HICON),
    ("szTip", WCHAR * 128),
    ("dwState", DWORD),
    ("dwStateMask", DWORD),
    ("szInfo", WCHAR * 256),
    ("uVersion", UINT),
    ("szInfoTitle", WCHAR * 64),
    ("dwInfoFlags", DWORD),
    ("guidItem", GUID),
    ("hBalloonIcon", HICON),
]


class NOTIFYICONDATAW(Structure):
    _fields_ = NOTIFYICONDATAW_fields[:]


class NOTIFYICONDATAW_V3(Structure):
    _fields_ = NOTIFYICONDATAW_fields[:-1]


class NOTIFYICONDATAW_V2(Structure):
    _fields_ = NOTIFYICONDATAW_fields[:-2]


class NOTIFYICONDATAW_V1(Structure):
    _fields_ = NOTIFYICONDATAW_fields[:6]


NOTIFYICONDATA_V3_SIZE = sizeof(NOTIFYICONDATAW_V3)
NOTIFYICONDATA_V2_SIZE = sizeof(NOTIFYICONDATAW_V2)
NOTIFYICONDATA_V1_SIZE = sizeof(NOTIFYICONDATAW_V1)


def get_NOTIFYICONDATAW(*largs):
    notify_data = NOTIFYICONDATAW(*largs)

    # get shell32 version to find correct NOTIFYICONDATAW size
    DllGetVersion = windll.Shell32.DllGetVersion
    DllGetVersion.argtypes = [POINTER(DLLVERSIONINFO)]
    DllGetVersion.restype = HRESULT

    version = get_DLLVERSIONINFO()
    if DllGetVersion(version):
        raise Exception('Cannot get Windows version numbers.')
    v = MAKEDLLVERULL(version.dwMajorVersion, version.dwMinorVersion,
                      version.dwBuildNumber, version.dwPlatformID)

    # from the version info find the NOTIFYICONDATA size
    if v >= MAKEDLLVERULL(6, 0, 6, 0):
        notify_data.cbSize = sizeof(NOTIFYICONDATAW)
    elif v >= MAKEDLLVERULL(6, 0, 0, 0):
        notify_data.cbSize = NOTIFYICONDATA_V3_SIZE
    elif v >= MAKEDLLVERULL(5, 0, 0, 0):
        notify_data.cbSize = NOTIFYICONDATA_V2_SIZE
    else:
        notify_data.cbSize = NOTIFYICONDATA_V1_SIZE
    return notify_data


CreateWindowExW = windll.User32.CreateWindowExW
CreateWindowExW.argtypes = [DWORD, ATOM, LPCWSTR, DWORD, INT, INT, INT, INT,
                            HWND, HMENU, HINSTANCE, LPVOID]
CreateWindowExW.restype = HWND

GetModuleHandleW = windll.Kernel32.GetModuleHandleW
GetModuleHandleW.argtypes = [LPCWSTR]
GetModuleHandleW.restype = HMODULE

WindowProc = WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)
DefWindowProcW = windll.User32.DefWindowProcW
DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
DefWindowProcW.restype = LRESULT


class WNDCLASSEXW(Structure):
    _fields_ = [
        ('cbSize', UINT),
        ('style', UINT),
        ('lpfnWndProc', WindowProc),
        ('cbClsExtra', INT),
        ('cbWndExtra', INT),
        ('hInstance', HINSTANCE),
        ('hIcon', HICON),
        ('hCursor', HCURSOR),
        ('hbrBackground', HBRUSH),
        ('lpszMenuName', LPCWSTR),
        ('lpszClassName', LPCWSTR),
        ('hIconSm', HICON),
    ]


def get_WNDCLASSEXW(*largs):
    wnd_class = WNDCLASSEXW(*largs)
    wnd_class.cbSize = sizeof(WNDCLASSEXW)
    return wnd_class


RegisterClassExW = windll.User32.RegisterClassExW
RegisterClassExW.argtypes = [POINTER(WNDCLASSEXW)]
RegisterClassExW.restype = ATOM

UpdateWindow = windll.User32.UpdateWindow
UpdateWindow.argtypes = [HWND]
UpdateWindow.restype = BOOL

LoadImageW = windll.User32.LoadImageW
LoadImageW.argtypes = [HINSTANCE, LPCWSTR, UINT, INT, INT, UINT]
LoadImageW.restype = HANDLE

Shell_NotifyIconW = windll.Shell32.Shell_NotifyIconW
Shell_NotifyIconW.argtypes = [DWORD, POINTER(NOTIFYICONDATAW)]
Shell_NotifyIconW.restype = BOOL

DestroyIcon = windll.User32.DestroyIcon
DestroyIcon.argtypes = [HICON]
DestroyIcon.restype = BOOL

UnregisterClassW = windll.User32.UnregisterClassW
UnregisterClassW.argtypes = [ATOM, HINSTANCE]
UnregisterClassW.restype = BOOL

DestroyWindow = windll.User32.DestroyWindow
DestroyWindow.argtypes = [HWND]
DestroyWindow.restype = BOOL

LoadIconW = windll.User32.LoadIconW
LoadIconW.argtypes = [HINSTANCE, LPCWSTR]
LoadIconW.restype = HICON


class SYSTEM_POWER_STATUS(Structure):
    _fields_ = [
        ('ACLineStatus', BYTE),
        ('BatteryFlag', BYTE),
        ('BatteryLifePercent', BYTE),
        ('Reserved1', BYTE),
        ('BatteryLifeTime', DWORD),
        ('BatteryFullLifeTime', DWORD),
    ]


SystemPowerStatusP = POINTER(SYSTEM_POWER_STATUS)

GetSystemPowerStatus = windll.kernel32.GetSystemPowerStatus
GetSystemPowerStatus.argtypes = [SystemPowerStatusP]
GetSystemPowerStatus.restype = BOOL


class GUID_(Structure):
    _fields_ = [
        ('Data1', DWORD),
        ('Data2', WORD),
        ('Data3', WORD),
        ('Data4', BYTE * 8)
    ]

    def __init__(self, uuid_):
        Structure.__init__(self)
        self.Data1, self.Data2, self.Data3, self.Data4[0], self.Data4[1], rest\
            = uuid_.fields
        for i in range(2, 8):
            self.Data4[i] = rest >> (8 - i - 1) * 8 & 0xff


_CoTaskMemFree = windll.ole32.CoTaskMemFree
_CoTaskMemFree.restype = None
_CoTaskMemFree.argtypes = [ctypes.c_void_p]

_SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
_SHGetKnownFolderPath.argtypes = [
    POINTER(GUID_),
    DWORD,
    HANDLE,
    POINTER(ctypes.c_wchar_p)
]


class PathNotFoundException(Exception):
    pass


def get_PATH(folderid):
    fid = GUID_(folderid)
    pPath = ctypes.c_wchar_p()
    S_OK = 0
    Result = _SHGetKnownFolderPath(ctypes.byref(fid),
                                   0, None, ctypes.byref(pPath))
    if Result != S_OK:
        raise PathNotFoundException()
    path = pPath.value
    _CoTaskMemFree(pPath)
    return path


WS_OVERLAPPED = 0x00000000
WS_SYSMENU = 0x00080000
WM_DESTROY = 2
CW_USEDEFAULT = 8

LR_LOADFROMFILE = 16
LR_DEFAULTSIZE = 0x0040
IDI_APPLICATION = 32512
IMAGE_ICON = 1

NOTIFYICON_VERSION_4 = 4
NIM_ADD = 0
NIM_MODIFY = 1
NIM_DELETE = 2
NIM_SETVERSION = 4
NIF_MESSAGE = 1
NIF_ICON = 2
NIF_TIP = 4
NIF_INFO = 0x10
NIIF_USER = 4
NIIF_LARGE_ICON = 0x20


class WindowsBalloonTip:
    '''
    Implementation of balloon tip notifications through Windows API.

    * Register Window class name:
      https://msdn.microsoft.com/en-us/library/windows/desktop/ms632596.aspx
    * Create an overlapped window using the registered class.
      - It's hidden everywhere in GUI unless ShowWindow(handle, SW_SHOW)
        function is called.
    * Show/remove a tray icon and a balloon tip notification.

    Each instance is a separate notification with different parameters.
    Can be used with Threads.
    '''

    _class_atom = 0
    _wnd_class_ex = None
    _hwnd = None
    _hicon = None
    _balloon_icon = None
    _notify_data = None
    _count = 0
    _lock = RLock()

    @staticmethod
    def _get_unique_id():
        '''
        Keep track of each created balloon tip notification names,
        so that they can be easily identified even from outside.

        Make sure the count is shared between all the instances
        i.e. use a lock, so that _count class variable is incremented
        safely when using balloon tip notifications with Threads.
        '''

        WindowsBalloonTip._lock.acquire()
        val = WindowsBalloonTip._count
        WindowsBalloonTip._count += 1
        WindowsBalloonTip._lock.release()
        return val

    def __init__(self, title, message, app_name, app_icon='',
                 timeout=10, **kwargs):
        '''
        The app_icon parameter, if given, is an .ICO file.
        '''
        atexit.register(self.__del__)

        wnd_class_ex = get_WNDCLASSEXW()
        class_name = 'PlyerTaskbar' + str(WindowsBalloonTip._get_unique_id())

        wnd_class_ex.lpszClassName = class_name

        # keep ref to it as long as window is alive
        wnd_class_ex.lpfnWndProc = WindowProc(
            DefWindowProcW
        )
        wnd_class_ex.hInstance = GetModuleHandleW(None)
        if wnd_class_ex.hInstance is None:
            raise Exception('Could not get windows module instance.')

        class_atom = RegisterClassExW(wnd_class_ex)
        if class_atom == 0:
            raise Exception('Could not register the PlyerTaskbar class.')

        self._class_atom = class_atom
        self._wnd_class_ex = wnd_class_ex

        # create window
        self._hwnd = CreateWindowExW(
            # dwExStyle, lpClassName, lpWindowName, dwStyle
            0, class_atom, '', WS_OVERLAPPED,
            # x, y, nWidth, nHeight
            0, 0, CW_USEDEFAULT, CW_USEDEFAULT,
            # hWndParent, hMenu, hInstance, lpParam
            None, None, wnd_class_ex.hInstance, None
        )
        if self._hwnd is None:
            raise Exception('Could not get create window.')
        UpdateWindow(self._hwnd)

        # load .ICO file for as balloon tip and tray icon
        if app_icon:
            icon_flags = LR_LOADFROMFILE | LR_DEFAULTSIZE
            hicon = LoadImageW(
                None, app_icon, IMAGE_ICON, 0, 0, icon_flags
            )

            if hicon is None:
                raise Exception('Could not load icon {}'.format(app_icon))
            self._balloon_icon = self._hicon = hicon
        else:
            self._hicon = LoadIconW(
                None,
                ctypes.cast(IDI_APPLICATION, LPCWSTR)
            )

        # show the notification
        self.notify(title, message, app_name)
        if timeout:
            time.sleep(timeout)

    def __del__(self):
        '''
        Clean visible parts of the notification object, then free all resources
        allocated for creating the nofitication Window and icon.
        '''
        self.remove_notify()
        if self._hicon is not None:
            DestroyIcon(self._hicon)
        if self._wnd_class_ex is not None:
            UnregisterClassW(
                self._class_atom,
                self._wnd_class_ex.hInstance
            )
        if self._hwnd is not None:
            DestroyWindow(self._hwnd)

    def notify(self, title, message, app_name):
        '''
        Displays a balloon in the systray. Can be called multiple times
        with different parameter values.
        '''
        # remove previous visible balloon tip nofitication if available
        self.remove_notify()

        # add icon and messages to window
        hicon = self._hicon
        flags = NIF_TIP | NIF_INFO
        icon_flag = 0

        if hicon is not None:
            flags |= NIF_ICON

            # if icon is default app's one, don't display it in message
            if self._balloon_icon is not None:
                icon_flag = NIIF_USER | NIIF_LARGE_ICON

        notify_data = get_NOTIFYICONDATAW(
            0, self._hwnd,
            id(self), flags, 0, hicon, app_name, 0, 0, message,
            NOTIFYICON_VERSION_4, title, icon_flag, GUID(),
            self._balloon_icon
        )

        self._notify_data = notify_data
        if not Shell_NotifyIconW(NIM_ADD, notify_data):
            raise Exception('Shell_NotifyIconW failed.')
        if not Shell_NotifyIconW(NIM_SETVERSION,
                                              notify_data):
            raise Exception('Shell_NotifyIconW failed.')

    def remove_notify(self):
        '''
        Removes the notify balloon, if displayed.
        '''
        if self._notify_data is not None:
            Shell_NotifyIconW(NIM_DELETE, self._notify_data)
            self._notify_data = None


def balloon_tip(**kwargs):
    '''
    Instance for balloon tip notification implementation.
    '''
    WindowsBalloonTip(**kwargs)





a = WindowsBalloonTip("Test", "test", "test app")

a.notify("Test", "test", "test app")