import shutil
from typing import Dict, List, Optional
from termcraft.config import AliasDefinition
from termcraft.core.config_manager import ConfigManager
from termcraft.adapters import get_available_adapters
from termcraft.presets.themes import BUILTIN_THEMES, resolve_theme_key, get_bat_theme, build_fzf_opts
from termcraft.utils.paths import get_starship_config_path, get_termcraft_dir


def filter_runnable_aliases(aliases: List[AliasDefinition]) -> List[AliasDefinition]:
    """`requires` alani dolu olup binary'si PATH'te olmayan alias'lari eler.

    Bu olmadan `alias ls='eza ...'` eza kurulu olmasa bile profile yaziliyor ve
    kullanicinin `ls` komutu tamamen bozuluyordu.
    """
    result = []
    for a in aliases:
        req = getattr(a, "requires", None)
        if req and shutil.which(req) is None:
            continue
        result.append(a)
    return result


def sync_all_shells(
    custom_theme: Optional[str] = None,
    custom_prompt_engine: Optional[str] = None,
    custom_prompt_preset: Optional[str] = None,
    extra_env: Optional[Dict[str, str]] = None
) -> Dict[str, bool]:
    """Tek giris noktasi: config'i okuyup her kabuk icin blogu bastan uretir.

    Tema uygulamak, alias eklemek, prompt degistirmek, doctor'un otomatik
    onarimi -> hepsi buraya cikiyor. Boylece profil dosyasindaki termcraft
    blogu her zaman butun halinde ve tutarli kaliyor. Blogun bir kismini
    tek basina yazan hicbir cagri olmamali, yoksa geri kalani siliniyor.
    """
    cfg_mgr = ConfigManager.get_instance()
    cfg = cfg_mgr.config

    theme_name = resolve_theme_key(custom_theme or cfg.theme.active_theme)
    engine = custom_prompt_engine or cfg.prompt.engine
    preset = custom_prompt_preset or cfg.prompt.preset
    aliases = filter_runnable_aliases(cfg_mgr.get_aliases())

    theme_data = BUILTIN_THEMES.get(theme_name, {})

    env_vars = {
        "BAT_THEME": get_bat_theme(theme_name),
        "FZF_DEFAULT_OPTS": build_fzf_opts(theme_data),
        "TERMCRAFT_THEME": theme_name
    }
    if extra_env:
        env_vars.update(extra_env)

    # starship kendi config'ini ~/.config/starship.toml'dan okuyor, oh-my-posh'a ise
    # json dosyasinin yolunu acikca vermek gerekiyor
    preset_path = None
    if engine == "starship":
        preset_path = str(get_starship_config_path())
    elif engine == "oh-my-posh":
        preset_path = str(get_termcraft_dir() / "prompts" / f"{preset}.json")

    results = {}
    for adapter in get_available_adapters():
        script = adapter.generate_unified_script(
            env_vars=env_vars,
            aliases=aliases,
            prompt_engine=engine,
            prompt_preset_path=preset_path,
            prompt_preset_name=preset
        )
        results[adapter.name] = adapter.inject_block(script)

    return results


def unsync_all_shells() -> Dict[str, bool]:
    """Termcraft blogunu tum kabuk profillerinden temizler (`termcraft uninstall`)."""
    results = {}
    for adapter in get_available_adapters():
        try:
            results[adapter.name] = adapter.remove_block()
        except Exception:
            results[adapter.name] = False
    return results
