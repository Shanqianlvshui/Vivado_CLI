from __future__ import annotations

import ctypes
import re
import sys
import time
from collections.abc import Iterable, Sequence


def wait_for_vivado_gui(
    *,
    root_pid: int | None,
    extra_pids: Iterable[int] = (),
    title_hints: Sequence[str] = (),
    timeout_seconds: int = 20,
    activate: bool = False,
) -> dict[str, object]:
    deadline = time.monotonic() + max(0, timeout_seconds)
    last_state = probe_vivado_gui(
        root_pid=root_pid,
        extra_pids=extra_pids,
        title_hints=title_hints,
        activate=activate,
    )
    while not last_state.get("visible") and time.monotonic() < deadline:
        time.sleep(0.25)
        last_state = probe_vivado_gui(
            root_pid=root_pid,
            extra_pids=extra_pids,
            title_hints=title_hints,
            activate=activate,
        )
    return last_state


def probe_vivado_gui(
    *,
    root_pid: int | None,
    extra_pids: Iterable[int] = (),
    title_hints: Sequence[str] = (),
    activate: bool = False,
) -> dict[str, object]:
    if sys.platform != "win32":
        return {
            "requested": True,
            "platform": sys.platform,
            "platform_supported": False,
            "visible": None,
            "activated": False,
            "windows": [],
            "detail": "GUI window probing is only implemented on Windows.",
        }

    watched_pids = {int(pid) for pid in extra_pids if int(pid) > 0}
    if root_pid and root_pid > 0:
        watched_pids.update(_process_tree_pids(root_pid))

    windows = _enum_visible_windows()
    matches = [
        window
        for window in windows
        if _matches_vivado_window(window, watched_pids=watched_pids, title_hints=title_hints)
    ]

    activated = False
    if activate and matches:
        activated = _activate_window(int(matches[0]["handle"]))

    if matches:
        detail = f"Matched {len(matches)} visible Vivado GUI window(s)."
        if activate and not activated:
            detail += " Activation was requested, but Windows did not grant foreground focus."
    else:
        detail = "No visible Vivado GUI window matched the managed process or project title hints."

    return {
        "requested": True,
        "platform": sys.platform,
        "platform_supported": True,
        "visible": bool(matches),
        "activated": activated,
        "windows": matches,
        "watched_pids": sorted(watched_pids),
        "title_hints": list(title_hints),
        "detail": detail,
    }


def _matches_vivado_window(
    window: dict[str, object],
    *,
    watched_pids: set[int],
    title_hints: Sequence[str],
) -> bool:
    title = str(window["title"])
    title_lower = title.lower()
    if not _looks_like_vivado_main_window(title) or "license manager" in title_lower:
        return False

    pid = int(window["pid"])
    if watched_pids and pid in watched_pids:
        return True

    normalized_hints = [hint.lower() for hint in title_hints if hint]
    if normalized_hints and any(hint in title_lower for hint in normalized_hints):
        return True

    return False


def _looks_like_vivado_main_window(title: str) -> bool:
    normalized = title.strip()
    if re.search(r"^vivado\s+\d{4}\.\d+(?:\s|$)", normalized, re.IGNORECASE):
        return True
    return bool(re.search(r"\s-\sVivado\s+\d{4}\.\d+\s*$", normalized, re.IGNORECASE))


def _process_tree_pids(root_pid: int) -> set[int]:
    process_entries = _snapshot_processes()
    pids = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent_pid in process_entries:
            if parent_pid in pids and pid not in pids:
                pids.add(pid)
                changed = True
    return pids


def _snapshot_processes() -> list[tuple[int, int]]:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        return []

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("cntUsage", ctypes.c_ulong),
            ("th32ProcessID", ctypes.c_ulong),
            ("th32DefaultHeapID", ctypes.c_void_p),
            ("th32ModuleID", ctypes.c_ulong),
            ("cntThreads", ctypes.c_ulong),
            ("th32ParentProcessID", ctypes.c_ulong),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.c_ulong),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    entries: list[tuple[int, int]] = []
    try:
        has_entry = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while has_entry:
            entries.append((int(entry.th32ProcessID), int(entry.th32ParentProcessID)))
            has_entry = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return entries


def _enum_visible_windows() -> list[dict[str, object]]:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    windows: list[dict[str, object]] = []

    enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        title_length = user32.GetWindowTextLengthW(hwnd)
        if title_length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(title_length + 1)
        user32.GetWindowTextW(hwnd, buffer, title_length + 1)
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        windows.append(
            {
                "handle": int(hwnd),
                "pid": int(pid.value),
                "title": buffer.value,
            }
        )
        return True

    user32.EnumWindows(enum_windows_proc(callback), 0)
    return windows


def _activate_window(handle: int) -> bool:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.ShowWindow(handle, 9)
    user32.BringWindowToTop(handle)
    if user32.SetForegroundWindow(handle):
        return True
    try:
        user32.SwitchToThisWindow(handle, True)
    except AttributeError:
        pass
    time.sleep(0.05)
    return int(user32.GetForegroundWindow()) == handle
