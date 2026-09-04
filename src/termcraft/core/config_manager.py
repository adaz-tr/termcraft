import shutil
import datetime
import yaml
from typing import Optional, List
from termcraft.config import TermCraftConfig, ProfileConfig, AliasDefinition
from termcraft.utils.paths import get_config_file_path
from termcraft.presets.aliases import get_alias_bundle

# config.yaml'in tek sahibi. surec boyunca tek instance uzerinden gidiyoruz ki
# iki farkli kopya birbirinin yazdigini ezmesin (i18n.set_language da buna bakiyor)
class ConfigManager:
    _instance: Optional["ConfigManager"] = None

    def __init__(self):
        self.config_path = get_config_file_path()
        # bozuk config bulunursa nereye tasidigimizi burada tutuyoruz,
        # CLI/TUI kullaniciya haber verebilsin diye
        self.recovered_from: Optional[str] = None
        self.config = self.load_config()

    @classmethod
    def get_instance(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        # testler ve dil degisiminden sonra temiz baslangic icin
        cls._instance = None

    def load_config(self) -> TermCraftConfig:
        if self.config_path.exists():
            try:
                raw_data = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
                if isinstance(raw_data, dict):
                    return TermCraftConfig.model_validate(raw_data)
            except Exception:
                # sema degisti ya da dosya bozuldu. eskiden burasi sessizce
                # varsayilana donup kullanicinin butun alias'larini siliyordu.
                # artik once bir kenara kopyaliyoruz ki veri kaybi olmasin
                self._quarantine_broken_config()
        cfg = TermCraftConfig.get_default()
        self.save_config(cfg)
        return cfg

    def _quarantine_broken_config(self) -> None:
        try:
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config_path.with_suffix(f".broken-{stamp}.yaml")
            shutil.copy2(self.config_path, backup_path)
            self.recovered_from = str(backup_path)
        except Exception:
            pass

    def save_config(self, config: Optional[TermCraftConfig] = None) -> None:
        if config is not None:
            self.config = config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        dump_data = self.config.model_dump()
        self.config_path.write_text(yaml.safe_dump(dump_data, sort_keys=False, allow_unicode=True), encoding="utf-8")

    def get_active_profile(self) -> ProfileConfig:
        # aktif profil yoksa ucar ucmaz olustur, boylece cagiran taraf None kontrolu yapmiyor
        prof_name = self.config.active_profile
        if prof_name not in self.config.profiles:
            self.config.profiles[prof_name] = ProfileConfig(name=prof_name)
            self.save_config()
        return self.config.profiles[prof_name]

    def get_language(self) -> str:
        return self.config.lang

    def set_language(self, lang: str) -> None:
        self.config.lang = lang
        self.save_config()

    def set_theme(self, theme_name: str) -> None:
        self.config.theme.active_theme = theme_name
        prof = self.get_active_profile()
        prof.theme = theme_name
        self.save_config()

    def set_prompt(self, engine: str, preset: str) -> None:
        self.config.prompt.engine = engine
        self.config.prompt.preset = preset
        prof = self.get_active_profile()
        prof.prompt_preset = preset
        self.save_config()

    def get_aliases(self) -> List[AliasDefinition]:
        # ilk calistirmada bos kalmasin diye sadece git paketini yukluyoruz.
        # modern-replacements bilerek disarida: ls/cat/cd'yi kullanicinin haberi
        # olmadan ezmek istemiyoruz, isteyen `termcraft alias bundle` ile alir
        prof = self.get_active_profile()
        if not prof.aliases:
            prof.aliases = get_alias_bundle("git")
            self.save_config()
        return prof.aliases

    def add_alias(self, alias: AliasDefinition) -> None:
        prof = self.get_active_profile()
        prof.aliases = [a for a in prof.aliases if a.name != alias.name]
        prof.aliases.append(alias)
        self.save_config()

    def remove_alias(self, name: str) -> bool:
        prof = self.get_active_profile()
        initial_len = len(prof.aliases)
        prof.aliases = [a for a in prof.aliases if a.name != name]
        if len(prof.aliases) < initial_len:
            self.save_config()
            return True
        return False

    def load_bundle(self, bundle_name: str) -> int:
        # ayni isimdekileri atliyoruz, kullanicinin elle duzenledigi alias ezilmesin
        bundle_items = get_alias_bundle(bundle_name)
        if not bundle_items:
            raise ValueError(f"Bundle '{bundle_name}' not found.")
        prof = self.get_active_profile()
        existing_names = {a.name for a in prof.aliases}
        count = 0
        for item in bundle_items:
            if item.name not in existing_names:
                prof.aliases.append(item)
                existing_names.add(item.name)
                count += 1
        if count > 0:
            self.save_config()
        return count
