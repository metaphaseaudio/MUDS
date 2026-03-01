from pathlib import Path
import logging
from ..util import run

logger = logging.getLogger(__name__)

def codesign_bundle(vst3_bundle: Path, apple_developer_id: str | None) -> None:
    logger.info("=== Code Signing ===")
    if apple_developer_id:
        logger.info("Signing with Developer ID: %s", apple_developer_id)
        run([
            "codesign", "--force", "--deep", "--sign", apple_developer_id,
            "--options", "runtime", "--timestamp", str(vst3_bundle),
        ])
    else:
        logger.warning("No APPLE_DEVELOPER_ID set, using ad-hoc signature")
        run(["codesign", "--force", "--deep", "--sign", "-", str(vst3_bundle)])

