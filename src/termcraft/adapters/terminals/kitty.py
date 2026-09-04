from pathlib import Path
from typing import Dict, Any, Optional
from termcraft.adapters.terminals.base import BaseTerminalAdapter
from termcraft.utils.paths import get_kitty_config_paths

class KittyAdapter(BaseTerminalAdapter):
    @property
    def name(self) -> str:
        return "kitty"

    def get_config_path(self) -> Optional[Path]:
        paths = get_kitty_config_paths()
        for p in paths:
            if p.exists():
                return p
        if paths:
            return paths[0]
        return None

    def is_available(self) -> bool:
        path = self.get_config_path()
        return path is not None and path.exists()

    def apply_theme(self, theme_data: Dict[str, Any]) -> bool:
        # kitty.conf duz anahtar-deger formatinda, ayni anahtar birden fazla
        # gecerse sonuncu kazaniyor. o yuzden blogu sona eklemek burada sorunsuz
        # calisiyor (alacritty/wezterm'de ayni sey gecerli degil)
        path = self.get_config_path()
        if not path:
            return False

        path.parent.mkdir(parents=True, exist_ok=True)
        conf_lines = [
            f"foreground {theme_data.get('foreground', '#c0caf5')}",
            f"background {theme_data.get('background', '#1a1b26')}",
            f"cursor {theme_data.get('cursor', '#c0caf5')}",
            f"selection_background {theme_data.get('selection', '#33467c')}",
            f"selection_foreground {theme_data.get('foreground', '#c0caf5')}",
            f"color0 {theme_data.get('black', '#15161e')}",
            f"color1 {theme_data.get('red', '#f7768e')}",
            f"color2 {theme_data.get('green', '#9ece6a')}",
            f"color3 {theme_data.get('yellow', '#e0af68')}",
            f"color4 {theme_data.get('blue', '#7aa2f7')}",
            f"color5 {theme_data.get('magenta', '#bb9af7')}",
            f"color6 {theme_data.get('cyan', '#7dcfff')}",
            f"color7 {theme_data.get('white', '#a9b1d6')}",
            f"color8 {theme_data.get('brightBlack', '#414868')}",
            f"color9 {theme_data.get('brightRed', '#f7768e')}",
            f"color10 {theme_data.get('brightGreen', '#9ece6a')}",
            f"color11 {theme_data.get('brightYellow', '#e0af68')}",
            f"color12 {theme_data.get('brightBlue', '#7aa2f7')}",
            f"color13 {theme_data.get('brightMagenta', '#bb9af7')}",
            f"color14 {theme_data.get('brightCyan', '#7dcfff')}",
            f"color15 {theme_data.get('brightWhite', '#c0caf5')}"
        ]
        conf_block = "\n".join(conf_lines)

        try:
            start_m = "# >>> termcraft theme >>>"
            end_m = "# <<< termcraft theme <<<"
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            block = f"{start_m}\n{conf_block}\n{end_m}\n"
            if start_m in current and end_m in current:
                start = current.find(start_m)
                end = current.find(end_m) + len(end_m)
                new_c = current[:start] + block + current[end:].lstrip("\n")
            else:
                new_c = current.rstrip() + ("\n\n" if current else "") + block
            path.write_text(new_c, encoding="utf-8")
            return True
        except Exception:
            return False
