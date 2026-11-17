import platform
import socket
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Any


def _get_process_ram_mb() -> float:
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return float(round(counters.WorkingSetSize / (1024 * 1024), 2))
        else:
            import resource
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform == "darwin":
                return float(round(rss / (1024 * 1024), 2))
            return float(round(rss / 1024, 2))
    except Exception:
        pass
    return 0.0


@dataclass
class EnvironmentDto:
    app_version: str
    os_name: str
    os_version: str
    device_model: str
    runtime_version: str
    process_ram_mb: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def collect_environment(app_version: str) -> EnvironmentDto:
    device_model = socket.gethostname() or platform.machine() or "unknown"
    return EnvironmentDto(
        app_version=app_version or "0.0.0",
        os_name=platform.system() or "unknown",
        os_version=platform.release() or "unknown",
        device_model=device_model,
        runtime_version=platform.python_version(),
        process_ram_mb=_get_process_ram_mb(),
    )