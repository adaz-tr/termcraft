import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict

# prompt ikonlarinin duzgun gorunmesi icin en cok kullanilan nerd font'lar.
# tam liste devasa, doctor'da uyari vermeye bu kadari yetiyor
POPULAR_NERD_FONTS = [
    "JetBrainsMono Nerd Font",
    "MesloLGS NF",
    "FiraCode Nerd Font",
    "CaskaydiaCove Nerd Font",
    "Cascadia Code NF",
    "Hack Nerd Font",
    "SourceCodePro Nerd Font",
    "Agave Nerd Font",
    "Mononoki Nerd Font",
    "VictorMono Nerd Font",
    "UbuntuMono Nerd Font",
    "ComicShanns Nerd Font"
]

def scan_windows_fonts() -> List[str]:
    # uc kaynaga birden bakiyoruz: registry (sistem + kullanici), windows font klasoru
    # ve kullaniciya ozel AppData Local font klasoru. registry bazen eksik oluyor,
    # dosya taramasi onu tamamliyor
    fonts: List[str] = []
    if sys.platform != "win32":
        return fonts
    try:
        import winreg
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts")
        ]
        for root_key, sub_key in registry_paths:
            try:
                with winreg.OpenKey(root_key, sub_key) as key:
                    for i in range(winreg.QueryInfoKey(key)[1]):
                        name, _, _ = winreg.EnumValue(key, i)
                        fonts.append(name)
            except Exception:
                pass
    except Exception:
        pass
    
    font_dir = Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"
    if font_dir.exists():
        for file in font_dir.glob("*.[tT][tT][fF]"):
            fonts.append(file.stem)
        for file in font_dir.glob("*.[oO][tT][fF]"):
            fonts.append(file.stem)
            
    local_font_dir = Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts"
    if local_font_dir.exists():
        for file in local_font_dir.glob("*.[tT][tT][fF]"):
            fonts.append(file.stem)
        for file in local_font_dir.glob("*.[oO][tT][fF]"):
            fonts.append(file.stem)
            
    return list(set(fonts))

def scan_unix_fonts() -> List[str]:
    # /usr/share/fonts alt klasorlere bolundugu icin rglob sart, duz glob
    # font'larin buyuk kismini kaciriyordu. fc-list varsa o da tamamliyor
    fonts: List[str] = []
    if sys.platform == "darwin":
        font_dirs = [
            Path.home() / "Library" / "Fonts",
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts")
        ]
    else:
        font_dirs = [
            Path.home() / ".local" / "share" / "fonts",
            Path.home() / ".fonts",
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts")
        ]
    for fdir in font_dirs:
        if fdir.exists():
            try:
                for f in fdir.rglob("*.[tToO][tT][fF]"):
                    fonts.append(f.stem)
            except OSError:
                # izin sorunu olan sistem klasorlerinde takilip kalmayalim
                pass
    try:
        result = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                for f in line.split(","):
                    cleaned = f.strip()
                    if cleaned and cleaned not in fonts:
                        fonts.append(cleaned)
    except Exception:
        pass
    return list(set(fonts))

def detect_nerd_fonts() -> Dict[str, bool]:
    # font isimleri her yerde farkli yaziliyor (JetBrainsMono NF / JetBrainsMono Nerd Font
    # / JetBrainsMonoNL...) o yuzden bosluk-tire atip substring karsilastiriyoruz
    all_fonts = scan_windows_fonts() if sys.platform == "win32" else scan_unix_fonts()
    normalized_fonts = [f.lower().replace(" ", "").replace("-", "") for f in all_fonts]
    
    results = {}
    for nf in POPULAR_NERD_FONTS:
        clean_key = nf.lower().replace(" ", "").replace("-", "")
        found = any(clean_key in f_norm for f_norm in normalized_fonts)
        results[nf] = found
    return results
