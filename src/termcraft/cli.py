import sys
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# windows konsolu default'ta ANSI escape'leri yutuyor, VT modunu elle acmazsak
# butun gradient/renk isi duz metin olarak dokuluyor ekrana. cp1254 olayi da cabasi
# not: bu blok import'lardan once calismali, console olusturulmadan
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004 | 0x0001 | 0x0002)
    except Exception:
        pass

# terminale yaziyorsak renkleri zorla (windows'ta rich bazen legacy moda dusuyor),
# ama pipe/dosyaya yazarken kapali biraksin - yoksa `termcraft theme list > x.txt`
# dosyaya escape kodlarini dolduruyor
_IS_TTY = sys.stdout.isatty()
console = Console(
    color_system="truecolor" if _IS_TTY else None,
    force_terminal=True if _IS_TTY else None,
    legacy_windows=False
)

from termcraft import __version__, __app_name__
from termcraft.utils.banner import print_banner
from termcraft.core.theme_engine import ThemeEngine
from termcraft.core.prompt_engine import PromptEngine
from termcraft.core.alias_manager import AliasManager
from termcraft.core.tool_hub import ToolHub
from termcraft.core.doctor import TerminalDoctor
from termcraft.core.profiler import ShellProfiler
from termcraft.core.backup_sync import BackupManager
from termcraft.core.config_manager import ConfigManager
from termcraft.core.sync import sync_all_shells, unsync_all_shells
from termcraft.presets.aliases import list_bundle_names
from termcraft.tui.app import run_tui
from termcraft.adapters import get_available_adapters
from termcraft.i18n import t, set_language

# ana uygulama + alt komut gruplari. her grup ayri Typer, asagida add_typer ile bagli
app = typer.Typer(
    name="termcraft",
    help="Universal Terminal & CLI Customization, Theming, Profiling and Management Suite",
    no_args_is_help=False
)

theme_app = typer.Typer(help="Manage and apply terminal color themes")
prompt_app = typer.Typer(help="Manage and customize terminal prompts (Starship & Oh-My-Posh)")
alias_app = typer.Typer(help="Universal cross-shell alias and shortcut manager")
tools_app = typer.Typer(help="Discover, check and install modern CLI tools", no_args_is_help=True)
backup_app = typer.Typer(help="Backup, restore and manage terminal configuration snapshots")

app.add_typer(theme_app, name="theme")
app.add_typer(prompt_app, name="prompt")
app.add_typer(alias_app, name="alias")
app.add_typer(tools_app, name="tools")
app.add_typer(backup_app, name="backup")


def _warn_if_config_recovered() -> None:
    # bozuk config karantinaya alindiysa kullaniciyi sessiz birakma
    mgr = ConfigManager.get_instance()
    if mgr.recovered_from:
        console.print(f"[yellow]⚠ {t('config_recovered', path=mgr.recovered_from)}[/yellow]")
        mgr.recovered_from = None


# alt komut verilmeden `termcraft` yazilirsa buraya duser, banner basip cikiyoruz
@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(None, "--version", "-v", help="Show TermCraft version"),
    animated: bool = typer.Option(False, "--animated", "-a", help="Animate banner gradient")
):
    if version:
        console.print(f"[bold #00ffff]{__app_name__}[/bold #00ffff] version [bold #00ff99]{__version__}[/bold #00ff99]")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        print_banner(animated=animated)
        console.print(
            "\n[bold #00ffff]Run [bold #ffcc00]termcraft studio[/bold #ffcc00] for the interactive TUI "
            "or [bold #ffcc00]termcraft --help[/bold #ffcc00] for CLI commands.[/bold #00ffff]\n"
        )


@app.command(name="banner")
def cmd_banner(
    palette: str = typer.Option("cyber-gradient", "--palette", "-p", help="Gradient palette key"),
    animated: bool = typer.Option(False, "--animated", "-a", help="Run animated color shifting loop"),
    loops: int = typer.Option(2, "--loops", "-l", help="Number of animation cycles")
):
    print_banner(palette_key=palette, animated=animated, loops=loops)


@app.command(name="lang")
def cmd_lang(
    language: str = typer.Argument(..., help="Language code ('tr' for Türkçe, 'en' for English)")
):
    try:
        set_language(language)
    except ValueError:
        console.print(f"[bold red]✗ {t('invalid_lang', lang=language, supported='tr, en')}[/bold red]")
        raise typer.Exit(code=1)
    console.print(f"[bold green]✔ {t('lang_changed')}[/bold green]")


@app.command(name="studio")
def cmd_studio():
    run_tui()


@app.command(name="tui")
def cmd_tui():
    run_tui()


@app.command(name="doctor")
def cmd_doctor(
    fix: bool = typer.Option(False, "--fix", "-f", help="Automatically apply recommended environment fixes"),
    exec_policy: bool = typer.Option(
        False, "--exec-policy",
        help="With --fix, also set PowerShell ExecutionPolicy to RemoteSigned (CurrentUser)"
    )
):
    _warn_if_config_recovered()
    console.print(Panel(f"[bold #ffcc00]🩺 {t('run_doctor_now')}[/bold #ffcc00]", border_style="#0099ff"))
    doctor = TerminalDoctor()
    report = doctor.run_diagnostics()

    # rapor satirlarini renkli tabloya cevir. status degerleri: pass / warn / info
    table = Table(show_header=True, header_style="bold #a800ff", expand=True)
    table.add_column(t("col_status"), width=10, justify="center")
    table.add_column(t("col_check"), style="bold #00ffff", width=24)
    table.add_column(t("col_result"), style="white")
    table.add_column(t("col_recommendation"), style="#ffcc00")

    for c in report.checks:
        st = c["status"]
        if st == "pass":
            status_text = Text("[PASS]", style="bold #00ff99")
        elif st == "warn":
            status_text = Text("[WARN]", style="bold #ffcc00")
        else:
            status_text = Text("[INFO]", style="bold #0099ff")
        table.add_row(status_text, c["title"], c["message"], c["fix_suggestion"])

    console.print(table)

    if fix:
        # ExecutionPolicy sistem ayari degistirdigi icin acikca onay istiyoruz
        run_policy = exec_policy
        if sys.platform == "win32" and not exec_policy and _IS_TTY:
            run_policy = typer.confirm(t("execpolicy_prompt"), default=False)

        console.print("\n[bold #00ffff]🔧 Applying automatic fixes...[/bold #00ffff]")
        for action in doctor.auto_fix(set_execution_policy=run_policy):
            console.print(f"[bold green]✔ {action}[/bold green]")
        console.print("[bold #00ff99]Auto-fix routine finished![/bold #00ff99]")


@app.command(name="benchmark")
def cmd_benchmark(
    iterations: int = typer.Option(3, "--iterations", "-i", help="Number of benchmark iterations per shell")
):
    console.print(f"[bold #00ffff]⏱️  Measuring shell startup latency ({iterations} iterations)...[/bold #00ffff]")
    profiler = ShellProfiler()
    results = profiler.run_all_benchmarks(iterations=iterations)

    table = Table(show_header=True, header_style="bold #00ffff", expand=True)
    table.add_column(t("col_shell"), style="bold white")
    table.add_column(t("col_status"), justify="center")
    table.add_column(t("col_avg"), justify="right", style="bold #ffcc00")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column(t("col_rating"), justify="center")

    # esikler tamamen gozle ayarlandi, bilimsel bir dayanagi yok
    # 75ms alti cok iyi, 180 ustu profil dosyasinda bir seyler sisiyor demektir
    for name, data in results.items():
        if data["samples"]:
            avg = data["avg_ms"]
            if avg < 75:
                rating = f"[bold #00ff99]⚡ {t('rate_fast')}[/bold #00ff99]"
            elif avg < 180:
                rating = f"[bold #ffcc00]✔ {t('rate_normal')}[/bold #ffcc00]"
            else:
                rating = f"[bold #ff0055]⚠ {t('rate_slow')}[/bold #ff0055]"
            table.add_row(
                name,
                f"[bold #00ff99]{t('st_available')}[/bold #00ff99]",
                f"{avg} ms", f"{data['min_ms']} ms", f"{data['max_ms']} ms", rating
            )
        else:
            # kabuk kurulu ama olcum alinamadi (timeout) -> "bulunamadi" demek yaniltici
            label = "timeout" if data.get("timed_out") else t("st_not_found")
            table.add_row(name, f"[dim]{label}[/dim]", "-", "-", "-", "-")

    console.print(table)


@app.command(name="init")
def cmd_init():
    _warn_if_config_recovered()
    console.print("[bold #00ffff]🚀 Initializing TermCraft environment and shell hooks...[/bold #00ffff]")
    # once bir kabuk var mi diye bak, yoksa bosuna dosya yazmayalim
    if not get_available_adapters():
        console.print("[bold #ff0055]No supported shells detected.[/bold #ff0055]")
        raise typer.Exit(code=1)

    for s_name, ok in sync_all_shells().items():
        if ok:
            console.print(f"[green]✔ Injected unified TermCraft hook into {s_name}[/green]")
        else:
            console.print(f"[yellow]⚠ Failed to inject hook for {s_name}[/yellow]")
    console.print(f"\n[bold #00ff99]✔ {t('init_done')}[/bold #00ff99]")


@app.command(name="uninstall")
def cmd_uninstall(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """TermCraft blogunu tum kabuk profillerinden kaldirir."""
    if not yes and _IS_TTY and not typer.confirm(t("restore_confirm"), default=False):
        console.print(f"[yellow]{t('aborted')}[/yellow]")
        raise typer.Exit()
    for s_name, ok in unsync_all_shells().items():
        st = "[green]removed[/green]" if ok else "[dim]nothing to remove[/dim]"
        console.print(f"  • {s_name}: {st}")
    console.print(f"[bold #00ff99]✔ {t('uninstall_done')}[/bold #00ff99]")


@theme_app.command(name="list")
def theme_list():
    engine = ThemeEngine()
    themes = engine.get_all_themes()

    table = Table(title="🎨 Available Color Themes", header_style="bold #a800ff", expand=True)
    table.add_column("Theme ID", style="bold #00ffff")
    table.add_column("Theme Name", style="bold white")
    table.add_column("Author", style="dim")
    table.add_column("Color Swatches (Hex Palette)")

    for k, v in themes.items():
        swatches = Text()
        # gradient temalarin 16 renkli ANSI paleti yerine stop listesi var,
        # tabloda tek satirda gostermek icin duz bir bar cizip geciyoruz
        if v.get("is_gradient"):
            swatches.append("█" * 18, style=v.get("foreground", "#00ffff"))
            swatches.append(" [RGB Gradient]", style="bold #ff00cc")
        else:
            for color_key in ["background", "red", "green", "yellow", "blue", "magenta", "cyan", "foreground"]:
                swatches.append(" ██ ", style=v.get(color_key, "#ffffff"))
        table.add_row(k, v.get("name", k), v.get("author", "Community"), swatches)

    console.print(table)


@theme_app.command(name="apply")
def theme_apply(theme_name: str = typer.Argument(..., help="Name of theme to apply")):
    engine = ThemeEngine()
    try:
        results = engine.apply_theme(theme_name)
    except ValueError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error applying theme: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]✔ {t('theme_apply_ok')} ([cyan]{theme_name}[/cyan])[/bold green]")
    for target, ok in results.items():
        st = "[green]Applied[/green]" if ok else "[yellow]Failed / Skipped[/yellow]"
        console.print(f"  • {target}: {st}")
    console.print(f"\n[dim yellow]ℹ {t('reload_hint')}[/dim yellow]")


@theme_app.command(name="preview")
def theme_preview(theme_name: str = typer.Argument(..., help="Theme name to preview")):
    engine = ThemeEngine()
    if not engine.get_theme(theme_name):
        console.print(f"[bold red]Error: Theme '{theme_name}' not found.[/bold red]")
        raise typer.Exit(code=1)
    console.print(engine.render_theme_preview(theme_name))


@prompt_app.command(name="list")
def prompt_list():
    engine = PromptEngine()

    table = Table(title="⚡ Available Prompt Presets", header_style="bold #00ffff", expand=True)
    table.add_column("Engine", style="bold #ffcc00")
    table.add_column("Preset ID", style="bold white")
    table.add_column("Name", style="bold #00ff99")
    table.add_column("Description")

    for k, v in engine.get_starship_presets().items():
        table.add_row("Starship", k, v["name"], v["description"])
    for k, v in engine.get_oh_my_posh_presets().items():
        table.add_row("Oh-My-Posh", k, v["name"], v["description"])

    console.print(table)


@prompt_app.command(name="apply")
def prompt_apply(
    preset_name: str = typer.Argument(..., help="Preset identifier to apply"),
    engine: Optional[str] = typer.Option(None, "--engine", "-e", help="Force prompt engine (starship or oh-my-posh)")
):
    p_engine = PromptEngine()
    try:
        # motoru preset'in kendisinden buluyoruz, --engine yanlis yazildiginda
        # sessizce yanlis motora gitmesin diye
        used = p_engine.apply_preset(preset_name, engine=engine)
    except ValueError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error applying prompt: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold #00ff99]✔ {t('prompt_applied', preset=preset_name)} ({used})[/bold #00ff99]")
    console.print(f"\n[dim yellow]ℹ {t('reload_hint')}[/dim yellow]")


@prompt_app.command(name="preview")
def prompt_preview(preset_name: str = typer.Argument(..., help="Preset identifier to preview")):
    p_engine = PromptEngine()
    if not p_engine.get_preset(preset_name):
        console.print(f"[bold red]Error: Preset '{preset_name}' not found.[/bold red]")
        raise typer.Exit(code=1)
    console.print(p_engine.render_prompt_preview(preset_name))


@alias_app.command(name="list")
def alias_list(
    cheat: bool = typer.Option(False, "--cheat", "-c", help="Show in condensed cheat-sheet format")
):
    mgr = AliasManager()
    table = Table(title="🛠️  Configured Aliases & Shortcuts", header_style="bold #a800ff", expand=True)
    table.add_column(t("col_alias"), style="bold #00ffff", width=12)
    table.add_column(t("col_command"), style="bold #00ff99")
    table.add_column(t("col_description"), style="white")
    # --cheat modunda shells kolonu hic eklenmedigi icin 3 hucre veriyoruz
    if not cheat:
        table.add_column(t("col_shells"), style="dim")

    for a in mgr.aliases:
        if cheat:
            table.add_row(a.name, a.command, a.description)
        else:
            table.add_row(a.name, a.command, a.description, ", ".join(a.shells))

    console.print(table)


@alias_app.command(name="bundle")
def alias_bundle(
    bundle_name: str = typer.Argument(..., help="Bundle name (git, docker, dev, modern-replacements)")
):
    mgr = AliasManager()
    try:
        count = mgr.load_bundle(bundle_name)
    except ValueError:
        console.print(f"[bold red]{t('bundle_unknown', bundle=bundle_name, available=', '.join(list_bundle_names()))}[/bold red]")
        raise typer.Exit(code=1)

    mgr.sync_to_shells()
    console.print(f"[bold green]✔ {t('bundle_loaded', bundle=bundle_name)} ({count})[/bold green]")

    # golgeleyen alias yuklendiyse kullaniciyi uyar, sessizce ls/cd bozulmasin
    shadowing = mgr.check_shadowing()
    if shadowing:
        desc = ", ".join([f"{n} -> {c}" for n, c in shadowing])
        console.print(f"[yellow]⚠ {t('alias_shadowing', aliases=desc)}[/yellow]")
        console.print(f"[dim yellow]  {t('alias_shadowing_hint')}[/dim yellow]")
    missing = mgr.check_missing_requirements()
    if missing:
        desc = ", ".join([f"{n} ({r})" for n, r in missing])
        console.print(f"[yellow]⚠ {t('alias_missing_tool', aliases=desc)}[/yellow]")


@alias_app.command(name="add")
def alias_add(
    name: str = typer.Argument(..., help="Alias name (e.g. gco)"),
    command: str = typer.Argument(..., help="Command to execute (e.g. git checkout)"),
    description: str = typer.Option("", "--desc", "-d", help="Short description"),
    requires: Optional[str] = typer.Option(None, "--requires", "-r", help="Binary that must exist on PATH"),
    sync: bool = typer.Option(True, "--sync/--no-sync", help="Automatically synchronize to shell profiles")
):
    mgr = AliasManager()
    try:
        new_alias = mgr.add_alias(name=name, command=command, description=description, requires=requires)
    except Exception as e:
        console.print(f"[bold red]{t('invalid_alias_name', reason=e)}[/bold red]")
        raise typer.Exit(code=1)

    if sync:
        mgr.sync_to_shells()
    console.print(f"[bold green]✔ Added alias '[cyan]{new_alias.name}[/cyan]' -> '[cyan]{new_alias.command}[/cyan]'[/bold green]")


@alias_app.command(name="remove")
def alias_remove(
    name: str = typer.Argument(..., help="Alias name to remove"),
    sync: bool = typer.Option(True, "--sync/--no-sync", help="Automatically synchronize to shell profiles")
):
    mgr = AliasManager()
    if mgr.remove_alias(name):
        if sync:
            mgr.sync_to_shells()
        console.print(f"[bold green]✔ {t('alias_removed', name=name)}[/bold green]")
    else:
        console.print(f"[yellow]⚠ {t('alias_not_found', name=name)}[/yellow]")


@alias_app.command(name="sync")
def alias_sync():
    mgr = AliasManager()
    results = mgr.sync_to_shells()
    console.print(f"[bold green]✔ {t('aliases_synced')}[/bold green]")
    for shell_name, ok in results.items():
        st = "[green]Synced[/green]" if ok else "[yellow]Failed[/yellow]"
        console.print(f"  • {shell_name}: {st}")


@tools_app.command(name="list")
def tools_list():
    hub = ToolHub()

    table = Table(title="🚀 Modern CLI Tools Ecosystem", header_style="bold #00ffff", expand=True)
    table.add_column(t("col_tool"), style="bold white", width=14)
    table.add_column(t("col_category"), style="dim", width=15)
    table.add_column(t("col_status"), justify="center", width=12)
    table.add_column(t("col_description"), style="white")
    table.add_column(t("col_install"), style="bold #ffcc00")

    for item in hub.get_tool_status():
        if item["installed"]:
            st = f"[bold #00ff99]✔ {t('st_installed')}[/bold #00ff99]"
        else:
            st = f"[bold #ff0055]✗ {t('st_missing')}[/bold #ff0055]"
        table.add_row(item["name"], item["category"], st, item["description"], item["install_command"])

    console.print(table)


@backup_app.command(name="create")
def backup_create(tag: str = typer.Option("manual", "--tag", "-t", help="Tag name for snapshot")):
    try:
        target = BackupManager().create_snapshot(tag=tag)
    except Exception as e:
        console.print(f"[bold red]Error creating backup: {e}[/bold red]")
        raise typer.Exit(code=1)
    console.print(f"[bold green]✔ {t('backup_created')}[/bold green] [cyan]{target}[/cyan]")


@backup_app.command(name="list")
def backup_list():
    snapshots = BackupManager().list_snapshots()
    if not snapshots:
        console.print("[yellow]No backups found.[/yellow]")
        return

    table = Table(title="💾 Backup Snapshots", header_style="bold #00ffff", expand=True)
    table.add_column(t("col_snapshot"), style="bold #00ff99")
    table.add_column(t("col_timestamp"), style="white")
    table.add_column(t("col_tag"), style="bold #ffcc00")
    table.add_column(t("col_files"), justify="right")

    for s in snapshots:
        table.add_row(s.get("dir_name", ""), s.get("timestamp", ""), s.get("tag", ""), str(len(s.get("files", []))))

    console.print(table)


@backup_app.command(name="restore")
def backup_restore(
    snapshot_name: str = typer.Argument(..., help="Name of snapshot to restore"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    if not yes and _IS_TTY and not typer.confirm(t("restore_confirm"), default=False):
        console.print(f"[yellow]{t('aborted')}[/yellow]")
        raise typer.Exit()

    # NOT: typer.Exit aslinda RuntimeError turevi. `except Exception` kullanirsak
    # asagidaki Exit'i de yakalar ve kullaniciya bos bir "Error:" satiri gider.
    # o yuzden basarisizligi donus degeriyle ele alip try'i dar tutuyoruz
    try:
        success = BackupManager().restore_snapshot(snapshot_name)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)

    if not success:
        console.print(f"[bold red]{t('snapshot_failed', snapshot=snapshot_name)}[/bold red]")
        raise typer.Exit(code=1)
    console.print(f"[bold green]✔ {t('snapshot_restored', snapshot=snapshot_name)}[/bold green]")


# pyproject'teki console_scripts buraya bagli (termcraft ve tc)
def main():
    app()


if __name__ == "__main__":
    main()
