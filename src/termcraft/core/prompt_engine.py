from typing import Dict, Any, Optional
from rich.panel import Panel
from rich.text import Text
from termcraft.presets.prompts import STARSHIP_PRESETS, OH_MY_POSH_PRESETS
from termcraft.utils.paths import get_starship_config_path, get_termcraft_dir
from termcraft.core.config_manager import ConfigManager
from termcraft.core.sync import sync_all_shells
from termcraft.core.backup_sync import maybe_snapshot

# starship/oh-my-posh preset'lerini diske yazip ardindan kabuklari senkronluyor
class PromptEngine:
    def __init__(self):
        self.custom_prompts_dir = get_termcraft_dir() / "prompts"
        self.custom_prompts_dir.mkdir(parents=True, exist_ok=True)
        self.config_mgr = ConfigManager.get_instance()

    def get_starship_presets(self) -> Dict[str, Dict[str, Any]]:
        return STARSHIP_PRESETS

    def get_oh_my_posh_presets(self) -> Dict[str, Dict[str, Any]]:
        return OH_MY_POSH_PRESETS

    def get_preset(self, preset_key: str) -> Optional[Dict[str, Any]]:
        return STARSHIP_PRESETS.get(preset_key) or OH_MY_POSH_PRESETS.get(preset_key)

    def apply_starship_preset(self, preset_key: str) -> bool:
        preset = STARSHIP_PRESETS.get(preset_key)
        if not preset:
            raise ValueError(f"Starship preset '{preset_key}' not found.")

        # kullanicinin mevcut starship.toml'unu komple eziyoruz, once yedegini al
        maybe_snapshot(tag="prompt")

        target_path = get_starship_config_path()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(preset["config_toml"], encoding="utf-8")

        self.config_mgr.set_prompt("starship", preset_key)
        sync_all_shells(custom_prompt_engine="starship", custom_prompt_preset=preset_key)
        return True

    def apply_oh_my_posh_preset(self, preset_key: str) -> bool:
        preset = OH_MY_POSH_PRESETS.get(preset_key)
        if not preset:
            raise ValueError(f"Oh-My-Posh preset '{preset_key}' not found.")

        maybe_snapshot(tag="prompt")

        target_path = self.custom_prompts_dir / f"{preset_key}.json"
        target_path.write_text(preset["config_json"], encoding="utf-8")

        self.config_mgr.set_prompt("oh-my-posh", preset_key)
        sync_all_shells(custom_prompt_engine="oh-my-posh", custom_prompt_preset=preset_key)
        return True

    def apply_preset(self, preset_key: str, engine: Optional[str] = None) -> str:
        """Motoru preset'in kendisinden bulup uygular, uygulanan motoru dondurur.

        CLI'daki --engine bayragi yanlis yazildiginda sessizce yanlis motora
        gitmesin diye once preset'in hangi katalogda oldugna bakiyoruz.
        """
        if engine == "oh-my-posh" or (engine is None and preset_key in OH_MY_POSH_PRESETS):
            if preset_key in OH_MY_POSH_PRESETS:
                self.apply_oh_my_posh_preset(preset_key)
                return "oh-my-posh"
        if preset_key in STARSHIP_PRESETS:
            self.apply_starship_preset(preset_key)
            return "starship"
        if preset_key in OH_MY_POSH_PRESETS:
            self.apply_oh_my_posh_preset(preset_key)
            return "oh-my-posh"
        raise ValueError(f"Prompt preset '{preset_key}' not found.")

    def render_prompt_preview(self, preset_key: str) -> Panel:
        # gercek prompt'u calistirmiyoruz, sadece nasil gorunecegini elle taklit ediyoruz.
        # yeni preset eklerken buraya da bir dal eklemek lazim yoksa generic ornek cikiyor
        preset = self.get_preset(preset_key)
        if not preset:
            return Panel(Text(f"Preset '{preset_key}' not found", style="bold red"), border_style="red")

        sample = Text()
        if preset_key == "modern-cyber":
            sample.append("  ", style="bold #7aa2f7")
            sample.append("  ~/projects/termcraft ", style="bold #7aa2f7")
            sample.append("  main ", style="bold #bb9af7")
            sample.append(" [⇡1 ✗1] ", style="bold #f7768e")
            sample.append("  3.12 ", style="bold #e0af68")
            sample.append("  20.10 ", style="bold #9ece6a")
            sample.append(" took 1.2s ", style="bold #e0af68")
            sample.append("\n ➜ ", style="bold #00ffcc")
        elif preset_key == "minimal-pure":
            sample.append("projects/termcraft ", style="bold cyan")
            sample.append("git:main ", style="bold yellow")
            sample.append("\n❯ ", style="bold green")
        elif preset_key == "powerline-gradient":
            sample.append(" ", style="#89b4fa")
            sample.append("  termcraft ", style="bg:#89b4fa fg:#11111b bold")
            sample.append("", style="bg:#fab387 fg:#89b4fa")
            sample.append("  main ", style="bg:#fab387 fg:#11111b bold")
            sample.append("", style="bg:#a6e3a1 fg:#fab387")
            sample.append("  v3.12 ", style="bg:#a6e3a1 fg:#11111b bold")
            sample.append("", style="fg:#a6e3a1")
            sample.append("\n ➜ ", style="bold #a6e3a1")
        else:
            sample.append("  ~/repo ", style="bg:#89b4fa fg:#11111b bold")
            sample.append("  main ", style="bg:#a6e3a1 fg:#11111b bold")
            sample.append("\n❯ ", style="bold #89b4fa")

        return Panel(
            sample,
            title=f"[bold yellow]Prompt Preset: {preset['name']}[/bold yellow]",
            subtitle=f"[dim]{preset['description']}[/dim]",
            border_style="cyan",
            padding=(1, 2)
        )
