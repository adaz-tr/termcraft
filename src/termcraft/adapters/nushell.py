import shutil
from pathlib import Path
from typing import List, Dict, Optional
from termcraft.adapters.base import BaseShellAdapter
from termcraft.config import AliasDefinition
from termcraft.utils.paths import get_nushell_config_paths

class NuShellAdapter(BaseShellAdapter):
    @property
    def name(self) -> str:
        return "nushell"

    def is_available(self) -> bool:
        return shutil.which("nu") is not None

    def get_config_path(self) -> Optional[Path]:
        # windows'ta APPDATA/nushell, digerlerinde ~/.config/nushell.
        # hicbiri yoksa ilk adaya yazip klasoru olusturuyoruz
        paths = get_nushell_config_paths()
        for p in paths:
            if p.exists():
                return p
        if paths:
            return paths[0]
        return None

    def generate_alias_script(self, aliases: List[AliasDefinition]) -> str:
        lines: List[str] = []
        for alias in aliases:
            if self.name in alias.shells:
                safe_name = alias.name.strip()
                cmd = alias.command.strip()
                lines.append(f"alias {safe_name} = {cmd}")
        return "\n".join(lines)

    def generate_env_script(self, env_vars: Dict[str, str]) -> str:
        lines: List[str] = []
        for k, v in env_vars.items():
            # nushell tek tirnak icinde kacis yapmiyor, degerdeki tirnaklari kaldiriyoruz
            safe_v = str(v).replace("'", "")
            lines.append(f"$env.{k} = '{safe_v}'")
        return "\n".join(lines)

    def generate_prompt_hook(self, engine: str, preset_path: Optional[str] = None, preset_name: Optional[str] = None) -> str:
        """Prompt motorunu nushell'in vendor/autoload klasorune tek seferlik kurar.

        Onemli: `starship init nu | save -f ...` bir KURULUM komutu, config.nu'ya
        dogrudan konursa her kabuk acilisinda subprocess calistirip dosya yaziyor.
        Bu yuzden dosya zaten varsa hicbir sey yapmayan bir kosula sariyoruz.
        Uretilen dosyayi nushell autoload ile kendisi yukluyor.
        """
        if engine == "starship":
            binary, out_name = "starship", "starship.nu"
            init_cmd = "starship init nu"
        elif engine == "oh-my-posh":
            binary, out_name = "oh-my-posh", "oh-my-posh.nu"
            init_cmd = f'oh-my-posh init nu --config "{preset_path}"' if preset_path else "oh-my-posh init nu"
        else:
            return ""

        return (
            f"if (which {binary} | length) > 0 {{\n"
            f'    let tc_autoload = ($nu.data-dir | path join "vendor" "autoload")\n'
            f'    let tc_target = ($tc_autoload | path join "{out_name}")\n'
            f"    if not ($tc_target | path exists) {{\n"
            f"        mkdir $tc_autoload\n"
            f"        {init_cmd} | save -f $tc_target\n"
            f"    }}\n"
            f"}}"
        )
