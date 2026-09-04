import shutil
from pathlib import Path
from typing import List, Dict, Optional
from termcraft.adapters.base import BaseShellAdapter
from termcraft.config import AliasDefinition
from termcraft.utils.paths import get_fish_config_path

class FishAdapter(BaseShellAdapter):
    @property
    def name(self) -> str:
        return "fish"

    def is_available(self) -> bool:
        return shutil.which("fish") is not None

    def get_config_path(self) -> Optional[Path]:
        return get_fish_config_path()

    def generate_alias_script(self, aliases: List[AliasDefinition]) -> str:
        # fish'te tek tirnak escape kabul etmiyor, mecburen cift tirnak.
        # cift tirnak icinde fish sadece su ucunu ozel sayiyor: \ " $
        # ucunu de kaciriyoruz (ters slash ONCE, yoksa kendi kacislarimizi bozar).
        # $ ozellikle onemli: kacirmazsak `alias h "echo $HOME"` tanimlama aninda
        # genisliyor ve deger donuyor. bash'te tek tirnak kullandigimiz icin orada
        # calisma aninda genisliyor - fish'in de ayni sekilde davranmasi lazim
        lines: List[str] = []
        for alias in aliases:
            if self.name in alias.shells:
                safe_name = alias.name.strip()
                escaped_cmd = (
                    alias.command.strip()
                    .replace("\\", "\\\\")
                    .replace('"', '\\"')
                    .replace("$", "\\$")
                )
                lines.append(f'alias {safe_name} "{escaped_cmd}"')
        return "\n".join(lines)

    def generate_env_script(self, env_vars: Dict[str, str]) -> str:
        lines: List[str] = []
        for k, v in env_vars.items():
            lines.append(f"set -gx {k} \"{v}\"")
        return "\n".join(lines)

    def generate_prompt_hook(self, engine: str, preset_path: Optional[str] = None, preset_name: Optional[str] = None) -> str:
        # tek satirda if/else/function yaziyoruz, sondaki iki 'end' sirasiyla
        # fish_prompt fonksiyonunu ve if blogunu kapatiyor
        if engine == "starship":
            return 'if type -q starship; starship init fish | source; else; function fish_prompt; set_color cyan; echo -n (prompt_pwd); set_color green; echo -n " ❯ "; set_color normal; end; end'
        elif engine == "oh-my-posh":
            cmd = f'oh-my-posh init fish --config "{preset_path}" | source' if preset_path else 'oh-my-posh init fish | source'
            return f'if type -q oh-my-posh; {cmd}; else; function fish_prompt; set_color cyan; echo -n (prompt_pwd); set_color green; echo -n " ❯ "; set_color normal; end; end'
        return ''
