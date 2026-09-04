import sys
import time
import platform
import psutil
import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.live import Live

from termcraft.utils.gradient import render_gradient_text, render_gradient_divider, is_truecolor_supported, GRADIENT_PALETTES
from termcraft.i18n import t

from pathlib import Path

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

console = Console(color_system="truecolor", force_terminal=True, legacy_windows=False)

# figlet 'standard' fontundan. raw string cunku ters slash'lar bozulmasin
LOGO = r"""
  _____                     ____            __ _   
 |_   _|__ _ __ _ __ ___   / ___|_ __ __ _ / _| |_ 
   | |/ _ \ '__| '_ ` _ \ | |   | '__/ _` | |_| __|
   | |  __/ |  | | | | | || |___| | | (_| |  _| |_ 
   |_|\___|_|  |_| |_| |_| \____|_|  \__,_|_|  \__|
"""

def get_system_stats() -> dict:
    # NOT: psutil.cpu_percent() interval'siz cagrildiginda ilk sefer hep 0.0 donuyor.
    # gercek deger istersek interval=0.1 vermek ya da onceden bir kez isitmak lazim
    uname = platform.uname()
    mem = psutil.virtual_memory()
    # windows'ta surucu kokunu (C: kismi) al, linux/mac'te dogrudan kok dizin
    root_path = Path.home().anchor if sys.platform == "win32" else "/"
    try:
        disk = psutil.disk_usage(root_path)
    except Exception:
        disk = psutil.disk_usage("/")
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    
    return {
        "os": f"{uname.system} {uname.release}",
        # interval vermezsek ilk cagri hep 0.0 donuyor. 0.1sn banner icin kabul edilebilir
        "cpu": f"{psutil.cpu_percent(interval=0.1)}% ({psutil.cpu_count(logical=True)} cores)",
        "memory": f"{mem.used // (1024*1024)}MB / {mem.total // (1024*1024)}MB ({mem.percent}%)",
        "disk": f"{disk.used // (1024*1024*1024)}GB / {disk.total // (1024*1024*1024)}GB ({disk.percent}%)",
        "uptime": f"{hours}h {minutes}m",
        "python": platform.python_version()
    }

def build_banner_renderable(palette_key: str = "cyber-gradient") -> Panel:
    # solda logo sagda sistem bilgisi olan iki kolonlu grid.
    # Live ile animasyon yaparken her karede bu bastan uretiliyor
    stats = get_system_stats()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("LogoCol", ratio=3, justify="center")
    table.add_column("StatsCol", ratio=2, justify="left")

    logo_gradient = render_gradient_text(LOGO.strip("\n"), palette_key=palette_key, mode="2d")

    stats_table = Table(show_header=False, box=None, padding=(0, 1))
    stats_table.add_column("Label", style="bold #00d4ff", width=10)
    stats_table.add_column("Val", style="bold #ffffff")

    stats_table.add_row("OS:", stats["os"])
    stats_table.add_row("CPU:", stats["cpu"])
    stats_table.add_row("RAM:", stats["memory"])
    stats_table.add_row("DISK:", stats["disk"])
    stats_table.add_row("UPTIME:", stats["uptime"])
    stats_table.add_row("PYTHON:", stats["python"])

    table.add_row(logo_gradient, stats_table)

    divider = render_gradient_divider(t("app_subtitle"), width=72, palette_key=palette_key)

    main_layout = Table.grid(expand=True)
    main_layout.add_row(table)
    main_layout.add_row(Text(""))
    main_layout.add_row(divider)

    panel = Panel(
        main_layout,
        title=f"[bold #00ffff]⚡ {t('app_title')} ⚡[/bold #00ffff]",
        border_style="#0099ff",
        padding=(1, 2)
    )
    return panel

def print_banner(palette_key: str = "cyber-gradient", animated: bool = False, loops: int = 2):
    if not is_truecolor_supported():
        console.print("[yellow]⚠ TrueColor (24-bit RGB) not detected. Windows Terminal, WezTerm or Alacritty recommended for best gradient rendering.[/yellow]")

    if not animated:
        panel = build_banner_renderable(palette_key)
        console.print(panel)
        return

    # animasyon: paletleri sirayla dolasip banner'i yeniden ciziyoruz.
    # 12 fps + 60ms bekleme goze yeterince akici geliyor
    keys = list(GRADIENT_PALETTES.keys())
    with Live(console=console, refresh_per_second=12) as live:
        for _ in range(loops):
            for k in keys:
                live.update(build_banner_renderable(k))
                time.sleep(0.06)
