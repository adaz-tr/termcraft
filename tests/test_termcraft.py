import json
import pytest
from typer.testing import CliRunner

from termcraft.cli import app
from termcraft.core.theme_engine import ThemeEngine
from termcraft.core.prompt_engine import PromptEngine
from termcraft.core.alias_manager import AliasManager
from termcraft.core.doctor import TerminalDoctor
from termcraft.core.profiler import ShellProfiler
from termcraft.core.tool_hub import ToolHub
from termcraft.core.backup_sync import BackupManager
from termcraft.core.config_manager import ConfigManager
from termcraft.core.sync import filter_runnable_aliases
from termcraft.adapters.base import BaseShellAdapter
from termcraft.adapters.powershell import PowerShellAdapter
from termcraft.adapters.bash import BashAdapter
from termcraft.adapters.zsh import ZshAdapter
from termcraft.adapters.fish import FishAdapter
from termcraft.adapters.nushell import NuShellAdapter
from termcraft.adapters.terminals.windows_terminal import WindowsTerminalAdapter
from termcraft.adapters.terminals.alacritty import AlacrittyAdapter
from termcraft.adapters.terminals.kitty import KittyAdapter
from termcraft.adapters.terminals.wezterm import WezTermAdapter
from termcraft.adapters.terminals.base import BaseTerminalAdapter
from termcraft.config import AliasDefinition
from termcraft.i18n import STRINGS, t, set_language, get_current_language
from termcraft.presets.themes import BUILTIN_THEMES, BAT_THEME_MAP, resolve_theme_key, get_bat_theme
from termcraft.utils.gradient import (
    contrast_ratio,
    ensure_contrast,
    get_gradient_palette,
    is_dark,
    mix_hex,
    readable_on,
    render_gradient_text,
)
from termcraft.utils.font_detector import detect_nerd_fonts

runner = CliRunner()

SAMPLE_THEME = {
    "name": "TestTheme",
    "foreground": "#ffffff",
    "background": "#000000",
    "cursor": "#ffffff",
    "selection": "#333333",
    "black": "#000000",
    "red": "#ff0000",
    "green": "#00ff00",
    "yellow": "#ffff00",
    "blue": "#0000ff",
    "magenta": "#ff00ff",
    "cyan": "#00ffff",
    "white": "#ffffff",
}


# ---------------------------------------------------------------- CLI temelleri

def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "termcraft" in result.stdout


def test_cli_banner():
    result = runner.invoke(app, ["banner"])
    assert result.exit_code == 0


def test_cli_theme_list():
    result = runner.invoke(app, ["theme", "list"])
    assert result.exit_code == 0
    assert "tokyo-night" in result.stdout
    assert "cyber-gradient" in result.stdout


def test_cli_theme_preview_invalid():
    result = runner.invoke(app, ["theme", "preview", "nonexistent-theme-xyz"])
    assert result.exit_code == 1


def test_cli_theme_apply_invalid():
    result = runner.invoke(app, ["theme", "apply", "nonexistent-theme-xyz"])
    assert result.exit_code == 1


def test_cli_prompt_list():
    result = runner.invoke(app, ["prompt", "list"])
    assert result.exit_code == 0
    assert "modern-cyber" in result.stdout


def test_cli_prompt_apply_invalid():
    result = runner.invoke(app, ["prompt", "apply", "nonexistent-prompt-xyz"])
    assert result.exit_code == 1


def test_cli_prompt_preview_invalid_exits_nonzero():
    # eskiden olmayan preset icin de exit 0 doniyordu
    result = runner.invoke(app, ["prompt", "preview", "nonexistent-prompt-xyz"])
    assert result.exit_code == 1


def test_cli_alias_list():
    result = runner.invoke(app, ["alias", "list"])
    assert result.exit_code == 0
    assert "gs" in result.stdout


def test_cli_alias_bundle_invalid():
    result = runner.invoke(app, ["alias", "bundle", "nonexistent-bundle-xyz"])
    assert result.exit_code == 1


def test_cli_tools_list():
    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "Starship" in result.stdout


def test_cli_alias_add_and_remove():
    res_add = runner.invoke(app, ["alias", "add", "mytestalias", "echo hello world", "--desc", "Test", "--no-sync"])
    assert res_add.exit_code == 0
    assert "mytestalias" in res_add.stdout
    res_rem = runner.invoke(app, ["alias", "remove", "mytestalias", "--no-sync"])
    assert res_rem.exit_code == 0
    assert "mytestalias" in res_rem.stdout


def test_cli_alias_add_rejects_bad_name():
    # bosluk / noktali virgul iceren ad kabuk dosyasina satir olarak yazilamamali
    result = runner.invoke(app, ["alias", "add", "bad; rm -rf ~", "ls", "--no-sync"])
    assert result.exit_code == 1


def test_cli_init(no_shells):
    # hicbir kabuk yoksa exit 1 verip dosyaya dokunmamali
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1


def test_cli_backup_restore_missing_snapshot_has_clean_output():
    # typer.Exit RuntimeError turevi -> eskiden kendi except'ine yakalanip
    # cikitya bos bir "Error:" satiri ekliyordu
    result = runner.invoke(app, ["backup", "restore", "yok-boyle-bir-snapshot", "--yes"])
    assert result.exit_code == 1
    assert "Error:" not in result.stdout


# ---------------------------------------------------------------- i18n

def test_i18n_translation():
    set_language("tr")
    assert "TermCraft" in t("app_title")
    set_language("en")
    assert "TermCraft" in t("app_title")


def test_i18n_invalid_raise():
    with pytest.raises(ValueError):
        set_language("invalid_code_123")


def test_i18n_all_languages_have_same_keys():
    keys = [set(v.keys()) for v in STRINGS.values()]
    assert all(k == keys[0] for k in keys)


def test_cli_lang():
    assert runner.invoke(app, ["lang", "tr"]).exit_code == 0
    assert get_current_language() == "tr"
    assert runner.invoke(app, ["lang", "en"]).exit_code == 0
    assert get_current_language() == "en"


def test_cli_lang_invalid():
    result = runner.invoke(app, ["lang", "invalid-lang-code"])
    assert result.exit_code == 1


# ---------------------------------------------------------------- gradient / tema

def test_gradient_engine():
    palette = get_gradient_palette(["#000000", "#ffffff"], 10)
    assert len(palette) == 10
    assert palette[0] == "#000000"
    assert palette[-1] == "#ffffff"
    assert render_gradient_text("TermCraft Studio", palette_key="cyber-gradient") is not None


def test_color_helpers():
    assert is_dark("#08090f") is True
    assert is_dark("#eff1f5") is False
    assert readable_on("#00ffff") == "#000000"
    assert readable_on("#0a0a2a") == "#ffffff"
    assert mix_hex("#000000", "#ffffff", 0.5) == "#7f7f7f"
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, abs=0.1)


def test_ensure_contrast_only_adjusts_when_needed():
    """Acik temalarda aksan rengi panel uzerinde okunmuyordu."""
    panel_light = mix_hex("#eff1f5", "#000000", 0.14)
    teal = "#179299"
    assert contrast_ratio(teal, panel_light) < 4.5
    fixed = ensure_contrast(teal, panel_light, 4.5)
    assert contrast_ratio(fixed, panel_light) >= 4.5

    # zaten yeterliyse renge dokunulmamali
    panel_dark = mix_hex("#08090f", "#ffffff", 0.14)
    assert ensure_contrast("#00ffff", panel_dark, 4.5) == "#00ffff"


def test_studio_ui_is_readable_for_every_builtin_theme():
    """Her dahili tema icin stüdyonun kendi arayuzu okunur olmali.

    TUI artik temayi takip ettigi icin acik temalar (catppuccin-latte) header
    ve footer'i okunmaz hale getirebiliyordu.
    """
    from termcraft.tui.app import TermCraftStudioApp

    app = TermCraftStudioApp()
    for key, palette in BUILTIN_THEMES.items():
        built = app._build_textual_theme(palette, f"t-{key}")
        v = built.variables
        assert contrast_ratio(v["tc-header-fg"], v["tc-panel"]) >= 4.4, key
        assert contrast_ratio(v["tc-footer-fg"], v["tc-panel"]) >= 3.4, key
        assert contrast_ratio(v["tc-fg"], v["tc-bg"]) >= 3.0, key
        # buton yazilari kendi zeminlerinde okunmali
        assert contrast_ratio(v["tc-on-cyan"], v["tc-cyan"]) >= 3.0, key
        assert contrast_ratio(v["tc-on-green"], v["tc-green"]) >= 3.0, key
        assert contrast_ratio(v["tc-on-red"], v["tc-red"]) >= 3.0, key
        # acik tema koyu isaretlenmemeli
        assert built.dark == is_dark(palette["background"]), key


def test_theme_engine():
    engine = ThemeEngine()
    themes = engine.get_all_themes()
    for key in ("tokyo-night", "cyber-gradient", "sunset-gradient", "rival-gradient"):
        assert key in themes
    assert engine.get_theme("cyber-gradient")["background"] == "#08090f"


def test_theme_key_is_normalized_before_saving():
    # "Tokyo Night" gibi bir girdi config'e ham haliyle yazilirsa sonraki sync
    # BUILTIN_THEMES'te bulamayip fallback renklere dusuyordu
    engine = ThemeEngine()
    key, theme = engine.resolve("Tokyo Night")
    assert key == "tokyo-night"
    assert theme is not None


def test_every_theme_has_bat_mapping():
    assert not set(BUILTIN_THEMES) - set(BAT_THEME_MAP)
    assert get_bat_theme("Tokyo Night") == "tokyonight_night"
    assert resolve_theme_key("bilinmeyen") == "bilinmeyen"


def test_rival_gradient_is_not_a_copy_of_cyber():
    assert BUILTIN_THEMES["rival-gradient"]["name"] != BUILTIN_THEMES["cyber-gradient"]["name"]
    assert BUILTIN_THEMES["rival-gradient"]["background"] != BUILTIN_THEMES["cyber-gradient"]["background"]


# ---------------------------------------------------------------- alias

def test_alias_manager_persistence():
    mgr = AliasManager()
    mgr.add_alias("tc_persist_test", "echo persisted", "test description")
    assert any(a.name == "tc_persist_test" for a in mgr.aliases)

    fresh_mgr = AliasManager()
    assert any(a.name == "tc_persist_test" for a in fresh_mgr.aliases)

    fresh_mgr.remove_alias("tc_persist_test")
    assert not any(a.name == "tc_persist_test" for a in fresh_mgr.aliases)


def test_alias_name_validation():
    with pytest.raises(Exception):
        AliasDefinition(name="oops; rm -rf ~", command="ls")
    with pytest.raises(Exception):
        AliasDefinition(name="two words", command="ls")
    assert AliasDefinition(name="g.co-2", command="ls").name == "g.co-2"


def test_default_profile_does_not_shadow_core_commands():
    # modern-replacements varsayilan olarak yuklenmemeli, yoksa eza/zoxide
    # kurulu olmayan makinede ls ve cd bozuluyor
    names = {a.name for a in ConfigManager.get_instance().get_aliases()}
    assert not names & {"ls", "cat", "cd", "grep", "find"}


def test_aliases_with_missing_requirements_are_filtered(monkeypatch):
    aliases = [
        AliasDefinition(name="ls", command="eza", requires="eza"),
        AliasDefinition(name="gs", command="git status"),
    ]
    monkeypatch.setattr("termcraft.core.sync.shutil.which", lambda n: None)
    kept = filter_runnable_aliases(aliases)
    assert [a.name for a in kept] == ["gs"]


def test_doctor_reports_shadowing_aliases():
    mgr = AliasManager()
    mgr.load_bundle("modern-replacements")
    shadowing = {name for name, _ in mgr.check_shadowing()}
    assert "ls" in shadowing


# ---------------------------------------------------------------- kabuk adapterleri

def test_shell_adapters_generation():
    # her kabugun kendi alias sozdizimi var, ciktilarin birebir eslesmesi onemli
    aliases = [AliasDefinition(name="gs", command="git status", description="status")]
    assert "Set-Alias" in PowerShellAdapter().generate_alias_script(aliases)
    assert "alias gs='git status'" in BashAdapter().generate_alias_script(aliases)
    assert "alias gs='git status'" in ZshAdapter().generate_alias_script(aliases)
    assert 'alias gs "git status"' in FishAdapter().generate_alias_script(aliases)
    assert "alias gs = git status" in NuShellAdapter().generate_alias_script(aliases)


def test_unified_script_generation():
    pwsh = PowerShellAdapter()
    script = pwsh.generate_unified_script(
        env_vars={"BAT_THEME": "Dracula", "TERMCRAFT_THEME": "dracula"},
        aliases=[AliasDefinition(name="ga", command="git add .", description="add")],
        prompt_engine="starship",
        prompt_preset_name="modern-cyber"
    )
    assert "$env:BAT_THEME" in script
    assert "Set-Alias" in script
    assert "starship" in script


def test_fish_alias_escapes_dollar_and_backslash():
    """fish cift tirnak icinde $ genisletiyor.

    Kacirmazsak `alias h "echo $HOME"` tanimlama aninda cozuluyordu; bash'te
    tek tirnak kullandigimiz icin orada calisma aninda cozuluyor. Ikisi ayni
    davranmali.
    """
    script = FishAdapter().generate_alias_script([AliasDefinition(name="h", command="echo $HOME")])
    assert script == r'alias h "echo \$HOME"'

    # ters slash iki katlanmali (docker --format {{.ID}}\t{{.Names}} gibi komutlar icin),
    # fish cift tirnagi cozunce docker yine tek ters slash goruyor
    tabbed = [AliasDefinition(name="dps", command=r"docker ps --format {{.ID}}\t{{.Names}}")]
    out = FishAdapter().generate_alias_script(tabbed)
    assert r"\\t" in out

    # cift tirnak da kacirilmali
    quoted = FishAdapter().generate_alias_script([AliasDefinition(name="q", command='echo "hi"')])
    assert quoted == r'alias q "echo \"hi\""'


def test_powershell_no_duplicate_prompt_in_env():
    assert "function prompt" not in PowerShellAdapter().generate_env_script({"TEST_ENV": "1"})


def test_nushell_prompt_hook_is_guarded(tmp_path):
    # kurulum komutu her acilista degil, sadece dosya yoksa calismali
    hook = NuShellAdapter().generate_prompt_hook("starship")
    assert "path exists" in hook
    assert "which starship" in hook

    omp = NuShellAdapter().generate_prompt_hook("oh-my-posh", preset_path="C:/custom/preset.json")
    assert '--config "C:/custom/preset.json"' in omp


def test_inject_and_remove_block_roundtrip(tmp_path, monkeypatch):
    adapter = BashAdapter()
    rc = tmp_path / ".bashrc"
    rc.write_text("# kullanicinin kendi satiri\nexport MYVAR=1\n", encoding="utf-8")
    monkeypatch.setattr(adapter, "get_config_path", lambda: rc)

    assert adapter.inject_block("alias gs='git status'") is True
    content = rc.read_text(encoding="utf-8")
    assert "alias gs=" in content
    assert "export MYVAR=1" in content

    assert adapter.remove_block() is True
    after = rc.read_text(encoding="utf-8")
    assert "alias gs=" not in after
    assert "export MYVAR=1" in after
    assert BaseShellAdapter.START_MARKER not in after


# ---------------------------------------------------------------- terminal adapterleri

def test_terminal_adapters_base_inheritance():
    for inst in (WindowsTerminalAdapter(), AlacrittyAdapter(), KittyAdapter(), WezTermAdapter()):
        assert isinstance(inst, BaseTerminalAdapter)
        assert inst.name


def test_wezterm_writes_valid_config_for_empty_file(tmp_path, monkeypatch):
    adapter = WezTermAdapter()
    config_file = tmp_path / ".wezterm.lua"
    monkeypatch.setattr(adapter, "get_config_path", lambda: config_file)
    assert adapter.apply_theme(SAMPLE_THEME) is True
    assert "config.colors" in config_file.read_text(encoding="utf-8")


def test_wezterm_does_not_append_after_return(tmp_path, monkeypatch):
    """En kritik regresyon: lua'da `return` son ifade olmak zorunda.

    Eskiden blok dosyanin sonuna ekleniyordu ve kullanicinin wezterm config'i
    sozdizimi hatasi verip tamamen calismaz hale geliyordu.
    """
    adapter = WezTermAdapter()
    config_file = tmp_path / ".wezterm.lua"
    config_file.write_text(
        "local wezterm = require 'wezterm'\n"
        "local config = wezterm.config_builder()\n"
        "config.font_size = 12\n"
        "return config\n",
        encoding="utf-8"
    )
    monkeypatch.setattr(adapter, "get_config_path", lambda: config_file)
    assert adapter.apply_theme(SAMPLE_THEME) is True

    content = config_file.read_text(encoding="utf-8")
    lines = [ln for ln in content.split("\n") if ln.strip()]
    assert lines[-1].strip() == "return config", "return dosyanin son ifadesi olmali"
    assert "config.font_size = 12" in content, "kullanicinin ayari korunmali"
    assert (config_file.parent / WezTermAdapter.COLORS_FILE).exists()


def test_wezterm_reapply_does_not_duplicate_block(tmp_path, monkeypatch):
    adapter = WezTermAdapter()
    config_file = tmp_path / ".wezterm.lua"
    config_file.write_text("local config = {}\nreturn config\n", encoding="utf-8")
    monkeypatch.setattr(adapter, "get_config_path", lambda: config_file)
    adapter.apply_theme(SAMPLE_THEME)
    adapter.apply_theme(SAMPLE_THEME)
    assert config_file.read_text(encoding="utf-8").count(WezTermAdapter.START_MARKER) == 1


def test_alacritty_output_stays_valid_toml(tmp_path, monkeypatch):
    """Kullanicida zaten [colors.primary] varsa TOML duplicate-table veriyordu."""
    tomllib = pytest.importorskip("tomllib")
    adapter = AlacrittyAdapter()
    config_file = tmp_path / "alacritty.toml"
    config_file.write_text(
        '[window]\nopacity = 0.9\n\n[colors.primary]\nbackground = "#111111"\n',
        encoding="utf-8"
    )
    monkeypatch.setattr(adapter, "get_config_path", lambda: config_file)
    assert adapter.apply_theme(SAMPLE_THEME) is True

    parsed = tomllib.loads(config_file.read_text(encoding="utf-8"))
    assert parsed["colors"]["primary"]["background"] == "#000000"
    assert parsed["window"]["opacity"] == 0.9, "ilgisiz ayarlar korunmali"


def test_alacritty_reapply_stays_valid(tmp_path, monkeypatch):
    tomllib = pytest.importorskip("tomllib")
    adapter = AlacrittyAdapter()
    config_file = tmp_path / "alacritty.toml"
    config_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(adapter, "get_config_path", lambda: config_file)
    adapter.apply_theme(SAMPLE_THEME)
    adapter.apply_theme(SAMPLE_THEME)
    tomllib.loads(config_file.read_text(encoding="utf-8"))


def test_kitty_theme_block(tmp_path, monkeypatch):
    adapter = KittyAdapter()
    config_file = tmp_path / "kitty.conf"
    config_file.write_text("font_size 12\n", encoding="utf-8")
    monkeypatch.setattr(adapter, "get_config_path", lambda: config_file)
    assert adapter.apply_theme(SAMPLE_THEME) is True
    content = config_file.read_text(encoding="utf-8")
    assert "background #000000" in content
    assert "font_size 12" in content


def test_windows_terminal_missing_profiles_key(tmp_path, monkeypatch):
    adapter = WindowsTerminalAdapter()
    config_file = tmp_path / "settings.json"
    config_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(adapter, "get_config_path", lambda: config_file)
    assert adapter.apply_theme(SAMPLE_THEME) is True
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert data["profiles"]["defaults"]["colorScheme"] == "TermCraft TestTheme"


def test_windows_terminal_handles_jsonc_and_missing_name(tmp_path, monkeypatch):
    adapter = WindowsTerminalAdapter()
    config_file = tmp_path / "settings.json"
    config_file.write_text(
        '{\n  // kullanici yorumu\n  "schemes": [],\n  "profiles": { "list": [] },\n}',
        encoding="utf-8"
    )
    monkeypatch.setattr(adapter, "get_config_path", lambda: config_file)
    # isimsiz tema eskiden KeyError atiyordu
    assert adapter.apply_theme({"background": "#000000"}) is True
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert data["profiles"]["defaults"]["colorScheme"] == "TermCraft Theme"


# ---------------------------------------------------------------- doctor / profiler

def test_doctor_diagnostics():
    assert len(TerminalDoctor().run_diagnostics().checks) > 0


def test_doctor_diagnostics_no_side_effects():
    cfg_mgr = ConfigManager.get_instance()
    initial = len(cfg_mgr.get_aliases())
    TerminalDoctor().run_diagnostics()
    assert len(cfg_mgr.get_aliases()) == initial


def test_autofix_preserves_aliases_and_prompt(tmp_path, monkeypatch):
    """En kritik regresyon: `doctor --fix` tum blogu eziyordu.

    inject_block termcraft blogunu komple degistirdigi icin sadece env yazan
    bir auto_fix, daha once konmus alias'lari ve prompt hook'unu siliyordu.
    """
    adapter = BashAdapter()
    rc = tmp_path / ".bashrc"
    monkeypatch.setattr(adapter, "get_config_path", lambda: rc)
    monkeypatch.setattr("termcraft.core.sync.get_available_adapters", lambda: [adapter])

    from termcraft.core.sync import sync_all_shells
    AliasManager().add_alias("tcfixtest", "git status")
    sync_all_shells()
    before = rc.read_text(encoding="utf-8")
    assert "tcfixtest" in before
    assert "starship" in before

    TerminalDoctor().auto_fix()
    after = rc.read_text(encoding="utf-8")
    assert "tcfixtest" in after, "auto_fix alias'lari silmemeli"
    assert "starship" in after, "auto_fix prompt hook'unu silmemeli"
    assert "TERMCRAFT_INIT" in after, "auto_fix kendi env degiskenini eklemeli"


def test_autofix_does_not_touch_execution_policy_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr("termcraft.core.doctor.subprocess.run", lambda *a, **kw: calls.append(a))
    TerminalDoctor().auto_fix()
    assert calls == []


def test_profiler_reports_timeout_instead_of_not_found(monkeypatch):
    profiler = ShellProfiler()
    monkeypatch.setattr(profiler, "_run_once", lambda cmd: None)
    result = profiler.benchmark_shell(["fake-shell"], iterations=2)
    assert result["samples"] == 0
    assert result["timed_out"] is True


def test_profiler_collects_samples(monkeypatch):
    profiler = ShellProfiler()
    monkeypatch.setattr(profiler, "_run_once", lambda cmd: 42.0)
    result = profiler.benchmark_shell(["fake-shell"], iterations=3)
    assert result["available"] is True
    assert result["samples"] == 3
    assert result["avg_ms"] == 42.0


def test_tool_hub():
    assert len(ToolHub().get_tool_status()) >= 5


def test_font_detector_structure():
    res = detect_nerd_fonts()
    assert isinstance(res, dict)
    assert "JetBrainsMono Nerd Font" in res


# ---------------------------------------------------------------- config / backup

def test_config_manager_lang_persistence():
    cfg_mgr = ConfigManager.get_instance()
    cfg_mgr.set_language("en")
    assert cfg_mgr.get_language() == "en"
    cfg_mgr.set_theme("tokyo-night")
    assert cfg_mgr.get_language() == "en"
    cfg_mgr.set_language("tr")
    assert cfg_mgr.get_language() == "tr"


def test_broken_config_is_quarantined_not_deleted(isolated_home):
    from termcraft.utils.paths import get_config_file_path
    cfg_path = get_config_file_path()
    cfg_path.write_text("bu: [gecersiz: yaml: {{{", encoding="utf-8")

    ConfigManager.reset_instance()
    mgr = ConfigManager.get_instance()
    assert mgr.recovered_from is not None
    # eski icerik silinmemis, bir kenara alinmis olmali
    assert "gecersiz" in open(mgr.recovered_from, encoding="utf-8").read()


def test_backup_manager_full_cycle():
    # config.yaml'in diskte olmasi icin once ConfigManager'i ayaga kaldir
    ConfigManager.get_instance().save_config()
    bm = BackupManager()
    snapshot_dir = bm.create_snapshot(tag="test_full")
    assert snapshot_dir.exists()
    assert (snapshot_dir / "manifest.json").exists()
    assert (snapshot_dir / "config.yaml").exists()
    assert bm.restore_snapshot(snapshot_dir.name) is True


def test_snapshots_sorted_newest_first():
    bm = BackupManager()
    bm.create_snapshot(tag="zzz")
    bm.create_snapshot(tag="aaa")
    snaps = bm.list_snapshots()
    stamps = [s["timestamp"] for s in snaps]
    assert stamps == sorted(stamps, reverse=True)


def test_apply_theme_takes_backup_when_auto_backup_on(monkeypatch):
    called = []
    monkeypatch.setattr("termcraft.core.theme_engine.maybe_snapshot", lambda tag="auto": called.append(tag))
    monkeypatch.setattr("termcraft.core.theme_engine.get_available_terminal_adapters", lambda: [])
    monkeypatch.setattr("termcraft.core.theme_engine.sync_all_shells", lambda **kw: {})
    ThemeEngine().apply_theme("dracula")
    assert called == ["theme"]


def test_apply_starship_preset_takes_backup(monkeypatch):
    called = []
    monkeypatch.setattr("termcraft.core.prompt_engine.maybe_snapshot", lambda tag="auto": called.append(tag))
    monkeypatch.setattr("termcraft.core.prompt_engine.sync_all_shells", lambda **kw: {})
    PromptEngine().apply_starship_preset("minimal-pure")
    assert called == ["prompt"]


# ---------------------------------------------------------------- TUI

@pytest.mark.asyncio
async def test_tui_app_mount():
    from termcraft.tui.app import TermCraftStudioApp
    app_instance = TermCraftStudioApp()
    async with app_instance.run_test() as pilot:
        assert app_instance.is_running
        await pilot.pause()
