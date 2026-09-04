import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
from termcraft.adapters.terminals.base import BaseTerminalAdapter
from termcraft.utils.paths import get_windows_terminal_settings_paths

class WindowsTerminalAdapter(BaseTerminalAdapter):
    @property
    def name(self) -> str:
        return "windows-terminal"

    def get_config_path(self) -> Optional[Path]:
        paths = get_windows_terminal_settings_paths()
        for p in paths:
            if p.exists():
                return p
        if paths:
            return paths[0]
        return None

    def is_available(self) -> bool:
        path = self.get_config_path()
        return path is not None and path.exists()

    # windows terminal settings.json aslinda JSONC: yorum satirlari ve sondaki
    # fazladan virguller olabiliyor. hazir kutuphane eklemek yerine ufak bir
    # durum makinesiyle yorumlari ayikliyoruz. string icindeki // korunmali,
    # o yuzden in_str / escaped takibi var
    def _strip_jsonc(self, text: str) -> str:
        res = []
        in_str = False
        in_line_comment = False
        in_block_comment = False
        escaped = False
        i = 0
        n = len(text)
        while i < n:
            c = text[i]
            nxt = text[i+1] if i + 1 < n else ''
            if in_line_comment:
                if c in '\r\n':
                    in_line_comment = False
                    res.append(c)
                i += 1
            elif in_block_comment:
                if c == '*' and nxt == '/':
                    in_block_comment = False
                    i += 2
                else:
                    i += 1
            elif in_str:
                res.append(c)
                if escaped:
                    escaped = False
                elif c == chr(92):
                    escaped = True
                elif c == chr(34):
                    in_str = False
                i += 1
            else:
                if c == chr(34):
                    in_str = True
                    res.append(c)
                    i += 1
                elif c == '/' and nxt == '/':
                    in_line_comment = True
                    i += 2
                elif c == '/' and nxt == '*':
                    in_block_comment = True
                    i += 2
                else:
                    res.append(c)
                    i += 1
        return ''.join(res)

    def apply_theme(self, theme_data: Dict[str, Any]) -> bool:
        # DIKKAT: json.dumps ile geri yazdigimiz an kullanicinin yorumlari ve
        # formatlamasi kayboluyor. ThemeEngine.apply_theme burayi cagirmadan once
        # maybe_snapshot() ile yedek aliyor, o yuzden geri donus mumkun
        path = self.get_config_path()
        if not path or not path.exists():
            return False

        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            clean = self._strip_jsonc(raw)
            clean = re.sub(r',\s*([\]\}])', r'\1', clean)
            data = json.loads(clean, strict=False)
        except Exception:
            return False

        # sondaki fazla virgulleri de temizle, json modulu onlari kabul etmiyor.
        # semayi kendi ad alanimizda tutuyoruz ki kullanicinin semalariyla carpismasin
        scheme_name = f"TermCraft {theme_data.get('name', 'Theme')}"
        scheme_def = {
            "name": scheme_name,
            "background": theme_data.get("background", "#08090f"),
            "foreground": theme_data.get("foreground", "#00ffff"),
            "cursorColor": theme_data.get("cursor", "#ff00cc"),
            "selectionBackground": theme_data.get("selection", "#1a0933"),
            "black": theme_data.get("black", "#0c0d14"),
            "red": theme_data.get("red", "#ff0055"),
            "green": theme_data.get("green", "#00ff99"),
            "yellow": theme_data.get("yellow", "#ffcc00"),
            "blue": theme_data.get("blue", "#0099ff"),
            "purple": theme_data.get("magenta", "#a800ff"),
            "cyan": theme_data.get("cyan", "#00ffff"),
            "white": theme_data.get("white", "#e6f0ff"),
            "brightBlack": theme_data.get("brightBlack", "#3d3f58"),
            "brightRed": theme_data.get("brightRed", "#ff3377"),
            "brightGreen": theme_data.get("brightGreen", "#33ffaa"),
            "brightYellow": theme_data.get("brightYellow", "#ffdd33"),
            "brightBlue": theme_data.get("brightBlue", "#33adff"),
            "brightPurple": theme_data.get("brightMagenta", "#c233ff"),
            "brightCyan": theme_data.get("brightCyan", "#33ffff"),
            "brightWhite": theme_data.get("brightWhite", "#ffffff")
        }

        # ayni isimde sema varsa uzerine yaz, yoksa listeye ekle
        schemes = data.get("schemes", [])
        updated = False
        for i, s in enumerate(schemes):
            if s.get("name") == scheme_name:
                schemes[i] = scheme_def
                updated = True
                break
        if not updated:
            schemes.append(scheme_def)
        data["schemes"] = schemes

        # profiles hem dict (defaults + list) hem duz list olabiliyor, ikisini de karsila
        if "profiles" not in data:
            data["profiles"] = {"defaults": {"colorScheme": scheme_name}}
        elif isinstance(data["profiles"], dict):
            if "defaults" not in data["profiles"]:
                data["profiles"]["defaults"] = {}
            data["profiles"]["defaults"]["colorScheme"] = scheme_name
        elif isinstance(data["profiles"], list):
            for p in data["profiles"]:
                p["colorScheme"] = scheme_name

        try:
            path.write_text(json.dumps(data, indent=4), encoding="utf-8")
            return True
        except Exception:
            return False
