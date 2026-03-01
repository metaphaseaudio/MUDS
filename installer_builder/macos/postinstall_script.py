from pathlib import Path

POSTINSTALL_SCRIPT_TEMPLATE = """\
#!/bin/bash
set -euo pipefail

LOG="/tmp/{product_name}-postinstall.log"
exec > >(tee -a "$LOG") 2>&1
set -x

STAGING_DIR="/Library/Application Support/{company_name}/{product_name}/staging/{target_type}"

REAL_USER=$(scutil <<< "show State:/Users/ConsoleUser" | awk '/Name :/ {{ print $3 }}')
REAL_HOME=$(dscl . -read "/Users/${{REAL_USER}}" NFSHomeDirectory | awk '{{print $2}}')
TARGET_DIR="${{REAL_HOME}}/Library/Application Support/{company_name}/{product_name}/{target_type}"

echo "Installing presets to: ${{TARGET_DIR}}"
mkdir -p "${{TARGET_DIR}}"
cp -R "${{STAGING_DIR}}/." "${{TARGET_DIR}}/"
chown -R "${{REAL_USER}}" "${{TARGET_DIR}}"
rm -rf "${{STAGING_DIR}}"
echo "Presets installed."
exit 0
"""

def write_postinstall_script(
        scripts_dir: Path,
        company_name: str="Metaphase Industries",
        product_name: str = "",
        target_type: str="presets"
) -> None:
    if not product_name:
        raise ValueError("product_name is required for write_postinstall_script")
    script = scripts_dir / "postinstall"
    script_content = POSTINSTALL_SCRIPT_TEMPLATE.format(
        company_name=company_name,
        product_name=product_name,
        target_type=target_type
    )
    script.write_text(script_content)
    script.chmod(0o755)
