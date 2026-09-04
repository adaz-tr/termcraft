import yaml
from typing import Dict, Optional
from termcraft.utils.paths import get_config_file_path

# tum ceviriler burada gomulu duruyor. ayri .po/.json dosyasi yok cunku
# metin sayisi az ve tek dosyada tutmak diff'te daha rahat okunuyor.
# yeni dil eklerken en'deki tum anahtarlari kopyalamak lazim, eksik kalan
# anahtar t() icinde sessizce ingilizceye dusuyor
STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "TermCraft Master CLI Studio",
        "app_subtitle": "Universal Shell & Terminal Customization Engine",
        "studio_title": "TermCraft Studio",
        "studio_subtitle": "Universal Terminal & Shell Customization Suite",
        "tab_themes": "Themes",
        "tab_prompts": "Prompts",
        "tab_aliases": "Aliases",
        "tab_doctor": "Doctor",
        "tab_benchmark": "Benchmark",
        "tab_tools": "Tools",
        "tab_lang": "Language",
        "select_theme": "Select Color Theme:",
        "apply_theme_global": "Apply Theme Globally",
        "theme_preview": "Theme Preview:",
        "select_prompt": "Select Prompt Preset:",
        "apply_prompt": "Apply Prompt Preset",
        "prompt_preview": "Prompt Live Preview:",
        "load_git_bundle": "Load Git Bundle",
        "load_docker_bundle": "Load Docker Bundle",
        "load_modern_bundle": "Load Modern Tools Bundle",
        "sync_to_shells": "Sync to Shells",
        "run_doctor_now": "Run Diagnostics Now",
        "benchmark_startup": "Benchmark Startup Latency",
        "scan_installed_tools": "Scan Installed Tools",
        "theme_applied": "Applied to:",
        "no_term_found": "No terminal config found",
        "prompt_applied": "Prompt preset '{preset}' applied successfully!",
        "reload_hint": "Tip: Open a new terminal tab or run '. $PROFILE' (source ~/.bashrc) to apply in this window immediately.",
        "aliases_synced": "Aliases synchronized across all available shell profiles!",
        "diag_complete": "Diagnostics complete.",
        "tools_scan_complete": "CLI tools scan complete.",
        "benchmark_complete": "Startup benchmark completed!",
        "shell_detection": "Shell Detection",
        "found_shells": "Found active shell(s): {shells}",
        "no_shells_found": "No configured shell profile found.",
        "init_shell_hint": "Initialize a shell profile using `termcraft init`",
        "terminals_detected": "Detected terminal(s): {terms}",
        "no_terminals_found": "No supported terminal emulator config detected.",
        "nerd_font_found": "Found Nerd Font(s): {fonts}",
        "nerd_font_missing": "No Nerd Font detected. Glyphs & icons may render as boxes.",
        "nerd_font_hint": "Download and install 'JetBrainsMono Nerd Font' or 'MesloLGS NF'",
        "path_ok": "PATH contains {count} valid entries with no dead links.",
        "path_issues": "PATH has issues: {issues}",
        "path_hint": "Clean up dead PATH entries in system environment variables.",
        "tools_installed": "Installed tools: {tools}",
        "tools_missing": "Recommended tools to install: {tools}",
        "tools_hint": "Run `termcraft tools` to view install commands.",
        "encoding_active": "Active encoding is {encoding}",
        "encoding_warn": "Active encoding is {encoding}, UTF-8 recommended for unicode icons.",
        "truecolor_support": "TrueColor (24-bit RGB) Support",
        "truecolor_ok": "Terminal supports 24-bit TrueColor RGB gradients.",
        "truecolor_warn": "TrueColor not detected. Windows Terminal, WezTerm or Alacritty recommended for full gradient rendering.",
        "truecolor_hint": "Open in Windows Terminal or a modern 24-bit terminal emulator.",
        "lang_changed": "Language switched to English.",
        "invalid_lang": "Invalid language code '{lang}'. Supported: {supported}",
        "init_done": "Initialization complete! Run `termcraft studio` to start customizing.",
        "backup_created": "Created snapshot backup at:",
        "snapshot_restored": "Successfully restored snapshot '{snapshot}'!",
        "snapshot_failed": "Failed to restore snapshot '{snapshot}'. Check snapshot name.",
        "alias_ok": "No conflicting or shadowing aliases found.",
        "alias_shadowing": "These aliases shadow core shell commands: {aliases}",
        "alias_shadowing_hint": "Remove them with `termcraft alias remove <name>` if the shell misbehaves.",
        "alias_missing_tool": "Aliases skipped because their tool is not installed: {aliases}",
        "config_recovered": "Config file was unreadable, a copy was kept at: {path}",
        "uninstall_done": "TermCraft block removed from all shell profiles.",
        "restore_confirm": "This will overwrite your current shell & terminal configs. Continue?",
        "aborted": "Aborted.",
        "bundle_unknown": "Unknown bundle '{bundle}'. Available: {available}",
        "invalid_alias_name": "Invalid alias name: {reason}",
        "execpolicy_prompt": "Also set PowerShell ExecutionPolicy to RemoteSigned (CurrentUser)?",
        "tab_backups": "Backups",
        "btn_add": "Add",
        "btn_remove": "Remove",
        "btn_snapshot": "Create Snapshot",
        "btn_restore": "Restore Selected",
        "btn_autofix": "Auto-Fix",
        "bundle_dev": "Load Dev Bundle",
        "ph_alias_name": "Alias name (e.g. gco)",
        "ph_alias_cmd": "Command (e.g. git checkout)",
        "alias_added": "Alias added and synchronized!",
        "alias_removed": "Alias '{name}' removed.",
        "alias_not_found": "Alias '{name}' not found.",
        "bundle_loaded": "Bundle '{bundle}' loaded.",
        "theme_apply_ok": "Theme applied successfully!",
        "snapshot_created": "Snapshot created: {name}",
        "restore_ok": "Snapshot ({name}) restored!",
        "restore_fail": "Restore failed.",
        "no_snapshots": "No snapshots to restore.",
        "autofix_done": "Auto-fix finished ({count} actions).",
        "working": "Working...",
        "col_alias": "Alias",
        "col_command": "Command",
        "col_description": "Description",
        "col_shells": "Shells",
        "col_status": "Status",
        "col_check": "Check",
        "col_result": "Result",
        "col_recommendation": "Recommendation / Fix",
        "col_tool": "Tool",
        "col_category": "Category",
        "col_install": "Install Command",
        "col_snapshot": "Snapshot Name",
        "col_timestamp": "Timestamp",
        "col_tag": "Tag",
        "col_files": "Files Backed Up",
        "col_shell": "Shell",
        "col_avg": "Avg Startup",
        "col_rating": "Rating",
        "st_installed": "Installed",
        "st_missing": "Missing",
        "st_available": "Available",
        "st_not_found": "Not Found",
        "rate_fast": "Blazing Fast",
        "rate_normal": "Normal",
        "rate_slow": "Slow",
        "btn_yes": "Yes",
        "btn_no": "Cancel"
    },
    "tr": {
        "app_title": "TermCraft Master CLI Studio",
        "app_subtitle": "Evrensel Kabuk ve Terminal Özelleştirme Motoru",
        "studio_title": "TermCraft Studio",
        "studio_subtitle": "Evrensel Terminal ve Kabuk Özelleştirme Merkezi",
        "tab_themes": "Temalar",
        "tab_prompts": "Promptlar",
        "tab_aliases": "Kısayollar",
        "tab_doctor": "Doktor",
        "tab_benchmark": "Hız Testi",
        "tab_tools": "Araçlar",
        "tab_lang": "Dil",
        "select_theme": "Renk Teması Seçin:",
        "apply_theme_global": "Temayı Genel Olarak Uygula",
        "theme_preview": "Tema Önizlemesi:",
        "select_prompt": "Prompt Şablonu Seçin:",
        "apply_prompt": "Prompt Şablonunu Uygula",
        "prompt_preview": "Prompt Canlı Önizlemesi:",
        "load_git_bundle": "Git Paketini Yükle",
        "load_docker_bundle": "Docker Paketini Yükle",
        "load_modern_bundle": "Modern Araçlar Paketini Yükle",
        "sync_to_shells": "Kabuklara Senkronize Et",
        "run_doctor_now": "Teşhisleri Şimdi Çalıştır",
        "benchmark_startup": "Açılış Hızını Ölç (Benchmark)",
        "scan_installed_tools": "Yüklü Araçları Tara",
        "theme_applied": "Uygulandı:",
        "no_term_found": "Uyumlu terminal yapılandırması bulunamadı",
        "prompt_applied": "'{preset}' prompt şablonu başarıyla uygulandı!",
        "reload_hint": "İpucu: Değişikliklerin bu pencerede hemen geçerli olması için '. $PROFILE' çalıştırın veya yeni bir sekme açın.",
        "aliases_synced": "Kısayollar (alias) tüm aktif kabuk profillerine senkronize edildi!",
        "diag_complete": "Teşhis analizi tamamlandı.",
        "tools_scan_complete": "CLI araçları taraması tamamlandı.",
        "benchmark_complete": "Açılış hızı benchmark testi tamamlandı!",
        "shell_detection": "Kabuk Algılama",
        "found_shells": "Aktif kabuklar bulundu: {shells}",
        "no_shells_found": "Yapılandırılmış kabuk profili bulunamadı.",
        "init_shell_hint": "`termcraft init` komutunu çalıştırarak kabuk profilini başlatın",
        "terminals_detected": "Algılanan terminal(ler): {terms}",
        "no_terminals_found": "Desteklenen terminal yapılandırması bulunamadı.",
        "nerd_font_found": "Nerd Font bulundu: {fonts}",
        "nerd_font_missing": "Nerd Font bulunamadı. Prompt ikonları ve simgeler kutucuk olarak görünebilir.",
        "nerd_font_hint": "'JetBrainsMono Nerd Font' veya 'MesloLGS NF' fontunu indirip kurun",
        "path_ok": "PATH değişkeni geçerli {count} dizin içeriyor, kırık link bulunamadı.",
        "path_issues": "PATH sorunları tespit edildi: {issues}",
        "path_hint": "Sistem ortam değişkenlerindeki geçersiz PATH kayıtlarını temizleyin.",
        "tools_installed": "Yüklü modern araçlar: {tools}",
        "tools_missing": "Kurulması önerilen modern araçlar: {tools}",
        "tools_hint": "Kurulum komutlarını görmek için `termcraft tools` komutunu çalıştırın.",
        "encoding_active": "Aktif karakter kodlaması: {encoding}",
        "encoding_warn": "Karakter kodlaması {encoding}. Unicode ikonları için UTF-8 önerilir.",
        "truecolor_support": "TrueColor (24-bit RGB) Desteği",
        "truecolor_ok": "Terminal 24-bit TrueColor RGB degrade (gradient) renkleri destekliyor.",
        "truecolor_warn": "TrueColor algılanamadı. Renk geçişli (gradient) temalar için Windows Terminal, WezTerm veya Alacritty önerilir.",
        "truecolor_hint": "Windows Terminal veya 24-bit RGB destekleyen modern bir terminalde açın.",
        "lang_changed": "Dil Türkçe olarak ayarlandı.",
        "invalid_lang": "Geçersiz dil kodu '{lang}'. Desteklenen diller: {supported}",
        "init_done": "Kurulum tamamlandı! Özelleştirmeye başlamak için `termcraft studio` çalıştırın.",
        "backup_created": "Yedek snapshot oluşturuldu:",
        "snapshot_restored": "'{snapshot}' yedeği başarıyla geri yüklendi!",
        "snapshot_failed": "'{snapshot}' yedeği geri yüklenemedi. Snapshot adını kontrol edin.",
        "alias_ok": "Çakışan veya temel komutları gölgeleyen kısayol bulunamadı.",
        "alias_shadowing": "Bu kısayollar temel kabuk komutlarını gölgeliyor: {aliases}",
        "alias_shadowing_hint": "Kabukta sorun yaşarsanız `termcraft alias remove <ad>` ile kaldırın.",
        "alias_missing_tool": "Aracı kurulu olmadığı için atlanan kısayollar: {aliases}",
        "config_recovered": "Yapılandırma dosyası okunamadı, bir kopyası şuraya alındı: {path}",
        "uninstall_done": "TermCraft bloğu tüm kabuk profillerinden kaldırıldı.",
        "restore_confirm": "Mevcut kabuk ve terminal ayarlarınızın üzerine yazılacak. Devam edilsin mi?",
        "aborted": "İşlem iptal edildi.",
        "bundle_unknown": "Bilinmeyen paket '{bundle}'. Kullanılabilir: {available}",
        "invalid_alias_name": "Geçersiz kısayol adı: {reason}",
        "execpolicy_prompt": "PowerShell ExecutionPolicy da RemoteSigned (CurrentUser) yapılsın mı?",
        "tab_backups": "Yedekler",
        "btn_add": "Ekle",
        "btn_remove": "Sil",
        "btn_snapshot": "Anlık Yedek Al",
        "btn_restore": "Seçiliyi Geri Yükle",
        "btn_autofix": "Otomatik Onar",
        "bundle_dev": "Geliştirici Paketini Yükle",
        "ph_alias_name": "Kısayol adı (örn: gco)",
        "ph_alias_cmd": "Komut (örn: git checkout)",
        "alias_added": "Kısayol eklendi ve senkronize edildi!",
        "alias_removed": "'{name}' kısayolu silindi.",
        "alias_not_found": "'{name}' kısayolu bulunamadı.",
        "bundle_loaded": "'{bundle}' paketi yüklendi.",
        "theme_apply_ok": "Tema başarıyla uygulandı!",
        "snapshot_created": "Yedek oluşturuldu: {name}",
        "restore_ok": "Snapshot ({name}) geri yüklendi!",
        "restore_fail": "Geri yükleme başarısız oldu.",
        "no_snapshots": "Geri yüklenecek snapshot bulunamadı.",
        "autofix_done": "Otomatik onarım tamamlandı ({count} işlem).",
        "working": "Çalışıyor...",
        "col_alias": "Kısayol",
        "col_command": "Komut",
        "col_description": "Açıklama",
        "col_shells": "Kabuklar",
        "col_status": "Durum",
        "col_check": "Kontrol",
        "col_result": "Sonuç",
        "col_recommendation": "Öneri / Düzeltme",
        "col_tool": "Araç",
        "col_category": "Kategori",
        "col_install": "Kurulum Komutu",
        "col_snapshot": "Snapshot Adı",
        "col_timestamp": "Tarih",
        "col_tag": "Etiket",
        "col_files": "Dosya Sayısı",
        "col_shell": "Kabuk",
        "col_avg": "Ort. Açılış",
        "col_rating": "Değerlendirme",
        "st_installed": "Yüklü",
        "st_missing": "Eksik",
        "st_available": "Mevcut",
        "st_not_found": "Bulunamadı",
        "rate_fast": "Çok Hızlı",
        "rate_normal": "Normal",
        "rate_slow": "Yavaş",
        "btn_yes": "Evet",
        "btn_no": "Vazgeç"
    }
}

# surec ici cache. t() cok siki cagriliyor (her tablo basligi icin), her seferinde
# config.yaml okumak bosuna disk trafigi. dosyanin mtime'ina bakip degismediyse
# cache'i kullaniyoruz
_current_lang = "tr"
_cache_key: Optional[tuple] = None

def get_current_language() -> str:
    global _current_lang, _cache_key
    config_file = get_config_file_path()
    try:
        stat = config_file.stat()
        key = (str(config_file), stat.st_mtime_ns, stat.st_size)
    except OSError:
        return _current_lang

    if key == _cache_key:
        return _current_lang

    try:
        data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "lang" in data:
            val = str(data["lang"]).lower().strip()
            if val in STRINGS:
                _current_lang = val
        _cache_key = key
    except Exception:
        pass
    return _current_lang

def set_language(lang: str) -> None:
    global _current_lang, _cache_key
    # tam config'i pydantic'e vermiyoruz, sadece lang alanini kurcaliyoruz ki
    # bozuk/eski bir config yuzunden dil degistirmek patlamasin
    clean_lang = lang.lower().strip()
    if clean_lang not in STRINGS:
        supported = ", ".join(STRINGS.keys())
        raise ValueError(f"Unsupported language code '{lang}'. Supported: {supported}")
    _current_lang = clean_lang
    config_file = get_config_file_path()
    data = {}
    if config_file.exists():
        try:
            data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
    data["lang"] = clean_lang
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    _cache_key = None
    # ConfigManager zaten ayaktaysa bellekteki kopyayi da guncelle,
    # yoksa bir sonraki save_config eski dili geri yazar
    try:
        from termcraft.core.config_manager import ConfigManager
        if ConfigManager._instance is not None:
            ConfigManager._instance.config.lang = clean_lang
    except Exception:
        pass

def t(key: str, **kwargs) -> str:
    # anahtar bulunamazsa: aktif dil -> ingilizce -> anahtarin kendisi.
    # format hatasinda da ham sablonu donuyoruz, cevirinin eksik olmasi
    # programi durdurmasin diye
    lang = get_current_language()
    template = STRINGS.get(lang, STRINGS["en"]).get(key) or STRINGS["en"].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
