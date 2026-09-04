import shutil
from pathlib import Path
from typing import List, Dict, Optional
from termcraft.adapters.base import BaseShellAdapter
from termcraft.config import AliasDefinition
from termcraft.utils.paths import get_bashrc_path

class BashAdapter(BaseShellAdapter):
    @property
    def name(self) -> str:
        return "bash"

    def is_available(self) -> bool:
        return shutil.which("bash") is not None

    def get_config_path(self) -> Optional[Path]:
        return get_bashrc_path()

    def generate_alias_script(self, aliases: List[AliasDefinition]) -> str:
        # komutu tek tirnak icine aliyoruz, icerideki tirnaklari da klasik kapat-kac-ac
        # numarasiyla escape ediyoruz. boylece dolar isareti / backtick genisletilmiyor
        lines: List[str] = []
        for alias in aliases:
            if self.name in alias.shells:
                safe_name = alias.name.strip()
                cmd = alias.command.strip()
                escaped_cmd = cmd.replace("'", "'\\''")
                lines.append(f"alias {safe_name}='{escaped_cmd}'")
        return "\n".join(lines)

    def generate_env_script(self, env_vars: Dict[str, str]) -> str:
        lines: List[str] = []
        for k, v in env_vars.items():
            lines.append(f"export {k}=\"{v}\"")
        return "\n".join(lines)

    def generate_prompt_hook(self, engine: str, preset_path: Optional[str] = None, preset_name: Optional[str] = None) -> str:
        # starship/oh-my-posh kurulu degilse kendi basit PS1'imize duselim ki
        # kullanici tamamen promptsuz kalmasin
        if engine == "starship":
            return 'if command -v starship >/dev/null 2>&1; then eval "$(starship init bash)"; else PS1="\\[\\033[38;2;0;255;255m\\]\\u@\\h:\\[\\033[38;2;0;255;153m\\]\\w\\[\\033[38;2;0;255;255m\\] ❯ \\[\\033[0m\\]"; fi'
        elif engine == "oh-my-posh":
            cmd = f'eval "$(oh-my-posh init bash --config \'{preset_path}\')"' if preset_path else 'eval "$(oh-my-posh init bash)"'
            return f'if command -v oh-my-posh >/dev/null 2>&1; then {cmd}; else PS1="\\[\\033[38;2;0;255;255m\\]\\u@\\h:\\[\\033[38;2;0;255;153m\\]\\w\\[\\033[38;2;0;255;255m\\] ❯ \\[\\033[0m\\]"; fi'
        return ''
