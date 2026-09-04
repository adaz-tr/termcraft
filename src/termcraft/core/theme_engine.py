import json
import yaml
from typing import Dict, Any, Optional, Tuple
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from termcraft.presets.themes import BUILTIN_THEMES, GRADIENT_THEME_KEYS, resolve_theme_key
from termcraft.adapters.terminals import get_available_terminal_adapters
from termcraft.utils.paths import get_termcraft_dir
from termcraft.utils.gradient import render_gradient_text, get_gradient_palette, GRADIENT_PALETTES
from termcraft.i18n import get_current_language
from termcraft.core.config_manager import ConfigManager
from termcraft.core.sync import sync_all_shells
from termcraft.core.backup_sync import maybe_snapshot

# temalari (dahili + ~/.termcraft/themes altindaki ozel json/yaml) toplayip
# terminal emulatorlerine ve kabuk araclarina dagitan katman
class ThemeEngine:
    def __init__(self):
        self.custom_themes_dir = get_termcraft_dir() / "themes"
        self.custom_themes_dir.mkdir(parents=True, exist_ok=True)
        self.config_mgr = ConfigManager.get_instance()

    def get_all_themes(self) -> Dict[str, Dict[str, Any]]:
        # kullanici temalari dahili olanlari ezebilsin diye once builtin'leri koyup
        # ustune dosyadan okunanlari yaziyoruz
        themes = dict(BUILTIN_THEMES)
        for file in self.custom_themes_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    themes[file.stem] = data
            except Exception:
                pass
        for pattern in ("*.yaml", "*.yml"):
            for file in self.custom_themes_dir.glob(pattern):
                try:
                    data = yaml.safe_load(file.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        themes[file.stem] = data
                except Exception:
                    pass
        return themes

    def resolve(self, name: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Kullanicinin yazdigi ismi (anahtar, tema) ciftine cevirir.

        Bu ayrim onemli: config'e her zaman normalize edilmis ANAHTAR yazilmali.
        Eskiden ham isim kaydediliyordu ve "Tokyo Night" gibi bir girdi sonraki
        sync'te BUILTIN_THEMES icinde bulunamayip fallback renklere dusuyordu.
        """
        all_themes = self.get_all_themes()
        if name in all_themes:
            return name, all_themes[name]
        normalized = resolve_theme_key(name)
        if normalized in all_themes:
            return normalized, all_themes[normalized]
        normalized = name.lower().strip().replace(" ", "-").replace("_", "-")
        if normalized in all_themes:
            return normalized, all_themes[normalized]
        return None, None

    def get_theme(self, name: str) -> Optional[Dict[str, Any]]:
        return self.resolve(name)[1]

    def apply_theme(self, name: str) -> Dict[str, bool]:
        key, theme = self.resolve(name)
        if not key or not theme:
            raise ValueError(f"Theme '{name}' not found.")

        # terminal config'lerinin ustune yazmadan once yedek al
        maybe_snapshot(tag="theme")

        self.config_mgr.set_theme(key)
        results: Dict[str, bool] = {}

        for adapter in get_available_terminal_adapters():
            results[adapter.name] = adapter.apply_theme(theme)

        results.update(sync_all_shells(custom_theme=key))
        return results

    def _gradient_palette_key(self, theme_key: str) -> str:
        # gradient temanin kendi paleti varsa onu kullan, yoksa varsayilana dus
        if theme_key in GRADIENT_PALETTES:
            return theme_key
        return "cyber-gradient"

    def render_theme_preview(self, theme_key: str) -> Panel:
        # CLI ve TUI ayni onizlemeyi kullaniyor. i18n icin t() yerine burada elle
        # tr/en kontrolu var, cunku etiketler sadece burada geciyor
        key, theme = self.resolve(theme_key)
        if not theme:
            return Panel(Text(f"Theme '{theme_key}' not found", style="bold red"))
        theme_key = key or theme_key

        is_tr = get_current_language() == "tr"
        lbl_name = "İsim:" if is_tr else "Name:"
        lbl_author = "Geliştirici:" if is_tr else "Author:"
        lbl_bg = "Arka Plan:" if is_tr else "Background:"
        lbl_fg = "Ön Plan:" if is_tr else "Foreground:"
        lbl_palette = "Palet:" if is_tr else "Palette:"
        lbl_sample = "Örnek Çıktı:" if is_tr else "Sample Code:"

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold #00d4ff", width=14)
        table.add_column()

        is_grad = bool(theme.get("is_gradient", False)) or theme_key in GRADIENT_THEME_KEYS
        theme_title = theme.get("name", theme_key)

        if is_grad:
            title_text = render_gradient_text(theme_title, palette_key=self._gradient_palette_key(theme_key), mode="2d")
            table.add_row(lbl_name, title_text)
        else:
            table.add_row(lbl_name, theme_title)

        table.add_row(lbl_author, theme.get("author", "Community"))
        table.add_row(lbl_bg, Text(theme.get("background", "#000000"), style=f"bold {theme.get('foreground', '#ffffff')} on {theme.get('background', '#000000')}"))
        table.add_row(lbl_fg, Text(theme.get("foreground", "#ffffff"), style=f"bold {theme.get('foreground', '#ffffff')}"))

        palette_text = Text()
        if is_grad:
            stops = theme.get("gradient_stops", ["#00ffff", "#ff00ff"])
            for c in get_gradient_palette(stops, 36):
                palette_text.append("█", style=c)
            palette_text.append(" [24-bit RGB Gradient]\n", style="bold #00ffff")
        else:
            for color_key in ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]:
                palette_text.append(" ██ ", style=theme.get(color_key, "#ffffff"))
            palette_text.append("\n")

        for color_key in ["brightBlack", "brightRed", "brightGreen", "brightYellow", "brightBlue", "brightMagenta", "brightCyan", "brightWhite"]:
            palette_text.append(" ██ ", style=theme.get(color_key, "#ffffff"))

        table.add_row(lbl_palette, palette_text)

        # temanin gercekte nasil gorunecegini anlatmak icin sahte bir git status ciktisi
        mock_terminal = Text()
        mock_terminal.append("❯ ", style=f"bold {theme.get('green', '#00ff00')}")
        mock_terminal.append("git status\n", style=f"bold {theme.get('foreground', '#ffffff')}")
        mock_terminal.append("On branch ", style=theme.get("foreground", "#ffffff"))
        mock_terminal.append("main\n", style=f"bold {theme.get('magenta', '#ff00ff')}")
        mock_terminal.append("Your branch is up to date with 'origin/main'.\n", style=f"dim {theme.get('foreground', '#ffffff')}")
        mock_terminal.append("Changes not staged for commit:\n", style=theme.get("yellow", "#ffff00"))
        mock_terminal.append("  modified:   src/termcraft/cli.py\n", style=theme.get("red", "#ff0000"))
        mock_terminal.append("  untracked:  themes/custom.json\n", style=theme.get("green", "#00ff00"))

        table.add_row(lbl_sample, mock_terminal)

        border_color = "#00d4ff" if is_grad else theme.get("cyan", theme.get("blue", "blue"))
        panel_title = f"[bold #00ffff]⚡ {theme_title} ⚡[/bold #00ffff]" if is_grad else f"[bold]{theme_title}[/bold]"

        return Panel(table, title=panel_title, border_style=border_color, padding=(1, 2))
