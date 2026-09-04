import shutil
from pathlib import Path
from typing import List, Dict, Optional
from termcraft.adapters.base import BaseShellAdapter
from termcraft.config import AliasDefinition
from termcraft.utils.paths import get_zshrc_path

# bash ile neredeyse ayni, tek fark prompt degiskeni PROMPT ve renk sozdizimi %F{}
class ZshAdapter(BaseShellAdapter):
    @property
    def name(self) -> str:
        return "zsh"

    def is_available(self) -> bool:
        return shutil.which("zsh") is not None

    def get_config_path(self) -> Optional[Path]:
        return get_zshrc_path()

    def generate_alias_script(self, aliases: List[AliasDefinition]) -> str:
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
        # %F{#rrggbb} truecolor formu zsh 5.7+ ister, eski zsh'ta prompt bozuk gorunur
        if engine == "starship":
            return 'if command -v starship >/dev/null 2>&1; then eval "$(starship init zsh)"; else PROMPT="%F{#00ffff}%n@%m:%F{#00ff99}%~%F{#00ffff} ❯ %f"; fi'
        elif engine == "oh-my-posh":
            if preset_path:
                return 'if command -v oh-my-posh >/dev/null 2>&1; then eval "$(oh-my-posh init zsh --config \'' + preset_path + '\')"; else PROMPT="%F{#00ffff}%n@%m:%F{#00ff99}%~%F{#00ffff} ❯ %f"; fi'
            return 'if command -v oh-my-posh >/dev/null 2>&1; then eval "$(oh-my-posh init zsh)"; else PROMPT="%F{#00ffff}%n@%m:%F{#00ff99}%~%F{#00ffff} ❯ %f"; fi'
        return ''
