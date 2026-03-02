"""
Entry point for the plugin build configuration tool.

Detects the current platform, gathers system information, and constructs
a PluginBuildConfig via CLI arguments.

Usage:
    python -m plugin_build --company "Acme Audio" --plugin "SuperFuzz" --version "1.2.0"
"""
import argparse
import logging
import platform
import subprocess
import sys
from typing import Dict
from pathlib import Path
from .build import build
from .linux import build_linux_installer
from .macos import build_macos_installer
from .windows import build_windows_installer
from .plugin_build_config import PluginBuildConfig

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Platform detection helpers
# ---------------------------------------------------------------------------

_PLATFORM_OUTPUT_MAP: Dict[str, Path] = {
    "darwin": Path("./installers/macos"),
    "windows": Path("./installers/windows"),
    "linux": Path("./installers/linux"),
}

DEFAULT_VST3_INSTALL_LOCATIONS: Dict[str, Path] = {
    "darwin": Path("~/Library/Audio/Plug-Ins/VST3"),
    "windows": Path("C:/Program Files/Common Files/VST3"),
    "linux": Path("/usr/lib/vst3"),
}

def _detect_platform() -> str:
    """Return a normalized platform key: 'darwin', 'windows', or 'linux'."""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    if system == "windows":
        return "windows"
    # Treat everything else as Linux-like
    return "linux"


def _default_output_dir(platform_key: str) -> Path:
    """Return the conventional installer output directory for the given platform."""
    return _PLATFORM_OUTPUT_MAP[platform_key]

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plugin_build",
        description="Populate a PluginBuildConfig for the current platform.",
    )

    # --- Required ---
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "--company",
        required=True,
        metavar="NAME",
        help="Company / publisher name (e.g. 'Acme Audio').",
    )
    required.add_argument(
        "--plugin",
        required=True,
        metavar="NAME",
        help="Plugin display name (e.g. 'SuperFuzz').",
    )
    required.add_argument(
        "--version",
        required=True,
        metavar="X.Y.Z",
        help="Semantic version string (e.g. '1.2.0').",
    )

    # --- Paths (optional; sensible defaults are derived at runtime) ---
    path_group = parser.add_argument_group("path overrides")
    path_group.add_argument(
        "--vst3-bundle",
        metavar="PATH",
        default=None,
        help=(
            "Path to the compiled .vst3 bundle. "
            "Defaults to the platform-standard VST3 directory."
        ),
    )
    path_group.add_argument(
        "--presets-source",
        metavar="PATH",
        default=None,
        help="Directory containing factory presets. Defaults to './presets'.",
    )
    path_group.add_argument(
        "--output-dir",
        metavar="PATH",
        default=None,
        help=(
            "Directory in which the installer artefact will be written. "
            "Defaults to './installers/<platform>'."
        ),
    )

    # --- Signing / notarisation ---
    signing_group = parser.add_argument_group("code signing (macOS)")
    signing_group.add_argument(
        "--bundle-id-prefix",
        default="com.metaphaseindustries",
        metavar="PREFIX",
        help="Reverse-DNS prefix for the bundle identifier (default: %(default)s).",
    )
    signing_group.add_argument(
        "--apple-developer-id",
        metavar="TEAM_ID",
        default=None,
        help="Apple Developer Team ID used for notarisation (macOS only).",
    )
    signing_group.add_argument(
        "--signing-identity",
        metavar="IDENTITY",
        default=None,
        help=(
            "Code-signing identity string, e.g. "
            "'Developer ID Application: Acme Audio (XXXXXXXXXX)'."
        ),
    )

    # --- Signing (Windows) ---
    win_signing_group = parser.add_argument_group("code signing (Windows)")
    win_signing_group.add_argument(
        "--signing-cert",
        metavar="PATH",
        default=None,
        help="Path to a .pfx code-signing certificate (Windows only).",
    )

    # --- Web UI / build target ---
    build_group = parser.add_argument_group("build options")
    build_group.add_argument(
        "--skip-web-ui",
        action="store_true",
        help="Skip the web UI build step (for plugins without a webview).",
    )
    build_group.add_argument(
        "--web-dir",
        metavar="PATH",
        default=None,
        help="Path to the web UI source directory. Defaults to src/plugin/gooey/web.",
    )
    build_group.add_argument(
        "--cmake-target",
        metavar="NAME",
        default=None,
        help="CMake build target name. Defaults to '<plugin>_VST3'.",
    )

    # --- Verbosity ---
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )

    return parser


# ---------------------------------------------------------------------------
# Config construction
# ---------------------------------------------------------------------------


def build_config(args: argparse.Namespace, platform_key) -> PluginBuildConfig:
    """Construct a :class:`PluginBuildConfig` from parsed CLI arguments."""
    logger.debug("Detected platform: %s", platform_key)
    presets_source = (
        Path(args.presets_source) if args.presets_source else (Path.cwd() / "presets")
    )
    output_dir = (
        Path(args.output_dir) if args.output_dir else _default_output_dir(platform_key)
    )

    config = PluginBuildConfig(
        company_name=args.company,
        plugin_name=args.plugin,
        version=args.version,
        presets_source=presets_source,
        output_dir=output_dir,
        bundle_id_prefix=args.bundle_id_prefix,
        apple_developer_id=args.apple_developer_id,
        signing_identity=args.signing_identity,
        signing_cert=args.signing_cert,
        skip_web_ui=args.skip_web_ui,
        web_dir=Path(args.web_dir) if args.web_dir else None,
        cmake_target=args.cmake_target,
    )

    logger.debug("Constructed config: %s", config)
    return config


def _warn_if_windows_signing_missing(config: PluginBuildConfig) -> None:
    """Emit a warning when Windows signing certificate is absent."""
    if not config.signing_cert:
        logger.warning(
            "Running on Windows but --signing-cert was not supplied; "
            "the installer will be unsigned."
        )


def _warn_if_macos_signing_missing(config: PluginBuildConfig) -> None:
    """Emit warnings when macOS-specific signing fields are absent on macOS."""
    if not config.apple_developer_id:
        logger.warning(
            "Running on macOS but --apple-developer-id was not supplied; "
            "notarisation will not be possible."
        )
    if not config.signing_identity:
        logger.warning(
            "Running on macOS but --signing-identity was not supplied; "
            "the installer will be unsigned."
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled.")

    logger.info(
        "Platform: %s %s (%s)",
        platform.system(),
        platform.release(),
        platform.machine(),
    )

    platform_name = _detect_platform()
    config = build_config(args, platform_name)

    try:
        bundle_path = build(config)

        if platform_name == "darwin":
            _warn_if_macos_signing_missing(config)
            build_macos_installer(config, bundle_path)
        elif platform_name == "windows":
            _warn_if_windows_signing_missing(config)
            build_windows_installer(config, bundle_path)
        elif platform_name == "linux":
            build_linux_installer(config, bundle_path)

    except subprocess.CalledProcessError as e:
        logger.error("Command failed (exit code %d): %s", e.returncode, e.cmd)
        sys.exit(e.returncode)
    except Exception as e:
        logger.error("%s", e)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
