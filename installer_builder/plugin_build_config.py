from dataclasses import dataclass
from pathlib import Path

@dataclass
class PluginBuildConfig:
    company_name: str
    plugin_name: str
    version: str
    presets_source: Path
    output_dir: Path
    bundle_id_prefix: str = "com.metaphaseindustries"
    apple_developer_id: str | None = None
    signing_identity: str | None = None
    signing_cert: str | None = None  # Windows .pfx certificate path
    skip_web_ui: bool = False
    web_dir: Path | None = None
    cmake_target: str | None = None
