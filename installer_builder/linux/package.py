import logging
import platform
import shutil
import subprocess as sp
import tempfile
from pathlib import Path

from ..plugin_build_config import PluginBuildConfig
from ..util import run

logger = logging.getLogger(__name__)

VST3_INSTALL_DIR = Path("/usr/lib/vst3")


def _detect_arch() -> str:
    """Return the machine architecture string (e.g. 'x86_64', 'aarch64')."""
    return platform.machine()


def _deb_arch() -> str:
    """Return the Debian architecture string, falling back to 'amd64'."""
    try:
        result = sp.run(
            ["dpkg", "--print-architecture"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (FileNotFoundError, sp.CalledProcessError):
        return "amd64"


# ---------------------------------------------------------------------------
# .deb
# ---------------------------------------------------------------------------

def _build_deb(
    cfg: PluginBuildConfig,
    bundle_path: Path,
    arch: str,
    output_dir: Path,
) -> Path | None:
    """Build a .deb package. Returns the path on success, None if skipped."""
    if not shutil.which("dpkg-deb"):
        logger.warning("dpkg-deb not found — skipping .deb creation")
        return None

    logger.info("Creating .deb package…")
    deb_arch = _deb_arch()
    pkg_name = cfg.plugin_name.lower()

    with tempfile.TemporaryDirectory() as tmp:
        deb_root = Path(tmp)
        debian_dir = deb_root / "DEBIAN"
        vst3_dest = deb_root / "usr" / "lib" / "vst3"

        debian_dir.mkdir(parents=True)
        vst3_dest.mkdir(parents=True)

        shutil.copytree(bundle_path, vst3_dest / bundle_path.name, dirs_exist_ok=True)

        control = f"""\
Package: {pkg_name}
Version: {cfg.version}
Section: sound
Priority: optional
Architecture: {deb_arch}
Maintainer: {cfg.company_name} <support@metaphase.io>
Description: {cfg.plugin_name} VST3 Plugin
 A VST3 audio plugin by {cfg.company_name}.
"""
        (debian_dir / "control").write_text(control)

        # Fix permissions
        debian_dir.chmod(0o755)
        for p in (deb_root / "usr").rglob("*"):
            if p.is_dir():
                p.chmod(0o755)

        deb_file = output_dir / f"{cfg.plugin_name}-{cfg.version}-linux-{arch}.deb"
        run(["dpkg-deb", "--build", str(deb_root), str(deb_file)])

    logger.info("Created .deb: %s", deb_file)
    return deb_file


# ---------------------------------------------------------------------------
# .rpm
# ---------------------------------------------------------------------------

def _build_rpm(
    cfg: PluginBuildConfig,
    bundle_path: Path,
    output_dir: Path,
) -> Path | None:
    """Build an .rpm package. Returns the path on success, None if skipped."""
    if not shutil.which("rpmbuild"):
        logger.warning("rpmbuild not found — skipping .rpm creation")
        return None

    logger.info("Creating .rpm package…")

    with tempfile.TemporaryDirectory() as tmp:
        rpm_root = Path(tmp)
        for sub in ("BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"):
            (rpm_root / sub).mkdir()

        # Create source tarball
        tarball_dir = rpm_root / "SOURCES" / f"{cfg.plugin_name}-{cfg.version}"
        vst3_dest = tarball_dir / "usr" / "lib" / "vst3"
        vst3_dest.mkdir(parents=True)
        shutil.copytree(bundle_path, vst3_dest / bundle_path.name, dirs_exist_ok=True)

        run(
            [
                "tar", "czf",
                f"{cfg.plugin_name}-{cfg.version}.tar.gz",
                f"{cfg.plugin_name}-{cfg.version}",
            ],
            cwd=rpm_root / "SOURCES",
        )

        # Write spec file
        spec = f"""\
Name: {cfg.plugin_name}
Version: {cfg.version}
Release: 1%{{?dist}}
Summary: {cfg.plugin_name} VST3 Plugin
License: Proprietary
Source0: %{{name}}-%{{version}}.tar.gz

%description
A VST3 audio plugin by {cfg.company_name}.

%prep
%setup -q

%install
mkdir -p %{{buildroot}}/usr/lib/vst3
cp -R usr/lib/vst3/* %{{buildroot}}/usr/lib/vst3/

%files
/usr/lib/vst3/{cfg.plugin_name}.vst3
"""
        spec_path = rpm_root / "SPECS" / f"{cfg.plugin_name}.spec"
        spec_path.write_text(spec)

        run([
            "rpmbuild",
            "--define", f"_topdir {rpm_root}",
            "-bb", str(spec_path),
        ])

        # Copy resulting RPMs to output
        rpm_files = list((rpm_root / "RPMS").rglob("*.rpm"))
        for rpm in rpm_files:
            dest = output_dir / rpm.name
            shutil.copy2(rpm, dest)
            logger.info("Created .rpm: %s", dest)

        return rpm_files[0] if rpm_files else None


# ---------------------------------------------------------------------------
# .tar.gz (always available)
# ---------------------------------------------------------------------------

def _build_tarball(
    cfg: PluginBuildConfig,
    bundle_path: Path,
    arch: str,
    output_dir: Path,
) -> Path:
    """Create a simple .tar.gz of the VST3 bundle."""
    logger.info("Creating tarball…")
    tarball = output_dir / f"{cfg.plugin_name}-{cfg.version}-linux-{arch}.tar.gz"

    run(
        ["tar", "czf", str(tarball), bundle_path.name],
        cwd=bundle_path.parent,
    )

    logger.info("Created tarball: %s", tarball)
    return tarball


# ---------------------------------------------------------------------------
# install.sh helper
# ---------------------------------------------------------------------------

def _write_install_script(cfg: PluginBuildConfig, output_dir: Path) -> Path:
    """Write a convenience install.sh into the output directory."""
    script = output_dir / "install.sh"
    script.write_text(f"""\
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
VST3_DIR="$HOME/.vst3"

echo "Installing {cfg.plugin_name} VST3 plugin…"

TARBALL=$(find "$SCRIPT_DIR" -name "*.tar.gz" | head -1)

if [ -z "$TARBALL" ]; then
    echo "Error: No tarball found in $SCRIPT_DIR"
    exit 1
fi

mkdir -p "$VST3_DIR"
tar xzf "$TARBALL" -C "$VST3_DIR"

echo "Installation complete!"
echo "Plugin installed to: $VST3_DIR"
echo ""
echo "You may also install system-wide by running:"
echo "  sudo tar xzf $TARBALL -C /usr/lib/vst3/"
""")
    script.chmod(0o755)
    logger.info("Created install script: %s", script)
    return script


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_linux_installer(cfg: PluginBuildConfig, bundle_path: Path) -> Path:
    """Build Linux packages (.deb, .rpm, .tar.gz) for a VST3 plug-in.

    Returns the path to the output directory containing the packages.
    """
    logger.info("Building Linux packages for %s v%s", cfg.plugin_name, cfg.version)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    arch = _detect_arch()

    _build_deb(cfg, bundle_path, arch, cfg.output_dir)
    _build_rpm(cfg, bundle_path, cfg.output_dir)
    _build_tarball(cfg, bundle_path, arch, cfg.output_dir)
    _write_install_script(cfg, cfg.output_dir)

    logger.info("Done — Linux packages at: %s", cfg.output_dir)
    return cfg.output_dir
