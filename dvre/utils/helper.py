import logging
import os
import sys
import time

import psutil
from dotenv import load_dotenv

from dvre.utils.types import Resolve

log = logging.getLogger(__name__)

load_dotenv()

RESOLVE_EXE = os.getenv(
    "RESOLVE_EXE",
    r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
)

RESOLVE_API = os.getenv(
    "RESOLVE_SCRIPT_API",
    r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
)

RESOLVE_LIB = os.getenv(
    "RESOLVE_SCRIPT_LIB",
    r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
)


def ensure_resolve_running() -> None:
    """Ensure DaVinci Resolve is running, start it if not."""
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] == "Resolve.exe":
                log.info("Resolve already running")
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    log.info("Starting Resolve...")
    import subprocess
    subprocess.Popen([RESOLVE_EXE, "-nogui"])


def get_resolve(timeout: int = 120) -> Resolve:
    """Connect to the DaVinci Resolve scripting API."""
    ensure_resolve_running()

    if RESOLVE_API not in sys.path:
        sys.path.append(RESOLVE_API)

    if RESOLVE_LIB not in sys.path:
        sys.path.append(RESOLVE_LIB)

    import DaVinciResolveScript as dvr  # type: ignore

    start = time.time()
    while time.time() - start < timeout:
        resolve: Resolve = dvr.scriptapp("Resolve")
        if resolve:
            log.info("Connected to Resolve")
            return resolve
        time.sleep(1)
        log.debug("Waiting for Resolve...")

    raise TimeoutError(f"Resolve didn't start in {timeout} seconds")
