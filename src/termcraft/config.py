import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

# alias adi kabuk dosyasina duz satir olarak yazildigi icin sadece "zararsiz"
# karakterlere izin veriyoruz. bosluk, noktali virgul, tirnak vs. kabul yok
ALIAS_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-\.]*$")

class ThemeSettings(BaseModel):
    active_theme: str = "tokyo-night"
    sync_terminal_emulator: bool = True
    sync_cli_tools: bool = True

class PromptSettings(BaseModel):
    engine: str = "starship"
    preset: str = "modern-cyber"
    show_banner: bool = True
    banner_style: str = "termcraft"

class AliasDefinition(BaseModel):
    name: str
    command: str
    description: str = ""
    shells: List[str] = Field(default_factory=lambda: ["powershell", "bash", "zsh", "fish", "nushell"])
    # bu alias'in calismasi icin PATH'te bulunmasi gereken binary.
    # mesela `ls -> eza` icin "eza". kurulu degilse sync sirasinda atlaniyor,
    # boylece kullanicinin ls/cat/cd komutlari bozulmuyor
    requires: Optional[str] = None

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        clean = v.strip()
        if not ALIAS_NAME_RE.match(clean):
            raise ValueError(
                f"Gecersiz alias adi: {v!r}. Sadece harf/rakam/_/-/. kullanilabilir "
                f"ve harf ya da _ ile baslamali."
            )
        return clean

class ProfileConfig(BaseModel):
    # profil = bir kullanicinin tema + prompt + alias seti.
    # coklu profil altyapisi duruyor ama CLI'da henuz switch komutu yok
    name: str = "default"
    theme: str = "tokyo-night"
    prompt_preset: str = "modern-cyber"
    aliases: List[AliasDefinition] = Field(default_factory=list)
    custom_env: Dict[str, str] = Field(default_factory=dict)

class TermCraftConfig(BaseModel):
    # ~/.termcraft/config.yaml'in semasi. pydantic sayesinde yaml'i dogrudan
    # model_validate ile okuyup yaziyoruz, elle parse yok
    version: str = "1.0.0"
    lang: str = "tr"
    active_profile: str = "default"
    theme: ThemeSettings = Field(default_factory=ThemeSettings)
    prompt: PromptSettings = Field(default_factory=PromptSettings)
    profiles: Dict[str, ProfileConfig] = Field(default_factory=dict)
    managed_shells: List[str] = Field(default_factory=lambda: ["powershell", "bash", "zsh", "fish", "nushell"])
    # True ise tema/prompt uygulamadan once otomatik snapshot aliniyor
    auto_backup: bool = True

    @classmethod
    def get_default(cls) -> "TermCraftConfig":
        # ilk calistirmada kullanilan bos-ama-gecerli config
        default_profile = ProfileConfig(name="default")
        return cls(profiles={"default": default_profile})
