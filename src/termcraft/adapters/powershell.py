import re
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from termcraft.adapters.base import BaseShellAdapter
from termcraft.config import AliasDefinition
from termcraft.utils.paths import get_powershell_profile_paths

# powershell butun kabuklar icinde en zahmetlisi: profil dosyasi tek degil,
# BOM'suz utf-8'i bazi surumler yanlis okuyor ve alias'lar sadece komut adi
# alabiliyor (parametre alamiyor). o yuzden base'deki inject/remove'u eziyoruz
class PowerShellAdapter(BaseShellAdapter):
    @property
    def name(self) -> str:
        return "powershell"

    def is_available(self) -> bool:
        return shutil.which("pwsh") is not None or shutil.which("powershell") is not None

    def get_config_path(self) -> Optional[Path]:
        candidates = get_powershell_profile_paths()
        for p in candidates:
            if p.exists():
                return p
        if candidates:
            return candidates[0]
        return None

    # base'den farki: tek dosyaya degil, var olan TUM profillere yaziyoruz.
    # kullanici hem pwsh 7 hem 5.1 kullaniyorsa ikisi de ayni ayara sahip olsun diye.
    # BOM (utf-8-sig) sart, yoksa 5.1 unicode ikonlari bozuk gosteriyor
    def inject_block(self, content: str) -> bool:
        candidates = get_powershell_profile_paths()
        target_files = [p for p in candidates if p.exists()]
        if not target_files and candidates:
            target_files = [candidates[0]]
            
        written = False
        block = f"{self.START_MARKER}\n{content.strip()}\n{self.END_MARKER}\n"
        
        for config_file in target_files:
            try:
                config_file.parent.mkdir(parents=True, exist_ok=True)
                existing = config_file.read_text(encoding="utf-8-sig") if config_file.exists() else ""
                
                if self.START_MARKER in existing and self.END_MARKER in existing:
                    start_idx = existing.find(self.START_MARKER)
                    end_idx = existing.find(self.END_MARKER) + len(self.END_MARKER)
                    new_content = existing[:start_idx] + block + existing[end_idx:]
                else:
                    new_content = existing + ("\n\n" if existing and not existing.endswith("\n") else "") + block

                config_file.write_text(new_content, encoding="utf-8-sig")
                written = True
            except Exception:
                pass
        return written

    def remove_block(self) -> bool:
        candidates = get_powershell_profile_paths()
        removed = False
        for config_file in candidates:
            if config_file.exists():
                try:
                    current = config_file.read_text(encoding="utf-8-sig")
                    if self.START_MARKER in current and self.END_MARKER in current:
                        start = current.find(self.START_MARKER)
                        end = current.find(self.END_MARKER) + len(self.END_MARKER)
                        new_content = current[:start].rstrip() + "\n" + current[end:].lstrip()
                        config_file.write_text(new_content.strip() + "\n", encoding="utf-8-sig")
                        removed = True
                except Exception:
                    pass
        return removed

    def generate_alias_script(self, aliases: List[AliasDefinition]) -> str:
        # Set-Alias sadece komut adina isaret edebiliyor, parametre kabul etmiyor.
        # o yuzden komutta bosluk varsa once bir sarmalayici fonksiyon uretip
        # alias'i ona bagliyoruz. $args ile de kullanicinin parametreleri geciyor.
        # DIKKAT: -Force ReadOnly built-in alias'lari da eziyor (ls, cat, cd, gc, gp...)
        lines: List[str] = []
        for alias in aliases:
            if self.name in alias.shells:
                safe_name = alias.name.strip()
                cmd = alias.command.strip()
                fn_suffix = re.sub(r'[^a-zA-Z0-9_]', '_', safe_name)
                if " " in cmd:
                    fn_name = f"__tc_alias_{fn_suffix}"
                    lines.append(f"function {fn_name} {{ {cmd} $args }}")
                    lines.append(f"Set-Alias -Name {safe_name} -Value {fn_name} -Option AllScope -Force")
                else:
                    lines.append(f"Set-Alias -Name {safe_name} -Value \"{cmd}\" -Option AllScope -Force")
        return "\n".join(lines)

    def generate_env_script(self, env_vars: Dict[str, str]) -> str:
        lines: List[str] = []
        for k, v in env_vars.items():
            lines.append(f"$env:{k} = \"{v}\"")
            
        # PSReadLine sozdizimi renkleri. env script'ine iliştirilmis durumda cunku
        # ayri bir 'tema' bolumu yok. env_vars bos gelirse bu blok da yazilmiyor
        script = """
$e = [char]27
$c_cyan = "$e[38;2;0;255;255m"
$c_blue = "$e[38;2;0;153;255m"
$c_purple = "$e[38;2;168;0;255m"
$c_magenta = "$e[38;2;255;0;204m"
$c_green = "$e[38;2;0;255;153m"
$c_yellow = "$e[38;2;255;204;0m"
$c_red = "$e[38;2;255;0;85m"
$c_reset = "$e[0m"

if (Get-Module -ListAvailable -Name PSReadLine) {
    try {
        Set-PSReadLineOption -Colors @{
            Command = "$e[38;2;0;255;255m"
            Parameter = "$e[38;2;0;153;255m"
            Operator = "$e[38;2;168;0;255m"
            Variable = "$e[38;2;0;255;153m"
            String = "$e[38;2;255;204;0m"
            Number = "$e[38;2;255;0;127m"
            Member = "$e[38;2;0;212;255m"
            Error = "$e[38;2;255;0;85m"
            Selection = "$e[48;2;26;9;51m"
            Default = "$e[38;2;230;240;255m"
        } -ErrorAction SilentlyContinue
    } catch {}
}
"""
        lines.append(script.strip())
        return "\n".join(lines)

    def generate_prompt_hook(self, engine: str, preset_path: Optional[str] = None, preset_name: Optional[str] = None) -> str:
        # mantik: once starship/oh-my-posh var mi diye bak, yoksa else dalinda
        # kendi saf-powershell prompt fonksiyonumuzu tanimla.
        # renk degiskenleri ($e[38;2;...) string icinde indeksleme gibi gorunse de
        # powershell string interpolasyonu koseli parantezi genisletmiyor, calisiyor
        p_name = preset_name or "modern-cyber"
        if engine == "starship":
            check_cmd = "if (Get-Command starship -ErrorAction SilentlyContinue) {\n    Invoke-Expression (&starship init powershell)\n} else {\n"
        elif engine == "oh-my-posh":
            cmd = f'oh-my-posh init pwsh --config "{preset_path}" | Invoke-Expression' if preset_path else 'oh-my-posh init pwsh | Invoke-Expression'
            check_cmd = f"if (Get-Command oh-my-posh -ErrorAction SilentlyContinue) {{\n    {cmd}\n}} else {{\n"
        else:
            check_cmd = ""

        # preset adina gore fallback prompt govdesi. hepsi her cizimde git calistiriyor,
        # buyuk repolarda prompt gecikmesi hissedilebiliyor
        if p_name == "minimal-pure":
            prompt_fn = """
    function prompt {
        $p = $executionContext.SessionState.Path.CurrentLocation.Path
        $branch = ""
        try {
            $b = (git rev-parse --abbrev-ref HEAD 2>$null)
            if ($b) { $branch = " " + $c_yellow + "(" + $b + ")" + $c_reset }
        } catch {}
        return "$c_cyan$p$branch $c_green❯$c_reset "
    }
"""
        elif p_name == "powerline-gradient":
            prompt_fn = """
    function prompt {
        $p = $executionContext.SessionState.Path.CurrentLocation.Path
        $user = [System.Environment]::UserName
        $branch = ""
        try {
            $b = (git rev-parse --abbrev-ref HEAD 2>$null)
            if ($b) { $branch = " " + $c_purple + "◆ " + $c_magenta + $b + $c_reset }
        } catch {}
        $l1 = "$c_cyan╭─[$c_blue$user$c_cyan] ── [$c_green$p$c_cyan]$branch"
        $l2 = "$c_cyan╰─❯$c_green❯$c_reset "
        return "$l1`n$l2"
    }
"""
        elif p_name == "catppuccin-clean":
            prompt_fn = """
    function prompt {
        $p = $executionContext.SessionState.Path.CurrentLocation.Path
        $branch = ""
        try {
            $b = (git rev-parse --abbrev-ref HEAD 2>$null)
            if ($b) { $branch = " on " + $c_magenta + $b + $c_reset }
        } catch {}
        $l1 = "$c_blue✦ $c_cyan$p$branch"
        $l2 = "$c_magenta➜ $c_reset"
        return "$l1`n$l2"
    }
"""
        else:
            prompt_fn = """
    function prompt {
        $p = $executionContext.SessionState.Path.CurrentLocation.Path
        $user = [System.Environment]::UserName
        $hostName = [System.Environment]::MachineName
        $gitBranch = ""
        try {
            $branch = (git rev-parse --abbrev-ref HEAD 2>$null)
            if ($branch) {
                $gitBranch = " " + $c_purple + "(" + $c_magenta + $branch + $c_purple + ")" + $c_reset
            }
        } catch {}
        $line1 = $c_cyan + "+--[" + $c_blue + $user + $c_cyan + "@" + $c_blue + $hostName + $c_cyan + "]--[" + $c_green + $p + $c_cyan + "]" + $gitBranch
        $line2 = $c_cyan + "+--> " + $c_reset
        return "$line1`n$line2"
    }
"""

        fallback_block = f"""
    $e = [char]27
    $c_cyan = "$e[38;2;0;255;255m"
    $c_blue = "$e[38;2;0;153;255m"
    $c_purple = "$e[38;2;168;0;255m"
    $c_magenta = "$e[38;2;255;0;204m"
    $c_green = "$e[38;2;0;255;153m"
    $c_yellow = "$e[38;2;255;204;0m"
    $c_reset = "$e[0m"
{prompt_fn}
"""
        if check_cmd:
            return f"{check_cmd}{fallback_block}}}"
        return fallback_block.strip()
