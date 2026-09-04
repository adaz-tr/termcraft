import re
from pathlib import Path
from typing import Dict, Any, Optional
from termcraft.adapters.terminals.base import BaseTerminalAdapter
from termcraft.utils.paths import get_wezterm_config_paths

# wezterm config'i duz bir lua dosyasi ve neredeyse her zaman `return config`
# ile bitiyor. lua'da return bir blogun SON ifadesi olmak zorunda, o yuzden
# dosyanin sonuna kod eklemek config'i komple sozdizimi hatasina sokuyordu.
# cozum: renkleri ana config'in yanindaki ayri bir termcraft_colors.lua'ya
# yazip ana dosyaya sadece kucuk bir dofile blogu koymak - onu da en sondaki
# return'den ONCE eklemek
class WezTermAdapter(BaseTerminalAdapter):
    START_MARKER = "-- >>> termcraft theme >>>"
    END_MARKER = "-- <<< termcraft theme <<<"
    COLORS_FILE = "termcraft_colors.lua"

    @property
    def name(self) -> str:
        return "wezterm"

    def get_config_path(self) -> Optional[Path]:
        paths = get_wezterm_config_paths()
        for p in paths:
            if p.exists():
                return p
        if paths:
            return paths[0]
        return None

    def is_available(self) -> bool:
        path = self.get_config_path()
        return path is not None and path.exists()

    def _colors_table(self, theme_data: Dict[str, Any]) -> str:
        return f"""{{
  foreground = '{theme_data.get('foreground', '#c0caf5')}',
  background = '{theme_data.get('background', '#1a1b26')}',
  cursor_bg = '{theme_data.get('cursor', '#c0caf5')}',
  cursor_fg = '{theme_data.get('background', '#1a1b26')}',
  cursor_border = '{theme_data.get('cursor', '#c0caf5')}',
  selection_bg = '{theme_data.get('selection', '#33467c')}',
  selection_fg = '{theme_data.get('foreground', '#c0caf5')}',
  ansi = {{
    '{theme_data.get('black', '#15161e')}',
    '{theme_data.get('red', '#f7768e')}',
    '{theme_data.get('green', '#9ece6a')}',
    '{theme_data.get('yellow', '#e0af68')}',
    '{theme_data.get('blue', '#7aa2f7')}',
    '{theme_data.get('magenta', '#bb9af7')}',
    '{theme_data.get('cyan', '#7dcfff')}',
    '{theme_data.get('white', '#a9b1d6')}',
  }},
  brights = {{
    '{theme_data.get('brightBlack', '#414868')}',
    '{theme_data.get('brightRed', '#f7768e')}',
    '{theme_data.get('brightGreen', '#9ece6a')}',
    '{theme_data.get('brightYellow', '#e0af68')}',
    '{theme_data.get('brightBlue', '#7aa2f7')}',
    '{theme_data.get('brightMagenta', '#bb9af7')}',
    '{theme_data.get('brightCyan', '#7dcfff')}',
    '{theme_data.get('brightWhite', '#c0caf5')}',
  }},
}}"""

    def _hook_lua(self, colors_path: Path) -> str:
        # yolu lua'ya gomerken ters slash'lari duz slash yapiyoruz, lua her iki
        # platformda da bunu kabul ediyor ve kacis derdi kalmiyor.
        # pcall ile sariyoruz: renk dosyasi silinse bile config yine acilsin
        lua_path = str(colors_path).replace("\\", "/")
        return (
            f"local tc_ok, tc_colors = pcall(dofile, '{lua_path}')\n"
            "if tc_ok and type(tc_colors) == 'table' and config ~= nil then\n"
            "  config.colors = tc_colors\n"
            "end"
        )

    def _insert_before_last_return(self, current: str, block: str) -> str:
        """Blogu dosyadaki en sondaki ust seviye `return` ifadesinden once koyar."""
        lines = current.split("\n")
        return_idx = None
        for i in range(len(lines) - 1, -1, -1):
            if re.match(r"^\s*return\b", lines[i]):
                return_idx = i
                break
        block_lines = block.rstrip("\n").split("\n")
        if return_idx is None:
            # return yoksa sona eklemek guvenli
            return current.rstrip() + "\n\n" + "\n".join(block_lines) + "\n"
        lines[return_idx:return_idx] = block_lines + [""]
        return "\n".join(lines)

    def apply_theme(self, theme_data: Dict[str, Any]) -> bool:
        path = self.get_config_path()
        if not path:
            return False

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            colors_table = self._colors_table(theme_data)

            if not current.strip():
                # bos/olmayan dosya -> dogrudan calisir bir config yaziyoruz
                standalone = (
                    "local wezterm = require 'wezterm'\n"
                    "local config = wezterm.config_builder and wezterm.config_builder() or {}\n"
                    f"config.colors = {colors_table}\n"
                    "return config\n"
                )
                path.write_text(standalone, encoding="utf-8")
                return True

            colors_path = path.parent / self.COLORS_FILE
            colors_path.write_text(
                "-- TermCraft tarafindan uretildi. her tema degisiminde uzerine yazilir\n"
                f"return {colors_table}\n",
                encoding="utf-8"
            )

            hook = f"{self.START_MARKER}\n{self._hook_lua(colors_path)}\n{self.END_MARKER}"

            if self.START_MARKER in current and self.END_MARKER in current:
                start = current.find(self.START_MARKER)
                end = current.find(self.END_MARKER) + len(self.END_MARKER)
                new_content = current[:start] + hook + current[end:]
            else:
                new_content = self._insert_before_last_return(current, hook)

            path.write_text(new_content, encoding="utf-8")
            return True
        except Exception:
            return False
