import shutil
from typing import List, Dict, Optional, Tuple
from termcraft.config import AliasDefinition
from termcraft.core.config_manager import ConfigManager
from termcraft.core.sync import sync_all_shells
from termcraft.presets.aliases import SHADOWING_ALIAS_NAMES

# ConfigManager'in uzerine ince bir katman. asil is orada, burasi sadece
# CLI/TUI'nin rahat cagirabilecegi bir yuz
class AliasManager:
    def __init__(self):
        self.config_mgr = ConfigManager.get_instance()

    @property
    def aliases(self) -> List[AliasDefinition]:
        return self.config_mgr.get_aliases()

    def load_bundle(self, bundle_name: str) -> int:
        return self.config_mgr.load_bundle(bundle_name)

    def add_alias(self, name: str, command: str, description: str = "",
                  shells: Optional[List[str]] = None, requires: Optional[str] = None) -> AliasDefinition:
        target_shells = shells or ["powershell", "bash", "zsh", "fish", "nushell"]
        # AliasDefinition icindeki validator gecersiz isimlerde ValueError atiyor,
        # cagiran taraf onu kullaniciya gosteriyor
        new_alias = AliasDefinition(
            name=name.strip(),
            command=command.strip(),
            description=description.strip(),
            shells=target_shells,
            requires=requires
        )
        self.config_mgr.add_alias(new_alias)
        return new_alias

    def remove_alias(self, name: str) -> bool:
        return self.config_mgr.remove_alias(name)

    def check_shadowing(self) -> List[Tuple[str, str]]:
        """Temel kabuk komutlarini golgeleyen alias'lari dondurur.

        Eskiden tam da bu isimler (ls/cat/cd/grep/find) uyari listesinden
        HARIC tutuluyordu, yani en tehlikeli durum sessizce geciyordu.
        """
        return [(a.name, a.command) for a in self.aliases if a.name in SHADOWING_ALIAS_NAMES]

    def check_missing_requirements(self) -> List[Tuple[str, str]]:
        """`requires` binary'si PATH'te olmayan alias'lar. Bunlar sync'te atlaniyor."""
        result = []
        for a in self.aliases:
            req = getattr(a, "requires", None)
            if req and shutil.which(req) is None:
                result.append((a.name, req))
        return result

    def check_conflicts(self) -> List[Tuple[str, str]]:
        """Alias adiyla ayni isimde PATH'te bir binary var mi diye bakar."""
        conflicts = []
        for a in self.aliases:
            # golgeleme zaten check_shadowing'de ayrica raporlaniyor, burada tekrar etme
            if a.name in SHADOWING_ALIAS_NAMES:
                continue
            sys_path = shutil.which(a.name)
            if sys_path:
                conflicts.append((a.name, sys_path))
        return conflicts

    def sync_to_shells(self) -> Dict[str, bool]:
        return sync_all_shells()
