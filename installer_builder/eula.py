from dataclasses import dataclass, asdict
from datetime import date
from html.parser import HTMLParser
import html as _html_module
from pathlib import Path
import re
import string

@dataclass
class EULAConfig:
    software_name: str
    software_version: str
    developer_name: str = "Metaphase Industries LLC"
    developer_address: str = ""
    developer_email: str = "info@metaphaseindustries.com"
    max_installations: int = 3
    effective_date: str = date.today().strftime("%B %d, %Y")
    governing_law: str = "Massachusetts, United States"


def make_eula(eula_config: EULAConfig) -> str:
    html_path = Path(__file__).parent / "templates" / "eula.html"
    # Explicit UTF-8 so the © in the template isn't misread on Windows (cp1252 default)
    with html_path.open("r", encoding="utf-8") as fp:
        eula_text = fp.read()
        eula_template = string.Template(eula_text)
        return eula_template.substitute(asdict(eula_config))


def make_eula_rtf(eula_config: EULAConfig) -> str:
    """Render the EULA as RTF for use in Windows (Inno Setup) installers."""
    return _html_to_rtf(make_eula(eula_config))


def _html_to_rtf(html_str: str) -> str:
    """Convert the EULA HTML to RTF suitable for Inno Setup's LicenseFile."""

    class _Builder(HTMLParser):
        _SKIP = {"style", "script", "head", "title"}

        def __init__(self):
            super().__init__()
            self.parts: list[str] = []
            self._skip = 0

        def emit(self, s: str) -> None:
            self.parts.append(s)

        @staticmethod
        def _escape(text: str) -> str:
            out = []
            for ch in text:
                if ch == "\\":
                    out.append("\\\\")
                elif ch == "{":
                    out.append("\\{")
                elif ch == "}":
                    out.append("\\}")
                elif ord(ch) < 128:
                    out.append(ch)
                elif ord(ch) <= 255:
                    out.append(f"\\'{ord(ch):02x}")
                else:
                    out.append(f"\\u{ord(ch)}?")
            return "".join(out)

        def handle_starttag(self, tag, attrs):
            if tag in self._SKIP:
                self._skip += 1
                return
            if self._skip:
                return
            if tag == "h1":
                self.emit(r"\pard\sb200\sa100\qc\b\fs32 ")
            elif tag == "h2":
                self.emit(r"\pard\sb240\sa80\b\fs22 ")
            elif tag == "p":
                self.emit(r"\pard\sb0\sa120\b0\i0\fs20 ")
            elif tag == "li":
                self.emit(r"\pard\sb0\sa80\li480\fi-240\b0\i0\fs20 \bullet  ")
            elif tag == "strong":
                self.emit(r"\b ")
            elif tag == "em":
                self.emit(r"\i ")
            elif tag == "br":
                self.emit(r"\line ")
            # div: transparent container — contained <p> elements handle their own formatting

        def handle_endtag(self, tag):
            if tag in self._SKIP:
                self._skip -= 1
                return
            if self._skip:
                return
            if tag in ("h1", "h2", "p", "li"):
                self.emit(r"\par ")
            elif tag == "strong":
                self.emit(r"\b0 ")
            elif tag == "em":
                self.emit(r"\i0 ")
            # div: no \par — avoids extra blank lines between container and its children

        def handle_data(self, data):
            if not self._skip:
                # Collapse HTML whitespace (indentation, newlines) to single spaces
                normalized = re.sub(r"\s+", " ", data)
                if normalized.strip():
                    self.emit(self._escape(normalized))

        def handle_entityref(self, name):
            self.handle_data(_html_module.unescape(f"&{name};"))

        def handle_charref(self, name):
            self.handle_data(_html_module.unescape(f"&#{name};"))

    builder = _Builder()
    builder.feed(html_str)
    body = "".join(builder.parts)

    return (
        "{\\rtf1\\ansi\\ansicpg1252\\deff0\n"
        "{\\fonttbl{\\f0\\fswiss\\fcharset0 Arial;}}\n"
        "\\widowctrl\\hyphauto\\f0\n"
        + body
        + "\n}"
    )
