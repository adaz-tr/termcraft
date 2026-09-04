"""README icin TUI ekran goruntulerini uretir.

Textual'in kendi SVG export'unu kullaniyoruz - PNG yerine SVG cunku vektorel,
her ekranda net gorunuyor ve GitHub markdown'da sorunsuz render ediliyor.

Kullanim:
    python scripts/make_screenshots.py

HOME'u gecici bir klasore cevirip calisiyor, kendi config'ine dokunmuyor.
"""

import asyncio
import pathlib
import shutil
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "docs" / "images"
TERMINAL_SIZE = (128, 36)

# (dosya adi, sekme id'si, tema anahtari, dil)
# ayni ekrani iki farkli temada cekiyoruz ki studyonun kendi renginin de
# temayla degistigi README'de gorulsun
SHOTS = [
    ("studio-themes-rival.svg", "tab-themes", "rival-gradient", "en"),
    ("studio-themes-latte.svg", "tab-themes", "catppuccin-latte", "en"),
    ("studio-doctor.svg", "tab-doctor", "tokyo-night", "en"),
    ("studio-tools.svg", "tab-tools", "dracula", "en"),
    ("studio-themes-tr.svg", "tab-themes", "cyber-gradient", "tr"),
]


async def capture(name: str, tab_id: str, theme_key: str, lang: str, out_dir: pathlib.Path) -> None:
    from textual.widgets import Select, TabbedContent

    from termcraft.i18n import set_language
    from termcraft.tui.app import TermCraftStudioApp

    # compose() etiketleri t() ile okuyor, dil app olusturulmadan once ayarlanmali
    set_language(lang)

    app = TermCraftStudioApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        # temayi sec -> hem onizleme hem studyonun kendi rengi degisiyor
        app.query_one("#theme-selector", Select).value = theme_key
        await pilot.pause()

        app.query_one(TabbedContent).active = tab_id
        await pilot.pause()

        # doctor/tools sekmeleri arka plan worker'i ile doluyor, bitmesini bekle
        await app.workers.wait_for_complete()
        for _ in range(3):
            await pilot.pause()

        app.save_screenshot(str(out_dir / name))
    print(f"  {name}")


async def main() -> None:
    # kendi ~/.termcraft ve kabuk profillerimize dokunmadan calis
    tmp_home = pathlib.Path(tempfile.mkdtemp(prefix="termcraft-shots-"))
    import os

    for var in ("HOME", "USERPROFILE"):
        os.environ[var] = str(tmp_home)
    os.environ["APPDATA"] = str(tmp_home / "AppData" / "Roaming")
    os.environ["LOCALAPPDATA"] = str(tmp_home / "AppData" / "Local")
    pathlib.Path.home = classmethod(lambda cls: tmp_home)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"ekran goruntuleri -> {OUT_DIR.relative_to(REPO_ROOT)}")
    try:
        for name, tab_id, theme_key, lang in SHOTS:
            await capture(name, tab_id, theme_key, lang, OUT_DIR)
    finally:
        shutil.rmtree(tmp_home, ignore_errors=True)
    print("bitti")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    asyncio.run(main())
