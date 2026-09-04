from typing import List, Dict, Type
from termcraft.adapters.base import BaseShellAdapter
from termcraft.adapters.powershell import PowerShellAdapter
from termcraft.adapters.bash import BashAdapter
from termcraft.adapters.zsh import ZshAdapter
from termcraft.adapters.fish import FishAdapter
from termcraft.adapters.nushell import NuShellAdapter

# kayit defteri. yeni kabuk eklerken sadece buraya bir satir atmak yetiyor
ALL_SHELL_ADAPTERS: Dict[str, Type[BaseShellAdapter]] = {
    "powershell": PowerShellAdapter,
    "bash": BashAdapter,
    "zsh": ZshAdapter,
    "fish": FishAdapter,
    "nushell": NuShellAdapter,
}

def get_available_adapters() -> List[BaseShellAdapter]:
    # "available" = ilgili binary PATH'te var demek, profil dosyasi olmasa da olur.
    # yani git bash kuruluysa windows'ta bash adapter'i da devreye giriyor
    adapters = []
    for cls in ALL_SHELL_ADAPTERS.values():
        inst = cls()
        if inst.is_available():
            adapters.append(inst)
    return adapters

def get_adapter(name: str) -> BaseShellAdapter:
    cls = ALL_SHELL_ADAPTERS.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown shell adapter: {name}")
    return cls()
