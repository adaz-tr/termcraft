from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, Static, Button, TabbedContent, TabPane, Select, Input, DataTable, Label
from textual.reactive import reactive
from textual.theme import Theme
from textual import work

from termcraft.presets.themes import BUILTIN_THEMES
from termcraft.presets.prompts import STARSHIP_PRESETS, OH_MY_POSH_PRESETS
from termcraft.core.theme_engine import ThemeEngine
from termcraft.core.prompt_engine import PromptEngine
from termcraft.core.alias_manager import AliasManager
from termcraft.core.doctor import TerminalDoctor
from termcraft.core.profiler import ShellProfiler
from termcraft.core.tool_hub import ToolHub
from termcraft.core.backup_sync import BackupManager
from termcraft.utils.gradient import ensure_contrast, is_dark, mix_hex, readable_on
from termcraft.i18n import t, set_language, get_current_language


class ConfirmScreen(ModalScreen[bool]):
    """Geri yukleme gibi geri donusu olmayan islemler icin basit onay ekrani."""

    CSS = """
    ConfirmScreen {
        align: center middle;
    }
    #confirm-box {
        width: 60;
        height: auto;
        background: $surface;
        border: round $error;
        padding: 1 2;
    }
    """

    def __init__(self, question: str):
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Label(self.question)
            with Horizontal():
                yield Button(t("btn_yes"), id="confirm-yes", variant="error")
                yield Button(t("btn_no"), id="confirm-no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-yes")


# textual tabanli tam ekran studio. CLI ile ayni core siniflarini kullaniyor,
# burada sadece sunum katmani var
class TermCraftStudioApp(App):
    # renkler aktif Textual Theme'inden geliyor (bkz. _build_textual_theme).
    # tema secilince stüdyonun kendi arayuzu de o temaya donuyor - bir tema
    # aracinin kendi penceresinin temayi yok saymasi tuhaf kaciyordu
    CSS = """
    Screen {
        background: $tc-bg;
        color: $tc-fg;
    }

    Header {
        background: $tc-panel;
        color: $tc-header-fg;
    }

    Footer {
        background: $tc-panel;
        color: $tc-footer-fg;
    }

    TabbedContent {
        height: 100%;
    }

    TabPane {
        padding: 1 2;
    }

    .card {
        background: $tc-panel;
        border: round $tc-blue;
        padding: 1;
        margin-bottom: 1;
    }

    .preview-box {
        height: 17;
        border: solid $tc-cyan;
        background: $tc-inset;
        padding: 1;
        margin-top: 1;
    }

    .btn-apply {
        background: $tc-cyan;
        color: $tc-on-cyan;
        text-style: bold;
        margin-top: 1;
        margin-right: 1;
    }

    .btn-action {
        background: $tc-green;
        color: $tc-on-green;
        text-style: bold;
        margin-top: 1;
        margin-right: 1;
    }

    .btn-danger {
        background: $tc-red;
        color: $tc-on-red;
        text-style: bold;
        margin-top: 1;
        margin-right: 1;
    }

    .input-field {
        margin-top: 1;
        margin-bottom: 1;
        background: $tc-inset;
        border: solid $tc-blue;
        color: $tc-fg;
    }
    """

    TITLE = "⚡ TermCraft Studio"
    SUB_TITLE = "Universal Terminal & Shell Customization Suite"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh_all", "Refresh"),
    ]

    selected_theme = reactive("cyber-gradient")
    selected_prompt = reactive("modern-cyber")

    # __init__ icinde _set_ui_theme cagrilana kadar gecerli bir palet dursun
    _ui_theme = BUILTIN_THEMES["cyber-gradient"]

    def _build_textual_theme(self, theme: dict, name: str) -> Theme:
        """TermCraft palet sozlugunu Textual'in kendi Theme nesnesine cevirir.

        Sadece kendi $tc-* degiskenlerimizi tanimlamak yetmiyordu: Tabs, Footer
        ve Select gibi hazir widget'lar Textual'in kendi tasarim token'larini
        ($surface, $panel, $text-muted ...) kullaniyor. Acik bir temada
        (catppuccin-latte) sekme etiketleri ve footer okunmaz hale geliyordu.
        Theme nesnesini kaydedince Textual butun bu token'lari kendisi turetiyor.
        """
        bg = theme.get("background", "#08090f")
        fg = theme.get("foreground", "#c0caf5")
        dark = is_dark(bg)

        # koyu temada zemini biraz aydinlat, acik temada biraz koyulastir.
        # dogrudan fg'ye karistirirsak panel temanin rengine bulaniyor
        lift = "#ffffff" if dark else "#000000"
        deep = "#000000" if dark else "#ffffff"

        cyan = theme.get("cyan", "#00ffff")
        green = theme.get("green", "#00ff99")
        red = theme.get("red", "#ff0055")
        surface = mix_hex(bg, lift, 0.08)
        inset = mix_hex(bg, deep, 0.30)

        return Theme(
            name=name,
            dark=dark,
            background=bg,
            foreground=fg,
            surface=surface,
            panel=mix_hex(bg, lift, 0.14),
            primary=theme.get("blue", "#0099ff"),
            secondary=cyan,
            accent=theme.get("magenta", "#a800ff"),
            success=green,
            warning=theme.get("yellow", "#ffcc00"),
            error=red,
            # kendi siniflarimiz ($tc-*) bunlari kullaniyor
            variables={
                "tc-bg": bg,
                "tc-fg": fg,
                "tc-panel": surface,
                "tc-inset": inset,
                "tc-dim": mix_hex(fg, bg, 0.40),
                # tema paletleri bizim panel zeminimiz dusunulerek yapilmiyor.
                # acik temalarda aksan rengi panel uzerinde okunmuyordu, o yuzden
                # tonu koruyup parlakligi kontrast esigine kadar kaydiriyoruz
                "tc-header-fg": ensure_contrast(cyan, surface, 4.5),
                "tc-footer-fg": ensure_contrast(mix_hex(fg, bg, 0.40), surface, 3.5),
                "tc-cyan": cyan,
                "tc-green": green,
                "tc-red": red,
                "tc-blue": theme.get("blue", "#0099ff"),
                # buton yazisi zeminine gore siyah ya da beyaz olmali, yoksa
                # acik renkli aksanlarda okunmuyor
                "tc-on-cyan": readable_on(cyan),
                "tc-on-green": readable_on(green),
                "tc-on-red": readable_on(red),
            },
        )

    def _set_ui_theme(self, theme_key: str) -> None:
        """Stüdyonun kendi renklerini secili temaya cevirir."""
        palette = self.theme_engine.get_theme(theme_key)
        if not palette:
            return
        self._ui_theme = palette
        textual_name = f"termcraft-{theme_key}"
        self.register_theme(self._build_textual_theme(palette, textual_name))
        self.theme = textual_name

    def __init__(self):
        super().__init__()
        # motorlari burada kuruyoruz. on_mount'ta olusturmak riskliydi: Select
        # widget'i mount sirasinda Changed mesaji yollarsa handler henuz var
        # olmayan self.theme_engine'e uzaniyordu
        self.theme_engine = ThemeEngine()
        self.prompt_engine = PromptEngine()
        self.alias_manager = AliasManager()
        self.doctor = TerminalDoctor()
        self.profiler = ShellProfiler()
        self.tool_hub = ToolHub()
        self.backup_mgr = BackupManager()
        # temayi burada kaydetmek zorundayiz: CSS'teki $tc-* degiskenleri aktif
        # Theme'den geliyor ve stylesheet mount'tan once cozuluyor
        self._set_ui_theme(self.selected_theme)

    def compose(self) -> ComposeResult:
        # sekmeler: tema / prompt / alias / doctor / benchmark / araclar / yedek / dil
        yield Header(show_clock=True)
        with TabbedContent(initial="tab-themes"):
            with TabPane(f"🎨 {t('tab_themes')}", id="tab-themes"):
                with Horizontal():
                    with Vertical(classes="card", id="theme-controls"):
                        yield Label(t("select_theme"), classes="label")
                        theme_options = [(v["name"], k) for k, v in BUILTIN_THEMES.items()]
                        yield Select(theme_options, value="cyber-gradient", id="theme-selector", allow_blank=False)
                        yield Button(t("apply_theme_global"), id="btn-apply-theme", classes="btn-apply")
                        yield Label("", id="theme-status-lbl")
                    with Vertical(classes="card"):
                        yield Label(t("theme_preview"), classes="label")
                        yield Static(id="theme-preview", classes="preview-box")

            with TabPane(f"⚡ {t('tab_prompts')}", id="tab-prompts"):
                with Horizontal():
                    with Vertical(classes="card", id="prompt-controls"):
                        yield Label(t("select_prompt"), classes="label")
                        prompt_options = (
                            [(f"Starship: {v['name']}", k) for k, v in STARSHIP_PRESETS.items()]
                            + [(f"Oh-My-Posh: {v['name']}", k) for k, v in OH_MY_POSH_PRESETS.items()]
                        )
                        yield Select(prompt_options, value="modern-cyber", id="prompt-selector", allow_blank=False)
                        yield Button(t("apply_prompt"), id="btn-apply-prompt", classes="btn-apply")
                        yield Label("", id="prompt-status-lbl")
                    with Vertical(classes="card"):
                        yield Label(t("prompt_preview"), classes="label")
                        yield Static(id="prompt-preview", classes="preview-box")

            with TabPane(f"🛠️ {t('tab_aliases')}", id="tab-aliases"):
                with VerticalScroll():
                    with Horizontal(classes="card"):
                        yield Button(t("load_git_bundle"), id="btn-bundle-git", classes="btn-action")
                        yield Button(t("load_docker_bundle"), id="btn-bundle-docker", classes="btn-action")
                        yield Button(t("load_modern_bundle"), id="btn-bundle-modern", classes="btn-action")
                        yield Button(t("bundle_dev"), id="btn-bundle-dev", classes="btn-action")
                        yield Button(t("sync_to_shells"), id="btn-sync-aliases", classes="btn-apply")
                    with Horizontal(classes="card"):
                        yield Input(placeholder=t("ph_alias_name"), id="input-alias-name", classes="input-field")
                        yield Input(placeholder=t("ph_alias_cmd"), id="input-alias-cmd", classes="input-field")
                        yield Button(f"➕ {t('btn_add')}", id="btn-add-alias", classes="btn-action")
                        yield Button(f"🗑️ {t('btn_remove')}", id="btn-remove-alias", classes="btn-danger")
                    yield DataTable(id="aliases-table")

            with TabPane(f"🩺 {t('tab_doctor')}", id="tab-doctor"):
                with VerticalScroll():
                    with Horizontal(classes="card"):
                        yield Button(t("run_doctor_now"), id="btn-run-doctor", classes="btn-action")
                        yield Button(f"🔧 {t('btn_autofix')}", id="btn-autofix-doctor", classes="btn-apply")
                    yield DataTable(id="doctor-table")

            with TabPane(f"⏱️ {t('tab_benchmark')}", id="tab-benchmark"):
                with VerticalScroll():
                    yield Button(t("benchmark_startup"), id="btn-run-benchmark", classes="btn-action")
                    yield DataTable(id="benchmark-table")

            with TabPane(f"🚀 {t('tab_tools')}", id="tab-tools"):
                with VerticalScroll():
                    yield Button(t("scan_installed_tools"), id="btn-scan-tools", classes="btn-action")
                    yield DataTable(id="tools-table")

            with TabPane(f"💾 {t('tab_backups')}", id="tab-backups"):
                with VerticalScroll():
                    with Horizontal(classes="card"):
                        yield Button(f"📸 {t('btn_snapshot')}", id="btn-create-snapshot", classes="btn-action")
                        yield Button(f"🔄 {t('btn_restore')}", id="btn-restore-snapshot", classes="btn-apply")
                    yield DataTable(id="backups-table")

            with TabPane(f"🌐 {t('tab_lang')}", id="tab-lang"):
                with Vertical(classes="card"):
                    yield Label("Dil / Language:")
                    lang_opts = [("Türkçe", "tr"), ("English", "en")]
                    yield Select(lang_opts, value=get_current_language(), id="lang-selector", allow_blank=False)
                    yield Label("", id="lang-status-lbl")

        yield Footer()

    def on_mount(self) -> None:
        self.update_theme_preview(self.selected_theme)
        self.update_prompt_preview(self.selected_prompt)
        self.populate_aliases_table()
        self.populate_backups_table()
        # doctor ve arac taramasi disk/PATH gezdigi icin acilisi kilitliyordu,
        # ikisini de arka plan thread'ine aliyoruz
        self.run_doctor_checks()
        self.populate_tools_table()

    def action_refresh_all(self) -> None:
        self.populate_aliases_table()
        self.populate_backups_table()
        self.run_doctor_checks()
        self.populate_tools_table()

    def watch_selected_theme(self, new_val: str) -> None:
        if self.is_running:
            self.update_theme_preview(new_val)

    def watch_selected_prompt(self, new_val: str) -> None:
        if self.is_running:
            self.update_prompt_preview(new_val)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "theme-selector" and event.value is not None:
            self.selected_theme = str(event.value)
            # stüdyonun kendi renkleri de secilen temaya donsun -> temayi
            # uygulamadan once tam olarak neye benzeyecegini goruyorsun
            self._set_ui_theme(self.selected_theme)
        elif event.select.id == "prompt-selector" and event.value is not None:
            self.selected_prompt = str(event.value)
        elif event.select.id == "lang-selector" and event.value is not None:
            new_lang = str(event.value)
            if new_lang == get_current_language():
                return
            set_language(new_lang)
            self.query_one("#lang-status-lbl", Label).update(f"[bold green]{t('lang_changed')}[/bold green]")
            # dil degisince tablolarin basliklari da cevriliyor, hepsini tazele
            self.alias_manager = AliasManager()
            self.action_refresh_all()

    def update_theme_preview(self, theme_key: str) -> None:
        self.query_one("#theme-preview", Static).update(self.theme_engine.render_theme_preview(theme_key))

    def update_prompt_preview(self, prompt_key: str) -> None:
        self.query_one("#prompt-preview", Static).update(self.prompt_engine.render_prompt_preview(prompt_key))

    def populate_aliases_table(self) -> None:
        table = self.query_one("#aliases-table", DataTable)
        table.clear(columns=True)
        table.add_columns(t("col_alias"), t("col_command"), t("col_description"), t("col_shells"))
        for a in self.alias_manager.aliases:
            table.add_row(f"[bold #00ffff]{a.name}[/bold #00ffff]", a.command, a.description, ", ".join(a.shells))

    def populate_backups_table(self) -> None:
        table = self.query_one("#backups-table", DataTable)
        table.clear(columns=True)
        table.add_columns(t("col_snapshot"), t("col_timestamp"), t("col_tag"), t("col_files"))
        for s in self.backup_mgr.list_snapshots():
            table.add_row(
                f"[bold #00ff99]{s.get('dir_name', '')}[/bold #00ff99]",
                s.get("timestamp", ""), s.get("tag", ""), str(len(s.get("files", [])))
            )

    @work(thread=True, exclusive=True, group="doctor")
    def run_doctor_checks(self) -> None:
        # font taramasi + onlarca shutil.which var, UI thread'inde calisirsa
        # arayuz donuyor. sonucu call_from_thread ile geri veriyoruz
        report = self.doctor.run_diagnostics()
        self.call_from_thread(self._render_doctor_report, report)

    def _render_doctor_report(self, report) -> None:
        table = self.query_one("#doctor-table", DataTable)
        table.clear(columns=True)
        table.add_columns(t("col_status"), t("col_check"), t("col_result"), t("col_recommendation"))
        for check in report.checks:
            st = check["status"]
            if st == "pass":
                st_styled = "[bold green]PASS[/bold green]"
            elif st == "warn":
                st_styled = "[bold yellow]WARN[/bold yellow]"
            else:
                st_styled = "[bold blue]INFO[/bold blue]"
            table.add_row(st_styled, check["title"], check["message"], check["fix_suggestion"])

    @work(thread=True, exclusive=True, group="tools")
    def populate_tools_table(self) -> None:
        statuses = self.tool_hub.get_tool_status()
        self.call_from_thread(self._render_tools, statuses)

    def _render_tools(self, statuses) -> None:
        table = self.query_one("#tools-table", DataTable)
        table.clear(columns=True)
        table.add_columns(t("col_tool"), t("col_category"), t("col_status"), t("col_install"))
        for item in statuses:
            if item["installed"]:
                st = f"[bold green]{t('st_installed')}[/bold green]"
            else:
                st = f"[bold red]{t('st_missing')}[/bold red]"
            table.add_row(f"[bold]{item['name']}[/bold]", item["category"], st, item["install_command"])

    @work(thread=True, exclusive=True, group="benchmark")
    def run_benchmark(self) -> None:
        # 6 kabuk x 3 tur x 15sn timeout -> en kotu senaryoda dakikalar suruyor,
        # kesinlikle UI thread'inde olmamali
        results = self.profiler.run_all_benchmarks(iterations=3)
        self.call_from_thread(self._render_benchmark, results)

    def _render_benchmark(self, results) -> None:
        table = self.query_one("#benchmark-table", DataTable)
        table.clear(columns=True)
        table.add_columns(t("col_shell"), t("col_status"), t("col_avg"), "Min", "Max", t("col_rating"))
        for shell_name, data in results.items():
            if data["samples"]:
                avg = data["avg_ms"]
                if avg < 75:
                    rating = f"[bold green]{t('rate_fast')}[/bold green]"
                elif avg < 200:
                    rating = f"[bold yellow]{t('rate_normal')}[/bold yellow]"
                else:
                    rating = f"[bold red]{t('rate_slow')}[/bold red]"
                table.add_row(
                    shell_name, f"[green]{t('st_available')}[/green]",
                    f"{avg} ms", f"{data['min_ms']} ms", f"{data['max_ms']} ms", rating
                )
            else:
                label = "timeout" if data.get("timed_out") else t("st_not_found")
                table.add_row(shell_name, f"[dim]{label}[/dim]", "-", "-", "-", "-")
        self.notify(t("benchmark_complete"))

    @work(thread=True, exclusive=True, group="apply")
    def apply_theme_worker(self, theme_key: str) -> None:
        # tema uygulamak dosya yaziyor, o da bloklayici
        try:
            res = self.theme_engine.apply_theme(theme_key)
            applied = [k for k, v in res.items() if v]
            msg = f"[bold green]{t('theme_applied')} {', '.join(applied) if applied else t('no_term_found')}[/bold green]"
            ok = True
        except Exception as e:
            msg, ok = f"[bold red]Error: {e}[/bold red]", False
        self.call_from_thread(self._finish_theme_apply, msg, ok)

    def _finish_theme_apply(self, msg: str, ok: bool) -> None:
        self.query_one("#theme-status-lbl", Label).update(msg)
        if ok:
            self.notify(t("theme_apply_ok"))

    @work(thread=True, exclusive=True, group="apply")
    def apply_prompt_worker(self, preset_key: str) -> None:
        try:
            self.prompt_engine.apply_preset(preset_key)
            msg = f"[bold green]{t('prompt_applied', preset=preset_key)}[/bold green]"
            ok = True
        except Exception as e:
            msg, ok = f"[bold red]Error: {e}[/bold red]", False
        self.call_from_thread(self._finish_prompt_apply, msg, ok)

    def _finish_prompt_apply(self, msg: str, ok: bool) -> None:
        self.query_one("#prompt-status-lbl", Label).update(msg)
        if ok:
            self.notify(t("prompt_applied", preset=self.selected_prompt))

    @work(thread=True, exclusive=True, group="apply")
    def autofix_worker(self) -> None:
        fixed = self.doctor.auto_fix()
        self.call_from_thread(self._finish_autofix, len(fixed))

    def _finish_autofix(self, count: int) -> None:
        self.notify(t("autofix_done", count=count))
        self.run_doctor_checks()

    def _load_bundle(self, name: str) -> None:
        try:
            self.alias_manager.load_bundle(name)
        except ValueError as e:
            self.notify(str(e), severity="error")
            return
        self.populate_aliases_table()
        self.notify(t("bundle_loaded", bundle=name))
        # golgeleyen alias yuklendiyse kullaniciyi uyar
        shadowing = self.alias_manager.check_shadowing()
        if shadowing:
            desc = ", ".join([f"{n} -> {c}" for n, c in shadowing])
            self.notify(t("alias_shadowing", aliases=desc), severity="warning")

    # tek bir dispatch noktasi. buton sayisi artarsa id -> handler dict'i daha temiz olur
    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-apply-theme":
            self.query_one("#theme-status-lbl", Label).update(f"[dim]{t('working')}[/dim]")
            self.apply_theme_worker(self.selected_theme)
        elif bid == "btn-apply-prompt":
            self.query_one("#prompt-status-lbl", Label).update(f"[dim]{t('working')}[/dim]")
            self.apply_prompt_worker(self.selected_prompt)
        elif bid == "btn-bundle-git":
            self._load_bundle("git")
        elif bid == "btn-bundle-docker":
            self._load_bundle("docker")
        elif bid == "btn-bundle-modern":
            self._load_bundle("modern-replacements")
        elif bid == "btn-bundle-dev":
            self._load_bundle("dev")
        elif bid == "btn-add-alias":
            name_input = self.query_one("#input-alias-name", Input)
            cmd_input = self.query_one("#input-alias-cmd", Input)
            if name_input.value.strip() and cmd_input.value.strip():
                try:
                    self.alias_manager.add_alias(name_input.value.strip(), cmd_input.value.strip())
                except Exception as e:
                    self.notify(t("invalid_alias_name", reason=e), severity="error")
                    return
                self.populate_aliases_table()
                self.alias_manager.sync_to_shells()
                name_input.value = ""
                cmd_input.value = ""
                self.notify(t("alias_added"))
        elif bid == "btn-remove-alias":
            name_input = self.query_one("#input-alias-name", Input)
            target = name_input.value.strip()
            if target:
                if self.alias_manager.remove_alias(target):
                    self.populate_aliases_table()
                    self.alias_manager.sync_to_shells()
                    self.notify(t("alias_removed", name=target))
                    name_input.value = ""
                else:
                    self.notify(t("alias_not_found", name=target), severity="warning")
        elif bid == "btn-sync-aliases":
            self.alias_manager.sync_to_shells()
            self.notify(t("aliases_synced"))
        elif bid == "btn-run-doctor":
            self.run_doctor_checks()
            self.notify(t("diag_complete"))
        elif bid == "btn-autofix-doctor":
            self.autofix_worker()
        elif bid == "btn-scan-tools":
            self.populate_tools_table()
            self.notify(t("tools_scan_complete"))
        elif bid == "btn-create-snapshot":
            target = self.backup_mgr.create_snapshot(tag="studio")
            self.populate_backups_table()
            self.notify(t("snapshot_created", name=target.name))
        elif bid == "btn-restore-snapshot":
            self._ask_restore()
        elif bid == "btn-run-benchmark":
            self.notify(t("working"))
            self.run_benchmark()

    def _ask_restore(self) -> None:
        # geri yukleme aktif kabuk profillerini eziyor, onaysiz calistirmiyoruz
        snapshots = self.backup_mgr.list_snapshots()
        if not snapshots:
            self.notify(t("no_snapshots"), severity="warning")
            return
        table = self.query_one("#backups-table", DataTable)
        idx = table.cursor_row if table.cursor_row is not None and 0 <= table.cursor_row < len(snapshots) else 0
        target_snapshot = snapshots[idx]["dir_name"]

        def _on_confirm(confirmed: bool) -> None:
            if not confirmed:
                self.notify(t("aborted"))
                return
            if self.backup_mgr.restore_snapshot(target_snapshot):
                self.notify(t("restore_ok", name=target_snapshot))
                self.populate_backups_table()
            else:
                self.notify(t("restore_fail"), severity="error")

        self.push_screen(ConfirmScreen(f"{t('restore_confirm')}\n\n{target_snapshot}"), _on_confirm)


def run_tui():
    TermCraftStudioApp().run()
