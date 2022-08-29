from dataclasses import dataclass
from dataclasses_json import dataclass_json
from pathlib import Path
from hashlib import md5
from uuid import UUID
from typing import List
from argparse import ArgumentParser
from jinja2 import Template
import subprocess as sp


TEMPLATE_FILE = Path(__file__).parent.joinpath("install_script_template.jinja2")


@dataclass_json
@dataclass
class Component:
    name: str
    source: str
    default_install_dir: Path
    description: str


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

    @property
    def hash(self):
        return str(UUID(bytes=md5((self.publisher + self.name + self.version_string).encode()).digest()))


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
