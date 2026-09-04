import os
import sys
from pathlib import Path
from typing import List

# butun yol hesaplari tek yerden ciksin diye burada topluyoruz.
# adapterler asla elle path kurmuyor, hep bu fonksiyonlari cagiriyor
def get_home_dir() -> Path:
    return Path.home()

def get_termcraft_dir() -> Path:
    # yan etkili bir getter -> cagirir cagirmaz klasorleri aciyor.
    # import zincirinde bunu cagiran bir modul varsa test ederken de
    # ~/.termcraft olusuyor, testlerde HOME'u izole etmek sart
    base = get_home_dir() / ".termcraft"
    base.mkdir(parents=True, exist_ok=True)
    (base / "backups").mkdir(exist_ok=True)
    (base / "themes").mkdir(exist_ok=True)
    (base / "prompts").mkdir(exist_ok=True)
    (base / "profiles").mkdir(exist_ok=True)
    return base

def get_config_file_path() -> Path:
    return get_termcraft_dir() / "config.yaml"

def get_powershell_profile_paths() -> List[Path]:
    # powershell'in profil yolu bir suru yerde olabiliyor: pwsh 7 Documents/PowerShell,
    # 5.1 Documents/WindowsPowerShell, ustune bir de OneDrive klasor yonlendirmesi.
    # hepsini dondurup adapter tarafinda var olanlara yaziyoruz
    paths: List[Path] = []
    home = get_home_dir()
    if sys.platform == "win32":
        docs = home / "Documents"
        onedrive_docs = home / "OneDrive" / "Documents"
        candidates = [
            docs / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
            docs / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1",
            onedrive_docs / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
            onedrive_docs / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1",
            docs / "PowerShell" / "profile.ps1",
            docs / "WindowsPowerShell" / "profile.ps1",
        ]
        for c in candidates:
            if c not in paths:
                paths.append(c)
    else:
        paths.append(home / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1")
    return paths

def get_bashrc_path() -> Path:
    return get_home_dir() / ".bashrc"

def get_zshrc_path() -> Path:
    return get_home_dir() / ".zshrc"

def get_fish_config_path() -> Path:
    # fish her platformda ayni yeri kullaniyor, ayrima gerek yok
    return get_home_dir() / ".config" / "fish" / "config.fish"

def get_nushell_config_paths() -> List[Path]:
    home = get_home_dir()
    paths: List[Path] = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            paths.append(Path(appdata) / "nushell" / "config.nu")
    paths.append(home / ".config" / "nushell" / "config.nu")
    return paths

def get_windows_terminal_settings_paths() -> List[Path]:
    # store surumu Packages altinda, msi/portable surum dogrudan LocalAppData'da.
    # hicbiri yoksa stable klasoru duruyorsa oraya yazmayi deniyoruz
    paths: List[Path] = []
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        base = Path(local_appdata) / "Packages"
        stable = base / "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json"
        preview = base / "Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe" / "LocalState" / "settings.json"
        unpackaged = Path(local_appdata) / "Microsoft" / "Windows Terminal" / "settings.json"
        for p in [stable, preview, unpackaged]:
            if p.exists():
                paths.append(p)
        if not paths and stable.parent.exists():
            paths.append(stable)
    return paths

def get_alacritty_config_paths() -> List[Path]:
    paths: List[Path] = []
    home = get_home_dir()
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            paths.append(Path(appdata) / "alacritty" / "alacritty.toml")
            paths.append(Path(appdata) / "alacritty" / "alacritty.yml")
    paths.append(home / ".config" / "alacritty" / "alacritty.toml")
    paths.append(home / ".config" / "alacritty" / "alacritty.yml")
    paths.append(home / ".alacritty.toml")
    return paths

def get_wezterm_config_paths() -> List[Path]:
    home = get_home_dir()
    return [
        home / ".wezterm.lua",
        home / ".config" / "wezterm" / "wezterm.lua"
    ]

def get_kitty_config_paths() -> List[Path]:
    home = get_home_dir()
    return [
        home / ".config" / "kitty" / "kitty.conf"
    ]

def get_starship_config_path() -> Path:
    # kullanici STARSHIP_CONFIG set etmisse ona saygi duy, ezme
    custom = os.environ.get("STARSHIP_CONFIG")
    if custom:
        return Path(custom)
    return get_home_dir() / ".config" / "starship.toml"
