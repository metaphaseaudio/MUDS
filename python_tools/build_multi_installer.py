from dataclasses import dataclass
from dataclasses_json import dataclass_json
from pathlib import Path
from hashlib import md5
from uuid import UUID
from typing import List, Optional
from argparse import ArgumentParser
from jinja2 import Template
import subprocess as sp


TEMPLATE_FILE = Path(__file__).parent.joinpath("install_script_template.jinja2")
SIGNTOOL = Path("/Program Files (x86)/Windows Kits/10/App Certification Kit/signtool.exe")


@dataclass_json
@dataclass
class InstallFile:
    source: str
    install_dir: str


@dataclass_json
@dataclass
class Component:
    name: str
    source: str
    default_install_dir: Path
    description: str
    extra_files: Optional[List[InstallFile]] = None


@dataclass_json
@dataclass
class Config:
    name: str
    version_string: str
    publisher: str
    url: str
    output_dir: str
    components: List[Component]
    languages: List[str]
    signing_cert: Optional[str] = None

    @property
    def hash(self):
        return str(UUID(bytes=md5((self.publisher + self.name + self.version_string).encode()).digest()))

    @property
    def output_base_filename(self):
        return f"Install {self.publisher} {self.name} {self.version_string}"


if __name__ == "__main__":
    parser = ArgumentParser(description="Generate multi-component inno install scripts")
    parser.add_argument("config", help="path to a config file to open")
    parser.add_argument("--run_iscc", "-r", action="store_true", help="run the Inno Setup compiler")

    args = parser.parse_args()

    config: Config
    with open(args.config, "r") as fp:
        config = Config.from_json(''.join(fp.readlines()))

    template: Template
    with TEMPLATE_FILE.open("r") as fp:
        template = Template(''.join(fp.readlines()), trim_blocks=True, lstrip_blocks=True)

    with open(f"{config.name}.iss", "w") as fp:
        fp.write(template.render(config=config))

    if args.run_iscc:
        p = sp.Popen(["iscc", f"{config.name}.iss"])
        p.wait()

    if config.signing_cert:
        # C:\Users\Matt\code\er1_plugin
        exe_path = Path(config.output_dir).joinpath(config.output_base_filename + ".exe")
        p = sp.Popen([str(SIGNTOOL), "sign", "/fd", "SHA256", "/f", config.signing_cert, exe_path])
        p.wait()

        if p.returncode != 0:
            print("Failed to sign installer.")
