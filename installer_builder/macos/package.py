import logging
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..eula import make_eula, EULAConfig
from ..util import run
from .codesign import codesign_bundle
from .postinstall_script import write_postinstall_script
from ..plugin_build_config import PluginBuildConfig

logger = logging.getLogger(__name__)

VST3_INSTALL_DIR = Path("/Library/Audio/Plug-Ins/VST3")


@dataclass
class WorkDirs:
    root: Path
    staging_dir: Path
    resources: Path
    scripts: Path
    component_pkg_vst3: Path
    component_pkg_presets: Path
    distribution_xml: Path
    presets_payload_root: Path
    vst3_payload_root: Path

    @staticmethod
    def from_root(root: Path, cfg: PluginBuildConfig):
        resources = root / "resources"
        scripts = root / "scripts"
        resources.mkdir(parents=True)
        scripts.mkdir(parents=True)
        return WorkDirs(
            root=root,
            staging_dir=Path(f"/Library/Application Support/") / cfg.company_name / cfg.plugin_name / "staging",
            resources=resources,
            scripts=scripts,
            component_pkg_vst3=root / "component_vst3.pkg",
            component_pkg_presets=root / "component_presets.pkg",
            distribution_xml=root / "distribution.xml",
            presets_payload_root=root / "presets_payload",
            vst3_payload_root=root / "vst3_payload",
        )


def ensure_vst3_source(vst3_bundle: Path) -> None:
    if not vst3_bundle.exists():
        logger.warning("VST3 not found at '%s' – using stub.", vst3_bundle)
        contents = vst3_bundle / "Contents"
        contents.mkdir(parents=True, exist_ok=True)
        (contents / "stub.txt").write_text("stub")


def ensure_presets_source(presets_source: Path) -> None:
    if not presets_source.is_dir():
        logger.warning("Presets not found at '%s' – using stub.", presets_source)
        presets_source.mkdir(parents=True, exist_ok=True)
        (presets_source / "Example.vstpreset").write_text("stub preset")


def stage_presets(work_dirs: WorkDirs, presets_source: Path) -> None:
    dest = work_dirs.presets_payload_root / (work_dirs.staging_dir / "presets").relative_to("/")
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(presets_source, dest, dirs_exist_ok=True)
    logger.debug("Presets staged to %s", dest)


def stage_vst3(work_dirs: WorkDirs, vst3_bundle: Path) -> None:
    dest = work_dirs.vst3_payload_root / VST3_INSTALL_DIR.relative_to("/")
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(vst3_bundle, dest / vst3_bundle.name, dirs_exist_ok=True)
    logger.debug("VST3 staged to %s", dest)


def pkgbuild_vst3(work_dirs: WorkDirs, cfg: PluginBuildConfig) -> None:
    logger.info("pkgbuild: VST3")
    run([
        "pkgbuild",
        "--root", str(work_dirs.vst3_payload_root),
        "--identifier", f"{cfg.bundle_id_prefix}.{cfg.plugin_name}.vst3",
        "--version", cfg.version,
        "--install-location", "/",
        str(work_dirs.component_pkg_vst3),
    ])


def pkgbuild_presets(work_dirs: WorkDirs, cfg: PluginBuildConfig) -> None:
    logger.info("pkgbuild: Presets")
    run([
        "pkgbuild",
        "--root", str(work_dirs.presets_payload_root),
        "--identifier", f"{cfg.bundle_id_prefix}.{cfg.plugin_name}.presets",
        "--version", cfg.version,
        "--install-location", "/",
        "--scripts", str(work_dirs.scripts),
        str(work_dirs.component_pkg_presets),
    ])


def write_distribution_xml(work_dirs: WorkDirs, cfg: PluginBuildConfig) -> None:
    xml = f"""\
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="2">

    <title>{cfg.plugin_name} v{cfg.version}</title>

    <background file="background.png" alignment="bottomleft" scaling="tofit"/>
    <welcome    file="welcome.html"   mime-type="text/html"/>
    <license    file="license.html"   mime-type="text/html"/>

    <options customize="never" require-scripts="false" hostArchitectures="x86_64,arm64"/>
    <domains enable_localSystem="true"/>

    <choices-outline>
        <line choice="{cfg.bundle_id_prefix}.choice.vst3"/>
        <line choice="{cfg.bundle_id_prefix}.choice.presets"/>
    </choices-outline>

    <choice id="{cfg.bundle_id_prefix}.choice.vst3"
            title="VST3 Plug-in"
            description="Installs {cfg.plugin_name}.vst3 to /Library/Audio/Plug-Ins/VST3"
            start_selected="true" start_enabled="true" start_visible="true">
        <pkg-ref id="{cfg.bundle_id_prefix}.{cfg.plugin_name}.vst3"/>
    </choice>

    <choice id="{cfg.bundle_id_prefix}.choice.presets"
            title="Factory Presets"
            description="Installs factory presets to ~/Library/Application Support/{cfg.company_name}/{cfg.plugin_name}/presets"
            start_selected="true" start_enabled="true" start_visible="true">
        <pkg-ref id="{cfg.bundle_id_prefix}.{cfg.plugin_name}.presets"/>
    </choice>

    <pkg-ref id="{cfg.bundle_id_prefix}.{cfg.plugin_name}.vst3"    version="{cfg.version}">#component_vst3.pkg</pkg-ref>
    <pkg-ref id="{cfg.bundle_id_prefix}.{cfg.plugin_name}.presets" version="{cfg.version}">#component_presets.pkg</pkg-ref>

</installer-gui-script>
"""
    work_dirs.distribution_xml.write_text(xml)
    logger.debug("distribution.xml written")


def write_installer_resources(work_dirs: WorkDirs, config: PluginBuildConfig) -> None:
    pages = {
        "welcome.html": "You will be guided through the steps necessary to install this software.",
        "license.html": make_eula(EULAConfig(software_name=config.plugin_name,software_version=config.version)),

    }
    for filename, content in pages.items():
        (work_dirs.resources / filename).write_text(content)
    logger.debug("Installer HTML resources written")


def productbuild(work_dirs: WorkDirs, cfg: PluginBuildConfig, unsigned_pkg: Path) -> None:
    logger.info("productbuild: assembling installer...")
    run([
        "productbuild",
        "--distribution", str(work_dirs.distribution_xml),
        "--resources", str(work_dirs.resources),
        "--package-path", str(work_dirs.root),
        str(unsigned_pkg),
    ])


def sign_or_move_package(unsigned_pkg: Path, final_pkg: Path, signing_identity: str | None) -> None:
    if signing_identity:
        logger.info("Signing: %s", signing_identity)
        run(["productsign", "--sign", signing_identity, str(unsigned_pkg), str(final_pkg)])
        unsigned_pkg.unlink()
        logger.info("Signed:   %s", final_pkg)
    else:
        unsigned_pkg.rename(final_pkg)
        logger.info("Unsigned: %s", final_pkg)
        logger.info("Set signing_identity to sign for distribution.")


def build_macos_installer(cfg: PluginBuildConfig, bundle_path: Path) -> Path:
    """Build a macOS .pkg installer for a VST3 plug-in.

    Returns the path to the final installer package.
    """
    logger.info("Building installer for %s v%s", cfg.plugin_name, cfg.version)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    installer_name = f"{cfg.plugin_name}-{cfg.version}-macOS"

    codesign_bundle(bundle_path, cfg.apple_developer_id)
    ensure_vst3_source(bundle_path)
    ensure_presets_source(cfg.presets_source)

    with tempfile.TemporaryDirectory() as tmp:
        work_dirs = WorkDirs.from_root(Path(tmp), cfg)

        write_postinstall_script(work_dirs.scripts, company_name=cfg.company_name, product_name=cfg.plugin_name)
        stage_presets(work_dirs, cfg.presets_source)
        stage_vst3(work_dirs, bundle_path)
        pkgbuild_vst3(work_dirs, cfg)
        pkgbuild_presets(work_dirs, cfg)
        write_distribution_xml(work_dirs, cfg)
        write_installer_resources(work_dirs, cfg)

        unsigned_pkg = cfg.output_dir / f"{installer_name}-unsigned.pkg"
        final_pkg = cfg.output_dir / f"{installer_name}.pkg"

        productbuild(work_dirs, cfg, unsigned_pkg)
        sign_or_move_package(unsigned_pkg, final_pkg, cfg.signing_identity)

    logger.info("Done — installer at: %s", final_pkg)
    return final_pkg
