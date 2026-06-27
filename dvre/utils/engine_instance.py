import logging
import os
import subprocess
import sys
import time

import psutil

from dvre.utils.types import Resolve

log = logging.getLogger(__name__)

RESOLVE_EXE = os.getenv(
    "RESOLVE_EXE", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
)

RESOLVE_API = os.getenv(
    "RESOLVE_SCRIPT_API",
    r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules",
)

RESOLVE_LIB = os.getenv(
    "RESOLVE_SCRIPT_LIB",
    r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll",
)


def ensure_resolve_running() -> bool:
    """Ensure DaVinci Resolve is running, start it if not. Returns True if Resolve was just started."""
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] == "Resolve.exe":
                log.debug("Resolve already running")
                return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    log.info("Starting Resolve...")
    subprocess.Popen([RESOLVE_EXE, "-nogui"])
    return True


def get_resolve(timeout: int = 120) -> Resolve:
    """Connect to the DaVinci Resolve scripting API."""
    fresh_start = ensure_resolve_running()

    if RESOLVE_API not in sys.path:
        sys.path.append(RESOLVE_API)

    if RESOLVE_LIB not in sys.path:
        sys.path.append(RESOLVE_LIB)

    # python version (try all the available versions. check via `py --list`) (as a last resort, use procmon to monitor the dll importing)
    # davinci preferences - enable the scripting
    # studio version required
    # `-nogui` is not the reason (works in gui and no gui version either)
    import DaVinciResolveScript as dvr  # type: ignore

    start = time.time()
    while time.time() - start < timeout:
        resolve: Resolve = dvr.scriptapp("Resolve")
        if resolve:
            log.debug("Connected to Resolve")
            if fresh_start:
                resolve.DisableBackgroundTasksForCurrentResolveSession()
                log.debug("Background tasks disabled for this Resolve session")
            return resolve
        time.sleep(1)
        log.debug("Waiting for Resolve...")

    raise TimeoutError(f"Resolve didn't start in {timeout} seconds")

