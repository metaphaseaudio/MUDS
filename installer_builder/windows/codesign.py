import logging
import shutil
from pathlib import Path

from ..util import run

logger = logging.getLogger(__name__)

KNOWN_SIGNTOOL_PATHS = [
    Path(r"C:\Program Files (x86)\Windows Kits\10\App Certification Kit\signtool.exe"),
    Path(r"C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"),
]


def _find_signtool() -> str:
    for candidate in KNOWN_SIGNTOOL_PATHS:
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("signtool")
    if found:
        return found
    raise FileNotFoundError(
        "signtool.exe not found in known SDK paths or on PATH. "
        "Install the Windows SDK or add signtool.exe to PATH."
    )


def sign_executable(exe_path: Path, signing_cert: str) -> None:
    logger.info("Signing %s with certificate %s", exe_path, signing_cert)
    signtool = _find_signtool()
    run([signtool, "sign", "/fd", "SHA256", "/f", signing_cert, str(exe_path)])
    logger.info("Successfully signed %s", exe_path)
