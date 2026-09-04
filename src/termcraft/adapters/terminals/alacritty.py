import re
from pathlib import Path
from typing import Dict, Any, Optional
from termcraft.adapters.terminals.base import BaseTerminalAdapter
from termcraft.utils.paths import get_alacritty_config_paths

# alacritty config'i TOML. eskiden renk blogunu dosyanin sonuna ekliyorduk ama
# kullanicida zaten bir [colors.*] tablosu varsa TOML "duplicate table" hatasi
# veriyor ve alacritty config'i komple reddediyordu.
# artik once mevcut butun [colors...] tablolarini cikarip sonra kendi blogumuzu
# ekliyoruz -> tekrar eden tablo kalmiyor. ayrica sadece .toml hedefliyoruz,
# eski .yml config'e TOML yazmak da ayni sekilde bozuyordu
class AlacrittyAdapter(BaseTerminalAdapter):
    START_MARKER = "# >>> termcraft theme >>>"
    END_MARKER = "# <<< termcraft theme <<<"

    @property
    def name(self) -> str:
        return "alacritty"

    def get_config_path(self) -> Optional[Path]:
        paths = [p for p in get_alacritty_config_paths() if p.suffix == ".toml"]
        for p in paths:
            if p.exists():
                return p
        if paths:
            return paths[0]
        return None

    def is_available(self) -> bool:
        path = self.get_config_path()
        return path is not None and path.exists()

    def _strip_color_tables(self, text: str) -> str:
        """Dosyadaki mevcut [colors] / [colors.*] tablolarini siler.

        Tema uygulamak zaten "renkleri degistir" demek, o yuzden eskilerin
        kalmasinin anlami yok - ustelik kalirlarsa TOML gecersiz oluyor.
        Yedek `auto_backup` ile zaten aliniyor.
        """
        lines = text.split("\n")
        result = []
        skipping = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                table = stripped[1:-1].strip()
                skipping = table == "colors" or table.startswith("colors.")
            if not skipping:
                result.append(line)
        return "\n".join(result)

    def apply_theme(self, theme_data: Dict[str, Any]) -> bool:
        path = self.get_config_path()
        if not path:
            return False

        toml_block = f"""[colors.primary]
background = "{theme_data.get('background', '#1a1b26')}"
foreground = "{theme_data.get('foreground', '#c0caf5')}"

[colors.cursor]
text = "{theme_data.get('background', '#1a1b26')}"
cursor = "{theme_data.get('cursor', '#c0caf5')}"

[colors.selection]
text = "{theme_data.get('foreground', '#c0caf5')}"
background = "{theme_data.get('selection', '#33467c')}"

[colors.normal]
black = "{theme_data.get('black', '#15161e')}"
red = "{theme_data.get('red', '#f7768e')}"
green = "{theme_data.get('green', '#9ece6a')}"
yellow = "{theme_data.get('yellow', '#e0af68')}"
blue = "{theme_data.get('blue', '#7aa2f7')}"
magenta = "{theme_data.get('magenta', '#bb9af7')}"
cyan = "{theme_data.get('cyan', '#7dcfff')}"
white = "{theme_data.get('white', '#a9b1d6')}"

[colors.bright]
black = "{theme_data.get('brightBlack', '#414868')}"
red = "{theme_data.get('brightRed', '#f7768e')}"
green = "{theme_data.get('brightGreen', '#9ece6a')}"
yellow = "{theme_data.get('brightYellow', '#e0af68')}"
blue = "{theme_data.get('brightBlue', '#7aa2f7')}"
magenta = "{theme_data.get('brightMagenta', '#bb9af7')}"
cyan = "{theme_data.get('brightCyan', '#7dcfff')}"
white = "{theme_data.get('brightWhite', '#c0caf5')}"
"""

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            current = path.read_text(encoding="utf-8") if path.exists() else ""

            # once kendi eski blogumuzu cikar
            if self.START_MARKER in current and self.END_MARKER in current:
                start = current.find(self.START_MARKER)
                end = current.find(self.END_MARKER) + len(self.END_MARKER)
                current = current[:start] + current[end:]

            # sonra kullanicinin elle yazdigi renk tablolarini
            current = self._strip_color_tables(current)
            # temizlikten arta kalan ust uste bos satirlari topla
            current = re.sub(r"\n{3,}", "\n\n", current).strip()

            block = f"{self.START_MARKER}\n{toml_block.strip()}\n{self.END_MARKER}\n"
            new_content = (current + "\n\n" if current else "") + block
            path.write_text(new_content, encoding="utf-8")
            return True
        except Exception:
            return False
