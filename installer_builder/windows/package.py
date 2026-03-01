import logging
import tempfile
from hashlib import md5
from pathlib import Path
from uuid import UUID

from jinja2 import Template

from ..eula import make_eula_rtf, EULAConfig
from ..plugin_build_config import PluginBuildConfig
from ..util import run
from .codesign import sign_executable

logger = logging.getLogger(__name__)

TEMPLATE_FILE = Path(__file__).resolve().parent.parent / "templates" / "inno_setup.iss.jinja2"
DEFAULT_VST3_DIR = r"C:\Program Files\Common Files\VST3"
DEFAULT_PRESETS_DIR = r"{{userappdata}}\{company}\{plugin}\presets"
URL = "https://metaphaseindustries.com"


def _generate_app_id(company: str, plugin: str, version: str) -> str:
    raw = md5((company + plugin + version).encode()).digest()
    return str(UUID(bytes=raw))


def _render_template(cfg: PluginBuildConfig, bundle_path: Path, eula_path: Path) -> str:
    template_text = TEMPLATE_FILE.read_text()
    template = Template(template_text, trim_blocks=True, lstrip_blocks=True)

    presets_dir = DEFAULT_PRESETS_DIR.format(
        company=cfg.company_name,
        plugin=cfg.plugin_name,
    )

    registry_key = rf"{cfg.company_name}\{cfg.plugin_name}"

    context = {
        "app_id": _generate_app_id(cfg.company_name, cfg.plugin_name, cfg.version),
        "plugin_name": cfg.plugin_name,
        "version": cfg.version,
        "company_name": cfg.company_name,
        "url": URL,
        "output_base_filename": f"Install {cfg.company_name} {cfg.plugin_name} {cfg.version}",
        "output_dir": str(cfg.output_dir.resolve()),
        "eula_path": str(eula_path),
        "vst3_bundle_name": bundle_path.name,
        "vst3_source": str(bundle_path) + r"\*",
        "presets_source": str(cfg.presets_source) + r"\*",
        "default_vst3_dir": DEFAULT_VST3_DIR,
        "default_presets_dir": presets_dir,
        "registry_key": registry_key,
    }

    return template.render(**context)


def build_windows_installer(cfg: PluginBuildConfig, bundle_path: Path) -> Path:
    """Build a Windows Inno Setup installer for a VST3 plug-in.

    Returns the path to the final installer .exe.
    """
    logger.info("Building Windows installer for %s v%s", cfg.plugin_name, cfg.version)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Generate EULA as RTF (Inno Setup renders it via Windows RichEdit)
        eula_content = make_eula_rtf(EULAConfig(
            software_name=cfg.plugin_name,
            software_version=cfg.version,
        ))
        eula_path = tmp_path / "license.rtf"
        eula_path.write_text(eula_content, encoding="ascii", errors="replace")

        # Render Inno Setup script
        iss_content = _render_template(cfg, bundle_path, eula_path)
        iss_path = tmp_path / f"{cfg.plugin_name}.iss"
        iss_path.write_text(iss_content)
        logger.info("Generated Inno Setup script: %s", iss_path)

        # Remove any prior installer before compiling so iscc can write freely
        prior = cfg.output_dir / f"Install {cfg.company_name} {cfg.plugin_name} {cfg.version}.exe"
        if prior.exists():
            prior.unlink()

        # Compile with iscc
        run(["iscc", str(iss_path)])

    installer_name = f"Install {cfg.company_name} {cfg.plugin_name} {cfg.version}.exe"
    exe_path = cfg.output_dir / installer_name

    if not exe_path.is_file():
        raise RuntimeError(f"Expected installer not found at {exe_path}")

    # Optionally sign
    if cfg.signing_cert:
        sign_executable(exe_path, cfg.signing_cert)
    else:
        logger.info("No signing certificate provided; installer will be unsigned.")

    logger.info("Done — installer at: %s", exe_path)
    return exe_path
