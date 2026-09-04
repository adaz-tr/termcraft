from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional
from termcraft.config import AliasDefinition

class BaseShellAdapter(ABC):
    # kabuk profillerine yazdigimiz her sey bu iki marker'in arasinda duruyor.
    # boylece kullanicinin kendi satirlarina dokunmadan blogu bulup
    # tamamen degistirebiliyoruz. marker'lari degistirmek eski kurulumlari
    # yetim birakir, dikkat
    START_MARKER = "# >>> termcraft initialize >>>"
    END_MARKER = "# <<< termcraft initialize <<<"

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def get_config_path(self) -> Optional[Path]:
        pass

    @abstractmethod
    def generate_alias_script(self, aliases: List[AliasDefinition]) -> str:
        pass

    @abstractmethod
    def generate_env_script(self, env_vars: Dict[str, str]) -> str:
        pass

    @abstractmethod
    def generate_prompt_hook(self, engine: str, preset_path: Optional[str] = None, preset_name: Optional[str] = None) -> str:
        pass

    # env + alias + prompt'u tek blokta birlestir. bos donen bolumleri atliyoruz
    # ki profilde gereksiz bos satir birikmesin.
    # DIKKAT: env_vars bos gelirse generate_env_script hic cagrilmiyor -> powershell
    # tarafinda PSReadLine renkleri de yazilmiyor. bilincli degil, yan etki
    def generate_unified_script(
        self,
        env_vars: Optional[Dict[str, str]] = None,
        aliases: Optional[List[AliasDefinition]] = None,
        prompt_engine: Optional[str] = None,
        prompt_preset_path: Optional[str] = None,
        prompt_preset_name: Optional[str] = None
    ) -> str:
        sections = []
        if env_vars:
            env_content = self.generate_env_script(env_vars).strip()
            if env_content:
                sections.append(env_content)
        if aliases:
            alias_content = self.generate_alias_script(aliases).strip()
            if alias_content:
                sections.append(alias_content)
        if prompt_engine:
            prompt_content = self.generate_prompt_hook(prompt_engine, prompt_preset_path, prompt_preset_name).strip()
            if prompt_content:
                sections.append(prompt_content)
        return "\n\n".join(sections)

    def read_config(self) -> str:
        path = self.get_config_path()
        if path and path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
        return ""

    # blok zaten varsa yerinde degistir, yoksa dosyanin sonuna ekle.
    #
    # SOZLESME: bu metot marker'lar arasindaki her seyi ATAR ve content ile
    # degistirir. yani kismi bir script ile cagirmak (sadece env, sadece alias)
    # geri kalanini siler. doctor.auto_fix bir zamanlar tam bunu yapiyordu ve
    # kullanicinin butun alias'larini ucuruyordu.
    # kural: profile yazan her sey sync_all_shells() uzerinden gecmeli, orasi
    # blogu butun halinde yeniden uretiyor. bloga bir sey eklemen gerekiyorsa
    # sync_all_shells'in extra_env parametresini kullan.
    # yedekleme cagiran tarafta: theme/prompt uygulamalari once maybe_snapshot()
    def inject_block(self, content: str) -> bool:
        path = self.get_config_path()
        if not path:
            return False
        
        path.parent.mkdir(parents=True, exist_ok=True)
        current = self.read_config()
        
        block = f"{self.START_MARKER}\n{content.strip()}\n{self.END_MARKER}\n"
        
        if self.START_MARKER in current and self.END_MARKER in current:
            start = current.find(self.START_MARKER)
            end = current.find(self.END_MARKER) + len(self.END_MARKER)
            new_content = current[:start] + block + current[end:].lstrip("\n")
        else:
            new_content = current.rstrip() + ("\n\n" if current else "") + block
            
        path.write_text(new_content, encoding="utf-8")
        return True

    # kurulumu geri almak icin. su an CLI'dan cagiran yok, sadece test/ileride lazim
    def remove_block(self) -> bool:
        path = self.get_config_path()
        if not path or not path.exists():
            return False
        current = self.read_config()
        if self.START_MARKER in current and self.END_MARKER in current:
            start = current.find(self.START_MARKER)
            end = current.find(self.END_MARKER) + len(self.END_MARKER)
            new_content = current[:start].rstrip() + "\n" + current[end:].lstrip()
            path.write_text(new_content.strip() + "\n", encoding="utf-8")
            return True
        return False
